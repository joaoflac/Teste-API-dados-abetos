# Planejamento — CRUD do painel e fila de validação humana

Rascunho de 26/11, revisado pelo Opus e atualizado com as decisões do dono no mesmo dia (§0). Ponto de partida: o front de administração já existe no `TERRITORIOS_SECTI` (branch `redesign`), mas ainda não grava nada.

## 0. Decisões do dono (26/11)

1. **Linha duvidosa não é publicada.** Ela fica no CRUD, marcada como "aguardando confirmação", até alguém **confirmar** ou **corrigir**. Vale para nome sem par **e** para casamento por aproximação.
2. **A pessoa vence (C1 decidido).** Linha ou coluna editada no CRUD **permanece** como a pessoa deixou: a recarga do ETL não a sobrescreve, nem quando o resto do conjunto muda, nem quando muda outra coluna da mesma linha. Motivo: a planilha do governo tem erros (ex.: nomes de município) e às vezes é preciso corrigir o dado oficial.
3. **Não há aba "Validação" separada.** As linhas pendentes aparecem **dentro das abas do CRUD**, junto com as outras, marcadas e filtráveis (§5).
4. **Retenção:** 12 meses para pendências fechadas, `audit.evento`, `etl.exclusao` e `etl.historico` (confirmado em 26/11).
5. **Edição × recarga, priorizando a autonomia** (decidido em 26/11, depois da proposta do Opus):
   - **A fonte exclui uma linha editada:** a linha sai **e a edição da pessoa sai junto** (cascata), sem perguntar. A trava de exclusão em massa continua valendo. As duas ficam **no log por 12 meses**, e a pessoa pode **restaurar** pelo CRUD; a linha volta como incluída pela pessoa, com as edições dela.
   - **A fonte muda a coluna editada:** o valor da pessoa continua (update restrito). **Só quando uma carga altera colunas editadas** (de uma linha ou em massa) aparece uma **solicitação de atualização da fonte**: um **pop-up** lista as linhas e colunas afetadas, cada uma com a caixa **"aceitar atualização da fonte" desmarcada**. Marcar e confirmar = a fonte vence naquelas colunas. Deixar desmarcado = a pessoa continua vencendo, e a solicitação só volta se a fonte mudar de novo. Sem carga que altere uma coluna editada, não aparece caixa nenhuma.
   - **A fonte passa a dizer o mesmo que a pessoa:** a fonte corrigiu o erro. A edição se encerra sozinha.
   - **Linha incluída ou excluída pela pessoa:** "a fonte removeu" não se aplica. A inclusão e a exclusão valem até a pessoa desfazê-las.
   - **Ainda exige alguém:** a linha duvidosa da decisão 1 e a confirmação do pop-up, que é opcional (enquanto ninguém confirma, vale o valor da pessoa).

## 1. O que existe hoje

**Front** (`TERRITORIOS_SECTI/src/components/AdminPage.jsx`, 1.741 linhas, e `src/utils/crudDraft.js`):
- abas `ativos`, `cursos` e `cadeias` (APL e IG), com busca, filtros, gaveta de edição, exclusão e histórico;
- lê as tabelas do **Supabase** (`lista_ativos_cti`, `lista_cursos_cti`, `distribuicao_cadeias`...) por `supabase-js` (`DataContext.jsx`); as alterações ficam num **rascunho no `localStorage`** (`@SectiPainel_CRUD_Draft_v1`) e o "histórico" é desse rascunho;
- a rota `/admin` **não tem login** (`App.jsx`). Hoje é inofensivo, porque nada é gravado; deixa de ser quando gravar.

**Banco novo** (este repositório):
- papel `api_crud`; auditoria por trigger com contexto declarado (`audit.contexto('api', usuario, request_id)`);
- curadoria que já sobrevive à recarga porque fica **fora do `_hash` e das colunas do MERGE**: `inep.regra_cti`, `inep.curso.oculto_curadoria`;
- de-para do APL em CSV (`PLANEJAMENTO_APL.md` §4), com `0` = ignorar de propósito;
- `apl.apl_municipio.metodo_cruzamento` já diz se o par veio do nome exato, do de-para ou da aproximação.

**Lacunas:**
- não há API nem login;
- quando um nome não casa, o ETL **aborta a carga inteira** (`montar()` em `orquestrador_apl.py`); quando casa por aproximação, só escreve no log;
- não há um lugar único onde a curadoria veja o que precisa de decisão.

## 2. Objetivo

1. **Curadoria no CRUD:** o que precisa de decisão humana aparece no próprio painel do CRUD quando a fonte muda e o dado não confere. Casos reais:
   - nome de município que nenhum método resolve ("Capela", "Tancredo Neves");
   - município casado por aproximação (Iritinga → Biritinga): **também espera confirmação** (decisão 1);
   - CNPJ do APL fora do APL, inválido ou inapto (BrasilAPI, quando for incorporada);
   - curso que mudou de IES entre censos (33 entre 2022 e 2023).
2. **Edição humana permanente:** o que a pessoa altera, inclui ou exclui no CRUD sobrevive às recargas (§3.5).
3. A decisão vale para as próximas cargas: ninguém decide duas vezes a mesma coisa, e uma mudança real da fonte volta para a curadoria.
4. Depois, o CRUD das abas atuais sobre o banco novo, com auditoria (depende de C4 e C5).

**Fica fora da fila, de propósito:**
- **Divergência com o Supabase** (as listas trocadas do cacau): o Supabase é só referência e sai de cena na migração (C4). A conferência é pontual e já existe no teste `07_teste_aproximacao.py --xlsx`; no banco novo o cacau já está certo, porque vem da planilha.
- **Rótulo CINE sem regra ou `revisar`:** já fica fora da view, e a decisão já tem casa (`inep.regra_cti`). O CRUD lista esses rótulos direto da tabela.

## 3. Proposta: fila de pendências (a "tabela clone")

### 3.1 Uma fila genérica, não um clone por tabela

Um clone por tabela (`apl.apl_municipio_pendente`, `inep.curso_pendente`...) duplica o DDL, a tela e a API por fonte. A proposta é **uma tabela só**. O "clone" é a evidência: o pedaço da linha da fonte que gerou a dúvida, guardado em `jsonb`.

**Princípio:** a fila é uma **caixa de entrada**, não o lugar da decisão. Sempre que possível, a decisão é gravada numa tabela de domínio que o ETL já lê. Exemplos: o de-para de municípios e `inep.regra_cti`. Assim a regra deixa de disparar sozinha na próxima carga. Só os avisos do tipo "estou ciente" guardam a decisão na própria fila.

```sql
CREATE TABLE curadoria.pendencia (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recurso         text   NOT NULL REFERENCES etl.recurso(id),     -- quem detectou (ex.: mdic_apl_ba)
    tabela          text   NOT NULL,                                -- tabela afetada (ex.: apl.apl_municipio)
    regra           text   NOT NULL CHECK (regra IN ('municipio_sem_par', 'municipio_aproximado',
                                                     'cnpj_fora_do_apl', 'cnpj_invalido', 'cnpj_inapto', 'curso_mudou_de_ies')),
    severidade      text   NOT NULL CHECK (severidade IN ('bloqueia', 'alerta')),
    chave           jsonb  NOT NULL,   -- o que a decisão resolve, com os tipos das colunas: {"nome": "capela"} ou {"co_curso": 123}
    evidencia       jsonb  NOT NULL,   -- o "clone": o que a fonte trouxe e o contexto (APLs onde o nome aparece, 1º e 2º candidatos)
    linha_fonte     jsonb,             -- a versão que chegou, inteira (linha + filhas, ex.: o APL e a lista de municípios); é o que o CRUD mostra ao lado do publicado
    evidencia_hash  text   NOT NULL,   -- md5 só do que a decisão leva em conta (não da linha inteira)
    proposta        jsonb,             -- o que o ETL sugere (ex.: {"codigo_ibge": 2903607})
    status          text   NOT NULL DEFAULT 'aberta' CHECK (status IN ('aberta', 'decidida', 'obsoleta')),
    decisao         jsonb,             -- {"acao": "de_para", "codigo_ibge": ...} | {"acao": "ignorar"} | {"acao": "ciente"}
    justificativa   text,
    decidido_por    text, decidido_em timestamptz,
    vista_execucao  bigint REFERENCES etl.execucao(id),              -- última carga que detectou a pendência
    criado_em       timestamptz NOT NULL DEFAULT now(),
    UNIQUE (recurso, regra, chave)
);
CREATE INDEX ON curadoria.pendencia (status) WHERE status = 'aberta';
```

Por que assim:
- **Uma linha por problema**, não uma por versão da fonte. O `UNIQUE (..., hash_fonte)` do rascunho acumulava linhas e reabria a pendência quando mudava qualquer coluna da linha, até uma sem relação com a dúvida (ex.: `qt_empresas` do APL).
- **Chave jsonb:** a ordem das chaves não importa no `jsonb`, mas o tipo sim (`12` ≠ `"12"`). Monte a chave como `audit.registrar` monta a sua, a partir das colunas tipadas (ou, no Python, com `int` para coluna `int`). Assim ela cruza direto com `audit.evento.chave` e `meta.v_linha_origem`.
- **Sem tabela `curadoria.regra`:** são 6 regras; um `CHECK` basta, e a severidade fica no código do orquestrador. A descrição de cada regra fica na tabela do §3.4 e no front.
- Volume pequeno (dezenas de linhas): o `UNIQUE` e o índice parcial bastam. Não precisa de GIN.

### 3.2 Ciclo de vida

**O ETL detecta** (dentro da transação da carga):

```sql
INSERT INTO curadoria.pendencia (recurso, tabela, regra, severidade, chave, evidencia, evidencia_hash, proposta, vista_execucao)
VALUES (...)
ON CONFLICT (recurso, regra, chave) DO UPDATE
   SET evidencia = EXCLUDED.evidencia, proposta = EXCLUDED.proposta, vista_execucao = EXCLUDED.vista_execucao,
       -- só reabre se a evidência que importa mudou (ou se estava obsoleta e voltou)
       status        = CASE WHEN pendencia.evidencia_hash <> EXCLUDED.evidencia_hash OR pendencia.status = 'obsoleta'
                            THEN 'aberta' ELSE pendencia.status END,
       decisao       = CASE WHEN pendencia.evidencia_hash <> EXCLUDED.evidencia_hash THEN NULL ELSE pendencia.decisao END,
       evidencia_hash = EXCLUDED.evidencia_hash;
```

**Ao fim de uma carga `ok`**, o que não foi visto nela sai da fila: `UPDATE ... SET status = 'obsoleta' WHERE recurso = <rid> AND status = 'aberta' AND vista_execucao <> <exe>`. Só depois de carga bem-sucedida, como o checkpoint. Uma carga que aborta não pode "resolver" pendências.

**A pessoa decide** pela função `curadoria.decidir(id, evidencia_hash, decisao, justificativa)`, numa transação:
1. `UPDATE curadoria.pendencia SET status = 'decidida', ... WHERE id = $1 AND status = 'aberta' AND evidencia_hash = $2`. Se nenhuma linha mudar, recusa ("a pendência mudou; recarregue"). Isso cobre a pessoa que decide com a tela desatualizada enquanto o ETL roda.
2. Grava o efeito na tabela de domínio, quando houver uma (§3.3).
3. Justificativa obrigatória.

Uma decisão tomada durante a carga vale a partir da carga seguinte (o orquestrador lê o de-para no início). Isso é aceitável.

**Histórico:** `audit.ativar('curadoria.pendencia', '{id}')` e o mesmo para o de-para. Atenção: o trigger `audit.carimbar` escreve `_hash`, `_modificado_em`, `_modificado_fonte_em` e `_execucao_id`. Essas tabelas precisam ter as colunas de controle, com `_hash` **anulável**, porque quando o ETL escreve ninguém o preenche. A decisão anterior de uma pendência reaberta fica em `audit.evento.antes`.

### 3.3 Linha duvidosa: fica no CRUD, fora do painel público

Pela decisão 1, toda regra de **dúvida sobre o dado** bloqueia: a linha duvidosa **não é publicada** e a versão anterior (se houver) continua valendo. O resto da carga segue. Problemas do **conjunto** (layout mudou, trava de exclusão em massa, `ibge.municipio` vazia) continuam abortando a carga inteira. Avisos que não põem em dúvida o dado publicado (CNPJ inapto, curso que mudou de IES) são **selos informativos**. Não bloqueiam nem exigem decisão: "ciente" só esconde o selo, e o aviso fica `obsoleta` sozinho quando a carga deixa de detectá-lo. As situações de edição do §3.5 não passam pela fila.

**Por que "fora do escopo" e não "fora do staging":** `etl.merge_tabela` exclui tudo o que está no escopo e não veio no staging. Uma linha bloqueada que só fosse omitida do staging seria **excluída** da tabela oficial (e contaria para a trava). O `p_escopo` filtra o staging (`_src`, alias `s`), o ramo `DELETE` e a contagem da trava (alias `t`). Basta acrescentar `AND NOT (<chave bloqueada>)` ao escopo: a linha não é inserida, alterada, excluída nem contada. **Não precisa mudar `merge_tabela`.**

**No APL (piloto):**
- **Nome sem par** congela o APL inteiro (a linha em `apl.apl` e a lista de municípios): não se sabe qual par antigo o nome errado substitui. Escopo de `apl.apl`: `{a}.uf = 'BA' AND {a}.nome_apl <> ALL(<congelados>)` (por nome, porque `stg.apl` não tem `id_apl`; o valor entra como `psycopg.sql.Literal`). Escopo de `apl.apl_municipio`: `AND {a}.id_apl <> ALL(<ids congelados>)`.
- **Casamento aproximado** segura só **o par**: o par sugerido não entra até a confirmação; o resto do APL é publicado. Confirmar = linha no de-para; na próxima carga o par entra como `de_para`.
- APL **novo** com nome sem par não entra até a decisão: não existe em `apl.apl`, então o `id_apl` no staging fica nulo e o par cai sozinho.
- O `raise` de `sem_par` em `montar()` sai; o polo sem par (`codigo_ibge_polo`) entra na mesma regra.
- **Primeira carga:** os 14 pares aproximados de hoje já foram conferidos com o Supabase (`PLANEJAMENTO_APL.md` §6). Para não abrir 14 pendências já resolvidas, a semente do de-para os inclui com `justificativa = 'conferido com o Supabase em 26/11'`.

### 3.4 Regras, chave e onde a decisão fica

| Regra | Fonte | Severidade | Chave | Decisão grava em | Exemplo real |
|---|---|---|---|---|---|
| `municipio_sem_par` | APL | bloqueia | `{"nome": chave_nome(nome)}` | `curadoria.de_para_municipio` (código ou `0` = ignorar) | "Capela" |
| `municipio_aproximado` | APL | bloqueia (decisão 1) | `{"nome": chave_nome(nome)}` | aprovar ou corrigir = linha no de-para; na próxima carga o par vira `de_para` e a regra não dispara mais | Iritinga → Biritinga |
| `cnpj_fora_do_apl` / `cnpj_invalido` / `cnpj_inapto` | APL (BrasilAPI) | alerta (selo) | `{"id_apl": n}` | nada obrigatório; "ciente" esconde o selo até o CNPJ ou a situação mudar | Giló, Pescados da BTS |
| `curso_mudou_de_ies` | INEP | alerta (selo) | `{"co_curso": n}` | nada obrigatório; "ciente" esconde o selo até mudar de novo | 33 cursos (2022 → 2023) |

`evidencia_hash` por regra: o nome e a proposta (regras de nome); o CNPJ e a situação (CNPJ); o par `co_ies` antigo e novo (curso). Edição humana × recarga não gera pendência: é resolvida sozinha ou vira selo (§3.5).

**`curadoria.de_para_municipio` substitui o CSV:**
- colunas `nome_chave`, `nome_original`, `codigo_ibge` (0 = ignorar), `justificativa` e as colunas de controle;
- é global (um nome vale para qualquer fonte que traga município por nome);
- o CSV vira **semente**, carregada com `ON CONFLICT DO NOTHING`, como `inep.regra_cti`. Depois disso a verdade é o banco, e o CSV não sobrescreve a curadoria. O backup `pg-portatil/backup/painel.sql` versiona a tabela.

### 3.5 Edição humana que a recarga respeita (C1 decidido: a pessoa vence)

**Colunas fixas:** o CRUD edita **valores** (campo de uma linha), inclui e exclui **linhas**. Ele nunca cria, remove ou renomeia colunas. Não são editáveis: as colunas da chave (mudar a chave = excluir + incluir) e as de controle (`_hash`, `_criado_em`, `_origem` etc.). Coluna nova só entra por migração SQL versionada (como `07_apl_modelo.sql`). Se a fonte mudar o layout, o ETL aborta a carga (`ler_xlsx` confere as colunas) até alguém ajustar o modelo.

**Regra:** o que a pessoa muda no CRUD fica como ela deixou, **por coluna**. A recarga do ETL continua atualizando tudo o que ninguém editou: outras linhas e **outras colunas da mesma linha**.

Hoje uma edição pela API recebe `_hash = 'api:...'` e o próximo MERGE da partição a sobrescreve (`PLANEJAMENTO_IBGE.md` §7C). Isso muda para uma tabela de **sobreposições**, aplicada no staging **antes** do MERGE:

```sql
CREATE TABLE curadoria.sobreposicao (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tabela        text  NOT NULL,                     -- ex.: apl.apl
    chave         jsonb NOT NULL,                     -- chave natural tipada, que existe no staging: {"uf": "BA", "nome_apl": "Ser do Sertão"}
    acao          text  NOT NULL CHECK (acao IN ('valor', 'incluir', 'excluir')),
    coluna        text,                               -- só em 'valor'; nunca uma coluna da chave (mudar a chave = excluir + incluir)
    valor         jsonb,                              -- 'valor': o valor da pessoa; 'incluir': a linha inteira
    valor_fonte   jsonb,                              -- o que a fonte dizia quando a pessoa editou (ou quando marcou "manter")
    fonte_atual   jsonb,                              -- o que a fonte trouxe na última carga (gravado por curadoria.aplicar)
    fonte_mudou_execucao bigint REFERENCES etl.execucao(id),  -- carga que mudou a coluna editada: agrupa a solicitação do pop-up
    justificativa text  NOT NULL,
    autor text NOT NULL, criado_em timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (tabela, chave, coluna)  -- uma edição por coluna (ou por linha, em incluir/excluir)
);
```

Não há coluna `ativa`: "voltar à fonte" **apaga** a sobreposição. O que ela dizia fica em `audit.evento`, porque a tabela tem `audit.ativar`.

**Como cada edição do CRUD vira sobreposição** (função `api.editar`, numa transação com `audit.contexto('api', ...)`):

| No CRUD | Sobreposição | Efeito imediato | Na recarga |
|---|---|---|---|
| altera uma coluna | `valor` (guarda `valor_fonte`) | atualiza a linha publicada | o staging recebe o valor da pessoa, então o MERGE não vê diferença naquela coluna; as outras colunas seguem a fonte |
| inclui uma linha que a fonte não tem | `incluir` (linha inteira) | insere a linha | a linha é reposta no staging, então o MERGE não a exclui. Se um dia a fonte trouxer a mesma chave, a linha da pessoa vence inteira |
| exclui uma linha que a fonte tem | `excluir` | apaga a linha | a linha sai do staging antes do MERGE e não volta, nem se a fonte a remover e depois a trouxer de novo |

**Aplicação genérica:** `curadoria.aplicar(tabela_destino, stg)`, chamada pelo orquestrador antes de cada `etl.merge_tabela`, casa a sobreposição com a linha do staging por contenção (`to_jsonb(s) @> chave`). Funciona para qualquer tabela, sem código por fonte. Por isso a chave usa só colunas que existem no staging: no APL é a chave natural (`uf`, `nome_apl`), não o `id_apl`.

**O que `curadoria.aplicar` faz em cada carga com uma edição de coluna (`valor`) cuja linha veio no staging.** Tudo é automático:

| A fonte agora diz (`s.coluna`) | Resultado | Por quê |
|---|---|---|
| o mesmo que a pessoa (`= valor`) | a edição **se encerra** (DELETE, auditado) | a fonte corrigiu o erro; a edição não tem mais função |
| o mesmo de quando a pessoa editou (`= valor_fonte`) | o staging recebe `valor` | caso normal: a pessoa vence |
| outro valor | o staging recebe `valor` (a pessoa continua vencendo); `fonte_atual` e `fonte_mudou_execucao` são gravados | update restrito; abre a **solicitação de atualização da fonte** |

**Solicitação de atualização da fonte** (o pop-up da decisão 5):
- **Existe só quando uma carga alterou colunas editadas**: `fonte_atual IS DISTINCT FROM valor_fonte`. Se a carga não tocou nenhuma coluna editada, ou nem houve carga, não há solicitação nem caixa na tela.
- **É agrupada pela carga** (`fonte_mudou_execucao`). Uma linha alterada ou uma atualização em massa da tabela aparecem no mesmo pop-up: "a carga de <data> do <recurso> mudou N colunas editadas em M linhas".
- Cada item mostra linha, coluna, **fonte quando a pessoa editou**, **fonte agora** e **valor da pessoa**, com a caixa **"aceitar atualização da fonte" desmarcada**. Há também "marcar todas".
- **Confirmar** chama `curadoria.resolver_atualizacao(ids_aceitos, ids_mantidos, justificativa)`, numa transação:
  - **aceitos:** a linha publicada recebe `fonte_atual` na hora (sem esperar a próxima carga), e a sobreposição é apagada (auditado);
  - **mantidos** (desmarcados): `valor_fonte := fonte_atual`. A solicitação fecha e só volta se a fonte mudar de novo.
- **Fechar o pop-up sem confirmar** deixa a solicitação aberta, com um contador no topo da aba. Enquanto isso, vale o valor da pessoa.

**`valor_fonte` continua necessário.** É por ele que se sabe se a fonte mudou desde a edição, e é ele que abre e fecha a solicitação.

**Quando a fonte exclui uma linha editada (cascata, decisão 5):**
- a edição não encontra a linha no staging e não tem efeito; o MERGE exclui a linha como qualquer outra;
- depois do MERGE, `curadoria.cascatear(destino)` apaga as edições `valor` cuja chave não existe mais na tabela oficial (`NOT EXISTS ... to_jsonb(t) @> chave`). O DELETE é auditado: a edição fica em `audit.evento.antes`, e a linha em `etl.exclusao.linha`, as duas com o mesmo `execucao_id`;
- **restaurar** (pelo CRUD, enquanto o log existir, 12 meses): a lista **"excluídas pela fonte"** lê `etl.exclusao` dos últimos 12 meses. "Restaurar" chama `api.restaurar(exclusao_id, justificativa)`, que cria uma sobreposição **`incluir`** com a última versão da linha **já com as edições da pessoa** (reaplicadas a partir de `audit.evento`). A linha volta e fica como incluída pela pessoa: a fonte não a exclui mais;
- **APL renomeado na fonte** (exclusão + inclusão, `id_apl` novo): o APL antigo e as edições dele vão para a lista "excluídas pela fonte". A pessoa decide se restaura o antigo ou se reaplica as edições no novo; nada some sem registro;
- **exclusão em massa** continua parando na trava de `etl.merge_tabela` (20% no APL e no INEP; 10%, o padrão, no IBGE), antes de qualquer cascata. As cascatas de FK continuam as do DDL: `apl.apl` → `apl.apl_municipio` é `CASCADE`; `ibge.municipio` → filhas é `RESTRICT` e aborta a carga, o que já é um caso de decisão humana.

`curadoria.cascatear` faz uma varredura por edição (`to_jsonb(t) @> chave`). São dezenas de edições: não precisa de índice.

**Inclusões e exclusões da pessoa:** não são afetadas pela exclusão na fonte. `incluir` é reposta no staging a cada carga; `excluir` continua tirando a linha. Só a pessoa as desfaz.

**Rastreabilidade:**
- `meta.v_linha_origem` ganha a coluna `editado_por_pessoa` (`EXISTS` em `curadoria.sobreposicao` pela mesma chave), porque depois da recarga a linha volta a dizer `_origem = 'etl'`;
- o CRUD mostra um selo "editado" por coluna;
- a view hoje só cobre `ibge.*`; incluir `apl` e `inep` é a pendência D11.

**Efeito colateral conhecido:** na primeira recarga depois de uma edição, o MERGE troca o `_hash = 'api:...'` pelo hash real, sem mudar valor. Isso gera uma entrada em `etl.historico`, e é esperado.

## 4. API

**Recomendação: PostgREST** num contêiner na VPS, atrás de um proxy reverso (Caddy ou nginx) que cuida de TLS e CORS. Não há código de servidor: as regras ficam no banco, que já tem auditoria e papéis.

**Exponha um schema só, `api`**, com views e funções (`db-schemas = api`), nunca `ibge`, `inep`, `apl`, `etl` ou `audit`:
- hoje `api_crud` tem `INSERT/UPDATE/DELETE` direto em `ibge.*` (`05_auditoria.sql`). Exposto, um curador editaria o PIB por fora da fila. Retire esse acesso do papel web;
- o schema `api` **é o contrato com o painel** (C4): o front lê `api.curso`, `api.apl_municipio` etc., e as tabelas podem mudar por baixo sem quebrar o front;
- com as permissões por papel e só views e funções expostas, **não precisa de RLS**.

**Papéis:**
- `web_anon`: só `SELECT` nas views públicas do `api`;
- `curador`: além disso, `api.pendencia_aberta`, `api.historico` (view sobre `audit.evento`) e as funções `curadoria.decidir` e as de edição de `regra_cti`, `oculto_curadoria` e de-para (expostas em `api`).

**Auditoria pelo `db-pre-request`:** ele roda na mesma transação da requisição, então o `set_config` local de `audit.contexto` vale. Ele **precisa ramificar por papel**: `audit.contexto` recusa usuário vazio, e uma chamada incondicional quebraria toda leitura anônima. Para `curador`, chama `audit.contexto('api', <sub ou e-mail do JWT>, <cabeçalho X-Request-Id>)`.

**Front:**
- o `supabase-js` monta `<url>/rest/v1/...` para dados e `<url>/auth/v1/...` para login (conferir na versão instalada). Para falar com o PostgREST próprio, há dois caminhos: o proxy mapeia `/rest/v1` para o PostgREST, e o front só troca a URL; ou o front usa `@supabase/postgrest-js` (mesma sintaxe de `.from()` e `.rpc()`);
- as views do `api` mantêm os nomes de coluna que o front espera, ou o front se adapta (C4).

**Login (decidir em F3, junto com C4):**
- **(a) Supabase Auth**, enquanto o painel estiver lá: o PostgREST valida o JWT pela chave pública (JWKS) do projeto, e o front mantém `supabase.auth`. Custo: dependência de um serviço do qual o projeto quer sair;
- **(b) login no próprio banco**: `api.entrar(email, senha)` com senha em bcrypt (`pgcrypto`) e um JWT HS256 assinado em SQL. O segredo fica só na configuração do PostgREST e numa tabela legível apenas pela função `SECURITY DEFINER`, **nunca numa GUC**, porque qualquer papel lê `current_setting`. É a opção para a VPS;
- se o admin for servido **na mesma origem** que a API, há uma opção mais simples: autenticação básica no proxy, que repassa o usuário num cabeçalho, sem JWT. Só vale com o PostgREST inacessível por fora do proxy.

**Riscos a fechar antes de abrir para a internet:** porta do PostgREST e do Postgres só na rede interna do Docker; CORS restrito à origem do painel; segredo do JWT fora do git (como o `pgpass.txt`); `max-rows` no PostgREST para leitura anônima.

## 5. Front: curadoria dentro das abas do CRUD (sem aba separada)

- **Login antes de tudo:** `/admin` passa a exigir sessão de `curador`.
- **Pendências na própria tabela:** em cada aba (`ativos`, `cursos`, `cadeias`), as linhas pendentes aparecem junto com as outras, com o selo **"aguardando confirmação"**. Há um filtro **"só pendentes"** e um contador por aba no topo. O `AdminPage` já tem o filtro "só modificados" e a pílula de status (`CrudStatusPill`): a ideia é estendê-los, não criar tela nova.
- **Gaveta de edição** de uma linha pendente: mostra **o que veio da fonte** (`evidencia`), ao lado da **proposta** e, quando existir, da linha publicada.
- **Ações:**
  - **confirmar** a proposta;
  - **corrigir**: o campo vem preenchido com a proposta; para município, um seletor com os 417;
  - **ignorar** (de-para `0`) ou **ciente**, nos avisos.

  Todas exigem justificativa. O front envia o `evidencia_hash` que mostrou.
- **Colunas editadas por pessoa:** selo **"editado"**; ao passar o mouse aparece o valor da fonte; há a opção **"voltar à fonte"**.
- **Pop-up "atualização da fonte"** (decisão 5): abre ao entrar na aba quando há solicitação, e fica num contador no topo.
  - aparece **só** depois de uma carga que mudou colunas editadas, de uma linha ou em massa;
  - lista as linhas e colunas afetadas com os três valores e a caixa **"aceitar atualização da fonte" desmarcada**, mais "marcar todas";
  - **confirmar** aplica as marcadas e mantém as outras; **fechar** deixa para depois.
- **"Excluídas pela fonte"** (filtro ou lista na aba): linhas e edições apagadas pela fonte nos últimos 12 meses, com a ação **"restaurar"**.
- **Coluna "Última modificação" no lugar de selos de situação** (protótipo de 26/11):
  - a célula mostra a data e quem mudou ("carga da fonte", "curadoria · nome" ou "ajuste direto no banco"), mais "N correções" quando há sobreposição;
  - a hora, a carga e a data dos dados da fonte ficam na dica (tooltip);
  - só ficam os selos que pedem ação: "Aguardando confirmação" e "Fonte mudou";
  - ordem padrão: o que precisa de atenção primeiro, depois a modificação mais recente.
  - **A data não pode ser o `_modificado_em` cru:** a primeira recarga depois de uma edição troca o `_hash 'api:...'` sem mudar valor e marcaria a linha como "carga da fonte". Por isso a view `api.*` expõe `ultima_alteracao_em/_origem/_por`, tirados do último `audit.evento` da linha que mudou algum valor (INSERT ou `campos_alterados` não vazio). Sem evento (mais de 12 meses, por causa da retenção), a view usa `_modificado_em`.
- **Rótulos CINE** sem regra ou `revisar`: lista na aba `cursos`, editando `inep.regra_cti`.
- **Histórico** por linha: `api.historico`, uma view sobre `audit.evento` que inclui as sobreposições e o de-para.
- **Ordem:**
  - a curadoria do APL vem primeiro, na aba `cadeias` ligada ao banco novo;
  - `ativos` e `cursos` dependem de C4 e C5: hoje espelham tabelas do Supabase que o banco novo não tem ("ativo" ↔ campus, `id_municipio` ↔ `codigo_ibge`);
  - o rascunho em `localStorage` sai aba por aba, quando cada uma ganha views no `api`.

## 6. Fases

Todos os testes rodam em **banco descartável ou com UF fictícia**. O escopo do APL é a BA inteira, e uma carga de teste no banco real apagaria pares de verdade (o incidente de 19/11 no `CLAUDE.md`).

| Fase | Entrega | Pronto quando |
|---|---|---|
| F0 | Decidido em 26/11: bloquear a linha duvidosa, a pessoa vence (C1), cascata com restauração, pop-up de atualização da fonte e retenção de 12 meses (inclusive `etl.exclusao`). Falta: quem são os curadores e o caminho de login (§4, ligado a C4) | registradas em `PENDENCIAS_E_PERGUNTAS.md` |
| F1 | schema `curadoria`: `pendencia`, `de_para_municipio` (semente: o CSV e os 14 aproximados já conferidos) e `sobreposicao`; funções `curadoria.decidir()`, `curadoria.aplicar()`, `curadoria.cascatear()`, `curadoria.resolver_atualizacao()`, `api.editar()` e `api.restaurar()`; auditoria nas três tabelas | teste SQL com dados fictícios: (1) a mesma evidência detectada de novo não reabre a pendência decidida; (2) evidência diferente reabre e limpa a decisão; (3) problema não visto numa carga `ok` vira `obsoleta`, numa carga abortada não; (4) `decidir` com `evidencia_hash` antigo é recusado; (5) coluna editada sobrevive à recarga, e a coluna vizinha da mesma linha segue a fonte; (6) a fonte muda a coluna editada: o valor da pessoa fica e abre a solicitação, agrupada pela carga; carga que não toca coluna editada não abre nada; (7) `resolver_atualizacao`: a coluna aceita recebe o valor da fonte na hora e a sobreposição some; a mantida fica, e a solicitação não volta na recarga seguinte com a mesma fonte; (8) a fonte passa a dizer o mesmo que a pessoa: a edição se encerra; (9) a fonte exclui a linha editada: a linha e a edição saem, aparecem em `etl.exclusao` e `audit.evento` com o mesmo `execucao_id`; `restaurar` traz a linha com as edições e a recarga seguinte não a exclui; (10) linha incluída pela pessoa não é excluída pelo MERGE, e linha excluída pela pessoa não volta; (11) tudo aparece em `audit.evento`; (12) os testes do §7.4 (camadas, excluídos, retenção, papel público) |
| F2 | piloto no APL: `montar()` grava pendências em vez de abortar, segura a linha duvidosa pelo escopo, lê o de-para do banco e chama `curadoria.aplicar` | (1) recarga `--forcar` da mesma planilha: 0 pendências novas e 0 linhas alteradas; (2) nome sem par num APL existente: carga `ok`, pares antigos do APL intactos, 0 exclusões, trava não acionada; (3) nome aproximado novo: o par só é publicado depois da confirmação e entra como `de_para`; (4) nome que some da planilha deixa a pendência `obsoleta`; (5) o teste 07 continua passando |
| F3 | PostgREST, schema `api`, `db-pre-request` e login no Postgres local; tirar de `api_crud` o acesso direto a `ibge.*` | `curl`: (1) GET anônimo numa view funciona; (2) escrita anônima e GET em `ibge.*` são recusados; (3) o curador decide uma pendência e edita uma coluna, e os eventos aparecem em `audit.evento` com `origem = 'api'` e o usuário do JWT; (4) a mesma decisão com hash antigo devolve erro |
| F4 | login e curadoria na aba `cadeias` do `AdminPage`: selos, filtro "só pendentes", gaveta com fonte × proposta, "editado", "voltar à fonte", pop-up "atualização da fonte" e "excluídas pela fonte" | pelo navegador: confirmar "Capela"; corrigir um campo de um APL; rodar a carga e ver que a pendência não volta e a edição continua; simular a fonte mudando o campo, ver o pop-up e aceitar; simular a fonte excluindo o APL e restaurá-lo |
| F5 | abas `ativos` e `cursos` (depois de C4 e C5); regras do INEP e da BrasilAPI; retenção de 12 meses (rotina que apaga pendências fechadas e linhas de `audit.evento`, `etl.exclusao` e `etl.historico` com mais de 12 meses; depois disso não há mais "restaurar"); depois BNDES, SICONFI, ANATEL e ANEEL | cada regra nova entra com os testes (1) a (4) de F2 |

## 7. Modelo de dados da curadoria: o que é publicado, o que fica guardado

Não há "tabelas velhas" nem cópia de tabela por versão. Cada dado fica em **uma de quatro camadas**. Só a primeira chega ao painel público; as outras ficam no mesmo banco, fora de produção, e o CRUD as lê por views do schema `api`.

| Camada | Tabela | O que guarda | Painel público | CRUD | Retenção |
|---|---|---|---|---|---|
| **Publicado** | `apl.apl`, `apl.apl_municipio` (e `ibge.*`, `inep.*`) | a versão em vigor: a fonte, com as correções da curadoria já aplicadas | sim, pelas views | sim | permanente |
| **Curadoria viva** | `curadoria.pendencia` | linha duvidosa que **não foi publicada**: o "clone" do que chegou (`linha_fonte`), o motivo, a proposta e a decisão | não | sim: selo "Aguardando confirmação", gaveta | abertas: até a decisão; decididas e obsoletas: 12 meses |
| | `curadoria.sobreposicao` | correções vigentes da curadoria, por coluna, com `valor_fonte` e `fonte_atual` | não (o efeito já está no publicado) | sim: "✎ N correções", pop-up "Atualização da fonte" | enquanto a correção valer |
| | `curadoria.de_para_municipio` | nome → município decidido por pessoas | não | sim (histórico da decisão) | permanente |
| **Log** (fora de produção, guardado) | `audit.evento` | toda escrita: linha antes e depois, quem, quando, origem e carga | não | sim: "Ver histórico", data e autor da "Última modificação" | 12 meses |
| | `etl.exclusao` | a linha inteira que a fonte excluiu | não | sim: "Excluídos pela fonte" e "Restaurar" | 12 meses |
| | `etl.historico` | a versão anterior de cada linha que uma carga atualizou | não | sim, dentro do histórico | 12 meses |
| | `etl.execucao` | cada carga: status, escopo e contagens | não | sim: "carga da fonte (execução 41)" | permanente (pequena; as tabelas publicadas apontam para ela) |
| **Transitório** | `stg.*` | o snapshot da carga em curso | não | não | apagado a cada carga |

### 7.1 Onde fica cada tipo de linha

- **Linha pendente de um APL que já existia:** o painel continua com a versão anterior, intacta em `apl.*`. A versão que chegou fica só em `curadoria.pendencia.linha_fonte`. O CRUD mostra as duas lado a lado. Decidida a pendência, a próxima carga publica a nova versão.
- **Linha pendente de um APL novo:** não existe em `apl.*`. Fica só em `linha_fonte`, sem `id_apl`, até a decisão.
- **Linha editada:** está em `apl.*` com o valor da pessoa. A correção (quem, quando, valor da fonte) fica em `curadoria.sobreposicao`, e cada edição fica também em `audit.evento`.
- **Versão antiga de uma linha atualizada pela fonte:** `etl.historico.linha_anterior` e `audit.evento.antes`. Não há tabela de versões: o histórico é uma consulta.
- **Linha excluída pela fonte:** sai de `apl.*` e fica em `etl.exclusao.linha` por 12 meses. As correções dela saem de `curadoria.sobreposicao`, e o que diziam fica em `audit.evento.antes`, com o mesmo `execucao_id` da exclusão. "Restaurar" junta as duas coisas e cria uma sobreposição `incluir`.
- **Decisão já tomada:** `curadoria.pendencia` (`status = 'decidida'`, `decisao`, `justificativa`) e o efeito na tabela de domínio (de-para ou sobreposição).

### 7.2 Views que o CRUD lê (schema `api`, papel `curador`)

| View | Base | Tela do protótipo |
|---|---|---|
| `api.apl` | `apl.apl` + `ultima_alteracao_em/_origem/_por` (último `audit.evento` que mudou valor; §5) + `n_correcoes` + `fonte_mudou` | tabela principal |
| `api.apl_pendente` | `curadoria.pendencia` aberta, com `linha_fonte` × a linha publicada (quando existe) | linhas "Aguardando confirmação" e a gaveta |
| `api.correcao` | `curadoria.sobreposicao` + nome do autor | "✎ N correções" e os campos da gaveta |
| `api.solicitacao_atualizacao` | `curadoria.sobreposicao` onde `fonte_atual IS DISTINCT FROM valor_fonte`, agrupada por `fonte_mudou_execucao` | faixa azul e pop-up "Atualização da fonte" |
| `api.excluido_pela_fonte` | `etl.exclusao` dos últimos 12 meses + correções apagadas na mesma carga (de `audit.evento`) + `guardado_ate = excluido_em + 12 meses` + `restaurado` | filtro "Excluídos pela fonte" |
| `api.historico` | `audit.evento` da linha (por `tabela` e `chave`) dos últimos 12 meses | "Ver histórico completo desta linha" |

O painel público lê **só** as views públicas (`api.apl` sem as colunas de curadoria). As views de curadoria e de log exigem o papel `curador`.

### 7.3 Retenção de 12 meses

- Uma rotina diária (no Hop ou no `cron` da VPS) apaga:
  - de `audit.evento`, `etl.exclusao` e `etl.historico`, o que tem mais de 12 meses;
  - de `curadoria.pendencia`, as decididas e obsoletas com mais de 12 meses.
- A rotina é auditada como `origem = 'etl'` e registra quantas linhas apagou em `etl.execucao` (recurso `retencao`).
- Depois de 12 meses: "Restaurar" deixa de existir para aquela exclusão, e a "Última modificação" usa `_modificado_em` (§5).
- `audit.evento` cresce pouco, porque a detecção em 3 níveis só grava as linhas que mudaram. Particionar por mês fica para quando o volume pedir.

### 7.4 Testes (entram em F1)

1. Pendência de APL existente: o painel (`api.apl`) mostra a versão anterior, e `api.apl_pendente` mostra a nova.
2. `api.excluido_pela_fonte` lista a linha excluída com as correções dela, e "Restaurar" a traz de volta.
3. Retenção com datas fictícias: o que tem mais de 12 meses some das três tabelas de log e das pendências fechadas; nada publicado é apagado.
4. O papel do painel público não lê `curadoria.*`, `audit.*` nem as views de curadoria.

## 8. Perguntas em aberto

1. Quem são os curadores (quantos, que login) e se há aprovação em dois níveis (o plano assume um nível).
2. Login: Supabase Auth enquanto o painel estiver lá, ou login no próprio banco na VPS (§4)? Decidir junto com C4.
3. A edição humana vence a fonte também no IBGE e no INEP, ou só no APL e nas tabelas de curadoria? O plano assume que vale para todas, por coluna.

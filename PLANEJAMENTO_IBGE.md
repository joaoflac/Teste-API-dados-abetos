# Planejamento IBGE — Painel Territorial CT&I

Documento vivo: registra decisões, testes e o desenho das cargas do IBGE para o painel
(repo `territorios_secti`, branch `redesign`). Contexto geral da orquestração em
`orquestracao/PLANO_ORQUESTRACAO_ETL.md`. Atualizar o **Registro de decisões** (§8) a cada mudança.

> **Ver também:** `automacao-hop-postgres/PLANO.md` (INEP, a primeira fonte que consome `ibge.municipio`). Os padrões deste documento (detecção em 3 níveis §7A, rastreabilidade §7B, schemas `meta`/`etl`) valem para todas as fontes.

---

## 1. Papel do IBGE no projeto

- O IBGE é a **base de informações municipais**: tabela-mestre (dimensão município) da Bahia, com 417 municípios.
- Todas as outras fontes (INEP, BNDES, SICONFI, ANATEL, ANEEL) se juntam a ela por `codigo_ibge` (7 dígitos).
- Também fornece os **denominadores** dos indicadores per capita e por km².
- Nenhuma tabela do IBGE tem classificação de CT&I. O IBGE dá contexto, não é indicador de CT&I.

**O que será armazenado:** Censo, estimativas de população, PIB, PIB per capita, VAB, tipologias territoriais e atividades econômicas dominantes.

---

## 2. Conjuntos e canais

| Conjunto | Canal | Endpoint / arquivo | Anos |
|---|---|---|---|
| Localidades (hierarquia territorial) | API | `api/v1/localidades/estados/29/municipios` | atual |
| Malhas (área, centroide, GeoJSON) | API | `api/v3/malhas/estados/29?intrarregiao=municipio` (+ `/metadados`) | atual |
| População estimada | API | agregado **6579**, var 9324 | 2001–2026 (sem anos de Censo e sem 2023) |
| Censo 2022 | API | agregado **4709**, var 93 | 2022 |
| **PIB dos Municípios** (PIB, per capita, VAB, tipologias, atividades) | **FTP** | `ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip` | 2010–2023 |
| PIB pela API (só conferência) | API | agregado **5938**, var 37 | 2002–2023 |

---

## 3. PIB: API × FTP

| Aspecto | API (agregado 5938) | FTP (base TXT) |
|---|---|---|
| Formato | JSON filtrado (só BA, só o que se pede) | ZIP de 7,7 MB: TXT de largura fixa (latin1) e PDF de layout |
| Abrangência | 417 municípios × variáveis × anos pedidos | Brasil: 5.570 municípios × 2010–2023 (77.965 linhas) |
| PIB | ✓ | ✓ |
| PIB per capita municipal | ✗ (a tabela 6784 só tem nível Brasil) | **✓ oficial** |
| VAB por setor | só até 2021 (2022–2023 vêm como `...`) | só até 2021 (2022–2023 em branco) |
| Precisão | arredondado (Salvador 2023: `76698777`) | 3 casas (`76698777.218`) |
| Tipologias territoriais | ✗ | ✓ (§5) |
| Atividades dominantes | ✗ | ✓ 1ª, 2ª e 3ª atividades por VAB (§6) |
| Detectar mudança | sem ETag; `/agregados/5938/periodos` → `modificacao` por ano | ETag, Last-Modified e 304 |
| Edição nova | mesma URL | **pasta nova** (`2022_2023/` → `2023_2024/`), é preciso descobrir |
| Fragilidade | estável | leitor depende das posições do layout |
| Carga | ETL | ELT (arquivo → staging → transformação no banco) |

**Decisão:** o FTP é a fonte principal do PIB. A API 5938 serve de conferência automática: a soma do PIB da BA tem de coincidir nos dois canais. Em 19/11/2026 coincide: R$ 430,99 bi em 2023.

### Notas oficiais do layout (PDF dentro do ZIP)

1. **2022 e 2023 são provisórios** e serão revisados na próxima publicação. A carga precisa tratar *atualização*, não só inclusão.
2. **2022–2023 têm só PIB e PIB per capita** (nota técnica 02/2024 do SCN). Não há VAB nem atividades.
3. **A população do PIB per capita não é a da 6579:**
   - 2010–2021: estimativa enviada ao TCU;
   - 2022: Censo (primeira apuração);
   - 2023: lista de população enviada ao TCU em 2023.

   Por isso **usar sempre o per capita oficial** e nunca recalcular PIB ÷ 6579.
4. Unidades: valores em **R$ 1.000**; per capita em **R$ 1,00**.

### Layout do TXT (posição inicial 1-based, tamanho)

| Pos | Tam | Campo | Pos | Tam | Campo |
|---:|---:|---|---:|---:|---|
| 1 | 4 | Ano | 517 | 7 | Cód. arranjo populacional |
| 6 | 1 | Cód. grande região | 525 | 86 | Nome arranjo populacional |
| 8 | 12 | Nome grande região | 612 | 32 | Hierarquia urbana |
| 21 | 2 | Cód. UF | 645 | 19 | Hierarquia urbana (principais categorias) |
| 24 | 2 | Sigla UF | 665 | 4 | Cód. região rural |
| 27 | 19 | Nome UF | 670 | 91 | Nome região rural |
| 47 | 7 | **Cód. município** | 762 | 43 | Região rural (classificação do núcleo) |
| 55 | 40 | Nome município | 806 | 4 | Amazônia Legal |
| 96 | 86 | Região metropolitana | 811 | 4 | Semiárido |
| 183 | 4 | Cód. mesorregião | 816 | 4 | Cidade-Região de SP |
| 188 | 40 | Nome mesorregião | 821 | 18.3 | VAB agropecuária |
| 229 | 5 | Cód. microrregião | 840 | 18.3 | VAB indústria |
| 235 | 40 | Nome microrregião | 859 | 18.3 | VAB serviços (exceto adm. pública) |
| 276 | 6 | Cód. região imediata | 878 | 18.3 | VAB administração pública |
| 283 | 66 | Nome região imediata | 897 | 18.3 | VAB total |
| 350 | 10 | Município da RGI (Polo/Entorno) | 916 | 18.3 | Impostos líquidos de subsídios |
| 361 | 4 | Cód. região intermediária | 935 | 18.3 | **PIB** |
| 366 | 35 | Nome região intermediária | 954 | 18.2 | **PIB per capita** |
| 402 | 10 | Município da RGInt (Polo/Entorno) | 973 | 94 | Atividade com maior VAB |
| 413 | 7 | Cód. concentração urbana | 1068 | 94 | 2ª atividade |
| 421 | 67 | Nome concentração urbana | 1163 | 94 | 3ª atividade |
| 489 | 27 | Tipo concentração urbana | | | |

O leitor atual (`scripts/ibge_pib_per_capita_oficial.py`) só extrai código, PIB e per capita. Ele precisa ser ampliado para ler o layout inteiro.

---

## 4. Outras ressalvas de dados

- **VAB municipal só até 2021**, nos dois canais. A amostra `amostras/ibge_2.2_pib_vab_5938_BA.csv` tem VAB vazio por isso. A base municipal (`base/ibge_base_municipal_BA.csv`) usa o VAB de 2021.
- **6579 não cobre anos de Censo nem 2023.** 2022 vem do agregado 4709.
- **Densidade demográfica** usa a população mais recente da 6579 (2026), e o PIB/km² usa o PIB de 2023. Os anos são diferentes de propósito, e isso precisa ficar documentado no painel.

---

## 5. Tipologias territoriais (FTP, BA, 2023)

São **fixas por município**: nenhum dos 417 municípios muda de valor entre 2010 e 2023 no arquivo. É a classificação vigente aplicada a todos os anos. Vão para a dimensão `ibge.municipio`, **sem ano**.

| Tipologia | Valores na BA |
|---|---|
| **Semiárido** | Sim **287** · Não 130 |
| **Hierarquia urbana** (8) | Centro Local 339 · Centro de Zona B 28 · Centro Sub-Regional B 14 · Centro de Zona A 10 · Metrópole 10 · Centro Sub-Regional A 9 · Capital Regional C 4 · Capital Regional B 3 |
| **Hierarquia urbana — principais** (5) | Centro Local 339 · Centro de Zona 38 · Centro Sub-Regional 23 · Metrópole 10 · Capital Regional 7 |
| **Região rural** (11) | Metrópole de Salvador 167 · CR Vitória da Conquista 69 · CR Ilhéus 50 · CSR Guanambi 24 · CSR Teixeira de Freitas 24 · CR Barreiras 21 · CSR Irecê 19 · CSR Bom Jesus da Lapa 19 · … |
| **Região rural (núcleo)** | de Metrópole 167 · de Capital Regional 149 · de Centro Sub-regional 101 |
| **Região metropolitana** | — 384 · RM Salvador 13 · Área de Expansão Metropolitana 10 · RM Feira de Santana 6 · RIDE Petrolina/Juazeiro 4 |
| **Concentração urbana** (14) | — 395 · Salvador/BA 10 municípios · Alagoinhas, Barreiras, Eunápolis, Feira de Santana, Ilhéus, Itabuna… |
| **Tipo de concentração urbana** | — 395 · Média 12 · Grande 10 |
| **Arranjo populacional** | agrupamentos de municípios integrados (ex.: Salvador/BA) |
| **Polo/Entorno da região imediata** | Polo 38 · do Entorno 379 |
| **Polo/Entorno da região intermediária** | Polo 9 · do Entorno 408 |
| **Amazônia Legal** | Não 417 (sem uso na BA) |

**Uso no painel:** filtros e recortes, por exemplo Semiárido × não Semiárido, polos × entorno, comparação por nível da hierarquia urbana.

---

## 6. Atividades econômicas dominantes (FTP, BA, 2021)

São as 1ª, 2ª e 3ª atividades com maior VAB no município. **Variam por ano e existem só até 2021**: 2022–2023 vêm em branco.
O IBGE usa 10 classes agregadas. "Demais serviços" junta transporte, alojamento, **informação e comunicação**, finanças, imobiliárias, **atividades profissionais, científicas e técnicas**, educação e saúde privadas, artes etc.

| Atividade | 1ª | 2ª | 3ª |
|---|---:|---:|---:|
| Administração, defesa, educação e saúde públicas e seguridade social | **290** | 80 | 33 |
| Demais serviços | 59 | **266** | 87 |
| Agricultura, inclusive apoio e pós-colheita | 25 | 17 | 78 |
| Pecuária, inclusive apoio | 11 | 24 | **96** |
| Eletricidade, gás, água, esgoto e resíduos | 11 | 6 | 1 |
| Indústrias de transformação | 10 | 8 | 16 |
| Indústrias extrativas | 6 | 3 | 11 |
| Comércio e reparação de veículos | 3 | 11 | 86 |
| Produção florestal, pesca e aquicultura | 2 | — | 7 |
| Construção | — | 2 | 2 |

**Leitura:** em **70% dos municípios** baianos a principal atividade é a administração pública. Serve como **perfil econômico** do município, **não como indicador de CT&I**, porque as classes são agregadas demais.

---

## 7. Modelo de armazenamento (PostgreSQL)

| Tabela | Conteúdo | Chave | Origem |
|---|---|---|---|
| `ibge.municipio` (dimensão) | identificação; meso/micro; regiões imediata e intermediária (com Polo/Entorno); área; centroide; **todas as tipologias do §5** | `codigo_ibge` | localidades + malhas + FTP |
| `ibge.populacao` | estimativas e Censo; coluna `tipo` ∈ {`estimativa`, `censo`} | `codigo_ibge, ano, tipo` | 6579 + 4709 |
| `ibge.pib_municipal` | PIB, **PIB per capita oficial**, VAB por setor, impostos, 1ª/2ª/3ª atividades; `provisorio` = true para 2022–2023 | `codigo_ibge, ano` | FTP |
| `ibge.malha` | geometria (GeoJSON → PostGIS, se adotado) | `codigo_ibge` | malhas |

Todas as tabelas levam as colunas de controle `_hash`, `_carregado_em`, `_atualizado_em` e `_execucao_id`. A carga usa o padrão MERGE com exclusão limitada ao escopo, descrito em `orquestracao/sql/02_carga_incremental.sql`.

### Metadados: o que cada canal oferece (testado em 19/11/2026)

| Canal | Metadado disponível | Formato | O que traz |
|---|---|---|---|
| Agregados (6579, 4709, 5938) | `GET /api/v3/agregados/{id}/metadados` | JSON | `nome`, `URL` (SIDRA), `pesquisa`, `assunto`, `periodicidade` (`inicio`/`fim`), `nivelTerritorial`, **`variaveis[]` (`id`, `nome`, `unidade`, `sumarizacao`)**, `classificacoes[]` |
| Agregados | `GET /api/v3/agregados/{id}/periodos` | JSON | `id` do período e **`modificacao`** (data da última alteração) |
| Pesquisas | `GET /api/v2/metadados/pesquisas` | JSON | código da pesquisa (PIB dos Municípios = `IO`), situação, periodicidade de coleta e divulgação, classificação temática e descrição |
| Localidades | sem endpoint de metadados | JSON | a estrutura é fixa e autoexplicativa (`id`/`nome` aninhados: microrregião → mesorregião → UF; região imediata → intermediária) |
| Malhas | `GET /api/v3/malhas/.../metadados` | JSON | área (`dimensao`, unidade), centroide, `id` |
| FTP PIB | **PDF de layout dentro do ZIP** | PDF (não legível por máquina) | posição, tamanho, tipo e nome de cada campo, notas e unidades (§3) |

#### Campos fixos de atualização (data)

| Canal | Campo de data? | Campo / formato |
|---|---|---|
| `/agregados/{id}/periodos` | **Sim**: o único campo fixo de atualização dos dados | `modificacao`, `dd/mm/aaaa`, por período |
| `/agregados/{id}/metadados` | Não | só `periodicidade.fim` (último ano disponível), usado como sinal indireto |
| `/api/v2/metadados/pesquisas` | Não | situação e periodicidade, sem data |
| `/malhas/.../metadados` | Não | sem data, sem ETag; usar hash do corpo |
| Localidades | Não | sem data; usar hash do corpo |
| FTP | Não no conteúdo | só os cabeçalhos HTTP `Last-Modified` e `ETag` |
| **`/api/v3/calendario`** | **Sim**: datas **futuras e passadas** de divulgação | `data_divulgacao` (`dd/mm/aaaa hh:mm:ss`), `produto_id`, `titulo`, `ano_referencia_*` |

O **calendário confere com as datas de modificação**:

| Produto (`produto_id`) | Divulgação no calendário | `modificacao` no agregado |
|---|---|---|
| Estimativas da População (**9103**) | 28/08/2026 (ref. 2026) | 6579 → 2025 e 2026: 28/08/2026 |
| PIB dos Municípios 2022-2023 (**9088**) | 19/12/2025 | 5938 → 2021 a 2023: 19/12/2025 |
| Censo Demográfico 2022 (**22827**) | várias divulgações temáticas | 4709 → 2022: 22/12/2023 |

Até 2027, o calendário ainda não lista a próxima edição do PIB dos Municípios. Endpoint por produto: `/api/v3/calendario/{produto_id}`.

**Uso na orquestração:** o calendário vira o agendador.
- Fora das datas de divulgação, o verificador roda em frequência baixa (semanal).
- Na data de divulgação de um produto, roda em frequência alta (de hora em hora no dia) até a `modificacao` ou o ETag mudar.
- Assim a carga entra no ar no mesmo dia da divulgação, sem consultas diárias o ano todo.

Achado: o agregado **4709** tem mais duas variáveis úteis, além da 93 (população):
- **5936**: variação absoluta da população desde 2010 (compatibilizada);
- **10605**: taxa de crescimento geométrico (%).

### Armazenamento dos metadados (schema `meta`)

| Tabela | Conteúdo | Origem |
|---|---|---|
| `meta.fonte_tabela` | uma linha por agregado/arquivo: id, nome, pesquisa, URL, periodicidade, níveis, **JSON bruto do `/metadados`** e `_hash` | `/metadados` (API); FTP: URL da edição e ETag |
| `meta.variavel` | `fonte`, `tabela`, `variavel_id`, `nome`, `unidade` | `variaveis[]` do `/metadados` |
| `meta.periodo` | `tabela`, `periodo`, `modificacao` | `/periodos` (é o próprio checkpoint de mudança) |
| `meta.layout_ftp` | `edicao`, `posicao`, `tamanho`, `tipo`, `campo`, `unidade`, `coluna_destino` | transcrição do PDF (§3), versionada por edição |
| `meta.dicionario` | `tabela_destino`, `coluna`, `descricao`, `unidade`, `origem`, `variavel_id`, `notas` | gerado na carga: é o que o painel mostra em "sobre o dado" |

Regras:
- **A unidade e o nome vêm do metadado, não do código.** Exemplo: a amostra 2.2 tinha `unidade` vazia para o VAB, mas o `/metadados` da 5938 informa `Mil Reais`.
- **Mudança de metadado também é mudança.** O `_hash` do `/metadados` entra no verificador; variável nova, unidade alterada ou `periodicidade.fim` avançando disparam alerta e recarga.
- **Layout do FTP:** como o PDF não é legível por máquina, a carga confere o layout transcrito antes de usar:
  - tamanho da linha = 1.256;
  - código do município numérico na posição 47;
  - soma do PIB da BA igual à da API 5938.

  Se alguma conferência falhar, a carga é abortada sem alterar as tabelas finais.

### Detecção de mudança e escopo

| Conjunto | Identificador | Escopo da recarga |
|---|---|---|
| Localidades, malhas | SHA-256 do corpo | recurso inteiro |
| 6579, 4709 | `/periodos` → `modificacao` | só os anos com data alterada |
| FTP PIB | ETag / Last-Modified (HEAD) e verificação da pasta da edição seguinte | anos presentes no arquivo; 2022–2023 são **atualizados** quando revisados |
| 5938 (conferência) | `/periodos` → `modificacao` | dispara a conferência da soma do PIB |

---

## 7A. Atualização incremental: o Hop nunca baixa e substitui tudo

**Restrição das fontes:** nenhuma fonte oficial informa *qual linha* mudou. Não existe feed de alterações por registro. O que existe é um sinal por **conjunto** (ETag, hash do CKAN) ou por **partição** (`modificacao` de cada ano no IBGE, `data_status` de cada município no SICONFI, CRC de cada CSV dentro do ZIP da ANATEL).
Por isso a detecção é feita em **três níveis**, cada um mais caro que o anterior, e só se passa ao seguinte quando o anterior acusa mudança.

| Nível | Pergunta | Como | Custo | Se não mudou |
|---|---|---|---|---|
| **1. Conjunto** | O dataset mudou? | `/periodos`, ETag/HEAD, hash do CKAN, hash do `/metadados` | 1 requisição, poucos KB, < 1 s | **para aqui**: nada é baixado |
| **2. Partição** | Qual parte mudou? | o mesmo sinal do nível 1, comparado item a item (ano, município, arquivo interno) | zero (já veio no nível 1) | baixa **só** a partição alterada |
| **3. Linha** | Quais linhas mudaram? | hash de cada linha da partição baixada, comparado com o `_hash` gravado | proporcional à partição, não ao dataset | grava **só** as linhas diferentes |

Dentro do nível 3 há um atalho: se o **hash da partição inteira** (ordenada) for igual ao da última carga, nem o MERGE roda.

### O que o nível 3 faz com cada linha

O nível 3 **substitui no lugar**. Uma linha alterada recebe `UPDATE`: mantém a chave e só troca os valores. Nenhuma linha nova é criada ao lado da antiga.

| Situação da linha | Ação | `_criado_em` | `_modificado_em` |
|---|---|---|---|
| Igual (mesmo `_hash`) | **nada**, nem é regravada | mantém | mantém |
| Mudou (mesma chave, `_hash` diferente) | **`UPDATE`**: substitui os valores daquela linha | mantém | data da carga |
| Chave nova | `INSERT` | data da carga | data da carga |
| Sumiu da fonte (dentro da partição baixada) | `DELETE` só dela, auditado em `etl.exclusao` | — | — |

- **Valor anterior:** antes do `UPDATE`, a versão antiga é copiada para `etl.historico` (§7B), o que permite consultar, por exemplo, o PIB 2022 antes da revisão do IBGE. Sem essa tabela, o `UPDATE` apenas sobrescreve.
- **Tabelas sem chave natural** (ex.: BNDES, identidade = `_hash` + `_ocorrencia`): uma linha alterada vira `DELETE` da versão antiga e `INSERT` da nova. Para quem consulta, o efeito é o mesmo, e só essa linha é tocada.
- **Postgres (MVCC):** internamente, todo `UPDATE` grava uma nova versão física da linha e o autovacuum limpa a antiga. Para a API é a mesma linha. Pular as linhas iguais evita escrita, WAL e vacuum desnecessários.

### Exemplo: o IBGE revisou 2 municípios da estimativa de 2025

1. **Nível 1:** `GET /agregados/6579/periodos` (cerca de 1 KB) mostra que só o período `2025` tem `modificacao` nova.
2. **Nível 2:** baixa só 2025 da BA: `/agregados/6579/periodos/2025/variaveis/9324?localidades=N6[N3[29]]`, 417 valores, cerca de 30 KB. Os outros 25 anos não são baixados.
3. **Nível 3:** na staging, 417 hashes são comparados com os gravados. Resultado: **2 UPDATE, 0 INSERT, 0 DELETE**. As outras 415 linhas não são reescritas, e o `_modificado_em` delas não muda.

### Exemplo: nova edição do FTP do PIB

1. **Nível 1:** o ETag do ZIP mudou, ou apareceu a pasta da edição nova.
2. **Nível 2:** o arquivo é um só (7,7 MB), então o download é inteiro. É inevitável e acontece uma vez por edição. O escopo da carga continua limitado à BA.
3. **Nível 3:** a revisão de 2022–2023 vira UPDATE só nos municípios cujos valores mudaram. 2010–2021 só é tocado se o IBGE tiver mexido nesses anos.

### Como o Hop executa cada nível

| Nível | Implementação |
|---|---|
| 1 e 2 | Passo 0 (`scripts/etl_verificar_mudanca.py`, chamado pelo Hop com a action *Shell*, ou reescrito com `HTTP Client` + `JSON Input`). Devolve a lista de partições alteradas. Lista vazia encerra o workflow. |
| Download | O workflow percorre só as partições da lista (*Repeat*/*Loop*), passando ano, município ou arquivo como parâmetro do pipeline. |
| 3 (no banco, **recomendado**) | `Table Output` para `stg.*` e depois `SQL` chamando `etl.carga_*()`, que faz o MERGE com hash (`orquestracao/sql/02_carga_incremental.sql`). É uma operação em lote dentro do Postgres, a mais rápida. |
| 3 (no Hop, alternativa) | Transform **Merge rows (diff)**, que compara o fluxo novo com o da tabela pela chave e marca cada linha como `identical`/`changed`/`new`/`deleted`. Depois, **Synchronize after merge** aplica só INSERT, UPDATE e DELETE. Serve para fontes pequenas ou quando se quer a regra visível no pipeline. |

---

## 7B. Rastreabilidade: fonte e data de atualização por linha

**Recomendação:** combinar as duas ideias.
1. **Poucas colunas de controle em cada tabela de dados.** Assim cada linha diz *quando* mudou.
2. **Um catálogo separado.** Ele diz *de onde* veio e *em que condições*, sem repetir URL e fonte em milhões de linhas.

### Colunas em cada tabela de dados

| Coluna | Significado |
|---|---|
| `_hash` | MD5 do conteúdo da linha (base do nível 3) |
| `_criado_em` | quando a linha entrou no banco |
| `_modificado_em` | quando o **conteúdo** mudou pela última vez. Só muda se o `_hash` mudar; recarregar o mesmo valor não altera a data |
| `_modificado_fonte_em` | quando **a fonte** alterou o dado, se ela informar: IBGE `modificacao` do período, SICONFI `data_status`, CKAN `last_modified` |
| `_execucao_id` | a carga que gravou a versão atual, ligada a `etl.execucao` e ao catálogo |

Com isso, uma consulta por linha responde: valor, fonte, data em que a fonte mudou, data em que o banco mudou e qual carga fez a mudança.

### Catálogo de fontes e atualizações (schemas `meta` e `etl`)

Fica no **mesmo banco** PostgreSQL, em schemas separados. Bancos separados no Postgres não fazem JOIN direto (exigem `dblink`/FDW), e o painel precisa cruzar linha com fonte.

| Objeto | Conteúdo |
|---|---|
| `meta.fonte_tabela` | fonte, tabela de origem (agregado/arquivo), URL, periodicidade, JSON bruto do `/metadados` (§7) |
| `etl.execucao` | cada carga: início, fim, status, escopo (anos/municípios), identificador da fonte no momento (ETag, `modificacao`, hash), contagens de inseridos/alterados/excluídos |
| `etl.historico` | versão **anterior** de cada linha alterada (chave, conteúdo antigo, execução). Permite ver o valor antes da revisão do IBGE |
| `etl.exclusao` | linhas excluídas, com conteúdo e execução (já existe em `01_controle.sql`) |
| `meta.v_status_dataset` (view) | uma linha por tabela do painel: fonte, data oficial de divulgação (calendário), última `modificacao` da fonte, última carga, próxima divulgação prevista, linhas alteradas na última carga |
| `meta.v_linha_origem` (view) | junta qualquer linha (`_execucao_id`) à execução e à fonte, para a API do painel devolver a "procedência" de um dado |

**API do painel (sugestão):**
- `GET /fontes`: lê `meta.v_status_dataset`, para a tela "fontes e atualização".
- Cada endpoint de dados devolve, por registro, `_modificado_em` e `_modificado_fonte_em`.
- `GET /origem/{tabela}/{chave}`: procedência completa de um dado.

---

## 7C. Origem do dado, auditoria e chaves estrangeiras (implementado em 24/11)

SQL: `orquestracao/sql/04_fk_ibge.sql` e `05_auditoria.sql`. Testes: `orquestracao/testes/05_teste_auditoria.sql` (e `03_`, ajustado).

**Dois escritores.** O ETL (Python que simula o Hop) e a API de CRUD do painel. O banco não adivinha quem escreve: o escritor declara o contexto **no início da transação**.

| Quem | Como declara | `_origem` na linha |
|---|---|---|
| ETL | conexão aberta com `options='-c app.origem=etl -c app.usuario=orquestrador_simulado'`; `app.execucao_id` por carga | `etl` |
| API | em cada requisição, **dentro da mesma transação do CRUD**: `SELECT audit.contexto('api', '<usuario>', '<request_id>')` (vale só até o `COMMIT`, indispensável com pool de conexões) | `api` |
| Qualquer outro (psql, migração, API que esqueceu o contexto) | nada | `direto_sql`, visível e nunca silencioso |

**O que fica registrado**
- **Na linha** (4 tabelas `ibge.*`): `_criado_origem` (como entrou, não muda mais), `_origem` e `_modificado_por` (última alteração). Linhas anteriores à auditoria ficaram como `etl`, porque o orquestrador era o único escritor.
- **No log `audit.evento`**: um registro por INSERT/UPDATE/DELETE, com `antes`, `depois`, `campos_alterados`, `origem`, `usuario`, `request_id`, `execucao_id`, papel do banco, IP e aplicação. UPDATE que não muda nenhum valor não gera evento.
- **Na carga** (`etl.execucao`): `disparo` (`agendado` | `manual` | `forcado`; o orquestrador lê `ETL_DISPARO`), `usuario` e `host`.
- `meta.v_linha_origem` passou a mostrar `_criado_origem`, `_origem`, `_modificado_por` e `carga_disparo`.

**Log como schema, não como banco separado.** O trigger grava na mesma transação do dado (se o dado sofre rollback, o log também) e o painel cruza linha e log com JOIN. Banco separado exigiria `dblink` e perderia as duas garantias.

**Papel da API.** `api_crud` (sem LOGIN no repositório) lê e escreve nos dados e lê o log; não é dono das tabelas, então não consegue `DISABLE TRIGGER` nem alterar `audit.evento` (testado). Dono e superusuário conseguem: no Postgres portátil de teste o usuário `etl` é superusuário, então o teste prova o mecanismo, não a proteção.

**Conflito entre API e ETL (decisão a confirmar): a fonte vence.** Uma linha alterada pela API recebe `_hash = 'api:...'`, nunca igual ao da fonte. O próximo MERGE que cobrir aquela partição a sobrescreve, e a versão da API fica em `audit.evento` e `etl.historico`. Mas a edição **não é desfeita na hora**: com a detecção em 3 níveis, o ETL só toca a partição quando a fonte muda (ex.: o PIB 2015 editado pela API fica assim até o IBGE republicar o arquivo). Uma linha **inserida** pela API dentro de um escopo recarregado é excluída pelo MERGE e pode acionar a trava de exclusão em massa. Se a SECTI precisar de correções manuais permanentes, falta um campo de bloqueio (`_bloqueado_etl`) ou uma tabela de sobreposições.

**Chaves estrangeiras.**
- `populacao`, `pib_municipal` e `malha` → `ibge.municipio(codigo_ibge)`; `_execucao_id` das quatro tabelas → `etl.execucao(id)`. Sem linhas órfãs na carga atual.
- **Ordem de carga:** `ibge.municipio` vem antes das filhas (o orquestrador foi reordenado; num banco vazio a ordem antiga violaria a FK).
- O ETL não consegue mais excluir um município que tenha filhas (`RESTRICT`): a carga aborta com rollback, o que exige decisão humana.
- Continuam relações lógicas, sem FK possível: `etl.recurso.tabela_destino`, `parametros->>'fonte_tabela'` (jsonb), `pib_municipal.edicao` → `meta.layout_ftp` e `etl.exclusao`/`etl.historico` (tabela + chave genéricas).
- Tabelas novas (INEP) ganham a auditoria com `SELECT audit.ativar('inep.curso', '{co_curso}')` e FKs para `ibge.municipio` no próprio DDL.

**Limites conhecidos.** `etl.historico` e `etl.exclusao` repetem parte do que `audit.evento` guarda para escritas do ETL (mantido de propósito: não mexi em `merge_tabela`). `audit.evento` não tem retenção nem partição. O trigger não cobre `TRUNCATE`. As tabelas `stg.*` não são auditadas.

---

## 7D. INEP: dimensões estáveis, fato por ano e "ativo" derivado (implementado em 24/11)

SQL: `orquestracao/sql/06_inep_modelo.sql`. Carga: `orquestracao/orquestrador_inep.py`. Teste: `orquestracao/testes/06_teste_inep.sql`. Plano do INEP: `automacao-hop-postgres/PLANO.md` §0.

**Decisão: o INEP não usa soft delete.** O plano de 13/11 mandava `ativo = false`; a análise do Opus, medida num banco descartável, mostrou por que não:
- Consulta que esquece `ativo` erra em silêncio (547 contra 347 cursos; 34 municípios com contagem errada; 132 contra 115 campi).
- A trava de exclusão em massa não pega desativação (200 de 547 cursos desativados sem aviso).
- Um curso que volta ao censo não era reativado; e a edição da curadoria era desfeita pela recarga.
- A desativação não aparece em `etl.exclusao` nem em `etl.historico`.
- **O escopo "ano do censo" não funcionava com chave sem ano**, nem no soft nem no hard delete (3 cursos sumiram e 0 foram tratados).

**Desenho**

| Peça | Tabelas | Carga |
|---|---|---|
| Dimensões, nunca apagadas | `inep.ies`, `ies_local` (campus = par IES + município), `curso`, `cine_classificacao` | `etl.merge_tabela(..., p_excluir => false)`: só INSERT e UPDATE |
| Fato por ano | `inep.curso_censo (co_curso, ano)` com vagas, ingressantes, matrículas, concluintes e o rótulo CINE do ano | MERGE com exclusão só do ano carregado, auditada, trava de **20%** |
| Regra da SECTI | `inep.regra_cti` (`incluir` / `excluir` / `revisar`) | semente do CSV só para rótulos sem regra; depois é curada pela API |
| Leitura | `inep.v_curso_atual`, `inep.v_campus_com_curso` | embutem o "ativo": censo vigente, regra `incluir`, sede na BA, não oculto |

- **Censo vigente** = maior ano com carga `ok` em `etl.execucao`, não `max(ano)`: uma carga parcial ou com erro de um censo novo nunca passa a valer.
- **Curadoria:** `curso.oculto_curadoria` fica fora do `_hash` e fora das colunas de valor do MERGE; o ETL nunca a toca (testado com `--forcar` sobre 2024).
- **Filtro CT&I na view, não na carga:** `curso` guarda o universo das áreas 05 a 09 (935 cursos em 2024). Mudar `regra_cti` vale na hora (rótulo `0714E04` para `excluir`: 547 para 533).
- **A API não lê as tabelas-base:** `api_crud` lê as views, edita `regra_cti` e só altera `oculto_curadoria` e `motivo_oculto` em `curso`.

**Medido com os censos reais (BA, presencial, `QT_CURSO = 1`, 2021 a 2024)**

| Transição | Permanecem | Saíram | Novos | Mesmo nome / município / grau | Mudaram de IES | Mudaram de rótulo |
|---|---:|---:|---:|---|---:|---:|
| 2021 → 2022 | 1.923 (97,8%) | 44 | 107 | 100% | 0 | 1 |
| 2022 → 2023 | 1.891 (93,2%) | 139 | 87 | 100% | **33** | 4 |
| 2023 → 2024 | 1.775 (89,7%) | 203 | 59 | nome 9 mudaram | 0 | **67** |

`CO_CURSO` nunca se repetiu dentro de um ano e identifica o mesmo curso entre anos. Mas **atributos mudam**: 33 cursos trocaram de IES (por isso `curso.co_ies` reflete o último censo) e o rótulo muda por ano (por isso ele fica em `curso_censo`). Saem do censo 2,2%, 7,0% e 10,3% dos cursos por ano (áreas 05-09: 1,7%, 6,9% e 9,0%), o que obrigou a trava de 10% do IBGE a virar 20% no INEP. 17 códigos somem e voltam.

**Resultado da carga real (banco do zero):** funil 720.349 → 40.715 (UF 29) → 1.851 (presencial) → 1.834 (`QT_CURSO = 1`, 17 ABI fora) → 552 (rótulo `incluir`) → **547** (sede na BA); 144 IES e 216 campi; a view, com `exigir_sede_ba = true` (como na simulação de 13/11), devolve exatamente os 547 cursos e os 132 campi. Com a UNIVASF permanecendo (`false`, decisão de 24/11) são 552 cursos e 133 campi.

**Tipos de curso × Supabase do painel:** os 5 de `tipo_cursos` têm o mesmo nome das áreas CINE 05 a 09. Dos 550 presenciais do Supabase, 542 casam com os 547 por (curso, município), todos com o mesmo tipo. Os 8 restantes: 5 cursos do UNIMAM (Supabase: Governador Mangabeira; INEP: Cruz das Almas) e 3 de rótulos `revisar` (Geologia em Barreiras e Salvador, Engenharia Agrícola e Ambiental em Itabuna). **Decisões de 24/11:** (1) a **UNIVASF permanece** (sede em PE, campus na BA): `exigir_sede_ba = false`, então a view tem 552 cursos e 133 campi; (2) o **dataset cru do INEP manda** em município, IES e curso (os 5 cursos do UNIMAM ficam em Cruz das Almas); o Supabase é só referência de comparação, não fonte; (3) os 6 rótulos `revisar` (10 cursos, 765 matrículas em 2024) **ficam fora da view** até a SECTI decidir.

**Incertezas que continuam**
- Só há 4 censos: o comportamento de `CO_CURSO` no censo 2025 é desconhecido.
- EAD não foi testado (fora do escopo).
- **Colunas do INEP:** as 30 colunas que o orquestrador lê (20 de cursos, 10 de IES) existem nos censos 2021 a 2024, com os mesmos domínios de valores (modalidade 1/2, rede 1/2, grau 1/2/3, `QT_CURSO` 0/1). O que muda: o arquivo de cursos foi de 200 para 223 colunas (as novas são cotas, não usadas), `CO_CINE_ROTULO` chega sempre com aspas literais, e o grau das ABI é vazio em 2021, 2023 e 2024 mas `0` em 2022 (por isso a ABI se identifica por `QT_CURSO = 0`, não pelo grau). O orquestrador aborta se uma coluna usada sumir.
- Um curso que muda de IES entre censos reaparece em outro campus, e os números de anos anteriores continuam ligados ao `co_curso`, não ao campus antigo.
- O recurso é por ano (`inep_censo_superior_<ano>`): `meta.v_status_dataset` mostra uma linha por censo carregado.

---

## 8. Registro de decisões

| Data | Decisão |
|---|---|
| 2026-10-07 | PIB per capita 2023 vem da base TXT oficial do FTP (a tabela 6784 só tem nível Brasil). |
| 2026-11-19 | IBGE é a base de informações municipais (tabela-mestre). Primeira versão: `scripts/ibge_base_municipal.py` → `base/ibge_base_municipal_BA.csv`. |
| 2026-11-19 | VAB municipal só existe até 2021; a base usa VAB de 2021. |
| 2026-11-19 | Identificadores de mudança testados. IBGE API: data de modificação por período; FTP: ETag e 304. |
| 2026-11-19 | Armazenar Censo, PIB e PIB per capita. **FTP é a fonte principal do PIB**; a API 5938 serve de conferência. |
| 2026-11-19 | Tipologias (fixas) vão para `ibge.municipio`; atividades dominantes (por ano, até 2021) vão para `ibge.pib_municipal`. |
| 2026-11-19 | Metadados guardados no schema `meta`: JSON bruto do `/metadados` com hash, variáveis e unidades, datas por período, layout do FTP versionado e dicionário de colunas. Mudança de metadado dispara alerta e recarga. |
| 2026-11-19 | Único campo fixo de atualização dos dados: `modificacao` em `/periodos`. O calendário IBGE (`/api/v3/calendario`, produtos 9103, 9088 e 22827) agenda o verificador nas datas de divulgação. |
| 2026-11-19 | Detecção em 3 níveis (conjunto → partição → linha). O Hop nunca baixa e substitui tudo: baixa só a partição alterada e grava só as linhas com `_hash` diferente. MERGE no Postgres é o padrão; Merge rows (diff) + Synchronize after merge é a alternativa no Hop. |
| 2026-11-19 | Rastreabilidade: colunas `_hash`, `_criado_em`, `_modificado_em`, `_modificado_fonte_em` e `_execucao_id` em toda tabela, mais o catálogo `meta`/`etl` no mesmo banco (views `v_status_dataset` e `v_linha_origem`, tabela `etl.historico`). |
| 2026-11-19 | **Testado em Postgres 17.6 real** (portátil, porta 5433) com o orquestrador `orquestracao/orquestrador_simulado.py`, que simula o Hop com dados reais do IBGE. Carga inicial: 6579 (22 períodos, 9.174 valores) e 4709 (417), 3 s. Sem mudança: 0,8 s, nada baixado. Revisão simulada de 2025: baixou só 2025 (50 KB), 2 UPDATE, 1 INSERT e 1 DELETE; demais anos intocados. SQL alinhado ao §7B (`tipo`, `_criado_em`, `_modificado_em`, `_modificado_fonte_em`, `etl.historico`, `etl.v_status`). |
| 2026-11-19 | Postgres portátil movido para **dentro do repo** (`pg-portatil/`). No git: scripts e `backup/painel.sql` (SQL texto, cerca de 3,8 MB, restauração testada). Fora do git: binários (recriados com `pg.ps1 instalar`), `data/` e senha. |
| 2026-11-19 | **Todo o armazenamento sugerido está carregado** (`orquestracao/sql/03_ibge_modelo.sql` + orquestrador): `ibge.municipio` 417 (com tipologias), `ibge.populacao` 9.591, `ibge.pib_municipal` 5.838 (2010–2023), `ibge.malha` 417, `meta.*` (6 fontes, 50 variáveis, 45 períodos, 54 eventos do calendário, 43 campos de layout), views `meta.v_status_dataset`, `meta.v_linha_origem` e `meta.v_dicionario` (descrições via `COMMENT ON`). |
| 2026-11-19 | **Incidente e trava:** o teste sintético usava anos e códigos reais e, pela exclusão por escopo, apagou as estimativas reais de 2024/2025 (reparadas pelo orquestrador em 1 rodada). Correções: (1) teste isolado em anos/códigos fictícios; (2) **trava de exclusão em massa** nas funções de carga: mais de 10 exclusões e acima de 10% do escopo abortam a carga com rollback. Protege também contra API que devolva dados incompletos. Testada: barrou 414/417 e 412/417. |
| 2026-11-19 | Graphify instalado (grafo de conhecimento do repo para economizar tokens). Extração semântica dos .md pendente: `/graphify .`. |
| 2026-11-24 | **Reconciliação com o plano do INEP** (`automacao-hop-postgres/PLANO.md`, feito em outra máquina em 13/11): `ibge.municipio` é a dimensão de município do INEP (FK de `ies_local` e `curso`; filtro dos 417 códigos lê dela); o INEP segue os schemas `etl`/`stg`/`meta` e terá schema `inep` (`06_inep_modelo.sql`). Em aberto: INEP quer *soft delete* (`ativo`), `etl.merge_tabela()` exclui por escopo; Hop 2.10.0 (compose) × 2.20.0 (decidido no INEP). |
| 2026-11-24 | **Origem do dado, auditoria e FKs (§7C).** FKs de `populacao`, `pib_municipal` e `malha` para `ibge.municipio` e de `_execucao_id` para `etl.execucao` (`04_fk_ibge.sql`). Auditoria por trigger com contexto declarado pelo escritor (`etl` | `api` | `direto_sql`), log `audit.evento` como schema no mesmo banco, colunas `_criado_origem`/`_origem`/`_modificado_por` e `etl.execucao.disparo` (`05_auditoria.sql`). Papel `api_crud` para a API de CRUD. Conflito API × ETL: a fonte vence na recarga da partição (a confirmar). Orquestrador reordenado: município antes das filhas. DDL do INEP passa a `06_inep_modelo.sql`. Testado em Postgres 17.6 (testes 03 e 05, mais subida do zero com 01 a 05). O orquestrador Python também foi executado (banco vazio, rodada sem mudança, `--simular`, edição pela API e FTP republicado): resultados em artifact. Achados: a simulação precisou criar o município fictício (FK) e o teste 05 filtrava mal. |
| 2026-11-24 | **INEP sem soft delete (§7D).** Desenho híbrido do Opus: dimensões que nunca se apagam (`etl.merge_tabela` ganhou `p_excluir`), fato por ano `inep.curso_censo` com trava de 20%, regra CT&I aplicada em view, "ativo" derivado, curadoria fora do `_hash`. Medido com os censos 2021 a 2024 reais. Carga real feita (`orquestrador_inep.py`, `06_inep_modelo.sql`): 547 cursos e 132 campi, idênticos à simulação. Tipos de curso conferidos com o Supabase do painel. |

---

## 9. Próximos passos

1. Ampliar o leitor do FTP para o layout completo (§3) e gravar staging com todas as colunas.
2. Escrever o SQL de `ibge.municipio`, `ibge.populacao` e `ibge.pib_municipal` com as funções de carga, e o schema `meta` (§7).
   Avaliar se as variáveis 5936 e 10605 do 4709 entram em `ibge.populacao`.
   ~~Alinhar `02_carga_incremental.sql` ao §7B e criar `etl.historico`~~ (feito em 19/11). Falta `meta.v_status_dataset` e `meta.v_linha_origem`.
   Mudar o verificador para devolver a lista de partições alteradas em formato que o Hop consiga percorrer (JSON/CSV).
3. Acrescentar tipologias e atividades à `base/ibge_base_municipal_BA.csv`.
4. Implementar a descoberta da edição nova do FTP (listar `ftp.ibge.gov.br/Pib_Municipios/`).
5. ~~Testar o MERGE no Postgres~~: feito em 19/11 com Postgres portátil e `orquestrador_simulado.py`. Próximo: incluir o PIB do FTP no orquestrador.
6. Decidir se a malha vai para PostGIS ou fica como GeoJSON simplificado para o front-end.
7. Entregar a `ibge.municipio` ao INEP: tabela de correspondência `id_municipio` (Supabase, serial 1–417) ↔ `codigo_ibge`, por nome normalizado (ver `automacao-hop-postgres/PLANO.md` §0 e §8).

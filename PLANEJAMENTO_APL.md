# Planejamento — APLs (Arranjos Produtivos Locais)

Fonte: lista oficial do **Observatório Brasileiro de APL** (MDIC). Implementado e testado em 26/11 no Postgres local.
Código: `orquestracao/orquestrador_apl.py` · modelo: `orquestracao/sql/07_apl_modelo.sql` · de-para: `orquestracao/meta/apl_municipio_de_para.csv` · teste: `orquestracao/testes/07_teste_aproximacao.py`.

## 1. Fonte e download

- Página: <https://www.gov.br/empresas-e-negocios/pt-br/portais-desconhecidos/observatorioapl/apls-brasileiros>, botão **"Baixe a Planilha de APLs"** → `Lista APLs_outubro2022_publico.xlsx` (uma aba, 397 APLs do Brasil, 30 colunas). O painel Power BI da página mostra os mesmos dados.
- **Sem API e sem conjunto no dados.gov.br.** O gov.br responde com **captcha** a qualquer cliente automatizado: o download é **manual**. Na VPS, uma pessoa deixa a planilha numa pasta e o Hop a vigia.
- Passo 0: `sha256` do arquivo × `etl.checkpoint` (`metodo = hash_corpo`). Arquivo igual = `sem_mudanca`, sem leitura.
- A planilha é de out/2022; as datas por APL vão de 2020 a 2021. Perguntar ao MDIC por link direto ou atualização.

## 2. Recorte e dados pessoais

- Entram os APLs com **BA entre os estados**: 54 só da BA e 2 interestaduais (decisão de 26/11). O interestadual mantém a **sede original** e só os **municípios baianos**: Vinhos do Vale do São Francisco (PE; BA, sede Petrolina) e Piscicultura do Sertão de Itaparica (PE; BA; AL, sede Jatobá; **confirmar**). Total: 56 APLs e 352 pares.
- **Não entram** (dado pessoal): nome, e-mail e telefone do gestor, endereço, CEP e "Fonte da Informação" (traz nomes de pessoas). Conferido: nenhum dos 95 nomes de gestor aparece nas colunas carregadas.

## 3. Modelo (igual ao Supabase)

- `apl.apl`: PK `id_apl` (gerado aqui; a planilha não tem código estável, "No." é número de linha), `UNIQUE (uf, nome_apl)` para o MERGE, `uf_fonte`, `codigo_ibge_polo` **sem FK** (sede pode ficar fora da BA).
- `apl.apl_municipio`: PK `(id_apl, codigo_ibge)`, FK para `apl.apl` e para `ibge.municipio`; guarda `nome_municipio_fonte` (como veio) e `metodo_cruzamento`.
- APL renomeado na fonte = exclusão + inclusão (id novo). Os `id_apl` não são os do Supabase.

## 4. Cruzamento nome → `codigo_ibge` (decidido em 26/11)

Ordem fixa, a primeira que resolver vence:

| Nível | Regra | Planilha de out/2022 |
|---|---|---|
| 1. exato | chave normalizada: minúsculo, sem acento, só letras e números ("Santa Luz" = Santaluz, "Casanova" = Casa Nova) | 329 |
| 2. de-para | `meta/apl_municipio_de_para.csv`, decisão humana | 2 |
| 3. aproximado | `difflib` ≥ **0,80** e folga ≥ **0,10** sobre o 2º colocado | 14 |
| nenhum | **a carga aborta** e lista o nome | 0 |

**De-para determinado (2 entradas, só o que os níveis 1 e 3 não resolvem):**

| Na planilha | Município | Código | Por quê |
|---|---|---|---|
| Tancredo Neves | Presidente Tancredo Neves | 2925758 | nome abreviado: similaridade 0,72, abaixo do mínimo |
| Capela | Capela do Alto Alegre | 2906857 | a aproximação apontaria Caravelas (errado) e foi recusada pela folga; inferido pelo território (Bacia do Jacuípe). **Confirmar com a SECTI** |

Regras do de-para:
- Entra só nome que o exato e o aproximado **não** resolvem. Entrada que a aproximação já resolve é redundante e sai (o teste falha).
- Código vazio = ignorar o nome de propósito (registrado no log).
- Na fase do CRUD, o de-para vira tabela no banco, editada pela curadoria e semeada por este CSV (ver `PLANEJAMENTO_CRUD_CURADORIA.md`).

**Por que a folga de 0,10:** há municípios reais quase iguais (Cristópolis × Crisópolis, 0,95; Caatiba × Acajutiba). Com folga 0,05 o estresse sobe de 92% para 97% de acerto, mas "Capela" passaria para Caravelas.

**Limite que nenhum método pega:** erro que forma outro nome real (escrever "Santa Luzia" querendo Santaluz) casa exato com o município errado. Só a revisão humana percebe.

## 5. Testes (`orquestracao/testes/07_teste_aproximacao.py`)

1. Os 17 nomes reais com problema: 15 resolvidos pela aproximação no município certo; Capela e Tancredo Neves recusados.
2. Estresse com 1.666 erros sintéticos (falta, sobra, troca e inversão de letra nos 417 nomes): **0 erros**, 92% de acerto, 8% de recusa.
3. De-para: exatamente as 2 entradas acima, válidas e necessárias.
4. Com `--xlsx`: a planilha real × gabarito do Supabase (`testes/dados/apl_gabarito_supabase.csv`, cópia do que o consultor montou à mão). Aproximado e de-para **nunca** divergem; as únicas divergências aceitas são as conhecidas abaixo.

## 6. Conferência com o Supabase (só leitura, 26/11)

- Os 417 nomes de `lista_municipioxterritorio` são idênticos aos do IBGE.
- 54 APLs nos dois lados; 52 casam pelo nome e 2 (Rio Gavião) foram renomeados no Supabase, com a mesma sede e os mesmos municípios.
- **Erro no Supabase:** as listas de municípios dos 2 APLs de **cacau** estão trocadas: o "Litoral Sul" (sede Itabuna) aparece com Ipiaú, Jequié e Jitaúna; o "Médio Rio de Contas" (sede Jequié) aparece com Itabuna, Uruçuca etc. A planilha está certa.
- O Supabase deixou "Capela" fora do Ser do Sertão.

## 7. BrasilAPI (teste de 26/11; não incorporado)

Só 27 dos 54 APLs da BA têm CNPJ. Resultado: 23 com o CNPJ na cidade-polo, 2 noutro município do APL, 1 fora do APL (Produção, Aquisição e Serviço: Feira de Santana × polo Irecê), 1 CNPJ inválido (Giló) e 1 cooperativa INAPTA (Pescados da BTS). Confere a sede, **não** a lista de municípios (onde estavam 15 dos 17 erros). Serve como verificação de qualidade e é candidato a regra de pendência no CRUD.

## 8. Pendências

Ver `PENDENCIAS_E_PERGUNTAS.md`, item D11: confirmar Capela e a Piscicultura; corrigir o cacau no Supabase; incluir `apl` em `meta.v_linha_origem` e `meta.v_dicionario`.

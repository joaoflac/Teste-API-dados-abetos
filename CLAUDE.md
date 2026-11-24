# CLAUDE.md — Teste-API-dados-abetos

## O que é este repositório

Laboratório de **planejamento e teste das fontes de dados e do ETL** do **Painel Territorial em CT&I** da SECTI-BA.
O código do painel fica em outro repositório: `territorios_secti`, branch `redesign`. Aqui se validam APIs, amostras, regras de carga e orquestração antes de levá-las para lá.

- **Recorte:** Bahia, 417 municípios. A chave de junção é sempre `codigo_ibge` (7 dígitos).
- **Fontes:** IBGE, INEP, BNDES, SICONFI, ANATEL e ANEEL.
- **Produção (futura):** VPS Ubuntu com **PostgreSQL 17** e **Apache Hop** em contêineres. ETL para APIs; ELT para CSV/ZIP sem API oficial.
- **Branch de trabalho:** `b2`. A principal é `main`.

## Tarefa atual (atualizar ao fim de cada sessão)

**Foco: planejar só o IBGE.** O documento de referência é `PLANEJAMENTO_IBGE.md`; registrar ali toda decisão nova (§8).
Próximos passos, em ordem (§9 do documento):
1. Ampliar o leitor do FTP do PIB dos Municípios para o layout completo (tipologias, VAB, atividades).
2. SQL de `ibge.municipio`, `ibge.populacao` e `ibge.pib_municipal`, com funções de carga MERGE.
3. Acrescentar tipologias e atividades a `base/ibge_base_municipal_BA.csv`.
4. Descoberta automática da edição nova do FTP.
5. ~~Testar o MERGE~~: feito com Postgres portátil e `orquestracao/orquestrador_simulado.py` (simula o Hop). Próximo: incluir o PIB do FTP no orquestrador.

## Decisões já tomadas (não reabrir sem motivo)

- **IBGE é a base de informações municipais** (tabela-mestre). As outras fontes se juntam por `codigo_ibge`.
- **PIB, PIB per capita, VAB, tipologias e atividades vêm do FTP**, da base TXT do PIB dos Municípios. A API 5938 serve só para conferência (soma do PIB da BA tem de bater).
- **PIB per capita:** usar sempre o oficial, nunca recalcular com a 6579 (o IBGE usa outra população).
- **VAB municipal e atividades só existem até 2021.** 2022 e 2023 são provisórios e serão revisados.
- **Tipologias são fixas por município** e vão para a dimensão, sem ano.
- **Verificar antes de baixar:** cada recurso tem um identificador de mudança (ETag/304, hash do CKAN, `modificacao` por período do IBGE, `extrato_entregas` do SICONFI, CRC32 dos arquivos dentro do ZIP da ANATEL). Ver `orquestracao/PLANO_ORQUESTRACAO_ETL.md`.
- **Detecção em 3 níveis** (conjunto → partição → linha): o Hop nunca baixa e substitui tudo; baixa só a partição alterada e grava só as linhas com `_hash` diferente (`PLANEJAMENTO_IBGE.md` §7A).
- **Rastreabilidade por linha:** toda tabela tem `_hash`, `_criado_em`, `_modificado_em`, `_modificado_fonte_em` e `_execucao_id`. Fonte, URL e histórico ficam no catálogo `meta`/`etl`, no mesmo banco (§7B).
- **Carga incremental:** MERGE por chave e `_hash`. A exclusão só alcança linhas **dentro do escopo baixado** e é auditada em `etl.exclusao`. O checkpoint só avança se a carga terminar bem.

## Mapa do repositório

| Caminho | Conteúdo |
|---|---|
| `PLANEJAMENTO_IBGE.md` | **Plano vivo do IBGE**: API × FTP, layout do TXT, tipologias, atividades, modelo de tabelas, registro de decisões |
| `orquestracao/PLANO_ORQUESTRACAO_ETL.md` | Identificadores de mudança por fonte, fluxo do Hop, padrão de carga e exclusão |
| `orquestracao/sql/` | `01_controle.sql` (schema `etl`), `02_carga_incremental.sql` (MERGE com escopo) |
| `orquestracao/testes/` | Teste do MERGE com dados sintéticos |
| `orquestracao/orquestrador_simulado.py` | Simula o workflow do Hop (passos 0–3) com dados reais do IBGE |
| `pg-portatil/` | Postgres 17.6 portátil **dentro do repo**: `pg.ps1` (instalar, start, stop, status, psql, backup, restaurar) e `backup/painel.sql` (versionado) |
| `orquestracao/sql/03_ibge_modelo.sql` | `ibge.municipio`, `ibge.pib_municipal`, `ibge.malha`, schema `meta`, `etl.merge_tabela()` genérica com trava de exclusão |
| `orquestracao/meta/layout_pib_municipios_2010_2023.csv` | Layout do TXT do FTP (lido pelo orquestrador; versionado por edição) |
| `orquestracao/docker-compose.yml` | Postgres 17.6 + Apache Hop (ainda não executado) |
| `RESULTADOS_AMOSTRAGEM.md` | Resultado da amostragem de todas as fontes (documento principal das amostras) |
| `APIs_TERRITORIOS_SECTI_extracao_planilha.md` | Especificação original dos indicadores (2.1–2.7 = IBGE) |
| `amostras/`, `categorias_cti/` | CSVs de amostra e filtros CT&I por fonte |
| `base/ibge_base_municipal_BA.csv` | Tabela-mestre de municípios (417 × 36) e dicionário |
| `scripts/ibge_base_municipal.py` | Gera a base municipal |
| `scripts/ibge_pib_per_capita_oficial.py` | Lê a base TXT do FTP (hoje só PIB e per capita) |
| `scripts/etl_verificar_mudanca.py` | Passo 0 da orquestração: detecta o que mudou, com escopo |
| `scripts/probe_identificadores_mudanca.py` | Testa ETag, Last-Modified, 304 e metadados de cada fonte |
| `scripts/httpzip.py` | Lê ZIP remoto por HTTP Range (CRC e extração de um arquivo interno) |

## Ambiente (Windows)

- **graphify 0.9.112** (`graphifyy[sql]`), instalado com `py -3.12 -m pip install --user`; executável em `%APPDATA%\Python\Python312\Scripts` (já no PATH do usuário). Grafo em `graphify-out/`. Hoje só tem **código e SQL** (AST); a **extração semântica dos .md ainda não foi feita**: rodar `/graphify .` numa sessão (usa subagentes e consome tokens uma vez). Após mudar código: `graphify update .`. CSV, XLSX e DOCX não são indexados.
- **Python:** usar `py -3.12` (pandas, requests e graphifyy instalados com `--user`). Para acentos no terminal, exportar `PYTHONIOENCODING=utf-8`.
- **Downloads grandes** (ZIP do IBGE, INEP, ANATEL) vão para uma pasta de cache fora do repositório, nunca commitados.
- **INEP:** o certificado tem cadeia incompleta no Python; use `curl`.
- **ANEEL:** o servidor derruba o TLS com SNI; acesse pelo IP `200.198.220.169` com o cabeçalho `Host`.
- **Docker:** o Docker Desktop está instalado, mas nunca foi iniciado (sem WSL). Por isso o teste local usa Postgres portátil.
- **Postgres local:** PostgreSQL 17.6 portátil em `pg-portatil/` (no repo), `localhost:5433`, banco `painel`, usuário `etl`, senha em `pg-portatil/pgpass.txt` (fora do git). Binários e `data/` ficam fora do git; **`pg-portatil/backup/painel.sql` é versionado**. Comandos: `powershell -File pg-portatil\pg.ps1 instalar|start|stop|status|psql|backup|restaurar`. **Não inicia sozinho após reiniciar o Windows.** Rodar `backup` antes de cada commit.
- **Testes no banco:** só com anos e códigos fictícios (`orquestracao/testes/`). A exclusão por escopo apaga as linhas reais do mesmo ano que não estão no snapshot. Já aconteceu em 19/11: 2024 e 2025 foram apagados e depois reparados.
- **Hop simulado:** `py -3.12 orquestracao/orquestrador_simulado.py` (`--simular` monta um cenário de revisão). Driver `psycopg` 3.3.9.

## Convenções

- Documentação e mensagens em **português**.
- Todo dado novo leva `fonte`, `url_fonte` e `data_coleta`.
- Não commitar sem pedido explícito.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. When the answer is under a Markdown heading, `graphify section "<heading>"` prints that section's text, so the .md need not be opened. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

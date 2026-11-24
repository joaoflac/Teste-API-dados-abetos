# CLAUDE.md — Teste-API-dados-abetos

## O que é este repositório

Laboratório de **planejamento e teste das fontes de dados e do ETL** do **Painel Territorial em CT&I** da SECTI-BA.
O código do painel fica em outro repositório: `territorios_secti`, branch `redesign`. Aqui se validam APIs, amostras, regras de carga e orquestração antes de levá-las para lá.

- **Recorte:** Bahia, 417 municípios. A chave de junção é sempre `codigo_ibge` (7 dígitos).
- **Fontes:** IBGE, INEP, BNDES, SICONFI, ANATEL e ANEEL.
- **Produção (futura):** VPS Ubuntu com **PostgreSQL 17** e **Apache Hop** em contêineres. ETL para APIs; ELT para CSV/ZIP sem API oficial.
- **Branch de trabalho:** `b2`. A principal é `main`.

## Tarefa atual (atualizar ao fim de cada sessão)

**Foco: IBGE e INEP já carregam no Postgres (24/11); próximos: BNDES, SICONFI, ANATEL, ANEEL.** Há dois planos, feitos em máquinas diferentes e reconciliados em 24/11: `PLANEJAMENTO_IBGE.md` (registrar decisões em §8) e `automacao-hop-postgres/PLANO.md` (INEP; o §0 mapeia os nomes dele para os da orquestração). Ambos seguem `orquestracao/PLANO_ORQUESTRACAO_ETL.md`.
**Em aberto:** (0) confirmar "a fonte vence" na edição manual via API; (b) Hop 2.10.0 no compose × 2.20.0 decidido no INEP; os 6 rótulos `revisar` do INEP. **Resolvido em 24/11:** soft delete do INEP (descartado; desenho híbrido, `PLANEJAMENTO_IBGE.md` §7D).
**Próximos passos:** ver `PENDENCIAS_E_PERGUNTAS.md`. Resumo: (1) a SECTI decide os rótulos `revisar` do INEP, Radiologia e as licenciaturas (A1 a A9); (2) confirmar "a fonte vence" na edição pela API e o contrato de views com o painel (C1, C4, C5); (3) série histórica por rótulo recodificado e teste do `baixar_zip` (D1, D2); (4) próximas fontes: BNDES, SICONFI, ANATEL, ANEEL (D8). IBGE e INEP já carregam no Postgres e passam nos testes (`orquestracao/testes/03_`, `05_`, `06_`).

## Decisões já tomadas (não reabrir sem motivo)

- **IBGE é a base de informações municipais** (tabela-mestre). As outras fontes se juntam por `codigo_ibge`.
- **PIB, PIB per capita, VAB, tipologias e atividades vêm do FTP**, da base TXT do PIB dos Municípios. A API 5938 serve só para conferência (soma do PIB da BA tem de bater).
- **PIB per capita:** usar sempre o oficial, nunca recalcular com a 6579 (o IBGE usa outra população).
- **VAB municipal e atividades só existem até 2021.** 2022 e 2023 são provisórios e serão revisados.
- **Tipologias são fixas por município** e vão para a dimensão, sem ano.
- **Verificar antes de baixar:** cada recurso tem um identificador de mudança (ETag/304, hash do CKAN, `modificacao` por período do IBGE, `extrato_entregas` do SICONFI, CRC32 dos arquivos dentro do ZIP da ANATEL). Ver `orquestracao/PLANO_ORQUESTRACAO_ETL.md`.
- **Detecção em 3 níveis** (conjunto → partição → linha): o Hop nunca baixa e substitui tudo; baixa só a partição alterada e grava só as linhas com `_hash` diferente (`PLANEJAMENTO_IBGE.md` §7A).
- **Rastreabilidade por linha:** toda tabela tem `_hash`, `_criado_em`, `_modificado_em`, `_modificado_fonte_em` e `_execucao_id`. Fonte, URL e histórico ficam no catálogo `meta`/`etl`, no mesmo banco (§7B).
- **INEP (`automacao-hop-postgres/PLANO.md`, `PLANEJAMENTO_IBGE.md` §7D):** Supabase atual é **só leitura**; Postgres novo recebe só **presencial** da Bahia (`CO_UF = 29` e `CO_MUNICIPIO` ∈ `ibge.municipio`); ABI (`QT_CURSO = 0`) fora do catálogo e dos indicadores; CT&I = **lista de rótulos CINE** (`inep.regra_cti`) aplicada na view; campus = par (`co_ies`, `co_municipio`). **Sem soft delete:** dimensões nunca apagadas (`p_excluir => false`), fato por ano `inep.curso_censo`, "ativo" derivado em `inep.v_curso_atual`; quem lê usa as views. **Decidido em 24/11:** a UNIVASF permanece (`exigir_sede_ba = false`: 552 cursos, 133 campi); o dataset cru do INEP manda e o Supabase é só referência; rótulos `revisar` ficam fora da view. **Em aberto:** os 6 rótulos `revisar` (Ecologia, Geologia, Agrimensura, Eng. agrícola, Optometria, Saúde coletiva) e as escolhas de política CT&I da SECTI (Radiologia, BI em Saúde, Arquitetura, licenciaturas).
- **Município é do IBGE:** nenhuma outra fonte cria tabela de município; tudo faz FK para `ibge.municipio`.
- **Origem do dado e auditoria (`PLANEJAMENTO_IBGE.md` §7C):** quem escreve declara o contexto na transação (`audit.contexto`: `etl` ou `api`; sem contexto = `direto_sql`). O log é o schema `audit` no mesmo banco, alimentado por trigger. O CRUD do painel entra pelo papel `api_crud`. **A fonte vence:** o ETL sobrescreve edição da API quando recarrega a partição (a confirmar). Município carrega antes das filhas (FKs).
- **Carga incremental:** MERGE por chave e `_hash`. A exclusão só alcança linhas **dentro do escopo baixado** e é auditada em `etl.exclusao`. O checkpoint só avança se a carga terminar bem.

## Mapa do repositório

| Caminho | Conteúdo |
|---|---|
| `PENDENCIAS_E_PERGUNTAS.md` | **Lista viva do que falta**: decisões de política CT&I (com a recomendação do Opus), perguntas à SECTI e ao consultor, decisões técnicas e trabalho técnico pendente. Começar por aqui ao retomar |
| `PLANEJAMENTO_IBGE.md` | **Plano vivo do IBGE**: API × FTP, layout do TXT, tipologias, atividades, modelo de tabelas, registro de decisões |
| `automacao-hop-postgres/` | **Plano do INEP**: `PLANO.md` (filtros, funil, orquestração, regra CT&I), `analise/` (CINE, `regra_cti_rotulos.csv`, cursos ambíguos), `simulacao/` (scripts Python stdlib e CSVs de saída). Sem infraestrutura própria: usa `orquestracao/` |
| `TERRITORIOS_SECTI_Resumo_Executivo_*.docx/.pdf` | Resumos executivos das amostras (gerados por `scripts/gerar_docx_executivo.js`) |
| `orquestracao/PLANO_ORQUESTRACAO_ETL.md` | Identificadores de mudança por fonte, fluxo do Hop, padrão de carga e exclusão |
| `orquestracao/sql/` | `01_controle.sql` (schema `etl`), `02_carga_incremental.sql` (MERGE com escopo) |
| `orquestracao/testes/` | Teste do MERGE com dados sintéticos |
| `orquestracao/orquestrador_simulado.py` | Simula o workflow do Hop (passos 0–3) com dados reais do IBGE |
| `orquestracao/orquestrador_inep.py` | INEP no orquestrador comum: Passo 0 (ETag/Last-Modified/ano seguinte), leitura do ZIP em streaming, validação, MERGE por tabela e checkpoint. `python orquestracao/orquestrador_inep.py <ano> [--zip arquivo] [--verificar] [--forcar]`. Censos 2021 a 2024 carregados e testados em 24/11 |
| `pg-portatil/` | Postgres 17.6 portátil **dentro do repo**: `pg.ps1` (instalar, start, stop, status, psql, backup, restaurar) e `backup/painel.sql` (versionado) |
| `orquestracao/sql/03_ibge_modelo.sql` | `ibge.municipio`, `ibge.pib_municipal`, `ibge.malha`, schema `meta`, `etl.merge_tabela()` genérica com trava de exclusão |
| `orquestracao/sql/04_fk_ibge.sql`, `05_auditoria.sql` | FKs do schema `ibge`; auditoria por trigger (`audit.evento`, `audit.contexto()`, `audit.ativar()`), colunas `_origem`, papel `api_crud`. Detalhe em `PLANEJAMENTO_IBGE.md` §7C |
| `orquestracao/sql/06_inep_modelo.sql` | Modelo do INEP: `inep.ies`, `ies_local`, `curso`, `curso_censo`, `cine_classificacao`, `regra_cti` e as views `v_curso_atual` e `v_campus_com_curso`. Testes em `orquestracao/testes/06_teste_inep.sql` |
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

**Duas máquinas, ambientes diferentes** (mesmo repo, branch `b2`):
- **Máquina do IBGE:** `py -3.12`, graphify em `%APPDATA%\Python\Python312\Scripts`, Postgres portátil e orquestrador simulado (detalhes abaixo).
- **Máquina do INEP:** (em 24/11 ganhou Postgres portátil e Python 3.12 em `%LOCALAPPDATA%ProgramsPythonPython312`, com requests e psycopg via `pip --user`; o launcher `py` não os enxerga, chame o `python.exe` direto e sem `-I`) sem Python de sistema, sem Java, sem Docker (falta *Virtual Machine Platform*, sem admin); tem `curl`, o graphify em `~/.local/bin` e o zip do INEP em `C:\Users\joao.vinicius\dados-inep\2024\` (fora do repo). Para rodar o Postgres aqui: `git pull`, `pg.ps1 instalar`, `pg.ps1 restaurar`. Para os scripts Python, instalar o Python 3.12 por usuário.

Os itens abaixo descrevem a máquina do IBGE, salvo indicação contrária.

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

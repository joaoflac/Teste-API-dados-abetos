# Graph Report - Teste-API-dados-abetos  (2026-11-26)

## Corpus Check
- 51 files · ~1,663,923 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 53 file(s) not represented in the graph (top: .csv 52, (none) 1)
- WARNING: 53 of 106 files seen (50%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 480 nodes · 749 edges · 27 communities (26 shown, 1 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8cc00a05`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Exploracao de Valores Unicos CT&I - INEP, BNDES, SICONFI, ANATEL e IBGE
- APIs_TERRITORIOS_SECTI_extracao_planilha.md
- orquestrador_inep.py
- ANEEL (fonte de dados)
- aneel_decfec_ba.py
- TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam
- json
- gerar_amostras.py
- gerar_planilha_amostras.py
- orquestrador_apl.py
- orquestrador_simulado.py
- environment
- TERRITORIOS_SECTI_Amostras_CTI_1b1ba1ae.md
- Planejamento IBGE — Painel Territorial CT&I
- CLAUDE.md — Teste-API-dados-abetos
- Orquestração ETL/ELT — Painel Territorial CT&I
- MER atual: IBGE × INEP
- PostgreSQL portátil do repositório
- Workflow check_<fonte> (check_inep)
- Resultados da amostragem (documento concentrador)
- cti_nivel / cti_motivo BNDES (regra explicita de CT&I)
- Especificacao de Extracao das APIs/Fonte da Planilha
- Tabelas Supabase (lista_cursos_cti, lista_ativos_cti, lista_municipioxterritorio, stats_ti, firjan)
- Planejamento — CRUD do painel e fila de validação humana
- Planejamento — APLs (Arranjos Produtivos Locais)
- orquestrador_inep.py

## God Nodes (most connected - your core abstractions)
1. `log()` - 17 edges
2. `montar()` - 16 edges
3. `Planejamento IBGE — Painel Territorial CT&I` - 14 edges
4. `executar()` - 11 edges
5. `Planejamento — CRUD do painel e fila de validação humana` - 10 edges
6. `copiar()` - 10 edges
7. `ftp_linhas_ba()` - 10 edges
8. `get()` - 10 edges
9. `recurso_malha()` - 10 edges
10. `recurso_municipio()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `1. O que existe hoje` --references--> `montar()`  [INFERRED]
  PLANEJAMENTO_CRUD_CURADORIA.md → orquestracao/orquestrador_apl.py
- `6. Fases` --references--> `montar()`  [INFERRED]
  PLANEJAMENTO_CRUD_CURADORIA.md → orquestracao/orquestrador_apl.py
- `3.3 Linha duvidosa: fica no CRUD, fora do painel público` --references--> `montar()`  [INFERRED]
  PLANEJAMENTO_CRUD_CURADORIA.md → orquestracao/orquestrador_apl.py
- `3.5 Edição humana que a recarga respeita (C1 decidido: a pessoa vence)` --references--> `ler_xlsx()`  [INFERRED]
  PLANEJAMENTO_CRUD_CURADORIA.md → orquestracao/orquestrador_apl.py
- `INEP (primeira fonte a automatizar)` --semantically_similar_to--> `INEP - Censo da Educacao Superior 2024`  [INFERRED] [semantically similar]
  automacao-hop-postgres/PLANO.md → OUTRAS_APIS_EXPLORACAO_VALORES_UNICOS_CTI.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Familia de datasets ANEEL homologados (SIGA, SAMP, INDGER, P&D, DEC/FEC)** — aneel_exploracao_valores_unicos_cti_siga, aneel_exploracao_valores_unicos_cti_samp, aneel_exploracao_valores_unicos_cti_indger, aneel_exploracao_valores_unicos_cti_ped, aneel_exploracao_valores_unicos_cti_dec_fec_indqual [EXTRACTED 1.00]
- **Fluxo de ingestao Hop com deteccao de mudanca** — automacao_hop_postgres_plano_workflow_check_fonte, automacao_hop_postgres_plano_deteccao_mudanca, automacao_hop_postgres_plano_fonte_controle, automacao_hop_postgres_plano_staging_upsert, automacao_hop_postgres_plano_apache_hop [EXTRACTED 1.00]
- **Sources with direct CT&I identifying variables** — graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_cine_area_geral, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_regra_cti_bndes, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_funcao_19, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_ped_aneel [EXTRACTED 1.00]
- **Six open data sources feeding the TERRITORIOS SECTI panel** — graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_ibge, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_inep, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_aneel, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_bndes, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_siconfi, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_anatel [EXTRACTED 1.00]
- **Estrategia de classificacao CT&I (nivel_cti, cti_nivel, P&D ANEEL)** — resultados_amostragem_nivel_cti, resultados_amostragem_bndes_cti_nivel, resultados_amostragem_aneel_ped_projetos, resultados_amostragem_quatro_situacoes_filtro_cti [INFERRED 0.85]

## Communities (27 total, 1 thin omitted)

### Community 0 - "Exploracao de Valores Unicos CT&I - INEP, BNDES, SICONFI, ANATEL e IBGE"
Cohesion: 0.31
Nodes (9): ANATEL - Banda larga fixa e conectividade, ANEEL (referencia cruzada), Classificacao CINE Brasil (areas gerais 05-09), Exploracao de Valores Unicos CT&I - INEP, BNDES, SICONFI, ANATEL e IBGE, Funcao 19 (Ciencia e Tecnologia) e Subfuncao 126 (TI), IBGE - Base demografica, PIB/VAB e malha, INEP - Censo da Educacao Superior 2024, Nucleo STEM (CINE 05, 06, 07: 399 cursos, 67.325 matriculas) (+1 more)

### Community 1 - "APIs_TERRITORIOS_SECTI_extracao_planilha.md"
Cohesion: 0.21
Nodes (11): anatel(), aneel(), bndes(), classifica_bndes(), ibge(), inep(), painel_cti_municipio_ano(), reg() (+3 more)

### Community 2 - "orquestrador_inep.py"
Cohesion: 0.08
Nodes (10): w(), ckan(), http_get(), indices_zip(), salvar(), todos(), HttpFile, open_remote_zip() (+2 more)

### Community 3 - "ANEEL (fonte de dados)"
Cohesion: 0.24
Nodes (9): ANEEL (fonte de dados), DEC/FEC e INDQUAL (954 conjuntos eletricos), INDGER - Unidades consumidoras por municipio, P&D ANEEL (99 projetos COELBA), SAMP - Mercado de energia (COELBA), SIGA - Geracao (1.163 usinas BA), SIGA Solar e Eolica (EOL/UFV, 1.026 usinas, 74 municipios), ANEEL (CKAN datastore_search: SIGA, INDGER, SAMP, P&D, DEC/FEC) (+1 more)

### Community 4 - "aneel_decfec_ba.py"
Cohesion: 0.05
Nodes (45): ANATEL (data publisher), Codigo Municipio (IBGE 7-digit code column), ANATEL 4G mobile coverage spreadsheet (Bahia municipalities), % area coberta (share of municipal area with 4G), % domicilios cobertos (share of households with 4G), % moradores cobertos (share of residents with 4G), ANATEL (connectivity and digital infrastructure), ANEEL (energy, P&D, grid quality) (+37 more)

### Community 5 - "TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam"
Cohesion: 0.11
Nodes (12): ABA, bl(), borda, bordas, C, doc, {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  HeadingLevel, AlignmentType, LevelFormat, Footer, Header, PageNumber, BorderStyle, PageBreak,
  TableOfContents,
}, fs (+4 more)

### Community 6 - "json"
Cohesion: 0.09
Nodes (10): digital(), escopo(), head(), NoSNIAdapter, NoSNIAdapter, aneel_url(), ckan_resource(), NoSNIAdapter (+2 more)

### Community 7 - "gerar_amostras.py"
Cohesion: 0.27
Nodes (10): Area territorial municipal (malhas IBGE), Densidade demografica (indicador derivado), IBGE (SIDRA / API agregados / malhas), PIB municipal (agregado 5938, variavel 37), PIB per capita (tabela 6784 + base oficial XLSX fallback), Populacao municipal (agregado 6579), ANATEL (SCM densidade, banda larga fixa, cobertura 4G), IBGE (amostras 2.1 a 2.7, sem variavel CT&I) (+2 more)

### Community 8 - "gerar_planilha_amostras.py"
Cohesion: 0.31
Nodes (4): aba_dados(), cabecalho(), larguras(), valor()

### Community 9 - "orquestrador_apl.py"
Cohesion: 0.10
Nodes (19): aproximado(), carregar(), chave_nome(), com_uf(), data_excel(), espacos(), inteiro(), ler_xlsx() (+11 more)

### Community 10 - "orquestrador_simulado.py"
Cohesion: 0.15
Nodes (23): carregar_meta(), fonte(), checkpoint(), copiar(), executar(), ftp_linhas_ba(), get(), limpar_simulacao() (+15 more)

### Community 11 - "environment"
Cohesion: 0.05
Nodes (36): postgres, HOP_FILE_PATH, HOP_PROJECT_FOLDER, HOP_PROJECT_NAME, HOP_RUN_CONFIG, PG_HOST, PG_PASSWORD, POSTGRES_DB (+28 more)

### Community 12 - "TERRITORIOS_SECTI_Amostras_CTI_1b1ba1ae.md"
Cohesion: 0.07
Nodes (27): Sheet: ANATEL_Acessos, Sheet: ANATEL_Cobertura_Movel, Sheet: ANATEL_Densidade, Sheet: ANEEL_DECFEC_Conjunto, Sheet: ANEEL_DECFEC_Municipio, Sheet: ANEEL_INDGER, Sheet: ANEEL_INDQUAL, Sheet: ANEEL_PeD (+19 more)

### Community 13 - "Planejamento IBGE — Painel Territorial CT&I"
Cohesion: 0.07
Nodes (26): 1. Papel do IBGE no projeto, 2. Conjuntos e canais, 3. PIB: API × FTP, 4. Outras ressalvas de dados, 5. Tipologias territoriais (FTP, BA, 2023), 6. Atividades econômicas dominantes (FTP, BA, 2021), 7. Modelo de armazenamento (PostgreSQL), 7A. Atualização incremental: o Hop nunca baixa e substitui tudo (+18 more)

### Community 14 - "CLAUDE.md — Teste-API-dados-abetos"
Cohesion: 0.11
Nodes (15): Ambiente (Windows), CLAUDE.md — Teste-API-dados-abetos, Convenções, Decisões já tomadas (não reabrir sem motivo), graphify, Mapa do repositório, O que é este repositório, Tarefa atual (atualizar ao fim de cada sessão) (+7 more)

### Community 15 - "Orquestração ETL/ELT — Painel Territorial CT&I"
Cohesion: 0.18
Nodes (10): 1. Princípio: verificar antes de baixar, 2. Resultado dos testes de identificadores (`scripts/probe_identificadores_mudanca.py`), 3. Carga incremental e exclusão pontual (`sql/`), 4. ETL × ELT, 5. Estrutura proposta no Hop (`orquestracao/hop/`, a criar), 6. Pendências, Chave por fonte, Observações por fonte (+2 more)

### Community 16 - "MER atual: IBGE × INEP"
Cohesion: 0.33
Nodes (5): 1. Domínio: município, IBGE e INEP, 2. Controle e rastreabilidade, 3. Situação de cada relacionamento, 4. Inconsistências e lacunas, MER atual: IBGE × INEP

### Community 17 - "PostgreSQL portátil do repositório"
Cohesion: 0.40
Nodes (4): Comandos (`powershell -File pg-portatil\pg.ps1 <acao>`), O que vai para o git e o que não vai, PostgreSQL portátil do repositório, Recuperar em máquina nova (ou se a pasta se perder)

### Community 19 - "Workflow check_<fonte> (check_inep)"
Cohesion: 0.29
Nodes (8): Apache Hop (workflows de ingestao), Deteccao de mudanca na origem (ETag, Last-Modified, 304, CKAN metadata_modified), Plano de automacao de ingestao Apache Hop + PostgreSQL, Tabela fonte_controle, Demais fontes futuras (IBGE, SICONFI, ANATEL, BNDES, ANEEL), PostgreSQL (destino da ingestao), Schema staging e upsert apos aprovacao, Workflow check_<fonte> (check_inep)

### Community 20 - "Resultados da amostragem (documento concentrador)"
Cohesion: 0.29
Nodes (6): ANEEL - Exploracao de Valores Unicos para CT&I, TERRITORIOS_SECTI_Amostras_CTI.xlsx, Resultados da amostragem (documento concentrador), Scripts de reproducao (gerar_amostras.py, extrair_amostras_aneel_ba.py, ibge_pib_per_capita_oficial.py), status_validacao_fontes.csv e filtros_cti_consolidado.csv, TERRITORIOS SECTI - Resumo Executivo de Dados (PDF)

### Community 21 - "cti_nivel / cti_motivo BNDES (regra explicita de CT&I)"
Cohesion: 0.33
Nodes (5): BNDES - Operacoes de financiamento (80.964 ops BA), BNDES (nao automaticas, indiretas automaticas, agregado 5.5), cti_nivel / cti_motivo BNDES (regra explicita de CT&I), INEP (amostras IES e cursos, microdados CSV), nivel_cti (classificacao derivada de CO_CINE_AREA_GERAL)

### Community 22 - "Especificacao de Extracao das APIs/Fonte da Planilha"
Cohesion: 0.33
Nodes (5): codigo_ibge (chave territorial), Especificacao de Extracao das APIs/Fonte da Planilha, Planilha de Avaliacao das Fontes do Painel Territorial, 27 Territorios de Identidade (SECTI/SEPLAN) e 417 municipios BA, Modelo proposto: ies, codigo_ibge, co_curso_inep

### Community 23 - "Tabelas Supabase (lista_cursos_cti, lista_ativos_cti, lista_municipioxterritorio, stats_ti, firjan)"
Cohesion: 0.33
Nodes (4): INEP (primeira fonte a automatizar), Supabase vicaqpcluxkwbbbwdpkg (banco atual do TERRITORIOS SECTI), Tabelas Supabase (lista_cursos_cti, lista_ativos_cti, lista_municipioxterritorio, stats_ti, firjan), Lista SECTI de 642 cursos CT&I (pendente)

### Community 24 - "Planejamento — CRUD do painel e fila de validação humana"
Cohesion: 0.14
Nodes (13): 0. Decisões do dono (26/11), 1. O que existe hoje, 2. Objetivo, 4. API, 5. Front: curadoria dentro das abas do CRUD (sem aba separada), 6. Fases, 7.1 Onde fica cada tipo de linha, 7.2 Views que o CRUD lê (schema `api`, papel `curador`) (+5 more)

### Community 25 - "Planejamento — APLs (Arranjos Produtivos Locais)"
Cohesion: 0.20
Nodes (9): 1. Fonte e download, 2. Recorte e dados pessoais, 3. Modelo (igual ao Supabase), 4. Cruzamento nome → `codigo_ibge` (decidido em 26/11), 5. Testes (`orquestracao/testes/07_teste_aproximacao.py`), 6. Conferência com o Supabase (só leitura, 26/11), 7. BrasilAPI (teste de 26/11; não incorporado), 8. Pendências (+1 more)

### Community 26 - "orquestrador_inep.py"
Cohesion: 0.14
Nodes (6): probe(), carregar_ano(), inteiro(), ler_zip(), limpa(), sondar()

## Knowledge Gaps
- **32 isolated node(s):** `ANATEL - Banda larga fixa e conectividade`, `Funcao 19 (Ciencia e Tecnologia) e Subfuncao 126 (TI)`, `Nucleo STEM (CINE 05, 06, 07: 399 cursos, 67.325 matriculas)`, `Deteccao de mudanca na origem (ETag, Last-Modified, 304, CKAN metadata_modified)`, `TERRITORIOS_SECTI_Amostras_CTI.xlsx` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 243 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `montar()` connect `orquestrador_apl.py` to `Planejamento — CRUD do painel e fila de validação humana`, `orquestrador_inep.py`, `orquestrador_simulado.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `montar()` (e.g. with `1. O que existe hoje` and `3.3 Linha duvidosa: fica no CRUD, fora do painel público`) actually correct?**
  _`montar()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ANATEL - Banda larga fixa e conectividade`, `Funcao 19 (Ciencia e Tecnologia) e Subfuncao 126 (TI)`, `Nucleo STEM (CINE 05, 06, 07: 399 cursos, 67.325 matriculas)` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `orquestrador_inep.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08108108108108109 - nodes in this community are weakly interconnected._
- **Why does `baixar_zip()` connect `CLAUDE.md — Teste-API-dados-abetos` to `orquestrador_inep.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Should `aneel_decfec_ba.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05353535353535353 - nodes in this community are weakly interconnected._
- **Why does `Planejamento — CRUD do painel e fila de validação humana` connect `Planejamento — CRUD do painel e fila de validação humana` to `orquestrador_apl.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
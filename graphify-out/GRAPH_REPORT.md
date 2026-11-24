# Graph Report - Teste-API-dados-abetos  (2026-11-24)

## Corpus Check
- 46 files · ~1,567,817 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 51 file(s) not represented in the graph (top: .csv 50, (none) 1)
- WARNING: 51 of 99 files seen (52%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 422 nodes · 633 edges · 19 communities (17 shown, 2 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 35 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `973ffbd8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ANEEL — Exploração de Valores Únicos para CT&I
- APIs_TERRITORIOS_SECTI_extracao_planilha.md
- orquestrador_inep.py
- etl_verificar_mudanca.py
- aneel_decfec_ba.py
- TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam
- json
- gerar_amostras.py
- gerar_docx_executivo.js
- environment
- orquestrador_simulado.py
- environment
- TERRITORIOS_SECTI_Amostras_CTI_1b1ba1ae.md
- Planejamento IBGE — Painel Territorial CT&I
- CLAUDE.md — Teste-API-dados-abetos
- Orquestração ETL/ELT — Painel Territorial CT&I
- MER atual: IBGE × INEP
- PostgreSQL portátil do repositório

## God Nodes (most connected - your core abstractions)
1. `log()` - 14 edges
2. `Planejamento IBGE — Painel Territorial CT&I` - 14 edges
3. `executar()` - 10 edges
4. `ftp_linhas_ba()` - 10 edges
5. `recurso_municipio()` - 10 edges
6. `recurso_malha()` - 10 edges
7. `TERRITORIOS SECTI Resumo Executivo (Dados, CSV version)` - 10 edges
8. `HttpFile` - 9 edges
9. `get()` - 8 edges
10. `copiar()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `TERRITORIOS SECTI - Resumo Executivo de Dados (PDF)` --semantically_similar_to--> `Resultados da amostragem (documento concentrador)`  [INFERRED] [semantically similar]
  TERRITORIOS_SECTI_Resumo_Executivo_Dados.pdf → RESULTADOS_AMOSTRAGEM.md
- `Tarefa atual (atualizar ao fim de cada sessão)` --references--> `baixar_zip()`  [INFERRED]
  CLAUDE.md → orquestracao/orquestrador_inep.py
- `D. Trabalho técnico pendente` --references--> `baixar_zip()`  [INFERRED]
  PENDENCIAS_E_PERGUNTAS.md → orquestracao/orquestrador_inep.py
- `INEP (primeira fonte a automatizar)` --semantically_similar_to--> `INEP - Censo da Educacao Superior 2024`  [INFERRED] [semantically similar]
  automacao-hop-postgres/PLANO.md → OUTRAS_APIS_EXPLORACAO_VALORES_UNICOS_CTI.md
- `Tabelas Supabase (lista_cursos_cti, lista_ativos_cti, lista_municipioxterritorio, stats_ti, firjan)` --semantically_similar_to--> `Lista SECTI de 642 cursos CT&I (pendente)`  [INFERRED] [semantically similar]
  automacao-hop-postgres/PLANO.md → RESULTADOS_AMOSTRAGEM.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Familia de datasets ANEEL homologados (SIGA, SAMP, INDGER, P&D, DEC/FEC)** — aneel_exploracao_valores_unicos_cti_siga, aneel_exploracao_valores_unicos_cti_samp, aneel_exploracao_valores_unicos_cti_indger, aneel_exploracao_valores_unicos_cti_ped, aneel_exploracao_valores_unicos_cti_dec_fec_indqual [EXTRACTED 1.00]
- **Fluxo de ingestao Hop com deteccao de mudanca** — automacao_hop_postgres_plano_workflow_check_fonte, automacao_hop_postgres_plano_deteccao_mudanca, automacao_hop_postgres_plano_fonte_controle, automacao_hop_postgres_plano_staging_upsert, automacao_hop_postgres_plano_apache_hop [EXTRACTED 1.00]
- **Sources with direct CT&I identifying variables** — graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_cine_area_geral, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_regra_cti_bndes, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_funcao_19, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_ped_aneel [EXTRACTED 1.00]
- **Six open data sources feeding the TERRITORIOS SECTI panel** — graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_ibge, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_inep, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_aneel, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_bndes, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_siconfi, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_anatel [EXTRACTED 1.00]
- **Estrategia de classificacao CT&I (nivel_cti, cti_nivel, P&D ANEEL)** — resultados_amostragem_nivel_cti, resultados_amostragem_bndes_cti_nivel, resultados_amostragem_aneel_ped_projetos, resultados_amostragem_quatro_situacoes_filtro_cti [INFERRED 0.85]

## Communities (19 total, 2 thin omitted)

### Community 0 - "ANEEL — Exploração de Valores Únicos para CT&I"
Cohesion: 0.06
Nodes (35): codigo_ibge (chave territorial), Especificacao de Extracao das APIs/Fonte da Planilha, Planilha de Avaliacao das Fontes do Painel Territorial, 27 Territorios de Identidade (SECTI/SEPLAN) e 417 municipios BA, Apache Hop (workflows de ingestao), Deteccao de mudanca na origem (ETag, Last-Modified, 304, CKAN metadata_modified), Plano de automacao de ingestao Apache Hop + PostgreSQL, Tabela fonte_controle (+27 more)

### Community 1 - "APIs_TERRITORIOS_SECTI_extracao_planilha.md"
Cohesion: 0.20
Nodes (11): anatel(), aneel(), bndes(), classifica_bndes(), ibge(), inep(), painel_cti_municipio_ano(), reg() (+3 more)

### Community 2 - "orquestrador_inep.py"
Cohesion: 0.07
Nodes (15): w(), carregar_ano(), inteiro(), ler_zip(), limpa(), sondar(), dsn(), ckan() (+7 more)

### Community 3 - "etl_verificar_mudanca.py"
Cohesion: 0.18
Nodes (11): ANEEL (fonte de dados), DEC/FEC e INDQUAL (954 conjuntos eletricos), ANEEL - Exploracao de Valores Unicos para CT&I, INDGER - Unidades consumidoras por municipio, P&D ANEEL (99 projetos COELBA), SAMP - Mercado de energia (COELBA), SIGA - Geracao (1.163 usinas BA), SIGA Solar e Eolica (EOL/UFV, 1.026 usinas, 74 municipios) (+3 more)

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
Cohesion: 0.07
Nodes (11): probe(), digital(), escopo(), head(), NoSNIAdapter, NoSNIAdapter, aneel_url(), ckan_resource() (+3 more)

### Community 7 - "gerar_amostras.py"
Cohesion: 0.27
Nodes (10): Area territorial municipal (malhas IBGE), Densidade demografica (indicador derivado), IBGE (SIDRA / API agregados / malhas), PIB municipal (agregado 5938, variavel 37), PIB per capita (tabela 6784 + base oficial XLSX fallback), Populacao municipal (agregado 6579), ANATEL (SCM densidade, banda larga fixa, cobertura 4G), IBGE (amostras 2.1 a 2.7, sem variavel CT&I) (+2 more)

### Community 8 - "gerar_docx_executivo.js"
Cohesion: 0.31
Nodes (4): aba_dados(), cabecalho(), larguras(), valor()

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

## Knowledge Gaps
- **32 isolated node(s):** `Deteccao de mudanca na origem (ETag, Last-Modified, 304, CKAN metadata_modified)`, `ANATEL - Banda larga fixa e conectividade`, `Funcao 19 (Ciencia e Tecnologia) e Subfuncao 126 (TI)`, `Nucleo STEM (CINE 05, 06, 07: 399 cursos, 67.325 matriculas)`, `BNDES (nao automaticas, indiretas automaticas, agregado 5.5)` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 210 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `baixar_zip()` connect `CLAUDE.md — Teste-API-dados-abetos` to `orquestrador_inep.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **What connects `Deteccao de mudanca na origem (ETag, Last-Modified, 304, CKAN metadata_modified)`, `ANATEL - Banda larga fixa e conectividade`, `Funcao 19 (Ciencia e Tecnologia) e Subfuncao 126 (TI)` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ANEEL — Exploração de Valores Únicos para CT&I` be split into smaller, more focused modules?**
  _Cohesion score 0.06282051282051282 - nodes in this community are weakly interconnected._
- **Should `orquestrador_inep.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06871035940803383 - nodes in this community are weakly interconnected._
- **Should `aneel_decfec_ba.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05353535353535353 - nodes in this community are weakly interconnected._
- **Should `TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam` be split into smaller, more focused modules?**
  _Cohesion score 0.11428571428571428 - nodes in this community are weakly interconnected._
- **Should `json` be split into smaller, more focused modules?**
  _Cohesion score 0.07439024390243902 - nodes in this community are weakly interconnected._
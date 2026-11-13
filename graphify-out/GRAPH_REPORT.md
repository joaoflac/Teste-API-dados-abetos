# Graph Report - Teste-API-dados-abetos  (2026-11-13)

## Corpus Check
- Large corpus: 20 files · ~703,202 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 206 nodes · 295 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Plano Hop e Postgres
- Sondas Python ANEEL
- Extracao ANEEL DEC/FEC
- ANEEL energia e CT&I
- ANATEL cobertura movel
- Gerador resumo docx
- Matriz de filtros CT&I
- IBGE indicadores
- Gerador planilha amostras
- Leitor HTTP de ZIP
- SICONFI DCA Bahia
- ANEEL limitacoes e territorios

## God Nodes (most connected - your core abstractions)
1. `TERRITORIOS SECTI Resumo Executivo (Dados, CSV version)` - 10 edges
2. `HttpFile` - 9 edges
3. `Resultados da amostragem (documento concentrador)` - 8 edges
4. `TERRITORIOS SECTI Resumo Executivo (Planilha, xlsx version)` - 8 edges
5. `ANATEL 4G mobile coverage spreadsheet (Bahia municipalities)` - 8 edges
6. `reg()` - 7 edges
7. `ibge()` - 7 edges
8. `ANEEL (fonte de dados)` - 7 edges
9. `Exploracao de Valores Unicos CT&I - INEP, BNDES, SICONFI, ANATEL e IBGE` - 7 edges
10. `salvar()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `TERRITORIOS SECTI - Resumo Executivo de Dados (PDF)` --semantically_similar_to--> `Resultados da amostragem (documento concentrador)`  [INFERRED] [semantically similar]
  TERRITORIOS_SECTI_Resumo_Executivo_Dados.pdf → RESULTADOS_AMOSTRAGEM.md
- `Modelo proposto: ies, codigo_ibge, co_curso_inep` --semantically_similar_to--> `codigo_ibge (chave territorial)`  [INFERRED] [semantically similar]
  automacao-hop-postgres/PLANO.md → APIs_TERRITORIOS_SECTI_extracao_planilha.md
- `INEP (primeira fonte a automatizar)` --semantically_similar_to--> `INEP - Censo da Educacao Superior 2024`  [INFERRED] [semantically similar]
  automacao-hop-postgres/PLANO.md → OUTRAS_APIS_EXPLORACAO_VALORES_UNICOS_CTI.md
- `Tabelas Supabase (lista_cursos_cti, lista_ativos_cti, lista_municipioxterritorio, stats_ti, firjan)` --semantically_similar_to--> `Lista SECTI de 642 cursos CT&I (pendente)`  [INFERRED] [semantically similar]
  automacao-hop-postgres/PLANO.md → RESULTADOS_AMOSTRAGEM.md
- `INEP (amostras IES e cursos, microdados CSV)` --semantically_similar_to--> `INEP - Censo da Educacao Superior 2024`  [INFERRED] [semantically similar]
  RESULTADOS_AMOSTRAGEM.md → OUTRAS_APIS_EXPLORACAO_VALORES_UNICOS_CTI.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Estrategia de classificacao CT&I (nivel_cti, cti_nivel, P&D ANEEL)** — resultados_amostragem_nivel_cti, resultados_amostragem_bndes_cti_nivel, resultados_amostragem_aneel_ped_projetos, resultados_amostragem_quatro_situacoes_filtro_cti [INFERRED 0.85]
- **Fluxo de ingestao Hop com deteccao de mudanca** — automacao_hop_postgres_plano_workflow_check_fonte, automacao_hop_postgres_plano_deteccao_mudanca, automacao_hop_postgres_plano_fonte_controle, automacao_hop_postgres_plano_staging_upsert, automacao_hop_postgres_plano_apache_hop [EXTRACTED 1.00]
- **Familia de datasets ANEEL homologados (SIGA, SAMP, INDGER, P&D, DEC/FEC)** — aneel_exploracao_valores_unicos_cti_siga, aneel_exploracao_valores_unicos_cti_samp, aneel_exploracao_valores_unicos_cti_indger, aneel_exploracao_valores_unicos_cti_ped, aneel_exploracao_valores_unicos_cti_dec_fec_indqual [EXTRACTED 1.00]
- **Six open data sources feeding the TERRITORIOS SECTI panel** — graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_ibge, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_inep, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_aneel, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_bndes, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_siconfi, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_anatel [EXTRACTED 1.00]
- **Sources with direct CT&I identifying variables** — graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_cine_area_geral, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_regra_cti_bndes, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_funcao_19, graphify_out_converted_territorios_secti_resumo_executivo_dados_1d5f63e8_ped_aneel [EXTRACTED 1.00]

## Communities (12 total, 2 thin omitted)

### Community 0 - "Plano Hop e Postgres"
Cohesion: 0.09
Nodes (26): Apache Hop (workflows de ingestao), Deteccao de mudanca na origem (ETag, Last-Modified, 304, CKAN metadata_modified), Plano de automacao de ingestao Apache Hop + PostgreSQL, Tabela fonte_controle, INEP (primeira fonte a automatizar), Demais fontes futuras (IBGE, SICONFI, ANATEL, BNDES, ANEEL), PostgreSQL (destino da ingestao), Schema staging e upsert apos aprovacao (+18 more)

### Community 1 - "Sondas Python ANEEL"
Cohesion: 0.14
Nodes (11): NoSNIAdapter, anatel(), aneel(), bndes(), classifica_bndes(), ibge(), inep(), painel_cti_municipio_ano() (+3 more)

### Community 2 - "Extracao ANEEL DEC/FEC"
Cohesion: 0.13
Nodes (8): ckan(), http_get(), indices_zip(), salvar(), todos(), open_remote_zip(), ler_csv(), salvar()

### Community 3 - "ANEEL energia e CT&I"
Cohesion: 0.10
Nodes (20): ANEEL (fonte de dados), DEC/FEC e INDQUAL (954 conjuntos eletricos), ANEEL - Exploracao de Valores Unicos para CT&I, INDGER - Unidades consumidoras por municipio, P&D ANEEL (99 projetos COELBA), SAMP - Mercado de energia (COELBA), SIGA - Geracao (1.163 usinas BA), SIGA Solar e Eolica (EOL/UFV, 1.026 usinas, 74 municipios) (+12 more)

### Community 4 - "ANATEL cobertura movel"
Cohesion: 0.11
Nodes (23): ANATEL (data publisher), Codigo Municipio (IBGE 7-digit code column), ANATEL 4G mobile coverage spreadsheet (Bahia municipalities), % area coberta (share of municipal area with 4G), % domicilios cobertos (share of households with 4G), % moradores cobertos (share of residents with 4G), ANATEL (connectivity and digital infrastructure), ANATEL fixed broadband (SCM): density and accesses (+15 more)

### Community 5 - "Gerador resumo docx"
Cohesion: 0.11
Nodes (12): ABA, bl(), borda, bordas, C, doc, {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  HeadingLevel, AlignmentType, LevelFormat, Footer, Header, PageNumber, BorderStyle, PageBreak,
  TableOfContents,
}, fs (+4 more)

### Community 6 - "Matriz de filtros CT&I"
Cohesion: 0.13
Nodes (16): categorias_cti/filtros_cti_consolidado.csv, Consolidated CT&I filter matrix, CT&I levels (Principal, Ampliado, Auxiliar, Recorte), Dataset CT&I filter status (filtered, classified, unfiltered with variable, no variable), ANATEL_Cobertura_Movel tab, Filtros_CTI tab (official CT&I filter rules), LEIA-ME tab (index of all dataset tabs), ANATEL (planilha version) (+8 more)

### Community 7 - "IBGE indicadores"
Cohesion: 0.27
Nodes (10): Area territorial municipal (malhas IBGE), Densidade demografica (indicador derivado), IBGE (SIDRA / API agregados / malhas), PIB municipal (agregado 5938, variavel 37), PIB per capita (tabela 6784 + base oficial XLSX fallback), Populacao municipal (agregado 6579), ANATEL (SCM densidade, banda larga fixa, cobertura 4G), IBGE (amostras 2.1 a 2.7, sem variavel CT&I) (+2 more)

### Community 8 - "Gerador planilha amostras"
Cohesion: 0.31
Nodes (4): aba_dados(), cabecalho(), larguras(), valor()

### Community 11 - "ANEEL limitacoes e territorios"
Cohesion: 0.33
Nodes (6): ANEEL (energy, P&D, grid quality), DEC/FEC grid quality indicators and INDQUAL de-para, Known limitations (data without municipality, N:N grid, EAD, faculty, ANATEL gaps), P&D ANEEL projects (99 COELBA projects), SIGA (ANEEL generation plants registry), Territorios de Identidade (27 territories, mapping pending)

## Knowledge Gaps
- **32 isolated node(s):** `SAMP - Mercado de energia (COELBA)`, `Planilha de Avaliacao das Fontes do Painel Territorial`, `27 Territorios de Identidade (SECTI/SEPLAN) e 417 municipios BA`, `Nucleo STEM (CINE 05, 06, 07: 399 cursos, 67.325 matriculas)`, `Funcao 19 (Ciencia e Tecnologia) e Subfuncao 126 (TI)` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 79 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Resultados da amostragem (documento concentrador)` connect `ANEEL energia e CT&I` to `Plano Hop e Postgres`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **What connects `SAMP - Mercado de energia (COELBA)`, `Planilha de Avaliacao das Fontes do Painel Territorial`, `27 Territorios de Identidade (SECTI/SEPLAN) e 417 municipios BA` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Plano Hop e Postgres` be split into smaller, more focused modules?**
  _Cohesion score 0.08505747126436781 - nodes in this community are weakly interconnected._
- **Why does `TERRITORIOS SECTI Resumo Executivo (Dados, CSV version)` connect `ANATEL cobertura movel` to `ANEEL limitacoes e territorios`, `Matriz de filtros CT&I`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Should `Sondas Python ANEEL` be split into smaller, more focused modules?**
  _Cohesion score 0.1425287356321839 - nodes in this community are weakly interconnected._
- **Why does `Exploracao de Valores Unicos CT&I - INEP, BNDES, SICONFI, ANATEL e IBGE` connect `Plano Hop e Postgres` to `ANEEL energia e CT&I`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Should `Extracao ANEEL DEC/FEC` be split into smaller, more focused modules?**
  _Cohesion score 0.13043478260869565 - nodes in this community are weakly interconnected._
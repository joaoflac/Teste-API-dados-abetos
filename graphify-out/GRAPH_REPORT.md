# Graph Report - Teste-API-dados-abetos  (2026-11-19)

## Corpus Check
- 26 files · ~37,778 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 40 file(s) not represented in the graph (top: .csv 39, (none) 1)
- WARNING: 40 of 66 files seen (61%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 390 nodes · 479 edges · 20 communities (19 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ec0faaf6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ANEEL — Exploração de Valores Únicos para CT&I
- APIs_TERRITORIOS_SECTI_extracao_planilha.md
- Exploração de Valores Únicos para CT&I — INEP, BNDES, SICONFI, ANATEL e IBGE
- etl_verificar_mudanca.py
- aneel_decfec_ba.py
- TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam
- postgres
- gerar_amostras.py
- gerar_docx_executivo.js
- environment
- Planejamento IBGE — Painel Territorial CT&I
- gerar_planilha_amostras.py
- Orquestração ETL/ELT — Painel Territorial CT&I
- CLAUDE.md — Teste-API-dados-abetos
- 11. Critérios de validação antes de entrar no painel
- 2. IBGE
- 3. INEP
- 01_controle.sql
- 02_carga_incremental.sql

## God Nodes (most connected - your core abstractions)
1. `TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam` - 13 edges
2. `ANEEL — Exploração de Valores Únicos para CT&I` - 12 edges
3. `Exploração de Valores Únicos para CT&I — INEP, BNDES, SICONFI, ANATEL e IBGE` - 12 edges
4. `Planejamento IBGE — Painel Territorial CT&I` - 10 edges
5. `HttpFile` - 9 edges
6. `7. P&D ANEEL` - 9 edges
7. `2. IBGE` - 8 edges
8. `3. INEP` - 8 edges
9. `CLAUDE.md — Teste-API-dados-abetos` - 8 edges
10. `ibge()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `7.1 `siconfi_6.2_dca_anexoIC_receita_salvador_2024_amostra.csv` — Receita (6.2)` --references--> `valor()`  [INFERRED]
  RESULTADOS_AMOSTRAGEM.md → scripts/gerar_planilha_amostras.py
- `7.2 `siconfi_6.3_rreo_anexo02_salvador_2025_cti.csv` — Despesa por função (RREO)` --references--> `valor()`  [INFERRED]
  RESULTADOS_AMOSTRAGEM.md → scripts/gerar_planilha_amostras.py

## Import Cycles
- None detected.

## Communities (20 total, 1 thin omitted)

### Community 0 - "ANEEL — Exploração de Valores Únicos para CT&I"
Cohesion: 0.04
Nodes (44): 10. Limitações, 11. Conclusão, 1. Objetivo, 2. Resumo, 3. SIGA — Geração, 4. SIGA — Solar e Eólica, 5. SAMP, 6. INDGER (+36 more)

### Community 1 - "APIs_TERRITORIOS_SECTI_extracao_planilha.md"
Cohesion: 0.05
Nodes (40): 10. Estrutura mínima de saída consolidada, 12. Fontes oficiais principais, 13. Observação final, 1. Regras gerais de extração, 4.1 Empreendimentos de geração e potência outorgada, 4.2 Potência instalada de geração renovável — Solar e Eólica, 4.3 Consumo de energia elétrica e unidades consumidoras, 4.4 Projetos de Pesquisa e Desenvolvimento — P&D ANEEL (+32 more)

### Community 2 - "Exploração de Valores Únicos para CT&I — INEP, BNDES, SICONFI, ANATEL e IBGE"
Cohesion: 0.05
Nodes (38): 10. Limitações e cuidados metodológicos específicos por fonte, 11. Conclusão, 1. Objetivo, 2. Resumo executivo, 3.1 Dimensões e categorias institucionais, 3.2 Classificação CINE Áreas (Mapeamento de Cursos CT&I), 3.3 Cobertura territorial, 3.4 Variáveis numéricas e grandezas (+30 more)

### Community 3 - "etl_verificar_mudanca.py"
Cohesion: 0.12
Nodes (9): digital(), escopo(), head(), NoSNIAdapter, aneel_url(), ckan_resource(), NoSNIAdapter, probe_http() (+1 more)

### Community 4 - "aneel_decfec_ba.py"
Cohesion: 0.10
Nodes (9): ckan(), http_get(), indices_zip(), salvar(), todos(), HttpFile, open_remote_zip(), ler_csv() (+1 more)

### Community 5 - "TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam"
Cohesion: 0.07
Nodes (29): 10. Divergências entre os `.md` anteriores (já corrigidas aqui), 11. Como reproduzir, 12. Pendências, 1. Como ler a coluna "Filtro CT&I", 2. Quadro-resumo por grupo de dataset, 3. IBGE, 4.1 `inep_3.1_3.7_ies_BA_amostra.csv` — Instituições (3.1) e titulação docente (3.7), 4.2 `inep_3.2_a_3.6_cursos_BA_amostra.csv` — Cursos, vagas, matrículas, ingressantes e concluintes (+21 more)

### Community 6 - "postgres"
Cohesion: 0.09
Nodes (22): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, interval, retries, test, image, ports (+14 more)

### Community 7 - "gerar_amostras.py"
Cohesion: 0.10
Nodes (14): NoSNIAdapter, anatel(), aneel(), bndes(), classifica_bndes(), ibge(), inep(), painel_cti_municipio_ano() (+6 more)

### Community 8 - "gerar_docx_executivo.js"
Cohesion: 0.11
Nodes (12): ABA, bl(), borda, bordas, C, doc, {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  HeadingLevel, AlignmentType, LevelFormat, Footer, Header, PageNumber, BorderStyle, PageBreak,
  TableOfContents,
}, fs (+4 more)

### Community 9 - "environment"
Cohesion: 0.14
Nodes (14): postgres, HOP_FILE_PATH, HOP_PROJECT_FOLDER, HOP_PROJECT_NAME, HOP_RUN_CONFIG, PG_HOST, PG_PASSWORD, depends_on (+6 more)

### Community 10 - "Planejamento IBGE — Painel Territorial CT&I"
Cohesion: 0.14
Nodes (13): 1. Papel do IBGE no projeto, 2. Conjuntos e canais, 3. PIB: API × FTP, 4. Outras ressalvas de dados, 5. Tipologias territoriais (FTP, BA, 2023), 6. Atividades econômicas dominantes (FTP, BA, 2021), 7. Modelo de armazenamento (PostgreSQL), 8. Registro de decisões (+5 more)

### Community 11 - "gerar_planilha_amostras.py"
Cohesion: 0.21
Nodes (8): 7.1 `siconfi_6.2_dca_anexoIC_receita_salvador_2024_amostra.csv` — Receita (6.2), 7.2 `siconfi_6.3_rreo_anexo02_salvador_2025_cti.csv` — Despesa por função (RREO), 7.3 `siconfi_6.3_6.4_dca_IE_BA_2024_ciencia_tecnologia_por_municipio.csv` — Painel de despesa CT&I (6.3, 6.4), 7. SICONFI / Tesouro, aba_dados(), cabecalho(), larguras(), valor()

### Community 12 - "Orquestração ETL/ELT — Painel Territorial CT&I"
Cohesion: 0.18
Nodes (10): 1. Princípio: verificar antes de baixar, 2. Resultado dos testes de identificadores (`scripts/probe_identificadores_mudanca.py`), 3. Carga incremental e exclusão pontual (`sql/`), 4. ETL × ELT, 5. Estrutura proposta no Hop (`orquestracao/hop/`, a criar), 6. Pendências, Chave por fonte, Observações por fonte (+2 more)

### Community 13 - "CLAUDE.md — Teste-API-dados-abetos"
Cohesion: 0.22
Nodes (8): Ambiente (Windows), CLAUDE.md — Teste-API-dados-abetos, Convenções, Decisões já tomadas (não reabrir sem motivo), graphify, Mapa do repositório, O que é este repositório, Tarefa atual (atualizar ao fim de cada sessão)

### Community 14 - "11. Critérios de validação antes de entrar no painel"
Cohesion: 0.29
Nodes (7): 11. Critérios de validação antes de entrar no painel, ANATEL, ANEEL, BNDES, IBGE, INEP, SICONFI

### Community 15 - "2. IBGE"
Cohesion: 0.25
Nodes (8): 2.1 População municipal residente, 2.2 PIB municipal, 2.3 PIB per capita, 2.4 Área territorial municipal, 2.5 Densidade demográfica, 2.6 PIB por km² (densidade econômica), 2.7 Malha geográfica municipal, 2. IBGE

### Community 16 - "3. INEP"
Cohesion: 0.25
Nodes (8): 3.1 Instituições de Educação Superior (IES), 3.2 Cursos de graduação (Geral e CT&I), 3.3 Cursos por modalidade — presencial x EAD, 3.4 Vagas ofertadas na graduação, 3.5 Matrículas no ensino superior, 3.6 Ingressantes e concluintes na graduação, 3.7 Docentes do ensino superior — titulação, 3. INEP

### Community 17 - "01_controle.sql"
Cohesion: 0.67
Nodes (5): etl.checkpoint, etl.exclusao, etl.execucao, etl.finalizar(), etl.recurso

### Community 18 - "02_carga_incremental.sql"
Cohesion: 0.33
Nodes (3): bndes.operacao_nao_automatica, ibge.populacao, stg.ibge_populacao

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam` connect `TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam` to `gerar_planilha_amostras.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Should `ANEEL — Exploração de Valores Únicos para CT&I` be split into smaller, more focused modules?**
  _Cohesion score 0.044444444444444446 - nodes in this community are weakly interconnected._
- **Why does `7. SICONFI / Tesouro` connect `gerar_planilha_amostras.py` to `TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Should `APIs_TERRITORIOS_SECTI_extracao_planilha.md` be split into smaller, more focused modules?**
  _Cohesion score 0.04878048780487805 - nodes in this community are weakly interconnected._
- **Should `Exploração de Valores Únicos para CT&I — INEP, BNDES, SICONFI, ANATEL e IBGE` be split into smaller, more focused modules?**
  _Cohesion score 0.05128205128205128 - nodes in this community are weakly interconnected._
- **Should `etl_verificar_mudanca.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11956521739130435 - nodes in this community are weakly interconnected._
- **Should `aneel_decfec_ba.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10114942528735632 - nodes in this community are weakly interconnected._
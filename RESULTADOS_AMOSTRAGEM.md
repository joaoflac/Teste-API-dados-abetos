# TERRITÓRIOS SECTI — Resultados da amostragem: o que há em cada dataset e quais filtros CT&I se aplicam

**Coleta:** 05/10/2026 (IBGE, INEP, BNDES, SICONFI, ANATEL), 01/10/2026 (ANEEL) e 07/10/2026 (ANEEL DEC/FEC 2025 e PIB per capita 2023) · **Escopo:** fontes de `APIs_TERRITORIOS_SECTI_extracao_planilha.md`, recorte Bahia (417 municípios)

Este é o **documento concentrador** da pasta. Ele reúne, para cada grupo de dataset em [amostras/](amostras/):
- o que o arquivo contém (linhas, colunas-chave, granularidade e período);
- como a amostra foi recortada (UF, município, agente, estratificação);
- **se o grupo é filtrado por alguma variável de CT&I, e por quais**.

Os demais `.md` da raiz continuam como material de apoio:

| Documento | Papel |
|---|---|
| `APIs_TERRITORIOS_SECTI_extracao_planilha.md` | Catálogo/especificação de origem: indicadores 2.1 a 7.1, endpoints e regras gerais (ex.: regra 9, não inventar nomes de campo) |
| `ANEEL_EXPLORACAO_VALORES_UNICOS_CTI.md` | Valores únicos e estatísticas detalhadas da ANEEL |
| `OUTRAS_APIS_EXPLORACAO_VALORES_UNICOS_CTI.md` | Valores únicos e estatísticas de INEP, BNDES, SICONFI, ANATEL e IBGE (ver divergências corrigidas no §10) |
| `TERRITORIOS_SECTI_Resumo_Executivo_Dados.docx` | Versão executiva (13 páginas) para gestores: papel de cada fonte, o que cada dataset retorna, variáveis categóricas, filtros CT&I e próximos passos. Gerado por `scripts/gerar_docx_executivo.js` |

**Arquivos de dados:**

| Pasta / arquivo | Conteúdo |
|---|---|
| [amostras/](amostras/) | Amostra de dados reais de cada fonte (CSV UTF-8 com BOM, abre direto no Excel) |
| [categorias_cti/](categorias_cti/) | Todos os valores das colunas categóricas, com contagem na BA e relação com CT&I |
| [categorias_cti/filtros_cti_consolidado.csv](categorias_cti/filtros_cti_consolidado.csv) | Lista única de filtros CT&I por fonte: campo, operador, valores, nível e justificativa |
| [status_validacao_fontes.csv](status_validacao_fontes.csv) | Status de cada indicador (validado / parcial), nº de linhas, URL testada e observações |
| [scripts/](scripts/) | Scripts que reproduzem tudo (§11) |
| `TERRITORIOS_SECTI_Resumo_Executivo_Dados.docx` | Resumo executivo em Word |
| `TERRITORIOS_SECTI_Resumo_Executivo_Planilha.docx` | Mesmo resumo, com a introdução e as referências apontando para as abas da planilha (para quem não usa o repositório) |
| `TERRITORIOS_SECTI_Amostras_CTI.xlsx` | **Todas as amostras em um só arquivo Excel**: aba LEIA-ME (índice com links), aba Filtros_CTI e uma aba por dataset. Gerada por `scripts/gerar_planilha_amostras.py` |

---

## 1. Como ler a coluna "Filtro CT&I"

Cada grupo de dataset cai em uma de quatro situações:

| Situação | Significado |
|---|---|
| ✅ **Filtrado por CT&I** | As linhas do arquivo **já foram selecionadas** por uma variável de CT&I. Tudo o que está no arquivo é CT&I |
| 🏷️ **Classificado (não filtrado)** | O arquivo traz linhas CT&I e não CT&I, mas cada linha tem uma **coluna de classificação** (`nivel_cti`, `cti_nivel`…). A amostra é estratificada por essa coluna |
| 🔶 **Não filtrado, mas tem variável CT&I** | Nenhum filtro foi aplicado, mas o dataset tem campos que permitem um recorte CT&I (principal ou auxiliar) |
| ⬜ **Sem variável CT&I** | O dataset não tem classificação de CT&I. Serve como denominador, contexto ou infraestrutura |

Recortes territoriais ou de agente (UF = BA, distribuidora = COELBA, lista de municípios de referência) **não** são filtros CT&I e aparecem separados na coluna "Recorte".

**Municípios de referência** usados em várias amostras (`AMOSTRA_MUN` em `gerar_amostras.py`): Salvador, Feira de Santana, Vitória da Conquista, Camaçari, Ilhéus, Juazeiro, Barreiras, Lauro de Freitas, Itabuna, Porto Seguro, Campo Formoso, Valença, Amélia Rodrigues, Casa Nova e Simões Filho.

---

## 2. Quadro-resumo por grupo de dataset

| Grupo de dataset (arquivo em `amostras/`) | Indicadores | Linhas | Recorte | Filtro CT&I | Variáveis CT&I |
|---|---|---:|---|---|---|
| `ibge_2.1_populacao_6579_BA` | 2.1 | 1.251 | 417 mun. × 2024–2026 | ⬜ Sem variável | — |
| `ibge_2.2_pib_vab_5938_BA` | 2.2 | 5.838 | 417 mun. × 2022–2023 × 7 variáveis | ⬜ Sem variável | — |
| `ibge_2.3_pib_per_capita_oficial_BA_2023` | 2.3 | 417 | Todos os municípios, 2023 (base oficial) | ⬜ Sem variável | — |
| `ibge_2.3_2.5_2.6_derivados_amostra_BA` | 2.3, 2.5, 2.6 | 15 | 15 mun. de referência × 2023 | ⬜ Sem variável | — |
| `ibge_2.4_area_centroide_BA` | 2.4 | 417 | Todos os municípios | ⬜ Sem variável | — |
| `ibge_2.7_malha_amostra_BA` | 2.7 | 30 | 30 primeiros municípios | ⬜ Sem variável | — |
| `inep_3.1_3.7_ies_BA_amostra` | 3.1, 3.7 | 40 | Top 40 IES da BA por nº de doutores | 🔶 Não filtrado | `ies_tecnologica_if_cefet` (TP_ORGANIZACAO_ACADEMICA ∈ {4, 5}), `QT_DOC_EX_DOUT/MEST` |
| **`inep_3.2_a_3.6_cursos_BA_amostra`** | 3.2 a 3.6 | 35 | Estratificada: 15 STEM pres. + 5 ampliado + 5 fora + 10 STEM EAD | 🏷️ Classificado | **`nivel_cti`** derivado de `CO_CINE_AREA_GERAL` (05/06/07 núcleo; 08/09 ampliado) |
| `inep_cursos_presenciais_por_municipio_nivel_cti_amostra` | 3.2 a 3.6 | 36 | Só presencial (`TP_DIMENSAO = 1`), 13 mun. de referência | 🏷️ Classificado | Agregado por `nivel_cti` |
| `aneel_4.1_4.2_siga_geracao_BA` | 4.1, 4.2 | 1.163 | `SigUFPrincipal = BA` (todas as usinas) | 🔶 Não filtrado | `SigTipoGeracao ∈ {EOL, UFV}` (auxiliar, transição energética) |
| `aneel_4.3_indger_comercial_BA_amostra` | 4.3 | 1.500 | `SigAgente = Neoenergia Coelba`, primeiras 1.500 linhas | ⬜ Sem variável | — |
| `aneel_4.3_samp_mercado_COELBA_amostra` | 4.3 | 1.000 | `SigAgenteDistribuidora = COELBA`, primeiras 1.000 linhas (jan/2024) | 🔶 Não filtrado | `DscDetalheMercado` (energia injetada/compensada) e `DscClasseConsumoMercado = Industrial` (auxiliar) |
| **`aneel_4.4_ped_projetos_COELBA`** | 4.4 | 99 | `NomAgente` contém COELBA | ✅ **Filtrado (dataset inteiro é P&D)** | Todo o dataset; subdividir por `SigTemaProjeto`, `SigFasInovacaoProjeto`, `SigTipoProdutoProjeto` |
| `aneel_4.5_decfec_conjunto_BA_2025` | 4.5 | 211 | COELBA, 2025 (12 meses), conjuntos ativos | ⬜ Sem variável | — (confiabilidade da rede) |
| `aneel_4.5_decfec_municipio_BA_2025` | 4.5 | 415 | Municípios atendidos pela COELBA, 2025 | ⬜ Sem variável | — |
| `aneel_4.5_indqual_conjunto_municipio_BA` | 4.5 | 1.262 | `SigUF = BA`, só os 211 conjuntos ativos em 2025 | ⬜ Sem variável | — (tabela de-para conjunto ↔ município) |
| **`bndes_5.x_nao_automaticas_BA_amostra`** | 5.1 a 5.5 | 30 | `uf = BA`; estratificada: 15 CT&I + 5 auxiliar + 10 fora | 🏷️ Classificado | **`inovacao`, `instrumento_financeiro`, `fonte_de_recurso_desembolsos`** → `cti_nivel`/`cti_motivo` |
| **`bndes_5.x_indiretas_automaticas_BA_amostra`** | 5.1 a 5.5 | 30 | `uf = " BA"`; estratificada: 15 CT&I + 5 auxiliar + 10 fora | 🏷️ Classificado | Idem |
| **`bndes_5.5_cti_por_municipio_ano_BA`** | 5.5 | 131 | **Completo:** todos os 76 municípios (incl. "SEM MUNICÍPIO") × anos com operação CT&I, 2002–2026 | ✅ **Filtrado** | `cti_nivel = "CT&I (regra explícita)"` |
| `siconfi_6.2_dca_anexoIC_receita_salvador_2024_amostra` | 6.2 | 40 | Salvador, 2024, primeiras 40 linhas | ⬜ Sem variável | — (receita não tem classificação CT&I) |
| **`siconfi_6.3_rreo_anexo02_salvador_2025_cti`** | 6.3 | 52 | Salvador, 2025, 6º bimestre | ✅ **Filtrado (por texto)** | `conta` contém "Ciência", "Tecnol" ou "TOTAL" |
| **`siconfi_6.3_6.4_dca_IE_BA_2024_ciencia_tecnologia_por_municipio`** | 6.3, 6.4 | 415 | Todos os municípios com DCA 2024 | 🏷️ Classificado (colunas CT&I) | Função 19, subfunções 571/572/573 e 126 viram colunas de valor |
| `anatel_7.1_densidade_scm_BA_amostra` | 7.1 | 162 | 5 mun. de referência × 2021, 2022, 2025, 2026 | ⬜ Sem variável | — (indicador inteiro é infraestrutura TIC) |
| `anatel_acessos_bl_fixa_2026_BA_amostra` | 7.1 (complementar) | 40 | 40 maiores linhas (ago/2026) nos mun. de referência | 🔶 Não filtrado | `Meio de Acesso = Fibra`, `Tecnologia ∈ {FTTH, FTTB}`, `Faixa de Velocidade = > 34Mbps` (auxiliar) |
| `anatel_7.2_cobertura_movel_4g_BA` | 7.2 | 417 | Completo: todos os 417 municípios da BA, Tecnologia 4G | ⬜ Sem variável | — (conectividade móvel: % território e % moradores cobertos) |

**Em uma frase por fonte:**
- **IBGE:** nenhum dataset tem variável CT&I. Serve de denominador e base territorial.
- **INEP:** cursos classificados pela CINE (`nivel_cti`). A amostra não é filtrada, é estratificada.
- **ANEEL:** só o **P&D** é CT&I por inteiro. O SIGA tem recorte auxiliar (solar/eólica). INDGER, SAMP e INDQUAL são contexto.
- **BNDES:** operações classificadas por regra explícita (`cti_nivel`). Só o agregado 5.5 é filtrado.
- **SICONFI:** o RREO de Salvador é filtrado por texto da conta. O painel DCA dos 415 municípios traz a Função 19 como coluna.
- **ANATEL:** sem filtro CT&I. Banda larga fixa (fibra/alta velocidade) e cobertura móvel 4G (% área e % moradores) são recortes de infraestrutura digital habilitadora.

---

## 3. IBGE

**Filtro CT&I: ⬜ nenhum.** As tabelas do catálogo não têm classificação de CT&I. A 5938 abre o VAB só em agropecuária, indústria, serviços e administração pública.

| Dataset | Origem | Conteúdo | Recorte |
|---|---|---|---|
| `ibge_2.1_populacao_6579_BA.csv` | `api/v3/agregados/6579/periodos/-3/variaveis/9324?localidades=N6[N3[29]]` | `codigo_ibge`, `ano_referencia`, `populacao` (estimativa). 2024: 14,85 mi · 2026: 14,89 mi | 417 municípios × 3 anos |
| `ibge_2.2_pib_vab_5938_BA.csv` | `…/agregados/5938/…/variaveis/37\|498\|513\|517\|6575\|525\|543` | Formato longo: PIB (var 37, mil R$) e VAB por atividade. PIB BA 2023: R$ 430,99 bi | 417 municípios × 2022–2023 |
| `ibge_2.3_pib_per_capita_oficial_BA_2023.csv` | `ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip` | `pib_mil_reais`, **`pib_per_capita_reais`** (oficial), `populacao_implicita`. São Francisco do Conde lidera (R$ 684 mil/hab); Mansidão é o menor (R$ 8,5 mil) | 417 municípios, 2023 |
| `ibge_2.3_2.5_2.6_derivados_amostra_BA.csv` | PIB per capita oficial + 6579 + malhas | `pib_per_capita_reais`, `densidade_demografica_hab_km2`, `pib_por_km2_mil_reais` | 15 municípios de referência, 2023 |
| `ibge_2.4_area_centroide_BA.csv` | `api/v3/malhas/estados/29/metadados?intrarregiao=municipio` | `area_km2`, `centroide_lon`, `centroide_lat` | 417 municípios |
| `ibge_2.7_malha_amostra_BA.csv` | `api/v3/malhas/estados/29?…&formato=application/vnd.geo+json` | Metadados da geometria (`tipo_geometria`, `n_vertices_aprox`). O GeoJSON completo tem `codarea` = código IBGE | 30 municípios |

**Ressalvas:**
- **2.3 PIB per capita:** a tabela 6784 só tem nível Brasil (N1) e a 6579 não tem população de 2023. Por isso o valor de 2023 vem da **base oficial do PIB dos Municípios** (TXT de largura fixa), lida por `scripts/ibge_pib_per_capita_oficial.py`. O PIB desse arquivo confere 100% com a SIDRA 5938 (soma BA R$ 430,99 bi).
- A densidade demográfica usa a população mais recente da 6579 (2026), não a de 2023.

---

## 4. INEP — Censo da Educação Superior 2024

**Fonte:** `download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2024.zip`. Arquivos `MICRODADOS_ED_SUP_IES_2024.CSV` (84 colunas) e `MICRODADOS_CADASTRO_CURSOS_2024.CSV` (223 colunas), separador `;`, latin1.

**Números da BA:** 145 IES sediadas em 45 municípios (107 faculdades, 25 centros universitários, 11 universidades, 2 IFs) · 10.022 docentes doutores em exercício · 40.715 linhas de curso (1.851 presenciais + 38.864 EAD por polo).

### 4.1 `inep_3.1_3.7_ies_BA_amostra.csv` — Instituições (3.1) e titulação docente (3.7)

| Item | Detalhe |
|---|---|
| Conteúdo | Uma linha por IES: `CO_IES`, `NO_IES`, `SG_IES`, município da **sede** (`CO_MUNICIPIO_IES`), organização acadêmica, categoria administrativa, `QT_DOC_EX_DOUT/MEST/ESP/GRAD`, `QT_DOC_EX_INT_DE`, `IN_REPOSITORIO_INSTITUCIONAL`, `IN_ACESSO_PORTAL_CAPES` |
| Recorte | `SG_UF_IES = BA`, 40 IES com mais doutores (UFBA lidera, com 2.466) |
| **Filtro CT&I** | 🔶 **Não filtrado.** Variáveis disponíveis: `ies_tecnologica_if_cefet` = `TP_ORGANIZACAO_ACADEMICA ∈ {4 IF, 5 CEFET}` (auxiliar) e a titulação docente como medida de capacidade de pesquisa |
| Ressalva | Não existe mais microdado público de docente. A titulação vem agregada por IES, sem município de lotação |

### 4.2 `inep_3.2_a_3.6_cursos_BA_amostra.csv` — Cursos, vagas, matrículas, ingressantes e concluintes

| Item | Detalhe |
|---|---|
| Conteúdo | Uma linha por curso × município: `CO_CURSO`, `NO_CURSO`, `CO_MUNICIPIO`, modalidade, dimensão, grau, **CINE completa** (área geral, específica, detalhada e rótulo), `nivel_cti`, `QT_VG_TOTAL`, `QT_VG_TOTAL_EAD`, `QT_INSCRITO_TOTAL`, `QT_ING`, `QT_MAT`, `QT_CONC` |
| Recorte | `SG_UF = BA`, amostra aleatória estratificada (`random_state=1`) |
| **Filtro CT&I** | 🏷️ **Classificado, não filtrado.** A coluna `nivel_cti` vem de **`CO_CINE_AREA_GERAL`** |
| Composição | 15 presenciais núcleo STEM · 5 presenciais ampliado · 5 presenciais fora de CT&I · 10 EAD núcleo STEM |

**Regra de classificação `nivel_cti`:**

| `CO_CINE_AREA_GERAL` | Área | `nivel_cti` |
|---|---|---|
| **05** | Ciências naturais, matemática e estatística | **CT&I núcleo (STEM)** |
| **06** | Computação e TIC | **CT&I núcleo (STEM)** |
| **07** | Engenharia, produção e construção | **CT&I núcleo (STEM)** |
| 08 | Agricultura, silvicultura, pesca e veterinária | CT&I ampliado |
| 09 | Saúde e bem-estar | CT&I ampliado |
| 00, 01, 02, 03, 04, 10 | Programas básicos, Educação, Artes, Ciências sociais, Negócios/direito, Serviços | Fora de CT&I |

**Variáveis auxiliares:** `TP_GRAU_ACADEMICO = 3` (Tecnológico, 18.707 linhas na BA) e IES com `TP_ORGANIZACAO_ACADEMICA ∈ {4, 5}`.
**Regra obrigatória:** `TP_DIMENSAO = 1` (presencial) não se soma com 2/3/4 (EAD). Vagas e inscritos de EAD não são calculados por município.

### 4.3 `inep_cursos_presenciais_por_municipio_nivel_cti_amostra.csv` — Agregado municipal

| Item | Detalhe |
|---|---|
| Conteúdo | `CO_MUNICIPIO`, `NO_MUNICIPIO`, `nivel_cti`, soma de `QT_CURSO`, `QT_VG_TOTAL`, `QT_MAT`, `QT_ING`, `QT_CONC` |
| Recorte | Só presencial (`TP_DIMENSAO = 1`), 13 dos municípios de referência que têm curso presencial |
| **Filtro CT&I** | 🏷️ **Classificado.** Até 3 linhas por município (núcleo, ampliado, fora) |

**Totais de matrícula na BA** (a partir de `categorias_cti/inep_cine_areas_BA_nivel_cti.csv`, presencial + EAD):

| `nivel_cti` | Matrículas BA (pres. + EAD) | Só presencial |
|---|---:|---:|
| CT&I núcleo (STEM) | 67.325 | 36.753 (399 cursos, 38 municípios) |
| CT&I ampliado | 156.386 | — |
| Fora de CT&I | 278.150 | — |

> **Lista SECTI de 642 cursos CT&I:** a planilha registra correspondência de 641/642 em 2023, mas a lista não está na pasta. O filtro por CINE é a aproximação reproduzível. Quando a lista chegar, entra como filtro **principal** por `CO_CURSO`/`CO_CINE_ROTULO`.

---

## 5. ANEEL

**Fonte:** CKAN `dadosabertos.aneel.gov.br`, via `datastore_search`. O servidor encerra o TLS quando o SNI é `dadosabertos.aneel.gov.br`. As amostras foram extraídas por `scripts/extrair_amostras_aneel_ba.py`, que conecta pelo IP `200.198.220.169` com cabeçalho `Host` e sem verificação de certificado.

`status_validacao_fontes.csv` e `filtros_cti_consolidado.csv` já refletem essa extração.

### 5.1 `aneel_4.1_4.2_siga_geracao_BA.csv` — SIGA: empreendimentos de geração (4.1) e solar/eólica (4.2)

| Item | Detalhe |
|---|---|
| Resource | `11ec447d-698d-4ab8-977f-b424d5deee6a` |
| Conteúdo | Uma linha por usina: `NomEmpreendimento`, `CodCEG`, `SigTipoGeracao`, `DscFaseUsina`, `NomFonteCombustivel`, `MdaPotenciaOutorgadaKw`, `MdaPotenciaFiscalizadaKw`, coordenadas, `DscMuninicpios` ("Nome - BA", texto livre) |
| Recorte | `SigUFPrincipal = BA`, **base completa** (1.163 usinas, 123 municípios) |
| **Filtro CT&I** | 🔶 **Não filtrado.** Recorte auxiliar de transição energética: **`SigTipoGeracao ∈ {EOL, UFV}`** (equivale a `NomFonteCombustivel ∈ {Cinética do vento, Radiação solar}`). São 520 EOL + 506 UFV = 1.026 usinas em 74 municípios. O indicador 4.2 é esse subconjunto |
| Ressalva | O município é texto; precisa de padronização para juntar com o código IBGE |

### 5.2 `aneel_4.3_indger_comercial_BA_amostra.csv` — INDGER: unidades consumidoras por município (4.3)

| Item | Detalhe |
|---|---|
| Resource | `fd10c9d4-cb76-4020-a322-e79afb13eaf7` |
| Conteúdo | `CodMunicipioIBGE` (7 dígitos), `DatReferenciaInformada`, `QtdUCAtiva`, `QtdUCAtivaFat` e cerca de 60 indicadores comerciais (faturas, ressarcimentos, postos de atendimento) |
| Recorte | `SigAgente = Neoenergia Coelba`, primeiras 1.500 linhas (409 municípios, abr/2023 a jul/2026) |
| **Filtro CT&I** | ⬜ **Sem variável CT&I.** Contexto de escala de mercado |

### 5.3 `aneel_4.3_samp_mercado_COELBA_amostra.csv` — SAMP: mercado de energia (4.3)

| Item | Detalhe |
|---|---|
| Resource | `ff80dd21-eade-4eb5-9ca8-d802c883940e` |
| Conteúdo | `DscClasseConsumoMercado`, `DscSubClasseConsumidor`, `DscSubGrupoTarifario`, `DscModalidadeTarifaria`, `DscDetalheMercado` (kWh, kW, R$, tributos), `DatCompetencia`, `VlrMercado` |
| Recorte | `SigAgenteDistribuidora = COELBA`, primeiras 1.000 linhas (todas de jan/2024; 9 classes e 24 tipos de detalhe na amostra) |
| **Filtro CT&I** | 🔶 **Não filtrado.** Recortes auxiliares: `DscDetalheMercado ∈ {Energia Injetada, Energia Compensada}` (adoção de geração distribuída) e `DscClasseConsumoMercado = Industrial` |
| Ressalva | **Sem município:** granularidade de concessionária |

### 5.4 `aneel_4.4_ped_projetos_COELBA.csv` — P&D ANEEL (4.4)

| Item | Detalhe |
|---|---|
| Resource | `3a7aee00-b6ee-4913-9670-f6b60f4a7bea` |
| Conteúdo | Uma linha por projeto: `DscCodProjeto`, `DscTituloProjeto`, `IdcSituacaoProjeto`, `SigSegmentoSetorEletrico`, `SigTemaProjeto`, `SigFasInovacaoProjeto`, `SigTipoProdutoProjeto`, `VlrCustoTotalPrevisto`, `VlrCustoTotalAuditado`, `AnoCadastroPropostaProjeto` |
| Recorte | `NomAgente` contém "COELBA" (99 projetos, 2009–2026) |
| **Filtro CT&I** | ✅ **Filtrado: o dataset inteiro é P&D regulado (CT&I direta).** Não precisa de filtro adicional, só do recorte por agente |
| Sub-recortes CT&I | `SigFasInovacaoProjeto` (DE 47, PA 24, CS 19, LP 5, IM 4) · `SigTemaProjeto` (10 temas) · `SigTipoProdutoProjeto` (6 tipos) · `IdcSituacaoProjeto` (Concluído 40, Cancelado 28, Em atraso 25, Em execução 6) · `SigSegmentoSetorEletrico` (D 96, G 2, T 1) |
| Valores | R$ 390,1 mi previstos (99 projetos) · R$ 198,7 mi auditados (47 projetos) |
| Ressalva | **Sem município** e sem a ICT executora. Não dá para atribuir a um município |

### 5.5 `aneel_4.5_indqual_conjunto_municipio_BA.csv` — INDQUAL: de-para conjunto elétrico ↔ município (4.5)

| Item | Detalhe |
|---|---|
| Resource | `3f841488-80a8-42f2-a6ca-e0c593b228de` |
| Conteúdo | `IdeConjUnidConsumidoras`, `CodMunicipio` (IBGE), `NomMunicipio` |
| Recorte | `SigUF = BA`, reduzido aos **211 conjuntos ativos em 2025**: 1.262 relações, 415 municípios. A base completa tem 954 conjuntos, a maioria já extinta |
| **Filtro CT&I** | ⬜ **Sem variável CT&I.** É a ponte para levar DEC/FEC (por conjunto) ao município. A relação é N:N |

### 5.6 `aneel_4.5_decfec_conjunto_BA_2025.csv` e `aneel_4.5_decfec_municipio_BA_2025.csv` — DEC e FEC (4.5)

| Item | Detalhe |
|---|---|
| Origem | ZIP `indicadores-continuidade-coletivos-2020-2029` (resource `4493985c-…`, gerado em 05/10/2026), extraído por `scripts/aneel_decfec_ba.py`. **Não usar o datastore desse recurso:** está defasado (jun/2026) e sem vários meses; o conjunto ABRANTES, por exemplo, não tem nenhuma linha de DEC em 2025 |
| Limites | Recurso `indicadores-continuidade-coletivos-limite` (`fd69e1dd-…`), `AnoLimiteQualidade = 2025` |
| Conteúdo por conjunto | `DEC_anual_horas` e `FEC_anual_vezes` (soma dos 12 meses), `consumidores_dez`, `limite_DEC`, `limite_FEC`, `DEC_acima_limite`, `FEC_acima_limite` |
| Conteúdo por município | `n_conjuntos`, `conjuntos`, `DEC_ponderado_horas`, `FEC_ponderado_vezes` (média dos conjuntos que atendem o município, ponderada pelos consumidores do conjunto), `conjuntos_DEC_acima_limite` |
| Recorte | COELBA, só 2025 (último ano completo; 2026 tem 8 meses) |
| **Filtro CT&I** | ⬜ **Sem variável CT&I.** Indicador de contexto: confiabilidade da infraestrutura elétrica |
| Resultado 2025 | 211 conjuntos, 6,2 mi consumidores · **DEC médio BA 9,39 h · FEC médio 3,76** · 46 conjuntos acima do limite de DEC e 14 acima do de FEC · Salvador: DEC 4,59 h / FEC 2,67 · piores DEC: Canavieiras (35,5 h), Cairu (31,6 h), Itacaré (31,2 h) |
| Ressalvas | Jandaíra e Rio Real ficam de fora porque são atendidos pela Sulgipe, não pela COELBA. O peso por consumidores é o do conjunto inteiro, já que o INDQUAL não informa quantos consumidores de cada conjunto estão em cada município |

---

## 6. BNDES

**Fonte:** CKAN `dadosabertos.bndes.gov.br`, dataset `operacoes-financiamento`, `datastore_search`.

| Base | resource_id | Filtro de UF | Linhas BA | CT&I (regra explícita) | Auxiliar | Fora |
|---|---|---|---:|---:|---:|---:|
| Não automáticas | `6f56b78c-510f-44b6-8274-78a5b7e931f4` | `{"uf":"BA"}` | 1.104 | 34 (R$ 697 mi) | 18 | 1.052 |
| Indiretas automáticas | `612faa0b-b6be-4b2c-9317-da5dc2c0b901` | `{"uf":" BA"}` (espaço à esquerda) | 79.860 | 280 (R$ 154 mi) | 297 | 79.283 |
| **Total** | | | **80.964** | **314 (R$ 851 mi, 1,0%)** | 315 | 80.335 |

### 6.1 `bndes_5.x_nao_automaticas_BA_amostra.csv` e `bndes_5.x_indiretas_automaticas_BA_amostra.csv`

| Item | Detalhe |
|---|---|
| Conteúdo | Uma linha por operação: cliente, `municipio_codigo` (IBGE, 100% preenchido), datas, valores contratado/desembolsado, `produto`, `instrumento_financeiro`, **`inovacao`**, `fonte_de_recurso_desembolsos`, CNAE, porte, forma e modalidade de apoio. A base não automática tem também `descricao_do_projeto` |
| Colunas CT&I calculadas | `cti_flag_oficial`, `cti_instrumento`, `cti_fonte_recurso`, `cti_cnae_tecnologico_aux`, `cti_descricao_projeto_aux`, **`cti_motivo`**, **`cti_nivel`** |
| Recorte | UF = BA; textos com `strip()`; estratificada: 15 mais recentes CT&I + 5 auxiliar + 10 fora |
| **Filtro CT&I** | 🏷️ **Classificado, não filtrado** |

**Regra de `cti_nivel`:**

```text
"CT&I (regra explícita)" =  inovacao == "SIM"
                         OR instrumento_financeiro IN (BNDES INOVAÇÃO, INOVAÇÃO, PSI - Inovação,
                              PROGRAMA BNDES MAIS INOVAÇÃO, FUNTEC, BNDES FUNTTEL, BNDES FINAME FUNTTEL,
                              BNDES PROSOFT, BNDES PROENGENHARIA, PSI - Proengenharia, ENGENHARIA AUTOMOTIVA,
                              BNDES PRODESIGN, INDÚSTRIA E SERVIÇOS DIFUSORES DE TECNOLOGIA,
                              PSI - BK - Tecnologia Nacional, BK AQUISIÇÃO E COMERCIALIZAÇÃO – MÁQUINAS 4.0,
                              INOVAGRO, PROGRAMA BNDES FUST, PROGRAMA BNDES FUST AUTOMÁTICO)
                         OR fonte_de_recurso_desembolsos CONTÉM (FUNTTEL | FUST | FNDCT)

"Auxiliar (revisar)"     =  subsetor_cnae_codigo[:3] IN (C21, C26, J61, J62, J63, M72)  OR  [:4] == P853
                         OR descricao_do_projeto ~ /INOVA|PESQUISA|P&D|PD&I|DESENVOLVIMENTO TECNOL|TECNOLOGIA|SOFTWARE|CIENT|LABORAT/

"Fora de CT&I"           =  o restante
```

**Ressalvas:**
- O flag `inovacao` sozinho não basta. **FUST** e **Indústria e Serviços Difusores de Tecnologia** vêm com `inovacao = NÃO`.
- **PROGRAMA BNDES MAIS INOVAÇÃO** (245 operações, todas `inovacao = SIM`) é na prática financiamento de máquinas: 49% dos tomadores são de Construção. Recomenda-se subdividir em "difusão tecnológica / BK" e "P&D e inovação" (FUNTEC, Proengenharia, PSI-Inovação, Inovação, Prosoft).
- Sem `strip()`, `inovacao == "SIM"` acha 207 operações na base indireta, em vez de 269.
- **267 operações não automáticas (R$ 22,8 bi, cerca de 40% do desembolso direto na BA) estão como `SEM MUNICÍPIO`** (código 0 ou 9999999).
- `area_operacional = "AREA DE DESENVOLVIMENTO PRODUTIVO E INOVACAO"` é ampla demais. Não usar como filtro.

### 6.2 `bndes_5.5_cti_por_municipio_ano_BA.csv` — Apoio à inovação por município e ano (5.5)

| Item | Detalhe |
|---|---|
| Conteúdo | `municipio_codigo`, `municipio`, `ano`, `operacoes`, `valor_contratado`, `valor_desembolsado` |
| Recorte | **Completo** (não é amostra): 131 combinações município × ano, 76 municípios, 2002–2026 |
| **Filtro CT&I** | ✅ **Filtrado: `cti_nivel = "CT&I (regra explícita)"`** (as duas bases somadas) |
| Resultado | 314 operações em 76 municípios, 2002–2026. Maiores valores: Camaçari R$ 486 mi, sem município R$ 153 mi, Salvador R$ 98 mi. 271 das 314 operações são de 2024–2026 |

---

## 7. SICONFI / Tesouro

**Fonte:** `apidatalake.tesouro.gov.br/ords/siconfi/tt/`.

### 7.1 `siconfi_6.2_dca_anexoIC_receita_salvador_2024_amostra.csv` — Receita (6.2)

| Item | Detalhe |
|---|---|
| Endpoint | `dca?an_exercicio=2024&no_anexo=DCA-Anexo I-C&id_ente=2927408` |
| Conteúdo | `coluna` (receitas brutas, deduções), `cod_conta`, `conta`, `valor`, `populacao` |
| Recorte | Salvador, 2024, primeiras 40 de 217 linhas |
| **Filtro CT&I** | ⬜ **Sem variável CT&I.** A receita não tem classificação funcional |

### 7.2 `siconfi_6.3_rreo_anexo02_salvador_2025_cti.csv` — Despesa por função (RREO)

| Item | Detalhe |
|---|---|
| Endpoint | `rreo?an_exercicio=2025&nr_periodo=6&co_tipo_demonstrativo=RREO&no_anexo=RREO-Anexo 02&id_ente=2927408` |
| Conteúdo | `coluna` (dotação inicial/atualizada, empenhado, liquidado…), `conta`, `valor` |
| Recorte | Salvador, 2025, 6º bimestre: 52 de 1.468 linhas |
| **Filtro CT&I** | ✅ **Filtrado por texto: `conta` contém "Ciência", "Tecnol" ou "TOTAL".** Contas que ficaram: *Ciência e Tecnologia*, *Desenvolvimento Tecnológico e Engenharia*, *Tecnologia da Informação* e *TOTAL (III)* |
| Ressalva | No RREO o `cod_conta` é genérico (`RREO2TotalDespesas`) e a subfunção não informa a função-mãe. **Para CT&I, preferir o DCA I-E** |

### 7.3 `siconfi_6.3_6.4_dca_IE_BA_2024_ciencia_tecnologia_por_municipio.csv` — Painel de despesa CT&I (6.3, 6.4)

| Item | Detalhe |
|---|---|
| Endpoint | `dca?an_exercicio=2024&no_anexo=DCA-Anexo I-E&id_ente={cod_ibge}` (varredura dos 417) |
| Conteúdo | Uma linha por município: `liquidado_total`, **`liquidado_funcao19_CT`**, **`liquidado_subf_571_572_573`**, `liquidado_subf_126_TI`, `populacao_2024`, `CT_por_habitante`, `CT_pct_despesa` |
| Recorte | 415 municípios (2 sem DCA 2024); estágio **Despesas Liquidadas** |
| **Filtro CT&I** | 🏷️ **Classificado em colunas.** As linhas não são filtradas (todos os municípios aparecem); as colunas CT&I são somas das contas filtradas |

**Filtros que geram as colunas:**

| Coluna | Filtro sobre `conta` do DCA I-E | Nível |
|---|---|---|
| `liquidado_funcao19_CT` | começa com `19 - ` (Função 19, Ciência e Tecnologia) | **Principal** |
| `liquidado_subf_571_572_573` | subfunção ∈ {571 Desenv. Científico, 572 Desenv. Tecnológico e Engenharia, 573 Difusão do Conhecimento} | Principal (detalhe) |
| `liquidado_subf_126_TI` | subfunção = 126 (Tecnologia da Informação) | Auxiliar (TI da prefeitura, não é fomento) |

Outros filtros auxiliares disponíveis em `categorias_cti/siconfi_funcoes_subfuncoes_BA_relacao_cti.csv`: `12.364` Ensino Superior, `12.363` Ensino Profissional e Função `24` Comunicações.

**Resultado 2024:** só **8 de 415** municípios liquidaram despesa na Função 19, somando R$ 126,49 mi:

| Município | Função 19 liquidada (R$) |
|---|---:|
| Salvador | 120.131.322,15 |
| Luís Eduardo Magalhães | 4.728.198,72 |
| Mucuri | 1.240.480,19 |
| Monte Santo | 290.514,07 |
| Itacaré | 48.960,00 |
| Lauro de Freitas | 42.058,31 |
| Ibipitanga | 6.400,00 |
| Madre de Deus | 1.582,50 |

Subfunção 126 (TI): 39 municípios, R$ 99,1 mi.
⚠️ O DCA agrupa subfunções pequenas em `FUxx - Demais Subfunções`, por isso a 571 não aparece isolada. **O filtro principal deve ser a Função 19 inteira.**

---

## 8. ANATEL

**Fonte:** `anatel.gov.br/dadosabertos/paineis_de_dados/acessos/acessos_banda_larga_fixa.zip` (1,05 GB), lido por HTTP Range (`scripts/httpzip.py`).

### 8.1 `anatel_7.1_densidade_scm_BA_amostra.csv` — Densidade SCM por 100 domicílios (7.1)

| Item | Detalhe |
|---|---|
| Membro do ZIP | `Densidade_Banda_Larga_Fixa.csv` |
| Conteúdo | `Ano`, `Mês`, `Município`, `Código IBGE`, `Densidade`, `Nível Geográfico Densidade`, `periodo`, **`alerta`** |
| Recorte | Nível = Município; Salvador, Feira de Santana, Vitória da Conquista, Camaçari, Ilhéus × anos 2021, 2022, 2025, 2026 (17 linhas com `alerta = valor anômalo`) |
| **Filtro CT&I** | ⬜ **Sem variável categórica.** O indicador inteiro é de infraestrutura TIC |

| Período | Situação na BA |
|---|---|
| 2007–2022 | ✅ 415–417 municípios por ano |
| 2023 e 2024 | ❌ Linhas vazias (UF, município e densidade) para todo o Brasil |
| 2025 | ❌ Só dezembro, 38 municípios |
| dez/2025 – mar/2026 | ⚠️ Valores anômalos (Salvador 0,016 a 0,21 contra ≈ 21) |
| abr/2026 em diante | ✅ 417 municípios, valores coerentes |

Para 2023–2025, recalcular com `acessos ÷ domicílios (Censo 2022) × 100` e marcar como **derivado**.

### 8.2 `anatel_acessos_bl_fixa_2026_BA_amostra.csv` — Acessos por tecnologia e velocidade (complementar)

| Item | Detalhe |
|---|---|
| Membro do ZIP | `Acessos_Banda_Larga_Fixa_2026_Colunas.csv` |
| Conteúdo | `CNPJ`, `Empresa`, `Porte da Prestadora`, `Tecnologia`, `Meio de Acesso`, `Faixa de Velocidade`, `Tipo de Produto`, `Código IBGE Município`, acessos mensais de 2026-01 a 2026-08 |
| Recorte | UF = BA, municípios de referência, 40 linhas com mais acessos em ago/2026 |
| **Filtro CT&I** | 🔶 **Não filtrado.** Recortes auxiliares de conectividade avançada |

| Campo | Valor CT&I (auxiliar) | Acessos BA (ago/2026) |
|---|---|---:|
| `Meio de Acesso` | = Fibra | 2.079.476 (88,8%) |
| `Tecnologia` | ∈ {FTTH, FTTB} | 1.877.773 + 8.455 |
| `Faixa de Velocidade` | = > 34Mbps | 2.176.069 (92,9%) |

### 8.3 `anatel_7.2_cobertura_movel_4g_BA.csv` — Cobertura da Telefonia Móvel SMP 4G (7.2)

**Origem:** Recurso `1449ea53-fe84-4547-8ac8-f6a465995958` (Painel de Cobertura Móvel / Dados Abertos da Anatel).

| Item | Detalhe |
|---|---|
| Arquivo gerado | `amostras/anatel_7.2_cobertura_movel_4g_BA.csv` |
| Aba na planilha | `ANATEL_Cobertura_Movel` em `TERRITORIOS_SECTI_Amostras_CTI.xlsx` |
| Conteúdo | `Código Município`, `Município`, `UF`, `Região`, `Operadora`, `Tecnologia`, `% área coberta`, `% moradores cobertos`, `% domicílios cobertos`, `Área km2`, `Moradores`, `Domicílios` |
| Recorte | Todos os **417 municípios da Bahia**, operadora `Todas`, tecnologia `4G` |
| **Filtro CT&I** | ⬜ **Sem variável categórica.** Métrica de infraestrutura digital habilitadora |

#### Estatísticas e destaques na Bahia

| Indicador | Média BA | Mínimo | Mediana | Máximo |
|---|---:|---:|---:|---:|
| **% Moradores cobertos** | **73,90%** | 29,66% (Jucuruçu) | 76,37% | 100,00% (Lauro de Freitas, Madre de Deus, Itaparica) |
| **% Área coberta** | **35,36%** | 3,10% (Barra) | 28,02% | 100,00% (Lauro de Freitas) |
| **% Domicílios cobertos** | **71,83%** | 27,24% (Jucuruçu) | 74,43% | 100,00% (Lauro de Freitas, Madre de Deus, Itaparica) |

- **Top 5 municípios em % de moradores cobertos (4G):**
  1. Lauro de Freitas (100,00% moradores \| 100,00% área)
  2. Madre de Deus (100,00% moradores \| 97,87% área)
  3. Itaparica (100,00% moradores \| 98,93% área)
  4. Salvador (99,99% moradores \| 89,39% área)
  5. Salinas da Margarida (99,96% moradores \| 96,67% área)

- **Bottom 5 municípios em % de moradores cobertos (4G):**
  1. Jucuruçu (29,66% moradores \| 7,04% área)
  2. Baianópolis (30,04% moradores \| 4,27% área)
  3. Ribeirão do Largo (30,89% moradores \| 9,16% área)
  4. Ibitiara (32,28% moradores \| 8,11% área)
  5. Itaguaçu da Bahia (34,98% moradores \| 4,48% área)

- **Amostra nos municípios de referência SECTI:**
  - Salvador: 99,99% moradores cobertos \| 89,39% área
  - Feira de Santana: 97,29% moradores cobertos \| 60,67% área
  - Camaçari: 97,22% moradores cobertos \| 66,22% área
  - Vitória da Conquista: 91,48% moradores cobertos \| 32,59% área
  - Barreiras: 91,15% moradores cobertos \| 9,06% área
  - Paulo Afonso: 91,24% moradores cobertos \| 18,37% área
  - Ilhéus: 91,01% moradores cobertos \| 30,55% área
  - Juazeiro: 86,41% moradores cobertos \| 12,89% área

#### Regras de limpeza
O arquivo original continha 421 linhas para a UF BA. Foram identificadas 4 duplicatas com grafias variantes e valores zerados/hífen (`Araçás`, `Iuiu`, `Muquém do São Francisco`, `Santa Terezinha` com moradores = 0 e % = `-`). Essas 4 linhas foram expurgadas, mantendo exatamente os 417 municípios oficiais da Bahia com dados 100% preenchidos.


---

## 9. Arquivos de categorias (`categorias_cti/`)

| Arquivo | Fonte | O que contém |
|---|---|---|
| `filtros_cti_consolidado.csv` | Todas | Um filtro por linha: campo, operador, valores, nível (principal/auxiliar/recorte) e se foi validado nos dados |
| `inep_cine_areas_BA_nivel_cti.csv` | INEP | 80 áreas CINE detalhadas presentes na BA, com `nivel_cti`, nº de cursos e matrículas |
| `inep_cine_rotulos_BA_nivel_cti.csv` | INEP | 240 rótulos CINE (ex.: Enfermagem, Engenharia química), com `nivel_cti` e matrículas |
| `inep_outras_categorias_BA.csv` | INEP | Códigos de organização acadêmica, categoria administrativa, dimensão, grau e modalidade, com uso CT&I |
| `bndes_valores_categoricos_BA_relacao_cti.csv` | BNDES | 366 valores de todas as colunas categóricas, com nº de operações, desembolso, nº com `inovacao = SIM` e relação CT&I |
| `bndes_subsetores_cnae_BA.csv` | BNDES | 1.172 subsetores CNAE, com flag `cnae_tecnologico_aux` |
| `bndes_resumo_niveis_cti_BA.csv` | BNDES | Contagem e desembolso por base × `cti_nivel` |
| `bndes_cti_instrumento_x_flag_inovacao_BA.csv` | BNDES | Cruzamento produto × instrumento × `inovacao` dentro do conjunto CT&I |
| `siconfi_funcoes_subfuncoes_BA_relacao_cti.csv` | SICONFI | 164 funções/subfunções do DCA I-E 2024 na BA, com municípios, valor liquidado e relação CT&I |
| `anatel_categorias_acessos_BA.csv` | ANATEL | Valores de tecnologia, meio de acesso, faixa de velocidade, tipo de produto, tipo de pessoa e porte, com acessos |

---

## 10. Divergências entre os `.md` anteriores (já corrigidas aqui)

| Ponto | `OUTRAS_APIS_…md` dizia | Valor conferido nos CSVs |
|---|---|---|
| Matrículas STEM | "67.325 matrículas **presenciais**" | 67.325 é **presencial + EAD**. Só presencial: 36.753 |
| Cursos presenciais STEM por área (tabela 3.2) | 99 + 549 + 631 cursos | Total presencial STEM = 399 cursos. Os números da tabela misturam linhas EAD |
| Municípios com Função 19 em 2024 | Inclui Irecê, Iaçu e Macururé, com valores diferentes | Os 8 são Salvador, LEM, Mucuri, Monte Santo, Itacaré, Lauro de Freitas, Ibipitanga e Madre de Deus (tabela do §7.3) |
| ANEEL | `RESULTADOS_AMOSTRAGEM_CTI.md` dizia "não testado" | Amostras extraídas via IP sem SNI (§5) |
| BNDES `inovacao = SIM` | 259 operações (R$ 684 mi) | 300 operações (R$ 767 mi), em `bndes_valores_categoricos_BA_relacao_cti.csv` |
| BNDES porte do cliente | MICRO 45.394 · PEQUENA 27.234 · MÉDIA 5.932 · GRANDE 2.404 | MICRO 30.754 · PEQUENA 20.761 · MÉDIA 17.117 · GRANDE 12.332 |
| BNDES forma de apoio | DIRETA 1.104 · INDIRETA 79.860 (confundia com as duas bases) | DIRETA 916 · INDIRETA 80.048 (parte da base "não automática" é indireta) |

---

## 11. Como reproduzir

```bash
# 1. caches (pasta à escolha)
python scripts/bndes_download_ba.py cache            # ~81 mil operações BA (datastore CKAN)
python scripts/siconfi_dca_ba.py 2024 cache          # DCA I-E dos 417 municípios
curl -o cache/inep_2024.zip https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2024.zip
#    extrair MICRODADOS_*.CSV e o dicionário como cache/inep_<nome>; ANATEL: usar scripts/httpzip.py
#    para extrair Densidade_Banda_Larga_Fixa.csv e Acessos_Banda_Larga_Fixa_2026_Colunas.csv
# 2. amostras + categorias + status (IBGE, INEP, BNDES, SICONFI, ANATEL)
python scripts/gerar_amostras.py cache
# 3. ANEEL
python scripts/aneel_probe.py                 # lista recursos (de rede sem bloqueio de SNI)
python scripts/extrair_amostras_aneel_ba.py   # extrai SIGA, P&D, INDQUAL, INDGER e SAMP via IP sem SNI
python scripts/aneel_decfec_ba.py 2025 cache  # DEC/FEC por conjunto e município (ZIP oficial) + INDQUAL dos conjuntos ativos
# 4. IBGE PIB per capita oficial (depois do passo 2, pois reescreve a amostra de derivados)
python scripts/ibge_pib_per_capita_oficial.py 2023 cache
# 5. entregáveis: planilha única e os dois DOCX
python scripts/gerar_planilha_amostras.py
node scripts/gerar_docx_executivo.js TERRITORIOS_SECTI_Resumo_Executivo_Dados.docx
node scripts/gerar_docx_executivo.js TERRITORIOS_SECTI_Resumo_Executivo_Planilha.docx excel
```

O certificado de `download.inep.gov.br` falha no Python (cadeia incompleta no certifi), por isso o download é com curl. Os IDs de recurso BNDES e ANEEL podem mudar; nesse caso, consultar `package_show`.

---

## 12. Pendências

**Resolvidas em 07/10/2026:**
- ~~Status da ANEEL~~: `status_validacao_fontes.csv` e `filtros_cti_consolidado.csv` atualizados (a linha malformada do filtro BNDES/`instrumento_financeiro` também foi corrigida).
- ~~ANEEL DEC/FEC~~: extraído 2025 por conjunto e por município (§5.6).
- ~~PIB per capita 2023~~: base oficial do PIB dos Municípios para os 417 municípios (§3).

**Em aberto:**
1. **Lista SECTI de 642 cursos CT&I:** colocar na pasta para virar o filtro principal do INEP.
2. **BNDES `SEM MUNICÍPIO`:** definir regra de rateio ou deixar fora do painel municipal (cerca de 40% do valor direto).
3. **ANATEL 2023–2025:** só é preciso recalcular a densidade se o painel for mostrar série histórica. Para o valor atual, a série publicada a partir de abr/2026 está coerente.
4. **Territórios de Identidade:** a tabela município → território (27 TIs) não está na pasta. Todas as amostras têm código IBGE (o SIGA tem só o nome) para a junção.

# TERRITÓRIOS SECTI — Resultado da validação das fontes, amostras e filtros CT&I

**Coleta:** 05/10/2026 · **Escopo:** fontes de `APIs_TERRITORIOS_SECTI_extracao_planilha.md`, recorte Bahia (417 municípios)
**Arquivos gerados:**

| Pasta / arquivo | Conteúdo |
|---|---|
| [status_validacao_fontes.csv](status_validacao_fontes.csv) | Status de cada indicador (validado / parcial / não testado), nº de linhas, URL testada e observações |
| [amostras/](amostras/) | Amostra de dados reais de cada fonte (CSV UTF-8 com BOM, abre direto no Excel) |
| [categorias_cti/](categorias_cti/) | Todos os valores das colunas categóricas (com contagem e valor na BA) e a relação de cada um com CT&I |
| [categorias_cti/filtros_cti_consolidado.csv](categorias_cti/filtros_cti_consolidado.csv) | **Lista única de filtros CT&I por fonte**: campo, operador, valores, nível (principal/auxiliar) e justificativa |
| [scripts/](scripts/) | Scripts que reproduzem tudo (ver §8) |

---

## 1. Resumo executivo

| Fonte | Resultado | Variável categórica CT&I? | Filtro CT&I recomendado |
|---|---|---|---|
| **IBGE** | ✅ População, PIB, área e malha validados para os 417 municípios. ⚠️ PIB per capita municipal **não** existe na tabela 6784 | **Não**: as tabelas do catálogo não têm classificação CT&I | — (denominadores e contexto) |
| **INEP** (Censo Sup. 2024) | ✅ IES, cursos, vagas, matrículas, ingressantes e concluintes validados. Docentes só no nível da IES | **Sim**: CINE (área geral, específica, detalhada e rótulo), grau tecnológico, IF/CEFET | `CO_CINE_AREA_GERAL ∈ {05, 06, 07}` (núcleo STEM). Ampliado: `{08, 09}` |
| **ANEEL** | ❌ **Não testado**: o servidor recusa a conexão a partir desta rede (§6) | P&D ANEEL é CT&I por definição | Ver §6 |
| **BNDES** | ✅ 80.964 operações da BA baixadas (1.104 não automáticas + 79.860 indiretas automáticas), 2002–2026, com código IBGE | **Sim**: campo **`inovacao` (SIM/NÃO)**, `instrumento_financeiro`, `fonte_de_recurso_desembolsos` | `inovacao = SIM` **OU** `instrumento_financeiro` ∈ lista CT&I **OU** fonte FUNTTEL/FUST |
| **SICONFI** | ✅ RREO e DCA validados; DCA 2024 varrido para **415/417** municípios | **Sim**: **Função 19 – Ciência e Tecnologia** e subfunções 571/572/573 | Conta começando com `19 - ` no DCA Anexo I-E |
| **ANATEL** | ⚠️ Densidade SCM validada, **mas com lacuna em 2023–2024 e valores anômalos entre dez/2025 e mar/2026** | Densidade: não. Arquivo de acessos: tecnologia, meio de acesso, faixa de velocidade | Infraestrutura TIC: `Meio de Acesso = Fibra`, `Faixa > 34Mbps` |

**O que muda em relação à planilha:**
1. **IBGE 2.3:** a tabela 6784 só tem nível Brasil (N1). O PIB per capita municipal precisa vir do XLSX oficial do PIB dos Municípios, ou ser derivado (PIB 5938 ÷ população). Derivei 2022 com a população do Censo (agregado 4709). **2023 não tem população municipal oficial no SIDRA**, porque a 6579 pula 2007, 2010, 2022 e 2023.
2. **INEP 3.7:** não existe mais microdado público de docente. A titulação vem agregada por IES (`QT_DOC_EX_DOUT/MEST/ESP`), sem município de lotação.
3. **BNDES:** existe um flag oficial `inovacao`, então não é preciso inferir pela linha. Mas ele sozinho não basta (§4.2).
4. **ANATEL 7.1:** a série publicada de densidade está **vazia em 2023 e 2024 para todos os municípios**.
5. **SICONFI:** só **8 dos 415** municípios baianos com DCA 2024 liquidaram despesa na Função 19 (C&T).

---

## 2. IBGE

| Indicador | Endpoint testado | Resultado |
|---|---|---|
| 2.1 População | `servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/-3/variaveis/9324?localidades=N6[N3[29]]` | 417 municípios; anos 2024, 2025 e 2026 |
| 2.2 PIB + VAB | `…/agregados/5938/periodos/-2/variaveis/37\|498\|513\|517\|6575\|525\|543?localidades=N6[N3[29]]` | 417 municípios; 2022–2023 (mil R$) |
| 2.3 PIB per capita | `…/agregados/6784/metadados` | ⚠️ só nível N1 (Brasil). Derivado: 2022 = PIB ÷ Censo 2022 (`4709/var 93`) |
| 2.4 Área | `…/api/v3/malhas/estados/29/metadados?intrarregiao=municipio` | 417 áreas (km²) + centroides |
| 2.7 Malha | `…/api/v3/malhas/estados/29?intrarregiao=municipio&formato=application/vnd.geo+json` | 417 polígonos, `codarea` = código IBGE |

**Categorias CT&I:** nenhuma. A 5938 abre o VAB só em agropecuária, indústria, serviços e administração pública, e as demais tabelas não têm classificação.
**Amostras:** `ibge_2.1_populacao_6579_BA.csv` (417 × 3 anos), `ibge_2.2_pib_vab_5938_BA.csv`, `ibge_2.4_area_centroide_BA.csv`, `ibge_2.7_malha_amostra_BA.csv`, `ibge_2.3_2.5_2.6_derivados_amostra_BA.csv`.

---

## 3. INEP — Censo da Educação Superior 2024

**Fonte:** `https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2024.zip` (457 MB). Arquivos: `MICRODADOS_ED_SUP_IES_2024.CSV` (84 colunas) e `MICRODADOS_CADASTRO_CURSOS_2024.CSV` (223 colunas). Separador `;`, codificação latin1.

**Números da Bahia (2024):**
- **145 IES com sede na BA**, em 45 municípios: 107 faculdades, 25 centros universitários, 11 universidades e 2 IFs. Somam 10.022 docentes doutores em exercício.
- **Presencial:** 1.851 cursos em 56 municípios, com 254.041 matrículas. **Núcleo STEM:** 399 cursos em 38 municípios, com 36.753 matrículas.
- **EAD:** linhas em 322 municípios/polos, com 247.820 matrículas.

**Regras confirmadas no dicionário oficial:**
- `TP_DIMENSAO`: 1 = presencial, 2 = EAD por município, 3 = EAD só nível Brasil, 4 = EAD no exterior. **Vagas e inscritos de EAD não são calculados por município** (nota do dicionário), então não se deve somá-los ao presencial.
- O arquivo IES traz só o município da **sede/reitoria**. Campus e polo saem do `CO_MUNICIPIO` do arquivo de cursos.

### 3.1 Variáveis categóricas e relação com CT&I

| Campo | Valores | Uso CT&I |
|---|---|---|
| `CO_CINE_AREA_GERAL` | 00 Programas básicos · 01 Educação · 02 Artes e humanidades · 03 Ciências sociais · 04 Negócios/direito · **05 Ciências naturais, matemática e estatística** · **06 Computação e TIC** · **07 Engenharia, produção e construção** · 08 Agricultura/veterinária · 09 Saúde e bem-estar · 10 Serviços | **05/06/07 = núcleo**; 08/09 = ampliado |
| `CO_CINE_AREA_ESPECIFICA` / `_DETALHADA` / `CO_CINE_ROTULO` | 80 áreas detalhadas e 240 rótulos presentes na BA | Lista completa em `categorias_cti/inep_cine_*` |
| `TP_GRAU_ACADEMICO` | 1 Bacharelado · 2 Licenciatura · **3 Tecnológico** · 4 Bach. e Lic. | Auxiliar |
| `TP_ORGANIZACAO_ACADEMICA` | 1 Universidade · 2 Centro Universitário · 3 Faculdade · **4 IF** · **5 CEFET** | Auxiliar (instituição tecnológica) |
| `TP_CATEGORIA_ADMINISTRATIVA`, `TP_REDE`, `TP_MODALIDADE_ENSINO` | — | Dimensões de recorte |
| IES: `QT_DOC_EX_DOUT`, `QT_DOC_EX_MEST`, `IN_REPOSITORIO_INSTITUCIONAL`, `IN_ACESSO_PORTAL_CAPES` | — | Capacidade de pesquisa |

> **Lista SECTI de 642 cursos CT&I:** a planilha cita correspondência de 641/642 em 2023, mas a lista não estava nesta pasta. O filtro por CINE é a aproximação reproduzível. Quando a lista estiver disponível, ela entra como camada separada por `CO_CURSO`/`CO_CINE_ROTULO`.

**Amostras:** `inep_3.1_3.7_ies_BA_amostra.csv`, `inep_3.2_a_3.6_cursos_BA_amostra.csv` (com coluna `nivel_cti`), `inep_cursos_presenciais_por_municipio_nivel_cti_amostra.csv`.

---

## 4. BNDES

**Fonte:** CKAN `dadosabertos.bndes.gov.br`, dataset `operacoes-financiamento`, via `datastore_search` (o endpoint SQL devolve 403).

| Recurso | resource_id | Filtro | Linhas BA |
|---|---|---|---|
| Operações não automáticas (diretas e indiretas não automáticas) | `6f56b78c-510f-44b6-8274-78a5b7e931f4` | `{"uf":"BA"}` | 1.104 |
| Operações indiretas automáticas (FINAME, BNDES Automático…) | `612faa0b-b6be-4b2c-9317-da5dc2c0b901` | `{"uf":" BA"}` ← **a UF tem um espaço à esquerda** | 79.860 |

**Campos territoriais:** `municipio_codigo` é o código IBGE de 7 dígitos e está 100% preenchido. ⚠️ Porém **267 operações não automáticas (R$ 22,8 bi, cerca de 40% do desembolso direto na BA) vêm como `SEM MUNICÍPIO`** (código 0 ou 9999999). São sobretudo concessionárias com projetos multimunicipais (Coelba, Concrod, Embasa, Veracel). Elas não podem ser atribuídas a um município sem uma regra adicional.

### 4.1 Colunas categóricas (todos os valores em `categorias_cti/bndes_valores_categoricos_BA_relacao_cti.csv`)

| Coluna | Nº de valores na BA | Relação com CT&I |
|---|---|---|
| **`inovacao`** | 2 (SIM/NÃO) | **Principal**: flag oficial |
| **`instrumento_financeiro`** | 140+ | **Principal** para os instrumentos listados em §4.2 |
| **`fonte_de_recurso_desembolsos`** | 42 + 9 | **Principal** quando contém FUNTTEL ou FUST |
| `area_operacional` | 10 | Auxiliar: "Área de Desenvolvimento Produtivo e Inovação" é ampla demais |
| `subsetor_cnae_codigo` / `_nome` / `_agrupado` | 1.091 códigos | Auxiliar: C21, C26, J61, J62, J63, M72 (lista em `bndes_subsetores_cnae_BA.csv`) |
| `produto` | 11 + 5 | Recorte (FINEM, FINAME, Não Reembolsável…) |
| `setor_bndes`, `subsetor_bndes`, `setor_cnae` | 4 / 20 / 4 | Recorte (5.2) |
| `porte_do_cliente` | MICRO, PEQUENA, MÉDIA, GRANDE | Recorte (5.3) |
| `forma_de_apoio` | DIRETA, INDIRETA | Recorte (5.4) |
| `modalidade_de_apoio` | REEMBOLSÁVEL, NÃO REEMBOLSÁVEL | Recorte |
| `natureza_do_cliente`, `custo_financeiro`, `situacao_*`, `tipo_de_garantia` | — | Não relacionados |

### 4.2 Filtro CT&I recomendado (regra explícita e auditável)

```text
CT&I = inovacao == "SIM"
    OR instrumento_financeiro IN (
        BNDES INOVAÇÃO, INOVAÇÃO, PSI - Inovação, PROGRAMA BNDES MAIS INOVAÇÃO, FUNTEC,
        BNDES FUNTTEL, BNDES FINAME FUNTTEL, BNDES PROSOFT, BNDES PROENGENHARIA,
        PSI - Proengenharia, ENGENHARIA AUTOMOTIVA, BNDES PRODESIGN,
        INDÚSTRIA E SERVIÇOS DIFUSORES DE TECNOLOGIA, PSI - BK - Tecnologia Nacional,
        BK AQUISIÇÃO E COMERCIALIZAÇÃO – MÁQUINAS 4.0, INOVAGRO,
        PROGRAMA BNDES FUST, PROGRAMA BNDES FUST AUTOMÁTICO)
    OR fonte_de_recurso_desembolsos CONTÉM ("FUNTTEL" | "FUST" | "FNDCT")
Auxiliar (revisão manual) = CNAE tecnológico  OR  descricao_do_projeto ~ /INOVA|PESQUISA|P&D|TECNOLOG|SOFTWARE|.../
```

Cada operação recebe as colunas `cti_nivel` e `cti_motivo`, que registram por que entrou no conjunto, como exige a regra 5.5.

**Resultado na BA (2002–2026):** **314 operações CT&I, R$ 851 mi desembolsados, 1,0% do total**, distribuídas em 76 municípios. Os maiores valores estão em Camaçari (R$ 486 mi), em operações sem município (R$ 153 mi) e em Salvador (R$ 98 mi). O volume se concentra em 2024–2026: 271 das 314 operações.

**Ressalvas encontradas nos dados:**
- **`PROGRAMA BNDES MAIS INOVAÇÃO` (FINAME) tem 245 operações na BA, todas com `inovacao = SIM`, mas 49% dos tomadores são de Construção e 18% de atividades imobiliárias/administrativas.** Na prática é financiamento de máquinas com conteúdo tecnológico. Recomendação: manter no conjunto CT&I, porém como subcategoria **"difusão tecnológica / aquisição de BK"**, separada de **"P&D e inovação"** (FUNTEC, Proengenharia, PSI-Inovação, Inovação, Prosoft).
- **FUST e Indústria e Serviços Difusores de Tecnologia** vêm com `inovacao = NÃO`. Usar só o flag oficial deixaria essas operações de fora.
- Os textos têm espaços extras. Na base indireta, `inovacao == "SIM"` sem `strip()` encontra 207 operações; com `strip()`, encontra 269. A UF também vem como `" BA"`. Aplique `strip()` em todas as colunas de texto antes de filtrar.

**Amostras:** `bndes_5.x_nao_automaticas_BA_amostra.csv`, `bndes_5.x_indiretas_automaticas_BA_amostra.csv` (CT&I + auxiliar + fora), `bndes_5.5_cti_por_municipio_ano_amostra.csv`. Categorias: `bndes_valores_categoricos_BA_relacao_cti.csv`, `bndes_subsetores_cnae_BA.csv`, `bndes_resumo_niveis_cti_BA.csv`, `bndes_cti_instrumento_x_flag_inovacao_BA.csv`.

---

## 5. SICONFI / Tesouro

| Indicador | Endpoint | Resultado |
|---|---|---|
| 6.2 Receita | `apidatalake.tesouro.gov.br/ords/siconfi/tt/dca?an_exercicio=2024&no_anexo=DCA-Anexo I-C&id_ente=2927408` | 217 linhas (Salvador) |
| 6.3 Despesa (RREO) | `…/tt/rreo?an_exercicio=2025&nr_periodo=6&co_tipo_demonstrativo=RREO&no_anexo=RREO-Anexo 02&id_ente=2927408` | 1.468 linhas (Salvador) |
| 6.3 Despesa (DCA) | `…/tt/dca?an_exercicio=2024&no_anexo=DCA-Anexo I-E&id_ente={cod_ibge}` | **415 de 417** municípios BA (2 sem DCA 2024) |

**Por que usar o DCA I-E para filtrar CT&I:** no RREO Anexo 02 o `cod_conta` é genérico (`RREO2TotalDespesas`) e a linha de subfunção não informa a função-mãe. Em Salvador, por exemplo, "Desenvolvimento Tecnológico e Engenharia" aparece com R$ 131 mi de dotação sem indicar a qual função pertence. No DCA I-E a conta vem como `19 - Ciência e Tecnologia` ou `19.572 - …`, com o código.

### 5.1 Categorias (lista completa em `categorias_cti/siconfi_funcoes_subfuncoes_BA_relacao_cti.csv`)

| Conta (DCA I-E) | Municípios BA com valor | Liquidado BA 2024 | Relação |
|---|---|---|---|
| **19 - Ciência e Tecnologia** | **8** | R$ 126,5 mi | **Principal** |
| 19.572 - Desenvolvimento Tecnológico e Engenharia | 1 (Salvador) | R$ 49,8 mi | Principal |
| 19.573 - Difusão do Conhecimento Científico e Tecnológico | 3 | R$ 0,35 mi | Principal |
| 19.122 Adm. Geral / FU19 Demais Subfunções | 3 | R$ 76,3 mi | Principal (dentro da F19) |
| xx.126 - Tecnologia da Informação | 39 | R$ 99,1 mi | Auxiliar: TI da própria prefeitura, não é fomento |
| 12.364 Ensino Superior / 12.363 Ensino Profissional | 75 / 8 | R$ 47,3 mi / 1,3 mi | Auxiliar |
| 24 - Comunicações (inclui 24.722 Telecom) | 17 | R$ 124,6 mi | Auxiliar |

⚠️ O DCA agrupa subfunções pequenas em `FUxx - Demais Subfunções`. Por isso a subfunção 571 (Desenvolvimento Científico) não aparece isolada. **O filtro principal deve ser a Função 19 inteira.**

**Municípios com Função 19 em 2024:** Salvador (R$ 120,1 mi; R$ 46,76/hab; 1,0% da despesa), Luís Eduardo Magalhães (R$ 4,7 mi), Mucuri (R$ 1,2 mi), Monte Santo, Itacaré, Lauro de Freitas, Ibipitanga e Madre de Deus.

**Amostras:** `siconfi_6.3_6.4_dca_IE_BA_2024_ciencia_tecnologia_por_municipio.csv` (415 municípios: total, F19, subfunções 571–573, TI, população, C&T por habitante e % da despesa), `siconfi_6.3_rreo_anexo02_salvador_2025_cti.csv`, `siconfi_6.2_dca_anexoIC_receita_salvador_2024_amostra.csv`.

---

## 6. ANEEL — não testado (bloqueio de conexão)

O servidor `dadosabertos.aneel.gov.br` (200.198.220.169) **encerra o handshake TLS sempre que o cliente envia o SNI `dadosabertos.aneel.gov.br`**. Testei com curl (schannel), Python/OpenSSL e WebFetch, e o resultado foi o mesmo. Uma conexão **sem SNI** completa normalmente e apresenta um certificado válido `*.aneel.gov.br`, o que indica um filtro de rede ou WAF baseado no SNI. Não usei o contorno de conectar pelo IP. O espelho `dadosabertos-aneel.opendata.arcgis.com` só tem BDGD (geodatabases das distribuidoras) e dois PDFs, nada de SIGA, SAMP, P&D ou DEC/FEC.

**O que fazer:** rodar `python scripts/aneel_probe.py` em outra rede (rede institucional, VPN ou servidor). O script lista os recursos de SIGA, SAMP, P&D e DEC/FEC e salva amostras e valores categóricos. Recurso já identificado por busca pública: SIGA, `siga-empreendimentos-geracao-diario.csv` (resource `2f65a1b0-19b8-4360-8238-b34ab4693d55`, dataset `6d90b77c-c5f5-4d81-bdec-7bc619494bb9`).

**Filtros CT&I esperados (a confirmar nos dicionários):** o dataset **P&D ANEEL** é CT&I por inteiro, bastando filtrar por UF/município da executora. No **SIGA**, o tipo/fonte de geração separa solar (UFV) e eólica (EOL) como transição energética, de uso auxiliar. Nenhum nome de campo da ANEEL foi preenchido sem verificação (regra 9).

---

## 7. ANATEL

**Fonte:** `https://www.anatel.gov.br/dadosabertos/paineis_de_dados/acessos/acessos_banda_larga_fixa.zip` (1,05 GB). Lido remotamente por HTTP Range, extraindo só os membros necessários.

| Membro do ZIP | Colunas |
|---|---|
| `Densidade_Banda_Larga_Fixa.csv` | Ano; Mês; UF; Município; Código IBGE; Densidade; Nível Geográfico Densidade |
| `Acessos_Banda_Larga_Fixa_2026_Colunas.csv` | CNPJ; Velocidade; Município; UF; Faixa de Velocidade; **Tecnologia**; Empresa; Porte da Prestadora; Tipo de Pessoa; Tipo de Produto; Código IBGE Município; Grupo Econômico; **Meio de Acesso**; 2026-01 … 2026-08 |
| `Densidades.pdf` | Metadados: banda larga fixa = acessos por **100 domicílios** |

### 7.1 Problemas de qualidade na densidade (verificados)

| Período | Situação na BA |
|---|---|
| 2007–2022 | ✅ 415–417 municípios por ano |
| **2023 e 2024** | ❌ **Linhas presentes, mas UF, município e densidade vazios para todo o Brasil** (752 mil linhas totalmente vazias no arquivo) |
| 2025 | ❌ Só dezembro, para 38 municípios |
| **dez/2025 – mar/2026** | ⚠️ Valores anômalos: Salvador 0,016 a 0,21 contra cerca de 21 antes e depois; BA 0,20 a 1,53 contra cerca de 15,6 |
| abr/2026 em diante | ✅ 417 municípios, valores coerentes (Salvador ≈ 21, BA ≈ 15,7) |

**Recomendação:** usar a densidade publicada para 2007–2022 e a partir de abr/2026. Para 2023–2025, recalcular com `acessos (arquivos anuais) ÷ domicílios (Censo 2022) × 100` e marcar o valor como **derivado**.

### 7.2 Categorias (acessos BA, ago/2026, em `categorias_cti/anatel_categorias_acessos_BA.csv`)

- **Meio de Acesso:** Fibra 2,08 mi · Cabo Coaxial 107 mil · Rádio 81 mil · Satélite 41 mil · Cabo Metálico 35 mil
- **Tecnologia:** FTTH 1,88 mi · Ethernet 202 mil · HFC 99 mil · Wi-Fi 80 mil · VSAT 40 mil · … (21 valores)
- **Faixa de Velocidade:** > 34 Mbps 2,18 mi (93%) · 12–34 Mbps · 2–12 Mbps · 512 kbps–2 Mbps · até 512 kbps
- **Tipo de Produto:** INTERNET, LINHA_DEDICADA, M2M, OUTROS

O indicador é todo de infraestrutura TIC. Para um recorte de "conectividade avançada", use `Meio de Acesso = Fibra` e `Faixa de Velocidade = > 34Mbps`.

**Amostras:** `anatel_7.1_densidade_scm_BA_amostra.csv` (com coluna `alerta`), `anatel_acessos_bl_fixa_2026_BA_amostra.csv`.

---

## 8. Como reproduzir

```bash
# 1. caches (pasta à escolha)
python scripts/bndes_download_ba.py cache            # ~81 mil operações BA (datastore CKAN)
python scripts/siconfi_dca_ba.py 2024 cache          # DCA I-E dos 417 municípios
curl -o cache/inep_2024.zip https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2024.zip
#    extrair MICRODADOS_*.CSV e o dicionário como cache/inep_<nome>; ANATEL: usar scripts/httpzip.py
#    para extrair Densidade_Banda_Larga_Fixa.csv e Acessos_Banda_Larga_Fixa_2026_Colunas.csv
# 2. amostras + categorias + status
python scripts/gerar_amostras.py cache
# 3. ANEEL (de outra rede)
python scripts/aneel_probe.py
```

Observações de ambiente: o certificado do `download.inep.gov.br` falha no Python (cadeia incompleta no certifi), por isso o download é feito com curl. Os IDs dos recursos BNDES podem mudar quando o portal é atualizado; nesse caso, consulte `package_show?id=operacoes-financiamento`.

---

## 9. Pendências

1. **ANEEL:** rodar `aneel_probe.py` fora desta rede e validar os 5 indicadores.
2. **Lista SECTI de 642 cursos CT&I:** colocar na pasta para substituir ou complementar o filtro CINE.
3. **BNDES `SEM MUNICÍPIO`:** definir uma regra de rateio ou deixar fora do painel municipal (40% do valor direto na BA).
4. **PIB per capita 2023:** baixar o XLSX oficial do PIB dos Municípios 2023 (a SIDRA não tem população municipal de 2023).
5. **ANATEL 2023–2025:** recalcular a densidade a partir dos arquivos de acessos.
6. **Territórios de Identidade:** a tabela município → território (27 TIs) não estava na pasta, então as agregações territoriais não foram feitas. Todas as amostras têm código IBGE para a junção.

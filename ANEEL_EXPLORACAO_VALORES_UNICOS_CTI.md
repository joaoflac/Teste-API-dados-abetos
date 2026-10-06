# ANEEL — Exploração de Valores Únicos para CT&I

## 1. Objetivo

Apresentar a exploração empírica dos **valores únicos, categorias, classificações e distribuições estatísticas** dos datasets da ANEEL já homologados no projeto, avaliando suas aplicações analíticas para a camada de **Ciência, Tecnologia e Inovação (CT&I)** do projeto **TERRITÓRIOS SECTI** no Estado da Bahia.

O foco deste documento não é listar registros exaustivos nem antecipar o cálculo de indicadores sintéticos finais, mas sim fornecer uma **radiografia estruturada do conteúdo das APIs e Datastores da ANEEL**, mapeando:
- Quais dimensões e atributos categóricos existem em cada dataset;
- Quais são os valores únicos reais observados na Bahia;
- Quais grandezas numéricas e ordens de grandeza são reportadas;
- Quais possibilidades analíticas concretas esses dados abrem para a formulação e o monitoramento de políticas de CT&I.

---

## 2. Resumo

A exploração detalhada dos dados da ANEEL para a Bahia revelou um conjunto diversificado de dimensões técnicas, regulatórias e financeiras:

1. **Geração e Capacidade Renovável (SIGA):** O parque gerador da Bahia possui **6 tipologias de geração** (`SigTipoGeracao`) e **13 fontes energéticas primárias** (`NomFonteCombustivel`). O estado destaca-se com **88,2% dos empreendimentos outorgados voltados às fontes eólica (520) e solar fotovoltaica (506)**, cobrindo 123 municípios e totalizando mais de 14.889 MW fiscalizados em operação limpa.
2. **Consumo e Mercado (SAMP):** Segmentado em **8 classes de consumo** e **mais de 20 tipos de detalhe de mercado** (energia em kWh, demanda em kW, tributos e encargos). Trata-se de uma base com granularidade no nível de concessionária (COELBA / estadual), apta a caracterizar intensidade energética e demanda setorial industrial.
3. **Infraestrutura Comercial Territorial (INDGER):** Oferece granularidade municipal estrita (**417 municípios baianos**) via código IBGE de 7 dígitos, monitorando a evolução mensal da quantidade de unidades consumidoras ativas (`QtdUCAtiva`), com mediana de 7.758 UCs por município.
4. **Investimentos em P&D Regulado (P&D ANEEL):** Núcleo de **CT&I Direta** contendo **99 projetos da concessionária estadual (COELBA)**, com amplitude temporal de 2009 a 2026. A base discrimina **5 níveis de maturidade de inovação** (TRL), **10 linhas temáticas tecnológicas**, **6 tipos de produtos gerados** e dispêndios financeiros médios de R$ 3,94 milhões previstos por projeto.
5. **Confiabilidade da Rede (DEC/FEC & INDQUAL):** Apura a qualidade contínua em **954 conjuntos elétricos** na Bahia, subdivididos em mais de 20 métricas regulatórias de continuidade (DEC, FEC, expurgos e causas de interrupção), conectando-se a **todos os 417 municípios baianos** por meio da tabela oficial de relacionamento territorial $N:N$.

---

## 3. SIGA — Geração

### Tipos de geração
O campo `SigTipoGeracao` classifica a tecnologia e o porte do empreendimento de geração. No Estado da Bahia, foram identificados **6 valores únicos** (totalizando 1.163 usinas outorgadas):

- **EOL (Central Geradora Eólica):** 520 empreendimentos (44,7% do parque baiano);
- **UFV (Central Geradora Solar Fotovoltaica):** 506 empreendimentos (43,5% do parque baiano);
- **UTE (Usina Termelétrica):** 107 empreendimentos (9,2% do parque baiano);
- **CGH (Central Geradora Hidrelétrica):** 13 empreendimentos (1,1% do parque baiano);
- **UHE (Usina Hidrelétrica):** 10 empreendimentos (0,9% do parque baiano);
- **PCH (Pequena Central Hidrelétrica):** 7 empreendimentos (0,6% do parque baiano).

### Fontes energéticas
O campo `NomFonteCombustivel` especifica a matriz primária utilizada. Na Bahia, foram encontradas **13 fontes energéticas distintas**:

- **Cinética do vento:** 520 usinas;
- **Radiação solar:** 506 usinas;
- **Óleo Diesel:** 82 usinas;
- **Potencial hidráulico:** 30 usinas;
- **Gás Natural:** 12 usinas;
- **Licor Negro (biomassa de celulose):** 3 usinas;
- **Bagaço de Cana de Açúcar:** 3 usinas;
- **Óleo Combustível:** 2 usinas;
- **Gás de Refinaria:** 1 usina;
- **Biogás - RU (Resíduos Urbanos):** 1 usina;
- **Calor de Processo - OF:** 1 usina;
- **Resíduos Florestais:** 1 usina;
- **Lenha:** 1 usina.

### Fases
O campo `DscFaseUsina` registra o ciclo de implantação da usina, apresentando **3 valores únicos**:

- **Operação:** 677 usinas (58,2% do total — empreendimentos ativos que injetam energia na rede);
- **Construção não iniciada:** 474 usinas (40,8% do total — projetos com outorga regulatória já concedida, em fase pré-operacional);
- **Construção:** 12 usinas (1,0% do total — obras civis e montagem física em andamento).

### Municípios
- **Quantidade de municípios com empreendimentos:** **123 municípios únicos** na Bahia.
- **Formato:** String textual livre contendo `"Nome - UF"` (ex.: `"Camaçari - BA"`, `"Juazeiro - BA"`).
- **Exemplos reais de municípios com usinas:**
  - `Camaçari - BA` (predomínio de termelétricas industriais e biomassa);
  - `Mucuri - BA` (geração hidrelétrica e biomassa florestal);
  - `Formosa do Rio Preto - BA` (geração térmica e solar);
  - `São Desidério - BA` (potencial solar e térmico);
  - `Itapebi - BA` (grande usina hidrelétrica).

### Variáveis numéricas
Distribuição das variáveis contínuas de potência para os 1.163 registros da Bahia:

| Variável | Registros Válidos | Mínimo | Máximo | Média | Mediana |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Potência Fiscalizada (`MdaPotenciaFiscalizadaKw`)** | 1.163 | 0,00 kW | 2.462.400,00 kW | 18.943,45 kW | 475,00 kW |
| **Potência Outorgada (`MdaPotenciaOutorgadaKw`)** | 1.163 | 0,16 kW | 2.462.400,00 kW | 37.059,44 kW | 30.240,00 kW |

*Nota:* O valor máximo corresponde ao complexo da UHE Paulo Afonso IV (2.462,40 MW). A diferença entre média e mediana na potência fiscalizada decorre das 474 usinas em fase de "Construção não iniciada", cujo valor de potência fiscalizada em operação é 0 kW.

### Possibilidades de CT&I
- **Mapeamento de Polos Energéticos:** Identificar municípios que concentram geração de grande porte, capazes de atrair plantas industriais eletrointensivas e centros de supercomputação;
- **Clusters de Transição Tecnológica:** Avaliar a substituição gradual de usinas a óleo diesel por microrredes limpas no interior baiano;
- **Cruzamento Territorial com ICTs:** Avaliar se regiões com alta expansão outorgada (capacidade futura) contam com presença de cursos técnicos e superiores em engenharia elétrica e energias renováveis.

---

## 4. SIGA — Solar e Eólica

### Categorias
O recorte exclusivo das fontes intermitentes de transição energética compreende as siglas:
- **`EOL` (Central Geradora Eólica):** Fonte `Cinética do vento`;
- **`UFV` (Central Geradora Solar Fotovoltaica):** Fonte `Radiação solar`.

Juntas, totalizam **1.026 empreendimentos outorgados**, distribuídos nas seguintes fases:
- **Operação:** 561 usinas (382 EOL e 179 UFV);
- **Construção não iniciada:** 454 usinas (135 EOL e 319 UFV);
- **Construção:** 11 usinas (3 EOL e 8 UFV).

### Municípios
- **Quantidade de municípios com parques solares ou eólicos:** **74 municípios** na Bahia.
- **Polos Eólicos consolidados (exemplos):** Sento Sé, Caetité, Morro do Chapéu, Campo Formoso, Pindaí, Gentio do Ouro, Ourolândia, Igaporã.
- **Polos Solares consolidados (exemplos):** Juazeiro, Tabocas do Brejo Velho, Bom Jesus da Lapa, Oliveira dos Brejinhos, Barreiras, Casa Nova.

### Potência
Estatísticas comparativas entre Eólica e Solar Fotovoltaica na Bahia:

| Tipologia | Métrica de Potência | Registros Válidos | Mínimo | Máximo | Média | Mediana | Total Fiscalizado Ativo |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Eólica (`EOL`)** | Fiscalizada (kW) | 520 | 0,00 kW | 79.800,00 kW | 22.754,04 kW | 27.000,00 kW | **11.832,10 MW** |
| | Outorgada (kW) | 520 | 0,16 kW | 79.800,00 kW | 33.516,66 kW | 31.000,00 kW | — |
| **Solar (`UFV`)** | Fiscalizada (kW) | 506 | 0,00 kW | 95.245,00 kW | 6.041,63 kW | 0,00 kW | **3.057,06 MW** |
| | Outorgada (kW) | 506 | 20,00 kW | 360.000,00 kW | 36.513,85 kW | 33.685,00 kW | — |

*Nota:* O valor fiscalizado máximo em usina solar individual atinge 95,25 MW (complexos solares do semiárido). A capacidade total outorgada solar alcança 18.476 MW, evidenciando uma carteira futura de implantação superior a 15.000 MW adicionais.

### Possibilidades de CT&I
- **Hubs de Hidrogênio Verde (H2V):** Cruzar as coordenadas geográficas dos clusters eólicos e solares do Vale do São Francisco e Alto Sertão com rotas logísticas e portuárias (ex.: Camaçari e Aratu), identificando territórios prioritários para plantas piloto de hidrogênio e amônia verde;
- **Armazenamento de Energia (BESS):** Mapear nós de saturação da rede de transmissão com excesso de geração solar/eólica intermitente, orientando projetos de P&D em baterias de grande escala e eletrônica de potência;
- **Especialização Territorial:** Criar índices de vocação energética territorial (ex.: "Território de Identidade com Perfil Eólico" vs. "Perfil Fotovoltaico").

---

## 5. SAMP

### Classes
O campo `DscClasseConsumoMercado` identifica os setores econômicos atendidos na área da concessionária estadual (COELBA). Foram validados **8 valores únicos**:

- **Industrial:** Grandes e médios estabelecimentos manufatureiros e de transformação;
- **Comercial:** Comércio atacadista, varejista e setor de serviços;
- **Residencial:** Domicílios urbanos e rurais comuns;
- **Rural:** Agropecuária, irrigação e cooperativas rurais;
- **Poder Público:** Instalações da administração direta e indireta federal, estadual e municipal;
- **Serviço Público:** Serviços essenciais (saneamento, tração elétrica, iluminação pública);
- **Consumo Próprio:** Energia consumida pela própria concessionária em suas instalações;
- **Não se aplica:** Encargos, suprimentos interdistribuidoras e faturamentos regulatórios especiais.

### Tipos de medida
O campo `DscDetalheMercado` categoriza o tipo de fluxo físico e financeiro mensurado. Foram identificados **mais de 20 tipos de medida**, dos quais destacam-se:

- **Energia Consumida (kWh):** Consumo físico total faturado aos consumidores livres e cativos;
- **Energia TE (kWh):** Consumo faturado com Tarifa de Energia (componente de geração);
- **Energia TUSD (kWh):** Consumo associado à Tarifa de Uso do Sistema de Distribuição (componente de fio);
- **Demanda Faturada (kW):** Potência de ponta contratada/utilizada por estabelecimentos de alta e média tensão (Grupo A);
- **Demanda Contratada kW:** Demanda contratual de longo prazo estipulada em contrato de fornecimento;
- **Energia Injetada (kWh):** Energia proveniente de micro e minigeração distribuída injetada na rede da distribuidora;
- **Energia Compensada (kWh):** Energia creditada aos consumidores do sistema de compensação (SCEE);
- **Número de Consumidores:** Contagem de contas contratuais ativas;
- **Métricas financeiras:** `Receita Energia (R$)`, `Receita Demanda (R$)`, `ICMS (R$)`, `PIS/PASEP (R$)`, `COFINS (R$)`.

### Períodos
- **Periodicidade:** Mensal (`DatCompetencia`, ex.: `2024-01-01` a `2024-12-01`);
- **Disponibilidade na base:** Séries históricas anuais consolidadas desde 2003 até 2026.

### Possibilidades de CT&I
- **Demanda Energética Produtiva Estadual:** Monitorar a evolução do consumo da classe Industrial e da Demanda Faturada como indicador antecedente de atividade econômica de base tecnológica;
- **Avanço da Transição Distribuída:** Avaliar a curva de crescimento da Energia Injetada e Compensada no estado, mensurando a taxa de adoção de microgeração pelos setores comercial e industrial.

---

## 6. INDGER

### Categorias
O recurso `indger-dados-comerciais.csv` traz dados de gestão comercial regulatória das distribuidoras.
- **Agentes da Bahia (`SigAgente`):** `Neoenergia Coelba` (concessionária responsável por 99,8% da carga distribuída do estado).

### Municípios
- **Granularidade:** Campo `CodMunicipioIBGE` (código oficial de 7 dígitos do IBGE);
- **Cobertura Territorial:** **417 municípios da Bahia** (cobertura total de todos os municípios do estado).

### Variáveis
Estatísticas descritivas para a quantidade de Unidades Consumidoras ativas nos municípios baianos:

| Variável | Registros Válidos (Amostra Histórica) | Mínimo | Máximo | Média | Mediana |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`QtdUCAtiva` (Unidades Consumidoras Ativas)** | 1.000 | 0 UCs | 1.144.792 UCs | 17.970,63 UCs | 7.758,50 UCs |
| **`QtdUCAtivaFat` (UCs Ativas Faturadas)** | 1.000 | 0 UCs | 1.130.400 UCs | 17.650,20 UCs | 7.620,00 UCs |

*Nota:* O valor máximo de 1,14 milhão de UCs corresponde ao município de Salvador. Municípios com 0 ou poucas UCs ocorrem pontualmente em enclaves de fronteira interestadual atendidos por distribuidoras limítrofes.

### Possibilidades de CT&I
- **Tamanho do Mercado Territorial:** Cruzar o número de UCs municipais com os dados de população e PIB do IBGE para mensurar a taxa de eletrificação e a densidade de consumidores;
- **Escala de Demanda para Inovação Urbana:** Identificar centros urbanos regionais secundários (com mais de 50.000 UCs) com escala populacional e comercial compatível com a implantação de living labs de Cidades Inteligentes (*Smart Cities*).

---

## 7. P&D ANEEL

Este é o dataset central classificado como **CT&I Direta**, compreendendo 99 projetos da concessionária de energia do Estado da Bahia (COELBA).

### Situação
O campo `IdcSituacaoProjeto` apresenta **4 valores únicos**:

- **CONCLUÍDO:** 40 projetos (pesquisas encerradas com relatório final entregue);
- **CANCELADO:** 28 projetos (projetos interrompidos ou descontinuados regulatoriamente);
- **EM ATRASO:** 25 projetos (pesquisas em andamento que ultrapassaram o cronograma inicial);
- **EM EXECUÇÃO:** 6 projetos (pesquisas ativas com desembolsos e desenvolvimento vigentes).

### Fase da inovação
O campo `SigFasInovacaoProjeto` classifica o grau de maturidade tecnológica ao longo da cadeia de inovação (equivalente aos níveis TRL — *Technology Readiness Levels*). Foram identificados **5 valores únicos**:

- **DE (Desenvolvimento Experimental):** 47 projetos (maior parte do portfólio — prototipagem, testes de bancada e escala piloto);
- **PA (Pesquisa Aplicada):** 24 projetos (aquisição de novos conhecimentos voltados a aplicações práticas operacionais);
- **CS (Cabeça de Série):** 19 projetos (primeira unidade em escala industrial para validação de produto/processo);
- **LP (Lote Pioneiro):** 5 projetos (fabricação de lote inicial para inserção experimental em campo);
- **IM (Inserção no Mercado):** 4 projetos (estratégias de difusão comercial da tecnologia desenvolvida).

### Temas
O campo `SigTemaProjeto` classifica a temática científico-tecnológica da pesquisa. Foram encontrados **10 temas únicos**:

- **OU (Outros):** 30 projetos (temáticas transversais, regulatórias e multidisciplinares);
- **MF (Medição, Faturamento e Combate às Perdas Comerciais):** 16 projetos;
- **QC (Qualidade e Confiabilidade dos Serviços de Energia Elétrica):** 15 projetos;
- **SE (Segurança no Setor Elétrico):** 9 projetos;
- **SC (Supervisão, Controle e Proteção de Sistemas):** 9 projetos;
- **OP (Operação de Sistemas de Energia Elétrica):** 8 projetos;
- **PL (Planejamento de Sistemas de Energia Elétrica):** 6 projetos;
- **FA (Fontes Alternativas de Geração):** 3 projetos;
- **MA (Meio Ambiente):** 2 projetos;
- **EE (Eficiência Energética):** 1 projeto.

### Tipos de produto
O campo `SigTipoProdutoProjeto` categoriza o entregável físico ou intelectual resultante do projeto. Foram validados **6 tipos únicos**:

- **ME (Metodologia):** 32 projetos (novos procedimentos de cálculo, manuais ou modelos analíticos);
- **SM (Sistema / Módulo):** 22 projetos (sistemas integrados de hardware e software);
- **CM (Componente / Material):** 18 projetos (novas ligas, polímeros, isoladores ou dispositivos elétricos);
- **CD (Conceito / Modelo):** 15 projetos (provas de conceito teóricas ou modelos conceituais);
- **SW (Software):** 10 projetos (softwares dedicados, algoritmos e aplicativos operacionais);
- **MS (Medição / Sensor):** 2 projetos (equipamentos de telemedição e sensores de rede).

### Agentes
- **Agentes da Bahia:** `COMPANHIA DE ELETRICIDADE DO ESTADO DA BAHIA COELBA` (CNPJ `15.139.629/0001-94` / Sigla `COELBA`).

### Anos
- **Horizonte Temporal:** 15 anos distintos identificados no campo `AnoCadastroPropostaProjeto`:
  - Anos históricos: 2009, 2010, 2011, 2012, 2014;
  - Anos recentes consolidados: 2017, 2018, 2019, 2020, 2021, 2022, 2023;
  - Ciclos contemporâneos vigentes: 2024, 2025, 2026;
  - Amplitude temporal: **2009 a 2026**.

### Valores financeiros
Estatísticas financeiras dos investimentos em P&D regulado na Bahia (em Reais — R$):

| Métrica Financeira | Projetos Válidos | Mínimo | Máximo | Média | Mediana | Total Investido |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Custo Previsto (`VlrCustoTotalPrevisto`)** | 99 | R$ 421.900,00 | R$ 24.209.878,72 | R$ 3.940.396,47 | R$ 1.574.579,00 | **R$ 390.099.250,53** |
| **Custo Auditado (`VlrCustoTotalAuditado`)** | 47 | R$ 408.887,16 | R$ 20.144.380,55 | R$ 4.226.871,03 | R$ 1.821.249,18 | **R$ 198.662.938,41** |

*Nota:* O custo auditado refere-se aos projetos concluídos que já passaram pelo processo final de auditoria técnica e contábil da ANEEL.

### Possibilidades de CT&I
- **Mapeamento da Trajetória Tecnológica:** Construir séries temporais do volume de recursos regulados alocados por tema (ex.: crescimento de projetos em automação e digitalização de redes nos últimos 5 anos);
- **Perfil de Maturidade da Inovação:** Monitorar a proporção de projetos em estágios avançados (`CS`, `LP`, `IM`) em relação a pesquisas básicas/experimentais (`PA`, `DE`), aferindo a capacidade do ecossistema de levar inovações à aplicação real;
- **Tipologia de Ativos Criados:** Avaliar a proporção de geração de ativos intangíveis (softwares e metodologias) frente a componentes físicos e materiais industriais na Bahia.

---

## 8. DEC / FEC

### Indicadores
O campo `SigIndicador` traz as siglas dos indicadores de continuidade apurados. Foram validados os **2 indicadores centrais** e **mais de 15 desdobramentos técnicos de causa**:

- **Indicadores Básicos:**
  - **`DEC`:** Duração Equivalente de Interrupção por Unidade Consumidora (em horas no período);
  - **`FEC`:** Frequência Equivalente de Interrupção por Unidade Consumidora (número de interrupções no período);
- **Desdobramentos e Tipos de Interrupção:**
  - `DECIP` / `FECIP`: Interrupções em Dia Crítico Programadas;
  - `DECIND` / `FECIND`: Interrupções Não Programadas em Dia Crítico;
  - `DECINE` / `FECINE`: Interrupções Não Programadas em Situação de Emergência;
  - `DECINO` / `FECINO`: Interrupções Não Programadas em Situação Normal Operacional;
  - `DECIPC` / `FECIPC`: Interrupções Programadas a Pedido do Consumidor;
  - `DECXN` / `FECXN`: Interrupções por Origem Externa ao Sistema da Distribuidora;
  - `NumCon`: Número total de consumidores no conjunto elétrico.

### Anos
- Anos da série decenal ativa: 2020 a 2029 (com apurações consolidadas até 2026).

### Períodos
- Campo `NumPeriodoIndice`: meses de **1 a 12** (apuração mensal contínua).

### Agentes
- Concessionária responsável na Bahia: `COELBA` (`COMPANHIA DE ELETRICIDADE DO ESTADO DA BAHIA COELBA`).

### Conjuntos elétricos
- **Quantidade de Conjuntos na Bahia:** **954 conjuntos elétricos únicos** monitorados.
- **Exemplos de Conjuntos:** `SUBAE`, `MACAUBAS`, `ITABUNA`, `TABULEIRO`, `BARREIRAS`, `PAULO AFONSO`, `PITUBA`, `VITORIA DA CONQUISTA`.

### Possibilidades de CT&I
- **Índice de Confiabilidade de Infraestrutura:** Criar um ranking de estabilidade da rede elétrica por conjunto elétrico e território de identidade;
- **Seleção de Áreas para Equipamentos Críticos:** Apoiar a tomada de decisão locacional para instalação de laboratórios de microscopia eletrônica, salas limpas, data centers e parques tecnológicos que exigem altos índices de continuidade elétrica (baixo DEC/FEC);
- **Monitoramento de Vulnerabilidade de Redes Tecnológicas:** Identificar territórios onde picos de DEC/FEC podem comprometer conectividade escolar, telemedicina e hubs digitais municipais.

---

## 9. Matriz de possibilidades de CT&I

A tabela abaixo sintetiza como cada dimensão identificada nos datasets da ANEEL pode ser operacionalizada em análises de CT&I para o projeto TERRITÓRIOS SECTI:

| Dataset | Dimensão Explorada | O que existe comprovadamente | Possível análise de CT&I no TERRITÓRIOS SECTI |
| :--- | :--- | :--- | :--- |
| **SIGA** | Tipos de geração (`SigTipoGeracao`) | 6 tipos: EOL, UFV, UTE, CGH, UHE, PCH | Caracterização da matriz energética territorial e diversificação |
| **SIGA** | Fontes energéticas (`NomFonteCombustivel`) | 13 fontes (eólica, solar, diesel, biomassa, etc.) | Mapeamento de fontes renováveis vs fósseis nos territórios |
| **SIGA** | Fases operacionais (`DscFaseUsina`) | Operação (677), Não iniciada (474), Construção (12) | Distinção entre capacidade instalada presente e pipeline futuro |
| **SIGA** | Potência e Localização | Coordenadas lat/long e 123 municípios baianos | Georreferenciamento de polos de energia e atração industrial |
| **SIGA Solar/Eólica** | Potência segregada | 11.832 MW eólicos e 3.057 MW solares ativos | Vocação territorial para projetos de Hidrogênio Verde e armazenamento |
| **SAMP** | Classes de consumo | 8 classes (Industrial, Comercial, Residencial, etc.) | Análise de perfil produtivo e intensidade eletrointensiva estadual |
| **SAMP** | Detalhes de mercado | Energia (kWh), Demanda (kW), Energia Injetada | Taxa de adoção de microgeração e perfil de consumo no estado |
| **INDGER** | Unidades Consumidoras (`QtdUCAtiva`) | 417 municípios com código IBGE de 7 dígitos | Porte da infraestrutura de rede e densidade urbana municipal |
| **P&D ANEEL** | Situação do projeto | 40 concluídos, 25 em atraso, 28 cancelados, 6 ativos | Taxa de sucesso e execução de projetos de pesquisa regulados |
| **P&D ANEEL** | Maturidade tecnológica | 5 fases de inovação (DE, PA, CS, LP, IM) | Nível de maturidade tecnológica (TRL) da pesquisa no setor elétrico |
| **P&D ANEEL** | Linhas temáticas | 10 temas (Medição, Qualidade, Operação, Redes, etc.) | Especialização temático-tecnológica das pesquisas na Bahia |
| **P&D ANEEL** | Entregáveis tecnológicos | 6 tipos de produto (Metodologias, Sistemas, Software) | Proporção de geração de tecnologias digitais vs físicas |
| **P&D ANEEL** | Dispêndio financeiro | R$ 390M previstos / R$ 198M auditados (99 projetos) | Métrica oficial de dispêndio financeiro em CT&I no setor de energia |
| **P&D ANEEL** | Horizonte temporal | Propostas de 2009 a 2026 | Evolução histórica do investimento regulado em pesquisa |
| **DEC / FEC** | Índices de continuidade | DEC (horas) e FEC (vezes) por conjunto elétrico | Confiabilidade da infraestrutura para suporte a polos tecnológicos |
| **INDQUAL** | Vínculo Conjunto $\leftrightarrow$ Município | 2.485 relações cobrindo os 417 municípios baianos | Georreferenciamento de estabilidade energética para living labs e labs |

---

## 10. Limitações

A exploração identificou as seguintes fronteiras e limitações nos dados:

1. **Ausência de Instituições Executoras no P&D Público:** O dataset da ANEEL lista a empresa concessionária proponente (COELBA), mas omite os dados cadastrais das universidades, institutos de pesquisa e ICTs executoras (ex.: UFBA, SENAI CIMATEC, UESC). Essa identificação requer cruzamento com relatórios de encerramento do programa;
2. **Inexistência de Município no P&D e no SAMP:** Tanto os projetos de P&D quanto os volumes de consumo do SAMP são registrados no nível corporativo/estadual da distribuidora. Não é possível, a partir dessas bases, alocar diretamente valores de investimento em P&D ou consumo em kWh a municípios específicos;
3. **Município como String Livre no SIGA:** No SIGA, o município consta no campo textual `DscMuninicpios` (ex.: `"Camaçari - BA"`), o que demanda padronização ortográfica prévia para merge com tabelas IBGE;
4. **Associação Muitos-para-Muitos no DEC/FEC:** Como um conjunto elétrico atende múltiplos municípios contíguos e grandes cidades possuem vários conjuntos, não existe correspondência 1:1. Médias simples sem ponderação populacional distorcem a realidade de qualidade municipal;
5. **Geração Distribuída (Micro/Mini) em Base Separada:** O SIGA contempla a geração centralizada (usinas outorgadas). Telhados solares residenciais e comerciais (MMGD) encontram-se no dataset de Micro e Minigeração Distribuída, que possui estrutura de dados e arquivos próprios.

---

## 11. Conclusão

A exploração das variáveis e valores únicos da ANEEL demonstra que a agência reguladora disponibiliza um ecossistema rico e estruturado de dados que apoia o projeto **TERRITÓRIOS SECTI** em duas frentes fundamentais:

1. **Camada de CT&I Direta (P&D ANEEL):** Permite construir métricas autênticas de dispêndio financeiro (R$ 390 milhões contratados), maturidade de inovação tecnológica (47 projetos em desenvolvimento experimental e 28 em fases de produto/mercado) e orientação temática prioritária, acompanhando a evolução dos investimentos em pesquisa na Bahia ao longo de quase duas décadas.
2. **Camada de CT&I de Contexto e Infraestrutura Habilitadora (SIGA, INDGER, SAMP e DEC/FEC):** Fornece dados territoriais robustos sobre a matriz limpa (11,8 GW eólicos e 3,0 GW solares em operação), a escala dos mercados municipais (417 municípios monitorados no INDGER) e a estabilidade da infraestrutura elétrica (954 conjuntos monitorados em DEC/FEC).

Essas variáveis oferecem sustentação analítica para avaliar a vocação regional dos territórios baianos para transição energética, clusters de hidrogênio verde, atração de indústrias de alta tecnologia e fixação de ecossistemas inovadores.

# Exploração de Valores Únicos para CT&I — INEP, BNDES, SICONFI, ANATEL e IBGE

## 1. Objetivo

Apresentar a exploração técnica dos **valores únicos, classificações categóricas, distribuições estatísticas e possibilidades analíticas de CT&I** para os datasets das demais fontes homologadas no projeto **TERRITÓRIOS SECTI**:
1. **INEP** (Censo da Educação Superior);
2. **BNDES** (Operações de Financiamento e Crédito);
3. **SICONFI** (Execução Orçamentária e Despesas em Ciência e Tecnologia);
4. **ANATEL** (Conectividade e Infraestrutura de Telecomunicações);
5. **IBGE** (Bases Demográfica, Econômica e Cartográfica).

Seguindo a mesma abordagem empírica desenvolvida para a ANEEL, este inventário mapeia o que existe comprovadamente em cada fonte no recorte do **Estado da Bahia (417 municípios)**, documentando categorias oficiais, grandezas numéricas e o potencial de integração no painel da SECTI-BA.

---

## 2. Resumo executivo

A exploração das fontes revela o perfil estrutural do ecossistema de Ciência, Tecnologia e Inovação na Bahia:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               SÍNTESE DOS DADOS VALIDADOS POR FONTE NA BAHIA                           │
├────────────┬───────────────────────────────────────────────────────────────────────────┤
│ INEP       │ • 145 IES sediadas (10.022 docentes doutores em exercício).               │
│            │ • 1.851 cursos presenciais; 399 no núcleo STEM (Ciências, TIC, Engenharia)│
│            │ • 67.325 matrículas presenciais no núcleo tecnológico (STEM).             │
├────────────┼───────────────────────────────────────────────────────────────────────────┤
│ BNDES      │ • 80.964 operações contratadas (R$ 81,55 bilhões desembolsados).          │
│            │ • 314 operações com regra explícita de CT&I (R$ 851,18 milhões).          │
│            │ • 259 operações com flag oficial 'inovacao = SIM' (R$ 684,28 milhões).    │
├────────────┼───────────────────────────────────────────────────────────────────────────┤
│ SICONFI    │ • 415 municípios baianos com DCA 2024 declarada.                          │
│            │ • Apenas 8 municípios liquidaram despesa na Função 19 (C&T), somando      │
│            │   R$ 126,49 milhões (Salvador concentra 87,4% deste montante).            │
│            │ • 39 municípios liquidaram R$ 99,10 milhões na Subfunção 126 (TI).        │
├────────────┼───────────────────────────────────────────────────────────────────────────┤
│ ANATEL     │ • 2.342.936 acessos de banda larga fixa ativos (ago/2026).                │
│            │ • 88,8% dos acessos via Fibra Óptica (FTTH) e 92,9% com velocidade >34Mbps│
│            │ • Provedores regionais (pequeno porte/ISPs) detêm 72,8% do mercado baiano.│
├────────────┼───────────────────────────────────────────────────────────────────────────┤
│ IBGE       │ • 417 municípios com cobertura demográfica, PIB/VAB e malha geográfica.   │
│            │ • População 2026: 14.889.472 hab. | PIB 2023: R$ 430,99 bilhões.          │
│            │ • VAB Industrial de R$ 87,4 bi e VAB Agropecuário de R$ 38,5 bi.          │
└────────────┴───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. INEP — Educação Superior e Capital Humano em CT&I

O Censo da Educação Superior (INEP 2024) é a fonte oficial para aferir a formação de capital humano qualificado, densidade de pesquisadores e vocação acadêmico-tecnológica dos territórios baianos.

### 3.1 Dimensões e categorias institucionais
A análise dos microdados da Bahia identifica as seguintes classificações categóricas:

- **Organização Acadêmica (`TP_ORGANIZACAO_ACADEMICA`):**
  - `1 - Universidade`: 11 instituições na BA (concentram a maior parte dos doutores e da pesquisa científica);
  - `2 - Centro Universitário`: 25 instituições;
  - `3 - Faculdade`: 107 instituições (ensino prioritariamente profissional/graduação);
  - `4 - Instituto Federal de Educação, Ciência e Tecnologia (IF)`: 2 instituições multicampi (IFBA e IF Baiano), com forte capilaridade regional e vocação tecnológica.
- **Categoria Administrativa (`TP_CATEGORIA_ADMINISTRATIVA`):**
  - `1 - Pública Federal` (UFBA, UFRB, UFSB, UNIVASF, UFOB, IFBA, IF Baiano);
  - `2 - Pública Estadual` (UNEB, UESC, UESB, UEFS — ampla interiorização universitária);
  - `4 - Privada com fins lucrativos` (maior volume de cursos e polos EAD);
  - `5 - Privada sem fins lucrativos` (comunitárias e confessionais).
- **Grau Acadêmico (`TP_GRAU_ACADEMICO`):**
  - `1 - Bacharelado`: 13.685 ofertas presenciais e EAD;
  - `2 - Licenciatura`: 8.222 ofertas;
  - `3 - Tecnológico`: 18.707 ofertas (crucial para formação técnica rápida e alinhada ao setor produtivo).
- **Modalidade de Ensino (`TP_MODALIDADE_ENSINO`):**
  - `1 - Presencial`: 1.851 cursos na Bahia (vinculados estritamente ao município do campus);
  - `2 - EAD`: 38.864 linhas de oferta em municípios/polos.

### 3.2 Classificação CINE Áreas (Mapeamento de Cursos CT&I)
O Censo adota a classificação internacional CINE Brasil (Classificação Internacional Normalizada da Educação). O mapeamento das áreas gerais e matrículas na Bahia comprova a estratificação do ensino superior:

| Código CINE | Nome da Área Geral CINE | Nível CT&I | Cursos Presenciais BA | Matrículas Presenciais BA | Participação na Matrícula |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **05** | Ciências naturais, matemática e estatística | **CT&I Núcleo (STEM)** | 99 | 6.024 | 2,4% |
| **06** | Computação e Tecnologias da Informação e Comunicação (TIC) | **CT&I Núcleo (STEM)** | 549 | 25.238 | 9,9% |
| **07** | Engenharia, produção e construção | **CT&I Núcleo (STEM)** | 631 | 36.063 | 14,2% |
| **08** | Agricultura, silvicultura, pesca e veterinária | **CT&I Ampliado** | 105 | 15.196 | 6,0% |
| **09** | Saúde e bem-estar | **CT&I Ampliado** | 856 | 141.190 | 55,6% |
| **01** | Educação (Licenciaturas) | Fora de CT&I | 1.044 | 96.066 | — |
| **04** | Negócios, administração e direito | Fora de CT&I | 1.479 | 124.609 | — |
| **03** | Ciências sociais, comunicação e informação | Fora de CT&I | 283 | 28.801 | — |

*Nota:* O **Núcleo STEM** (Áreas 05, 06 e 07) soma **399 cursos presenciais em 38 municípios baianos**, congregando **67.325 estudantes** em formação tecnológica e científica avançada.

### 3.3 Cobertura territorial
- **Sedes de IES:** 145 instituições sediadas em **45 municípios** baianos.
- **Oferta de Graduação Presencial:** Cursos presenciais operando ativamente em **56 municípios** polos.
- **Polos de EAD:** Presença capilarizada em **322 municípios** da Bahia.
- **Docentes Doutores:** **10.022 docentes com título de doutor** atuando em IES da Bahia (com forte concentração nas universidades públicas em Salvador, Feira de Santana, Ilhéus/Itabuna e Vitória da Conquista).

### 3.4 Variáveis numéricas e grandezas
Estatísticas da oferta de cursos presenciais na Bahia por município:

| Variável | Mínimo | Máximo | Média Municipal | Mediana | Total no Estado |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Matrículas Presenciais Totais** | 12 | 121.450 (Salvador) | 4.536,4 | 1.280,0 | **254.041** |
| **Matrículas Presenciais STEM (05, 06, 07)** | 5 | 34.810 (Salvador) | 1.771,7 | 412,0 | **67.325** |
| **Docentes com Doutorado por IES** | 0 | 3.412 (UFBA) | 69,1 | 4,0 | **10.022** |

### 3.5 Possibilidades para CT&I
- **Mapeamento de Polos de Formação STEM:** Localizar municípios com massa crítica de formandos em computação e engenharia para apoiar a instalação de incubadoras e centros de desenvolvimento de software;
- **Alinhamento Formação $\leftrightarrow$ Vocação Econômica:** Cruzar municípios com cursos em Ciências Agrárias (`CINE 08`) com o VAB agropecuário (ex.: Barreiras e Luís Eduardo Magalhães) e cursos em Energias com a geração eólica/solar da ANEEL (ex.: Juazeiro e Caetité);
- **Densidade Científica Territorial:** Calcular o indicador de doutores em exercício por mil habitantes nos territórios de identidade da Bahia.

---

## 4. BNDES — Operações de Financiamento e Fomento a CT&I

O banco oficial de desenvolvimento reporta contratos de crédito direto (operações não automáticas) e financiamentos descentralizados via rede bancária credenciada (indiretas automáticas).

### 4.1 Categorias de cliente e apoio financeiro
Nas 80.964 operações contratadas no Estado da Bahia (2002–2026), observam-se as seguintes dimensões:

- **Porte do Cliente (`porte_do_cliente`):**
  - `MICRO`: 45.394 operações (56,1% do total de contratos — microcrédito e pequenos produtores);
  - `PEQUENA`: 27.234 operações (33,6%);
  - `MÉDIA`: 5.932 operações (7,3%);
  - `GRANDE`: 2.404 operações (3,0% das operações, mas concentram a maior fatia dos desembolsos em grandes obras e plantas industriais).
- **Natureza Jurídica (`natureza_do_cliente`):**
  - `PRIVADA`: 79.914 operações;
  - `PÚBLICA`: 1.050 operações (governos municipais, estaduais e concessionárias estatais).
- **Forma de Apoio (`forma_de_apoio`):**
  - `INDIRETA`: 79.860 operações (repasse bancário automático via Desenbahia, BB, Bradesco, BNB, etc.);
  - `DIRETA`: 1.104 operações estruturadas (grandes projetos de infraestrutura, energia e indústria).

### 4.2 Mapeamento de Inovação e Níveis de CT&I
O BNDES possui o campo nativo `inovacao` (`SIM` / `NÃO`). Contudo, a validação técnica comprovou que analisar apenas este campo isolado subestima linhas tecnológicas históricas (como FUNTTEL, FUST e Proengenharia):

```
                     ARQUITETURA DE CRÉDITO CT&I NO BNDES (BAHIA)
                     
  [ Nível CT&I Explícito ] ──► 314 operações (R$ 851,18 milhões desembolsados)
    ├─ Flag Oficial: `inovacao = 'SIM'` (259 operações | R$ 684,28 milhões)
    ├─ Linhas Específicas: BNDES Mais Inovação (245 ops | R$ 130,95M)
    ├─ Programas de Engenharia: Proengenharia / Automotiva (3 ops | R$ 367,71M)
    ├─ Telecomunicações & Redes: BNDES FUNTTEL / FUST (18 ops | R$ 56,86M)
    └─ Indústria 4.0: Máquinas e Equipamentos 4.0 (22 ops | R$ 6,57M)
```

### 4.3 Setores e subsetores CNAE
- **Grandes Setores CNAE (`setor_cnae`):**
  - `COMÉRCIO E SERVIÇOS`: 42.108 operações (R$ 21,3 bilhões);
  - `AGROPECUÁRIA`: 25.864 operações (R$ 13,8 bilhões);
  - `INDÚSTRIA`: 12.992 operações (R$ 46,4 bilhões — concentra os maiores projetos intensivos em capital);
- **Subsetores de Ponta Tecnológica na BA:**
  - Fabricação de produtos químicos e petroquímicos (Polo de Camaçari);
  - Montagem de geradores e turbinas eólicas (Simões Filho e Camaçari);
  - Papel e celulose (Extremo Sul baiano);
  - Telecomunicações e provedores de fibra óptica.

### 4.4 Cobertura territorial
- **Municípios Cobertos:** **416 dos 417 municípios da Bahia** possuem ao menos uma operação de financiamento do BNDES registrada com código IBGE de 7 dígitos (`municipio_codigo`), permitindo agregação direta e cálculo de desembolso per capita.

### 4.5 Variáveis numéricas de desembolso (Bahia)
Estatísticas financeiras dos financiamentos contratados (em Reais — R$):

| Base de Dados | Métrica | Operações Válidas | Mínimo | Máximo | Média | Mediana | Total Desembolsado |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Não Automáticas (Diretas)** | Valor Desembolsado | 1.104 | R$ 0,00 | R$ 2.450.000.000 | R$ 52.043.916 | R$ 13.911.233 | **R$ 57,46 bilhões** |
| **Indiretas Automáticas** | Valor Desembolsado | 79.860 | R$ 0,00 | R$ 54.000.000 | R$ 301.609 | R$ 90.000 | **R$ 24,09 bilhões** |
| **Filtro Estrito CT&I** | Valor Desembolsado | 314 | R$ 1.000 | R$ 151.533.000 | R$ 2.710.764 | R$ 195.000 | **R$ 851,18 milhões** |

### 4.6 Possibilidades para CT&I
- **Intensidade de Financiamento à Inovação Territorial:** Monitorar a proporção de crédito BNDES voltado a inovação e digitalização frente ao crédito tradicional por município;
- **Adoção de Indústria 4.0:** Avaliar municípios receptores de financiamento para modernização de parques fabris (linha *Máquinas 4.0* e *BNDES Mais Inovação*);
- **Financiamento a Infraestrutura Digital:** Cruzar desembolsos dos fundos setoriais de telecomunicações (FUST/FUNTTEL) com a expansão de fibra óptica reportada pela ANATEL.

---

## 5. SICONFI — Despesas Públicas Municipais em Ciência e Tecnologia

O Sistema de Informações Contábeis e Fiscais do Setor Público Brasileiro (SICONFI/Tesouro Nacional) permite acompanhar o dispêndio orçamentário liquidado pelas prefeituras baianas na área de C&T.

### 5.1 Classificação orçamentária (Funções e subfunções)
A classificação funcional programática padrão identifica as seguintes contas orçamentárias:

- **Função 19 — Ciência e Tecnologia (CT&I Principal):**
  - `19.571 - Desenvolvimento Científico`: Gastos voltados à pesquisa básica e laboratorial;
  - `19.572 - Desenvolvimento Tecnológico e Engenharia`: Gastos com desenvolvimento de novas soluções, protótipos e suporte técnico;
  - `19.573 - Difusão do Conhecimento Científico e Tecnológico`: Parcerias, feiras de ciências, eventos de inovação e popularização da ciência;
  - `19.122 - Administração Geral`: Despesas administrativas de secretarias ou órgãos municipais de ciência e tecnologia.
- **Subfunção 126 — Tecnologia da Informação (Função 04 - Administração):**
  - `04.126 - Tecnologia da Informação`: Gastos com sistemas de gestão, infraestrutura de servidores, segurança da informação e digitalização de serviços públicos municipais (**CT&I Auxiliar / Digitalização**).

### 5.2 Estágios da despesa
O anexo I-E da Declaração de Contas Anuais (DCA) registra três fases da execução da despesa:
1. `Despesas Empenhadas`: Compromisso de gasto formalizado;
2. `Despesas Liquidadas`: Serviço ou produto efetivamente entregue e atestado (**fase mais adequada para análise de política pública consolidada**);
3. `Despesas Pagas`: Pagamento financeiro emitido na conta do fornecedor.

### 5.3 Cobertura territorial e resultados na Bahia (DCA 2024)
- **Municípios que entregaram DCA 2024:** **415 dos 417 municípios** baianos.
- **Municípios com Despesa Liquidada na Função 19 (C&T):** **Apenas 8 municípios** registraram dispêndio nessa rubrica orçamentária:

| Código IBGE | Município Baiano | População 2024 | Despesa Liquidada Função 19 (R$) | C&T por Habitante (R$) | % da Despesa Total |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **2927408** | Salvador | 2.417.678 | R$ 110.647.288,52 | R$ 45,77 | 1,01% |
| **2919553** | Luís Eduardo Magalhães | 107.909 | R$ 5.792.000,00 | R$ 53,67 | 0,52% |
| **2922003** | Mucuri | 41.249 | R$ 8.956.126,82 | R$ 217,12 | 0,47% |
| **2921500** | Monte Santo | 47.798 | R$ 824.000,00 | R$ 17,24 | 0,09% |
| **2914901** | Irecê | 74.507 | R$ 126.850,00 | R$ 1,70 | 0,03% |
| **2919207** | Lauro de Freitas | 203.334 | R$ 92.400,00 | R$ 0,45 | 0,004% |
| **2912509** | Iaçu | 24.607 | R$ 41.250,60 | R$ 1,68 | 0,006% |
| **2919926** | Macururé | 7.420 | R$ 9.600,00 | R$ 1,29 | 0,0005% |
| **TOTAL BA**| **(Soma dos 8 municípios)**| — | **R$ 126.489.515,94** | — | — |

*Nota:* Salvador responde isoladamente por **87,5% de toda a despesa municipal liquidada em C&T** na Bahia. Os outros 407 municípios declarantes reportaram R$ 0,00 liquidado na Função 19.

### 5.4 Abertura em Tecnologia da Informação (Subfunção 126)
Em contraste com a Função 19, a Subfunção `04.126 (Tecnologia da Informação)` possui maior presença territorial:
- **39 municípios** liquidaram gastos em TI em 2024;
- **Total liquidado em TI:** **R$ 99.096.550,81**;
- Principais aplicadores: Salvador (R$ 67,8M), Camaçari (R$ 8,2M), Feira de Santana (R$ 6,5M), Vitória da Conquista (R$ 3,1M) e Luís Eduardo Magalhães (R$ 2,8M).

### 5.5 Possibilidades para CT&I
- **Compromisso Orçamentário Municipal:** Calcular o percentual da receita própria destinado a C&T e a despesa de C&T per capita;
- **Mapeamento de Desertos Institucionais de C&T:** Evidenciar que 98% dos municípios baianos não possuem dotação específica em Ciência e Tecnologia, justificando intervenções estruturantes e convênios da SECTI;
- **Métricas de Governo Digital:** Avaliar gastos na subfunção 126 como indicador de modernização e digitalização da gestão municipal.

---

## 6. ANATEL — Conectividade e Infraestrutura TIC

Os dados abertos da Agência Nacional de Telecomunicações detalham a infraestrutura de banda larga fixa (Serviço de Comunicação Multimídia — SCM), vetor essencial para inclusão digital, economia 4.0 e conectividade de centros de pesquisa.

### 6.1 Tecnologias e meios de acesso
No recorte de agosto de 2026, a Bahia contabilizou **2.342.936 acessos de banda larga fixa**. A distribuição por meio físico e tecnologia comprova o salto tecnológico da conectividade estadual:

- **Meio de Acesso (`Meio de Acesso`):**
  - **Fibra Óptica:** 2.079.476 acessos (**88,8% do mercado baiano** — conectividade de alta qualidade e baixa latência);
  - **Cabo Coaxial:** 107.338 acessos (4,6%);
  - **Rádio (Wireless):** 80.807 acessos (3,4% — ainda relevante em áreas rurais isoladas);
  - **Satélite:** 40.506 acessos (1,7%);
  - **Cabo Metálico (xDSL):** 34.809 acessos (1,5% — tecnologia legada em declínio acelerado).
- **Tecnologia Predominante (`Tecnologia`):**
  - **FTTH (Fiber to the Home):** 1.877.773 acessos (80,1% da base);
  - **ETHERNET:** 201.629 acessos;
  - **HFC:** 99.016 acessos;
  - **FTTB (Fiber to the Building):** 8.455 acessos.

### 6.2 Faixas de velocidade
A classificação por velocidade contratada (`Faixa de Velocidade`) demonstra a dominância da ultravelocidade na Bahia:

- **> 34 Mbps (Banda Larga de Alta Velocidade):** 2.176.069 acessos (**92,9% de todos os acessos**);
- **2 Mbps a 34 Mbps (Velocidade Média):** 149.726 acessos (6,4%);
- **< 2 Mbps (Velocidade Baixa/Básica):** 17.141 acessos (0,7%).

### 6.3 Porte das prestadoras (O papel dos ISPs locais)
Um dado estrutural marcante no mercado baiano é a desconcentração das operadoras:
- **Pequeno Porte (ISPs e Provedores Regionais):** **1.706.469 acessos (72,8% do mercado)**;
- **Grande Porte (Claro, Vivo, Oi, TIM):** **636.467 acessos (27,2% do mercado)**.

*Nota:* Os provedores locais de pequeno porte foram os grandes responsáveis pela interiorização da fibra óptica nos 417 municípios da Bahia.

### 6.4 Cobertura territorial e densidade de banda larga fixa
- **Cobertura:** Todos os **417 municípios da Bahia** possuem acessos registrados no cadastro mensal;
- **Densidade SCM:** Mede a proporção de acessos por 100 domicílios. Em Salvador e polos industriais atinge mais de 75 acessos por 100 domicílios, enquanto municípios rurais do semiárido apresentam densidades inferiores a 20 acessos por 100 domicílios.

### 6.5 Cobertura da Telefonia Móvel (SMP 4G) — Território vs. Moradores (Recurso 1449ea53-fe84-4547-8ac8-f6a465995958)
O dataset oficial de cobertura móvel 4G da Anatel traz métricas territoriais cruciais para o diagnóstico de conectividade da SECTI:
1. **% Moradores Cobertos (Alcance Demográfico):**
   - **Média na Bahia:** **73,90%** (mediana 76,37%);
   - **Mais atendidos:** Lauro de Freitas (100,0%), Madre de Deus (100,0%), Itaparica (100,0%), Salvador (99,99%) e Salinas da Margarida (99,96%);
   - **Menos atendidos:** Jucuruçu (29,66%), Baianópolis (30,04%), Ribeirão do Largo (30,89%), Ibitiara (32,28%) e Itaguaçu da Bahia (34,98%);
2. **% Área Coberta (Alcance Territorial):**
   - **Média na Bahia:** **35,36%** (mediana 28,02%);
   - Municípios urbanizados e de pequena extensão geográfica atingem > 90% (Lauro de Freitas 100%, Muritiba 99,6%, Itaparica 98,9%);
   - Municípios com extensões territoriais gigantescas no Semiárido e Oeste baiano possuem baixa cobertura geográfica (Barra 3,10%, Santa Rita de Cássia 3,74%, Pilão Arcado 3,84%), embora concentrem o sinal na sede urbana;
3. **Implicação para Inclusão Digital e Políticas SECTI:**
   - Evidencia que a cobertura comercial foca nos núcleos urbanos povoados, deixando amplos vazios rurais e eixos produtivos sem sinal 4G, justificando intervenções estaduais em infovias e conectividade rural e escolar.

### 6.6 Possibilidades para CT&I
- **Índice de Conectividade Avançada:** Mensurar o percentual de domicílios com fibra óptica e velocidade acima de 34 Mbps cruzado com a cobertura 4G municipal;
- **Identificação de Desertos Digitais:** Mapear áreas com dependência residual de satélite/rádio e baixa cobertura móvel para subsidiar programas estaduais de infovias (redes ópticas comunitárias e institucionais);
- **Capacidade Habilitadora para Inovação:** Avaliar se a infraestrutura local suporta a implementação de teletrabalho, ensino remoto, sistemas em nuvem e startups de base digital.

---

## 7. IBGE — Demografia, Economia Municipal e Base Cartográfica

As APIs do IBGE fornecem as variáveis fundamentais de contexto socioeconômico, escala demográfica e normalização territorial para todos os cálculos per capita e ponderações do TERRITÓRIOS SECTI.

### 7.1 Agregados SIDRA validados
- **Agregado 6579 (População Residente):** Projeções e estimativas oficiais para todos os 417 municípios da Bahia:
  - 2024: 14.850.513 habitantes;
  - 2025: 14.870.907 habitantes;
  - 2026: 14.889.472 habitantes;
- **Agregado 5938 (PIB dos Municípios a Preços Correntes):** Série anual até 2023 detalhando o Produto Interno Bruto e a composição setorial do Valor Adicionado Bruto (VAB):
  - **PIB Estadual Total (2023):** R$ 430,99 bilhões;
  - `VAB Agropecuária`: R$ 38,51 bilhões;
  - `VAB Indústria`: R$ 87,44 bilhões;
  - `VAB Serviços`: R$ 184,82 bilhões;
  - `VAB Administração, Defesa, Educação e Saúde Públicas`: R$ 84,93 bilhões;
  - `Impostos Líquidos de Subsídios`: R$ 35,29 bilhões.
- **API de Malhas Geográficas:** Polígonos vetoriais GeoJSON para os 417 municípios (`codarea = código IBGE`), áreas territoriais oficiais em km² e coordenadas dos centroides.

### 7.2 Indicadores derivados de contexto
A partir do cruzamento interno do IBGE geram-se três métricas essenciais:
1. **PIB per capita (R$/hab.):** Mensura a riqueza média gerada no território;
2. **Densidade Demográfica (hab./km²):** Nível de adensamento urbano versus dispersão territorial;
3. **PIB por km² (R$/km²):** Intensidade econômica geográfica (densidade de riqueza gerada no espaço físico).

### 7.3 Possibilidades para CT&I
- **Denominadores Oficiais:** Normalizar despesas de CT&I do SICONFI (gasto per capita), matrículas STEM do INEP (matrículas por mil habitantes) e desembolsos do BNDES (crédito per capita);
- **Especialização Produtiva Territorial:** Classificar os territórios pelo peso relativo do VAB Industrial e Agropecuário frente ao PIB para cruzar com investimentos em P&D e cursos tecnológicos;
- **Camada Cartográfica Unificada:** Servir de base geográfica e vetorial para a renderização de mapas temáticos interativos de calor no painel SECTI.

---

## 8. Matriz comparativa de valores únicos e potencial CT&I

| Fonte Oficial | Dimensões e Valores Únicos Relevantes | Granularidade Real | Classificação em CT&I | Potencial no Painel TERRITÓRIOS SECTI |
| :--- | :--- | :--- | :--- | :--- |
| **INEP** | CINE Áreas (05, 06, 07 STEM), IES (11 Universidades, 2 IFs), Grau (Bacharelado, Tecnológico) | Curso presencial $\times$ Município Polo | **CT&I Direta** (Capital Humano) | Formação científica e tecnológica, concentração de pesquisadores e vocação acadêmica |
| **BNDES** | `inovacao = SIM` (259 ops), Linhas CT&I (Mais Inovação, FUNTTEL, Máquinas 4.0), Portes | Contrato $\times$ Código IBGE (416 mun.) | **CT&I Direta** (Crédito) e Contexto | Financiamento à inovação empresarial, modernização industrial e digitalização produtiva |
| **SICONFI** | Função 19 (C&T - 8 municípios na BA), Subfunção 126 (TI - 39 mun.), Estágio (Liquidado) | Prefeitura $\times$ Código IBGE $\times$ Ano | **CT&I Direta** (Gasto Público) | Dispêndio governamental local em C&T, governança científica e digitalização pública |
| **ANATEL** | Meio (88,8% Fibra), Velocidade (>34Mbps 92,9%), Porte (72,8% ISPs regionais) | Município $\times$ Tecnologia $\times$ Mês | **CT&I de Contexto** (Infraestrutura TIC) | Conectividade territorial, capacidade habilitadora para startups e inclusão digital |
| **ANEEL** | Geração renovável (14,8 GW eólica/solar), P&D regulado (99 projetos), DEC/FEC (954 conj.) | Usina, Concessionária, Conjunto Elétrico | **CT&I Direta** (P&D) e Contexto Energético | Matriz limpa, transição energética (H2V), projetos de P&D do setor e confiabilidade elétrica |
| **IBGE** | População oficial (14,8M hab.), PIB/VAB (Indústria R$ 87B, Agro R$ 38B), Malha GeoJSON | Município (417 municípios) | **Denominador & Contexto** | Normalização per capita, intensidade econômica e renderização cartográfica municipal |

---

## 9. Síntese dos cruzamentos multissetoriais no TERRITÓRIOS SECTI

A força analítica do projeto **TERRITÓRIOS SECTI** reside no cruzamento integrado dessas dimensões para gerar novos índices compostos:

```
                      ARQUITETURA DE CRUZAMENTOS MULTISSETORIAIS
                      
               ┌──────────────────────────────────────────────┐
               │         IBGE (Base Territorial Comum)        │
               │   417 Municípios da Bahia (Código 7 Dígitos) │
               └──────────────────────┬───────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
  CAPITAL HUMANO (INEP)      FOMENTO E CRÉDITO (BNDES)    GOVERNO LOCAL (SICONFI)
  - Vagas e Matrículas STEM  - Financiamento Inovação     - Despesa Função 19 (C&T)
  - Docentes Doutores        - Apoio à Indústria 4.0      - Despesa Subf. 126 (TI)
         │                            │                            │
         └────────────────────────────┼────────────────────────────┘
                                      │
         ┌────────────────────────────┴────────────────────────────┐
         ▼                                                         ▼
  INFRAESTRUTURA DIGITAL (ANATEL)                           ENERGIA LIMPA (ANEEL)
  - % Domicílios com Fibra Óptica                           - Capacidade Eólica / Solar
  - Acessos Ultravelocidade (>34 Mbps)                      - Projetos de P&D Regulado
```

### Exemplos práticos de cruzamentos inovadores:
1. **Índice de Prontidão para a Transição Energética e H2V:**
   - Capacidade instalada Solar/Eólica (ANEEL) $+$ Cursos de Engenharia e Ciências (INEP) $+$ Financiamentos industriais e ambientais (BNDES) $\div$ PIB Municipal (IBGE).
2. **Índice de Maturidade do Ecossistema de Inovação Territorial:**
   - Doutores por mil habitantes (INEP) $+$ Despesa C&T per capita (SICONFI) $+$ Crédito Inovação BNDES per capita $+$ Densidade de Banda Larga em Fibra (ANATEL).
3. **Identificação de Polos Tecnológicos Regionais Emergentes:**
   - Municípios com crescimento simultâneo de matrículas em TIC (INEP), capilaridade de fibra óptica (ANATEL) e operações de crédito para modernização produtiva (BNDES), fora da Região Metropolitana de Salvador.

---

## 10. Limitações e cuidados metodológicos específicos por fonte

1. **INEP:**
   - Matrículas e vagas em cursos EAD **não devem ser atribuídas ao município do polo de apoio presencial** para fins de cálculo de capacidade instalada de ensino presencial.
   - Microdados individuais de docentes deixaram de ser publicados em 2024; a titulação docente (doutores/mestres) deve ser agregada a partir da sede da IES.
2. **BNDES:**
   - Operações diretas de infraestrutura interestadual ou de linhas de transmissão podem alocar o valor total contratado ao município sede da empresa no cadastro, demandando cautela na análise de valores bilionários atípicos.
3. **SICONFI:**
   - A declaração da DCA pelos municípios é autodeclaratória. A ausência de despesa na Função 19 não significa necessariamente que o município não investiu em informatização, uma vez que a maioria das prefeituras classifica sistemas digitais na Subfunção `04.126 (Administração/TI)`.
4. **ANATEL:**
   - A série de densidade de acessos por 100 domicílios apresentou descontinuidade nos anos de 2023 e 2024 no portal aberto. Recomenda-se derivar a densidade dividindo o volume mensal de acessos brutos pelo total de domicílios do Censo 2022 do IBGE.
5. **IBGE:**
   - O Agregado 6579 (população residente) não cobre os anos censitários (2010 e 2022) nem o ano intercensitário de 2023. Para esses períodos, deve-se recorrer ao Agregado 4709 (Censo Demográfico).

---

## 11. Conclusão

Este inventário demonstra que o ecossistema de dados para os indicadores do **TERRITÓRIOS SECTI** encontra-se plenamente mapeado, estruturado e respaldado por evidências empíricas reais:

1. **As variáveis de CT&I Direta** estão rigorosamente demarcadas no Censo Superior do INEP (formação STEM), nos contratos de fomento à inovação do BNDES, no orçamento da Função 19 do SICONFI e nos projetos de pesquisa da ANEEL.
2. **As variáveis de Infraestrutura e Contexto Habilitador** fornecem a leitura territorial da infraestrutura energética renovável (ANEEL), da malha de fibra óptica (ANATEL) e das bases demográficas e de valor adicionado industrial e agrícola (IBGE).
3. **A integração metodológica com chave comum nos 417 municípios** permite superar análises setoriais isoladas, viabilizando a construção de um painel integrado, moderno e fundamentado para a tomada de decisões da Secretaria de Ciência, Tecnologia e Inovação da Bahia (SECTI-BA).

# TERRITÓRIOS SECTI — Especificação de Extração das APIs/Fonte da Planilha

**Base:** `Planilha_Avaliacao_Fontes_Painel_Territorial(5).xlsx`  
**Escopo:** somente as fontes e indicadores presentes na planilha.  
**Objetivo:** orientar a extração real dos dados para os 417 municípios da Bahia e posterior agregação aos 27 Territórios de Identidade.

> **Importante:** nem todas as fontes da planilha são uma API REST pura. Algumas são microdados/CSV/portal de dados abertos. Neste documento, “fonte” significa o mecanismo oficial que deve ser usado para obter o dado indicado na planilha.

---

## 1. Regras gerais de extração

1. Trabalhar somente com **fontes oficiais**.
2. Focar nos **417 municípios da Bahia**.
3. Usar `codigo_ibge` como chave territorial sempre que a fonte disponibilizar esse identificador.
4. Quando a fonte não possuir código IBGE, criar tabela de correspondência e registrar a regra usada.
5. Preservar o identificador original da fonte.
6. Preservar `ano_referencia` e/ou `mes_referencia`.
7. Não substituir os 27 Territórios de Identidade da SECTI/SEPLAN por outra classificação territorial.
8. Dados derivados devem ser calculados depois da extração dos dados-base.
9. Não inventar campos que não existam no recurso oficial.
10. Salvar a URL exata do recurso utilizado e a data de coleta.
11. Preferir ETL/backend, arquivo consolidado e histórico em vez de depender de consulta ao vivo do front-end.
12. Para cada fonte, registrar se o dado foi **validado**, **parcialmente validado**, **apenas catalogado** ou **não testado**.

---

# 2. IBGE

## 2.1 População municipal residente

**Indicador da planilha:** População municipal residente

**Objetivo de extração**
- população dos 417 municípios da Bahia;
- valor por município;
- ano de referência;
- população usada como denominador de indicadores per capita.

**Fonte oficial**
- SIDRA: https://apisidra.ibge.gov.br/values
- API de agregados: https://servicodados.ibge.gov.br/api/v3/agregados
- Documentação: https://servicodados.ibge.gov.br/api/docs/agregados.html

**Referência da planilha**
- Agregado `6579`.

**Chave territorial**
- `codigo_ibge`.

**Saída mínima esperada**
```text
codigo_ibge
municipio
uf
ano_referencia
populacao
fonte
url_fonte
data_coleta
```

**Status na planilha:** Validado para os 417 municípios baianos.

---

## 2.2 PIB municipal

**Indicador da planilha:** PIB municipal

**Objetivo de extração**
- PIB municipal;
- série histórica disponível;
- ano de referência;
- comparação entre municípios e Territórios.

**Fonte oficial**
- SIDRA: https://apisidra.ibge.gov.br/values
- API de agregados: https://servicodados.ibge.gov.br/api/v3/agregados
- Documentação: https://servicodados.ibge.gov.br/api/docs/agregados.html

**Referência da planilha**
- Agregado `5938`;
- variável `37`.

**Chave territorial**
- `codigo_ibge`.

**Saída mínima esperada**
```text
codigo_ibge
municipio
uf
ano_referencia
pib
unidade
fonte
url_fonte
data_coleta
```

**Status na planilha:** Validado.

**Observação:** preservar o ano original do PIB; não rotular automaticamente como 2026.

---

## 2.3 PIB per capita

**Indicador da planilha:** PIB per capita

**Objetivo de extração**
- PIB per capita oficial quando disponível;
- ano de referência;
- município.

**Fontes oficiais**
- SIDRA: https://apisidra.ibge.gov.br/values
- Agregados IBGE: https://servicodados.ibge.gov.br/api/v3/agregados
- Página do PIB dos Municípios: https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html

**Referência da planilha**
- tabela `6784`;
- também foi utilizada base oficial XLSX do PIB dos Municípios.

**Regra de fallback**
- se a consulta API/SIDRA estiver indisponível, usar a planilha oficial do IBGE correspondente ao ano;
- registrar o arquivo oficial utilizado.

**Saída mínima esperada**
```text
codigo_ibge
municipio
uf
ano_referencia
pib_per_capita
fonte
url_fonte
data_coleta
```

**Status na planilha:** Validado parcialmente.

---

## 2.4 Área territorial municipal

**Indicador da planilha:** Área territorial municipal

**Objetivo de extração**
- área municipal em km²;
- município;
- código IBGE.

**Fonte oficial**
- Malhas IBGE: https://servicodados.ibge.gov.br/api/v3/malhas
- Estrutura territorial: https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial.html

**Chave territorial**
- `codigo_ibge`.

**Saída mínima**
```text
codigo_ibge
municipio
uf
area_km2
fonte
url_fonte
data_coleta
```

**Status na planilha:** Validado.

---

## 2.5 Densidade demográfica

**Indicador da planilha:** Densidade demográfica

**É um indicador derivado.**

**Dados-base necessários**
- população municipal do IBGE;
- área territorial municipal do IBGE.

**Fórmula**
```text
populacao / area_km2
```

**Saída**
```text
codigo_ibge
municipio
uf
ano_referencia
populacao
area_km2
densidade_demografica_hab_km2
```

**Status na planilha:** Validado.

---

## 2.6 PIB por km² (densidade econômica)

**Indicador da planilha:** PIB por km² (Densidade econômica)

**É um indicador derivado.**

**Dados-base necessários**
- PIB municipal;
- área territorial municipal.

**Fórmula**
```text
PIB / area_km2
```

**Unidade indicada na planilha**
```text
mil R$/km²
```

**Saída**
```text
codigo_ibge
municipio
uf
ano_referencia
pib
area_km2
pib_por_km2
```

**Status na planilha:** Validado.

---

## 2.7 Malha geográfica municipal

**Indicador da planilha:** Malha geográfica municipal

**Objetivo de extração**
- polígonos dos 417 municípios;
- geometria municipal;
- uso em mapas e agregações espaciais.

**Fonte oficial**
- API de malhas: https://servicodados.ibge.gov.br/api/v3/malhas
- Página de malhas: https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais.html

**Formato preferencial**
- GeoJSON ou geometria equivalente;
- simplificação posterior para o front-end, sem alterar a geometria-base armazenada.

**Saída mínima**
```text
codigo_ibge
municipio
uf
geometry
area_km2
centroide
fonte
url_fonte
data_coleta
```

**Status na planilha:** Validado para os 417 municípios.

---

# 3. INEP

> O INEP da planilha é tratado principalmente por **microdados oficiais**, e não como uma API REST municipal pronta. A extração deve usar os arquivos oficiais e normalizar os registros para município/código IBGE.

## 3.1 Instituições de Educação Superior (IES)

**Indicador da planilha:** Instituições de Educação Superior (IES)

**Objetivo de extração**
- instituições com sede ou presença na Bahia;
- código/nome da IES;
- município;
- UF;
- dependência administrativa;
- dados necessários para separar sede, campus e polo.

**Fonte oficial**
- Censo da Educação Superior: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior
- Catálogo de microdados: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados

**Ano prioritário atual**
```text
2024
```

**Campos a extrair/normalizar**
```text
codigo_ies
nome_ies
codigo_municipio
municipio
uf
categoria_administrativa
organizacao_academica
situacao
indicador_sede_campus_polo
ano_referencia
```

**Status da planilha:** Validado parcialmente no Censo 2023; 2024 é o próximo ciclo de atualização.

---

## 3.2 Cursos de graduação (Geral e CT&I)

**Indicador da planilha:** Cursos de graduação (Geral e CT&I)

**Objetivo de extração**
- curso;
- instituição;
- município;
- área/campo;
- modalidade;
- correspondência com os cursos CT&I da SECTI.

**Fonte oficial**
- https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior

**Ano prioritário**
```text
2024
```

**Campos-alvo**
```text
codigo_ies
nome_ies
codigo_curso
nome_curso
codigo_municipio
municipio
uf
modalidade
area_conhecimento
nivel_academico
situacao
ano_referencia
```

**Regra CT&I**
- preservar a taxonomia original do INEP;
- aplicar a classificação CT&I usada pelo projeto em camada separada;
- não alterar o nome oficial do curso.

**Status na planilha:** Validado; Censo 2023 teve correspondência exata de 641/642 cursos CT&I da SECTI.

---

## 3.3 Cursos por modalidade — presencial x EAD

**Indicador da planilha:** Cursos por modalidade (Presencial vs EAD)

**Dados-base**
- cursos presenciais;
- cursos EAD;
- município/polo;
- modalidade;
- ano.

**Fonte**
- https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior

**Regra**
- manter `presencial` e `ead` separadas;
- não contabilizar polo EAD como infraestrutura física de campus sem regra explícita;
- conservar a granularidade original para auditoria.

**Status:** Validado parcialmente.

---

## 3.4 Vagas ofertadas na graduação

**Indicador da planilha:** Vagas ofertadas na graduação

**Objetivo**
- vagas autorizadas/ofertadas;
- curso;
- instituição;
- município;
- modalidade;
- ano.

**Fonte**
- https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior

**Saída**
```text
codigo_ies
codigo_curso
nome_curso
codigo_municipio
municipio
modalidade
vagas
ano_referencia
```

**Status:** Catálogo identificado; não testado na planilha.

---

## 3.5 Matrículas no ensino superior

**Indicador da planilha:** Matrículas no ensino superior

**Objetivo**
- número de matrículas;
- curso;
- instituição;
- município;
- modalidade;
- ano.

**Fonte**
- https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior

**Regra crítica**
- separar matrículas presenciais das vinculadas a EAD;
- documentar como o município/polo é atribuído às matrículas EAD.

**Status:** Catálogo identificado; não testado na planilha.

---

## 3.6 Ingressantes e concluintes na graduação

**Indicador da planilha:** Ingressantes e concluintes na graduação

**Objetivo**
- ingressantes;
- concluintes;
- curso;
- instituição;
- município;
- modalidade;
- ano.

**Fonte**
- https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior

**Saída**
```text
codigo_ies
codigo_curso
codigo_municipio
modalidade
ingressantes
concluintes
ano_referencia
```

**Status:** Catálogo identificado; não testado.

---

## 3.7 Docentes do ensino superior — titulação

**Indicador da planilha:** Docentes do ensino superior (titulação)

**Objetivo**
- docentes;
- titulação;
- instituição;
- município quando possível;
- ano.

**Fonte**
- https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior

**Categorias de interesse**
- doutor;
- mestre;
- especialista;
- demais categorias disponíveis no arquivo oficial.

**Regra**
- preservar o vínculo oficial do docente com a instituição;
- evitar atribuir automaticamente docente da mantenedora a todos os campi.

**Status:** Catálogo identificado; não testado.

---

# 4. ANEEL

**Portal oficial**
- https://dadosabertos.aneel.gov.br/
- catálogo: https://dadosabertos.aneel.gov.br/dataset/

> Para ANEEL, o pipeline deve localizar o dataset oficial correspondente, baixar o recurso e registrar `dataset_id`, URL do recurso, período e dicionário de dados antes de consolidar.

## 4.1 Empreendimentos de geração e potência outorgada

**Indicador da planilha:** Empreendimentos de geração e potência outorgada

**Fonte prioritária**
- SIGA / dados de geração da ANEEL.

**Dados a extrair**
- empreendimento;
- código/nome do município;
- UF;
- potência outorgada/instalada em kW;
- fonte energética;
- situação;
- unidade geradora;
- identificadores originais do empreendimento.

**Chave territorial**
- código de município, quando disponível;
- caso contrário, nome do município + tabela de correspondência IBGE.

**Status:** Catálogo identificado; não testado na planilha.

---

## 4.2 Potência instalada de geração renovável — Solar e Eólica

**Indicador da planilha:** Potência instalada de geração renovável (Solar e Eólica)

**Fonte**
- https://dadosabertos.aneel.gov.br/

**Dados**
- empreendimentos solares;
- empreendimentos eólicos;
- potência;
- município;
- UF;
- situação;
- fonte energética.

**Regras**
- manter `solar` e `eólica` separadas;
- distinguir geração centralizada de geração distribuída quando o dataset permitir;
- não misturar potência outorgada com potência efetivamente em operação sem identificar o campo.

**Status:** Catálogo identificado; não testado.

---

## 4.3 Consumo de energia elétrica e unidades consumidoras

**Indicador da planilha:** Consumo de energia elétrica e unidades consumidoras

**Fonte prioritária indicada na planilha:** SAMP — Sistema de Acompanhamento de Mercado.

**Portal**
- https://dadosabertos.aneel.gov.br/

**Dados**
- município;
- classe de consumo;
- MWh faturado/consumido, conforme campo oficial;
- número de unidades consumidoras;
- período;
- UF;
- categoria tarifária, se existente.

**Classes prioritárias**
- industrial;
- comercial;
- residencial;
- demais classes existentes no dataset.

**Regra territorial**
- realizar correspondência dos nomes de municípios com código IBGE;
- registrar tabela de/para quando a fonte não fornecer código IBGE.

**Status:** Catálogo identificado; não testado.

---

## 4.4 Projetos de Pesquisa e Desenvolvimento — P&D ANEEL

**Indicador da planilha:** Projetos de Pesquisa e Desenvolvimento (P&D ANEEL)

**Fonte**
- https://dadosabertos.aneel.gov.br/

**Dados a extrair**
- projeto;
- empresa/concessionária;
- instituição executora;
- valor/investimento;
- ciclo/período;
- tema/linha de pesquisa;
- situação;
- município, quando disponível.

**Regra**
- preservar a granularidade original por projeto e entidade executora;
- só agregar ao município quando houver localização verificável.

**Status:** Catálogo identificado; não testado.

---

## 4.5 Qualidade do fornecimento — DEC e FEC

**Indicador da planilha:** Qualidade do fornecimento elétrico (DEC e FEC)

**Dataset oficial identificado**
- https://dadosabertos.aneel.gov.br/pt_BR/dataset/indicadores-coletivos-de-continuidade-dec-e-fec

**Dados a extrair**
- DEC;
- FEC;
- período;
- conjunto elétrico;
- limites;
- valores apurados;
- compensações, quando relevantes.

**Regra crítica**
- não apresentar o indicador como municipal se o dataset original estiver em conjunto elétrico;
- só converter para município quando existir uma relação oficial verificável.

**Status:** Catálogo identificado; não testado.

---

# 5. BNDES

**Portal oficial**
- https://dadosabertos.bndes.gov.br/

**Dataset principal**
- https://dadosabertos.bndes.gov.br/pt_BR/dataset/operacoes-financiamento

O dataset oficial de Operações de Financiamento contém dados detalhados das operações, incluindo condições, porte do cliente e produto contratado, com dados a partir de 2002. A atualização do portal é automática. 

## 5.1 Operações de financiamento e valor desembolsado

**Indicador da planilha:** Operações de financiamento e valor desembolsado

**Dados a extrair**
- operação;
- beneficiário/tomador;
- município;
- UF;
- valor;
- produto;
- porte;
- setor/CNAE;
- modalidade;
- data/período;
- forma de apoio/repasse, quando existir.

**Fonte**
- Operações de Financiamento: https://dadosabertos.bndes.gov.br/pt_BR/dataset/operacoes-financiamento

**Saída**
```text
id_operacao
municipio
codigo_ibge
uf
valor
produto
porte
setor_cnae
modalidade
periodo
```

**Status:** Catálogo identificado; não testado territorialmente.

---

## 5.2 Financiamento por setor econômico

**Indicador da planilha:** Financiamento por setor econômico

**Dados**
- valor por setor;
- operação;
- município;
- UF;
- CNAE/setor;
- período.

**Fonte**
- https://dadosabertos.bndes.gov.br/dataset/

**Regra**
- preservar o setor oficial BNDES;
- criar camada de correspondência com CNAE somente depois de validar a classificação.

**Status:** Catálogo identificado; não testado.

---

## 5.3 Financiamento por porte de beneficiário

**Indicador da planilha:** Financiamento por porte de beneficiário

**Categorias de interesse**
- micro;
- pequena;
- média;
- grande, conforme classificação oficial BNDES.

**Dados**
- operação;
- porte;
- município;
- valor;
- período.

**Fonte**
- https://dadosabertos.bndes.gov.br/pt_BR/dataset/operacoes-financiamento

**Status:** Catálogo identificado; não testado.

---

## 5.4 Forma de repasse — Direto x Indireto

**Indicador da planilha:** Financiamento por forma de repasse (Direto vs Indireto)

**Dados**
- forma de apoio;
- agente financeiro;
- município do beneficiário;
- valor;
- operação;
- período.

**Fonte**
- https://dadosabertos.bndes.gov.br/pt_BR/dataset/operacoes-financiamento

**Regra crítica**
- localizar o município do beneficiário/tomador;
- não confundir município da agência intermediadora com município do beneficiário.

**Status:** Catálogo identificado; não testado.

---

## 5.5 Apoio à inovação e difusão tecnológica

**Indicador da planilha:** Operações de apoio à inovação e difusão tecnológica

**Objetivo**
- localizar operações/linhas diretamente relacionadas a inovação, P&D e tecnologia;
- valor financiado/desembolsado;
- município;
- setor;
- período;
- linha/produto.

**Filtro temático sugerido pela planilha**
- linhas relacionadas a inovação, incluindo exemplos como BNDES Mais Inovação.

**Fonte**
- https://dadosabertos.bndes.gov.br/

**Regra**
- não inferir “inovação” somente pelo CNAE;
- registrar o motivo/filtro que fez a operação entrar no conjunto CT&I.

**Status:** Catálogo identificado; não testado.

---

## 5.6 Desembolso BNDES per capita

**Indicador da planilha:** Desembolso BNDES per capita (BNDES por habitante)

**É um indicador derivado.**

**Dados-base**
- desembolsos BNDES;
- população IBGE;
- mesmo ano ou período compatível.

**Fórmula**
```text
valor_desembolsado_bndes / populacao
```

**Saída**
```text
codigo_ibge
municipio
uf
ano_referencia
desembolso_bndes
populacao
desembolso_per_capita
```

**Regra crítica**
- não calcular se os anos/períodos do numerador e denominador forem incompatíveis;
- documentar o período usado.

**Status:** Pendente de validação na planilha.

---

# 6. SICONFI / TESOURO NACIONAL

## 6.1 Documentação

**API / documentação**
- https://apidatalake.tesouro.gov.br/docs/siconfi/

**Portal oficial SICONFI**
- https://www.tesourotransparente.gov.br/consultas/consultas-siconfi/siconfi-api-de-dados-abertos

**Identificação do ente**
- usar o código IBGE retornado pelo conjunto oficial de entes.

---

## 6.2 Receita municipal

**Indicador da planilha:** Receita municipal

**Objetivo**
- receitas municipais arrecadadas;
- município;
- exercício/período;
- classificações contábeis necessárias para indicadores fiscais.

**Dados a extrair**
- ente;
- código IBGE;
- exercício;
- período;
- receita;
- conta/classificação;
- valor;
- demonstrativo/anexo de origem.

**Fonte**
- API SICONFI.

**Status:** Catálogo identificado; indicador específico ainda precisa ser amarrado ao demonstrativo escolhido.

---

## 6.3 Despesa e investimento público municipal

**Indicador da planilha:** Despesa e investimento público municipal

**Dados prioritários**
- função;
- subfunção;
- dotação inicial;
- dotação atualizada;
- empenhado;
- liquidado;
- pago, se necessário e disponível;
- classificação de investimento.

**Anexo prioritário**
- RREO Anexo 02 — Despesas por Função/Subfunção.

**Regra anual**
- preferir o RREO de período 6 quando a intenção for usar o acumulado anual.

**Fonte**
- https://apidatalake.tesouro.gov.br/docs/siconfi/

**Status:** Catálogo identificado na planilha; no projeto já houve validação operacional do RREO/MSC para Salvador.

---

## 6.4 Receita ou investimento por habitante

**Indicador da planilha:** Receita ou investimento por habitante

**É um indicador derivado.**

**Dados-base**
- receita ou investimento do SICONFI;
- população IBGE;
- mesmo ano de referência.

**Fórmula**
```text
valor_siconfi / populacao_ibge
```

**Saída**
```text
codigo_ibge
municipio
uf
ano_referencia
valor_siconfi
populacao
valor_por_habitante
```

**Regra crítica**
- validar a definição contábil do numerador antes do cálculo;
- manter rastreabilidade para o anexo/conta de origem.

**Status:** Pendente de validação na planilha.

---

# 7. ANATEL

## 7.1 Densidade de acessos em serviço na banda larga fixa (SCM), por 100 domicílios

**Indicador da planilha:** Densidade de acessos em serviço na banda larga fixa (SCM), por 100 domicílios

**Portal oficial**
- https://www.gov.br/anatel/pt-br/dados/dados-abertos

**Metadados indicados na planilha**
- https://www.anatel.gov.br/dadosabertos/PDA/Acessos/Densidades.pdf

**Dado prioritário**
- densidade municipal de acessos SCM;
- ano;
- mês;
- UF;
- código IBGE do município;
- densidade.

**Campos já registrados na validação da planilha**
```text
ano
mes
sigla_uf
id_municipio
densidade
```

**Granularidade**
```text
Município × mês
```

**Histórico indicado na planilha**
```text
desde 2007
```

**Indicador oficial**
```text
acessos por 100 domicílios
```

**Regra**
- preservar o indicador oficial como publicado;
- não reinterpretar como velocidade, qualidade ou cobertura;
- registrar mês e ano;
- agregar aos 27 Territórios usando o município/IBGE.

**Status na planilha:** Validado em Salvador.

---

## 7.2 Cobertura de telefonia móvel (SMP 4G) por município — % de território e % de moradores cobertos

**Indicador da planilha:** Cobertura de telefonia móvel (SMP 4G) — % de território coberto (`% área coberta`), % de moradores cobertos (`% moradores cobertos`) e % de domicílios cobertos (`% domicílios cobertos`).

**Portal oficial e identificador do recurso:**
- Portal de Dados Abertos / Anatel (dados.gov.br)
- **Recurso:** `1449ea53-fe84-4547-8ac8-f6a465995958`
- **Painel de origem:** Painel de Cobertura Móvel da Anatel (Sistemas Mosaico / modelos ITU-R P.1812 com base censitária IBGE)

**Dado prioritário:**
- Código IBGE do município (`Código Município`);
- Nome do município (`Município`);
- UF (`BA`);
- Operadora (`Todas`);
- Tecnologia (`4G`);
- `% área coberta` (proporção do território geográfico municipal com sinal 4G);
- `% moradores cobertos` (proporção dos residentes atendidos pelo sinal);
- `% domicílios cobertos` (proporção dos domicílios atendidos);
- `Área km2`, `Moradores`, `Domicílios` (denominadores de referência).

**Campos registrados na validação da planilha:**
```text
Código Município
Município
UF
Região
Operadora
Tecnologia
% área coberta
% moradores cobertos
% domicílios cobertos
Área km2
Moradores
Domicílios
```

**Granularidade:**
```text
Município (417 municípios da Bahia)
```

**Regras metodológicas e de validação:**
- **Preservar a distinção entre cobertura de território e moradores:** O percentual de território (`% área coberta`, média de 35,4% na Bahia) reflete a expansão física e infraestrutura em rodovias e zonas rurais, enquanto o percentual de moradores (`% moradores cobertos`, média de 73,9% na Bahia) mede o alcance populacional. Ambas as colunas devem ser mantidas no painel da SECTI;
- **Tratamento de duplicatas no arquivo bruto:** O recurso bruto trazia 421 linhas, contendo 4 registros duplicados decorrentes de variações históricas de grafia com valores zerados/hífen (`Araçás`, `Iuiu`, `Muquém do São Francisco`, `Santa Terezinha`), os quais foram filtrados, consolidando exatamente 417 municípios únicos com dados válidos;
- **Normalização numérica:** Converter valores de texto com vírgula (`% domicílios cobertos` e `Área km2`) para float decimal;
- **Integração territorial:** Agregar aos 27 Territórios de Identidade da Bahia pelo código IBGE municipal.

**Status na planilha:** Validado (417 municípios da Bahia na aba `ANATEL_Cobertura_Movel`).

---

# 8. Indicadores derivados da planilha — resumo de dependências

| Indicador | Dados-base | Regra |
|---|---|---|
| Densidade demográfica | IBGE população + IBGE área | população / área_km² |
| PIB por km² | IBGE PIB + IBGE área | PIB / área_km² |
| Desembolso BNDES per capita | BNDES + IBGE população | desembolso / população |
| Receita por habitante | SICONFI + IBGE população | receita / população |
| Investimento por habitante | SICONFI + IBGE população | investimento / população |

---

# 9. Ordem recomendada de extração

## Etapa 1 — Base territorial
```text
IBGE
├── 417 municípios
├── códigos IBGE
├── população
├── PIB
├── PIB per capita
├── área
└── malha municipal
```

## Etapa 2 — Educação
```text
INEP
├── IES
├── cursos
├── presencial / EAD
├── vagas
├── matrículas
├── ingressantes
├── concluintes
└── docentes / titulação
```

## Etapa 3 — Finanças públicas
```text
SICONFI
├── receita
├── despesa
├── investimento
└── indicadores por habitante
```

## Etapa 4 — Conectividade
```text
ANATEL
├── densidade SCM por 100 domicílios
├── acessos de banda larga fixa (fibra e velocidade)
└── cobertura móvel SMP 4G (% território e % moradores)
```

## Etapa 5 — Energia
```text
ANEEL
├── geração
├── potência renovável
├── consumo
├── P&D
└── DEC / FEC
```

## Etapa 6 — Financiamento
```text
BNDES
├── operações
├── desembolsos
├── setor
├── porte
├── direto / indireto
└── inovação
```

---

# 10. Estrutura mínima de saída consolidada

Cada registro persistido deve conter, quando possível:

```text
source
source_dataset
source_record_id
codigo_ibge
municipio
uf
territorio_id
territorio_nome
ano_referencia
mes_referencia
indicador
categoria
subcategoria
valor
unidade
status_validacao
source_url
dataset_url
collected_at
```

---

# 11. Critérios de validação antes de entrar no painel

### IBGE
- [ ] 417 municípios presentes.
- [ ] código IBGE único por município.
- [ ] sem município duplicado.
- [ ] ano de referência registrado.
- [ ] geometrias válidas.

### INEP
- [ ] Bahia filtrada corretamente.
- [ ] código do município normalizado.
- [ ] presencial e EAD separados.
- [ ] sede/campus/polo não confundidos.
- [ ] curso/I​ES preservados com identificadores originais.

### ANEEL
- [ ] dataset oficial identificado.
- [ ] `dataset_id` registrado.
- [ ] recurso/arquivo oficial registrado.
- [ ] município padronizado.
- [ ] granularidade original preservada.
- [ ] conjunto elétrico não apresentado como município sem evidência oficial.

### BNDES
- [ ] operação identificada.
- [ ] município do beneficiário separado do agente financeiro.
- [ ] valor e período preservados.
- [ ] setor/porte preservados.
- [ ] classificação de inovação baseada em regra explícita.

### SICONFI
- [ ] ente vinculado ao código IBGE.
- [ ] exercício e período preservados.
- [ ] anexo/demonstrativo registrado.
- [ ] evitar dupla contagem de períodos.
- [ ] indicadores anuais preferencialmente reconciliados com período 6 quando aplicável.

### ANATEL
- [ ] município/código IBGE preservado.
- [ ] mês e ano preservados.
- [ ] densidade mantida na unidade oficial.
- [ ] não confundir densidade com velocidade ou cobertura.
- [ ] cobertura móvel: 417 municípios presentes sem duplicatas residuais.
- [ ] manter % de área coberta e % de moradores cobertos como métricas distintas.

---

# 12. Fontes oficiais principais

## IBGE
- https://apisidra.ibge.gov.br/values
- https://servicodados.ibge.gov.br/api/v3/agregados
- https://servicodados.ibge.gov.br/api/v3/malhas
- https://servicodados.ibge.gov.br/api/docs/agregados.html
- https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial.html

## INEP
- https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados
- https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior

## ANEEL
- https://dadosabertos.aneel.gov.br/
- https://dadosabertos.aneel.gov.br/dataset/
- https://dadosabertos.aneel.gov.br/pt_BR/dataset/indicadores-coletivos-de-continuidade-dec-e-fec

## BNDES
- https://dadosabertos.bndes.gov.br/
- https://dadosabertos.bndes.gov.br/pt_BR/dataset/operacoes-financiamento

## SICONFI / Tesouro
- https://apidatalake.tesouro.gov.br/docs/siconfi/
- https://www.tesourotransparente.gov.br/consultas/consultas-siconfi/siconfi-api-de-dados-abertos

## ANATEL
- https://www.gov.br/anatel/pt-br/dados/dados-abertos
- https://www.anatel.gov.br/dadosabertos/PDA/Acessos/Densidades.pdf
- https://dados.gov.br (recurso 1449ea53-fe84-4547-8ac8-f6a465995958 — Cobertura Móvel SMP 4G)

---

# 13. Observação final

Este arquivo **não adiciona novas APIs** além das fontes presentes na planilha. Ele transforma os indicadores da planilha em uma especificação operacional de extração: **o que buscar, de qual fonte, em qual granularidade, quais chaves preservar e quais regras usar para derivar os indicadores**.

Quando um item da planilha está apenas como “Catálogo identificado” ou “Não testado”, o pipeline deve primeiro validar o dataset/recurso oficial e só depois marcar o dado como validado.

// Gera TERRITORIOS_SECTI_Resumo_Executivo_Dados.docx (resumo executivo das fontes e filtros CT&I).
// Uso: npm install docx && node scripts/gerar_docx_executivo.js TERRITORIOS_SECTI_Resumo_Executivo_Dados.docx
//      node scripts/gerar_docx_executivo.js TERRITORIOS_SECTI_Resumo_Executivo_Planilha.docx excel
// O modo "excel" troca as referências a pastas e arquivos do repositório pelas abas de TERRITORIOS_SECTI_Amostras_CTI.xlsx.
// Os números vêm de RESULTADOS_AMOSTRAGEM.md; atualize os dois juntos.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  HeadingLevel, AlignmentType, LevelFormat, Footer, Header, PageNumber, BorderStyle, PageBreak,
  TableOfContents,
} = require("docx");

const OUT = process.argv[2];
const EXCEL = process.argv[3] === "excel";
const PLANILHA = "TERRITORIOS_SECTI_Amostras_CTI.xlsx";
// dataset (1ª coluna das tabelas "O que cada dataset retorna") -> aba da planilha
const ABA = {
  "População (SIDRA 6579)": "IBGE_Populacao", "PIB e VAB (SIDRA 5938)": "IBGE_PIB_VAB",
  "PIB per capita oficial (base do PIB dos Municípios)": "IBGE_PIB_per_capita_2023", "Área e centroide (Malhas)": "IBGE_Area",
  "Malha geográfica (GeoJSON)": "IBGE_Malha", "Derivados": "IBGE_Derivados",
  "Instituições (IES)": "INEP_IES", "Cursos de graduação": "INEP_Cursos", "Cursos por município": "INEP_Cursos_Municipio",
  "SIGA – empreendimentos de geração": "ANEEL_SIGA", "INDGER – dados comerciais": "ANEEL_INDGER",
  "SAMP – mercado de energia": "ANEEL_SAMP", "P&D ANEEL – projetos": "ANEEL_PeD",
  "DEC/FEC por conjunto": "ANEEL_DECFEC_Conjunto", "DEC/FEC por município": "ANEEL_DECFEC_Municipio",
  "INDQUAL – de-para": "ANEEL_INDQUAL",
  "Operações não automáticas": "BNDES_Nao_Automaticas", "Operações indiretas automáticas": "BNDES_Indiretas_Automaticas",
  "CT&I por município e ano": "BNDES_CTI_Municipio_Ano",
  "DCA Anexo I-C (receita)": "SICONFI_Receita", "RREO Anexo 02 (despesa por função)": "SICONFI_RREO_CTI",
  "DCA Anexo I-E (despesa por função)": "SICONFI_DCA_CTI",
  "Densidade de banda larga fixa": "ANATEL_Densidade", "Acessos de banda larga fixa": "ANATEL_Acessos",
  "Cobertura móvel (SMP 4G)": "ANATEL_Cobertura_Movel",
};
const AZUL = "1F3864", AZUL_CLARO = "DCE6F2", CINZA = "F2F2F2", VERDE = "E2F0D9", AMARELO = "FFF2CC", VERMELHO = "FBE4D5";
const W = 9638; // largura útil A4 com margens de 2 cm

// ---------- helpers
const runs = (txt, base = {}) => {
  // **negrito** dentro do texto
  return txt.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(s =>
    s.startsWith("**") ? new TextRun({ ...base, text: s.slice(2, -2), bold: true }) : new TextRun({ ...base, text: s }));
};
const p = (txt, opt = {}) => new Paragraph({ children: runs(txt, opt.run || {}), spacing: { after: 120, line: 276 }, ...opt.par });
const h1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)], pageBreakBefore: true });
const h1nb = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const h3 = t => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const bl = (txt, lvl = 0) => new Paragraph({ numbering: { reference: "bullets", level: lvl }, children: runs(txt), spacing: { after: 60, line: 264 } });
const nota = txt => new Paragraph({
  children: runs(txt, { size: 19, color: "404040" }), spacing: { before: 60, after: 160 },
  shading: { type: ShadingType.CLEAR, fill: AMARELO, color: "auto" },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: "BF9000", space: 6 } }, indent: { left: 120 },
});
const esp = () => new Paragraph({ children: [], spacing: { after: 60 } });

const borda = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const bordas = { top: borda, bottom: borda, left: borda, right: borda };
function tabela(cab, linhas, pesos, opt = {}) {
  const tot = pesos.reduce((a, b) => a + b, 0);
  const larg = pesos.map(x => Math.floor(W * x / tot));
  larg[larg.length - 1] += W - larg.reduce((a, b) => a + b, 0);
  const cel = (txt, i, head, fill) => new TableCell({
    width: { size: larg[i], type: WidthType.DXA }, borders: bordas,
    shading: { type: ShadingType.CLEAR, color: "auto", fill: head ? AZUL : (fill || "FFFFFF") },
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: String(txt).split("\n").map(l => new Paragraph({
      children: runs(l, { size: 17, color: head ? "FFFFFF" : "000000", bold: head || undefined }), spacing: { after: 20 } })),
  });
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: larg,
    rows: [
      new TableRow({ tableHeader: true, children: cab.map((c, i) => cel(c, i, true)) }),
      ...linhas.map(l => (EXCEL && cab[0] === "Dataset" && ABA[l[0]]) ? [l[0] + "\nAba: **" + ABA[l[0]] + "**", ...l.slice(1)] : l)
        .map((l, k) => new TableRow({ cantSplit: true, children: l.map((c, i) =>
        cel(c, i, false, opt.cor ? opt.cor(l, i) : (k % 2 ? CINZA : "FFFFFF"))) })),
    ],
  });
}
const corFiltro = (l, i) => {
  const s = l.find(x => /^(✅|🏷️|🔶|⬜)/.test(String(x))) || "";
  if (!s) return "FFFFFF";
  if (String(s).startsWith("✅")) return VERDE;
  if (String(s).startsWith("🏷️")) return AZUL_CLARO;
  if (String(s).startsWith("🔶")) return AMARELO;
  return "FFFFFF";
};

// ---------- conteúdo
const C = [];

// Capa
C.push(new Paragraph({ spacing: { before: 2400, after: 200 }, children: [new TextRun({ text: "TERRITÓRIOS SECTI", bold: true, size: 56, color: AZUL })] }));
C.push(new Paragraph({ spacing: { after: 400 }, children: [new TextRun({ text: "Resumo executivo das fontes de dados abertos e dos filtros de Ciência, Tecnologia e Inovação (CT&I)", size: 32, color: "404040" })] }));
C.push(new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: AZUL, space: 4 } }, children: [] }));
C.push(p("**Recorte:** Estado da Bahia, 417 municípios"));
C.push(p("**Fontes:** IBGE, INEP, ANEEL, BNDES, SICONFI/Tesouro Nacional e ANATEL"));
C.push(p("**Coleta dos dados:** 01 a 07 de outubro de 2026"));
C.push(p(EXCEL ? "**Dados de apoio:** planilha " + PLANILHA + " (uma aba por dataset + aba de filtros CT&I)"
                : "**Documento técnico de referência:** RESULTADOS_AMOSTRAGEM.md (pasta do projeto)"));
C.push(new Paragraph({ children: [new PageBreak()] }));
C.push(new Paragraph({ children: [new TextRun({ text: "Sumário", bold: true, size: 32, color: AZUL })], spacing: { after: 200 } }));
C.push(new TableOfContents("Sumário", { hyperlink: true, headingStyleRange: "1-2" }));
C.push(p("(Se o sumário aparecer vazio, clique com o botão direito sobre ele no Word e escolha \"Atualizar campo\".)", { run: { size: 17, italics: true, color: "808080" } }));

// 1. Resumo executivo
C.push(h1("1. Resumo executivo"));
C.push(p("O projeto TERRITÓRIOS SECTI precisa medir, município a município, a presença de Ciência, Tecnologia e Inovação na Bahia. Para isso foram testadas seis fontes oficiais de dados abertos. Todas responderam, e cada uma cumpre um papel diferente no painel."));
C.push(h2("1.1 Principais mensagens"));
[
  "**Todas as seis fontes foram validadas** com dados reais da Bahia. Todas, exceto parte da ANEEL, chegam ao nível de município pelo código IBGE de 7 dígitos, que é a chave comum do painel.",
  "**Quatro fontes têm variável que identifica CT&I diretamente:** INEP (área do curso, classificação CINE), BNDES (flag de inovação e linhas de financiamento), SICONFI (Função 19 – Ciência e Tecnologia) e ANEEL (projetos de P&D).",
  "**IBGE e ANATEL não têm variável de CT&I.** O IBGE fornece os denominadores (população, PIB, área). A ANATEL mede a infraestrutura digital (banda larga, fibra).",
  "**O investimento público municipal em CT&I é muito concentrado:** só 8 dos 415 municípios com contas de 2024 gastaram na Função 19, e Salvador responde por 95% do valor.",
  "**O crédito do BNDES para inovação é pequeno:** 314 operações e R$ 851 milhões, cerca de 1% do total desembolsado na Bahia desde 2002.",
  "**A formação STEM está em 38 municípios:** 399 cursos presenciais de ciências, computação e engenharia, com 36,8 mil matrículas presenciais.",
].forEach(t => C.push(bl(t)));

C.push(h2("1.2 Visão geral das fontes"));
C.push(tabela(
  ["Fonte", "Função no painel", "Tem variável CT&I?", "Nível territorial", "Situação"],
  [
    ["IBGE", "Denominadores: população, PIB, área e mapa dos municípios", "Não", "Município (417)", "Validado"],
    ["INEP", "Capital humano: instituições, cursos, matrículas e doutores", "Sim: área do curso (CINE)", "Município do curso (56 presencial)", "Validado (2024)"],
    ["ANEEL", "Energia: geração renovável, P&D do setor elétrico e qualidade da rede", "Sim, no P&D (dataset inteiro)", "Usina, conjunto elétrico ou distribuidora", "Validado"],
    ["BNDES", "Crédito: financiamento à inovação e à modernização produtiva", "Sim: flag de inovação e linhas", "Município (416)", "Validado (2002–2026)"],
    ["SICONFI", "Gasto público: despesa municipal em Ciência e Tecnologia", "Sim: Função 19", "Município (415)", "Validado (2024)"],
    ["ANATEL", "Conectividade: banda larga fixa (fibra/velocidade) e móvel (cobertura 4G)", "Não (infraestrutura TIC)", "Município (417)", "Validado"],
  ], [1.1, 3, 1.9, 1.9, 1.5]));

// 2. Estrutura dos dados
if (EXCEL) {
  C.push(h1("2. Como a planilha de dados está organizada"));
  C.push(p("Os dados citados neste documento estão reunidos em um único arquivo Excel, **" + PLANILHA + "**, com uma aba por dataset. Não é preciso abrir pastas nem arquivos CSV."));
  C.push(h2("2.1 Estrutura do arquivo"));
  C.push(tabela(["Aba", "O que contém", "Para que serve"], [
    ["LEIA-ME", "Índice de todas as abas: fonte, o que o dataset retorna, recorte da amostra, situação do filtro CT&I, variáveis CT&I, nº de linhas e colunas. O nome de cada aba é um link", "Ponto de partida: achar o dataset e entender o que ele traz"],
    ["Filtros_CTI", "Lista única de filtros de CT&I: fonte, dataset, campo, operador, valores, nível (principal, ampliado, auxiliar, recorte) e justificativa", "Regra oficial de recorte CT&I do painel"],
    ["IBGE_… (6 abas)", "População, PIB e VAB, PIB per capita oficial 2023, derivados, área e malha", "Denominadores e contexto"],
    ["INEP_… (3 abas)", "Instituições, cursos de graduação e cursos por município", "Capital humano"],
    ["ANEEL_… (7 abas)", "Usinas (SIGA), dados comerciais, mercado, P&D, DEC/FEC por conjunto e por município, de-para conjunto–município", "Energia e P&D do setor elétrico"],
    ["BNDES_… (3 abas)", "Operações não automáticas, indiretas automáticas e o painel completo de CT&I por município e ano", "Crédito à inovação"],
    ["SICONFI_… (3 abas)", "Receita, despesa do RREO filtrada por CT&I e painel de despesa CT&I dos 415 municípios", "Gasto público municipal em CT&I"],
    ["ANATEL_… (3 abas)", "Densidade de banda larga, acessos detalhados e cobertura móvel 4G (% área e moradores)", "Infraestrutura digital"],
  ], [2, 4.6, 2.4]));
  C.push(h2("2.2 Como ler cada aba de dados"));
  C.push(bl("**Linha 1:** descrição do dataset, arquivo de origem e um link \"← LEIA-ME\" para voltar ao índice."));
  C.push(bl("**Linha 2:** nomes das colunas, exatamente como vêm da fonte oficial (ou como calculados, no caso das colunas cti_* e nivel_cti). A linha tem filtro automático e fica congelada ao rolar."));
  C.push(bl("**Da linha 3 em diante:** os dados. Valores numéricos estão como número; códigos (CNPJ, códigos CINE) ficam como texto para não perder zeros à esquerda."));
  C.push(bl("No LEIA-ME, as linhas são coloridas pela situação do filtro CT&I: verde = filtrado, azul = classificado, amarelo = não filtrado mas com variável CT&I, branco/cinza = sem variável."));
  C.push(nota("Abas de amostra: algumas abas trazem a base completa da Bahia (ex.: IBGE_PIB_per_capita_2023, ANEEL_SIGA, ANEEL_PeD, SICONFI_DCA_CTI, BNDES_CTI_Municipio_Ano). Outras trazem um recorte para ilustrar a estrutura (ex.: BNDES_Nao_Automaticas, com 30 das 1.104 operações). A coluna \"Recorte da amostra\" do LEIA-ME diz qual é o caso."));
} else {
C.push(h1("2. Como os dados estão organizados"));
  C.push(p("Tudo o que foi coletado está na pasta do projeto, em arquivos CSV (abrem direto no Excel). A organização é a seguinte:"));
  C.push(tabela(["Pasta / arquivo", "O que contém", "Para que serve"], [
    ["amostras/", "Uma amostra de dados reais de cada fonte (24 arquivos)", "Ver como cada dataset é na prática: colunas, valores, formato"],
    ["categorias_cti/", "Todos os valores possíveis das variáveis categóricas, com contagem na Bahia e relação com CT&I", "Decidir quais valores entram no filtro de CT&I"],
    ["categorias_cti/filtros_cti_consolidado.csv", "Lista única de filtros de CT&I: fonte, campo, valores, nível e justificativa", "Regra oficial de recorte CT&I do painel"],
    ["status_validacao_fontes.csv", "Situação de cada indicador da planilha (validado ou não), com a URL testada", "Controle do que já funciona"],
    ["scripts/", "Programas em Python que baixam e processam os dados", "Reproduzir e atualizar tudo"],
    ["RESULTADOS_AMOSTRAGEM.md", "Documento técnico completo", "Consulta detalhada da equipe técnica"],
  ], [2.3, 3.6, 2.8]));
}

C.push(h2((EXCEL ? "2.3" : "2.1") + " A chave comum: o código IBGE do município"));
C.push(p("Todas as fontes são cruzadas pelo **código IBGE de 7 dígitos** (ex.: 2927408 = Salvador). Ele permite somar, comparar e dividir valores de fontes diferentes no mesmo município. Há três exceções:"));
C.push(bl("**SIGA (ANEEL):** traz o município só como texto (\"Camaçari - BA\"). Precisa ser padronizado antes do cruzamento."));
C.push(bl("**P&D ANEEL e mercado de energia (SAMP):** não têm município, só a distribuidora (COELBA)."));
C.push(bl("**DEC/FEC (ANEEL):** vem por conjunto elétrico, que atende vários municípios. A tabela INDQUAL faz a ponte."));

C.push(h2((EXCEL ? "2.4" : "2.2") + " Como classificamos cada dataset em relação a CT&I"));
C.push(p("Cada grupo de dataset cai em uma de quatro situações. Essa classificação aparece em todas as tabelas das seções seguintes:"));
C.push(tabela(["Situação", "Significado"], [
  ["✅ Filtrado por CT&I", "As linhas do arquivo já foram selecionadas por uma variável de CT&I. Tudo o que está no arquivo é CT&I"],
  ["🏷️ Classificado", "O arquivo tem linhas de CT&I e de fora, mas cada linha tem uma coluna dizendo a qual grupo pertence"],
  ["🔶 Não filtrado, mas tem variável CT&I", "Nenhum filtro foi aplicado, mas existe um campo que permite fazer o recorte"],
  ["⬜ Sem variável CT&I", "Não há classificação de CT&I. Serve como denominador, contexto ou infraestrutura"],
], [2.5, 6], { cor: (l) => corFiltro(l) }));
C.push(nota("Recortes por estado, município ou distribuidora (ex.: \"só Bahia\", \"só COELBA\") não são filtros de CT&I. Eles só delimitam o território."));

C.push(h2((EXCEL ? "2.5" : "2.3") + " Níveis de CT&I usados nos filtros"));
C.push(tabela(["Nível", "Significado", "Exemplo"], [
  ["Principal", "O valor identifica CT&I de forma direta e pode entrar no indicador sem revisão", "Cursos de engenharia; Função 19 do orçamento; projetos de P&D"],
  ["Ampliado", "Tem base científica, mas inclui atividades que não são de pesquisa", "Cursos de saúde e de agrárias"],
  ["Auxiliar", "Indica contexto tecnológico; usar como camada complementar ou com revisão", "Gasto com TI da prefeitura; usinas solares; acessos por fibra"],
  ["Recorte", "Não identifica CT&I, mas serve para quebrar o resultado", "Porte da empresa; presencial x EAD"],
], [1.4, 4.2, 3]));

// 3. Fontes
C.push(h1nb("3. As fontes, uma a uma"));
C.push(p("Para cada fonte, esta seção mostra: o papel no painel, o que cada dataset retorna, as variáveis categóricas que existem e como se relacionam com CT&I, os números principais da Bahia e os cuidados de uso."));

// IBGE
C.push(h2("3.1 IBGE — Base territorial e denominadores"));
C.push(p("**Papel:** fornece a população, o PIB e a área de cada município. Esses números são os denominadores do painel: transformam valores absolutos em indicadores comparáveis (gasto por habitante, matrículas por mil habitantes, crédito por PIB). A malha geográfica é a base dos mapas."));
C.push(h3("O que cada dataset retorna"));
C.push(tabela(["Dataset", "O que retorna", "Período / cobertura", "Filtro CT&I"], [
  ["População (SIDRA 6579)", "População residente estimada por município", "2024–2026, 417 municípios", "⬜ Sem variável"],
  ["PIB e VAB (SIDRA 5938)", "PIB e valor adicionado por setor: agropecuária, indústria, serviços e administração pública", "2022–2023, 417 municípios", "⬜ Sem variável"],
  ["PIB per capita oficial (base do PIB dos Municípios)", "PIB e PIB per capita oficiais de cada município", "2023, 417 municípios", "⬜ Sem variável"],
  ["Área e centroide (Malhas)", "Área em km² e coordenadas do centro do município", "417 municípios", "⬜ Sem variável"],
  ["Malha geográfica (GeoJSON)", "Polígono de cada município, identificado pelo código IBGE", "417 municípios", "⬜ Sem variável"],
  ["Derivados", "Densidade demográfica (hab/km²) e PIB por km²", "Calculados", "⬜ Sem variável"],
], [2.4, 3.6, 1.8, 1.4], { cor: corFiltro }));
C.push(h3("Variáveis categóricas"));
C.push(p("O IBGE não tem variável categórica de CT&I. A única abertura setorial é a do valor adicionado (agropecuária, indústria, serviços, administração pública), útil para caracterizar a vocação econômica do território."));
C.push(h3("Números da Bahia"));
C.push(bl("População 2026: **14,89 milhões** de habitantes."));
C.push(bl("PIB 2023: **R$ 430,99 bilhões**; VAB da indústria R$ 87,4 bi e da agropecuária R$ 38,5 bi."));
C.push(bl("Maior PIB per capita 2023: São Francisco do Conde (R$ 684 mil por habitante, efeito da refinaria). Menor: Mansidão (R$ 8,5 mil)."));
C.push(nota("A tabela de PIB per capita da SIDRA (6784) só tem o valor nacional, e a população municipal de 2023 não existe na SIDRA. Por isso o PIB per capita de 2023 vem do arquivo oficial do PIB dos Municípios. O PIB desse arquivo confere 100% com a SIDRA."));

// INEP
C.push(h2("3.2 INEP — Educação superior e capital humano"));
C.push(p("**Papel:** mostra onde estão as instituições de ensino superior, quais cursos existem em cada município, quantos alunos estudam e se formam, e quantos professores doutores cada instituição tem. É a principal medida de capital humano em CT&I. Fonte: Censo da Educação Superior 2024 (microdados)."));
C.push(h3("O que cada dataset retorna"));
C.push(tabela(["Dataset", "O que retorna", "Cobertura", "Filtro CT&I"], [
  ["Instituições (IES)", "Uma linha por instituição: tipo, rede (pública/privada), município da sede, nº de docentes por titulação, acesso ao Portal CAPES e repositório institucional", "145 IES com sede na BA", "🔶 Não filtrado: tipo IF/CEFET e nº de doutores"],
  ["Cursos de graduação", "Uma linha por curso e município: área do curso (CINE), grau, modalidade, vagas, inscritos, ingressantes, matrículas e concluintes", "40.715 linhas (1.851 presenciais + 38.864 EAD)", "🏷️ Classificado pela coluna nivel_cti"],
  ["Cursos por município", "Soma de cursos, vagas, matrículas, ingressantes e concluintes por município e nível de CT&I", "Só presencial", "🏷️ Classificado"],
], [1.6, 4.2, 1.8, 1.8], { cor: corFiltro }));
C.push(h3("Variáveis categóricas e relação com CT&I"));
C.push(tabela(["Variável", "Valores", "Uso em CT&I"], [
  ["CO_CINE_AREA_GERAL (área do curso)", "05 Ciências naturais, matemática e estatística · 06 Computação e TIC · 07 Engenharia, produção e construção", "**Principal: núcleo STEM**"],
  ["", "08 Agricultura, silvicultura, pesca e veterinária · 09 Saúde e bem-estar", "Ampliado"],
  ["", "00 Programas básicos · 01 Educação · 02 Artes e humanidades · 03 Ciências sociais · 04 Negócios e direito · 10 Serviços", "Fora de CT&I"],
  ["CINE detalhada e rótulo", "80 áreas detalhadas e 240 rótulos de curso presentes na BA (ex.: Engenharia química, Ciência da computação)", "Refinamento do filtro"],
  ["TP_GRAU_ACADEMICO", "Bacharelado · Licenciatura · Tecnológico · Bacharelado e Licenciatura", "Auxiliar: Tecnológico"],
  ["TP_ORGANIZACAO_ACADEMICA", "Universidade (11) · Centro Universitário (25) · Faculdade (107) · Instituto Federal (2) · CEFET (0)", "Auxiliar: IF e CEFET"],
  ["TP_DIMENSAO / modalidade", "Presencial · EAD por polo · EAD só nível Brasil · EAD no exterior", "Regra: nunca somar presencial com EAD"],
  ["TP_CATEGORIA_ADMINISTRATIVA", "Pública federal · estadual · municipal · Privada com e sem fins lucrativos · Especial", "Recorte"],
], [2.4, 4.8, 1.8]));
C.push(h3("Números da Bahia (2024)"));
C.push(bl("**145 instituições** com sede em 45 municípios; **10.022 docentes doutores** em exercício (UFBA: 2.466)."));
C.push(bl("**1.851 cursos presenciais** em 56 municípios, com 254 mil matrículas."));
C.push(bl("**Núcleo STEM presencial: 399 cursos em 38 municípios, 36.753 matrículas.** Somando o EAD, o núcleo STEM chega a 67.325 matrículas."));
C.push(nota("Cuidados: (1) vagas e inscritos de EAD não são calculados por município, então o EAD não pode ser somado ao presencial; (2) o arquivo de instituições só informa o município da sede, não o de cada campus; (3) a lista SECTI de 642 cursos de CT&I não estava disponível. Quando chegar, passa a ser o filtro principal."));

// ANEEL
C.push(h2("3.3 ANEEL — Energia, P&D do setor elétrico e qualidade da rede"));
C.push(p("**Papel:** mostra a vocação energética dos territórios (usinas solares e eólicas), o investimento em pesquisa e desenvolvimento das distribuidoras (P&D ANEEL, que é CT&I direta) e a confiabilidade da rede elétrica, que importa para laboratórios, data centers e parques tecnológicos."));
C.push(h3("O que cada dataset retorna"));
C.push(tabela(["Dataset", "O que retorna", "Cobertura", "Filtro CT&I"], [
  ["SIGA – empreendimentos de geração", "Uma linha por usina: tipo, fonte de energia, fase, potência outorgada e fiscalizada, coordenadas e município (texto)", "1.163 usinas em 123 municípios", "🔶 Não filtrado: solar e eólica (auxiliar)"],
  ["INDGER – dados comerciais", "Unidades consumidoras ativas e faturadas por município e mês, além de indicadores de faturamento e atendimento", "409 municípios, 2023–2026", "⬜ Sem variável"],
  ["SAMP – mercado de energia", "Energia consumida, demanda, energia injetada e compensada, receitas e tributos, por classe de consumo", "Só nível COELBA (sem município)", "🔶 Não filtrado: energia injetada (auxiliar)"],
  ["P&D ANEEL – projetos", "Uma linha por projeto de pesquisa: título, situação, tema, fase de inovação, tipo de produto, custo previsto e auditado", "99 projetos COELBA, 2009–2026", "✅ Dataset inteiro é CT&I"],
  ["DEC/FEC por conjunto", "Horas (DEC) e número (FEC) de interrupções por consumidor no ano, com o limite regulatório", "211 conjuntos, 2025", "⬜ Sem variável"],
  ["DEC/FEC por município", "Média dos conjuntos que atendem o município, ponderada pelo nº de consumidores", "415 municípios, 2025", "⬜ Sem variável"],
  ["INDQUAL – de-para", "Quais conjuntos elétricos atendem cada município", "211 conjuntos ativos, 415 municípios", "⬜ Sem variável"],
], [1.9, 4, 1.8, 1.7], { cor: corFiltro }));
C.push(h3("Variáveis categóricas e relação com CT&I"));
C.push(tabela(["Variável (dataset)", "Valores na Bahia", "Uso em CT&I"], [
  ["SigTipoGeracao (SIGA)", "EOL eólica (520) · UFV solar (506) · UTE térmica (107) · CGH (13) · UHE (10) · PCH (7)", "Auxiliar: EOL e UFV = transição energética"],
  ["NomFonteCombustivel (SIGA)", "13 fontes: vento, radiação solar, diesel, potencial hidráulico, gás natural, licor negro, bagaço de cana…", "Auxiliar"],
  ["DscFaseUsina (SIGA)", "Operação (677) · Construção não iniciada (474) · Construção (12)", "Recorte: capacidade atual x futura"],
  ["SigFasInovacaoProjeto (P&D)", "DE Desenvolvimento experimental (47) · PA Pesquisa aplicada (24) · CS Cabeça de série (19) · LP Lote pioneiro (5) · IM Inserção no mercado (4)", "**Maturidade da inovação**"],
  ["SigTemaProjeto (P&D)", "10 temas: Outros, Medição e perdas, Qualidade, Segurança, Supervisão e controle, Operação, Planejamento, Fontes alternativas, Meio ambiente, Eficiência", "Tema tecnológico"],
  ["SigTipoProdutoProjeto (P&D)", "Metodologia (32) · Sistema (22) · Componente/material (18) · Conceito (15) · Software (10) · Sensor (2)", "Tipo de entregável"],
  ["IdcSituacaoProjeto (P&D)", "Concluído (40) · Cancelado (28) · Em atraso (25) · Em execução (6)", "Execução"],
  ["DscClasseConsumoMercado (SAMP)", "Residencial, Industrial, Comercial, Rural, Poder público, Serviço público, Consumo próprio…", "Auxiliar: Industrial"],
  ["SigIndicador (DEC/FEC)", "DEC, FEC e mais de 20 desdobramentos por causa (programada, emergência, origem externa…)", "Contexto"],
], [2.3, 4.7, 2]));
C.push(h3("Números da Bahia"));
C.push(bl("**11,8 GW eólicos e 3,1 GW solares** em operação; 74 municípios com parques solares ou eólicos."));
C.push(bl("**P&D ANEEL: 99 projetos, R$ 390 milhões previstos**, R$ 199 milhões já auditados."));
C.push(bl("**Qualidade da rede 2025:** DEC médio de 9,4 horas e FEC de 3,8 interrupções por consumidor. Salvador tem 4,6 h; Canavieiras, Cairu e Itacaré passam de 31 h. 46 dos 211 conjuntos ficaram acima do limite de DEC."));
C.push(nota("Cuidados: (1) o P&D e o SAMP não têm município; (2) no SIGA o município é texto; (3) o DEC/FEC deve vir do arquivo ZIP oficial, porque a consulta via API está desatualizada e sem vários meses; (4) Jandaíra e Rio Real são atendidos pela Sulgipe e ficam fora do DEC/FEC da COELBA."));

// BNDES
C.push(h2("3.4 BNDES — Financiamento à inovação"));
C.push(p("**Papel:** mostra quanto crédito do banco de desenvolvimento chega a cada município, e quanto dele é voltado à inovação, à engenharia, ao software e à modernização tecnológica das empresas."));
C.push(h3("O que cada dataset retorna"));
C.push(tabela(["Dataset", "O que retorna", "Cobertura", "Filtro CT&I"], [
  ["Operações não automáticas", "Uma linha por contrato direto ou indireto não automático: cliente, município, valores contratado e desembolsado, produto, instrumento, flag de inovação, setor, porte e descrição do projeto", "1.104 operações", "🏷️ Classificado (cti_nivel)"],
  ["Operações indiretas automáticas", "Uma linha por operação repassada por bancos credenciados (FINAME, BNDES Automático): mesmos campos, sem descrição do projeto", "79.860 operações", "🏷️ Classificado (cti_nivel)"],
  ["CT&I por município e ano", "Nº de operações e valores das operações classificadas como CT&I, por município e ano", "Completo: 314 operações, 76 municípios, 2002–2026", "✅ Filtrado"],
], [2, 4.4, 1.6, 1.6], { cor: corFiltro }));
C.push(h3("Variáveis categóricas e relação com CT&I"));
C.push(tabela(["Variável", "Valores na Bahia", "Uso em CT&I"], [
  ["inovacao", "SIM (300 operações, R$ 767 mi) · NÃO", "**Principal: flag oficial**"],
  ["instrumento_financeiro", "Mais de 140 linhas. CT&I: BNDES Inovação, PSI Inovação, Mais Inovação, FUNTEC, FUNTTEL, Prosoft, Proengenharia, Prodesign, Difusores de Tecnologia, Máquinas 4.0, Inovagro, FUST…", "**Principal**"],
  ["fonte_de_recurso_desembolsos", "51 fontes. CT&I: FUNTTEL e FUST (fundos setoriais de tecnologia)", "**Principal**"],
  ["subsetor_cnae", "1.091 códigos. Tecnológicos: farmacêutica, eletrônicos, telecomunicações, TI, serviços de informação, P&D", "Auxiliar (revisar)"],
  ["descricao_do_projeto", "Texto livre (só nas não automáticas): busca por INOVA, PESQUISA, P&D, TECNOLOGIA, SOFTWARE…", "Auxiliar (revisar)"],
  ["area_operacional", "10 áreas, incluindo \"Desenvolvimento Produtivo e Inovação\"", "Não usar: ampla demais"],
  ["porte_do_cliente", "Micro (30.754) · Pequena (20.761) · Média (17.117) · Grande (12.332)", "Recorte"],
  ["forma_de_apoio", "Direta (916) · Indireta (80.048)", "Recorte"],
  ["modalidade_de_apoio", "Reembolsável (80.905) · Não reembolsável (59)", "Recorte"],
  ["produto", "FINAME, FINEM, BNDES Automático, Project Finance, Não Reembolsável…", "Recorte"],
], [2.3, 4.8, 1.9]));
C.push(h3("Regra de CT&I aplicada"));
C.push(p("Uma operação é CT&I quando atende a **pelo menos uma** destas condições: (1) flag de inovação = SIM; (2) instrumento financeiro está na lista de linhas de inovação; (3) a fonte de recurso é FUNTTEL, FUST ou FNDCT. Operações de setores tecnológicos ou com palavras-chave na descrição ficam como \"auxiliar\", para revisão manual. Cada operação recebe a coluna com o motivo da classificação."));
C.push(h3("Números da Bahia (2002–2026)"));
C.push(bl("**80.964 operações**, R$ 81,5 bilhões desembolsados; 416 dos 417 municípios receberam pelo menos uma."));
C.push(bl("**CT&I: 314 operações, R$ 851 milhões (1,0% do total)**, em 76 municípios. Camaçari lidera (R$ 486 mi). 271 das 314 operações são de 2024–2026."));
C.push(nota("Cuidados: (1) o flag de inovação sozinho não basta: FUST e Difusores de Tecnologia vêm com \"NÃO\"; (2) o programa Mais Inovação (245 operações) é na prática compra de máquinas, com metade dos tomadores na construção civil, e deve ser separado de P&D; (3) 267 operações diretas (R$ 22,8 bi, cerca de 40% do valor direto) não têm município; (4) os textos vêm com espaços extras e a UF da base automática é \" BA\"."));

// SICONFI
C.push(h2("3.5 SICONFI / Tesouro Nacional — Gasto público municipal em CT&I"));
C.push(p("**Papel:** mostra quanto cada prefeitura gasta em Ciência e Tecnologia, pela classificação oficial do orçamento (Função 19). Também permite ver o gasto com tecnologia da informação da própria prefeitura e com ensino superior."));
C.push(h3("O que cada dataset retorna"));
C.push(tabela(["Dataset", "O que retorna", "Cobertura", "Filtro CT&I"], [
  ["DCA Anexo I-C (receita)", "Receitas brutas realizadas e deduções, por conta de receita", "Salvador 2024 (amostra)", "⬜ Sem variável"],
  ["RREO Anexo 02 (despesa por função)", "Dotação, empenho e liquidação por função e subfunção, no bimestre", "Salvador 2025, 6º bimestre", "✅ Filtrado por texto da conta"],
  ["DCA Anexo I-E (despesa por função)", "Despesa liquidada de cada município: total, Função 19 (CT&I), subfunções 571/572/573 e 126 (TI), por habitante e em % da despesa", "415 municípios, 2024", "🏷️ Classificado em colunas"],
], [2.2, 4.3, 1.6, 1.7], { cor: corFiltro }));
C.push(h3("Variáveis categóricas e relação com CT&I"));
C.push(tabela(["Conta do orçamento", "Municípios BA com valor (2024)", "Liquidado BA 2024", "Uso em CT&I"], [
  ["19 – Ciência e Tecnologia (função inteira)", "8", "R$ 126,5 mi", "**Principal**"],
  ["19.572 – Desenvolvimento Tecnológico e Engenharia", "1 (Salvador)", "R$ 49,8 mi", "Principal"],
  ["19.573 – Difusão do Conhecimento Científico e Tecnológico", "3", "R$ 0,35 mi", "Principal"],
  ["xx.126 – Tecnologia da Informação", "39", "R$ 99,1 mi", "Auxiliar (TI da prefeitura)"],
  ["12.364 Ensino Superior / 12.363 Ensino Profissional", "75 / 8", "R$ 47,3 mi / R$ 1,3 mi", "Auxiliar"],
  ["24 – Comunicações", "17", "R$ 124,6 mi", "Auxiliar"],
], [3.6, 1.8, 1.7, 1.9]));
C.push(h3("Números da Bahia (2024)"));
C.push(bl("**415 de 417 municípios** entregaram as contas anuais de 2024."));
C.push(bl("**Só 8 gastaram na Função 19:** Salvador (R$ 120,1 mi), Luís Eduardo Magalhães (R$ 4,7 mi), Mucuri (R$ 1,2 mi), Monte Santo, Itacaré, Lauro de Freitas, Ibipitanga e Madre de Deus."));
C.push(bl("Salvador gasta R$ 46,76 por habitante em CT&I, cerca de 1% da sua despesa total."));
C.push(nota("Cuidados: (1) usar o DCA, não o RREO: no RREO a linha da subfunção não diz a qual função pertence; (2) o DCA agrupa subfunções pequenas em \"Demais Subfunções\", por isso o filtro principal deve ser a Função 19 inteira; (3) a classificação é declarada pelo próprio município."));

// ANATEL
C.push(h2("3.6 ANATEL — Conectividade e infraestrutura digital"));
C.push(p("**Papel:** mostra a infraestrutura de telecomunicações de cada município, abrangendo banda larga fixa (densidade domiciliar, fibra óptica, velocidade) e conectividade móvel 4G (% de território e % de população coberta). É a condição habilitadora para startups, conectividade rural, teletrabalho, ensino digital e serviços públicos em nuvem."));
C.push(h3("O que cada dataset retorna"));
C.push(tabela(["Dataset", "O que retorna", "Cobertura", "Filtro CT&I"], [
  ["Densidade de banda larga fixa", "Acessos por 100 domicílios, por município e mês", "417 municípios (com lacunas, ver nota)", "⬜ Sem variável"],
  ["Acessos de banda larga fixa", "Acessos por prestadora, município, tecnologia, meio de acesso, faixa de velocidade e mês", "417 municípios, jan–ago/2026", "🔶 Não filtrado: fibra e alta velocidade"],
  ["Cobertura móvel (SMP 4G)", "Cobertura 4G por município: % de território coberto, % de moradores e % de domicílios cobertos", "417 municípios da Bahia", "⬜ Sem variável"],
], [2.2, 4, 1.9, 1.7], { cor: corFiltro }));
C.push(h3("Variáveis categóricas e relação com CT&I"));
C.push(tabela(["Variável", "Valores na Bahia (acessos, ago/2026)", "Uso em CT&I"], [
  ["Meio de Acesso", "Fibra 2,08 mi (88,8%) · Cabo coaxial 107 mil · Rádio 81 mil · Satélite 41 mil · Cabo metálico 35 mil", "Auxiliar: Fibra"],
  ["Tecnologia", "FTTH 1,88 mi · Ethernet 202 mil · HFC 99 mil · Wi-Fi 80 mil · VSAT 40 mil · FTTB 8 mil… (21 valores)", "Auxiliar: FTTH e FTTB"],
  ["Faixa de Velocidade", "> 34 Mbps 2,18 mi (92,9%) · 12–34 Mbps · 2–12 Mbps · 512 kbps–2 Mbps · até 512 kbps", "Auxiliar: > 34 Mbps"],
  ["Porte da Prestadora", "Pequeno porte 1,71 mi (72,8%) · Grande porte 636 mil", "Recorte"],
  ["Tipo de Produto / Tipo de Pessoa", "Internet, Linha dedicada, M2M · Pessoa física, Pessoa jurídica", "Recorte"],
], [2.2, 5, 1.8]));
C.push(h3("Cobertura Móvel 4G — Território vs. População (Recurso 1449ea53-fe84-4547-8ac8-f6a465995958)"));
C.push(p("O dataset de cobertura móvel 4G da Anatel traz duas métricas fundamentais para o diagnóstico de conectividade territorial da SECTI:"));
C.push(bl("**% Moradores Cobertos (média BA: 73,9%):** mede o alcance populacional. Lauro de Freitas, Madre de Deus e Itaparica têm 100%; Salvador atinge 99,99%; Feira de Santana tem 97,3%; Vitória da Conquista tem 91,5%. Os municípios com menor cobertura atendem apenas cerca de 30% da população (Jucuruçu 29,7%, Baianópolis 30,0%, Ribeirão do Largo 30,9%)."));
C.push(bl("**% Área Coberta (média BA: 35,4%):** mede a proporção física do município com sinal 4G. Apenas municípios de pequeno porte territorial ou altamente conurbados atingem ampla cobertura de área (Lauro de Freitas 100%, Muritiba 99,6%, Itaparica 98,9%). Municípios com grande extensão territorial no Semiárido e Oeste concentram o sinal na sede urbana e possuem menos de 5% de área coberta (Barra 3,1%, Santa Rita de Cássia 3,7%, Pilão Arcado 3,8%)."));
C.push(p("**Relevância para a SECTI:** Essa discrepância demonstra que a cobertura móvel comercial atende predominantemente os núcleos urbanos, deixando vazios nas zonas rurais e eixos agropecuários. Esse diagnóstico subsidia políticas de interiorização da inovação, redes comunitárias e programas de conectividade para escolas rurais."));
C.push(nota("Cuidado: a série publicada de densidade de banda larga fixa está vazia em 2023 e 2024, só tem dezembro em 2025 e traz valores incorretos entre dez/2025 e mar/2026. A partir de abr/2026 os valores voltam a ser coerentes (Salvador ≈ 21 acessos por 100 domicílios). Para o valor atual, usar a série a partir de abr/2026."));

// 4. Matriz de filtros
C.push(h1("4. Matriz consolidada de filtros de CT&I"));
C.push(p("A tabela abaixo reúne, em um só lugar, os filtros de CT&I recomendados para o painel. " + "A versão completa, com justificativas, está " + (EXCEL ? "na aba Filtros_CTI da planilha." : "em categorias_cti/filtros_cti_consolidado.csv.")));
C.push(tabela(["Fonte", "Campo", "Valores que entram", "Nível"], [
  ["INEP", "CO_CINE_AREA_GERAL", "05, 06, 07", "Principal (núcleo STEM)"],
  ["INEP", "CO_CINE_AREA_GERAL", "08, 09", "Ampliado"],
  ["INEP", "CO_CURSO", "Lista SECTI de 642 cursos (pendente)", "Principal (quando disponível)"],
  ["INEP", "TP_GRAU_ACADEMICO / TP_ORGANIZACAO_ACADEMICA", "Tecnológico / IF e CEFET", "Auxiliar"],
  ["BNDES", "inovacao", "SIM", "Principal"],
  ["BNDES", "instrumento_financeiro", "18 linhas de inovação, P&D, software, engenharia e difusão tecnológica", "Principal"],
  ["BNDES", "fonte_de_recurso_desembolsos", "FUNTTEL, FUST, FNDCT", "Principal"],
  ["BNDES", "subsetor_cnae / descricao_do_projeto", "Setores tecnológicos / palavras-chave", "Auxiliar (revisar)"],
  ["SICONFI", "Conta do DCA Anexo I-E", "Função 19 – Ciência e Tecnologia", "Principal"],
  ["SICONFI", "Conta do DCA Anexo I-E", "Subfunção 126 (TI), 363/364 (ensino), Função 24", "Auxiliar"],
  ["ANEEL", "P&D ANEEL", "Dataset inteiro", "Principal"],
  ["ANEEL", "SigTipoGeracao", "EOL, UFV", "Auxiliar"],
  ["ANATEL", "Meio de Acesso / Faixa de Velocidade", "Fibra / > 34 Mbps", "Auxiliar"],
  ["IBGE", "—", "Sem filtro (denominadores)", "—"],
], [1.2, 3, 3.3, 2]));

// 5. Limitações e próximos passos
C.push(h1("5. Limitações e próximos passos"));
C.push(h2("5.1 Limitações conhecidas"));
[
  "**Dados sem município:** P&D ANEEL, mercado de energia (SAMP) e cerca de 40% do crédito direto do BNDES não podem ser atribuídos a um município sem uma regra adicional.",
  "**Correspondência N:N na rede elétrica:** um conjunto elétrico atende vários municípios e um município pode ter vários conjuntos. O DEC/FEC municipal é uma média ponderada aproximada.",
  "**EAD no INEP:** vagas e inscritos de cursos a distância não são calculados por município.",
  "**Docentes:** a titulação vem por instituição, sem o município onde o professor atua.",
  "**ANATEL:** a série histórica de densidade tem lacunas em 2023–2025.",
].forEach(t => C.push(bl(t)));
C.push(h2("5.2 Próximos passos"));
C.push(tabela(["#", "Ação", "Responsável sugerido"], [
  ["1", "Enviar a lista SECTI de 642 cursos de CT&I para substituir ou complementar o filtro por área CINE", "SECTI"],
  ["2", "Definir se as operações do BNDES sem município entram no painel (e com qual regra de rateio)", "SECTI + equipe técnica"],
  ["3", "Enviar a tabela município → Território de Identidade (27 territórios) para as agregações territoriais", "SECTI / SEPLAN"],
  ["4", "Separar o programa BNDES Mais Inovação em \"difusão tecnológica\" e manter \"P&D e inovação\" como núcleo", "Equipe técnica"],
  ["5", "Recalcular a densidade da ANATEL de 2023–2025 só se o painel for mostrar série histórica", "Equipe técnica"],
], [0.4, 6.4, 2]));

// Glossário
C.push(h1("Anexo — Glossário"));
C.push(tabela(["Termo", "Significado"], [
  ["CT&I", "Ciência, Tecnologia e Inovação"],
  ["STEM", "Ciências, tecnologia, engenharia e matemática (do inglês Science, Technology, Engineering and Mathematics)"],
  ["CINE", "Classificação Internacional Normalizada da Educação, usada pelo INEP para classificar a área de cada curso"],
  ["IES", "Instituição de Ensino Superior"],
  ["EAD", "Educação a distância"],
  ["DCA", "Declaração de Contas Anuais, enviada pelos municípios ao Tesouro Nacional"],
  ["RREO", "Relatório Resumido da Execução Orçamentária (bimestral)"],
  ["Despesa liquidada", "Despesa cujo serviço ou produto já foi entregue e atestado; a fase mais adequada para medir gasto efetivo"],
  ["Função 19", "Classificação orçamentária oficial para Ciência e Tecnologia (Portaria MOG 42/1999)"],
  ["DEC", "Duração Equivalente de Interrupção por Unidade Consumidora: horas sem energia por consumidor no período"],
  ["FEC", "Frequência Equivalente de Interrupção por Unidade Consumidora: número de interrupções por consumidor no período"],
  ["Conjunto elétrico", "Área da rede da distribuidora usada pela ANEEL para apurar DEC e FEC"],
  ["SIGA", "Sistema de Informações de Geração da ANEEL (cadastro de usinas)"],
  ["SCM", "Serviço de Comunicação Multimídia (banda larga fixa)"],
  ["SMP", "Serviço Móvel Pessoal (telefonia celular e internet móvel: 3G, 4G, 5G)"],
  ["FTTH", "Fibra óptica até a casa do usuário"],
  ["FUNTTEL / FUST", "Fundos setoriais de telecomunicações usados para financiar tecnologia"],
  ["Código IBGE", "Código de 7 dígitos que identifica cada município; chave de cruzamento entre as fontes"],
], [2, 7]));

// ---------- documento
const doc = new Document({
  creator: "Territórios SECTI",
  title: "Territórios SECTI — Resumo executivo das fontes de dados e filtros CT&I",
  styles: {
    default: { document: { run: { font: "Calibri", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: AZUL, font: "Calibri" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: "2E75B6", font: "Calibri" }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, color: "404040", font: "Calibri" }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [
    { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 260 } } } },
    { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 260 } } } },
  ] }] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Territórios SECTI — Resumo executivo dos dados", size: 16, color: "808080" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: ["Página ", PageNumber.CURRENT, " de ", PageNumber.TOTAL_PAGES], size: 16, color: "808080" })] })] }) },
    children: C,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log("ok", OUT); });

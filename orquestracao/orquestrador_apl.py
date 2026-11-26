"""
APLs do Observatório Brasileiro de APL (MDIC) no orquestrador comum (Python que simula o Hop). Modelo: orquestracao/sql/07_apl_modelo.sql.

O gov.br responde com captcha a qualquer cliente automatizado, então NÃO há download: uma pessoa baixa a planilha no botão
"Baixe a Planilha de APLs" e a deixa numa pasta fora do repositório. O Hop, na VPS, vigia essa pasta.

Passo 0   sha256 do arquivo x etl.checkpoint (metodo hash_corpo). Igual = 'sem_mudanca', a planilha nem é lida.
Passo 1   lê o XLSX só com a stdlib (é um ZIP de XML), valida o layout, fica com Estado = BA, descarta dados pessoais e
          converte nomes de município em codigo_ibge: nome normalizado exato > meta/apl_municipio_de_para.csv > aproximado
          (difflib, com folga sobre o 2º colocado). Nome sem par = carga abortada.
Passo 2   MERGE apl.apl e apl.apl_municipio com escopo uf = 'BA' e trava de exclusão em 20%.
Passo 3   etl.finalizar(): checkpoint só avança se a carga terminou bem.

Uso:  python orquestracao/orquestrador_apl.py --xlsx "C:/.../Lista APLs_outubro2022_publico.xlsx" [--verificar] [--forcar]
"""
import csv, datetime as dt, difflib, hashlib, json, re, sys, unicodedata, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
from orquestrador_simulado import dsn, OPCOES_AUDITORIA, RAIZ, API, copiar, executar, checkpoint, get, log
import psycopg

RID = "mdic_apl_ba"
UF = "BA"
URL = "https://www.gov.br/empresas-e-negocios/pt-br/portais-desconhecidos/observatorioapl/apls-brasileiros"
DE_PARA = RAIZ / "orquestracao" / "meta" / "apl_municipio_de_para.csv"
LIMITE_EXCLUSAO_PCT = 20
SIMILARIDADE_MIN = 0.80      # cruzamento aproximado (ver aproximado())
MARGEM_MIN = 0.10
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
# cabeçalho da planilha -> coluna de apl.apl. Gestor (nome, e-mail, telefone), endereço, CEP e "Fonte da Informação"
# (traz nomes de pessoas) ficam de fora de propósito: dado pessoal não entra no banco nem no backup versionado.
COLUNAS = {
    "Nome do APL*": "nome_apl", "Setor Produtivo*": "setor_produtivo", "CNAES*": "cnaes", "CNPJ do APL": "cnpj",
    "Site ou Mídia Social": "site", "Número de Empresas (ou Produtores)*": "qt_empresas",
    "Número de Funcionários (ou Produtores)*": "qt_funcionarios", "Produtos e Serviços*": "produtos_servicos",
    "Especialização": "especializacao", "Indicação Geográfica - IG": "indicacao_geografica",
    "Plano de Desenvolvimento*": "plano_desenvolvimento", "Instituições de Ensino": "instituicoes_ensino",
    "Instituições de Capacitação": "instituicoes_capacitacao", "Instituições de Financiamento": "instituicoes_financiamento",
    "Instituições de Promoção Comercial": "instituicoes_promocao", "Participação em Projetos": "projetos",
    "Participação em Redes Setoriais": "redes_setoriais", "Instituições que validam as informações": "instituicoes_validacao",
    "Data última atualização": "data_atualizacao_fonte",
}
OUTRAS = ["Estado*", "Cidade Polo*", "Municípios que compõem o APL*"]


def espacos(s):
    return " ".join((s or "").split())


def chave_nome(s):
    """Chave de cruzamento: minúsculo, sem acento e só letras/números ("Santa Luz" = "Santaluz", "Olho D'Água" = "olhodagua")."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalnum())


def ler_xlsx(caminho):
    """Primeira planilha como lista de dicts {cabeçalho: texto}. Só stdlib: XLSX é ZIP de XML."""
    z = zipfile.ZipFile(caminho)
    ss = [ "".join(t.text or "" for t in si.iter(M + "t")) for si in ET.fromstring(z.read("xl/sharedStrings.xml"))]
    linhas = []
    for r in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).find(M + "sheetData"):
        d = {}
        for c in r:
            letra = "".join(ch for ch in c.get("r") if ch.isalpha())
            if c.get("t") == "inlineStr":
                d[letra] = "".join(t.text or "" for t in c.iter(M + "t"))
            elif (v := c.find(M + "v")) is not None:
                d[letra] = ss[int(v.text)] if c.get("t") == "s" else v.text
        linhas.append(d)
    cab = {k: espacos(v) for k, v in linhas[0].items()}
    falta = [c for c in [*COLUNAS, *OUTRAS] if c not in cab.values()]
    if falta:
        raise ValueError(f"o layout da planilha mudou; colunas ausentes: {falta}. Carga abortada")
    return [{cab[k]: v for k, v in d.items() if k in cab} for d in linhas[1:] if d]


def texto(v):
    v = espacos(v)
    return None if v in ("", "N/A", "Planilha anterior sem informação") else v


def inteiro(v, ruins):
    v = texto(v)
    if v is None:
        return None
    try:
        return int(float(v))
    except ValueError:
        ruins.append(v); return None


def data_excel(v):
    v = texto(v)
    return dt.date(1899, 12, 30) + dt.timedelta(days=int(float(v))) if v and v.replace(".", "").isdigit() else None


def aproximado(chave, municipios):
    """Município mais parecido (difflib) se for claramente o melhor: similaridade >= SIMILARIDADE_MIN e folga >= MARGEM_MIN sobre o 2º.
    Medido em 26/11: os 15 erros de digitação da planilha passam; "Capela" (→ Caravelas, errado) e "Tancredo Neves" não passam.
    Há municípios reais quase iguais (Cristópolis × Crisópolis, 0,95): por isso o nome exato vem sempre antes e a folga é exigida."""
    r = sorted(((difflib.SequenceMatcher(None, chave, k).ratio(), k) for k in municipios), reverse=True)[:2]
    (s1, k1), (s2, _) = r
    return municipios[k1] if s1 >= SIMILARIDADE_MIN and s1 - s2 >= MARGEM_MIN else None


def com_uf(nome):
    """APL interestadual escreve "Petrolina - PE" (às vezes com ponto final). Devolve (nome, UF ou None)."""
    m = re.match(r"^(.*?)\s+-\s+([A-Z]{2})\.?$", espacos(nome))
    return (m[1], m[2]) if m else (espacos(nome).rstrip("."), None)


def polo_fora(nome, uf, cache={}):
    """Código IBGE de um polo fora da BA (APL interestadual mantém a sede original), pela API de localidades do IBGE."""
    if uf not in cache:
        cache[uf] = {chave_nome(m["nome"]): m["id"] for m in get(f"{API}/v1/localidades/estados/{uf}/municipios").json()}
    return cache[uf].get(chave_nome(nome))


def montar(linhas, municipios):
    """Passo 1: (apls, pares). Nome -> codigo_ibge em 3 níveis: exato (normalizado) > de-para (decisão humana) > aproximado.
    Nome que nenhum nível resolve aborta a carga. Cada par guarda o nível usado (metodo_cruzamento) para a curadoria revisar."""
    de_para = {chave_nome(l["nome_planilha"]): int(l["codigo_ibge"]) if l["codigo_ibge"].strip() else 0   # vazio = ignorar de propósito
               for l in csv.DictReader(open(DE_PARA, encoding="utf-8"), delimiter=";")}

    def resolver(nome):
        k = chave_nome(nome)
        if k in municipios:
            return municipios[k], "exato"
        if k in de_para:
            return de_para[k], "de_para"
        cod = aproximado(k, municipios)
        return (cod, "aproximado") if cod else (None, None)

    apls, pares, sem_par, ruins, aprox = {}, {}, set(), [], set()
    for l in linhas:
        estados = [e.strip() for e in espacos(l.get("Estado*")).split(";")]
        if UF not in estados:
            continue      # APL interestadual com a BA entra: sede original e só os municípios baianos
        a = {col: texto(l.get(cab)) for cab, col in COLUNAS.items()}
        a["uf"], a["uf_fonte"] = UF, "; ".join(estados)
        if a["nome_apl"] in (None,) or (UF, a["nome_apl"]) in apls:
            raise ValueError(f"APL sem nome ou repetido na planilha: {a['nome_apl']!r}. Carga abortada")
        a["qt_empresas"] = inteiro(a["qt_empresas"], ruins)
        a["qt_funcionarios"] = inteiro(a["qt_funcionarios"], ruins)
        a["plano_desenvolvimento"] = {"Sim": True, "Não": False}.get(a["plano_desenvolvimento"])
        a["data_atualizacao_fonte"] = data_excel(l.get("Data última atualização"))
        polo, uf_polo = com_uf(l.get("Cidade Polo*") or "")
        polo = texto(polo)
        a["codigo_ibge_polo"] = (polo_fora(polo, uf_polo) if uf_polo not in (None, UF) else resolver(polo)[0]) if polo else None
        if polo and not a["codigo_ibge_polo"]:
            sem_par.add(polo)
        for nome in (l.get("Municípios que compõem o APL*") or "").replace(",", ";").split(";"):
            nome, uf_mun = com_uf(nome)
            if uf_mun not in (None, UF):
                continue  # município de outra UF num APL interestadual
            if texto(nome):
                cod, metodo = resolver(nome)
                if cod == 0:
                    log(RID, f"ignorado pelo de-para: {espacos(nome)!r} ({a['nome_apl']})")
                elif cod:
                    # a fonte repete nomes ("Igaci; Igaci"): fica a 1ª grafia
                    pares.setdefault((a["nome_apl"], cod), (espacos(nome), metodo))
                    if metodo == "aproximado":
                        aprox.add((espacos(nome), cod))
                else:
                    sem_par.add(espacos(nome))
        apls[(UF, a["nome_apl"])] = a
    if sem_par:
        raise ValueError(f"municípios sem codigo_ibge (incluir em {DE_PARA.name}): {sorted(sem_par)}. Carga abortada")
    if not apls:
        raise ValueError(f"nenhum APL com Estado = {UF} na planilha")
    if aprox:
        log(RID, f"passo 1: {len(aprox)} nomes casados por aproximação (revisar): {sorted(aprox)}")
    return list(apls.values()), sorted((*k, *v) for k, v in pares.items()), ruins


def carregar(cur, exe, linhas, data_fonte):
    cur.execute("SELECT codigo_ibge, municipio FROM ibge.municipio")
    nomes = cur.fetchall()
    municipios = {chave_nome(n): c for c, n in nomes}
    if len(municipios) != len(nomes):
        raise ValueError("dois municípios do IBGE ficaram com a mesma chave normalizada; o cruzamento por nome deixou de valer")
    if not municipios:
        raise ValueError("ibge.municipio está vazia: carregue o IBGE antes (as FKs do APL dependem dela)")
    apls, pares, ruins = montar(linhas, municipios)
    log(RID, f"passo 1: {len(apls)} APLs da BA, {len(pares)} pares APL x município"
             + (f" | {len(ruins)} quantidades não numéricas viraram NULL: {ruins[:5]}" if ruins else ""))
    cols = ["uf", *COLUNAS.values(), "codigo_ibge_polo", "uf_fonte"]
    copiar(cur, "stg.apl", cols + ["modificado_fonte_em"], [[a[c] for c in cols] + [data_fonte] for a in apls])
    copiar(cur, "stg.apl_municipio", ["nome_apl", "codigo_ibge", "nome_municipio_fonte", "metodo_cruzamento", "modificado_fonte_em"],
           [[*p, data_fonte] for p in pares])
    det, soma = {}, [0, 0, 0]

    def merge(destino, stg, chaves, valores, escopo):
        cur.execute("SELECT * FROM etl.merge_tabela(%s, %s, %s, %s, %s, %s, %s)",
                    (exe, destino, stg, chaves, valores, escopo, LIMITE_EXCLUSAO_PCT))
        r = cur.fetchone(); det[destino] = list(r)
        for i in range(3):
            soma[i] += r[i]

    merge("apl.apl", "stg.apl", ["uf", "nome_apl"], cols[2:], f"{{a}}.uf = '{UF}'")
    # id_apl nasce no apl.apl (identity); o par recebe o id pelo nome, já com os APLs novos inseridos
    cur.execute("UPDATE stg.apl_municipio s SET id_apl = a.id_apl FROM apl.apl a WHERE a.uf = %s AND a.nome_apl = s.nome_apl", (UF,))
    merge("apl.apl_municipio", "stg.apl_municipio", ["id_apl", "codigo_ibge"], ["nome_municipio_fonte", "metodo_cruzamento"],
          f"{{a}}.id_apl IN (SELECT id_apl FROM apl.apl WHERE uf = '{UF}')")
    cur.execute("UPDATE etl.execucao SET escopo = escopo || %s::jsonb WHERE id = %s",
                (json.dumps({"apls": len(apls), "pares": len(pares), "tabelas": det}), exe))
    log(RID, "passo 2: " + " | ".join(f"{k} +{v[0]} ~{v[1]} -{v[2]}" for k, v in det.items()))
    return tuple(soma)


if __name__ == "__main__":
    if "--xlsx" not in sys.argv:
        sys.exit(f"informe a planilha baixada em {URL}: --xlsx <arquivo>")
    xlsx = Path(sys.argv[sys.argv.index("--xlsx") + 1])
    corpo = xlsx.read_bytes()
    digital = {"sha256": hashlib.sha256(corpo).hexdigest(), "arquivo": xlsx.name, "tamanho": len(corpo)}
    data_fonte = dt.date.fromtimestamp(xlsx.stat().st_mtime)      # quando a pessoa baixou: a planilha não traz data de publicação
    with psycopg.connect(dsn(), options=OPCOES_AUDITORIA.replace("orquestrador_simulado", "orquestrador_apl")) as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO etl.recurso (id, fonte, modo, metodo, url, tabela_destino, frequencia, parametros)
                           VALUES (%s, 'MDIC', 'ELT_ARQUIVO', 'hash_corpo', %s, 'apl.apl', 'mensal', %s)
                           ON CONFLICT (id) DO UPDATE SET url = EXCLUDED.url, parametros = EXCLUDED.parametros""",
                        (RID, URL, json.dumps({"uf": UF, "download": "manual (captcha no gov.br)"})))
            antes = checkpoint(cur, RID)
            conn.commit()
        mudou = antes is None or antes.get("sha256") != digital["sha256"]
        log(RID, f"passo 0: {xlsx.name} sha256 {digital['sha256'][:12]} | "
                 + ("CARGA INICIAL" if antes is None else "MUDOU" if mudou else "SEM MUDANÇA"))
        if "--verificar" in sys.argv:
            sys.exit(0)
        if not mudou and "--forcar" not in sys.argv:
            executar(conn, RID, digital, None, None); sys.exit(0)
        executar(conn, RID, digital, {"uf": UF}, lambda cur, exe: carregar(cur, exe, ler_xlsx(xlsx), data_fonte))

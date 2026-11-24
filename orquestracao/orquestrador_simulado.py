"""
Orquestrador que SIMULA o workflow do Apache Hop (PLANEJAMENTO_IBGE.md §7A) com dados reais do IBGE.
Na VPS, cada passo vira uma action/pipeline do Hop; a lógica e as funções SQL são as mesmas.

  workflow principal
   ├─ meta      metadados (/metadados, /periodos, calendário, layout do FTP) -> schema meta
   └─ para cada recurso:
       ├─ Passo 0  níveis 1+2: identificador barato (modificacao por período, ETag, hash) x etl.checkpoint
       │           nada mudou? registra 'sem_mudanca' e segue (nenhum dado baixado)
       ├─ Passo 1  baixa SÓ o escopo alterado -> stg.*
       ├─ Passo 2  nível 3: MERGE por chave + _hash (INSERT/UPDATE/DELETE pontuais, histórico e exclusões)
       └─ Passo 3  etl.finalizar(): checkpoint só avança se a carga deu certo

  Recursos: ibge_6579_populacao, ibge_4709_censo (API, por período) · ibge_pib_municipal (FTP, ETag)
            ibge_municipio (localidades + malhas/metadados + tipologias do FTP) · ibge_malha (GeoJSON)

Uso:
  py -3.12 orquestracao/orquestrador_simulado.py             rodada normal
  py -3.12 orquestracao/orquestrador_simulado.py --simular   cenário de revisão (ver preparar_simulacao)

Conexão: variável PG_DSN, ou padrão local (porta 5433, senha em pg-portatil/pgpass.txt).
"""
import csv, hashlib, io, json, os, sys, time, zipfile, datetime as dt
from email.utils import parsedate_to_datetime
from pathlib import Path
import requests, psycopg

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "orquestracao" / "cache"
LAYOUT_CSV = RAIZ / "orquestracao" / "meta" / "layout_pib_municipios_2010_2023.csv"
API = "https://servicodados.ibge.gov.br/api"
AGR = f"{API}/v3/agregados"
U_LOC = f"{API}/v1/localidades/estados/29/municipios"
U_MALHA_META = f"{API}/v3/malhas/estados/29/metadados?intrarregiao=municipio"
QUALIDADE_MALHA = "minima"
U_MALHA = f"{API}/v3/malhas/estados/29?intrarregiao=municipio&formato=application/vnd.geo+json&qualidade={QUALIDADE_MALHA}"
FTP_EDICAO = "2022_2023"
U_FTP = f"https://ftp.ibge.gov.br/Pib_Municipios/{FTP_EDICAO}/base/base_de_dados_2010_2023_txt.zip"
U_FTP_PROXIMA = "https://ftp.ibge.gov.br/Pib_Municipios/2023_2024/"
POPULACAO = [
    dict(id="ibge_6579_populacao", agregado=6579, variavel=9324, tipo="estimativa", fonte="IBGE/SIDRA 6579", produto_id=9103),
    dict(id="ibge_4709_censo", agregado=4709, variavel=93, tipo="censo", fonte="IBGE/SIDRA 4709", produto_id=22827),
]
CTX = {}  # dados compartilhados entre recursos na mesma rodada (ex.: linhas do FTP)
# Como esta rodada foi iniciada (etl.execucao.disparo): agendado (cron/Hop) | manual | forcado. O cron define ETL_DISPARO=agendado.
DISPARO = os.environ.get("ETL_DISPARO", "manual")
# Contexto de auditoria (05_auditoria.sql): toda escrita desta conexão é rotulada origem=etl. Vai na abertura da conexão para valer
# em todas as transações e não ser desfeito por rollback. Sem isto o banco rotula as escritas como direto_sql.
OPCOES_AUDITORIA = "-c app.origem=etl -c app.usuario=orquestrador_simulado"


def dsn():
    if os.environ.get("PG_DSN"):
        return os.environ["PG_DSN"]
    senha = (RAIZ / "pg-portatil" / "pgpass.txt").read_text().strip()
    return f"host=localhost port=5433 dbname=painel user=etl password={senha}"


def log(passo, msg):
    print(f"{dt.datetime.now():%H:%M:%S} [{passo}] {msg}")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def get(url, **kw):
    r = requests.get(url, timeout=300, **kw); r.raise_for_status(); return r


def copiar(cur, tabela, colunas, linhas):
    cur.execute(f"TRUNCATE {tabela}")
    with cur.copy(f"COPY {tabela} ({', '.join(colunas)}) FROM STDIN") as cp:
        for l in linhas:
            cp.write_row([json.dumps(v) if isinstance(v, (dict, list)) else v for v in l])


def registrar_recurso(cur, rid, metodo, modo, url, tabela, params):
    cur.execute("""INSERT INTO etl.recurso (id, fonte, modo, metodo, url, tabela_destino, parametros)
                   VALUES (%s, 'IBGE', %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO UPDATE SET url = EXCLUDED.url, parametros = EXCLUDED.parametros""",
                (rid, modo, metodo, url, tabela, json.dumps(params)))


def checkpoint(cur, rid):
    cur.execute("SELECT digital FROM etl.checkpoint WHERE recurso_id = %s", (rid,))
    r = cur.fetchone(); return r[0] if r else None


# ============================================================================================ META
def carregar_meta(conn):
    t = time.time()
    with conn.cursor() as cur:
        def fonte(fid, nome, pesquisa, url, periodicidade, metadados):
            h = sha(json.dumps(metadados, sort_keys=True).encode())
            cur.execute("SELECT _hash FROM meta.fonte_tabela WHERE id = %s", (fid,))
            ant = cur.fetchone()
            cur.execute("""INSERT INTO meta.fonte_tabela (id, fonte, nome, pesquisa, url, periodicidade, metadados, _hash)
                           VALUES (%s, 'IBGE', %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome, pesquisa = EXCLUDED.pesquisa,
                             url = EXCLUDED.url, periodicidade = EXCLUDED.periodicidade, metadados = EXCLUDED.metadados,
                             _hash = EXCLUDED._hash, _verificado_em = now(),
                             _modificado_em = CASE WHEN meta.fonte_tabela._hash IS DISTINCT FROM EXCLUDED._hash
                                                   THEN now() ELSE meta.fonte_tabela._modificado_em END""",
                        (fid, nome, pesquisa, url, json.dumps(periodicidade), json.dumps(metadados), h))
            if ant and ant[0] != h:
                log("meta", f"ALERTA: metadado de {fid} mudou (variável, unidade ou período novo?)")

        for ag in (6579, 4709, 5938):
            m = get(f"{AGR}/{ag}/metadados").json()
            fid = f"sidra_{ag}"
            fonte(fid, m["nome"], m["pesquisa"], m["URL"], m["periodicidade"], m)
            for v in m["variaveis"]:
                cur.execute("""INSERT INTO meta.variavel VALUES (%s, %s, %s, %s)
                               ON CONFLICT (fonte_tabela_id, variavel_id) DO UPDATE SET nome = EXCLUDED.nome, unidade = EXCLUDED.unidade""",
                            (fid, v["id"], v["nome"], v["unidade"]))
            for p in get(f"{AGR}/{ag}/periodos").json():
                cur.execute("""INSERT INTO meta.periodo VALUES (%s, %s, %s)
                               ON CONFLICT (fonte_tabela_id, periodo) DO UPDATE SET modificacao = EXCLUDED.modificacao""",
                            (fid, p["id"], dt.datetime.strptime(p["modificacao"], "%d/%m/%Y").date()))
        h = requests.head(U_FTP, timeout=60).headers
        fonte("ftp_pib_municipios", "PIB dos Municípios - base TXT", "Produto Interno Bruto dos Municípios", U_FTP,
              {"frequencia": "anual"}, {"etag": h.get("ETag"), "last_modified": h.get("Last-Modified"),
                                        "content_length": h.get("Content-Length"), "edicao": FTP_EDICAO})
        fonte("localidades", "Localidades - municípios BA", None, U_LOC, None, {"endpoint": U_LOC})
        fonte("malhas", "Malhas territoriais - municípios BA", None, U_MALHA, None, {"qualidade": QUALIDADE_MALHA})
        n_cal = 0
        for prod in (9103, 9088, 22827):
            for i in get(f"{API}/v3/calendario/{prod}?qtd=200").json()["items"]:
                cur.execute("""INSERT INTO meta.calendario VALUES (%s, %s, %s, %s, %s, %s)
                               ON CONFLICT (id) DO UPDATE SET titulo = EXCLUDED.titulo, data_divulgacao = EXCLUDED.data_divulgacao""",
                            (i["id"], i["produto_id"], i["titulo"], dt.datetime.strptime(i["data_divulgacao"], "%d/%m/%Y %H:%M:%S"),
                             i["ano_referencia_inicio"] or None, i["ano_referencia_fim"] or None))
                n_cal += 1
        with open(LAYOUT_CSV, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cur.execute("""INSERT INTO meta.layout_ftp VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                               ON CONFLICT (edicao, posicao) DO UPDATE SET coluna_destino = EXCLUDED.coluna_destino""",
                            (r["edicao"], int(r["posicao"]), int(r["tamanho"]), int(r["decimais"]) if r["decimais"] else None,
                             r["tipo"], r["campo"], r["unidade"] or None, r["coluna_destino"] or None))
        st, _ = requests.head(U_FTP_PROXIMA, timeout=60).status_code, None
        conn.commit()
    log("meta", f"metadados de 3 agregados, FTP, localidades, malhas, {n_cal} eventos do calendário, layout "
                f"({time.time() - t:.1f}s). Próxima edição do FTP ({U_FTP_PROXIMA.split('/')[-2]}): "
                f"{'PUBLICADA' if st < 400 else 'ainda não publicada'}")


# ============================================================================================ EXECUÇÃO GENÉRICA
def executar(conn, rid, digital_novo, escopo, carregar):
    """Passos 0 (decisão já tomada), 1-2 (carregar) e 3 (finalizar) com log e tratamento de erro."""
    with conn.cursor() as cur:
        cur.execute("INSERT INTO etl.execucao (recurso_id, escopo, digital_novo, disparo) VALUES (%s, %s, %s, %s) RETURNING id",
                    (rid, json.dumps(escopo), json.dumps(digital_novo), DISPARO))
        exe = cur.fetchone()[0]
        # a auditoria (audit.registrar) grava esta carga em cada evento; nível de sessão, pois o commit abaixo e os rollbacks não o desfazem
        cur.execute("SELECT set_config('app.execucao_id', %s, false)", (str(exe),)); conn.commit()
        if escopo is None:
            cur.execute("SELECT etl.finalizar(%s, 'sem_mudanca')", (exe,))
            cur.execute("UPDATE etl.checkpoint SET verificado_em = now() WHERE recurso_id = %s", (rid,))
            conn.commit(); log(rid, "passo 0: nada mudou -> nada a baixar"); return
        try:
            ins, upd, dele = carregar(cur, exe)
            cur.execute("UPDATE etl.execucao SET inseridos=%s, atualizados=%s, excluidos=%s WHERE id=%s", (ins, upd, dele, exe))
            log(rid, f"passo 2: MERGE -> {ins} inseridos, {upd} atualizados, {dele} excluídos")
            cur.execute("SELECT etl.finalizar(%s, 'ok')", (exe,)); conn.commit()
            log(rid, "passo 3: checkpoint atualizado")
        except Exception as e:
            conn.rollback()
            cur.execute("SELECT etl.finalizar(%s, 'erro', %s)", (exe, str(e)[:500])); conn.commit()
            log(rid, f"ERRO (checkpoint NÃO avançou; próxima rodada tenta de novo): {e}")


def merge(cur, exe, destino, stg, chaves, valores, escopo="true"):
    cur.execute("SELECT * FROM etl.merge_tabela(%s, %s, %s, %s, %s, %s)", (exe, destino, stg, chaves, valores, escopo))
    return cur.fetchone()


# ============================================================================================ POPULAÇÃO (API)
def recurso_populacao(conn, r):
    rid = r["id"]
    with conn.cursor() as cur:
        registrar_recurso(cur, rid, "ibge_per", "ETL_API", f"{AGR}/{r['agregado']}", "ibge.populacao",
                          {"fonte_tabela": f"sidra_{r['agregado']}", "produto_id": r["produto_id"]})
        agora = {p["id"]: p["modificacao"] for p in get(f"{AGR}/{r['agregado']}/periodos").json()}
        antes = checkpoint(cur, rid) or {}
    alterados = sorted(p for p in agora if antes.get(p) != agora[p])
    removidos = sorted(p for p in antes if p not in agora)
    escopo = alterados + removidos
    if escopo:
        log(rid, f"passo 0: {len(alterados)} período(s) alterado(s) {alterados[:6]}{'…' if len(alterados) > 6 else ''}"
                 f"{f'; removidos {removidos}' if removidos else ''}")

    def carregar(cur, exe):
        if alterados:
            t = time.time()
            resp = get(f"{AGR}/{r['agregado']}/periodos/{'|'.join(alterados)}/variaveis/{r['variavel']}?localidades=N6[N3[29]]")
            linhas = [(int(s["localidade"]["id"]), int(a), r["tipo"], int(v), r["fonte"],
                       dt.datetime.strptime(agora[a], "%d/%m/%Y").date())
                      for x in resp.json() for res in x["resultados"] for s in res["series"]
                      for a, v in s["serie"].items() if v and v.lstrip("-").isdigit()]
            copiar(cur, "stg.ibge_populacao", ["codigo_ibge", "ano", "tipo", "populacao", "fonte", "modificado_fonte_em"], linhas)
            log(rid, f"passo 1: baixou {len(linhas)} valores ({len(resp.content) / 1024:.0f} KB em {time.time() - t:.1f}s)")
        else:
            cur.execute("TRUNCATE stg.ibge_populacao")
        cur.execute("SELECT * FROM etl.carga_ibge_populacao(%s, %s, %s)", (exe, r["tipo"], [int(a) for a in escopo]))
        return cur.fetchone()

    executar(conn, rid, agora, escopo or None, carregar)


# ============================================================================================ FTP PIB DOS MUNICÍPIOS
def ftp_linhas_ba():
    """Baixa o ZIP (cache por ETag), lê o TXT pelo layout versionado e valida antes de entregar as linhas."""
    if "ftp" in CTX:
        return CTX["ftp"]
    h = requests.head(U_FTP, timeout=60).headers
    etag = h["ETag"].strip('"').replace(":", "_")
    arq = CACHE / f"pib_municipios_{FTP_EDICAO}_{etag}.zip"
    if not arq.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        t = time.time(); arq.write_bytes(get(U_FTP).content)
        log("ibge_pib_municipal", f"passo 1: baixou o ZIP ({arq.stat().st_size / 1e6:.1f} MB em {time.time() - t:.1f}s)")
    else:
        log("ibge_pib_municipal", "passo 1: ZIP desta versão (mesmo ETag) já está no cache, sem download")
    with open(LAYOUT_CSV, encoding="utf-8") as f:
        layout = [r for r in csv.DictReader(f) if r["coluna_destino"]]
    tam_linha = max(int(r["posicao"]) + int(r["tamanho"]) - 1 for r in csv.DictReader(open(LAYOUT_CSV, encoding="utf-8")))
    z = zipfile.ZipFile(arq)
    txt = next(n for n in z.namelist() if n.endswith(".txt"))
    linhas = []
    for l in z.open(txt).read().decode("latin1").splitlines():
        if l[46:48] != "29":
            continue
        if len(l) != tam_linha or not l[46:53].isdigit() or l[23:25] != "BA":
            raise ValueError(f"layout do FTP não confere (linha com {len(l)} caracteres, esperado {tam_linha}): "
                             "o IBGE pode ter mudado o layout; carga abortada")
        d = {}
        for r in layout:
            v = l[int(r["posicao"]) - 1:int(r["posicao"]) - 1 + int(r["tamanho"])].strip()
            d[r["coluna_destino"]] = (v or None) if r["tipo"] == "caractere" else (v if v else None)
        linhas.append(d)
    # conferência com a API 5938 (nível UF) no último ano
    ult = max(int(d["ano"]) for d in linhas)
    soma = sum(float(d["pib_mil_reais"]) for d in linhas if int(d["ano"]) == ult)
    api = float(get(f"{AGR}/5938/periodos/{ult}/variaveis/37?localidades=N3[29]").json()[0]["resultados"][0]["series"][0]["serie"][str(ult)])
    if abs(soma - api) / api > 1e-6:
        raise ValueError(f"soma do PIB BA {ult} no FTP ({soma:,.0f}) difere da API 5938 ({api:,.0f}); carga abortada")
    log("ibge_pib_municipal", f"passo 1: {len(linhas)} linhas BA lidas pelo layout; conferência PIB {ult} FTP x API 5938 OK "
                              f"(R$ {soma / 1e6:,.2f} bi)")
    CTX["ftp"] = (linhas, parsedate_to_datetime(h["Last-Modified"]).date(), ult)
    return CTX["ftp"]


def recurso_pib(conn):
    rid = "ibge_pib_municipal"
    with conn.cursor() as cur:
        registrar_recurso(cur, rid, "http", "ELT_ARQUIVO", U_FTP, "ibge.pib_municipal",
                          {"fonte_tabela": "ftp_pib_municipios", "produto_id": 9088})
        h = requests.head(U_FTP, timeout=60).headers
        agora = {"etag": h.get("ETag"), "last_modified": h.get("Last-Modified"), "edicao": FTP_EDICAO}
        antes = checkpoint(cur, rid)
    escopo = None if antes == agora else {"ba": "todos os anos (arquivo único)"}
    if escopo:
        log(rid, f"passo 0: {'carga inicial' if antes is None else 'ETag/edição mudou'}")

    def carregar(cur, exe):
        linhas, data_fonte, _ = ftp_linhas_ba()
        provisorios = {int(a) for a in FTP_EDICAO.split("_")}
        cols = ["codigo_ibge", "ano", "pib_mil_reais", "pib_per_capita_reais", "vab_agropecuaria_mil_reais",
                "vab_industria_mil_reais", "vab_servicos_mil_reais", "vab_adm_publica_mil_reais", "vab_total_mil_reais",
                "impostos_liquidos_mil_reais", "atividade_1", "atividade_2", "atividade_3"]
        copiar(cur, "stg.ibge_pib_municipal", cols + ["provisorio", "edicao", "modificado_fonte_em"],
               [[d[c] for c in cols] + [int(d["ano"]) in provisorios, FTP_EDICAO, data_fonte] for d in linhas])
        return merge(cur, exe, "ibge.pib_municipal", "stg.ibge_pib_municipal", ["codigo_ibge", "ano"],
                     cols[2:] + ["provisorio", "edicao"])

    executar(conn, rid, agora, escopo, carregar)


# ============================================================================================ MUNICÍPIO (dimensão)
def recurso_municipio(conn):
    rid = "ibge_municipio"
    with conn.cursor() as cur:
        registrar_recurso(cur, rid, "hash_corpo", "ETL_API", U_LOC, "ibge.municipio",
                          {"fonte_tabela": "localidades", "componentes": ["localidades", "malhas/metadados", "ftp tipologias"]})
        loc_b, meta_b = get(U_LOC).content, get(U_MALHA_META).content
        agora = {"localidades": sha(loc_b), "malhas_metadados": sha(meta_b),
                 "ftp_etag": requests.head(U_FTP, timeout=60).headers.get("ETag")}
        antes = checkpoint(cur, rid)
    mudou = [k for k in agora if (antes or {}).get(k) != agora[k]]
    escopo = {"componentes_alterados": mudou} if mudou else None
    if escopo:
        log(rid, f"passo 0: componentes alterados {mudou}")

    def carregar(cur, exe):
        ftp, data_fonte, ult = ftp_linhas_ba()
        tip = {int(d["codigo_ibge"]): d for d in ftp if int(d["ano"]) == ult}
        area = {int(m["id"]): m for m in json.loads(meta_b)}
        g = lambda d, *ks: [d := (d or {}).get(k) for k in ks][-1]
        linhas = []
        for m in json.loads(loc_b):
            c, t, a = m["id"], tip.get(m["id"], {}), area.get(m["id"], {})
            linhas.append([c, m["nome"], "BA",
                           g(m, "microrregiao", "id"), g(m, "microrregiao", "nome"),
                           g(m, "microrregiao", "mesorregiao", "id"), g(m, "microrregiao", "mesorregiao", "nome"),
                           g(m, "regiao-imediata", "id"), g(m, "regiao-imediata", "nome"), t.get("polo_regiao_imediata") == "Polo",
                           g(m, "regiao-imediata", "regiao-intermediaria", "id"), g(m, "regiao-imediata", "regiao-intermediaria", "nome"),
                           t.get("polo_regiao_intermediaria") == "Polo",
                           t.get("regiao_metropolitana"), t.get("codigo_concentracao_urbana"), t.get("concentracao_urbana"),
                           t.get("tipo_concentracao_urbana"), t.get("codigo_arranjo_populacional"), t.get("arranjo_populacional"),
                           t.get("hierarquia_urbana"), t.get("hierarquia_urbana_principal"),
                           t.get("codigo_regiao_rural"), t.get("regiao_rural"), t.get("regiao_rural_nucleo"),
                           t.get("semiarido") == "Sim", t.get("amazonia_legal") == "Sim",
                           g(a, "area", "dimensao"), g(a, "centroide", "longitude"), g(a, "centroide", "latitude"), data_fonte])
        cols = ["codigo_ibge", "municipio", "uf", "codigo_microrregiao", "microrregiao", "codigo_mesorregiao", "mesorregiao",
                "codigo_regiao_imediata", "regiao_imediata", "polo_regiao_imediata", "codigo_regiao_intermediaria",
                "regiao_intermediaria", "polo_regiao_intermediaria", "regiao_metropolitana", "codigo_concentracao_urbana",
                "concentracao_urbana", "tipo_concentracao_urbana", "codigo_arranjo_populacional", "arranjo_populacional",
                "hierarquia_urbana", "hierarquia_urbana_principal", "codigo_regiao_rural", "regiao_rural", "regiao_rural_nucleo",
                "semiarido", "amazonia_legal", "area_km2", "centroide_lon", "centroide_lat"]
        copiar(cur, "stg.ibge_municipio", cols + ["modificado_fonte_em"], linhas)
        log(rid, f"passo 1: {len(linhas)} municípios montados (localidades + malhas + {len(tip)} tipologias do FTP {ult})")
        return merge(cur, exe, "ibge.municipio", "stg.ibge_municipio", ["codigo_ibge"], cols[1:])

    executar(conn, rid, agora, escopo, carregar)


# ============================================================================================ MALHA
def recurso_malha(conn):
    rid = "ibge_malha"
    with conn.cursor() as cur:
        registrar_recurso(cur, rid, "hash_corpo", "ETL_API", U_MALHA, "ibge.malha", {"fonte_tabela": "malhas"})
        t = time.time(); corpo = get(U_MALHA).content
        agora = {"sha256": sha(corpo), "qualidade": QUALIDADE_MALHA}
        antes = checkpoint(cur, rid)
    escopo = None if antes == agora else {"ba": "todos os municípios"}
    if escopo:
        log(rid, f"passo 0: hash do GeoJSON mudou ({len(corpo) / 1024:.0f} KB em {time.time() - t:.1f}s; "
                 "a API de malhas não tem ETag, então o corpo é baixado para calcular o hash)")

    def carregar(cur, exe):
        feats = json.loads(corpo)["features"]
        copiar(cur, "stg.ibge_malha", ["codigo_ibge", "qualidade", "geometria", "modificado_fonte_em"],
               [[int(f["properties"]["codarea"]), QUALIDADE_MALHA, f["geometry"], None] for f in feats])
        log(rid, f"passo 1: {len(feats)} geometrias")
        return merge(cur, exe, "ibge.malha", "stg.ibge_malha", ["codigo_ibge"], ["qualidade", "geometria"])

    executar(conn, rid, agora, escopo, carregar)


# ============================================================================================ SIMULAÇÃO
def preparar_simulacao(conn):
    """Deixa o banco 'desatualizado' em pontos conhecidos, para ver o nível 3 agir só neles."""
    with conn.cursor() as cur:
        cur.execute("""UPDATE ibge.populacao SET populacao = populacao + 1, _hash = md5(row(populacao + 1, fonte)::text)
                       WHERE tipo='estimativa' AND ano=2025 AND codigo_ibge IN (2927408, 2910800)""")
        cur.execute("DELETE FROM ibge.populacao WHERE tipo='estimativa' AND ano=2025 AND codigo_ibge = 2905701")
        # a FK (04_fk_ibge.sql) exige o município; ele é removido no fim da simulação (limpar_simulacao)
        cur.execute("""INSERT INTO ibge.municipio (codigo_ibge, municipio, uf, _hash)
                       VALUES (2999999, 'Município fictício (simulação)', 'BA', 'x') ON CONFLICT DO NOTHING""")
        cur.execute("""INSERT INTO ibge.populacao (codigo_ibge, ano, tipo, populacao, fonte, _hash)
                       VALUES (2999999, 2025, 'estimativa', 1, 'IBGE/SIDRA 6579', 'x') ON CONFLICT DO NOTHING""")
        cur.execute("""UPDATE etl.checkpoint SET digital = jsonb_set(digital, '{2025}', '"01/01/2000"')
                       WHERE recurso_id = 'ibge_6579_populacao'""")
        # PIB: o IBGE "revisou" 2 municípios em 2022 (provisório) -> simula com valor antigo + hash antigo
        cur.execute("""UPDATE ibge.pib_municipal SET pib_mil_reais = pib_mil_reais - 1000, _hash = 'versao-anterior'
                       WHERE ano = 2022 AND codigo_ibge IN (2927408, 2905701)""")
        cur.execute("""UPDATE etl.checkpoint SET digital = jsonb_set(digital, '{etag}', '"etag-antigo"')
                       WHERE recurso_id = 'ibge_pib_municipal'""")
        conn.commit()
    print("simulação: população 2025 (2 alteradas, 1 apagada, 1 fictícia) e PIB 2022 (2 municípios com valor antigo), "
          "checkpoints envelhecidos\n")


def limpar_simulacao(conn):
    """Remove o município fictício; a população dele já foi excluída pelo MERGE (era o caso 'sumiu da fonte')."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM ibge.municipio WHERE codigo_ibge = 2999999")
        conn.commit()


def resumo(conn):
    with conn.cursor() as cur:
        print("\nConteúdo do banco:")
        for t in ("ibge.municipio", "ibge.populacao", "ibge.pib_municipal", "ibge.malha", "meta.fonte_tabela",
                  "meta.variavel", "meta.periodo", "meta.calendario", "meta.layout_ftp", "etl.historico", "etl.exclusao"):
            cur.execute(f"SELECT count(*) FROM {t}"); print(f"  {t:22} {cur.fetchone()[0]:>6} linhas")


if __name__ == "__main__":
    with psycopg.connect(dsn(), options=OPCOES_AUDITORIA) as conn:
        if "--simular" in sys.argv:
            preparar_simulacao(conn)
        t = time.time()
        log("workflow", f"início (disparo: {DISPARO})")
        carregar_meta(conn)
        # ORDEM: ibge.municipio primeiro. populacao, pib_municipal e malha têm FK para ela (04_fk_ibge.sql);
        # num banco vazio, carregar uma filha antes violaria a FK. O recurso do município lê o FTP sozinho (ftp_linhas_ba).
        recurso_municipio(conn)
        for r in POPULACAO:
            recurso_populacao(conn, r)
        recurso_pib(conn)
        recurso_malha(conn)
        if "--simular" in sys.argv:
            limpar_simulacao(conn)
        log("workflow", f"fim ({time.time() - t:.1f}s)")
        resumo(conn)

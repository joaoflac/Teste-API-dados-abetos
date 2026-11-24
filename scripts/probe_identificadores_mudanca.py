"""
Testa, para cada fonte do Painel Territorial CT&I, quais identificadores de mudança existem antes de baixar dados:
  - cabeçalhos HTTP: ETag, Last-Modified, Content-Length, Accept-Ranges, Cache-Control
  - requisição condicional: If-None-Match / If-Modified-Since devolvem 304?
  - estabilidade: o ETag e o hash do corpo se repetem em duas chamadas seguidas?
  - metadados próprios da fonte (CKAN resource_show, IBGE periodos/metadados, SICONFI extrato_entregas)

Uso:  py -3.12 scripts/probe_identificadores_mudanca.py
Saída: orquestracao/probe_identificadores_mudanca.csv e .json (resposta crua dos metadados)
"""
import hashlib, json, ssl, datetime as dt, warnings
from pathlib import Path
import requests, urllib3

warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "orquestracao"; OUT.mkdir(exist_ok=True)
UA = {"User-Agent": "painel-territorial-cti-probe/1.0"}
IBGE = "https://servicodados.ibge.gov.br/api"
SICONFI = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
BNDES = "https://dadosabertos.bndes.gov.br/api/3/action"
ANEEL_HOST, ANEEL_IP = "dadosabertos.aneel.gov.br", "200.198.220.169"


class NoSNIAdapter(requests.adapters.HTTPAdapter):
    """ANEEL derruba o TLS quando há SNI; conecta pelo IP sem SNI e manda o Host no cabeçalho."""
    def init_poolmanager(self, *a, **kw):
        ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        kw["ssl_context"] = ctx; kw["server_hostname"] = None
        return super().init_poolmanager(*a, **kw)


S = requests.Session(); S.headers.update(UA)
SA = requests.Session(); SA.headers.update(UA); SA.mount("https://", NoSNIAdapter())


def aneel_url(u):
    return u.replace(f"https://{ANEEL_HOST}", f"https://{ANEEL_IP}")


def req(method, url, aneel=False, headers=None, corpo=True, timeout=120):
    s, h = (SA, {"Host": ANEEL_HOST}) if aneel else (S, {})
    h.update(headers or {})
    r = s.request(method, aneel_url(url) if aneel else url, headers=h, timeout=timeout, stream=True,
                  verify=not aneel, allow_redirects=True)
    body = b""
    if corpo and method == "GET":
        body = r.content  # só usado para endpoints pequenos
    r.close()
    return r, body


def probe_http(nome, fonte, tipo, url, aneel=False, grande=False):
    """grande=True: arquivo pesado, não baixa o corpo (HEAD, e GET só com Range de 1 byte)."""
    lin = dict(fonte=fonte, recurso=nome, tipo=tipo, url=url)
    try:
        r, b1 = req("HEAD", url, aneel)
        if r.status_code >= 400 or (not r.headers.get("ETag") and not r.headers.get("Last-Modified")):
            r, b1 = req("GET", url, aneel, headers={"Range": "bytes=0-0"} if grande else None, corpo=not grande)
        hd = r.headers
        lin.update(status=r.status_code, etag=hd.get("ETag", ""), last_modified=hd.get("Last-Modified", ""),
                   content_length=hd.get("Content-Range", "").split("/")[-1] if r.status_code == 206 else hd.get("Content-Length", ""),
                   accept_ranges=hd.get("Accept-Ranges", ""), cache_control=hd.get("Cache-Control", ""),
                   server=hd.get("Server", ""))
        # condicional
        cond = {}
        if lin["etag"]:
            cond["If-None-Match"] = lin["etag"]
        if lin["last_modified"]:
            cond["If-Modified-Since"] = lin["last_modified"]
        if cond:
            rc, _ = req("GET", url, aneel, headers=cond, corpo=False)
            lin["condicional_304"] = "sim" if rc.status_code == 304 else f"não ({rc.status_code})"
        else:
            lin["condicional_304"] = "sem validador"
        # estabilidade (2ª chamada)
        if not grande:
            r2, b2 = req("GET", url, aneel)
            if not b1:
                r1, b1 = req("GET", url, aneel)
            lin["etag_estavel"] = ("sim" if r2.headers.get("ETag", "") == lin["etag"] else "não") if lin["etag"] else "-"
            lin["hash_corpo_estavel"] = "sim" if hashlib.sha256(b1).digest() == hashlib.sha256(b2).digest() else "não"
            lin["tamanho_corpo"] = len(b2)
    except Exception as e:
        lin.update(status="erro", observacao=f"{type(e).__name__}: {e}"[:200])
    print(f"  {fonte:8} {nome:45} {lin.get('status')} etag={bool(lin.get('etag'))} lm={lin.get('last_modified','')[:25]} 304={lin.get('condicional_304')}")
    return lin


def ckan_resource(fonte, base, rid, aneel=False):
    try:
        r, b = req("GET", f"{base}/resource_show?id={rid}", aneel)
        res = json.loads(b)["result"]
        r2, b2 = req("GET", f"{base}/package_show?id={res['package_id']}", aneel)
        pkg = json.loads(b2)["result"]
        ds = {}
        if res.get("datastore_active"):
            r3, b3 = req("GET", f"{base}/datastore_search?resource_id={rid}&limit=1", aneel)
            j = json.loads(b3)["result"]
            ds = dict(datastore_total=j.get("total"), datastore_campos=[f["id"] for f in j.get("fields", [])])
        return dict(resource_id=rid, nome=res.get("name"), formato=res.get("format"), url=res.get("url"),
                    last_modified=res.get("last_modified"), metadata_modified=res.get("metadata_modified"),
                    created=res.get("created"), hash=res.get("hash"), size=res.get("size"),
                    datastore_active=res.get("datastore_active"), pacote=pkg.get("name"),
                    pacote_metadata_modified=pkg.get("metadata_modified"), **ds)
    except Exception as e:
        return dict(resource_id=rid, erro=f"{type(e).__name__}: {e}"[:200])


linhas, meta = [], {}
print("HTTP")
# ---------------- IBGE (API)
for nome, u in [
    ("localidades municipios BA", f"{IBGE}/v1/localidades/estados/29/municipios"),
    ("agregado 6579 populacao", f"{IBGE}/v3/agregados/6579/periodos/-3/variaveis/9324?localidades=N6[N3[29]]"),
    ("agregado 5938 PIB", f"{IBGE}/v3/agregados/5938/periodos/-2/variaveis/37?localidades=N6[N3[29]]"),
    ("agregado 4709 censo 2022", f"{IBGE}/v3/agregados/4709/periodos/2022/variaveis/93?localidades=N6[N3[29]]"),
    ("malhas metadados BA", f"{IBGE}/v3/malhas/estados/29/metadados?intrarregiao=municipio"),
    ("malhas geojson BA", f"{IBGE}/v3/malhas/estados/29?intrarregiao=municipio&formato=application/vnd.geo+json&qualidade=minima"),
    ("agregado 6579 periodos", f"{IBGE}/v3/agregados/6579/periodos"),
    ("agregado 5938 metadados", f"{IBGE}/v3/agregados/5938/metadados"),
]:
    linhas.append(probe_http(nome, "IBGE", "API", u))
# ---------------- Arquivos (sem API)
for nome, fonte, u in [
    ("PIB Municipios base TXT zip", "IBGE", "https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip"),
    ("Censo Ed. Superior 2024 zip", "INEP", "https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2024.zip"),
    ("Acessos banda larga fixa zip", "ANATEL", "https://www.anatel.gov.br/dadosabertos/paineis_de_dados/acessos/acessos_banda_larga_fixa.zip"),
]:
    linhas.append(probe_http(nome, fonte, "Arquivo", u, grande=True))
linhas.append(probe_http("DEC/FEC conjuntos zip", "ANEEL", "Arquivo",
              f"https://{ANEEL_HOST}/dataset/d5f0712e-62f6-4736-8dff-9991f10758a7/resource/4493985c-baea-429c-9df5-3030422c71d7/download/indicadores-continuidade-coletivos-2020-2029.zip",
              aneel=True, grande=True))
# ---------------- SICONFI (API ORDS)
for nome, u in [
    ("DCA I-E Salvador 2024", f"{SICONFI}/dca?an_exercicio=2024&no_anexo=DCA-Anexo%20I-E&id_ente=2927408"),
    ("RREO Anexo 02 Salvador 2025 6o bim", f"{SICONFI}/rreo?an_exercicio=2025&nr_periodo=6&co_tipo_demonstrativo=RREO&no_anexo=RREO-Anexo%2002&id_ente=2927408"),
    ("extrato_entregas Salvador 2025", f"{SICONFI}/extrato_entregas?id_ente=2927408&an_referencia=2025"),
]:
    linhas.append(probe_http(nome, "SICONFI", "API", u))
# ---------------- CKAN datastore (BNDES / ANEEL)
for nome, rid in [("operacoes nao automaticas", "6f56b78c-510f-44b6-8274-78a5b7e931f4"),
                  ("operacoes indiretas automaticas", "612faa0b-b6be-4b2c-9317-da5dc2c0b901")]:
    linhas.append(probe_http(f"datastore {nome} (limit 5)", "BNDES", "API",
                             f"{BNDES}/datastore_search?resource_id={rid}&limit=5"))
for nome, rid in [("INDGER", "fd10c9d4-cb76-4020-a322-e79afb13eaf7"), ("SIGA", "11ec447d-698d-4ab8-977f-b424d5deee6a"),
                  ("P&D", "3a7aee00-b6ee-4913-9670-f6b60f4a7bea")]:
    linhas.append(probe_http(f"datastore {nome} (limit 5)", "ANEEL", "API",
                             f"https://{ANEEL_HOST}/api/3/action/datastore_search?resource_id={rid}&limit=5", aneel=True))

print("Metadados específicos")
# IBGE: periodos (data de modificação por período) e metadados
for ag in (6579, 5938, 4709):
    _, b = req("GET", f"{IBGE}/v3/agregados/{ag}/periodos")
    meta[f"ibge_{ag}_periodos"] = json.loads(b)[-4:]
    _, b = req("GET", f"{IBGE}/v3/agregados/{ag}/metadados")
    m = json.loads(b); meta[f"ibge_{ag}_periodicidade"] = m.get("periodicidade")
# SICONFI extrato de entregas
_, b = req("GET", f"{SICONFI}/extrato_entregas?id_ente=2927408&an_referencia=2025")
meta["siconfi_extrato_entregas_salvador_2025"] = json.loads(b).get("items", [])[:6]
# CKAN
meta["bndes_ckan"] = [ckan_resource("BNDES", BNDES, rid) for rid in
                      ("6f56b78c-510f-44b6-8274-78a5b7e931f4", "612faa0b-b6be-4b2c-9317-da5dc2c0b901")]
meta["aneel_ckan"] = [ckan_resource("ANEEL", f"https://{ANEEL_HOST}/api/3/action", rid, aneel=True) for rid in
                      ("fd10c9d4-cb76-4020-a322-e79afb13eaf7", "11ec447d-698d-4ab8-977f-b424d5deee6a",
                       "3a7aee00-b6ee-4913-9670-f6b60f4a7bea", "4493985c-baea-429c-9df5-3030422c71d7")]

import csv
cols = ["fonte", "recurso", "tipo", "status", "etag", "last_modified", "content_length", "accept_ranges",
        "condicional_304", "etag_estavel", "hash_corpo_estavel", "tamanho_corpo", "cache_control", "server", "url", "observacao"]
with open(OUT / "probe_identificadores_mudanca.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(linhas)
(OUT / "probe_identificadores_mudanca_metadados.json").write_text(
    json.dumps(dict(data_teste=dt.datetime.now().isoformat(timespec="seconds"), **meta), ensure_ascii=False, indent=1, default=str),
    encoding="utf-8")
print("-> orquestracao/probe_identificadores_mudanca.csv e _metadados.json")

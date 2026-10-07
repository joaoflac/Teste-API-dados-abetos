"""
ANEEL 4.5 — DEC e FEC da COELBA no último ano completo, por conjunto elétrico e por município.

Uso:  python aneel_decfec_ba.py [ano] [pasta_cache]   (padrão: ano anterior ao corrente, ./cache)
Só biblioteca padrão. Conecta pelo IP sem SNI (o servidor derruba o TLS com SNI dadosabertos.aneel.gov.br).
Os índices vêm do ZIP oficial (72 MB): o datastore do mesmo recurso está defasado e sem vários meses
(ex.: conjunto ABRANTES sem nenhuma linha de DEC em 2025), enquanto o CSV do ZIP tem os 12 meses de todos.

Saídas (amostras/):
  aneel_4.5_decfec_conjunto_BA_<ano>.csv   DEC/FEC anuais (soma dos 12 meses), limites regulatórios e consumidores
  aneel_4.5_decfec_municipio_BA_<ano>.csv  média dos conjuntos que atendem o município, ponderada por consumidores
  aneel_4.5_indqual_conjunto_municipio_BA.csv  de-para reduzido aos conjuntos ativos no ano
"""
import csv, http.client, io, json, ssl, sys, urllib.parse, zipfile, datetime as dt
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AM = ROOT / "amostras"
ANO = int(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today().year - 1
CACHE = Path(sys.argv[2] if len(sys.argv) > 2 else "cache")
ZIP_INDICES = ("/dataset/d5f0712e-62f6-4736-8dff-9991f10758a7/resource/4493985c-baea-429c-9df5-3030422c71d7"
               "/download/indicadores-continuidade-coletivos-2020-2029.zip")
R_LIMITES = "fd69e1dd-fd66-4269-b60c-cc0b7eb221b4"   # indicadores-continuidade-coletivos-limite
R_INDQUAL = "3f841488-80a8-42f2-a6ca-e0c593b228de"   # de-para conjunto -> município

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def http_get(caminho):
    c = http.client.HTTPSConnection("200.198.220.169", context=ctx, timeout=600)
    c.request("GET", caminho, headers={"Host": "dadosabertos.aneel.gov.br"})
    return c.getresponse().read()


def ckan(action, **p):
    q = urllib.parse.urlencode({k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in p.items()})
    return json.loads(http_get(f"/api/3/action/{action}?{q}"))["result"]


def indices_zip():
    arq = CACHE / "aneel_indicadores-continuidade-coletivos-2020-2029.zip"
    if not arq.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        arq.write_bytes(http_get(ZIP_INDICES))
    z = zipfile.ZipFile(arq)
    for r in csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin1"), delimiter=";"):
        if (r["SigAgente"].strip() == "COELBA" and r["AnoIndice"] == str(ANO)
                and r["SigIndicador"] in ("DEC", "FEC", "NumCon")):
            yield r


def todos(resource_id, filters):
    out, off = [], 0
    while True:
        r = ckan("datastore_search", resource_id=resource_id, filters=filters, limit=32000, offset=off)
        out += r["records"]
        off += 32000
        if off >= r["total"]:
            return out


def num(v):
    return float(str(v).replace(".", "").replace(",", ".")) if v not in (None, "") else None


def salvar(linhas, nome):
    with open(AM / nome, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(f"  -> amostras/{nome} ({len(linhas)} linhas)")


print(f"DEC/FEC COELBA {ANO}")
idx = list(indices_zip())
lim = todos(R_LIMITES, {"SigAgente": "COELBA", "AnoLimiteQualidade": ANO})

conj = defaultdict(lambda: dict(DEC=0.0, FEC=0.0, meses=set(), NumCon={}))
nome = {}
for r in idx:
    k = str(r["IdeConjUndConsumidoras"])
    nome[k] = r["DscConjUndConsumidoras"].strip()
    v, mes = num(r["VlrIndiceEnviado"]), int(r["NumPeriodoIndice"])
    if r["SigIndicador"] == "NumCon":
        conj[k]["NumCon"][mes] = v
    else:
        conj[k][r["SigIndicador"]] += v or 0
        conj[k]["meses"].add(mes)
limite = {(str(r["IdeConjUndConsumidoras"]), r["SigIndicador"]): num(r["VlrLimite"]) for r in lim}

linhas_conj = []
for k, d in sorted(conj.items(), key=lambda x: nome[x[0]]):
    cons = d["NumCon"][max(d["NumCon"])] if d["NumCon"] else None
    ld, lf = limite.get((k, "DEC")), limite.get((k, "FEC"))
    linhas_conj.append(dict(
        ano=ANO, IdeConjUndConsumidoras=k, DscConjUndConsumidoras=nome[k], meses_apurados=len(d["meses"]),
        consumidores_dez=int(cons) if cons else "", DEC_anual_horas=round(d["DEC"], 2), FEC_anual_vezes=round(d["FEC"], 2),
        limite_DEC=ld if ld is not None else "", limite_FEC=lf if lf is not None else "",
        DEC_acima_limite="" if ld is None else d["DEC"] > ld, FEC_acima_limite="" if lf is None else d["FEC"] > lf))
salvar(linhas_conj, f"aneel_4.5_decfec_conjunto_BA_{ANO}.csv")

# de-para conjunto -> município (só conjuntos ativos no ano)
dp = [r for r in todos(R_INDQUAL, {"SigUF": "BA"}) if str(r["IdeConjUnidConsumidoras"]) in conj]
for r in dp:
    r.pop("_id", None)
salvar(dp, "aneel_4.5_indqual_conjunto_municipio_BA.csv")

por_conj = {l["IdeConjUndConsumidoras"]: l for l in linhas_conj}
mun = defaultdict(list)
for r in dp:
    mun[(str(r["CodMunicipio"]), r["NomMunicipio"])].append(por_conj[str(r["IdeConjUnidConsumidoras"])])
linhas_mun = []
for (cod, nm), cs in sorted(mun.items(), key=lambda x: x[0][1]):
    peso = [c["consumidores_dez"] or 0 for c in cs]
    tot = sum(peso) or 1
    linhas_mun.append(dict(
        ano=ANO, codigo_ibge=cod, municipio=nm, n_conjuntos=len(cs),
        conjuntos="; ".join(c["DscConjUndConsumidoras"] for c in cs),
        DEC_ponderado_horas=round(sum(c["DEC_anual_horas"] * p for c, p in zip(cs, peso)) / tot, 2),
        FEC_ponderado_vezes=round(sum(c["FEC_anual_vezes"] * p for c, p in zip(cs, peso)) / tot, 2),
        conjuntos_DEC_acima_limite=sum(c["DEC_acima_limite"] is True for c in cs)))
salvar(linhas_mun, f"aneel_4.5_decfec_municipio_BA_{ANO}.csv")

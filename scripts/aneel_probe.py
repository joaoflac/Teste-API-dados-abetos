"""
Sonda o portal CKAN da ANEEL (rodar de uma rede que alcance dadosabertos.aneel.gov.br).
Lista os datasets do catálogo, os recursos e — quando o datastore estiver ativo — os campos
e os valores distintos das colunas categóricas (amostra de 5.000 linhas filtradas para BA quando possível).
Saída: amostras/aneel_*.csv e categorias_cti/aneel_*.csv
"""
import json, requests, pandas as pd
from pathlib import Path

B = "https://dadosabertos.aneel.gov.br/api/3/action/"
ROOT = Path(__file__).resolve().parent.parent
BUSCAS = {"4.1/4.2 SIGA geração": "siga", "4.3 SAMP mercado": "samp", "4.4 P&D": "pesquisa desenvolvimento",
          "4.5 DEC FEC": "indicadores-coletivos-de-continuidade-dec-e-fec"}
s = requests.Session()
recs, cats = [], []
for ind, q in BUSCAS.items():
    for pkg in s.get(B + "package_search", params={"q": q, "rows": 5}, timeout=120).json()["result"]["results"]:
        for r in pkg["resources"]:
            recs.append(dict(indicador=ind, dataset_id=pkg["name"], recurso_id=r["id"], recurso=r["name"],
                             formato=r.get("format"), datastore=r.get("datastore_active"), url=r["url"]))
            if not r.get("datastore_active"):
                continue
            res = s.get(B + "datastore_search", params={"resource_id": r["id"], "limit": 5000}, timeout=300).json()["result"]
            df = pd.DataFrame(res["records"])
            uf = next((c for c in df.columns if c.lower() in ("siguf", "sig_uf", "uf", "sgluf")), None)
            if uf:
                ba = s.get(B + "datastore_search", params={"resource_id": r["id"], "limit": 5000,
                                                         "filters": json.dumps({uf: "BA"})}, timeout=300).json()["result"]
                df = pd.DataFrame(ba["records"]) if ba["records"] else df
            df.head(30).to_csv(ROOT / "amostras" / f"aneel_{r['id'][:8]}_amostra.csv", index=False, encoding="utf-8-sig")
            for c in df.columns:
                if df[c].dtype == object and df[c].nunique() < 200:
                    for v, n in df[c].value_counts().items():
                        cats.append(dict(indicador=ind, recurso_id=r["id"], coluna=c, valor=v, n_amostra=n))
pd.DataFrame(recs).to_csv(ROOT / "amostras" / "aneel_recursos_catalogo.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(cats).to_csv(ROOT / "categorias_cti" / "aneel_valores_categoricos.csv", index=False, encoding="utf-8-sig")
print(len(recs), "recursos;", len(cats), "valores categóricos")

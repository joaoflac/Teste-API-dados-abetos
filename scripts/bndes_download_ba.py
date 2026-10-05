"""Baixa todas as operações BNDES com UF=BA (datastore CKAN) para cache local."""
import json, sys, requests, pandas as pd
from pathlib import Path

B = "https://dadosabertos.bndes.gov.br/api/3/action/datastore_search"
RES = {
    "nao_automaticas": ("6f56b78c-510f-44b6-8274-78a5b7e931f4", "BA"),
    "indiretas_automaticas": ("612faa0b-b6be-4b2c-9317-da5dc2c0b901", " BA"),  # UF vem com espaço à esquerda
}
out = Path(sys.argv[1] if len(sys.argv) > 1 else "cache")
out.mkdir(exist_ok=True)
for nome, (rid, uf) in RES.items():
    rows, offset = [], 0
    while True:
        r = requests.get(B, params={"resource_id": rid, "filters": json.dumps({"uf": uf}),
                                    "limit": 20000, "offset": offset}, timeout=300).json()["result"]
        rows += r["records"]
        offset += len(r["records"])
        print(nome, offset, "/", r["total"], flush=True)
        if not r["records"] or offset >= r["total"]:
            break
    pd.DataFrame(rows).to_csv(out / f"bndes_{nome}_BA.csv", index=False, encoding="utf-8-sig")

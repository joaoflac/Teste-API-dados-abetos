"""Varre DCA Anexo I-E (despesa por função/subfunção) e I-C (receita) para os 417 municípios da BA."""
import sys, time, requests, pandas as pd
from concurrent.futures import ThreadPoolExecutor

U = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/"
ANO = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
OUT = sys.argv[2] if len(sys.argv) > 2 else "."
s = requests.Session()

entes = pd.DataFrame(s.get(U + "entes", timeout=120).json()["items"])
ba = entes[(entes.uf == "BA") & (entes.esfera == "M")]
print("municipios BA em /entes:", len(ba), flush=True)


def get(path, **p):
    for t in range(4):
        try:
            r = s.get(U + path, params=p, timeout=120)
            if r.status_code == 200:
                return r.json()["items"]
        except requests.RequestException:
            pass
        time.sleep(2 * (t + 1))
    return None


def um(cod):
    d = get("dca", an_exercicio=ANO, no_anexo="DCA-Anexo I-E", id_ente=cod)
    return cod, d


rows, sem = [], []
with ThreadPoolExecutor(4) as ex:
    for cod, d in ex.map(um, ba.cod_ibge):
        if not d:
            sem.append(cod)
        else:
            rows += d
pd.DataFrame(rows).to_csv(f"{OUT}/siconfi_dca_IE_BA_{ANO}.csv", index=False, encoding="utf-8-sig")
pd.Series(sem, name="cod_ibge_sem_dca").to_csv(f"{OUT}/siconfi_dca_IE_BA_{ANO}_sem_dados.csv", index=False)
print("com dados:", len(ba) - len(sem), "sem dados:", len(sem))

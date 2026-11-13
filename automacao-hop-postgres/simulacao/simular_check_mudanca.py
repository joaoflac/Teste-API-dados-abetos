"""Simulação (Python, stdlib) das etapas 1 e 8 do PLANO.md §9c: check de mudança por ETag/Last-Modified.
Não é o Hop. Usa curl com Range (o servidor do INEP reseta GET/HEAD simples e conexões do Python).
Uso: python -I simular_check_mudanca.py   (rode duas vezes: 1a = primeira carga, 2a = sem mudança)
"""
import csv, subprocess, sys, datetime, os

sys.stdout.reconfigure(encoding="utf-8")
BASE = r"C:\Users\joao.vinicius\Desktop\Teste-API-dados-abetos\automacao-hop-postgres\simulacao" + "\\"
CTRL = BASE + "fonte_controle.csv"
ANO = 2024
URL = "https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_%d.zip"
COLS = ["fonte", "recurso", "url", "etag", "last_modified", "tamanho_bytes", "ultima_verificacao", "ultima_mudanca", "status"]


def probe(url, tentativas=4):
    """GET com Range 0-0: devolve (http_status, etag, last_modified, tamanho_total). Refaz se o servidor resetar (acontece)."""
    import time
    out = ""
    for i in range(tentativas):
        out = subprocess.run(["curl", "-sS", "-m", "60", "-A", "Mozilla/5.0", "-r", "0-0", "-D", "-", "-o", os.devnull, url],
                             capture_output=True, text=True).stdout
        if out.strip():
            break
        print(f"   (tentativa {i + 1} sem resposta; refazendo)")
        time.sleep(5)
    st, h = 0, {}
    for ln in out.splitlines():
        ln = ln.strip()
        if ln.upper().startswith("HTTP/"):
            st = int(ln.split()[1])
        elif ":" in ln:
            k, v = ln.split(":", 1)
            h[k.strip().lower()] = v.strip()
    tam = h.get("content-range", "").split("/")[-1]
    return st, h.get("etag", ""), h.get("last-modified", ""), tam


agora = datetime.datetime.now().isoformat(timespec="seconds")
ctrl = {}
if os.path.exists(CTRL):
    ctrl = {r["recurso"]: r for r in csv.DictReader(open(CTRL, encoding="utf-8-sig"), delimiter=";")}

url = URL % ANO
st, etag, lm, tam = probe(url)
if st not in (200, 206):
    sys.exit(f"ERRO: sonda do ano {ANO} devolveu HTTP {st}; alerta, sem alterar fonte_controle")
chave = f"censo_superior_{ANO}"
ant = ctrl.get(chave)
if ant is None:
    decisao = "PRIMEIRA CARGA -> segue para download"
    mudou = True
elif ant["etag"] != etag or ant["last_modified"] != lm or ant["tamanho_bytes"] != tam:
    decisao = "MUDOU -> segue para download"
    mudou = True
else:
    decisao = "SEM MUDANCA -> encerra sem baixar nada"
    mudou = False
print(f"[{ANO}] HTTP {st} | ETag {etag} | Last-Modified {lm} | tamanho {tam}")
print("Decisao:", decisao)

# sonda do ano seguinte (censo novo?)
st2, e2, l2, t2 = probe(URL % (ANO + 1))
print(f"[{ANO + 1}] HTTP {st2} ->", "CENSO NOVO DISPONIVEL: avisar" if st2 in (200, 206) else "ainda nao publicado")

# etapa 8: so grava o novo estado se a carga fechou OK (aqui simulado: grava na primeira vez e quando muda)
FALHA = "--falha" in sys.argv  # simula uma carga que falhou depois do check
if mudou and FALHA:
    print("Carga FALHOU (simulado): etapa 8 NAO roda -> etag/last_modified guardados nao sao atualizados; o proximo ciclo tenta de novo")
    if ant is not None:
        ant["ultima_verificacao"] = agora
elif mudou:
    ctrl[chave] = {"fonte": "INEP", "recurso": chave, "url": url, "etag": etag, "last_modified": lm, "tamanho_bytes": tam,
                   "ultima_verificacao": agora, "ultima_mudanca": agora, "status": "ok"}
else:
    ctrl[chave]["ultima_verificacao"] = agora
ctrl[f"censo_superior_{ANO + 1}"] = {"fonte": "INEP", "recurso": f"censo_superior_{ANO + 1}", "url": URL % (ANO + 1),
                                    "etag": e2 if st2 in (200, 206) else "",
                                    "last_modified": l2 if st2 in (200, 206) else "",
                                    "tamanho_bytes": t2 if st2 in (200, 206) else "", "ultima_verificacao": agora, "ultima_mudanca": "",
                                    "status": "publicado" if st2 in (200, 206) else "nao_publicado"}
with open(CTRL, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS, delimiter=";")
    w.writeheader()
    w.writerows(ctrl.values())

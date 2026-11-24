"""
Passo 0 da orquestração: decide O QUE baixar, sem baixar os dados.

Para cada recurso calcula uma "impressão digital" pelo método mais barato que a fonte oferece
(resultado de scripts/probe_identificadores_mudanca.py) e compara com o checkpoint anterior:

  http        ETag / Last-Modified / Content-Length via HEAD (arquivos ZIP: IBGE FTP, INEP)
  zip_crc     CRC32 de cada arquivo dentro do ZIP remoto, lido por HTTP Range (ANATEL, 1 GB -> ~0,6 s)
  ckan        resource_show -> hash (MD5 do arquivo) + last_modified (BNDES, ANEEL datastore)
  ibge_per    /agregados/{id}/periodos -> data de modificação de cada período (SIDRA não manda ETag)
  siconfi     extrato_entregas -> data_status de cada entregável do ente (DCA, RREO...)
  hash_corpo  SHA-256 do corpo (endpoints pequenos sem validador: localidades, malhas)
  novo_ano    HEAD na URL do próximo ano/edição (descobre publicação nova com URL nova)

Uso:  py -3.12 scripts/etl_verificar_mudanca.py [arquivo_estado]
Estado local (teste): orquestracao/estado_checkpoint.json  -> na VPS vira a tabela etl.checkpoint.
Saída: lista de recursos a processar, com o escopo exato (ex.: só os períodos IBGE alterados,
só os municípios cujo DCA foi reenviado) e o motivo. Código de saída 0 = nada mudou, 10 = há trabalho.
"""
import hashlib, json, ssl, subprocess, sys, datetime as dt, warnings
from pathlib import Path
import requests, urllib3

warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)
ROOT = Path(__file__).resolve().parent.parent
ESTADO = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "orquestracao" / "estado_checkpoint.json"
AGORA = dt.datetime.now().isoformat(timespec="seconds")
IBGE = "https://servicodados.ibge.gov.br/api"
SICONFI = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ANEEL_HOST, ANEEL_IP = "dadosabertos.aneel.gov.br", "200.198.220.169"
UA = {"User-Agent": "painel-territorial-cti-etl/1.0"}

# Catálogo de recursos: id, método, parâmetros. Na VPS isto vive em etl.recurso.
RECURSOS = [
    dict(id="ibge_localidades_ba", metodo="hash_corpo", url=f"{IBGE}/v1/localidades/estados/29/municipios"),
    dict(id="ibge_malhas_metadados_ba", metodo="hash_corpo", url=f"{IBGE}/v3/malhas/estados/29/metadados?intrarregiao=municipio"),
    dict(id="ibge_6579_populacao", metodo="ibge_per", agregado=6579),
    dict(id="ibge_5938_pib", metodo="ibge_per", agregado=5938),
    dict(id="ibge_4709_censo", metodo="ibge_per", agregado=4709),
    dict(id="ibge_pib_municipios_txt", metodo="http",
         url="https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip"),
    dict(id="ibge_pib_municipios_proxima_edicao", metodo="novo_ano",
         url="https://ftp.ibge.gov.br/Pib_Municipios/2023_2024/"),
    dict(id="inep_censo_superior_2024", metodo="http",
         url="https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2024.zip"),
    dict(id="inep_censo_superior_2025", metodo="novo_ano",
         url="https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2025.zip"),
    dict(id="anatel_bl_fixa_zip", metodo="zip_crc",
         url="https://www.anatel.gov.br/dadosabertos/paineis_de_dados/acessos/acessos_banda_larga_fixa.zip"),
    dict(id="aneel_decfec_zip", metodo="ckan", aneel=True, resource_id="4493985c-baea-429c-9df5-3030422c71d7"),
    dict(id="aneel_indger", metodo="ckan", aneel=True, resource_id="fd10c9d4-cb76-4020-a322-e79afb13eaf7"),
    dict(id="aneel_siga", metodo="ckan", aneel=True, resource_id="11ec447d-698d-4ab8-977f-b424d5deee6a"),
    dict(id="aneel_ped", metodo="ckan", aneel=True, resource_id="3a7aee00-b6ee-4913-9670-f6b60f4a7bea"),
    dict(id="bndes_nao_automaticas", metodo="ckan", resource_id="6f56b78c-510f-44b6-8274-78a5b7e931f4"),
    dict(id="bndes_indiretas_automaticas", metodo="ckan", resource_id="612faa0b-b6be-4b2c-9317-da5dc2c0b901"),
    # Na VPS: um por ente (417). Aqui, uma amostra para o teste.
    dict(id="siconfi_entregas_2025", metodo="siconfi", ano=2025, entes=[2927408, 2910800, 2905701]),
]


class NoSNIAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *a, **kw):
        ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        kw["ssl_context"] = ctx; kw["server_hostname"] = None
        return super().init_poolmanager(*a, **kw)


S = requests.Session(); S.headers.update(UA)
SA = requests.Session(); SA.headers.update({**UA, "Host": ANEEL_HOST}); SA.mount("https://", NoSNIAdapter())


def head(url):
    """HEAD com fallback para curl (o INEP manda cadeia de certificados incompleta, que o certifi rejeita)."""
    try:
        r = S.head(url, timeout=60, allow_redirects=True)
        return r.status_code, {k.lower(): v for k, v in r.headers.items()}
    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
        out = subprocess.run(["curl", "-sI", "-L", url], capture_output=True, text=True, timeout=60).stdout
        blocos = [b for b in out.replace("\r", "").split("\n\n") if b.strip()]
        linhas = blocos[-1].splitlines()
        hd = {l.split(":", 1)[0].lower(): l.split(":", 1)[1].strip() for l in linhas[1:] if ":" in l}
        return int(linhas[0].split()[1]), hd


def digital(r):
    m = r["metodo"]
    if m == "http":
        st, hd = head(r["url"])
        return dict(etag=hd.get("etag"), last_modified=hd.get("last-modified"), tamanho=hd.get("content-length")), {}
    if m == "novo_ano":
        st, _ = head(r["url"])
        return dict(publicado=st < 400), {}
    if m == "hash_corpo":
        b = S.get(r["url"], timeout=120).content
        return dict(sha256=hashlib.sha256(b).hexdigest(), bytes=len(b)), {}
    if m == "ibge_per":
        per = S.get(f"{IBGE}/v3/agregados/{r['agregado']}/periodos", timeout=60).json()
        return {p["id"]: p["modificacao"] for p in per}, {}
    if m == "ckan":
        if r.get("aneel"):
            j = SA.get(f"https://{ANEEL_IP}/api/3/action/resource_show?id={r['resource_id']}", verify=False, timeout=60).json()
        else:
            j = S.get(f"https://dadosabertos.bndes.gov.br/api/3/action/resource_show?id={r['resource_id']}", timeout=60).json()
        res = j["result"]
        return dict(hash=res.get("hash"), last_modified=res.get("last_modified"), size=res.get("size")), {}
    if m == "siconfi":
        d = {}
        for ente in r["entes"]:
            for i in S.get(f"{SICONFI}/extrato_entregas?id_ente={ente}&an_referencia={r['ano']}", timeout=60).json()["items"]:
                if "Prefeitura" in i["instituicao"] and i["entregavel"] in ("Balanço Anual (DCA)", "Relatório Resumido de Execução Orçamentária"):
                    d[f"{ente}|{i['entregavel']}|{i['periodo']}"] = i["data_status"]
        return d, {}
    if m == "zip_crc":
        # Lê só o diretório central do ZIP por HTTP Range: CRC32 de cada arquivo interno, sem baixar o ZIP
        sys.path.insert(0, str(ROOT / "scripts")); import httpzip
        return {i.filename: f"{i.CRC:08x}" for i in httpzip.open_remote_zip(r["url"]).infolist()}, {}
    raise ValueError(m)


def escopo(r, antes, agora):
    """O que exatamente mudou -> escopo da carga (e da exclusão) incremental."""
    if r["metodo"] in ("ibge_per", "siconfi", "zip_crc"):
        return sorted(k for k in agora if antes.get(k) != agora[k]) + [f"REMOVIDO:{k}" for k in antes if k not in agora]
    return ["recurso inteiro"]


estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
trabalho = []
for r in RECURSOS:
    try:
        fp, _ = digital(r)
    except Exception as e:
        print(f"  ERRO   {r['id']:36} {type(e).__name__}: {str(e)[:90]}")
        continue
    ant = estado.get(r["id"], {}).get("digital")
    if r["metodo"] == "novo_ano" and not fp["publicado"]:
        situacao, esc = "aguardando", []
    elif ant is None:
        situacao, esc = "NOVO", ["carga inicial"]
    elif ant == fp:
        situacao, esc = "igual", []
    else:
        situacao, esc = "MUDOU", escopo(r, ant, fp)
    if situacao in ("NOVO", "MUDOU"):
        trabalho.append(dict(recurso=r["id"], situacao=situacao, escopo=esc))
    estado[r["id"]] = dict(digital=fp, verificado_em=AGORA,
                           alterado_em=AGORA if situacao in ("NOVO", "MUDOU") else estado.get(r["id"], {}).get("alterado_em"))
    print(f"  {situacao:6} {r['id']:36} {r['metodo']:10} {'; '.join(esc)[:80]}")

ESTADO.parent.mkdir(exist_ok=True)
ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n{len(trabalho)} recurso(s) a processar. Estado salvo em {ESTADO.relative_to(ROOT)}")
sys.exit(10 if trabalho else 0)

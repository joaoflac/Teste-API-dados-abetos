"""Simulação (Python, só stdlib) da lógica das etapas 4b a 7 do desenho em PLANO.md §9c.
NÃO é o Hop: valida as regras e os números e gera as tabelas esperadas em CSV.
Uso: python -I simular_orquestracao.py
"""
import csv, collections, sys, json, gzip, urllib.request, datetime

sys.stdout.reconfigure(encoding="utf-8")
IN = r"C:\Users\joao.vinicius\dados-inep\2024" + "\\"
OUT = r"C:\Users\joao.vinicius\Desktop\Teste-API-dados-abetos\automacao-hop-postgres\simulacao" + "\\"
REGRA = r"C:\Users\joao.vinicius\Desktop\Teste-API-dados-abetos\automacao-hop-postgres\analise\regra_cti_rotulos.csv"
P = {"ano": "2024", "uf": "29", "modalidade": "1", "exigir_sede_ba": True}  # controle.parametro
CTI_AREAS = {"05", "06", "07", "08", "09"}
CAT = {"1": "Pública Federal", "2": "Pública Estadual", "3": "Pública Municipal", "4": "Privada com fins lucrativos",
       "5": "Privada sem fins lucrativos", "7": "Especial"}
ORG = {"1": "Universidade", "2": "Centro Universitário", "3": "Faculdade", "4": "Instituto Federal", "5": "CEFET"}
GRAU = {"1": "Bacharelado", "2": "Licenciatura", "3": "Tecnológico", "4": "Bacharelado e Licenciatura"}
REDE = {"1": "Pública", "2": "Privada"}
NIVEL = {"05": "CT&I núcleo (STEM)", "06": "CT&I núcleo (STEM)", "07": "CT&I núcleo (STEM)",
         "08": "CT&I ampliado", "09": "CT&I ampliado"}


def w(nome, cols, rows):
    with open(OUT + nome, "w", encoding="utf-8-sig", newline="") as f:
        x = csv.writer(f, delimiter=";")
        x.writerow(cols)
        x.writerows(rows)


# pré-requisitos: 417 municípios do IBGE e a tabela regra_cti
req = urllib.request.Request("https://servicodados.ibge.gov.br/api/v1/localidades/estados/29/municipios",
                             headers={"Accept-Encoding": "identity", "User-Agent": "Mozilla/5.0"})
b = urllib.request.urlopen(req, timeout=90).read()
if b[:2] == bytes([0x1F, 0x8B]):
    b = gzip.decompress(b)
COD417 = {str(m["id"]) for m in json.loads(b)}
regra = {r["co_cine_rotulo"]: r["status_proposto"]
         for r in csv.DictReader(open(REGRA, encoding="utf-8-sig"), delimiter=";")}

# 4a) staging.inep_ies
ies = {r["CO_IES"]: r for r in csv.DictReader(open(IN + "MICRODADOS_ED_SUP_IES_2024.CSV", encoding="latin1", newline=""), delimiter=";")}

# 4b) staging.inep_cursos (streaming) com filtros 0-2 e limpeza
K_TOTAL = "0 linhas no arquivo (Brasil)"
K_ANO = "0 ano = parametro"
K_UF = "1 CO_UF = 29"
K_MUN = "2 municipio em 417"
K_EAD = "  (EAD descartado)"
K_PRES = "3 presencial"
K_ABI = "  (ABI: QT_CURSO = 0, vai para staging.inep_abi)"
K_Q1 = "4 QT_CURSO = 1"
K_CTI = "5 rotulo em regra_cti = incluir"
K_REV = "  (rotulo revisar -> pendencias)"
K_SEDE = "6 IES com sede na BA"
funil = collections.OrderedDict((k, 0) for k in [K_TOTAL, K_ANO, K_UF, K_MUN, K_EAD, K_PRES, K_ABI, K_Q1, K_CTI, K_REV, K_SEDE])
stg = []
for r in csv.DictReader(open(IN + "MICRODADOS_CADASTRO_CURSOS_2024.CSV", encoding="latin1", newline=""), delimiter=";"):
    funil[K_TOTAL] += 1
    if r["NU_ANO_CENSO"] != P["ano"]:
        continue
    funil[K_ANO] += 1
    if r["CO_UF"] != P["uf"]:
        continue
    funil[K_UF] += 1
    if r["CO_MUNICIPIO"] not in COD417:
        continue
    funil[K_MUN] += 1
    r["CO_CINE_ROTULO"] = r["CO_CINE_ROTULO"].replace('"', "").strip()  # aspas literais no campo
    stg.append(r)

# 5) portoes de qualidade
val = []


def gate(nome, ok, det):
    val.append((nome, "OK" if ok else "FALHOU", det))


pres_all = [r for r in stg if r["TP_MODALIDADE_ENSINO"] == P["modalidade"]]
dup = [k for k, v in collections.Counter(r["CO_CURSO"] for r in pres_all).items() if v > 1]
gate("co_ies nao nulo", all(r["CO_IES"] for r in stg), f"{sum(1 for r in stg if not r['CO_IES'])} nulos")
gate("todo co_ies existe em staging.inep_ies", all(r["CO_IES"] in ies for r in stg), f"{len({r['CO_IES'] for r in stg} - set(ies))} ausentes")
gate("co_curso unico (presenciais)", not dup, f"{len(dup)} duplicados")
gate("municipio em 417 (100%)", all(r["CO_MUNICIPIO"] in COD417 for r in stg), "0 fora")
val.append(("faixa de linhas vs ano anterior", "NAO_AVALIADO", "sem carga anterior (1a carga)"))
if any(v[1] == "FALHOU" for v in val):
    w("validacao.csv", ["gate", "resultado", "detalhe"], val)
    raise SystemExit("validacao falhou: producao intacta")

# 6) promover
funil[K_EAD] = sum(1 for r in stg if r["TP_MODALIDADE_ENSINO"] != P["modalidade"])
f3 = pres_all
funil[K_PRES] = len(f3)
abi = [r for r in f3 if r["QT_CURSO"] != "1"]
funil[K_ABI] = len(abi)
f4 = [r for r in f3 if r["QT_CURSO"] == "1"]
funil[K_Q1] = len(f4)


def decide(r):
    st = regra.get(r["CO_CINE_ROTULO"])
    if st in ("incluir", "excluir", "revisar"):
        return st
    # rotulo fora da tabela: nas areas 05-09 vai para triagem; nas demais areas o padrao e ficar fora
    return "nao_classificado" if r["CO_CINE_AREA_GERAL"] in CTI_AREAS else "excluir"


dec = [(r, decide(r)) for r in f4]
f5 = [r for r, d in dec if d == "incluir"]
rev = [r for r, d in dec if d == "revisar"]
nc = [r for r, d in dec if d == "nao_classificado"]
funil[K_CTI] = len(f5)
funil[K_REV] = len(rev)


def sede_ba(r):
    return ies[r["CO_IES"]]["CO_UF_IES"] == "29"


f6 = [r for r in f5 if sede_ba(r) or not P["exigir_sede_ba"]]
fora_sede = [r for r in f5 if not sede_ba(r)]
funil[K_SEDE] = len(f6)
hoje = datetime.date.today().isoformat()
ano = P["ano"]

# ies e ies_local: derivados dos cursos apos o filtro 4 (todas as areas); nunca apagados
cti_par = collections.Counter((r["CO_IES"], r["CO_MUNICIPIO"]) for r in f6)
cti_ies = collections.Counter(r["CO_IES"] for r in f6)
mun_por_ies = collections.defaultdict(set)
for r in f4:
    mun_por_ies[r["CO_IES"]].add(r["CO_MUNICIPIO"])
ies_ids = sorted(mun_por_ies, key=int)
rows = []
for c in ies_ids:
    i = ies[c]
    rows.append([c, i["NO_IES"], i["SG_IES"], i["CO_MANTENEDORA"], i["NO_MANTENEDORA"],
                 i["TP_CATEGORIA_ADMINISTRATIVA"], CAT.get(i["TP_CATEGORIA_ADMINISTRATIVA"], ""),
                 i["TP_ORGANIZACAO_ACADEMICA"], ORG.get(i["TP_ORGANIZACAO_ACADEMICA"], ""),
                 i["CO_MUNICIPIO_IES"], i["NO_MUNICIPIO_IES"], i["SG_UF_IES"],
                 len(mun_por_ies[c]), cti_ies.get(c, 0), ano, hoje, "true"])
w("ies.csv", ["co_ies", "no_ies", "sg_ies", "co_mantenedora", "no_mantenedora", "tp_categoria_administrativa",
              "categoria_administrativa", "tp_organizacao_academica", "organizacao_academica", "co_municipio_sede",
              "no_municipio_sede", "uf_sede", "qtd_municipios_oferta", "qtd_cursos_cti", "ultimo_ano_visto",
              "primeira_carga", "ativa"], rows)
pares = sorted({(r["CO_IES"], r["CO_MUNICIPIO"], r["NO_MUNICIPIO"]) for r in f4}, key=lambda x: (int(x[0]), x[1]))
w("ies_local.csv", ["co_ies", "sg_ies", "co_municipio", "no_municipio", "qtd_cursos_cti", "aparece_na_api",
                    "ultimo_ano_visto", "ativa"],
  [[c, ies[c]["SG_IES"], m, n, cti_par.get((c, m), 0), "true" if cti_par.get((c, m), 0) else "false", ano, "true"]
   for c, m, n in pares])

# curso: filtros 5 e 6
cols = ["co_curso", "co_ies", "co_municipio", "no_municipio", "no_curso", "co_cine_rotulo", "no_cine_rotulo",
        "co_cine_area_geral", "tipo_curso (no_cine_area_geral)", "nivel_cti", "tp_grau_academico", "grau_academico",
        "tp_rede", "rede", "tp_categoria_administrativa", "qt_vg_total", "qt_ing", "qt_mat", "qt_conc",
        "nu_ano_censo", "ativo"]
w("curso.csv", cols,
  [[r["CO_CURSO"], r["CO_IES"], r["CO_MUNICIPIO"], r["NO_MUNICIPIO"], r["NO_CURSO"], r["CO_CINE_ROTULO"],
    r["NO_CINE_ROTULO"], r["CO_CINE_AREA_GERAL"], r["NO_CINE_AREA_GERAL"], NIVEL.get(r["CO_CINE_AREA_GERAL"], ""),
    r["TP_GRAU_ACADEMICO"], GRAU.get(r["TP_GRAU_ACADEMICO"], ""), r["TP_REDE"], REDE.get(r["TP_REDE"], ""),
    r["TP_CATEGORIA_ADMINISTRATIVA"], r["QT_VG_TOTAL"], r["QT_ING"], r["QT_MAT"], r["QT_CONC"],
    r["NU_ANO_CENSO"], "true"]
   for r in sorted(f6, key=lambda r: (r["CO_CINE_AREA_GERAL"], r["CO_CINE_ROTULO"], r["NO_MUNICIPIO"], int(r["CO_CURSO"])))])

pend = ([(r, "rotulo_revisar") for r in rev] + [(r, "rotulo_novo_nao_classificado") for r in nc]
        + [(r, "ies_sede_fora_da_BA") for r in fora_sede])
w("pendencias_revisao.csv", ["motivo", "co_curso", "co_ies", "sg_ies", "uf_sede_ies", "no_curso", "no_municipio",
                             "co_cine_rotulo", "no_cine_rotulo", "grau_academico", "qt_mat"],
  [[m, r["CO_CURSO"], r["CO_IES"], ies[r["CO_IES"]]["SG_IES"], ies[r["CO_IES"]]["SG_UF_IES"], r["NO_CURSO"],
    r["NO_MUNICIPIO"], r["CO_CINE_ROTULO"], r["NO_CINE_ROTULO"], GRAU.get(r["TP_GRAU_ACADEMICO"], ""), r["QT_MAT"]]
   for r, m in sorted(pend, key=lambda x: (x[1], x[0]["NO_CURSO"]))])
w("abi_staging.csv", ["eh_abi", "co_curso", "co_ies", "sg_ies", "no_curso", "no_municipio", "co_cine_rotulo",
                      "no_cine_rotulo", "qt_vg_total", "qt_mat"],
  [["true", r["CO_CURSO"], r["CO_IES"], ies[r["CO_IES"]]["SG_IES"], r["NO_CURSO"], r["NO_MUNICIPIO"],
    r["CO_CINE_ROTULO"], r["NO_CINE_ROTULO"], r["QT_VG_TOTAL"], r["QT_MAT"]] for r in abi])
w("funil.csv", ["etapa", "linhas"], list(funil.items()))
gate("rotulos novos nas areas 05-09 sem regra", not nc, f"{len(nc)} cursos")
w("validacao.csv", ["gate", "resultado", "detalhe"], val)

print("FUNIL:")
for k, v in funil.items():
    print("  ", k, v)
print("ies:", len(ies_ids), "| ies_local:", len(pares),
      "(aparecem na API:", sum(1 for c, m, n in pares if cti_par.get((c, m), 0)), ") | curso:", len(f6),
      "| pendencias:", len(pend), dict(collections.Counter(m for _, m in pend)))
print("validacoes:", [(g, r) for g, r, d in val])

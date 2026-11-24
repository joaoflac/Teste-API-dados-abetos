"""
Monta a base municipal da Bahia a partir do IBGE: uma linha por município (417), chave `codigo_ibge`.
É a tabela-mestre (dimensão município) à qual as demais fontes (INEP, BNDES, SICONFI, ANATEL, ANEEL) se juntam.

Uso:  python scripts/ibge_base_municipal.py
Pré-requisito: amostras IBGE já geradas (gerar_amostras.py + ibge_pib_per_capita_oficial.py).
Busca na API apenas a hierarquia territorial (localidades) e a população do Censo 2022 (agregado 4709).
Saídas: base/ibge_base_municipal_BA.csv e base/ibge_base_municipal_BA_dicionario.csv
"""
import datetime as dt
from pathlib import Path
import requests, pandas as pd

ROOT = Path(__file__).resolve().parent.parent
AM, BASE = ROOT / "amostras", ROOT / "base"
BASE.mkdir(exist_ok=True)
HOJE = dt.date.today().isoformat()
U_LOC = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/29/municipios"
U_CENSO = "https://servicodados.ibge.gov.br/api/v3/agregados/4709/periodos/2022/variaveis/93?localidades=N6[N3[29]]"


def ler(nome):
    return pd.read_csv(AM / nome, encoding="utf-8-sig")


def g(d, *ks):  # acesso aninhado tolerante a None
    for k in ks:
        d = d.get(k) if isinstance(d, dict) else None
    return d


# 1. Identificação e hierarquia territorial (API de localidades)
loc = []
for m in requests.get(U_LOC, timeout=120).json():
    loc.append(dict(
        codigo_ibge=m["id"], municipio=m["nome"], uf="BA", codigo_uf=29,
        codigo_microrregiao=g(m, "microrregiao", "id"), microrregiao=g(m, "microrregiao", "nome"),
        codigo_mesorregiao=g(m, "microrregiao", "mesorregiao", "id"),
        mesorregiao=g(m, "microrregiao", "mesorregiao", "nome"),
        codigo_regiao_imediata=g(m, "regiao-imediata", "id"), regiao_imediata=g(m, "regiao-imediata", "nome"),
        codigo_regiao_intermediaria=g(m, "regiao-imediata", "regiao-intermediaria", "id"),
        regiao_intermediaria=g(m, "regiao-imediata", "regiao-intermediaria", "nome")))
base = pd.DataFrame(loc)

# 2. Território: área e centroide (malhas)
area = ler("ibge_2.4_area_centroide_BA.csv")[["codigo_ibge", "area_km2", "centroide_lon", "centroide_lat"]]
base = base.merge(area, on="codigo_ibge", how="left")

# 3. População: Censo 2022 (4709) + estimativas (6579), largas por ano
censo = []
for v in requests.get(U_CENSO, timeout=120).json():
    for r in v["resultados"]:
        for s in r["series"]:
            censo.append(dict(codigo_ibge=int(s["localidade"]["id"]),
                              populacao_censo_2022=pd.to_numeric(s["serie"]["2022"], errors="coerce")))
base = base.merge(pd.DataFrame(censo), on="codigo_ibge", how="left")
pop = ler("ibge_2.1_populacao_6579_BA.csv")
pw = pop.pivot(index="codigo_ibge", columns="ano_referencia", values="populacao")
pw.columns = [f"populacao_estimada_{a}" for a in pw.columns]
base = base.merge(pw.reset_index(), on="codigo_ibge", how="left")
ANO_POP = int(pop.ano_referencia.max())

# 4. Economia: PIB (5938, var 37) dos dois últimos anos
pib = ler("ibge_2.2_pib_vab_5938_BA.csv")
pib = pib[pib.variavel_id == 37]
ANO_PIB = int(pib.ano_referencia.max())
pw = pib.pivot(index="codigo_ibge", columns="ano_referencia", values="valor")
pw.columns = [f"pib_{a}_mil_reais" for a in pw.columns]
base = base.merge(pw.reset_index(), on="codigo_ibge", how="left")

# VAB por atividade: o IBGE não divulga VAB municipal para 2022–2023 (SIDRA e base TXT vêm com "..."/vazio),
# então busca o último ano com VAB publicado (hoje 2021).
VARS = {498: "vab_total", 513: "vab_agropecuaria", 517: "vab_industria", 6575: "vab_servicos",
        525: "vab_adm_publica", 543: "impostos_liquidos"}
U_VAB = ("https://servicodados.ibge.gov.br/api/v3/agregados/5938/periodos/-6/variaveis/"
         + "|".join(map(str, VARS)) + "?localidades=N6[N3[29]]")
vab = []
for v in requests.get(U_VAB, timeout=300).json():
    for r in v["resultados"]:
        for s in r["series"]:
            for ano, val in s["serie"].items():
                vab.append(dict(codigo_ibge=int(s["localidade"]["id"]), var=int(v["id"]), ano=int(ano),
                                valor=pd.to_numeric(val, errors="coerce")))
vab = pd.DataFrame(vab).dropna(subset=["valor"])
ANO_VAB = int(vab.ano.max())
vw = vab[vab.ano == ANO_VAB].pivot(index="codigo_ibge", columns="var", values="valor").rename(columns=VARS)
vw = vw[list(VARS.values())]
vw.columns = [f"{c}_{ANO_VAB}_mil_reais" for c in vw.columns]
base = base.merge(vw.reset_index(), on="codigo_ibge", how="left")

# 5. PIB per capita oficial (base TXT do PIB dos Municípios)
ppc = ler(f"ibge_2.3_pib_per_capita_oficial_BA_{ANO_PIB}.csv")[["codigo_ibge", "pib_per_capita_reais"]]
base = base.merge(ppc.rename(columns={"pib_per_capita_reais": f"pib_per_capita_{ANO_PIB}_reais"}),
                  on="codigo_ibge", how="left")

# 6. Derivados
pib_ult, vab_tot = base[f"pib_{ANO_PIB}_mil_reais"], base[f"vab_total_{ANO_VAB}_mil_reais"]
base[f"densidade_demografica_{ANO_POP}_hab_km2"] = (base[f"populacao_estimada_{ANO_POP}"] / base.area_km2).round(2)
base[f"pib_por_km2_{ANO_PIB}_mil_reais"] = (pib_ult / base.area_km2).round(2)
for setor in ["agropecuaria", "industria", "servicos", "adm_publica"]:
    base[f"part_vab_{setor}_{ANO_VAB}_pct"] = (base[f"vab_{setor}_{ANO_VAB}_mil_reais"] / vab_tot * 100).round(2)
base["fonte"] = "IBGE (localidades v1, malhas v3, agregados 4709/6579/5938, PIB dos Municípios)"
base["data_montagem"] = HOJE
base = base.sort_values("codigo_ibge")

# Checagens
assert len(base) == 417 and base.codigo_ibge.is_unique, f"esperado 417 municípios únicos, veio {len(base)}"
nulos = base.isna().sum()
if nulos.any():
    print("Atenção, colunas com nulos:\n", nulos[nulos > 0])

base.to_csv(BASE / "ibge_base_municipal_BA.csv", index=False, encoding="utf-8-sig")
print(f"-> base/ibge_base_municipal_BA.csv ({len(base)} linhas, {base.shape[1]} colunas)")

# Dicionário de dados
GRUPO = [("codigo_ibge", "Chave", "Código IBGE do município (7 dígitos) — chave de junção com as demais fontes", U_LOC)]
for c in base.columns[1:]:
    if c in ("municipio", "uf", "codigo_uf"):
        GRUPO.append((c, "Identificação", "Nome/UF do município", U_LOC))
    elif "regiao" in c:
        GRUPO.append((c, "Hierarquia territorial", "Divisão regional IBGE (2017: imediata/intermediária; antiga: micro/meso)", U_LOC))
    elif c in ("area_km2", "centroide_lon", "centroide_lat"):
        GRUPO.append((c, "Território", "Área (km²) e centroide (WGS84) da malha municipal", "api/v3/malhas/estados/29/metadados"))
    elif c.startswith("populacao_censo"):
        GRUPO.append((c, "Demografia", "População residente — Censo 2022 (agregado 4709, var 93)", U_CENSO))
    elif c.startswith("populacao_estimada"):
        GRUPO.append((c, "Demografia", "População residente estimada (agregado 6579, var 9324)", "agregado 6579"))
    elif c.startswith("pib_per_capita"):
        GRUPO.append((c, "Economia", "PIB per capita oficial (R$)", "ftp PIB dos Municípios (base TXT)"))
    elif c.startswith(("pib_", "vab_", "impostos")) and "km2" not in c:
        GRUPO.append((c, "Economia", "PIB/VAB a preços correntes (mil R$) — agregado 5938. VAB municipal "
                      f"só publicado até {ANO_VAB}", "agregado 5938"))
    elif c.startswith(("densidade", "pib_por_km2", "part_vab")):
        GRUPO.append((c, "Derivado", "Calculado: densidade = pop/área; PIB/km²; participação % do setor no VAB total", "derivado"))
    else:
        GRUPO.append((c, "Metadado", "Proveniência da linha", ""))
pd.DataFrame(GRUPO, columns=["coluna", "grupo", "descricao", "origem"]).to_csv(
    BASE / "ibge_base_municipal_BA_dicionario.csv", index=False, encoding="utf-8-sig")
print("-> base/ibge_base_municipal_BA_dicionario.csv")

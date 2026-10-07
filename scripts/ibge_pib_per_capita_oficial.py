"""
IBGE 2.3 — PIB per capita municipal oficial (PIB dos Municípios), último ano publicado, Bahia.

A tabela SIDRA 6784 só tem nível Brasil e a 6579 não tem população de 2023, então o PIB per capita
municipal vem da base oficial em TXT de largura fixa (ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/).

Uso:  python ibge_pib_per_capita_oficial.py [ano] [pasta_cache]   (padrão: 2023, ./cache)
Só biblioteca padrão.

Saídas (amostras/):
  ibge_2.3_pib_per_capita_oficial_BA_<ano>.csv        417 municípios: PIB (mil R$), PIB per capita (R$), população implícita
  ibge_2.3_2.5_2.6_derivados_amostra_BA.csv          reescrito só com o <ano>, usando o PIB per capita oficial
"""
import csv, sys, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AM = ROOT / "amostras"
ANO = sys.argv[1] if len(sys.argv) > 1 else "2023"
CACHE = Path(sys.argv[2] if len(sys.argv) > 2 else "cache")
URL = "https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip"
# Posições no TXT (largura fixa, latin1), conferidas contra o PIB da SIDRA 5938
P_COD, P_PIB, P_PC = 46, slice(930, 960), slice(955, 980)


def ler_csv(nome):
    with open(AM / nome, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def salvar(linhas, nome):
    with open(AM / nome, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(f"  -> amostras/{nome} ({len(linhas)} linhas)")


arq = CACHE / "ibge_pib_municipios_2010_2023_txt.zip"
if not arq.exists():
    CACHE.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(URL, arq)
z = zipfile.ZipFile(arq)
txt = next(n for n in z.namelist() if n.endswith(".txt"))

of = {}
for l in z.open(txt).read().decode("latin1").splitlines():
    if l[:4] == ANO and l[P_COD:P_COD + 2] == "29":
        cod = l[P_COD:P_COD + 7]
        pib, pc = float(l[P_PIB]), float(l[P_PC])
        of[cod] = dict(codigo_ibge=cod, municipio=l[P_COD + 8:P_COD + 48].strip(), ano_referencia=ANO,
                       pib_mil_reais=pib, pib_per_capita_reais=pc,
                       populacao_implicita=round(pib * 1000 / pc), fonte="IBGE PIB dos Municípios (base TXT oficial)",
                       url_fonte=URL)
assert len(of) == 417, f"esperado 417 municípios BA, achei {len(of)}"
salvar(sorted(of.values(), key=lambda r: r["municipio"]), f"ibge_2.3_pib_per_capita_oficial_BA_{ANO}.csv")

# Reescreve a amostra de derivados só com o ano oficial
area = {r["codigo_ibge"]: float(r["area_km2"]) for r in ler_csv("ibge_2.4_area_centroide_BA.csv")}
pop = {}
for r in ler_csv("ibge_2.1_populacao_6579_BA.csv"):
    if r["codigo_ibge"] not in pop or r["ano_referencia"] > pop[r["codigo_ibge"]][1]:
        pop[r["codigo_ibge"]] = (int(r["populacao"]), r["ano_referencia"])
amostra = {r["codigo_ibge"] for r in ler_csv("ibge_2.3_2.5_2.6_derivados_amostra_BA.csv")}
der = []
for cod in sorted(amostra, key=lambda c: of[c]["municipio"]):
    o, a, (p, ano_p) = of[cod], area[cod], pop[cod]
    der.append(dict(codigo_ibge=cod, municipio=o["municipio"], ano_referencia=ANO, pib_mil_reais=o["pib_mil_reais"],
                    pib_per_capita_reais=o["pib_per_capita_reais"], fonte_pib_per_capita="IBGE PIB dos Municípios (oficial)",
                    area_km2=a, pib_por_km2_mil_reais=round(o["pib_mil_reais"] / a, 2),
                    populacao_ultimo_ano=p, ano_populacao=ano_p, densidade_demografica_hab_km2=round(p / a, 2)))
salvar(der, "ibge_2.3_2.5_2.6_derivados_amostra_BA.csv")

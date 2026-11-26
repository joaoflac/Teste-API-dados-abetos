"""
Teste do cruzamento aproximado de nomes de município (orquestrador_apl.aproximado). Só leitura: usa ibge.municipio.
Rodar:  python orquestracao/testes/07_teste_aproximacao.py [--xlsx "Lista APLs_outubro2022_publico.xlsx"]

1. Casos reais da planilha do Observatório APL (out/2022): os 15 erros de digitação caem no município certo;
   "Capela" e "Tancredo Neves" são recusados (ficam no de-para; "Capela" iria para Caravelas, errado).
2. Estresse: 4 erros sintéticos por município (falta, sobra, troca e inversão de letra), semente fixa.
   Exige ZERO casamento errado; recusar é aceitável (a carga para e pede o de-para), errar não é.
   Medido em 26/11 com 0,80/0,10: 1.538 acertos, 128 recusas, 0 erros. Com folga 0,05 seriam 97% de acerto, mas "Capela" passaria.
3. De-para (PLANEJAMENTO_APL.md §4): exatamente as entradas decididas; cada uma aponta para município existente e é NECESSÁRIA
   (nem o nome exato nem a aproximação a resolvem). Entrada que a aproximação já resolve é redundante e deve sair.
4. Dados reais (só com --xlsx): cruzamento da planilha (exato > de-para > aproximado) x gabarito do Supabase
   (testes/dados/apl_gabarito_supabase.csv, montado à mão pelo consultor). Aproximado e de-para nunca divergem do gabarito;
   as únicas divergências aceitas são os 2 APLs de cacau (listas trocadas NO SUPABASE) e Capela (ausente do Supabase).
"""
import csv, collections, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import psycopg
from orquestrador_apl import DE_PARA, aproximado, chave_nome, espacos, ler_xlsx, texto
from orquestrador_simulado import dsn

with psycopg.connect(dsn()) as c:
    mun = {chave_nome(n): k for k, n in c.execute("SELECT codigo_ibge, municipio FROM ibge.municipio")}
assert len(mun) == 417, "ibge.municipio incompleta"

REAIS = {"Itaroro": 2917102, "Santa Cruz da Viotria": 2927804, "Monte Santos": 2921500, "Barra do Choças": 2902906,
         "Encruzilhada Bahia": 2910404, "Porções": 2925105, "Morro do Chapel": 2921708, "Milo Peçanha": 2922607,
         "Belos Campos": 2903508, "Quinjengue": 2925907, "Catité": 2905206, "Jacuruçu": 2918456, "Manoel Viitorino": 2920403,
         "Iritinga": 2903607, "Mari": 2920106, "Capela": None, "Tancredo Neves": None}
for nome, esperado in REAIS.items():
    assert aproximado(chave_nome(nome), mun) == esperado, f"{nome}: esperado {esperado}"
print(f"1. casos reais: {len(REAIS)} ok")

rnd, AZ = random.Random(26), "abcdefghijklmnopqrstuvwxyz"
def erro(s, t):
    i = rnd.randrange(len(s))
    if t == 0: return s[:i] + s[i + 1:]
    if t == 1: return s[:i] + rnd.choice(AZ) + s[i:]
    if t == 2: return s[:i] + rnd.choice(AZ.replace(s[i], "")) + s[i + 1:]
    i = min(i, len(s) - 2); return s[:i] + s[i + 1] + s[i] + s[i + 2:]

acertos = recusas = 0; errados = []
for k, cod in mun.items():
    for t in range(4):
        e = erro(k, t)
        if e in mun:
            continue          # o erro formou outro nome real: casa exato, nenhum método percebe (limite conhecido)
        got = aproximado(e, mun)
        if got == cod: acertos += 1
        elif got is None: recusas += 1
        else: errados.append((e, k))
assert not errados, f"casamentos ERRADOS: {errados[:10]}"
assert acertos >= 0.9 * (acertos + recusas), f"acerto caiu: {acertos} de {acertos + recusas}"
print(f"2. estresse: {acertos} acertos, {recusas} recusas, 0 erros ({acertos / (acertos + recusas):.0%})")

DECIDIDO = {"Tancredo Neves": 2925758, "Capela": 2906857}
de_para = {l["nome_planilha"]: int(l["codigo_ibge"]) for l in csv.DictReader(open(DE_PARA, encoding="utf-8"), delimiter=";")}
assert de_para == DECIDIDO, f"de-para diferente do decidido: {de_para}"
for n, cod in de_para.items():
    assert cod in mun.values(), f"{n}: código {cod} não existe em ibge.municipio"
    assert chave_nome(n) not in mun and aproximado(chave_nome(n), mun) is None, f"{n}: redundante, o cruzamento automático já resolve"
print(f"3. de-para: {len(de_para)} entradas, todas válidas e necessárias")

if "--xlsx" in sys.argv:
    gab, sede = collections.defaultdict(set), {}
    for l in csv.DictReader(open(Path(__file__).parent / "dados" / "apl_gabarito_supabase.csv", encoding="utf-8"), delimiter=";"):
        gab[chave_nome(l["entidade"])].add(mun[chave_nome(l["municipio"])]); sede[chave_nome(l["sede"])] = chave_nome(l["entidade"])
    cont, diverge = collections.Counter(), []
    for l in ler_xlsx(sys.argv[sys.argv.index("--xlsx") + 1]):
        if espacos(l.get("Estado*")) != "BA":
            continue
        apl = chave_nome(l["Nome do APL*"]); apl = apl if apl in gab else sede[chave_nome(l["Cidade Polo*"])]   # 2 renomeados no Supabase
        for n in (l["Municípios que compõem o APL*"] or "").replace(",", ";").split(";"):
            if not texto(n):
                continue
            k = chave_nome(n)
            cod, met = (mun[k], "exato") if k in mun else (de_para[espacos(n)], "de_para") if espacos(n) in de_para else (aproximado(k, mun), "aproximado")
            cont[met] += 1
            if cod not in gab[apl]:
                diverge.append((met, espacos(n), espacos(l["Nome do APL*"])))
    assert all(m == "exato" and "cacau" in a.lower() for m, n, a in diverge if n != "Capela"), f"divergência inesperada: {diverge}"
    assert sum(1 for m, *_ in diverge if m != "exato") == 1, "só Capela (de-para) pode faltar no gabarito"
    print(f"4. dados reais: {dict(cont)}; divergências só as conhecidas ({len(diverge)}: 10 do cacau no Supabase + Capela)")

"""
Gera as amostras de dados de cada fonte do catálogo e as tabelas de categorias/filtros CT&I.

Uso:  python gerar_amostras.py <pasta_cache>
A pasta de cache deve conter os arquivos baixados por bndes_download_ba.py, siconfi_dca_ba.py,
o ZIP do INEP 2024 extraído e os CSVs da ANATEL (ver README em RESULTADOS_AMOSTRAGEM.md).
"""
import re, sys, json, datetime as dt
from pathlib import Path
import requests, pandas as pd

CACHE = Path(sys.argv[1] if len(sys.argv) > 1 else "cache")
ROOT = Path(__file__).resolve().parent.parent
AM, CAT = ROOT / "amostras", ROOT / "categorias_cti"
AM.mkdir(exist_ok=True); CAT.mkdir(exist_ok=True)
HOJE = dt.date.today().isoformat()
UF_BA = "29"
# Municípios de referência para amostras (capital, polos regionais e municípios pequenos)
AMOSTRA_MUN = [2927408, 2910800, 2933307, 2905701, 2913606, 2918407, 2903201, 2919207,
               2914802, 2925303, 2906006, 2932903, 2901106, 2907202, 2930709]
status = []  # status de validação por indicador


def salvar(df, pasta, nome):
    df.to_csv(pasta / nome, index=False, encoding="utf-8-sig")
    print(f"  -> {pasta.name}/{nome} ({len(df)} linhas)")


def reg(fonte, indicador, st, linhas, url, obs=""):
    status.append(dict(fonte=fonte, indicador=indicador, status_validacao=st, linhas_retornadas=linhas,
                       url_testada=url, data_coleta=HOJE, observacao=obs))


# ----------------------------------------------------------------------------- IBGE
def ibge():
    print("IBGE")
    A = "https://servicodados.ibge.gov.br/api/v3/agregados"
    mun = pd.DataFrame(requests.get(
        "https://servicodados.ibge.gov.br/api/v1/localidades/estados/29/municipios", timeout=120).json())
    mun = mun.rename(columns={"id": "codigo_ibge", "nome": "municipio"})[["codigo_ibge", "municipio"]]

    def agregado(tab, var, per, cls=""):
        url = f"{A}/{tab}/periodos/{per}/variaveis/{var}?localidades=N6[N3[{UF_BA}]]{cls}"
        out = []
        for v in requests.get(url, timeout=300).json():
            for res in v["resultados"]:
                for s in res["series"]:
                    for ano, val in s["serie"].items():
                        out.append(dict(codigo_ibge=int(s["localidade"]["id"]), variavel_id=v["id"],
                                        variavel=v["variavel"], unidade=v["unidade"], ano_referencia=int(ano),
                                        valor=pd.to_numeric(val, errors="coerce")))
        return pd.DataFrame(out), url

    # 2.1 População (6579/9324) — último ano disponível
    pop, u_pop = agregado(6579, 9324, "-3")
    pop = pop.merge(mun, on="codigo_ibge").assign(uf="BA", fonte="IBGE/SIDRA agregado 6579", url_fonte=u_pop,
                                                   data_coleta=HOJE)
    salvar(pop.rename(columns={"valor": "populacao"}), AM, "ibge_2.1_populacao_6579_BA.csv")
    n = pop[pop.ano_referencia == pop.ano_referencia.max()].codigo_ibge.nunique()
    reg("IBGE", "2.1 População municipal residente", "Validado", n, u_pop,
        f"{n} municípios no ano {pop.ano_referencia.max()}; 6579 não tem 2007, 2010, 2022 e 2023 (anos de Censo/contagem)")

    # 2.2 PIB (5938) — PIB + VAB setoriais (a tabela não tem classificação CT&I)
    vars_pib = "37|498|513|517|6575|525|543"
    pib, u_pib = agregado(5938, vars_pib, "-2")
    pib = pib.merge(mun, on="codigo_ibge").assign(uf="BA", fonte="IBGE/SIDRA agregado 5938", url_fonte=u_pib,
                                                   data_coleta=HOJE)
    salvar(pib, AM, "ibge_2.2_pib_vab_5938_BA.csv")
    n = pib[pib.variavel_id == "37"].codigo_ibge.nunique()
    reg("IBGE", "2.2 PIB municipal", "Validado", n, u_pib,
        f"PIB (var 37, mil R$) + VAB por atividade; último ano {pib.ano_referencia.max()}")

    # 2.4 Área e centroide (malhas/metadados)
    u_area = "https://servicodados.ibge.gov.br/api/v3/malhas/estados/29/metadados?intrarregiao=municipio"
    meta = requests.get(u_area, timeout=300).json()
    area = pd.DataFrame([dict(codigo_ibge=int(m["id"]), area_km2=float(m["area"]["dimensao"]),
                              centroide_lon=m["centroide"]["longitude"], centroide_lat=m["centroide"]["latitude"])
                         for m in meta if m.get("area")])
    if len(area) < 400:  # fallback: um a um
        area = pd.DataFrame([dict(codigo_ibge=c, **(lambda m: dict(
            area_km2=float(m["area"]["dimensao"]), centroide_lon=m["centroide"]["longitude"],
            centroide_lat=m["centroide"]["latitude"]))(requests.get(
            f"https://servicodados.ibge.gov.br/api/v3/malhas/municipios/{c}/metadados", timeout=60).json()[0]))
            for c in mun.codigo_ibge])
        u_area = "https://servicodados.ibge.gov.br/api/v3/malhas/municipios/{codigo_ibge}/metadados"
    area = area.merge(mun, on="codigo_ibge").assign(uf="BA", fonte="IBGE Malhas v3", url_fonte=u_area,
                                                     data_coleta=HOJE)
    salvar(area, AM, "ibge_2.4_area_centroide_BA.csv")
    reg("IBGE", "2.4 Área territorial municipal", "Validado", len(area), u_area)

    # 2.7 Malha — conta features do GeoJSON (amostra sem geometria no CSV)
    u_geo = ("https://servicodados.ibge.gov.br/api/v3/malhas/estados/29?intrarregiao=municipio"
             "&formato=application/vnd.geo+json&qualidade=minima")
    gj = requests.get(u_geo, timeout=300).json()
    feats = pd.DataFrame([dict(codigo_ibge=int(f["properties"]["codarea"]), tipo_geometria=f["geometry"]["type"],
                               n_vertices_aprox=len(json.dumps(f["geometry"]["coordinates"]).split("],")))
                          for f in gj["features"]])
    salvar(feats.merge(mun, on="codigo_ibge").head(30), AM, "ibge_2.7_malha_amostra_BA.csv")
    reg("IBGE", "2.7 Malha geográfica municipal", "Validado", len(feats), u_geo,
        "GeoJSON com codarea = código IBGE; CSV traz só metadados da geometria")

    # Derivados 2.3 / 2.5 / 2.6
    p37 = pib[pib.variavel_id == "37"][["codigo_ibge", "ano_referencia", "valor"]].rename(columns={"valor": "pib_mil_reais"})
    # 6579 não tem 2022 (ano de Censo): completa com a população do Censo 2022 (agregado 4709, var 93)
    censo, _ = agregado(4709, 93, "2022")
    pp = pd.concat([pop[["codigo_ibge", "ano_referencia", "valor"]].assign(fonte_populacao="6579 estimativa"),
                    censo[["codigo_ibge", "ano_referencia", "valor"]].assign(fonte_populacao="4709 Censo 2022")])
    pp = pp.rename(columns={"valor": "populacao"})
    der = p37.merge(pp, on=["codigo_ibge", "ano_referencia"], how="left").merge(area[["codigo_ibge", "area_km2"]], on="codigo_ibge")
    ult_pop = pop[pop.ano_referencia == pop.ano_referencia.max()][["codigo_ibge", "valor", "ano_referencia"]]
    ult_pop.columns = ["codigo_ibge", "populacao_ultimo_ano", "ano_populacao"]
    der = der.merge(ult_pop, on="codigo_ibge").merge(mun, on="codigo_ibge")
    der["pib_per_capita_reais"] = der.pib_mil_reais * 1000 / der.populacao  # só quando o ano da população = ano do PIB
    der["pib_por_km2_mil_reais"] = der.pib_mil_reais / der.area_km2
    der["densidade_demografica_hab_km2"] = der.populacao_ultimo_ano / der.area_km2
    salvar(der[der.codigo_ibge.isin(AMOSTRA_MUN)], AM, "ibge_2.3_2.5_2.6_derivados_amostra_BA.csv")
    # O PIB per capita oficial de 2023 vem de ibge_pib_per_capita_oficial.py, que reescreve a amostra de derivados
    reg("IBGE", "2.3 PIB per capita", "Validado (2023, base oficial)", 417,
        "https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip",
        "Tabela 6784 só tem nível Brasil (N1) e a 6579 não tem população de 2023; o valor oficial vem da base TXT do "
        "PIB dos Municípios (rodar ibge_pib_per_capita_oficial.py depois deste script). PIB confere 100% com a SIDRA 5938")
    reg("IBGE", "2.5 Densidade demográfica (derivado)", "Validado", len(der.codigo_ibge.unique()), "derivado")
    reg("IBGE", "2.6 PIB por km² (derivado)", "Validado", len(der.codigo_ibge.unique()), "derivado")
    return mun, pop


# ----------------------------------------------------------------------------- INEP
CINE_CTI = {  # área geral CINE -> nível CT&I
    "5": ("CT&I núcleo (STEM)", "Ciências naturais, matemática e estatística"),
    "6": ("CT&I núcleo (STEM)", "Computação e TIC"),
    "7": ("CT&I núcleo (STEM)", "Engenharia, produção e construção"),
    "8": ("CT&I ampliado", "Agricultura, silvicultura, pesca e veterinária (base científica/tecnológica)"),
    "9": ("CT&I ampliado", "Saúde e bem-estar (biomédicas/tecnologias em saúde)"),
}
ORG = {1: "Universidade", 2: "Centro Universitário", 3: "Faculdade",
       4: "Instituto Federal de Educação, Ciência e Tecnologia", 5: "Centro Federal de Educação Tecnológica"}
CAT_ADM = {1: "Pública Federal", 2: "Pública Estadual", 3: "Pública Municipal", 4: "Privada com fins lucrativos",
           5: "Privada sem fins lucrativos", 7: "Especial"}
DIM = {1: "Presencial (município de oferta)", 2: "EAD ofertado no Brasil (por município/polo)",
       3: "EAD só nível Brasil", 4: "EAD no exterior"}
GRAU = {1: "Bacharelado", 2: "Licenciatura", 3: "Tecnológico", 4: "Bacharelado e Licenciatura"}


def inep():
    print("INEP")
    url = "https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2024.zip"
    ies = pd.read_csv(CACHE / "inep_MICRODADOS_ED_SUP_IES_2024.CSV", sep=";", encoding="latin1", low_memory=False)
    cur = pd.read_csv(CACHE / "inep_MICRODADOS_CADASTRO_CURSOS_2024.CSV", sep=";", encoding="latin1",
                      low_memory=False, dtype={"CO_CINE_AREA_GERAL": str, "CO_CINE_AREA_ESPECIFICA": str,
                                               "CO_CINE_AREA_DETALHADA": str, "CO_CINE_ROTULO": str})
    nomes_ies = ies[["CO_IES", "NO_IES", "SG_IES"]]

    # 3.1 IES com sede na BA (o arquivo IES só traz o município da sede/reitoria)
    ies_ba = ies[ies.SG_UF_IES == "BA"].copy()
    ies_ba["organizacao_academica"] = ies_ba.TP_ORGANIZACAO_ACADEMICA.map(ORG)
    ies_ba["categoria_administrativa"] = ies_ba.TP_CATEGORIA_ADMINISTRATIVA.map(CAT_ADM)
    ies_ba["ies_tecnologica_if_cefet"] = ies_ba.TP_ORGANIZACAO_ACADEMICA.isin([4, 5])
    cols = ["NU_ANO_CENSO", "CO_IES", "NO_IES", "SG_IES", "CO_MUNICIPIO_IES", "NO_MUNICIPIO_IES", "SG_UF_IES",
            "organizacao_academica", "categoria_administrativa", "ies_tecnologica_if_cefet",
            "IN_REPOSITORIO_INSTITUCIONAL", "IN_ACESSO_PORTAL_CAPES", "QT_DOC_TOTAL", "QT_DOC_EXE",
            "QT_DOC_EX_DOUT", "QT_DOC_EX_MEST", "QT_DOC_EX_ESP", "QT_DOC_EX_GRAD", "QT_DOC_EX_INT_DE",
            "QT_TEC_DOUTORADO_FEM", "QT_TEC_DOUTORADO_MASC"]
    salvar(ies_ba.sort_values("QT_DOC_EX_DOUT", ascending=False)[cols].head(40), AM, "inep_3.1_3.7_ies_BA_amostra.csv")
    reg("INEP", "3.1 Instituições de Educação Superior", "Validado (2024)", len(ies_ba), url,
        "Arquivo IES traz só o município da sede/reitoria; campus/polo vem do arquivo de cursos (CO_MUNICIPIO)")
    reg("INEP", "3.7 Docentes — titulação", "Validado (2024) no nível IES", int(ies_ba.QT_DOC_EX_DOUT.sum()), url,
        "Microdado público de docente não existe mais; titulação vem agregada por IES (QT_DOC_EX_DOUT/MEST/ESP…), "
        "sem município de lotação")

    # 3.2–3.6 Cursos na BA
    ba = cur[cur.SG_UF == "BA"].copy()
    ba = ba.merge(nomes_ies, on="CO_IES", how="left")
    ba["dimensao"] = ba.TP_DIMENSAO.map(DIM)
    ba["grau_academico"] = ba.TP_GRAU_ACADEMICO.map(GRAU)
    ba["modalidade"] = ba.TP_MODALIDADE_ENSINO.map({1: "Presencial", 2: "EAD"})
    ba["nivel_cti"] = ba.CO_CINE_AREA_GERAL.map(lambda c: CINE_CTI.get(str(c).lstrip("0"), ("Fora de CT&I",))[0])
    cc = ["NU_ANO_CENSO", "CO_IES", "NO_IES", "CO_CURSO", "NO_CURSO", "CO_MUNICIPIO", "NO_MUNICIPIO", "SG_UF",
          "modalidade", "dimensao", "grau_academico", "CO_CINE_AREA_GERAL", "NO_CINE_AREA_GERAL",
          "CO_CINE_AREA_ESPECIFICA", "NO_CINE_AREA_ESPECIFICA", "CO_CINE_AREA_DETALHADA", "NO_CINE_AREA_DETALHADA",
          "CO_CINE_ROTULO", "NO_CINE_ROTULO", "nivel_cti", "QT_CURSO", "QT_VG_TOTAL", "QT_VG_TOTAL_EAD",
          "QT_INSCRITO_TOTAL", "QT_ING", "QT_MAT", "QT_CONC"]
    pres = ba[ba.TP_DIMENSAO == 1]
    amostra = pd.concat([pres[pres.nivel_cti == "CT&I núcleo (STEM)"].sample(15, random_state=1),
                         pres[pres.nivel_cti == "CT&I ampliado"].sample(5, random_state=1),
                         pres[pres.nivel_cti == "Fora de CT&I"].sample(5, random_state=1),
                         ba[(ba.TP_DIMENSAO == 2) & (ba.nivel_cti == "CT&I núcleo (STEM)")].sample(10, random_state=1)])
    salvar(amostra[cc], AM, "inep_3.2_a_3.6_cursos_BA_amostra.csv")
    for ind, campo in [("3.2 Cursos de graduação (Geral e CT&I)", "QT_CURSO"),
                       ("3.3 Cursos por modalidade (Presencial x EAD)", "QT_CURSO"),
                       ("3.4 Vagas ofertadas", "QT_VG_TOTAL"), ("3.5 Matrículas", "QT_MAT"),
                       ("3.6 Ingressantes e concluintes", "QT_ING")]:
        reg("INEP", ind, "Validado (2024)", len(ba), url,
            f"{len(ba)} linhas BA (presencial={len(pres)}, EAD por município/polo={len(ba) - len(pres)}); "
            "atenção: vagas/inscritos EAD não são calculados por município (ver dicionário)")

    # Painel municipal CT&I (presencial) — exemplo de agregação
    agg = (pres.groupby(["CO_MUNICIPIO", "NO_MUNICIPIO", "nivel_cti"])[["QT_CURSO", "QT_VG_TOTAL", "QT_MAT", "QT_ING", "QT_CONC"]]
           .sum().reset_index())
    salvar(agg[agg.CO_MUNICIPIO.isin(AMOSTRA_MUN)], AM, "inep_cursos_presenciais_por_municipio_nivel_cti_amostra.csv")

    # Categorias CINE (todas as presentes na BA) com contagens
    cine = (ba.groupby(["CO_CINE_AREA_GERAL", "NO_CINE_AREA_GERAL", "CO_CINE_AREA_ESPECIFICA", "NO_CINE_AREA_ESPECIFICA",
                        "CO_CINE_AREA_DETALHADA", "NO_CINE_AREA_DETALHADA", "nivel_cti"])
            .agg(linhas_curso_municipio=("CO_CURSO", "size"), cursos_distintos=("CO_CURSO", "nunique"),
                 matriculas_BA=("QT_MAT", "sum")).reset_index().sort_values("CO_CINE_AREA_DETALHADA"))
    salvar(cine, CAT, "inep_cine_areas_BA_nivel_cti.csv")
    rot = (ba.groupby(["CO_CINE_ROTULO", "NO_CINE_ROTULO", "CO_CINE_AREA_GERAL", "nivel_cti"])
           .agg(cursos_distintos=("CO_CURSO", "nunique"), matriculas_BA=("QT_MAT", "sum")).reset_index()
           .sort_values(["nivel_cti", "matriculas_BA"], ascending=[True, False]))
    salvar(rot, CAT, "inep_cine_rotulos_BA_nivel_cti.csv")
    outras = []
    for campo, mapa in [("TP_ORGANIZACAO_ACADEMICA", ORG), ("TP_CATEGORIA_ADMINISTRATIVA", CAT_ADM),
                        ("TP_DIMENSAO", DIM), ("TP_GRAU_ACADEMICO", GRAU), ("TP_MODALIDADE_ENSINO", {1: "Presencial", 2: "EAD"})]:
        for k, v in mapa.items():
            n = int((ba[campo] == k).sum())
            rel = ""
            if campo == "TP_ORGANIZACAO_ACADEMICA" and k in (4, 5): rel = "Auxiliar CT&I: instituição tecnológica"
            if campo == "TP_GRAU_ACADEMICO" and k == 3: rel = "Auxiliar CT&I: cruzar com CINE 05/06/07"
            if campo == "TP_DIMENSAO" and k != 1: rel = "Separar de presencial (regra 3.3)"
            outras.append(dict(campo=campo, codigo=k, descricao=v, linhas_BA=n, uso_cti=rel))
    salvar(pd.DataFrame(outras), CAT, "inep_outras_categorias_BA.csv")


# ----------------------------------------------------------------------------- BNDES
INSTR_CTI = {  # instrumento_financeiro -> motivo (todos verificados nos dados da BA)
    "BNDES INOVAÇÃO": "Linha de inovação", "INOVAÇÃO": "Linha de inovação", "PSI - Inovação": "PSI linha Inovação",
    "PROGRAMA BNDES MAIS INOVAÇÃO": "Programa Mais Inovação (ver ressalva no .md)", "FUNTEC": "Fundo Tecnológico (não reembolsável)",
    "BNDES FUNTTEL": "Fundo p/ Desenv. Tecnológico das Telecom.", "BNDES FINAME FUNTTEL": "FUNTTEL via FINAME",
    "BNDES PROSOFT": "Software e serviços de TI", "BNDES PROENGENHARIA": "Engenharia/P&D",
    "PSI - Proengenharia": "Engenharia/P&D", "ENGENHARIA AUTOMOTIVA": "Engenharia automotiva (P&D)",
    "BNDES PRODESIGN": "Design/inovação", "INDÚSTRIA E SERVIÇOS DIFUSORES DE TECNOLOGIA": "Difusão tecnológica",
    "PSI - BK - Tecnologia Nacional": "BK com tecnologia nacional",
    "BK AQUISIÇÃO E COMERCIALIZAÇÃO – MÁQUINAS 4.0": "Máquinas 4.0 (difusão tecnológica)",
    "INOVAGRO": "Inovação tecnológica agropecuária", "PROGRAMA BNDES FUST": "FUST — conectividade/telecom",
    "PROGRAMA BNDES FUST AUTOMÁTICO": "FUST — conectividade/telecom",
}
FONTE_CTI = ["FUNTTEL", "FUST", "FNDCT"]
CNAE_TEC = {"C21": "Farmoquímicos e farmacêuticos", "C26": "Equip. informática, eletrônicos e ópticos",
            "J61": "Telecomunicações", "J62": "Atividades de TI", "J63": "Prestação de serviços de informação",
            "M72": "Pesquisa e desenvolvimento científico", "C30.4": "Aeronaves", "P853": "Educação superior"}
KW_PROJ = re.compile(r"INOVA|PESQUISA|P&D|PD&I|DESENVOLVIMENTO TECNOL|TECNOLOGIA|SOFTWARE|CIENT|LABORAT", re.I)


def classifica_bndes(df):
    s = lambda c: df[c].astype(str).str.strip()
    cnae = s("subsetor_cnae_codigo")
    df["cti_flag_oficial"] = s("inovacao").eq("SIM")
    df["cti_instrumento"] = s("instrumento_financeiro").isin(INSTR_CTI)
    df["cti_fonte_recurso"] = s("fonte_de_recurso_desembolsos").str.contains("|".join(FONTE_CTI))
    df["cti_cnae_tecnologico_aux"] = cnae.str[:3].isin([k for k in CNAE_TEC if len(k) == 3]) | cnae.str[:4].isin(["P853"])
    df["cti_descricao_projeto_aux"] = (s("descricao_do_projeto").str.contains(KW_PROJ)
                                       if "descricao_do_projeto" in df else False)
    motivo = []
    for _, r in df.iterrows():
        m = []
        if r.cti_flag_oficial: m.append("inovacao=SIM")
        if r.cti_instrumento: m.append("instrumento:" + str(r.instrumento_financeiro).strip())
        if r.cti_fonte_recurso: m.append("fonte_recurso CT&I")
        if r.cti_cnae_tecnologico_aux: m.append("CNAE tecnológico (aux)")
        if r.cti_descricao_projeto_aux: m.append("descrição do projeto (aux)")
        motivo.append("; ".join(m))
    df["cti_motivo"] = motivo
    df["cti_nivel"] = "Fora de CT&I"
    df.loc[df.cti_cnae_tecnologico_aux | df.cti_descricao_projeto_aux, "cti_nivel"] = "Auxiliar (revisar)"
    df.loc[df.cti_flag_oficial | df.cti_instrumento | df.cti_fonte_recurso, "cti_nivel"] = "CT&I (regra explícita)"
    return df


def painel_cti_municipio_ano(df):
    cti = df[df.cti_nivel == "CT&I (regra explícita)"]
    return (cti.groupby(["municipio_codigo", "municipio", "ano"]).agg(
        operacoes=("cliente", "size"), valor_contratado=("valor_operacao_reais", "sum"),
        valor_desembolsado=("valor_desembolsado_reais", "sum")).reset_index()
        .sort_values(["ano", "valor_desembolsado"], ascending=False))


def bndes():
    print("BNDES")
    base = "https://dadosabertos.bndes.gov.br/api/3/action/datastore_search?resource_id="
    arqs = {"nao_automaticas": ("6f56b78c-510f-44b6-8274-78a5b7e931f4", "valor_contratado_reais"),
            "indiretas_automaticas": ("612faa0b-b6be-4b2c-9317-da5dc2c0b901", "valor_da_operacao_em_reais")}
    todos = []
    for nome, (rid, vcol) in arqs.items():
        df = pd.read_csv(CACHE / f"bndes_{nome}_BA.csv", low_memory=False)
        for c in df.columns:
            if df[c].dtype == object: df[c] = df[c].str.strip()
        df = classifica_bndes(df)
        df["ano"] = df.data_da_contratacao.str[:4].astype(int)
        df["base"] = nome
        df["valor_operacao_reais"] = df[vcol]
        todos.append(df)
        amostra = pd.concat([df[df.cti_nivel == "CT&I (regra explícita)"].sort_values("data_da_contratacao").tail(15),
                             df[df.cti_nivel == "Auxiliar (revisar)"].tail(5),
                             df[df.cti_nivel == "Fora de CT&I"].tail(10)])
        salvar(amostra.drop(columns=["_id"]), AM, f"bndes_5.x_{nome}_BA_amostra.csv")
        reg("BNDES", f"5.1–5.5 Operações ({nome.replace('_', ' ')})", "Validado (UF=BA)", len(df),
            base + rid + "&filters={\"uf\":\"" + ("BA" if nome == "nao_automaticas" else " BA") + "\"}",
            f"{len(df)} operações BA; {int((df.cti_nivel == 'CT&I (regra explícita)').sum())} CT&I por regra explícita; "
            f"código IBGE em municipio_codigo ({df.municipio_codigo.notna().mean():.0%} preenchido)")
    df = pd.concat(todos, ignore_index=True)

    # Painel CT&I por município/ano — completo (todos os municípios e anos com operação CT&I)
    salvar(painel_cti_municipio_ano(df), AM, "bndes_5.5_cti_por_municipio_ano_BA.csv")
    reg("BNDES", "5.6 Desembolso per capita (derivado)", "Viável", len(df.municipio_codigo.unique()), "derivado",
        "municipio_codigo é IBGE 7 dígitos → junta direto com população IBGE do mesmo ano")

    # Valores distintos de TODAS as colunas categóricas, com contagem/valor e classificação
    cats = ["inovacao", "produto", "instrumento_financeiro", "modalidade_de_apoio", "forma_de_apoio", "area_operacional",
            "setor_bndes", "subsetor_bndes", "setor_cnae", "subsetor_cnae_agrupado", "porte_do_cliente",
            "natureza_do_cliente", "fonte_de_recurso_desembolsos", "custo_financeiro", "situacao_do_contrato",
            "situacao_da_operacao", "tipo_de_garantia", "tipo_de_excepcionalidade"]
    linhas = []
    for c in cats:
        if c not in df: continue
        g = df.groupby(c).agg(n_operacoes_BA=("cliente", "size"), valor_desembolsado_BA=("valor_desembolsado_reais", "sum"),
                              n_inovacao_sim=("cti_flag_oficial", "sum")).reset_index()
        for _, r in g.iterrows():
            v = str(r[c]); rel, regra = "Não", ""
            if c == "inovacao" and v == "SIM": rel, regra = "Sim (principal)", "Flag oficial do BNDES"
            elif c == "instrumento_financeiro" and v in INSTR_CTI: rel, regra = "Sim (principal)", INSTR_CTI[v]
            elif c == "fonte_de_recurso_desembolsos" and any(k in v for k in FONTE_CTI): rel, regra = "Sim (principal)", "Fundo setorial de tecnologia"
            elif c == "area_operacional" and "INOVACAO" in v: rel, regra = "Auxiliar", "Área ampla (inclui crédito produtivo não-inovador)"
            elif c in ("subsetor_cnae_agrupado",) and v in ("Informação e comunicação", "INFORMAÇÃO E COMUNICAÇÃO",
                    "Equip info, eletronico, ótico", "Farmoquímico, farmacêutico", "Telecomunicações", "TELECOMUNICAÇÕES"):
                rel, regra = "Auxiliar", "Setor intensivo em tecnologia (não inferir inovação só pelo CNAE)"
            elif c == "subsetor_bndes" and v == "TELECOMUNICAÇÕES": rel, regra = "Auxiliar", "Infraestrutura TIC"
            elif r.n_inovacao_sim > 0: rel, regra = "Contém operações com inovacao=SIM", f"{int(r.n_inovacao_sim)} op. SIM"
            linhas.append(dict(coluna=c, valor=v, n_operacoes_BA=int(r.n_operacoes_BA),
                               valor_desembolsado_BA=round(r.valor_desembolsado_BA, 2),
                               n_inovacao_sim=int(r.n_inovacao_sim), relacao_cti=rel, justificativa=regra))
    salvar(pd.DataFrame(linhas), CAT, "bndes_valores_categoricos_BA_relacao_cti.csv")

    sub = (df.groupby(["subsetor_cnae_codigo", "subsetor_cnae_nome"]).agg(
        n_operacoes_BA=("cliente", "size"), valor_desembolsado_BA=("valor_desembolsado_reais", "sum"),
        n_inovacao_sim=("cti_flag_oficial", "sum"), cnae_tecnologico_aux=("cti_cnae_tecnologico_aux", "max")).reset_index()
           .sort_values("subsetor_cnae_codigo"))
    salvar(sub, CAT, "bndes_subsetores_cnae_BA.csv")

    resumo = (df.groupby(["base", "cti_nivel"]).agg(n=("cliente", "size"), desembolsado=("valor_desembolsado_reais", "sum"))
              .reset_index())
    resumo["desembolsado_bi"] = (resumo.desembolsado / 1e9).round(3)
    salvar(resumo, CAT, "bndes_resumo_niveis_cti_BA.csv")
    cruz = (df[df.cti_nivel == "CT&I (regra explícita)"].groupby(["base", "produto", "instrumento_financeiro", "inovacao"])
            .agg(n=("cliente", "size"), desembolsado=("valor_desembolsado_reais", "sum")).reset_index()
            .sort_values("desembolsado", ascending=False))
    salvar(cruz, CAT, "bndes_cti_instrumento_x_flag_inovacao_BA.csv")
    return df


# ----------------------------------------------------------------------------- SICONFI
SUBF_CTI = {"571": ("Principal", "Desenvolvimento Científico"),
            "572": ("Principal", "Desenvolvimento Tecnológico e Engenharia"),
            "573": ("Principal", "Difusão do Conhecimento Científico e Tecnológico"),
            "126": ("Auxiliar", "Tecnologia da Informação (TI do próprio ente — não é fomento)"),
            "364": ("Auxiliar", "Ensino Superior"), "363": ("Auxiliar", "Ensino Profissional")}


def siconfi(pop):
    print("SICONFI")
    U = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/"
    # 6.3 RREO Anexo 02 (período 6) — Salvador
    p = dict(an_exercicio=2025, nr_periodo=6, co_tipo_demonstrativo="RREO", no_anexo="RREO-Anexo 02", id_ente=2927408)
    r = pd.DataFrame(requests.get(U + "rreo", params=p, timeout=120).json()["items"])
    u = requests.Request("GET", U + "rreo", params=p).prepare().url
    salvar(r[r.conta.str.contains("Ciência|Tecnol|TOTAL", regex=True)], AM, "siconfi_6.3_rreo_anexo02_salvador_2025_cti.csv")
    reg("SICONFI", "6.3 Despesa por função/subfunção (RREO Anexo 02)", "Validado (Salvador 2025 P6)", len(r), u,
        "RREO não traz código da função na linha (cod_conta genérico); para filtrar CT&I usar DCA Anexo I-E")

    # 6.2 Receita — DCA Anexo I-C Salvador 2024
    p = dict(an_exercicio=2024, no_anexo="DCA-Anexo I-C", id_ente=2927408)
    rc = pd.DataFrame(requests.get(U + "dca", params=p, timeout=120).json()["items"])
    u = requests.Request("GET", U + "dca", params=p).prepare().url
    salvar(rc.head(40), AM, "siconfi_6.2_dca_anexoIC_receita_salvador_2024_amostra.csv")
    reg("SICONFI", "6.2 Receita municipal (DCA Anexo I-C)", "Validado (Salvador 2024)", len(rc), u)

    # DCA I-E todos os municípios BA (arquivo gerado por siconfi_dca_ba.py)
    f = CACHE / "siconfi_dca_IE_BA_2024.csv"
    if f.exists():
        d = pd.read_csv(f)
        d["funcao"] = d.conta.str.extract(r"^(?:FU)?(\d{2})")[0]
        d["subfuncao"] = d.conta.str.extract(r"^\d{2}\.(\d{3})")[0]
        liq = d[(d.coluna == "Despesas Liquidadas") & (d.cod_conta == "TotalDespesas")]
        f19 = liq[liq.conta.str.startswith("19 - ")][["cod_ibge", "instituicao", "valor"]].rename(columns={"valor": "liquidado_funcao19_CT"})
        tot = liq[liq.conta == "Despesas Exceto Intraorçamentárias"][["cod_ibge", "valor"]].rename(columns={"valor": "liquidado_total"})
        sub = liq[liq.subfuncao.isin(["571", "572", "573"])].groupby("cod_ibge").valor.sum().rename("liquidado_subf_571_572_573").reset_index()
        ti = liq[liq.subfuncao == "126"].groupby("cod_ibge").valor.sum().rename("liquidado_subf_126_TI").reset_index()
        entes = d[["cod_ibge", "instituicao"]].drop_duplicates("cod_ibge")
        f19 = f19.drop(columns="instituicao")
        painel = entes.merge(tot, on="cod_ibge", how="left").merge(f19, on="cod_ibge", how="left").merge(sub, on="cod_ibge", how="left").merge(ti, on="cod_ibge", how="left")
        pp = pop[pop.ano_referencia == 2024][["codigo_ibge", "valor"]].rename(columns={"codigo_ibge": "cod_ibge", "valor": "populacao_2024"})
        painel = painel.merge(pp, on="cod_ibge", how="left")
        # ente entregou a DCA mas não tem linha na função/subfunção = despesa zero
        cols_ct = ["liquidado_funcao19_CT", "liquidado_subf_571_572_573", "liquidado_subf_126_TI"]
        painel[cols_ct] = painel[cols_ct].fillna(0)
        painel["CT_por_habitante"] = painel.liquidado_funcao19_CT / painel.populacao_2024
        painel["CT_pct_despesa"] = 100 * painel.liquidado_funcao19_CT / painel.liquidado_total
        painel = painel.sort_values("liquidado_funcao19_CT", ascending=False)
        salvar(painel, AM, "siconfi_6.3_6.4_dca_IE_BA_2024_ciencia_tecnologia_por_municipio.csv")
        n_mun = d.cod_ibge.nunique(); n_ct = int(painel.liquidado_funcao19_CT.gt(0).sum())
        reg("SICONFI", "6.3/6.4 Despesa C&T por município (DCA I-E 2024)", "Validado", n_mun,
            U + "dca?an_exercicio=2024&no_anexo=DCA-Anexo%20I-E&id_ente={cod_ibge}",
            f"{n_mun} municípios BA com DCA 2024; {n_ct} com despesa liquidada na Função 19")
        # Catálogo de funções/subfunções observadas
        fs = (liq.groupby("conta").agg(municipios=("cod_ibge", "nunique"), liquidado_BA=("valor", "sum")).reset_index())
        fs["funcao"] = fs.conta.str.extract(r"^(?:FU)?(\d{2})")[0]
        fs["subfuncao"] = fs.conta.str.extract(r"^\d{2}\.(\d{3})")[0]

        def rel(r):
            if r.funcao == "19": return ("Principal", "Função 19 — Ciência e Tecnologia")
            if isinstance(r.subfuncao, str) and r.subfuncao in SUBF_CTI: return SUBF_CTI[r.subfuncao]
            if r.funcao == "24": return ("Auxiliar", "Função 24 — Comunicações")
            return ("Não", "")
        fs[["relacao_cti", "justificativa"]] = fs.apply(lambda r: pd.Series(rel(r)), axis=1)
        salvar(fs.sort_values(["funcao", "subfuncao"], na_position="first"), CAT, "siconfi_funcoes_subfuncoes_BA_relacao_cti.csv")


# ----------------------------------------------------------------------------- ANATEL
def anatel():
    print("ANATEL")
    url = "https://www.anatel.gov.br/dadosabertos/paineis_de_dados/acessos/acessos_banda_larga_fixa.zip"
    d = pd.read_csv(CACHE / "Densidade_Banda_Larga_Fixa.csv", sep=";", decimal=",", dtype={"Código IBGE": str}, low_memory=False)
    d = d.dropna(subset=["UF", "Densidade"])
    ba = d[(d.UF == "BA") & (d["Nível Geográfico Densidade"] == "Municipio")].copy()
    ba["periodo"] = ba.Ano * 100 + ba.Mês
    am = ba[ba["Código IBGE"].astype(str).isin(map(str, AMOSTRA_MUN[:5]))].sort_values(["Código IBGE", "periodo"])
    am = am[am.Ano.isin([2021, 2022, 2025, 2026])]
    am["alerta"] = ""
    am.loc[(am.periodo >= 202512) & (am.periodo <= 202603), "alerta"] = "valor anômalo (ver .md)"
    salvar(am, AM, "anatel_7.1_densidade_scm_BA_amostra.csv")
    cobertura = ba.groupby("Ano")["Código IBGE"].nunique()
    reg("ANATEL", "7.1 Densidade SCM por 100 domicílios", "Validado com ressalvas", len(ba), url + " → Densidade_Banda_Larga_Fixa.csv",
        "Município×mês 2007–2022 e abr/2026+ ok; 2023–2024 vazios para todos os municípios; 2025 só dez (38 mun.); "
        f"dez/2025–mar/2026 com valores ~0 (inconsistentes). Municípios BA por ano: {cobertura.to_dict()}")

    # Acessos 2026 por tecnologia/meio/velocidade (categorias para recorte CT&I/TIC)
    f = CACHE / "Acessos_Banda_Larga_Fixa_2026_Colunas.csv"
    if f.exists():
        a = pd.read_csv(f, sep=";", decimal=",", dtype={"Código IBGE Município": str, "CNPJ": str}, low_memory=False)
        a = a[a.UF == "BA"]
        mes = sorted(c for c in a.columns if re.fullmatch(r"\d{4}-\d{2}", c))[-1]
        salvar(a[a["Código IBGE Município"].isin(map(str, AMOSTRA_MUN))].sort_values(mes, ascending=False).head(40),
               AM, "anatel_acessos_bl_fixa_2026_BA_amostra.csv")
        cats = []
        for c in ["Tecnologia", "Meio de Acesso", "Faixa de Velocidade", "Tipo de Produto", "Tipo de Pessoa", "Porte da Prestadora"]:
            g = a.groupby(c)[mes].sum().sort_values(ascending=False)
            for v, n in g.items():
                rel = ""
                if c == "Meio de Acesso" and str(v).lower().startswith("fibra"): rel = "Conectividade avançada (fibra)"
                if c == "Tecnologia" and v in ("FTTH", "FTTB", "FTTC", "FTTx"): rel = "Conectividade avançada (fibra)"
                if c == "Faixa de Velocidade" and str(v).startswith(">"): rel = "Alta velocidade"
                cats.append(dict(coluna=c, valor=v, acessos_BA=int(n), mes_referencia=mes, uso_cti=rel))
        salvar(pd.DataFrame(cats), CAT, "anatel_categorias_acessos_BA.csv")
        reg("ANATEL", "Acessos BL fixa por tecnologia/velocidade (complementar)", "Validado", len(a), url + " → Acessos_Banda_Larga_Fixa_2026_Colunas.csv",
            "Permite recalcular densidade para meses sem dado (acessos ÷ domicílios Censo 2022) e recortes por tecnologia")


# ----------------------------------------------------------------------------- ANEEL
def aneel():
    print("ANEEL")
    # Extração feita por extrair_amostras_aneel_ba.py e aneel_decfec_ba.py (conexão pelo IP, sem SNI)
    ds = "https://dadosabertos.aneel.gov.br/api/3/action/datastore_search?resource_id="
    sem_sni = "O servidor derruba o TLS com SNI dadosabertos.aneel.gov.br; extraído pelo IP 200.198.220.169 sem SNI. "
    for ind, st, n, url, obs in [
        ("4.1 Empreendimentos de geração e potência outorgada", "Validado", 1163, ds + "11ec447d-698d-4ab8-977f-b424d5deee6a",
         "SIGA, SigUFPrincipal=BA: 1.163 usinas em 123 municípios; município só como texto ('Nome - BA')"),
        ("4.2 Potência instalada solar/eólica", "Validado", 1026, ds + "11ec447d-698d-4ab8-977f-b424d5deee6a",
         "Subconjunto do SIGA com SigTipoGeracao em EOL (520) e UFV (506), 74 municípios"),
        ("4.3 Consumo de energia e unidades consumidoras", "Validado com ressalvas", 1500, ds + "fd10c9d4-cb76-4020-a322-e79afb13eaf7",
         "INDGER (UCs por município, código IBGE) validado; SAMP (ff80dd21-…) só no nível da distribuidora, sem município"),
        ("4.4 Projetos de P&D ANEEL", "Validado", 99, ds + "3a7aee00-b6ee-4913-9670-f6b60f4a7bea",
         "99 projetos COELBA 2009–2026; sem município e sem ICT executora"),
        ("4.5 DEC e FEC", "Validado (2025)", 211,
         "https://dadosabertos.aneel.gov.br/dataset/d5f0712e-62f6-4736-8dff-9991f10758a7/resource/"
         "4493985c-baea-429c-9df5-3030422c71d7/download/indicadores-continuidade-coletivos-2020-2029.zip",
         "211 conjuntos COELBA × 12 meses de 2025, levados a 415 municípios pelo INDQUAL (ponderado por consumidores). "
         "Usar o ZIP: o datastore do recurso está defasado e sem vários meses")]:
        reg("ANEEL", ind, st, n, url, sem_sni + obs)


if __name__ == "__main__":
    mun, pop = ibge()
    inep()
    bndes()
    siconfi(pop)
    anatel()
    aneel()
    salvar(pd.DataFrame(status), ROOT, "status_validacao_fontes.csv")

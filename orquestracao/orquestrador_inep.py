"""
INEP no orquestrador comum (Python que simula o Hop). Mesmo padrão do IBGE: Passo 0 (verificar), 1 (staging), 2 (MERGE), 3 (checkpoint).
Desenho híbrido (PLANEJAMENTO_IBGE.md §7D, orquestracao/sql/06_inep_modelo.sql):
  dimensões que nunca se apagam  cine_classificacao, ies, ies_local, curso   -> etl.merge_tabela(..., p_excluir => false)
  fato por ano                   curso_censo (co_curso, ano)                 -> MERGE com exclusão só dentro do ano carregado
  regra CT&I                     semeada do CSV só se estiver vazia; depois é da curadoria (API)
  "ativo" não existe como coluna: é derivado em inep.v_curso_atual

Passo 0   GET Range 0-0 no ZIP do ano e no do ano seguinte (HEAD e GET simples são derrubados pelo servidor); compara com etl.checkpoint.
Passo 1   lê o ZIP em streaming (sem extrair), aplica os filtros 0 a 4 do PLANO §9b e valida antes de gravar qualquer coisa.
Passo 2   MERGE por tabela (ordem: cine, regra, ies, ies_local, curso, curso_censo). Trava de exclusão em 20% (rotatividade real do censo 2023→2024 foi 10,3%).
Passo 3   etl.finalizar() grava o checkpoint só se a carga terminou bem.

Uso:  python orquestracao/orquestrador_inep.py [ano] [--zip arquivo.zip] [--verificar] [--forcar]
  --verificar  só registra o catálogo e diz o que faria (não carrega, não grava checkpoint)
  --zip        usa um ZIP já baixado (os censos antigos têm a mesma estrutura); sem isto baixa para orquestracao/cache/
  --forcar     carrega mesmo que o checkpoint diga "sem mudança"
Conexão: variável PG_DSN, ou padrão local (como orquestrador_simulado.py). ETL_DISPARO=agendado|manual|forcado.
"""
import csv, datetime as dt, hashlib, io, json, os, subprocess, sys, zipfile
from email.utils import parsedate_to_datetime
from pathlib import Path
from orquestrador_simulado import dsn, OPCOES_AUDITORIA, RAIZ, CACHE, copiar, executar, checkpoint, log  # mesma conexão, auditoria e passos
import psycopg

csv.field_size_limit(10 ** 9)
ZIP_ARG = sys.argv[sys.argv.index("--zip") + 1] if "--zip" in sys.argv else None
ARGS = [a for a in sys.argv[1:] if not a.startswith("--") and a != ZIP_ARG]
ANO = int(ARGS[0]) if ARGS else 2024
URL = "https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_{}.zip"
RID = f"inep_censo_superior_{ANO}"
FONTE_TABELA = "inep_censo_superior"
PARAMETROS = {"ano": ANO, "uf": 29, "modalidade": 1, "exigir_sede_ba": False, "fonte_tabela": FONTE_TABELA}
REGRA_CSV = RAIZ / "automacao-hop-postgres" / "analise" / "regra_cti_rotulos.csv"
AREAS_CTI = {"05", "06", "07", "08", "09"}      # universo que entra em inep.curso; a regra_cti decide, por rótulo, quem é CT&I
LIMITE_EXCLUSAO_PCT = 20                         # curso_censo: o censo real perde até ~10% dos cursos por ano
TOLERANCIA_ANO_VIZINHO = 0.20                    # validação da etapa 5: linhas do ano x ano mais próximo já carregado
DISPARO = os.environ.get("ETL_DISPARO", "manual")


# ============================================================================================ PASSO 0
def sondar(url, tentativas=4):
    """GET com Range 0-0 via curl (o Python recebe 'connection reset' do INEP). Devolve (http, etag, last_modified, tamanho)."""
    saida = ""
    for _ in range(tentativas):
        saida = subprocess.run(["curl", "-sS", "-m", "60", "-A", "Mozilla/5.0", "-r", "0-0", "-D", "-", "-o", os.devnull, url],
                               capture_output=True, text=True).stdout
        if saida.strip():
            break
    h = {}
    for linha in saida.splitlines():
        if ":" in linha:
            k, v = linha.split(":", 1); h[k.strip().lower()] = v.strip()
    http = int(saida.split()[1]) if saida.startswith("HTTP") else 0
    tam = int(h["content-range"].rsplit("/", 1)[1]) if "content-range" in h else None
    return http, h.get("etag", "").strip('"'), h.get("last-modified"), tam


def baixar_zip(url, tam, destino):
    """Baixa em blocos de 8 MB com Range (o servidor reseta GET sem Range), refazendo cada bloco até 6 vezes."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".parcial")
    with open(tmp, "wb") as f:
        ini = 0
        while ini < tam:
            fim = min(ini + 8 * 1024 * 1024, tam) - 1
            for _ in range(6):
                r = subprocess.run(["curl", "-sS", "-m", "180", "-A", "Mozilla/5.0", "-r", f"{ini}-{fim}", url], capture_output=True)
                if len(r.stdout) == fim - ini + 1:
                    break
            else:
                raise RuntimeError(f"download falhou no bloco {ini}-{fim}")
            f.write(r.stdout); ini = fim + 1
    tmp.replace(destino)


# ============================================================================================ PASSO 1
def limpa(v):
    """Códigos CINE chegam com aspas literais dentro do campo e devem continuar TEXTO (zero à esquerda, letras)."""
    return (v or "").strip().strip('"').strip()


def inteiro(v):
    v = (v or "").strip()
    return int(float(v)) if v else None      # CO_MUNICIPIO pode chegar como 2919207.0 em alguns arquivos


def ler_zip(caminho, municipios):
    """Streaming do ZIP: devolve (funil, linhas_base, ies_do_arquivo). linhas_base = presencial BA com QT_CURSO = 1, todas as áreas."""
    z = zipfile.ZipFile(caminho)
    nm = lambda parte: next(i for i in z.namelist() if i.upper().endswith(".CSV") and parte in i.upper())
    funil = dict(arquivo=0, ano=0, uf29=0, municipio_ba=0, presencial=0, abi=0, qt_curso_1=0)
    base, vistos = [], set()
    leitor = csv.DictReader(io.TextIOWrapper(z.open(nm("CADASTRO_CURSOS")), encoding="latin1", newline=""), delimiter=";")
    obrig = ["NU_ANO_CENSO", "CO_UF", "CO_MUNICIPIO", "TP_MODALIDADE_ENSINO", "QT_CURSO", "CO_CURSO", "CO_IES", "NO_CURSO",
             "TP_GRAU_ACADEMICO", "TP_REDE", "CO_CINE_ROTULO", "NO_CINE_ROTULO", "CO_CINE_AREA_GERAL", "NO_CINE_AREA_GERAL",
             "CO_CINE_AREA_ESPECIFICA", "CO_CINE_AREA_DETALHADA", "QT_VG_TOTAL", "QT_ING", "QT_MAT", "QT_CONC"]
    falta = [c for c in obrig if c not in leitor.fieldnames]
    if falta:
        raise ValueError(f"o layout do CSV de cursos mudou; colunas ausentes: {falta}. Carga abortada")
    for l in leitor:
        funil["arquivo"] += 1
        if l["NU_ANO_CENSO"] != str(ANO):
            continue
        funil["ano"] += 1
        if l["CO_UF"] != "29":
            continue
        funil["uf29"] += 1
        if inteiro(l["CO_MUNICIPIO"]) not in municipios:
            continue
        funil["municipio_ba"] += 1
        if l["TP_MODALIDADE_ENSINO"] != "1":
            continue
        funil["presencial"] += 1
        if l["QT_CURSO"] != "1":
            funil["abi"] += 1           # Áreas Básicas de Ingresso: fora do catálogo e dos indicadores (decisão de 13/11)
            continue
        funil["qt_curso_1"] += 1
        co = inteiro(l["CO_CURSO"])
        if co in vistos:
            raise ValueError(f"CO_CURSO {co} repetido entre os cursos presenciais da BA; a chave natural deixou de valer. Carga abortada")
        vistos.add(co)
        base.append(dict(
            co_curso=co, co_ies=inteiro(l["CO_IES"]), co_municipio=inteiro(l["CO_MUNICIPIO"]), no_curso=l["NO_CURSO"].strip(),
            tp_grau_academico=inteiro(l["TP_GRAU_ACADEMICO"]), tp_rede=inteiro(l["TP_REDE"]),
            co_cine_rotulo=limpa(l["CO_CINE_ROTULO"]), no_cine_rotulo=limpa(l["NO_CINE_ROTULO"]),
            co_cine_area_geral=limpa(l["CO_CINE_AREA_GERAL"]).zfill(2), no_cine_area_geral=limpa(l["NO_CINE_AREA_GERAL"]),
            co_cine_area_especifica=limpa(l["CO_CINE_AREA_ESPECIFICA"]), co_cine_area_detalhada=limpa(l["CO_CINE_AREA_DETALHADA"]),
            qt_vg_total=inteiro(l["QT_VG_TOTAL"]), qt_ing=inteiro(l["QT_ING"]), qt_mat=inteiro(l["QT_MAT"]), qt_conc=inteiro(l["QT_CONC"])))
    ies = {}
    for l in csv.DictReader(io.TextIOWrapper(z.open(nm("_IES_")), encoding="latin1", newline=""), delimiter=";"):
        ies[inteiro(l["CO_IES"])] = l
    return funil, base, ies


# ============================================================================================ CARGA
def carregar_ano(cur, exe, digital, caminho_zip):
    """Passos 1 e 2. Devolve (inseridos, atualizados, excluídos) somados; detalhes por tabela vão para etl.execucao.escopo."""
    data_fonte = parsedate_to_datetime(digital["last_modified"]).date() if digital.get("last_modified") else None
    cur.execute("SELECT codigo_ibge FROM ibge.municipio")
    municipios = {r[0] for r in cur.fetchall()}
    if not municipios:
        raise ValueError("ibge.municipio está vazia: carregue o IBGE antes (as FKs do INEP dependem dela)")
    t = dt.datetime.now()
    funil, base, ies_arq = ler_zip(caminho_zip, municipios)
    log(RID, f"passo 1: ZIP lido em {(dt.datetime.now() - t).total_seconds():.0f}s | " + " | ".join(f"{k} {v}" for k, v in funil.items()))

    # validações (etapa 5 do PLANO): qualquer falha aborta antes de gravar qualquer coisa
    sem_ies = sorted({r["co_ies"] for r in base} - set(ies_arq))
    if not base:
        raise ValueError(f"nenhum curso presencial da BA no censo {ANO}")
    if sem_ies:
        raise ValueError(f"CO_IES dos cursos ausentes do arquivo de IES: {sem_ies[:10]}")
    cur.execute("""SELECT ano, count(*) FROM inep.curso_censo WHERE ano <> %s GROUP BY ano ORDER BY abs(ano - %s) LIMIT 1""", (ANO, ANO))
    vizinho = cur.fetchone()
    universo = [r for r in base if r["co_cine_area_geral"] in AREAS_CTI]
    if vizinho and abs(len(universo) - vizinho[1]) > TOLERANCIA_ANO_VIZINHO * vizinho[1]:
        raise ValueError(f"{len(universo)} cursos nas áreas 05-09 contra {vizinho[1]} em {vizinho[0]}: variação acima de "
                         f"{TOLERANCIA_ANO_VIZINHO:.0%}; o arquivo pode estar incompleto. Carga abortada")
    funil.update(areas_05_09=len(universo), ies=len({r["co_ies"] for r in base}),
                 campi=len({(r["co_ies"], r["co_municipio"]) for r in base}))

    # staging
    cine = {r["co_cine_rotulo"]: [r["co_cine_rotulo"], r["no_cine_rotulo"], r["co_cine_area_detalhada"], r["co_cine_area_especifica"],
                                  r["co_cine_area_geral"], r["no_cine_area_geral"], data_fonte] for r in base}
    copiar(cur, "stg.inep_cine", ["co_cine_rotulo", "no_cine_rotulo", "co_cine_area_detalhada", "co_cine_area_especifica",
                                  "co_cine_area_geral", "no_cine_area_geral", "modificado_fonte_em"], list(cine.values()))
    usadas = sorted({r["co_ies"] for r in base})
    ies_linhas = []
    for co in usadas:
        i = ies_arq[co]
        ies_linhas.append([co, i["NO_IES"].strip(), i["SG_IES"].strip() or None, inteiro(i["CO_MANTENEDORA"]), i["NO_MANTENEDORA"].strip(),
                           inteiro(i["TP_CATEGORIA_ADMINISTRATIVA"]), inteiro(i["TP_ORGANIZACAO_ACADEMICA"]),
                           inteiro(i["CO_MUNICIPIO_IES"]), i["NO_MUNICIPIO_IES"].strip(), i["SG_UF_IES"].strip(), data_fonte])
    copiar(cur, "stg.inep_ies", ["co_ies", "no_ies", "sg_ies", "co_mantenedora", "no_mantenedora", "tp_categoria_administrativa",
                                 "tp_organizacao_academica", "co_municipio_sede", "no_municipio_sede", "uf_sede", "modificado_fonte_em"], ies_linhas)
    copiar(cur, "stg.inep_local", ["co_ies", "co_municipio"], sorted({(r["co_ies"], r["co_municipio"]) for r in base}))
    copiar(cur, "stg.inep_curso", ["co_curso", "co_ies", "co_municipio", "no_curso", "tp_grau_academico", "tp_rede", "modificado_fonte_em"],
           [[r["co_curso"], r["co_ies"], r["co_municipio"], r["no_curso"], r["tp_grau_academico"], r["tp_rede"], data_fonte] for r in universo])
    copiar(cur, "stg.inep_curso_censo", ["co_curso", "ano", "co_cine_rotulo", "qt_vg_total", "qt_ing", "qt_mat", "qt_conc", "modificado_fonte_em"],
           [[r["co_curso"], ANO, r["co_cine_rotulo"], r["qt_vg_total"], r["qt_ing"], r["qt_mat"], r["qt_conc"], data_fonte] for r in universo])

    # MERGE por tabela
    det, soma = {}, [0, 0, 0]

    def merge(destino, stg, chaves, valores, escopo="true", excluir=True, limite=10):
        cur.execute("SELECT * FROM etl.merge_tabela(%s, %s, %s, %s, %s, %s, %s, %s)",
                    (exe, destino, stg, chaves, valores, escopo, limite, excluir))
        r = cur.fetchone(); det[destino] = list(r)
        for i in range(3):
            soma[i] += r[i]

    merge("inep.cine_classificacao", "stg.inep_cine", ["co_cine_rotulo"],
          ["no_cine_rotulo", "co_cine_area_detalhada", "co_cine_area_especifica", "co_cine_area_geral", "no_cine_area_geral"], excluir=False)
    # semente da regra: só rótulos que AINDA NÃO têm regra (nunca sobrescreve a curadoria)
    cur.execute("SELECT co_cine_rotulo FROM inep.regra_cti")
    com_regra = {r[0] for r in cur.fetchall()}
    regra = [[l["co_cine_rotulo"], l["status_proposto"], None, data_fonte]
             for l in csv.DictReader(open(REGRA_CSV, encoding="utf-8-sig"), delimiter=";")
             if l["co_cine_rotulo"] in cine and l["co_cine_rotulo"] not in com_regra]
    if regra:
        copiar(cur, "stg.inep_regra_cti", ["co_cine_rotulo", "status", "observacao", "modificado_fonte_em"], regra)
        merge("inep.regra_cti", "stg.inep_regra_cti", ["co_cine_rotulo"], ["status", "observacao"], excluir=False)
        log(RID, f"passo 2: regra_cti semeada com {len(regra)} rótulos novos (analise/regra_cti_rotulos.csv)")
    merge("inep.ies", "stg.inep_ies", ["co_ies"],
          ["no_ies", "sg_ies", "co_mantenedora", "no_mantenedora", "tp_categoria_administrativa", "tp_organizacao_academica",
           "co_municipio_sede", "no_municipio_sede", "uf_sede"], excluir=False)
    cur.execute("""INSERT INTO inep.ies_local (co_ies, co_municipio, _hash, _modificado_fonte_em, _execucao_id)
                   SELECT co_ies, co_municipio, md5(co_ies::text || '-' || co_municipio::text), %s, %s FROM stg.inep_local
                   ON CONFLICT DO NOTHING""", (data_fonte, exe))
    det["inep.ies_local"] = [cur.rowcount, 0, 0]; soma[0] += cur.rowcount
    merge("inep.curso", "stg.inep_curso", ["co_curso"], ["co_ies", "co_municipio", "no_curso", "tp_grau_academico", "tp_rede"], excluir=False)
    merge("inep.curso_censo", "stg.inep_curso_censo", ["co_curso", "ano"],
          ["co_cine_rotulo", "qt_vg_total", "qt_ing", "qt_mat", "qt_conc"], escopo=f"{{a}}.ano = {int(ANO)}", limite=LIMITE_EXCLUSAO_PCT)

    # funil restante, para o relatório (rótulo incluir da regra vigente; sede na BA)
    cur.execute("""SELECT count(*) FILTER (WHERE r.status = 'incluir'),
                          count(*) FILTER (WHERE r.status = 'incluir' AND i.uf_sede = 'BA'),
                          count(*) FILTER (WHERE r.status = 'revisar'),
                          count(*) FILTER (WHERE r.co_cine_rotulo IS NULL)
                   FROM stg.inep_curso_censo s JOIN stg.inep_curso c USING (co_curso) JOIN stg.inep_ies i ON i.co_ies = c.co_ies
                   LEFT JOIN inep.regra_cti r ON r.co_cine_rotulo = s.co_cine_rotulo""")
    inc, inc_ba, rev, sem_regra = cur.fetchone()
    funil.update(rotulo_incluir=inc, rotulo_incluir_e_sede_ba=inc_ba, rotulo_revisar=rev, rotulo_sem_regra=sem_regra)
    if sem_regra:
        log(RID, f"ATENÇÃO: {sem_regra} cursos das áreas 05-09 com rótulo sem regra em inep.regra_cti (ficam fora até a curadoria decidir)")
    cur.execute("UPDATE etl.execucao SET escopo = escopo || %s::jsonb WHERE id = %s",
                (json.dumps({"funil": funil, "tabelas": det}), exe))
    log(RID, "passo 2: " + " | ".join(f"{k.split('.')[1]} +{v[0]} ~{v[1]} -{v[2]}" for k, v in det.items()))
    return tuple(soma)


# ============================================================================================ PRINCIPAL
if __name__ == "__main__":
    http, etag, lm, tam = sondar(URL.format(ANO))
    http2, *_ = sondar(URL.format(ANO + 1))
    if http not in (200, 206):
        sys.exit(f"ZIP do censo {ANO} respondeu HTTP {http}; nada registrado")
    digital = {"etag": etag, "last_modified": lm, "tamanho": tam, "ano": ANO}
    metadados = {**digital, "ano_seguinte": {"ano": ANO + 1, "http": http2, "publicado": http2 in (200, 206)}}
    hash_meta = hashlib.sha256(json.dumps(metadados, sort_keys=True).encode()).hexdigest()
    with psycopg.connect(dsn(), options=OPCOES_AUDITORIA.replace("orquestrador_simulado", "orquestrador_inep")) as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO etl.recurso (id, fonte, modo, metodo, url, tabela_destino, frequencia, parametros)
                           VALUES (%s, 'INEP', 'ELT_ARQUIVO', 'http', %s, 'inep.curso_censo', 'semanal', %s)
                           ON CONFLICT (id) DO UPDATE SET url = EXCLUDED.url, parametros = EXCLUDED.parametros,
                               frequencia = EXCLUDED.frequencia, tabela_destino = EXCLUDED.tabela_destino""",
                        (RID, URL.format(ANO), json.dumps(PARAMETROS)))
            cur.execute("""INSERT INTO meta.fonte_tabela (id, fonte, nome, pesquisa, url, periodicidade, metadados, _hash)
                           VALUES (%s, 'INEP', 'Microdados do Censo da Educação Superior', 'Censo da Educação Superior', %s, %s, %s, %s)
                           ON CONFLICT (id) DO UPDATE SET url = EXCLUDED.url, metadados = EXCLUDED.metadados, _verificado_em = now(),
                               _modificado_em = CASE WHEN meta.fonte_tabela._hash IS DISTINCT FROM EXCLUDED._hash THEN now()
                                                     ELSE meta.fonte_tabela._modificado_em END, _hash = EXCLUDED._hash""",
                        (FONTE_TABELA, URL.format(ANO), json.dumps({"frequencia": "anual"}), json.dumps(metadados), hash_meta))
            cur.execute("""INSERT INTO meta.periodo (fonte_tabela_id, periodo, modificacao) VALUES (%s, %s, %s)
                           ON CONFLICT (fonte_tabela_id, periodo) DO UPDATE SET modificacao = EXCLUDED.modificacao""",
                        (FONTE_TABELA, str(ANO), parsedate_to_datetime(lm).date() if lm else None))
            antes = checkpoint(cur, RID)
            conn.commit()
        mudou = antes != digital
        decisao = ("CARGA INICIAL" if antes is None else "MUDOU (ETag, data ou tamanho)" if mudou else "SEM MUDANÇA") + (
            f" | o censo {ANO + 1} já está publicado (rodar com {ANO + 1} se ainda não foi carregado)" if http2 in (200, 206) else "")
        log(RID, f"passo 0: HTTP {http} | ETag {etag} | Last-Modified {lm} | {tam} bytes | ano seguinte HTTP {http2} | {decisao}")
        if "--verificar" in sys.argv:
            sys.exit(0)
        if not mudou and "--forcar" not in sys.argv:
            executar(conn, RID, digital, None, None)          # registra 'sem_mudanca' e só renova verificado_em
            sys.exit(0)
        zip_local = Path(ZIP_ARG) if ZIP_ARG else CACHE / f"inep_{ANO}_{etag}.zip"
        if not zip_local.exists():
            t = dt.datetime.now(); baixar_zip(URL.format(ANO), tam, zip_local)
            log(RID, f"passo 1: baixou o ZIP ({zip_local.stat().st_size / 1e6:.0f} MB em {(dt.datetime.now() - t).total_seconds():.0f}s)")
        else:
            log(RID, f"passo 1: ZIP já existe ({zip_local}), sem download")
        executar(conn, RID, digital, {"ano": ANO}, lambda cur, exe: carregar_ano(cur, exe, digital, zip_local))
        with conn.cursor() as cur:
            cur.execute("SELECT status, inseridos, atualizados, excluidos, erro FROM etl.execucao WHERE recurso_id = %s ORDER BY id DESC LIMIT 1", (RID,))
            log(RID, f"resultado da execução: {cur.fetchone()}")

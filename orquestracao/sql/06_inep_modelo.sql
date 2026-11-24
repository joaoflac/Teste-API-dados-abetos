-- Modelo do INEP (Censo da Educação Superior), desenho híbrido (PLANEJAMENTO_IBGE.md §7D). PostgreSQL 17+. Requer 01 a 05.
--
--   DIMENSÕES que nunca se apagam   inep.ies, inep.ies_local, inep.curso, inep.cine_classificacao   (carga com p_excluir = false)
--   FATO por ano                    inep.curso_censo (co_curso, ano)   (MERGE com exclusão limitada ao ano do censo + trava)
--   REGRA (curada pela SECTI)       inep.regra_cti   (semente do CSV; depois editada pela API)
--   "ATIVO" é DERIVADO, nunca gravado: inep.v_curso_atual = fato do ano vigente + regra CT&I + sede na BA + não oculto.
--   Quem lê (API, painel) lê as views, nunca as tabelas-base.
--
-- Por que não existe coluna "ativo": consulta que a esquece erra em silêncio; a desativação em massa escapa da trava; a reativação e a
-- edição da curadoria se perdem na recarga. Medido pelo Opus em banco descartável e confirmado com os censos 2021-2024 reais.

CREATE SCHEMA IF NOT EXISTS inep;

-- ===================================================================================================== classificação CINE
-- Códigos são TEXTO: co_cine_rotulo tem letra (0916F01) e co_cine_area_geral tem zero à esquerda (05).
CREATE TABLE IF NOT EXISTS inep.cine_classificacao (
    co_cine_rotulo          text PRIMARY KEY,
    no_cine_rotulo          text NOT NULL,
    co_cine_area_detalhada  text,
    co_cine_area_especifica text,
    co_cine_area_geral      text NOT NULL,
    no_cine_area_geral      text,
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint REFERENCES etl.execucao(id)
);
COMMENT ON TABLE inep.cine_classificacao IS 'Hierarquia CINE (área geral > específica > detalhada > rótulo) como o INEP a publica. Dimensão: nunca é apagada.';
COMMENT ON COLUMN inep.cine_classificacao.co_cine_rotulo IS 'Rótulo CINE de 7 caracteres, ex.: 0916F01 (texto: tem letra)';
COMMENT ON COLUMN inep.cine_classificacao.co_cine_area_geral IS 'Área geral CINE com 2 dígitos, ex.: 05 (texto: tem zero à esquerda). As áreas 05 a 09 correspondem aos 5 tipos de curso do painel';

-- ===================================================================================================== regra CT&I
CREATE TABLE IF NOT EXISTS inep.regra_cti (
    co_cine_rotulo text PRIMARY KEY REFERENCES inep.cine_classificacao(co_cine_rotulo),
    status         text NOT NULL CHECK (status IN ('incluir', 'excluir', 'revisar')),
    observacao     text,
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint REFERENCES etl.execucao(id)
);
COMMENT ON TABLE inep.regra_cti IS 'Quais rótulos CINE contam como CT&I. Curada pela SECTI (semente: analise/regra_cti_rotulos.csv). Só status = incluir entra em v_curso_atual. Rótulo ausente daqui não entra.';
COMMENT ON COLUMN inep.regra_cti.status IS 'incluir | excluir | revisar. Mudar o status vale na hora: a regra é aplicada na view, não na carga';

-- ===================================================================================================== IES e campus
CREATE TABLE IF NOT EXISTS inep.ies (
    co_ies                      int PRIMARY KEY,
    no_ies                      text,
    sg_ies                      text,
    co_mantenedora              int,
    no_mantenedora              text,
    tp_categoria_administrativa smallint,
    tp_organizacao_academica    smallint,
    co_municipio_sede           int,            -- SEM FK: UNIVASF (PE) e UNILAB (CE) têm sede fora da BA
    no_municipio_sede           text,
    uf_sede                     text,
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint REFERENCES etl.execucao(id)
);
COMMENT ON TABLE inep.ies IS 'Instituições (matriz). Derivadas dos cursos presenciais da BA; o arquivo de IES só fornece atributos. Nunca é apagada.';
COMMENT ON COLUMN inep.ies.co_municipio_sede IS 'Município da sede (pode ficar fora da BA, por isso não há FK para ibge.municipio)';

-- Campus = par (IES, município de oferta). O INEP não tem código de campus.
CREATE TABLE IF NOT EXISTS inep.ies_local (
    co_ies       int NOT NULL REFERENCES inep.ies(co_ies),
    co_municipio int NOT NULL REFERENCES ibge.municipio(codigo_ibge),
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint REFERENCES etl.execucao(id),
    PRIMARY KEY (co_ies, co_municipio)
);
COMMENT ON TABLE inep.ies_local IS 'Campus = par (co_ies, co_municipio) onde há curso presencial. Dois campi da mesma IES no mesmo município viram um só. Nunca é apagada.';

-- ===================================================================================================== curso (dimensão) e fato por ano
CREATE TABLE IF NOT EXISTS inep.curso (
    co_curso           int PRIMARY KEY,
    co_ies             int NOT NULL,
    co_municipio       int NOT NULL,
    no_curso           text,
    tp_grau_academico  smallint,
    tp_rede            smallint,
    oculto_curadoria   boolean NOT NULL DEFAULT false,   -- decisão humana (via API); fora do _hash, o ETL nunca a toca
    motivo_oculto      text,
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint REFERENCES etl.execucao(id),
    FOREIGN KEY (co_ies, co_municipio) REFERENCES inep.ies_local(co_ies, co_municipio)
);
COMMENT ON TABLE inep.curso IS 'Cursos presenciais da BA nas áreas CINE 05 a 09 (universo CT&I). Dimensão: nunca é apagada. co_ies e co_municipio refletem o ÚLTIMO censo (33 cursos mudaram de IES entre 2022 e 2023).';
COMMENT ON COLUMN inep.curso.oculto_curadoria IS 'true = a SECTI escondeu o curso do painel. Preservada pelas recargas (fora das colunas de valor do MERGE)';

CREATE TABLE IF NOT EXISTS inep.curso_censo (
    co_curso       int  NOT NULL REFERENCES inep.curso(co_curso),
    ano            int  NOT NULL,
    co_cine_rotulo text NOT NULL REFERENCES inep.cine_classificacao(co_cine_rotulo),   -- por ano: o INEP reclassifica (67 cursos em 2023→2024)
    qt_vg_total    int,
    qt_ing         int,
    qt_mat         int,
    qt_conc        int,
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint REFERENCES etl.execucao(id),
    PRIMARY KEY (co_curso, ano)
);
COMMENT ON TABLE inep.curso_censo IS 'Fato por curso e ano do censo (vagas, ingressantes, matrículas, concluintes) e o rótulo CINE daquele ano. O curso que saiu do censo X simplesmente não tem linha em X.';
COMMENT ON COLUMN inep.curso_censo.qt_mat IS 'Matrículas no ano do censo';

-- ===================================================================================================== staging (truncada a cada carga)
CREATE UNLOGGED TABLE IF NOT EXISTS stg.inep_cine (co_cine_rotulo text, no_cine_rotulo text, co_cine_area_detalhada text,
    co_cine_area_especifica text, co_cine_area_geral text, no_cine_area_geral text, modificado_fonte_em date);
CREATE UNLOGGED TABLE IF NOT EXISTS stg.inep_regra_cti (co_cine_rotulo text, status text, observacao text, modificado_fonte_em date);
CREATE UNLOGGED TABLE IF NOT EXISTS stg.inep_ies (co_ies int, no_ies text, sg_ies text, co_mantenedora int, no_mantenedora text,
    tp_categoria_administrativa smallint, tp_organizacao_academica smallint, co_municipio_sede int, no_municipio_sede text,
    uf_sede text, modificado_fonte_em date);
CREATE UNLOGGED TABLE IF NOT EXISTS stg.inep_local (co_ies int, co_municipio int);
CREATE UNLOGGED TABLE IF NOT EXISTS stg.inep_curso (co_curso int, co_ies int, co_municipio int, no_curso text,
    tp_grau_academico smallint, tp_rede smallint, modificado_fonte_em date);
CREATE UNLOGGED TABLE IF NOT EXISTS stg.inep_curso_censo (co_curso int, ano int, co_cine_rotulo text, qt_vg_total int, qt_ing int,
    qt_mat int, qt_conc int, modificado_fonte_em date);

-- ===================================================================================================== parâmetros e ano vigente
-- Ano vigente = maior ano cuja carga TERMINOU BEM. Não é max(ano) da tabela: uma carga parcial ou falha de um censo novo
-- (status 'erro') nunca passa a valer, e recarregar um ano antigo não o faz voltar atrás.
CREATE OR REPLACE FUNCTION inep.ano_vigente() RETURNS int LANGUAGE sql STABLE AS $$
    SELECT max((e.escopo ->> 'ano')::int) FROM etl.execucao e JOIN etl.recurso r ON r.id = e.recurso_id
     WHERE r.fonte = 'INEP' AND e.status = 'ok' AND e.escopo ? 'ano' $$;

-- Filtro 6 do PLANO (IES com sede na BA, metodologia do Supabase): parâmetro do recurso mais recente, padrão true
CREATE OR REPLACE FUNCTION inep.exigir_sede_ba() RETURNS boolean LANGUAGE sql STABLE AS $$
    SELECT coalesce((SELECT (r.parametros ->> 'exigir_sede_ba')::boolean FROM etl.recurso r WHERE r.fonte = 'INEP'
                      ORDER BY (r.parametros ->> 'ano')::int DESC LIMIT 1), true) $$;

-- ===================================================================================================== views de leitura (embutem "ativo")
CREATE OR REPLACE VIEW inep.v_curso_atual AS
SELECT c.co_curso, c.no_curso, c.co_ies, i.sg_ies, i.no_ies, c.co_municipio, m.municipio AS no_municipio,
       cc.co_cine_rotulo, k.no_cine_rotulo, k.co_cine_area_geral, k.no_cine_area_geral,
       c.tp_grau_academico, c.tp_rede, cc.ano, cc.qt_vg_total, cc.qt_ing, cc.qt_mat, cc.qt_conc
FROM inep.curso_censo cc
JOIN inep.curso c ON c.co_curso = cc.co_curso
JOIN inep.ies i ON i.co_ies = c.co_ies
JOIN ibge.municipio m ON m.codigo_ibge = c.co_municipio
JOIN inep.cine_classificacao k ON k.co_cine_rotulo = cc.co_cine_rotulo
JOIN inep.regra_cti r ON r.co_cine_rotulo = cc.co_cine_rotulo AND r.status = 'incluir'
WHERE cc.ano = inep.ano_vigente() AND NOT c.oculto_curadoria AND (i.uf_sede = 'BA' OR NOT inep.exigir_sede_ba());
COMMENT ON VIEW inep.v_curso_atual IS 'Cursos CT&I do censo vigente: presentes no ano vigente, rótulo com regra incluir, sede na BA (parâmetro) e não ocultos. Use esta view, nunca a tabela inep.curso.';

CREATE OR REPLACE VIEW inep.v_campus_com_curso AS
SELECT co_ies, sg_ies, no_ies, co_municipio, no_municipio, ano, count(*) AS qtd_cursos, sum(qt_mat) AS qt_mat
FROM inep.v_curso_atual GROUP BY co_ies, sg_ies, no_ies, co_municipio, no_municipio, ano;
COMMENT ON VIEW inep.v_campus_com_curso IS 'Campi (IES + município) com pelo menos um curso CT&I no censo vigente. É o que a API do painel deve expor.';

-- ===================================================================================================== auditoria e procedência
SELECT audit.ativar('inep.cine_classificacao', '{co_cine_rotulo}');
SELECT audit.ativar('inep.regra_cti',          '{co_cine_rotulo}');
SELECT audit.ativar('inep.ies',                '{co_ies}');
SELECT audit.ativar('inep.ies_local',          '{co_ies,co_municipio}');
SELECT audit.ativar('inep.curso',              '{co_curso}');
SELECT audit.ativar('inep.curso_censo',        '{co_curso,ano}');

-- Dicionário: passa a cobrir o schema inep
CREATE OR REPLACE VIEW meta.v_dicionario AS
SELECT n.nspname || '.' || c.relname AS tabela, a.attname AS coluna, format_type(a.atttypid, a.atttypmod) AS tipo,
       col_description(c.oid, a.attnum) AS descricao, obj_description(c.oid, 'pg_class') AS descricao_tabela
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
WHERE n.nspname IN ('ibge', 'inep') AND c.relkind = 'r'
ORDER BY 1, a.attnum;

-- Procedência por linha: agora também as tabelas do INEP (substitui a versão de 05_auditoria.sql; rodar 06 depois de 05)
DROP VIEW IF EXISTS meta.v_linha_origem;
CREATE VIEW meta.v_linha_origem AS
WITH linhas AS (
    SELECT 'ibge.municipio' AS tabela, jsonb_build_object('codigo_ibge', codigo_ibge) AS chave, _criado_em, _modificado_em,
           _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM ibge.municipio
    UNION ALL SELECT 'ibge.populacao', jsonb_build_object('codigo_ibge', codigo_ibge, 'ano', ano, 'tipo', tipo), _criado_em, _modificado_em,
           _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM ibge.populacao
    UNION ALL SELECT 'ibge.pib_municipal', jsonb_build_object('codigo_ibge', codigo_ibge, 'ano', ano), _criado_em, _modificado_em,
           _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM ibge.pib_municipal
    UNION ALL SELECT 'ibge.malha', jsonb_build_object('codigo_ibge', codigo_ibge), _criado_em, _modificado_em,
           _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM ibge.malha
    UNION ALL SELECT 'inep.cine_classificacao', jsonb_build_object('co_cine_rotulo', co_cine_rotulo), _criado_em, _modificado_em,
           _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM inep.cine_classificacao
    UNION ALL SELECT 'inep.regra_cti', jsonb_build_object('co_cine_rotulo', co_cine_rotulo), _criado_em, _modificado_em,
           _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM inep.regra_cti
    UNION ALL SELECT 'inep.ies', jsonb_build_object('co_ies', co_ies), _criado_em, _modificado_em,
           _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM inep.ies
    UNION ALL SELECT 'inep.ies_local', jsonb_build_object('co_ies', co_ies, 'co_municipio', co_municipio), _criado_em, _modificado_em,
           _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM inep.ies_local
    UNION ALL SELECT 'inep.curso', jsonb_build_object('co_curso', co_curso), _criado_em, _modificado_em,
           _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM inep.curso
    UNION ALL SELECT 'inep.curso_censo', jsonb_build_object('co_curso', co_curso, 'ano', ano), _criado_em, _modificado_em,
           _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM inep.curso_censo
)
SELECT l.*, e.recurso_id AS recurso, r.fonte, r.url, e.inicio AS carga_em, e.escopo AS escopo_da_carga, e.disparo AS carga_disparo
FROM linhas l LEFT JOIN etl.execucao e ON e.id = l._execucao_id LEFT JOIN etl.recurso r ON r.id = e.recurso_id;
GRANT SELECT ON meta.v_linha_origem, meta.v_dicionario TO api_crud;

-- ===================================================================================================== papel da API
-- A API lê as views; edita a regra CT&I; oculta/mostra cursos. Não lê o fato nem as tabelas de dimensão (exceto as colunas abaixo).
GRANT USAGE ON SCHEMA inep TO api_crud;
GRANT SELECT ON inep.v_curso_atual, inep.v_campus_com_curso TO api_crud;
GRANT SELECT, INSERT, UPDATE, DELETE ON inep.regra_cti TO api_crud;
GRANT SELECT ON inep.cine_classificacao TO api_crud;   -- a tela de regra mostra o nome do rótulo
GRANT SELECT (co_curso, no_curso, oculto_curadoria, motivo_oculto), UPDATE (oculto_curadoria, motivo_oculto) ON inep.curso TO api_crud;

-- Modelo IBGE completo + metadados (PLANEJAMENTO_IBGE.md §7, §7A, §7B). PostgreSQL 17+.
-- Requer 01_controle.sql e 02_carga_incremental.sql (ibge.populacao).

CREATE SCHEMA IF NOT EXISTS ibge;
CREATE SCHEMA IF NOT EXISTS meta;

-- =====================================================================================================
-- Carga genérica (nível 3): a mesma regra para qualquer tabela com colunas de controle.
--   p_destino / p_stg  tabela final e staging (a staging tem as mesmas colunas de dados + modificado_fonte_em)
--   p_chaves           colunas da chave         p_valores  colunas de conteúdo (entram no _hash)
--   p_escopo           condição SQL sobre o alias {a} (ex.: '{a}.ano = ANY(''{2025}'')'); só dentro dela há DELETE
--   p_limite_exclusao_pct  TRAVA: mais de 10 exclusões E acima deste % do escopo -> exceção e rollback (padrão 10)
-- Linhas iguais: nada. Alteradas: versão anterior -> etl.historico, UPDATE no lugar.
-- Ausentes na fonte dentro do escopo: DELETE + etl.exclusao. Fora do escopo: intocadas.
-- =====================================================================================================
DROP FUNCTION IF EXISTS etl.merge_tabela(bigint, regclass, regclass, text[], text[], text);
CREATE OR REPLACE FUNCTION etl.merge_tabela(p_exec bigint, p_destino regclass, p_stg regclass,
                                            p_chaves text[], p_valores text[], p_escopo text DEFAULT 'true',
                                            p_limite_exclusao_pct numeric DEFAULT 10)
RETURNS TABLE (inseridos int, atualizados int, excluidos int) LANGUAGE plpgsql AS $$
DECLARE
    v_on    text := (SELECT string_agg(format('t.%1$I = s.%1$I', c), ' AND ') FROM unnest(p_chaves) c);
    v_hash  text := format('md5(row(%s)::text)', (SELECT string_agg(format('s.%I', c), ', ') FROM unnest(p_valores) c));
    v_set   text := (SELECT string_agg(format('%1$I = s.%1$I', c), ', ') FROM unnest(p_valores) c);
    v_cols  text := (SELECT string_agg(format('%I', c), ', ') FROM unnest(p_chaves || p_valores) c);
    v_vals  text := (SELECT string_agg(format('s.%I', c), ', ') FROM unnest(p_chaves || p_valores) c);
    v_chave text := (SELECT 'jsonb_build_object(' || string_agg(format('%L, t.%I', c, c), ', ') || ')' FROM unnest(p_chaves) c);
    v_total_escopo bigint;
BEGIN
    EXECUTE format('SELECT count(*) FROM %s t WHERE %s', p_destino, replace(p_escopo, '{a}', 't')) INTO v_total_escopo;
    DROP TABLE IF EXISTS _src; DROP TABLE IF EXISTS _res;
    EXECUTE format('CREATE TEMP TABLE _src ON COMMIT DROP AS SELECT s.*, %s AS _hash_novo FROM %s s WHERE %s',
                   v_hash, p_stg, replace(p_escopo, '{a}', 's'));

    EXECUTE format('INSERT INTO etl.historico (execucao_id, tabela, chave, linha_anterior)
                    SELECT %L::bigint, %L, %s, to_jsonb(t) FROM %s t JOIN _src s ON %s WHERE t._hash <> s._hash_novo',
                   p_exec, p_destino::text, v_chave, p_destino, v_on);

    EXECUTE format($m$
        CREATE TEMP TABLE _res ON COMMIT DROP AS
        WITH m AS (
            MERGE INTO %1$s t USING _src s ON %2$s
            WHEN MATCHED AND t._hash <> s._hash_novo THEN
                UPDATE SET %3$s, _hash = s._hash_novo, _modificado_em = now(),
                           _modificado_fonte_em = s.modificado_fonte_em, _execucao_id = %6$L::bigint
            WHEN NOT MATCHED BY TARGET THEN
                INSERT (%4$s, _hash, _modificado_fonte_em, _execucao_id)
                VALUES (%5$s, s._hash_novo, s.modificado_fonte_em, %6$L::bigint)
            WHEN NOT MATCHED BY SOURCE AND %7$s THEN
                DELETE
            RETURNING merge_action() AS acao, %8$s AS chave, to_jsonb(t) AS linha
        ) SELECT * FROM m$m$,
        p_destino, v_on, v_set, v_cols, v_vals, p_exec, replace(p_escopo, '{a}', 't'), v_chave);


    -- TRAVA: fonte devolveu dados incompletos? Exclusão em massa aborta a carga inteira (rollback).
    IF (SELECT count(*) FROM _res WHERE acao = 'DELETE') > 10
       AND (SELECT count(*) FROM _res WHERE acao = 'DELETE') > v_total_escopo * p_limite_exclusao_pct / 100 THEN
        RAISE EXCEPTION 'TRAVA DE EXCLUSAO em %: % de % linhas do escopo seriam excluidas (limite % por cento). Carga abortada; verifique a fonte.',
            p_destino, (SELECT count(*) FROM _res WHERE acao = 'DELETE'), v_total_escopo, p_limite_exclusao_pct;
    END IF;

    INSERT INTO etl.exclusao (execucao_id, tabela, chave, linha)
    SELECT p_exec, p_destino::text, chave, linha FROM _res WHERE acao = 'DELETE';

    RETURN QUERY SELECT count(*) FILTER (WHERE acao = 'INSERT')::int,
                        count(*) FILTER (WHERE acao = 'UPDATE')::int,
                        count(*) FILTER (WHERE acao = 'DELETE')::int FROM _res;
END $$;

-- =====================================================================================================
-- ibge.municipio — dimensão (tabela-mestre). Fontes: localidades (API), malhas/metadados (API), FTP PIB (tipologias)
-- =====================================================================================================
CREATE TABLE IF NOT EXISTS ibge.municipio (
    codigo_ibge                 int PRIMARY KEY,
    municipio                   text NOT NULL,
    uf                          text NOT NULL,
    codigo_microrregiao         int,  microrregiao text,
    codigo_mesorregiao          int,  mesorregiao text,
    codigo_regiao_imediata      int,  regiao_imediata text,  polo_regiao_imediata boolean,
    codigo_regiao_intermediaria int,  regiao_intermediaria text,  polo_regiao_intermediaria boolean,
    regiao_metropolitana        text,
    codigo_concentracao_urbana  int,  concentracao_urbana text,  tipo_concentracao_urbana text,
    codigo_arranjo_populacional int,  arranjo_populacional text,
    hierarquia_urbana           text, hierarquia_urbana_principal text,
    codigo_regiao_rural         int,  regiao_rural text,  regiao_rural_nucleo text,
    semiarido                   boolean,
    amazonia_legal              boolean,
    area_km2                    numeric(12,3),
    centroide_lon               numeric(9,4),
    centroide_lat               numeric(9,4),
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint
);
CREATE UNLOGGED TABLE IF NOT EXISTS stg.ibge_municipio (LIKE ibge.municipio);
ALTER TABLE stg.ibge_municipio DROP COLUMN IF EXISTS _hash, DROP COLUMN IF EXISTS _criado_em,
    DROP COLUMN IF EXISTS _modificado_em, DROP COLUMN IF EXISTS _execucao_id;
DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='stg' AND table_name='ibge_municipio' AND column_name='_modificado_fonte_em') THEN ALTER TABLE stg.ibge_municipio RENAME COLUMN _modificado_fonte_em TO modificado_fonte_em; END IF; END $$;

COMMENT ON TABLE  ibge.municipio IS 'Dimensão município (BA). Tabela-mestre: as demais fontes se juntam por codigo_ibge.';
COMMENT ON COLUMN ibge.municipio.codigo_ibge IS 'Código IBGE do município (7 dígitos). Fonte: localidades v1';
COMMENT ON COLUMN ibge.municipio.municipio IS 'Nome do município. Fonte: localidades v1';
COMMENT ON COLUMN ibge.municipio.microrregiao IS 'Microrregião geográfica (divisão de 1989). Fonte: localidades v1';
COMMENT ON COLUMN ibge.municipio.mesorregiao IS 'Mesorregião geográfica (divisão de 1989). Fonte: localidades v1';
COMMENT ON COLUMN ibge.municipio.regiao_imediata IS 'Região geográfica imediata (divisão de 2017). Fonte: localidades v1';
COMMENT ON COLUMN ibge.municipio.polo_regiao_imediata IS 'true = município polo da região imediata; false = entorno. Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.regiao_intermediaria IS 'Região geográfica intermediária (divisão de 2017). Fonte: localidades v1';
COMMENT ON COLUMN ibge.municipio.polo_regiao_intermediaria IS 'true = polo da região intermediária; false = entorno. Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.regiao_metropolitana IS 'Região metropolitana / RIDE / área de expansão. Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.concentracao_urbana IS 'Concentração urbana (Arranjos Populacionais 2015). Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.tipo_concentracao_urbana IS 'Média ou Grande concentração urbana. Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.arranjo_populacional IS 'Arranjo populacional (municípios integrados). Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.hierarquia_urbana IS 'Hierarquia urbana REGIC (8 níveis na BA). Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.hierarquia_urbana_principal IS 'Hierarquia urbana, categorias principais (5 níveis). Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.regiao_rural IS 'Região rural (classificação IBGE). Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.regiao_rural_nucleo IS 'Tipo de região rural segundo o núcleo. Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.semiarido IS 'Município do Semiárido. Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.amazonia_legal IS 'Município da Amazônia Legal. Fonte: FTP PIB dos Municípios';
COMMENT ON COLUMN ibge.municipio.area_km2 IS 'Área territorial (km²). Fonte: malhas v3 /metadados';
COMMENT ON COLUMN ibge.municipio.centroide_lon IS 'Longitude do centroide (WGS84). Fonte: malhas v3 /metadados';
COMMENT ON COLUMN ibge.municipio.centroide_lat IS 'Latitude do centroide (WGS84). Fonte: malhas v3 /metadados';

-- =====================================================================================================
-- ibge.pib_municipal — fato anual. Fonte: FTP PIB dos Municípios (base TXT oficial)
-- =====================================================================================================
CREATE TABLE IF NOT EXISTS ibge.pib_municipal (
    codigo_ibge                 int NOT NULL,
    ano                         int NOT NULL,
    pib_mil_reais               numeric(18,3),
    pib_per_capita_reais        numeric(18,2),
    vab_agropecuaria_mil_reais  numeric(18,3),
    vab_industria_mil_reais     numeric(18,3),
    vab_servicos_mil_reais      numeric(18,3),
    vab_adm_publica_mil_reais   numeric(18,3),
    vab_total_mil_reais         numeric(18,3),
    impostos_liquidos_mil_reais numeric(18,3),
    atividade_1                 text,
    atividade_2                 text,
    atividade_3                 text,
    provisorio                  boolean NOT NULL DEFAULT false,
    edicao                      text,
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint,
    PRIMARY KEY (codigo_ibge, ano)
);
CREATE UNLOGGED TABLE IF NOT EXISTS stg.ibge_pib_municipal (LIKE ibge.pib_municipal);
ALTER TABLE stg.ibge_pib_municipal DROP COLUMN IF EXISTS _hash, DROP COLUMN IF EXISTS _criado_em,
    DROP COLUMN IF EXISTS _modificado_em, DROP COLUMN IF EXISTS _execucao_id;
DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='stg' AND table_name='ibge_pib_municipal' AND column_name='_modificado_fonte_em') THEN ALTER TABLE stg.ibge_pib_municipal RENAME COLUMN _modificado_fonte_em TO modificado_fonte_em; END IF; END $$;

COMMENT ON TABLE  ibge.pib_municipal IS 'PIB dos Municípios (BA), 2010 em diante. Fonte: FTP IBGE, base TXT oficial.';
COMMENT ON COLUMN ibge.pib_municipal.pib_mil_reais IS 'PIB a preços correntes (R$ 1.000)';
COMMENT ON COLUMN ibge.pib_municipal.pib_per_capita_reais IS 'PIB per capita OFICIAL (R$). Não recalcular com a 6579: o IBGE usa outra população';
COMMENT ON COLUMN ibge.pib_municipal.vab_agropecuaria_mil_reais IS 'VAB agropecuária (R$ 1.000). Divulgado só até 2021';
COMMENT ON COLUMN ibge.pib_municipal.vab_industria_mil_reais IS 'VAB indústria (R$ 1.000). Divulgado só até 2021';
COMMENT ON COLUMN ibge.pib_municipal.vab_servicos_mil_reais IS 'VAB serviços exceto adm. pública (R$ 1.000). Divulgado só até 2021';
COMMENT ON COLUMN ibge.pib_municipal.vab_adm_publica_mil_reais IS 'VAB administração, defesa, educação e saúde públicas e seguridade (R$ 1.000). Divulgado só até 2021';
COMMENT ON COLUMN ibge.pib_municipal.vab_total_mil_reais IS 'VAB total (R$ 1.000). Divulgado só até 2021';
COMMENT ON COLUMN ibge.pib_municipal.impostos_liquidos_mil_reais IS 'Impostos líquidos de subsídios sobre produtos (R$ 1.000). Divulgado só até 2021';
COMMENT ON COLUMN ibge.pib_municipal.atividade_1 IS 'Atividade econômica com maior VAB (10 classes IBGE). Divulgado só até 2021';
COMMENT ON COLUMN ibge.pib_municipal.atividade_2 IS 'Atividade com segundo maior VAB. Divulgado só até 2021';
COMMENT ON COLUMN ibge.pib_municipal.atividade_3 IS 'Atividade com terceiro maior VAB. Divulgado só até 2021';
COMMENT ON COLUMN ibge.pib_municipal.provisorio IS 'true = ano sujeito a revisão na próxima edição (nota 1 do layout)';
COMMENT ON COLUMN ibge.pib_municipal.edicao IS 'Edição do FTP de onde veio a linha (ex.: 2022_2023)';

-- =====================================================================================================
-- ibge.malha — geometria municipal (GeoJSON em jsonb; migrar para PostGIS na VPS se adotado)
-- =====================================================================================================
CREATE TABLE IF NOT EXISTS ibge.malha (
    codigo_ibge int PRIMARY KEY,
    qualidade   text NOT NULL,
    geometria   jsonb NOT NULL,
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint
);
CREATE UNLOGGED TABLE IF NOT EXISTS stg.ibge_malha (codigo_ibge int, qualidade text, geometria jsonb, modificado_fonte_em date);
COMMENT ON TABLE  ibge.malha IS 'Malha municipal (BA). Fonte: malhas v3, GeoJSON';
COMMENT ON COLUMN ibge.malha.geometria IS 'Geometria GeoJSON (Polygon/MultiPolygon, WGS84)';
COMMENT ON COLUMN ibge.malha.qualidade IS 'Parâmetro "qualidade" da API de malhas (minima | intermediaria | maxima)';

COMMENT ON TABLE  ibge.populacao IS 'População residente por município e ano: estimativas (6579) e Censo (4709)';
COMMENT ON COLUMN ibge.populacao.tipo IS 'estimativa (agregado 6579, var 9324) | censo (agregado 4709, var 93)';
COMMENT ON COLUMN ibge.populacao.populacao IS 'Pessoas';

-- =====================================================================================================
-- meta — catálogo de fontes e metadados
-- =====================================================================================================
CREATE TABLE IF NOT EXISTS meta.fonte_tabela (
    id             text PRIMARY KEY,               -- sidra_6579, ftp_pib_municipios, localidades, malhas...
    fonte          text NOT NULL,
    nome           text,
    pesquisa       text,
    url            text,
    periodicidade  jsonb,
    metadados      jsonb,                          -- JSON bruto do /metadados ou cabeçalhos HTTP do arquivo
    _hash          text,
    _verificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_em timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS meta.variavel (
    fonte_tabela_id text REFERENCES meta.fonte_tabela(id),
    variavel_id     int,
    nome            text,
    unidade         text,
    PRIMARY KEY (fonte_tabela_id, variavel_id)
);
CREATE TABLE IF NOT EXISTS meta.periodo (
    fonte_tabela_id text REFERENCES meta.fonte_tabela(id),
    periodo         text,
    modificacao     date,
    PRIMARY KEY (fonte_tabela_id, periodo)
);
CREATE TABLE IF NOT EXISTS meta.layout_ftp (
    edicao text, posicao int, tamanho int, decimais int, tipo text, campo text, unidade text, coluna_destino text,
    PRIMARY KEY (edicao, posicao)
);
CREATE TABLE IF NOT EXISTS meta.calendario (
    id              int PRIMARY KEY,               -- id do evento no calendário IBGE
    produto_id      int,
    titulo          text,
    data_divulgacao timestamp,
    ano_referencia_inicio int,
    ano_referencia_fim    int
);

-- Dicionário: lido dos COMMENT ON das tabelas (a documentação vive junto com o esquema)
CREATE OR REPLACE VIEW meta.v_dicionario AS
SELECT n.nspname || '.' || c.relname AS tabela, a.attname AS coluna, format_type(a.atttypid, a.atttypmod) AS tipo,
       col_description(c.oid, a.attnum) AS descricao, obj_description(c.oid, 'pg_class') AS descricao_tabela
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
WHERE n.nspname = 'ibge' AND c.relkind = 'r'
ORDER BY 1, a.attnum;

-- Status por tabela do painel: fonte, data oficial, última carga, próxima divulgação
CREATE OR REPLACE VIEW meta.v_status_dataset AS
SELECT r.tabela_destino AS tabela, r.id AS recurso, r.fonte, r.url,
       coalesce((SELECT max(p.modificacao) FROM meta.periodo p WHERE p.fonte_tabela_id = r.parametros->>'fonte_tabela'),
                (SELECT (f.metadados->>'last_modified')::timestamptz::date FROM meta.fonte_tabela f
                  WHERE f.id = r.parametros->>'fonte_tabela')) AS ultima_modificacao_fonte,
       s.alterado_em AS ultima_alteracao_banco, s.verificado_em AS ultima_verificacao,
       s.status AS status_ultima_execucao, s.inseridos, s.atualizados, s.excluidos,
       (SELECT min(c.data_divulgacao) FROM meta.calendario c
         WHERE c.produto_id = (r.parametros->>'produto_id')::int AND c.data_divulgacao > now()) AS proxima_divulgacao,
       (SELECT max(c.data_divulgacao) FROM meta.calendario c
         WHERE c.produto_id = (r.parametros->>'produto_id')::int AND c.data_divulgacao <= now()) AS ultima_divulgacao
FROM etl.recurso r JOIN etl.v_status s ON s.recurso = r.id
WHERE r.tabela_destino IS NOT NULL;

-- Procedência de qualquer linha: chave -> datas da linha -> execução -> recurso/URL
CREATE OR REPLACE VIEW meta.v_linha_origem AS
WITH linhas AS (
    SELECT 'ibge.municipio' AS tabela, jsonb_build_object('codigo_ibge', codigo_ibge) AS chave,
           _criado_em, _modificado_em, _modificado_fonte_em, _execucao_id FROM ibge.municipio
    UNION ALL
    SELECT 'ibge.populacao', jsonb_build_object('codigo_ibge', codigo_ibge, 'ano', ano, 'tipo', tipo),
           _criado_em, _modificado_em, _modificado_fonte_em, _execucao_id FROM ibge.populacao
    UNION ALL
    SELECT 'ibge.pib_municipal', jsonb_build_object('codigo_ibge', codigo_ibge, 'ano', ano),
           _criado_em, _modificado_em, _modificado_fonte_em, _execucao_id FROM ibge.pib_municipal
    UNION ALL
    SELECT 'ibge.malha', jsonb_build_object('codigo_ibge', codigo_ibge),
           _criado_em, _modificado_em, _modificado_fonte_em, _execucao_id FROM ibge.malha
)
SELECT l.*, e.recurso_id AS recurso, r.fonte, r.url, e.inicio AS carga_em, e.escopo AS escopo_da_carga
FROM linhas l LEFT JOIN etl.execucao e ON e.id = l._execucao_id LEFT JOIN etl.recurso r ON r.id = e.recurso_id;

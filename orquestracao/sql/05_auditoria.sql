-- Auditoria: COMO cada dado entrou e QUEM o alterou (PostgreSQL 17+). Requer 01 a 04.
--
-- Dois escritores no banco: o ETL (Python que simula o Hop) e a API de CRUD do painel. O banco não adivinha quem é:
-- quem escreve declara o contexto no INÍCIO DA TRANSAÇÃO com  SELECT audit.contexto('api', '<usuario>', '<request_id>');
-- Sem contexto, a escrita é rotulada 'direto_sql' (psql, migração, alguém que contornou a API): visível, nunca silenciosa.
--
-- Camadas:
--   1. Colunas em cada linha: _criado_origem (como entrou), _origem e _modificado_por (última alteração).
--   2. audit.evento: um registro por INSERT/UPDATE/DELETE (antes, depois, campos alterados, origem, usuário, request, IP).
--   3. etl.execucao ganha disparo (agendado | manual | forcado), usuario e host: como a CARGA foi iniciada.
-- O log é um SCHEMA no mesmo banco, não um banco separado: o trigger grava na mesma transação do dado (atomicidade) e o
-- painel consegue cruzar linha e log com JOIN (PLANEJAMENTO_IBGE.md §7B). Banco separado exigiria dblink e perderia as duas coisas.
--
-- Regra de conflito (decisão a confirmar): a FONTE VENCE quando a partição é recarregada. Uma linha alterada pela API recebe
-- _hash 'api:...', diferente do hash da fonte, e o próximo MERGE que cobrir aquela partição a sobrescreve (a versão da API
-- fica em audit.evento e em etl.historico). Linha inserida pela API dentro de um escopo recarregado é excluída pelo MERGE
-- (e pode acionar a trava de exclusão em massa). Não há proteção de edição manual contra o ETL.
--
-- Segurança: o papel api_crud NÃO é dono das tabelas, então não consegue DISABLE TRIGGER nem alterar audit.evento. Quem é dono
-- ou superusuário (inclusive o usuário 'etl' do Postgres portátil de teste) pode: lá o teste prova o mecanismo, não a proteção.

CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.evento (
    id               bigserial PRIMARY KEY,
    ocorrido_em      timestamptz NOT NULL DEFAULT now(),
    tabela           text        NOT NULL,                                  -- ibge.pib_municipal
    operacao         char(1)     NOT NULL CHECK (operacao IN ('I', 'U', 'D')),
    chave            jsonb       NOT NULL,                                  -- {"codigo_ibge": 2927408, "ano": 2023}
    antes            jsonb,                                                 -- linha antes (U, D)
    depois           jsonb,                                                 -- linha depois (I, U)
    campos_alterados text[],                                                -- só U; colunas de controle (_*) ficam de fora
    origem           text        NOT NULL CHECK (origem IN ('etl', 'api', 'direto_sql')),
    usuario          text,                                                  -- api: usuário do painel; etl: nome do script; direto_sql: papel do banco
    request_id       text,                                                  -- correlação com o log da API
    execucao_id      bigint,                                                -- carga do ETL; sem FK de propósito: o log sobrevive à limpeza de etl.execucao
    db_role          text        NOT NULL DEFAULT session_user,
    ip               inet        DEFAULT inet_client_addr(),
    aplicacao        text        DEFAULT current_setting('application_name')
);
CREATE INDEX IF NOT EXISTS evento_tabela_idx ON audit.evento (tabela, ocorrido_em DESC);
CREATE INDEX IF NOT EXISTS evento_chave_idx  ON audit.evento USING gin (chave jsonb_path_ops);
COMMENT ON TABLE audit.evento IS 'Log de toda escrita nas tabelas de dados (trigger audit.registrar). Só INSERT; sem política de retenção ainda.';

-- Colunas de controle: fora do cálculo de "mudou?" e de campos_alterados
CREATE OR REPLACE FUNCTION audit.colunas_controle() RETURNS text[] LANGUAGE sql IMMUTABLE AS
$$ SELECT ARRAY['_hash', '_criado_em', '_modificado_em', '_modificado_fonte_em', '_execucao_id',
                '_origem', '_criado_origem', '_modificado_por'] $$;

-- Declara o contexto da escrita. p_local = true (padrão): vale só até o fim da transação, o que é obrigatório para a API atrás
-- de pool de conexões (chamar DENTRO da mesma transação do CRUD). O ETL usa a conexão dedicada e passa p_local = false.
CREATE OR REPLACE FUNCTION audit.contexto(p_origem text, p_usuario text, p_request_id text DEFAULT NULL, p_local boolean DEFAULT true)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    IF p_origem NOT IN ('etl', 'api') THEN
        RAISE EXCEPTION 'origem invalida: % (use etl ou api; direto_sql e o que sobra sem contexto)', p_origem;
    END IF;
    IF coalesce(p_usuario, '') = '' THEN RAISE EXCEPTION 'usuario obrigatorio'; END IF;
    PERFORM set_config('app.origem', p_origem, p_local),
            set_config('app.usuario', p_usuario, p_local),
            set_config('app.request_id', coalesce(p_request_id, ''), p_local);
END $$;

-- BEFORE INSERT/UPDATE: carimba a linha. Fora do ETL, o _hash passa a ser 'origem:md5', nunca igual ao da fonte
-- (o MERGE seguinte reconcilia a partição) e _modificado_em/_execucao_id deixam de apontar para uma carga que não escreveu isto.
CREATE OR REPLACE FUNCTION audit.carimbar() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_origem  text := coalesce(nullif(current_setting('app.origem', true), ''), 'direto_sql');
    v_usuario text := coalesce(nullif(current_setting('app.usuario', true), ''), session_user);
BEGIN
    IF TG_OP = 'UPDATE' AND v_origem <> 'etl'
       AND (to_jsonb(NEW) - audit.colunas_controle()) = (to_jsonb(OLD) - audit.colunas_controle()) THEN
        RETURN OLD;                              -- UPDATE que não muda nada: sem carimbo e sem evento
    END IF;
    NEW._origem := v_origem;
    NEW._modificado_por := v_usuario;
    NEW._criado_origem := CASE WHEN TG_OP = 'INSERT' THEN v_origem ELSE OLD._criado_origem END;   -- não forjável pelo UPDATE
    IF v_origem <> 'etl' THEN
        NEW._hash := v_origem || ':' || md5((to_jsonb(NEW) - audit.colunas_controle())::text);
        NEW._modificado_em := now();
        NEW._modificado_fonte_em := NULL;
        NEW._execucao_id := NULL;
    END IF;
    RETURN NEW;
END $$;

-- AFTER INSERT/UPDATE/DELETE: grava o evento. SECURITY DEFINER: quem escreve na tabela não precisa de INSERT em audit.evento.
-- As colunas da chave vêm dos argumentos do trigger (audit.ativar).
CREATE OR REPLACE FUNCTION audit.registrar() RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER SET search_path = pg_catalog, audit AS $$
DECLARE
    v_antes  jsonb := CASE WHEN TG_OP <> 'INSERT' THEN to_jsonb(OLD) END;
    v_depois jsonb := CASE WHEN TG_OP <> 'DELETE' THEN to_jsonb(NEW) END;
    v_ref    jsonb := coalesce(v_depois, v_antes);
    v_campos text[];
    v_origem text  := coalesce(nullif(current_setting('app.origem', true), ''), 'direto_sql');
BEGIN
    IF TG_OP = 'UPDATE' THEN
        SELECT array_agg(k ORDER BY k) INTO v_campos FROM jsonb_object_keys(v_depois) k
         WHERE k <> ALL (audit.colunas_controle()) AND v_depois -> k IS DISTINCT FROM v_antes -> k;
        IF v_campos IS NULL THEN RETURN NULL; END IF;
    END IF;
    INSERT INTO audit.evento (tabela, operacao, chave, antes, depois, campos_alterados, origem, usuario, request_id, execucao_id)
    VALUES (TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME, left(TG_OP, 1),
            (SELECT jsonb_object_agg(a, v_ref -> a) FROM unnest(TG_ARGV) a),
            v_antes, v_depois, v_campos, v_origem,
            coalesce(nullif(current_setting('app.usuario', true), ''), session_user),
            nullif(current_setting('app.request_id', true), ''),
            CASE WHEN v_origem = 'etl' THEN
                 coalesce(nullif(current_setting('app.execucao_id', true), '')::bigint,
                          CASE WHEN TG_OP <> 'DELETE' THEN (v_depois ->> '_execucao_id')::bigint END) END);
    RETURN NULL;
END $$;

-- Liga a auditoria em uma tabela de dados (a tabela precisa ter _hash, _criado_em, _modificado_em, _modificado_fonte_em, _execucao_id).
-- Linhas que já existem ficam como origem 'etl': até aqui o orquestrador era o único escritor.
-- Para as tabelas do INEP: SELECT audit.ativar('inep.curso', '{co_curso}');
CREATE OR REPLACE FUNCTION audit.ativar(p_tabela regclass, p_chaves text[]) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    EXECUTE format('ALTER TABLE %s ADD COLUMN IF NOT EXISTS _origem text, ADD COLUMN IF NOT EXISTS _criado_origem text,
                                   ADD COLUMN IF NOT EXISTS _modificado_por text', p_tabela);
    EXECUTE format('DROP TRIGGER IF EXISTS tg_audit_carimbo ON %s', p_tabela);
    EXECUTE format('DROP TRIGGER IF EXISTS tg_audit_evento ON %s', p_tabela);
    EXECUTE format($q$UPDATE %s SET _origem = 'etl', _criado_origem = 'etl', _modificado_por = 'orquestrador_simulado'
                      WHERE _origem IS NULL$q$, p_tabela);
    EXECUTE format('CREATE TRIGGER tg_audit_carimbo BEFORE INSERT OR UPDATE ON %s FOR EACH ROW EXECUTE FUNCTION audit.carimbar()', p_tabela);
    EXECUTE format('CREATE TRIGGER tg_audit_evento AFTER INSERT OR UPDATE OR DELETE ON %s FOR EACH ROW EXECUTE FUNCTION audit.registrar(%s)',
                   p_tabela, (SELECT string_agg(quote_literal(c), ', ') FROM unnest(p_chaves) c));
    EXECUTE format('COMMENT ON COLUMN %s._criado_origem IS %L', p_tabela, 'Como a linha entrou: etl | api | direto_sql');
    EXECUTE format('COMMENT ON COLUMN %s._origem IS %L', p_tabela, 'Origem da última alteração: etl | api | direto_sql');
    EXECUTE format('COMMENT ON COLUMN %s._modificado_por IS %L', p_tabela, 'Quem fez a última alteração (usuário do painel, script do ETL ou papel do banco)');
END $$;

-- Como a carga foi iniciada (etl.execucao): o orquestrador passa disparo; usuario e host se preenchem sozinhos
ALTER TABLE etl.execucao ADD COLUMN IF NOT EXISTS disparo text NOT NULL DEFAULT 'manual',
                         ADD COLUMN IF NOT EXISTS usuario text,
                         ADD COLUMN IF NOT EXISTS host text;
ALTER TABLE etl.execucao ALTER COLUMN usuario SET DEFAULT coalesce(nullif(current_setting('app.usuario', true), ''), session_user),
                         ALTER COLUMN host SET DEFAULT coalesce(inet_client_addr()::text, 'local');
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'execucao_disparo_chk' AND conrelid = 'etl.execucao'::regclass) THEN
        ALTER TABLE etl.execucao ADD CONSTRAINT execucao_disparo_chk CHECK (disparo IN ('agendado', 'manual', 'forcado'));
    END IF;
END $$;
COMMENT ON COLUMN etl.execucao.disparo IS 'agendado (cron/Hop) | manual (alguém rodou) | forcado (ignorou o checkpoint)';

SELECT audit.ativar('ibge.municipio',     '{codigo_ibge}');
SELECT audit.ativar('ibge.populacao',     '{codigo_ibge,ano,tipo}');
SELECT audit.ativar('ibge.pib_municipal', '{codigo_ibge,ano}');
SELECT audit.ativar('ibge.malha',         '{codigo_ibge}');

-- Procedência por linha agora inclui como entrou e quem alterou
DROP VIEW IF EXISTS meta.v_linha_origem;
CREATE VIEW meta.v_linha_origem AS
WITH linhas AS (
    SELECT 'ibge.municipio' AS tabela, jsonb_build_object('codigo_ibge', codigo_ibge) AS chave,
           _criado_em, _modificado_em, _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM ibge.municipio
    UNION ALL
    SELECT 'ibge.populacao', jsonb_build_object('codigo_ibge', codigo_ibge, 'ano', ano, 'tipo', tipo),
           _criado_em, _modificado_em, _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM ibge.populacao
    UNION ALL
    SELECT 'ibge.pib_municipal', jsonb_build_object('codigo_ibge', codigo_ibge, 'ano', ano),
           _criado_em, _modificado_em, _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM ibge.pib_municipal
    UNION ALL
    SELECT 'ibge.malha', jsonb_build_object('codigo_ibge', codigo_ibge),
           _criado_em, _modificado_em, _modificado_fonte_em, _execucao_id, _criado_origem, _origem, _modificado_por FROM ibge.malha
)
SELECT l.*, e.recurso_id AS recurso, r.fonte, r.url, e.inicio AS carga_em, e.escopo AS escopo_da_carga, e.disparo AS carga_disparo
FROM linhas l LEFT JOIN etl.execucao e ON e.id = l._execucao_id LEFT JOIN etl.recurso r ON r.id = e.recurso_id;

-- Papel da API de CRUD: lê e escreve nos dados, lê o log. Não é dono de nada. As senhas/LOGIN são criadas fora do repositório.
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api_crud') THEN CREATE ROLE api_crud NOLOGIN; END IF;
END $$;
GRANT USAGE ON SCHEMA ibge, audit, meta TO api_crud;
GRANT SELECT, INSERT, UPDATE, DELETE ON ibge.municipio, ibge.populacao, ibge.pib_municipal, ibge.malha TO api_crud;
GRANT SELECT ON audit.evento, meta.v_linha_origem, meta.v_dicionario, meta.v_status_dataset TO api_crud;
GRANT EXECUTE ON FUNCTION audit.contexto(text, text, text, boolean) TO api_crud;

-- Esquema de controle da orquestração (PostgreSQL 17+).
-- etl.recurso     catálogo do que é coletado e como detectar mudança
-- etl.checkpoint  última "impressão digital" de cada recurso (substitui orquestracao/estado_checkpoint.json)
-- etl.execucao    log de cada carga, com contagens de inseridos/atualizados/excluídos
-- etl.exclusao    auditoria: cada linha excluída fica registrada (chave + conteúdo), nada some sem rastro

CREATE SCHEMA IF NOT EXISTS etl;
CREATE SCHEMA IF NOT EXISTS stg;   -- staging: recebe o snapshot bruto (truncado a cada carga)

CREATE TABLE IF NOT EXISTS etl.recurso (
    id           text PRIMARY KEY,
    fonte        text NOT NULL,                       -- IBGE, INEP, BNDES, SICONFI, ANATEL, ANEEL
    modo         text NOT NULL CHECK (modo IN ('ETL_API', 'ELT_ARQUIVO')),
    metodo       text NOT NULL CHECK (metodo IN ('http', 'zip_crc', 'ckan', 'ibge_per', 'siconfi', 'hash_corpo', 'novo_ano')),
    url          text,
    parametros   jsonb NOT NULL DEFAULT '{}',
    tabela_destino text,                              -- ex.: ibge.populacao
    frequencia   text NOT NULL DEFAULT 'diaria',      -- diaria | semanal | mensal
    ativo        boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS etl.checkpoint (
    recurso_id    text PRIMARY KEY REFERENCES etl.recurso(id),
    digital       jsonb NOT NULL,                     -- ETag/Last-Modified, hash CKAN, CRCs do ZIP, datas por período...
    verificado_em timestamptz NOT NULL DEFAULT now(),
    alterado_em   timestamptz
);

CREATE TABLE IF NOT EXISTS etl.execucao (
    id           bigserial PRIMARY KEY,
    recurso_id   text NOT NULL REFERENCES etl.recurso(id),
    inicio       timestamptz NOT NULL DEFAULT now(),
    fim          timestamptz,
    status       text NOT NULL DEFAULT 'rodando' CHECK (status IN ('rodando', 'ok', 'erro', 'sem_mudanca')),
    escopo       jsonb,                               -- ex.: {"anos":[2025]} ou {"entes":[2910800]}
    digital_novo jsonb,                               -- só vira checkpoint se a carga terminar 'ok'
    inseridos    int DEFAULT 0,
    atualizados  int DEFAULT 0,
    excluidos    int DEFAULT 0,
    erro         text
);

CREATE TABLE IF NOT EXISTS etl.exclusao (
    id          bigserial PRIMARY KEY,
    execucao_id bigint REFERENCES etl.execucao(id),
    tabela      text NOT NULL,
    chave       jsonb NOT NULL,
    linha       jsonb NOT NULL,
    excluido_em timestamptz NOT NULL DEFAULT now()
);

-- Versão anterior de cada linha substituída por UPDATE (o MERGE do PG17 só devolve o valor novo)
CREATE TABLE IF NOT EXISTS etl.historico (
    id             bigserial PRIMARY KEY,
    execucao_id    bigint REFERENCES etl.execucao(id),
    tabela         text NOT NULL,
    chave          jsonb NOT NULL,
    linha_anterior jsonb NOT NULL,
    substituido_em timestamptz NOT NULL DEFAULT now()
);

-- Situação de cada recurso: último checkpoint e última execução (base de meta.v_status_dataset)
CREATE OR REPLACE VIEW etl.v_status AS
SELECT r.id AS recurso, r.fonte, r.tabela_destino,
       c.verificado_em, c.alterado_em,
       e.id AS ultima_execucao, e.status, e.inicio, e.fim, e.escopo,
       e.inseridos, e.atualizados, e.excluidos
FROM etl.recurso r
LEFT JOIN etl.checkpoint c ON c.recurso_id = r.id
LEFT JOIN LATERAL (SELECT * FROM etl.execucao x WHERE x.recurso_id = r.id ORDER BY x.id DESC LIMIT 1) e ON true;

-- Fecha a execução e só então avança o checkpoint (se a carga falhar, a próxima rodada tenta de novo).
CREATE OR REPLACE FUNCTION etl.finalizar(p_execucao bigint, p_status text, p_erro text DEFAULT NULL)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE e etl.execucao;
BEGIN
    UPDATE etl.execucao SET fim = now(), status = p_status, erro = p_erro WHERE id = p_execucao RETURNING * INTO e;
    IF p_status = 'ok' AND e.digital_novo IS NOT NULL THEN
        INSERT INTO etl.checkpoint (recurso_id, digital, verificado_em, alterado_em)
        VALUES (e.recurso_id, e.digital_novo, now(), now())
        ON CONFLICT (recurso_id) DO UPDATE SET digital = EXCLUDED.digital, verificado_em = now(), alterado_em = now();
    END IF;
END $$;

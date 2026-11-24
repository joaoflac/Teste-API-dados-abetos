-- Padrão de carga incremental com exclusão pontual (PostgreSQL 17+: MERGE ... WHEN NOT MATCHED BY SOURCE / RETURNING).
--
-- Fluxo:  fonte -> stg.<tabela> (snapshot do ESCOPO baixado) -> MERGE na tabela final
--   * linha nova (chave não existe)          -> INSERT
--   * linha existente com _hash diferente    -> UPDATE (só ela)
--   * linha igual                            -> nada (não reescreve, não gera WAL)
--   * linha que existe no banco, DENTRO do escopo baixado, mas sumiu da fonte -> DELETE (só ela) + auditoria
--   * linhas FORA do escopo baixado          -> intocadas (baixar só 2025 nunca apaga 2024)

-- ============================================================ Caso A: chave natural (IBGE população)
CREATE SCHEMA IF NOT EXISTS ibge;

-- Colunas de controle (PLANEJAMENTO_IBGE.md §7B):
--   _hash                 MD5 do conteúdo (não inclui datas)  -> decide se a linha mudou
--   _criado_em            entrada da linha no banco
--   _modificado_em        última mudança de CONTEÚDO (recarregar o mesmo valor não altera)
--   _modificado_fonte_em  data em que a fonte publicou o valor atual (IBGE: "modificacao" do período)
--   _execucao_id          carga que gravou a versão atual -> etl.execucao
CREATE TABLE IF NOT EXISTS ibge.populacao (
    codigo_ibge          int    NOT NULL,
    ano                  int    NOT NULL,
    tipo                 text   NOT NULL CHECK (tipo IN ('estimativa', 'censo')),
    populacao            bigint,
    fonte                text,
    _hash                text   NOT NULL,
    _criado_em           timestamptz NOT NULL DEFAULT now(),
    _modificado_em       timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date,
    _execucao_id         bigint,
    PRIMARY KEY (codigo_ibge, ano, tipo)
);

CREATE UNLOGGED TABLE IF NOT EXISTS stg.ibge_populacao (
    codigo_ibge int, ano int, tipo text, populacao bigint, fonte text, modificado_fonte_em date
);

-- p_tipo + p_anos = escopo vindo do verificador (períodos cujo "modificacao" mudou).
-- Linhas iguais: nada. Alteradas: versão antiga -> etl.historico, depois UPDATE no lugar.
-- Ausentes na fonte (dentro do escopo): DELETE + etl.exclusao. Fora do escopo: intocadas.
DROP FUNCTION IF EXISTS etl.carga_ibge_populacao(bigint, text, int[]);
CREATE OR REPLACE FUNCTION etl.carga_ibge_populacao(p_execucao bigint, p_tipo text, p_anos int[],
                                                    p_limite_exclusao_pct numeric DEFAULT 10)
RETURNS TABLE (inseridos int, atualizados int, excluidos int) LANGUAGE plpgsql AS $$
DECLARE v_total_escopo bigint;
BEGIN
    SELECT count(*) INTO v_total_escopo FROM ibge.populacao WHERE tipo = p_tipo AND ano = ANY (p_anos);
    CREATE TEMP TABLE _src ON COMMIT DROP AS
    SELECT s.*, md5(row(s.populacao, s.fonte)::text) AS _hash
    FROM stg.ibge_populacao s WHERE s.tipo = p_tipo AND s.ano = ANY (p_anos);

    INSERT INTO etl.historico (execucao_id, tabela, chave, linha_anterior)
    SELECT p_execucao, 'ibge.populacao',
           jsonb_build_object('codigo_ibge', t.codigo_ibge, 'ano', t.ano, 'tipo', t.tipo), to_jsonb(t)
    FROM ibge.populacao t JOIN _src s USING (codigo_ibge, ano, tipo)
    WHERE t._hash <> s._hash;

    CREATE TEMP TABLE _res ON COMMIT DROP AS
    WITH m AS (
        MERGE INTO ibge.populacao t
        USING _src s ON t.codigo_ibge = s.codigo_ibge AND t.ano = s.ano AND t.tipo = s.tipo
        WHEN MATCHED AND t._hash <> s._hash THEN
            UPDATE SET populacao = s.populacao, fonte = s.fonte, _hash = s._hash, _modificado_em = now(),
                       _modificado_fonte_em = s.modificado_fonte_em, _execucao_id = p_execucao
        WHEN NOT MATCHED BY TARGET THEN
            INSERT (codigo_ibge, ano, tipo, populacao, fonte, _hash, _modificado_fonte_em, _execucao_id)
            VALUES (s.codigo_ibge, s.ano, s.tipo, s.populacao, s.fonte, s._hash, s.modificado_fonte_em, p_execucao)
        WHEN NOT MATCHED BY SOURCE AND t.tipo = p_tipo AND t.ano = ANY (p_anos) THEN   -- escopo
            DELETE
        RETURNING merge_action() AS acao, t.*
    )
    SELECT * FROM m;


    -- TRAVA: fonte devolveu dados incompletos? Exclusão em massa aborta a carga inteira (rollback).
    IF (SELECT count(*) FROM _res WHERE acao = 'DELETE') > 10
       AND (SELECT count(*) FROM _res WHERE acao = 'DELETE') > v_total_escopo * p_limite_exclusao_pct / 100 THEN
        RAISE EXCEPTION 'TRAVA DE EXCLUSAO em %: % de % linhas do escopo seriam excluidas (limite % por cento). Carga abortada; verifique a fonte.',
            'ibge.populacao', (SELECT count(*) FROM _res WHERE acao = 'DELETE'), v_total_escopo, p_limite_exclusao_pct;
    END IF;

    INSERT INTO etl.exclusao (execucao_id, tabela, chave, linha)
    SELECT p_execucao, 'ibge.populacao', jsonb_build_object('codigo_ibge', codigo_ibge, 'ano', ano, 'tipo', tipo),
           to_jsonb(r) - 'acao'
    FROM _res r WHERE acao = 'DELETE';

    RETURN QUERY SELECT count(*) FILTER (WHERE acao = 'INSERT')::int,
                        count(*) FILTER (WHERE acao = 'UPDATE')::int,
                        count(*) FILTER (WHERE acao = 'DELETE')::int FROM _res;
END $$;


-- ============================================================ Caso B: sem chave natural (BNDES não automáticas)
-- numero_do_contrato se repete (subcréditos): 30 linhas de amostra, 16 contratos. A identidade da linha
-- passa a ser o hash do conteúdo + nº da ocorrência (linhas idênticas repetidas). Linha alterada na fonte
-- = DELETE da versão antiga + INSERT da nova; as demais 24 mil linhas ficam intocadas.
CREATE SCHEMA IF NOT EXISTS bndes;

CREATE TABLE IF NOT EXISTS bndes.operacao_nao_automatica (
    _hash          text NOT NULL,
    _ocorrencia    int  NOT NULL,
    dados          jsonb NOT NULL,                     -- colunas tipadas podem ser views/colunas geradas sobre o jsonb
    municipio_codigo int GENERATED ALWAYS AS ((dados->>'municipio_codigo')::int) STORED,
    uf             text GENERATED ALWAYS AS (dados->>'uf') STORED,
    _criado_em     timestamptz NOT NULL DEFAULT now(),
    _execucao_id   bigint,
    PRIMARY KEY (_hash, _ocorrencia)
);

CREATE UNLOGGED TABLE IF NOT EXISTS stg.bndes_operacao_nao_automatica (dados jsonb);

CREATE OR REPLACE FUNCTION etl.carga_bndes_nao_automatica(p_execucao bigint, p_uf text)
RETURNS TABLE (inseridos int, atualizados int, excluidos int) LANGUAGE plpgsql AS $$
BEGIN
    CREATE TEMP TABLE _res ON COMMIT DROP AS
    WITH h AS (
        SELECT dados, md5(dados::text) AS _hash FROM stg.bndes_operacao_nao_automatica WHERE dados->>'uf' = p_uf
    ), src AS (
        SELECT dados, _hash, row_number() OVER (PARTITION BY _hash)::int AS _ocorrencia FROM h
    ), m AS (
        MERGE INTO bndes.operacao_nao_automatica t
        USING src s ON t._hash = s._hash AND t._ocorrencia = s._ocorrencia
        WHEN NOT MATCHED BY TARGET THEN
            INSERT (_hash, _ocorrencia, dados, _execucao_id) VALUES (s._hash, s._ocorrencia, s.dados, p_execucao)
        WHEN NOT MATCHED BY SOURCE AND t.uf = p_uf THEN
            DELETE
        RETURNING merge_action() AS acao, t._hash, t._ocorrencia, t.dados
    )
    SELECT * FROM m;

    INSERT INTO etl.exclusao (execucao_id, tabela, chave, linha)
    SELECT p_execucao, 'bndes.operacao_nao_automatica', jsonb_build_object('_hash', _hash, '_ocorrencia', _ocorrencia), dados
    FROM _res WHERE acao = 'DELETE';

    RETURN QUERY SELECT count(*) FILTER (WHERE acao = 'INSERT')::int, 0,
                        count(*) FILTER (WHERE acao = 'DELETE')::int FROM _res;
END $$;

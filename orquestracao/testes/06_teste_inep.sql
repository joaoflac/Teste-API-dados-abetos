-- Teste do desenho híbrido do INEP (06_inep_modelo.sql) e de etl.merge_tabela(p_excluir => false).
-- Tudo dentro de BEGIN ... ROLLBACK, só dados fictícios (município 9900001, IES 9990001, rótulo TESTE01, ano 2099).
-- Rodar:  psql -h localhost -p 5433 -U etl -d painel -f orquestracao/testes/06_teste_inep.sql      (precisa de 01 a 06 aplicados)
-- Esperado: 'TESTE OK' ao final.
\set ON_ERROR_STOP on
BEGIN;
SELECT audit.contexto('etl', 'teste_06', NULL);
INSERT INTO etl.recurso (id, fonte, modo, metodo, tabela_destino, parametros)
VALUES ('teste_inep_2099', 'INEP', 'ELT_ARQUIVO', 'http', 'inep.curso_censo', '{"ano": 2099, "exigir_sede_ba": true}');
INSERT INTO etl.execucao (recurso_id, escopo, status) VALUES ('teste_inep_2099', '{"ano": 2099}', 'ok');
INSERT INTO ibge.municipio (codigo_ibge, municipio, uf, _hash) VALUES (9900001, 'Teste Um', 'BA', 'h');
INSERT INTO inep.cine_classificacao (co_cine_rotulo, no_cine_rotulo, co_cine_area_geral, no_cine_area_geral, _hash)
VALUES ('TESTE01', 'Rotulo de teste', '05', 'Area de teste', 'h');
INSERT INTO inep.regra_cti (co_cine_rotulo, status, _hash) VALUES ('TESTE01', 'incluir', 'h');
INSERT INTO inep.ies (co_ies, no_ies, sg_ies, uf_sede, _hash) VALUES (9990001, 'IES Teste', 'IT', 'BA', 'h'), (9990002, 'IES Fora', 'IF', 'PE', 'h');
INSERT INTO inep.ies_local (co_ies, co_municipio, _hash) VALUES (9990001, 9900001, 'h'), (9990002, 9900001, 'h');

\echo '--- 1. dimensão com p_excluir = false: o que sumiu da carga NÃO é apagado'
INSERT INTO inep.curso (co_curso, co_ies, co_municipio, no_curso, _hash)
SELECT c, 9990001, 9900001, 'Curso ' || c, 'h' FROM generate_series(9990001, 9990030) c;
TRUNCATE stg.inep_curso;
INSERT INTO stg.inep_curso (co_curso, co_ies, co_municipio, no_curso, modificado_fonte_em)
SELECT c, 9990001, 9900001, 'Curso ' || c || ' (renomeado)', '2099-01-01' FROM generate_series(9990001, 9990010) c;   -- só 10 dos 30
CREATE TEMP TABLE r1 AS SELECT * FROM etl.merge_tabela(currval('etl.execucao_id_seq'), 'inep.curso', 'stg.inep_curso',
    '{co_curso}', '{co_ies,co_municipio,no_curso,tp_grau_academico,tp_rede}', 'true', 10, false);
DO $$ BEGIN
  IF (SELECT row(inseridos, atualizados, excluidos)::text FROM r1) <> '(0,10,0)' THEN RAISE EXCEPTION 'TESTE FALHOU: p_excluir=false deveria atualizar 10 e excluir 0 (%)', (SELECT row(inseridos, atualizados, excluidos)::text FROM r1); END IF;
  IF (SELECT count(*) FROM inep.curso WHERE co_curso BETWEEN 9990001 AND 9990030) <> 30 THEN RAISE EXCEPTION 'TESTE FALHOU: algum curso foi apagado'; END IF;
END $$;

\echo '--- 2. fato por ano: a exclusão só alcança o ano carregado e a trava vale 20%'
INSERT INTO inep.curso_censo (co_curso, ano, co_cine_rotulo, qt_mat, _hash)
SELECT c, 2098, 'TESTE01', 10, 'h' FROM generate_series(9990001, 9990030) c;
INSERT INTO inep.curso_censo (co_curso, ano, co_cine_rotulo, qt_mat, _hash)
SELECT c, 2099, 'TESTE01', 10, 'h' FROM generate_series(9990001, 9990030) c;
TRUNCATE stg.inep_curso_censo;
INSERT INTO stg.inep_curso_censo SELECT c, 2099, 'TESTE01', 1, 1, 12, 1, '2099-01-01' FROM generate_series(9990001, 9990027) c;   -- 3 saíram (10%)
CREATE TEMP TABLE r2 AS SELECT * FROM etl.merge_tabela(currval('etl.execucao_id_seq'), 'inep.curso_censo', 'stg.inep_curso_censo',
    '{co_curso,ano}', '{co_cine_rotulo,qt_vg_total,qt_ing,qt_mat,qt_conc}', '{a}.ano = 2099', 20, true);
DO $$ BEGIN
  IF (SELECT excluidos FROM r2) <> 3 THEN RAISE EXCEPTION 'TESTE FALHOU: devia excluir 3 de 2099'; END IF;
  IF (SELECT count(*) FROM inep.curso_censo WHERE ano = 2098 AND co_curso >= 9990001) <> 30 THEN RAISE EXCEPTION 'TESTE FALHOU: 2098 foi tocado'; END IF;
  IF (SELECT count(*) FROM etl.exclusao WHERE tabela = 'inep.curso_censo') <> 3 THEN RAISE EXCEPTION 'TESTE FALHOU: etl.exclusao'; END IF;
END $$;
DROP TABLE _src, _res;
TRUNCATE stg.inep_curso_censo;
INSERT INTO stg.inep_curso_censo SELECT c, 2099, 'TESTE01', 1, 1, 12, 1, '2099-01-01' FROM generate_series(9990001, 9990010) c;   -- 17 saem de 27 (63%)
DO $$ BEGIN
  PERFORM * FROM etl.merge_tabela(currval('etl.execucao_id_seq'), 'inep.curso_censo', 'stg.inep_curso_censo',
      '{co_curso,ano}', '{co_cine_rotulo,qt_vg_total,qt_ing,qt_mat,qt_conc}', '{a}.ano = 2099', 20, true);
  RAISE EXCEPTION 'TESTE FALHOU: a trava de 20%% devia abortar 17 de 27';
EXCEPTION WHEN raise_exception THEN
  IF SQLERRM NOT LIKE 'TRAVA DE EXCLUSAO%' THEN RAISE; END IF;
END $$;

\echo '--- 3. "ativo" é derivado: ano vigente ignora carga com erro e a view aplica regra, sede e curadoria'
INSERT INTO etl.execucao (recurso_id, escopo, status) VALUES ('teste_inep_2099', '{"ano": 2100}', 'erro');   -- carga parcial que falhou
INSERT INTO inep.curso_censo (co_curso, ano, co_cine_rotulo, qt_mat, _hash) VALUES (9990001, 2100, 'TESTE01', 1, 'h');
UPDATE inep.curso SET co_ies = 9990002 WHERE co_curso = 9990028;   -- IES com sede em PE
INSERT INTO inep.curso_censo (co_curso, ano, co_cine_rotulo, qt_mat, _hash) VALUES (9990028, 2099, 'TESTE01', 5, 'h');
DO $$ BEGIN
  IF inep.ano_vigente() <> 2099 THEN RAISE EXCEPTION 'TESTE FALHOU: ano vigente devia ser 2099 (carga 2100 deu erro), veio %', inep.ano_vigente(); END IF;
  IF (SELECT count(*) FROM inep.v_curso_atual WHERE co_curso BETWEEN 9990001 AND 9990030) <> 27 THEN
     RAISE EXCEPTION 'TESTE FALHOU: view devia ter 27 cursos (28 de 2099 menos o de sede em PE), veio %', (SELECT count(*) FROM inep.v_curso_atual WHERE co_curso BETWEEN 9990001 AND 9990030); END IF;
END $$;
UPDATE etl.recurso SET parametros = jsonb_set(parametros, '{exigir_sede_ba}', 'false') WHERE id = 'teste_inep_2099';
DO $$ BEGIN
  IF (SELECT count(*) FROM inep.v_curso_atual WHERE co_curso = 9990028) <> 1 THEN RAISE EXCEPTION 'TESTE FALHOU: com exigir_sede_ba=false o curso da IES de PE devia aparecer'; END IF;
END $$;
UPDATE inep.regra_cti SET status = 'excluir' WHERE co_cine_rotulo = 'TESTE01';
DO $$ BEGIN
  IF (SELECT count(*) FROM inep.v_curso_atual WHERE co_curso BETWEEN 9990001 AND 9990030) <> 0 THEN RAISE EXCEPTION 'TESTE FALHOU: regra excluir devia esvaziar a view na hora'; END IF;
END $$;
UPDATE inep.regra_cti SET status = 'incluir' WHERE co_cine_rotulo = 'TESTE01';

\echo '--- 4. curadoria pela API (api_crud) sobrevive à recarga do ETL; a API não lê o fato nem edita dados da fonte'
SET LOCAL ROLE api_crud;
SELECT audit.contexto('api', 'maria@secti', 'req-inep-1');
UPDATE inep.curso SET oculto_curadoria = true, motivo_oculto = 'duplicado no painel' WHERE co_curso = 9990001;
DO $$ BEGIN
  BEGIN PERFORM 1 FROM inep.curso_censo LIMIT 1; RAISE EXCEPTION 'TESTE FALHOU: api_crud leu o fato diretamente';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
  BEGIN UPDATE inep.curso SET no_curso = 'x' WHERE co_curso = 9990002; RAISE EXCEPTION 'TESTE FALHOU: api_crud alterou coluna de dados do curso';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
RESET ROLE;
SELECT audit.contexto('etl', 'teste_06', NULL);
DO $$ BEGIN
  IF (SELECT _hash NOT LIKE 'api:%' FROM inep.curso WHERE co_curso = 9990001) THEN RAISE EXCEPTION 'TESTE FALHOU: edicao da API devia marcar o _hash'; END IF;
  IF (SELECT _origem FROM inep.curso WHERE co_curso = 9990001) <> 'api' THEN RAISE EXCEPTION 'TESTE FALHOU: origem da edicao'; END IF;
END $$;
TRUNCATE stg.inep_curso;
DROP TABLE IF EXISTS _src, _res;
INSERT INTO stg.inep_curso (co_curso, co_ies, co_municipio, no_curso, modificado_fonte_em)
SELECT c, 9990001, 9900001, 'Curso ' || c || ' (de novo)', '2099-02-01' FROM generate_series(9990001, 9990027) c;
SELECT * FROM etl.merge_tabela(currval('etl.execucao_id_seq'), 'inep.curso', 'stg.inep_curso',
    '{co_curso}', '{co_ies,co_municipio,no_curso,tp_grau_academico,tp_rede}', 'true', 10, false) \gset
DO $$ DECLARE c record; BEGIN
  SELECT * INTO c FROM inep.curso WHERE co_curso = 9990001;
  IF c.no_curso <> 'Curso 9990001 (de novo)' OR c._origem <> 'etl' THEN RAISE EXCEPTION 'TESTE FALHOU: o ETL devia atualizar o nome (fonte vence nos valores): %', to_jsonb(c); END IF;
  IF NOT c.oculto_curadoria OR c.motivo_oculto <> 'duplicado no painel' THEN RAISE EXCEPTION 'TESTE FALHOU: a recarga apagou a curadoria: %', to_jsonb(c); END IF;
  IF (SELECT count(*) FROM inep.v_curso_atual WHERE co_curso = 9990001) <> 0 THEN RAISE EXCEPTION 'TESTE FALHOU: curso oculto apareceu na view'; END IF;
  IF NOT EXISTS (SELECT 1 FROM audit.evento WHERE tabela = 'inep.curso' AND origem = 'api' AND usuario = 'maria@secti' AND request_id = 'req-inep-1'
                   AND campos_alterados = ARRAY['motivo_oculto', 'oculto_curadoria']) THEN RAISE EXCEPTION 'TESTE FALHOU: evento da curadoria'; END IF;
  RAISE NOTICE 'TESTE OK';
END $$;
ROLLBACK;

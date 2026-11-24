-- Teste de 04_fk_ibge.sql e 05_auditoria.sql. Tudo dentro de BEGIN ... ROLLBACK: não deixa nada no banco.
-- Só dados fictícios (município 9900001/9900002, ano 1900): a exclusão por escopo apagaria dados reais do mesmo ano.
-- Rodar:  psql -h localhost -p 5433 -U etl -d painel -f orquestracao/testes/05_teste_auditoria.sql
-- Esperado: 'TESTE OK' ao final. Qualquer falha aborta com a mensagem da verificação.
\set ON_ERROR_STOP on
BEGIN;

INSERT INTO etl.recurso (id, fonte, modo, metodo, tabela_destino) VALUES ('teste_aud', 'IBGE', 'ETL_API', 'ibge_per', 'ibge.populacao');

\echo '--- 1. FK: população de município inexistente é rejeitada'
DO $$ BEGIN
  INSERT INTO ibge.populacao (codigo_ibge, ano, tipo, populacao, _hash) VALUES (9900099, 1900, 'estimativa', 1, 'x');
  RAISE EXCEPTION 'TESTE FALHOU: FK nao rejeitou municipio inexistente';
EXCEPTION WHEN foreign_key_violation THEN NULL; END $$;

\echo '--- 2. API (papel api_crud): insert, update, update sem mudança, delete'
SET LOCAL ROLE api_crud;
SELECT audit.contexto('api', 'maria@secti', 'req-1');
INSERT INTO ibge.municipio (codigo_ibge, municipio, uf) VALUES (9900001, 'Teste Um', 'BA');
INSERT INTO ibge.populacao (codigo_ibge, ano, tipo, populacao, fonte) VALUES (9900001, 1900, 'estimativa', 1000, 'api');
UPDATE ibge.populacao SET populacao = 1500 WHERE codigo_ibge = 9900001 AND ano = 1900;
UPDATE ibge.populacao SET populacao = 1500 WHERE codigo_ibge = 9900001 AND ano = 1900;   -- sem mudança
RESET ROLE;
DO $$ DECLARE r record; BEGIN
  SELECT * INTO r FROM ibge.populacao WHERE codigo_ibge = 9900001 AND ano = 1900;
  IF r._criado_origem <> 'api' OR r._origem <> 'api' OR r._modificado_por <> 'maria@secti' OR r._hash NOT LIKE 'api:%' OR r._execucao_id IS NOT NULL
     THEN RAISE EXCEPTION 'TESTE FALHOU: carimbo da API incorreto: %', to_jsonb(r); END IF;
  IF (SELECT count(*) FROM audit.evento WHERE tabela = 'ibge.populacao' AND chave->>'codigo_ibge' = '9900001') <> 2
     THEN RAISE EXCEPTION 'TESTE FALHOU: esperava 2 eventos (I + U); o UPDATE sem mudanca nao deve gerar evento'; END IF;
  IF (SELECT campos_alterados FROM audit.evento WHERE tabela = 'ibge.populacao' AND operacao = 'U' AND chave->>'codigo_ibge' = '9900001') <> ARRAY['populacao']
     THEN RAISE EXCEPTION 'TESTE FALHOU: campos_alterados'; END IF;
  IF (SELECT usuario || origem || request_id FROM audit.evento WHERE tabela = 'ibge.populacao' AND operacao = 'I' AND chave->>'codigo_ibge' = '9900001') <> 'maria@secti' || 'api' || 'req-1'
     THEN RAISE EXCEPTION 'TESTE FALHOU: usuario/origem/request_id do evento'; END IF;
END $$;

\echo '--- 3. papel api_crud não consegue desligar trigger nem adulterar o log'
SET LOCAL ROLE api_crud;
DO $$ BEGIN
  BEGIN ALTER TABLE ibge.populacao DISABLE TRIGGER ALL; RAISE EXCEPTION 'TESTE FALHOU: api_crud desligou o trigger';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
  BEGIN UPDATE audit.evento SET usuario = 'x'; RAISE EXCEPTION 'TESTE FALHOU: api_crud alterou o log';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
  BEGIN DELETE FROM audit.evento; RAISE EXCEPTION 'TESTE FALHOU: api_crud apagou o log';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
RESET ROLE;

\echo '--- 4. ETL sobrescreve a edição da API quando a partição é recarregada (a fonte vence)'
SELECT audit.contexto('etl', 'orquestrador_simulado', NULL);
INSERT INTO etl.execucao (recurso_id, escopo, disparo) VALUES ('teste_aud', '{"anos":[1900]}', 'agendado');
SELECT set_config('app.execucao_id', currval('etl.execucao_id_seq')::text, true);
TRUNCATE stg.ibge_populacao;
INSERT INTO stg.ibge_populacao VALUES (9900001, 1900, 'estimativa', 2000, 'ibge', '1900-12-30');
CREATE TEMP TABLE r AS SELECT * FROM etl.carga_ibge_populacao(currval('etl.execucao_id_seq'), 'estimativa', '{1900}');
DO $$ DECLARE x record; BEGIN
  IF (SELECT row(inseridos, atualizados, excluidos)::text FROM r) <> '(0,1,0)' THEN RAISE EXCEPTION 'TESTE FALHOU: ETL devia atualizar 1 linha'; END IF;
  SELECT * INTO x FROM ibge.populacao WHERE codigo_ibge = 9900001 AND ano = 1900;
  IF x.populacao <> 2000 OR x._origem <> 'etl' OR x._criado_origem <> 'api' OR x._hash <> md5(row(2000::bigint, 'ibge'::text)::text)
     OR x._modificado_por <> 'orquestrador_simulado' THEN RAISE EXCEPTION 'TESTE FALHOU: linha apos ETL: %', to_jsonb(x); END IF;
  IF NOT EXISTS (SELECT 1 FROM audit.evento WHERE operacao = 'U' AND origem = 'etl' AND chave->>'codigo_ibge' = '9900001'
                   AND antes->>'_origem' = 'api' AND execucao_id = currval('etl.execucao_id_seq'))
     THEN RAISE EXCEPTION 'TESTE FALHOU: evento do ETL (com a versao da API em "antes") nao encontrado'; END IF;
  IF NOT EXISTS (SELECT 1 FROM etl.historico WHERE linha_anterior->>'_origem' = 'api')
     THEN RAISE EXCEPTION 'TESTE FALHOU: etl.historico deveria guardar a versao da API'; END IF;
END $$;

\echo '--- 5. ETL exclui o que sumiu do escopo e o log registra D com a execução'
TRUNCATE stg.ibge_populacao;
DROP TABLE r, _src, _res;   -- em produção cada carga é uma transação própria; aqui são duas na mesma
CREATE TEMP TABLE r AS SELECT * FROM etl.carga_ibge_populacao(currval('etl.execucao_id_seq'), 'estimativa', '{1900}');
DO $$ BEGIN
  IF (SELECT excluidos FROM r) <> 1 THEN RAISE EXCEPTION 'TESTE FALHOU: ETL devia excluir 1 linha'; END IF;
  IF NOT EXISTS (SELECT 1 FROM audit.evento WHERE operacao = 'D' AND origem = 'etl' AND execucao_id = currval('etl.execucao_id_seq'))
     THEN RAISE EXCEPTION 'TESTE FALHOU: evento D do ETL'; END IF;
END $$;

\echo '--- 6. FK RESTRICT: município com filhas não pode ser excluído'
INSERT INTO ibge.populacao (codigo_ibge, ano, tipo, populacao, fonte, _hash) VALUES (9900001, 1900, 'estimativa', 1, 'x', 'h');
DO $$ BEGIN
  BEGIN DELETE FROM ibge.municipio WHERE codigo_ibge = 9900001; RAISE EXCEPTION 'TESTE FALHOU: excluiu municipio com filha';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
END $$;

\echo '--- 7. escrita sem contexto vira direto_sql'
SELECT set_config('app.origem', '', true), set_config('app.usuario', '', true);
UPDATE ibge.municipio SET municipio = 'Teste Um (editado no psql)' WHERE codigo_ibge = 9900001;
DO $$ BEGIN
  IF (SELECT _origem FROM ibge.municipio WHERE codigo_ibge = 9900001) <> 'direto_sql'
     OR (SELECT _modificado_por FROM ibge.municipio WHERE codigo_ibge = 9900001) <> session_user
     OR (SELECT _hash FROM ibge.municipio WHERE codigo_ibge = 9900001) NOT LIKE 'direto_sql:%'
     THEN RAISE EXCEPTION 'TESTE FALHOU: escrita sem contexto deveria ser direto_sql'; END IF;
  IF NOT EXISTS (SELECT 1 FROM meta.v_linha_origem WHERE tabela = 'ibge.municipio' AND chave->>'codigo_ibge' = '9900001' AND _origem = 'direto_sql')
     THEN RAISE EXCEPTION 'TESTE FALHOU: meta.v_linha_origem'; END IF;
  RAISE NOTICE 'TESTE OK';
END $$;
ROLLBACK;

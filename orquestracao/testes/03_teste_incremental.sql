-- Teste do padrão incremental com dados sintéticos.
-- ISOLADO: usa anos (1900/1901) e códigos (99000xx) fictícios. NUNCA usar anos/códigos reais: a exclusão por
-- escopo apagaria as linhas reais do mesmo ano que não estão no snapshot do teste.
-- Rodar:  psql -h localhost -p 5433 -U etl -d painel -f orquestracao/testes/03_teste_incremental.sql
-- Esperado: carga 1 = 4 inseridos; carga 2 = 1 inserido, 1 atualizado, 1 excluído; carga 3 = nada;
--           1900 nunca é tocado; o valor antigo de Salvador 1901 vai para etl.historico.
\set ON_ERROR_STOP on
INSERT INTO etl.recurso (id, fonte, modo, metodo, tabela_destino)
VALUES ('teste_pop', 'IBGE', 'ETL_API', 'ibge_per', 'ibge.populacao') ON CONFLICT DO NOTHING;
DELETE FROM ibge.populacao WHERE codigo_ibge IN (9900001, 9900002, 9900003) AND ano IN (1900, 1901) AND fonte = 'teste';
DELETE FROM etl.exclusao WHERE linha->>'fonte' = 'teste';
DELETE FROM etl.historico WHERE linha_anterior->>'fonte' = 'teste';
CREATE TEMP TABLE r (carga int, inseridos int, atualizados int, excluidos int);

\echo '--- carga 1 (inicial, anos 1900 e 1901)'
TRUNCATE stg.ibge_populacao;
INSERT INTO stg.ibge_populacao VALUES
  (9900001, 1900, 'estimativa', 2568928, 'teste', '1900-12-30'), (9900001, 1901, 'estimativa', 2564204, 'teste', '1901-08-28'),
  (9900002, 1900, 'estimativa', 656000, 'teste', '1900-12-30'),  (9900002, 1901, 'estimativa', 657000, 'teste', '1901-08-28');
INSERT INTO etl.execucao (recurso_id, escopo) VALUES ('teste_pop', '{"anos":[1900,1901]}');
INSERT INTO r SELECT 1, * FROM etl.carga_ibge_populacao(currval('etl.execucao_id_seq'), 'estimativa', '{1900,1901}');

\echo '--- carga 2 (IBGE revisou 1901: 9900001 mudou, 9900002 sumiu, 9900003 entrou)'
TRUNCATE stg.ibge_populacao;
INSERT INTO stg.ibge_populacao VALUES
  (9900001, 1901, 'estimativa', 2570000, 'teste', '2026-08-28'), (9900003, 1901, 'estimativa', 324000, 'teste', '2026-08-28');
INSERT INTO etl.execucao (recurso_id, escopo) VALUES ('teste_pop', '{"anos":[1901]}');
INSERT INTO r SELECT 2, * FROM etl.carga_ibge_populacao(currval('etl.execucao_id_seq'), 'estimativa', '{1901}');

\echo '--- carga 3 (mesmo snapshot de novo: nada muda)'
INSERT INTO r SELECT 3, * FROM etl.carga_ibge_populacao(currval('etl.execucao_id_seq'), 'estimativa', '{1901}');
SELECT * FROM r ORDER BY carga;

\echo '--- estado final (1900 intacto, Feira 1901 excluída)'
SELECT codigo_ibge, ano, populacao, _modificado_fonte_em, _execucao_id,
       _criado_em = _modificado_em AS nunca_alterada
FROM ibge.populacao WHERE fonte = 'teste' ORDER BY ano, codigo_ibge;
\echo '--- historico (valor anterior das linhas substituídas)'
SELECT chave, linha_anterior->>'populacao' AS populacao_anterior FROM etl.historico WHERE linha_anterior->>'fonte' = 'teste';
\echo '--- exclusoes'
SELECT chave, linha->>'populacao' AS populacao_excluida FROM etl.exclusao WHERE linha->>'fonte' = 'teste';

-- Verificação automática
DO $$ BEGIN
  IF (SELECT array_agg(row(inseridos, atualizados, excluidos)::text ORDER BY carga) FROM r)
     <> ARRAY['(4,0,0)', '(1,1,1)', '(0,0,0)'] THEN RAISE EXCEPTION 'TESTE FALHOU: contagens inesperadas'; END IF;
  RAISE NOTICE 'TESTE OK';
END $$;
DELETE FROM ibge.populacao WHERE fonte = 'teste';
DELETE FROM etl.historico WHERE linha_anterior->>'fonte' = 'teste';
DELETE FROM etl.exclusao WHERE linha->>'fonte' = 'teste';
DELETE FROM etl.execucao WHERE recurso_id = 'teste_pop';
DELETE FROM etl.recurso WHERE id = 'teste_pop';

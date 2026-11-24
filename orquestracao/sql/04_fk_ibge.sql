-- Chaves estrangeiras do schema ibge (PostgreSQL 17+). Requer 01, 02 e 03.
--   1. codigo_ibge de populacao, pib_municipal e malha -> ibge.municipio (a tabela-mestre passa a ser garantida pelo banco)
--   2. _execucao_id de municipio, populacao, pib_municipal e malha -> etl.execucao (a procedência deixa de ser convenção)
--
-- Efeitos que precisam estar no desenho do ETL:
--   * ORDEM DE CARGA: ibge.municipio carrega ANTES das tabelas filhas (o orquestrador já foi reordenado).
--   * Município não pode mais ser excluído pelo ETL enquanto houver filhas (RESTRICT): a carga aborta e faz rollback.
--     É o comportamento desejado: um município que some da fonte exige decisão humana.
--   * etl.execucao não pode ser apagada se alguma linha ainda aponta para ela.
-- Sem índice em _execucao_id: as tabelas têm milhares de linhas; criar se algum dia a limpeza de etl.execucao ficar lenta.
-- Idempotente: pode rodar de novo. Se houver linhas órfãs, ADD CONSTRAINT falha com a chave violada.

DO $$
DECLARE
    f record;
BEGIN
    FOR f IN
        SELECT * FROM (VALUES
            ('ibge.populacao',      'populacao_municipio_fk',      'codigo_ibge',  'ibge.municipio (codigo_ibge)'),
            ('ibge.pib_municipal',  'pib_municipal_municipio_fk',  'codigo_ibge',  'ibge.municipio (codigo_ibge)'),
            ('ibge.malha',          'malha_municipio_fk',          'codigo_ibge',  'ibge.municipio (codigo_ibge)'),
            ('ibge.municipio',      'municipio_execucao_fk',       '_execucao_id', 'etl.execucao (id)'),
            ('ibge.populacao',      'populacao_execucao_fk',       '_execucao_id', 'etl.execucao (id)'),
            ('ibge.pib_municipal',  'pib_municipal_execucao_fk',   '_execucao_id', 'etl.execucao (id)'),
            ('ibge.malha',          'malha_execucao_fk',           '_execucao_id', 'etl.execucao (id)')
        ) AS t(tabela, nome, coluna, alvo)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = f.nome AND conrelid = f.tabela::regclass) THEN
            EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %s', f.tabela, f.nome, f.coluna, f.alvo);
        END IF;
    END LOOP;
END $$;

-- Fora de alcance de FK (continuam relações lógicas, documentadas em MER_IBGE_INEP.md):
--   etl.recurso.tabela_destino, etl.recurso.parametros->>'fonte_tabela' (jsonb), ibge.pib_municipal.edicao -> meta.layout_ftp
--   (layout_ftp não tem chave única só em edicao), etl.exclusao/etl.historico (tabela + chave genéricas).

-- APLs (Arranjos Produtivos Locais) do Observatório Brasileiro de APL (MDIC). PostgreSQL 17+. Requer 01 a 05.
-- Fonte: planilha "Lista APLs" baixada à mão em gov.br/empresas-e-negocios/.../observatorioapl/apls-brasileiros
-- (o gov.br responde com captcha a cliente automatizado: não há download sem intervenção humana).
--
--   apl.apl            um APL da BA por linha. PK id_apl (gerado aqui: a planilha não tem código estável, "No." é número de linha);
--                      o MERGE casa por (uf, nome_apl), que é UNIQUE. APL renomeado na fonte = exclusão + inclusão (id novo).
--   apl.apl_municipio  N:N, como no Supabase: PK (id_apl, codigo_ibge), FK para apl.apl e para ibge.municipio.
--                      Nome da planilha -> codigo_ibge: exato normalizado > meta/apl_municipio_de_para.csv > aproximado (difflib).
--                      metodo_cruzamento diz qual nível casou; nome sem correspondência aborta a carga.
-- Dados pessoais da planilha (nome, e-mail e telefone do gestor, endereço, CEP, "Fonte da Informação") NÃO entram no banco.

CREATE SCHEMA IF NOT EXISTS apl;

CREATE TABLE IF NOT EXISTS apl.apl (
    id_apl                       int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uf                           text NOT NULL,
    nome_apl                     text NOT NULL,
    setor_produtivo              text,
    cnaes                        text,          -- como na fonte: lista separada por "; "
    cnpj                         text,
    site                         text,
    qt_empresas                  int,
    qt_funcionarios              int,
    produtos_servicos            text,
    especializacao               text,
    indicacao_geografica         text,
    plano_desenvolvimento        boolean,
    codigo_ibge_polo             int,           -- SEM FK: APL interestadual mantém a sede original (Vinhos: Petrolina/PE)
    uf_fonte                     text,          -- "Estado*" como na planilha; 'PE; BA' = interestadual (só os municípios baianos entram)
    instituicoes_ensino          text,
    instituicoes_capacitacao     text,
    instituicoes_financiamento   text,
    instituicoes_promocao        text,
    projetos                     text,
    redes_setoriais              text,
    instituicoes_validacao       text,
    data_atualizacao_fonte       date,          -- "Data última atualização" da planilha (por APL)
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint REFERENCES etl.execucao(id),
    UNIQUE (uf, nome_apl)
);
COMMENT ON TABLE apl.apl IS 'APLs da lista oficial do Observatório Brasileiro de APL (MDIC) com a BA entre os estados (inclui interestaduais). uf = recorte (sempre BA). Sem dados pessoais do gestor.';
COMMENT ON COLUMN apl.apl.qt_funcionarios IS 'Número de funcionários (ou produtores) informado pelo APL; texto não numérico na fonte vira NULL';

CREATE TABLE IF NOT EXISTS apl.apl_municipio (
    id_apl       int  NOT NULL REFERENCES apl.apl(id_apl) ON DELETE CASCADE,
    codigo_ibge  int  NOT NULL REFERENCES ibge.municipio(codigo_ibge),
    nome_municipio_fonte text,   -- como estava escrito na planilha (rastreia o cruzamento)
    metodo_cruzamento    text CHECK (metodo_cruzamento IN ('exato', 'de_para', 'aproximado')),
    _hash text NOT NULL, _criado_em timestamptz NOT NULL DEFAULT now(), _modificado_em timestamptz NOT NULL DEFAULT now(),
    _modificado_fonte_em date, _execucao_id bigint REFERENCES etl.execucao(id),
    PRIMARY KEY (id_apl, codigo_ibge)
);
COMMENT ON TABLE apl.apl_municipio IS 'Municípios que compõem cada APL (N:N). Um município pode estar em vários APLs.';

CREATE UNLOGGED TABLE IF NOT EXISTS stg.apl (LIKE apl.apl);
ALTER TABLE stg.apl DROP COLUMN IF EXISTS id_apl, DROP COLUMN IF EXISTS _hash, DROP COLUMN IF EXISTS _criado_em, DROP COLUMN IF EXISTS _modificado_em,
    DROP COLUMN IF EXISTS _modificado_fonte_em, DROP COLUMN IF EXISTS _execucao_id, ADD COLUMN IF NOT EXISTS modificado_fonte_em date;
CREATE UNLOGGED TABLE IF NOT EXISTS stg.apl_municipio (nome_apl text, id_apl int, codigo_ibge int, nome_municipio_fonte text,
    metodo_cruzamento text, modificado_fonte_em date);

SELECT audit.ativar('apl.apl',           '{id_apl}');
SELECT audit.ativar('apl.apl_municipio', '{id_apl,codigo_ibge}');

GRANT USAGE ON SCHEMA apl TO api_crud;
GRANT SELECT ON apl.apl, apl.apl_municipio TO api_crud;

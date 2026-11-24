# MER atual: IBGE × INEP

Retrato em 2026-11-24, depois de `04_fk_ibge.sql` e `05_auditoria.sql`. **IBGE = implementado** (`orquestracao/sql/01` a `05`). **INEP = implementado** em `06_inep_modelo.sql` (desenho híbrido: dimensões que nunca se apagam, fato por ano, "ativo" derivado em view; `PLANEJAMENTO_IBGE.md` §7D). Censos 2021 a 2024 carregados.

**Legenda dos diagramas**
- Prefixo do nome: `ibge_`, `etl_`, `meta_`, `audit_` e `inep_` estão implementados. No banco, o primeiro `_` vira ponto: `ibge_municipio` = `ibge.municipio`.
- Linha cheia (`--`) = FK declarada no SQL. Linha tracejada (`..`) = relação lógica sem FK ou relação proposta. A tabela da §3 diz qual é qual.
- Colunas de controle (`_hash`, `_criado_em`, `_modificado_em`, `_modificado_fonte_em`, `_execucao_id`): ficam fora do diagrama 1 e aparecem no diagrama 2.

## 1. Domínio: município, IBGE e INEP

```mermaid
erDiagram
    %% ===== IBGE (implementado, 02/03_*.sql) =====
    ibge_municipio {
        int codigo_ibge PK "7 digitos, 417 da BA"
        text municipio
        text uf
        int codigo_regiao_imediata
        int codigo_regiao_intermediaria
        text hierarquia_urbana
        boolean semiarido
        numeric area_km2
        numeric centroide_lat
        numeric centroide_lon
    }
    ibge_populacao {
        int codigo_ibge PK, FK
        int ano PK
        text tipo PK "estimativa | censo"
        bigint populacao
        text fonte
    }
    ibge_pib_municipal {
        int codigo_ibge PK, FK
        int ano PK
        numeric pib_mil_reais
        numeric pib_per_capita_reais
        numeric vab_total_mil_reais
        text atividade_1
        boolean provisorio
        text edicao
    }
    ibge_malha {
        int codigo_ibge PK, FK "1-1"
        text qualidade
        jsonb geometria
    }

    inep_ies {
        int co_ies PK
        text no_ies
        text sg_ies
        int co_mantenedora
        smallint tp_categoria_administrativa
        smallint tp_organizacao_academica
        int co_municipio_sede "sem FK: pode ser fora da BA"
        text uf_sede
    }
    inep_ies_local {
        int co_ies PK, FK "campus = par"
        int co_municipio PK, FK
    }
    inep_curso {
        int co_curso PK "dimensao, nunca apagada"
        int co_ies FK "FK composta -> ies_local"
        int co_municipio FK "FK composta -> ies_local"
        text no_curso
        smallint tp_grau_academico
        smallint tp_rede
        boolean oculto_curadoria "fora do _hash"
        text motivo_oculto
    }
    inep_curso_censo {
        int co_curso PK, FK
        int ano PK "fato por ano"
        text co_cine_rotulo FK "rotulo do ano"
        int qt_vg_total
        int qt_ing
        int qt_mat
        int qt_conc
    }
    inep_cine_classificacao {
        text co_cine_rotulo PK "ex.: 0916F01"
        text no_cine_rotulo
        text co_cine_area_detalhada
        text co_cine_area_especifica
        text co_cine_area_geral "2 digitos, ex.: 05"
        text no_cine_area_geral
    }
    inep_regra_cti {
        text co_cine_rotulo PK, FK
        text status "incluir | excluir | revisar"
        text observacao
    }

    ibge_municipio ||--o{ ibge_populacao : "codigo_ibge"
    ibge_municipio ||--o{ ibge_pib_municipal : "codigo_ibge"
    ibge_municipio ||--o| ibge_malha : "codigo_ibge"
    inep_ies ||--|{ inep_ies_local : "tem campus"
    ibge_municipio ||--o{ inep_ies_local : "sedia campus"
    inep_ies_local ||--o{ inep_curso : "oferece (co_ies, co_municipio)"
    inep_curso ||--|{ inep_curso_censo : "uma linha por censo"
    inep_cine_classificacao ||--o{ inep_curso_censo : "classifica no ano"
    inep_cine_classificacao ||--o| inep_regra_cti : "regra CT&I"
    ibge_municipio |o..o{ inep_ies : "sede (so se BA; sem FK)"
```

**Cardinalidades do campus e do curso**
- O campus é o par (`co_ies`, `co_municipio`); o INEP não tem código de campus, então dois campi da mesma IES no mesmo município viram um só.
- `curso` (dimensão) aponta para o campus por FK composta e tem uma linha em `curso_censo` por censo em que existiu. O curso que saiu do censo não é marcado: apenas não tem linha no ano vigente (`inep.v_curso_atual`).
- `co_ies` e `co_municipio` de `curso` refletem o último censo (33 cursos mudaram de IES entre 2022 e 2023). O rótulo CINE fica em `curso_censo`, porque muda por ano.
- `ies` → município da sede é opcional e **sem FK**: a sede pode ficar fora da BA (UNIVASF em PE, UNILAB no CE).
- Contagens em 2024: 144 IES, 216 campi; com a UNIVASF permanecendo (`exigir_sede_ba = false`), a view tem 552 cursos e 133 campi.

## 2. Controle e rastreabilidade

```mermaid
erDiagram
    etl_recurso {
        text id PK
        text fonte
        text modo "ETL_API | ELT_ARQUIVO"
        text metodo
        text url
        jsonb parametros "fonte_tabela, produto_id..."
        text tabela_destino "texto, sem FK"
        text frequencia
        boolean ativo
    }
    etl_checkpoint {
        text recurso_id PK, FK
        jsonb digital
        timestamptz verificado_em
        timestamptz alterado_em
    }
    etl_execucao {
        bigint id PK
        text recurso_id FK
        timestamptz inicio
        timestamptz fim
        text status
        jsonb escopo
        jsonb digital_novo
        int inseridos
        int atualizados
        int excluidos
        text disparo "agendado | manual | forcado"
        text usuario
        text host
    }
    etl_exclusao {
        bigint id PK
        bigint execucao_id FK
        text tabela
        jsonb chave
        jsonb linha
    }
    etl_historico {
        bigint id PK
        bigint execucao_id FK
        text tabela
        jsonb chave
        jsonb linha_anterior
    }
    meta_fonte_tabela {
        text id PK
        text fonte
        text url
        jsonb metadados
    }
    meta_variavel {
        text fonte_tabela_id PK, FK
        int variavel_id PK
        text nome
        text unidade
    }
    meta_periodo {
        text fonte_tabela_id PK, FK
        text periodo PK
        date modificacao
    }
    meta_calendario {
        int id PK
        int produto_id
        timestamp data_divulgacao
    }
    meta_layout_ftp {
        text edicao PK
        int posicao PK
        text campo
        text coluna_destino
    }
    ibge_pib_municipal {
        int codigo_ibge PK
        int ano PK
        text edicao
        text _hash
        timestamptz _criado_em
        timestamptz _modificado_em
        date _modificado_fonte_em
        bigint _execucao_id FK
        text _criado_origem "etl | api | direto_sql"
        text _origem
        text _modificado_por
    }
    inep_curso {
        int co_curso PK
        text _hash
        timestamptz _criado_em
        timestamptz _modificado_em
        date _modificado_fonte_em
        bigint _execucao_id FK
    }
    audit_evento {
        bigint id PK
        text tabela "ex.: ibge.pib_municipal"
        char operacao "I | U | D"
        jsonb chave
        jsonb antes
        jsonb depois
        text campos_alterados "text[]"
        text origem "etl | api | direto_sql"
        text usuario
        text request_id
        bigint execucao_id "sem FK, de proposito"
    }

    etl_recurso ||--o| etl_checkpoint : "ultima digital"
    etl_recurso ||--o{ etl_execucao : "cargas"
    etl_execucao ||--o{ etl_exclusao : "linhas excluidas"
    etl_execucao ||--o{ etl_historico : "versoes anteriores"
    meta_fonte_tabela ||--o{ meta_variavel : "variaveis"
    meta_fonte_tabela ||--o{ meta_periodo : "modificacao por periodo"
    meta_fonte_tabela |o..o{ etl_recurso : "parametros->>fonte_tabela"
    meta_calendario }o..o{ etl_recurso : "produto_id = parametros->>produto_id"
    meta_layout_ftp }o..o{ ibge_pib_municipal : "edicao"
    etl_execucao |o--o{ ibge_pib_municipal : "_execucao_id"
    ibge_pib_municipal ||..o{ audit_evento : "tabela + chave (trigger)"
    etl_execucao |o..o{ audit_evento : "execucao_id (logico)"
    etl_execucao |o--o{ inep_curso : "_execucao_id"
```

**Relação genérica:** toda tabela de dados tem `_execucao_id` → `etl.execucao.id` (0..1—N, FK declarada nas tabelas `ibge.*`). O diagrama mostra dois exemplos. No IBGE isso vale para `municipio`, `populacao`, `pib_municipal` e `malha`. No INEP vale, em proposta (§0), para `ies`, `ies_local`, `curso`, `cine_classificacao` e `regra_cti`. As staging (`stg.ibge_*`, `stg.inep_ies`, `stg.inep_cursos`, `stg.inep_abi`) não têm colunas de controle nem FK: são truncadas a cada carga. Em `etl.exclusao` e `etl.historico`, o alvo é identificado por `tabela` (text) + `chave` (jsonb), sem FK.

## 3. Situação de cada relacionamento

(a) = FK declarada no SQL · (b) = relação lógica sem FK · (c) = proposta ainda sem DDL (hoje nenhuma)

| Relacionamento | Card. | Tipo | Onde |
|---|---|---|---|
| `etl.checkpoint.recurso_id` → `etl.recurso.id` | 1—0..1 | (a) | `01_controle.sql` l.23 |
| `etl.execucao.recurso_id` → `etl.recurso.id` | 1—N | (a) | `01_controle.sql` l.31 |
| `etl.exclusao.execucao_id` → `etl.execucao.id` | 1—N | (a), coluna anulável | `01_controle.sql` l.45 |
| `etl.historico.execucao_id` → `etl.execucao.id` | 1—N | (a), coluna anulável | `01_controle.sql` l.55 |
| `meta.variavel` / `meta.periodo` → `meta.fonte_tabela` | 1—N | (a) | `03_ibge_modelo.sql` l.201, 208 |
| `ibge.populacao.codigo_ibge` → `ibge.municipio` | 1—N | (a) | `04_fk_ibge.sql` |
| `ibge.pib_municipal.codigo_ibge` → `ibge.municipio` | 1—N | (a) | `04_fk_ibge.sql` |
| `ibge.malha.codigo_ibge` → `ibge.municipio` | 1—0..1 | (a) | `04_fk_ibge.sql` |
| `_execucao_id` (tabelas `ibge.*`) → `etl.execucao` | 0..1—N | (a) | `04_fk_ibge.sql`; anulável: linha da API não tem carga |
| `audit.evento.tabela` + `chave` → qualquer tabela de dados | N—1 | (b) | genérica (jsonb); `execucao_id` sem FK de propósito |
| `etl.recurso.tabela_destino` → tabela final | — | (b) | text |
| `etl.recurso.parametros->>'fonte_tabela'` → `meta.fonte_tabela` | 0..1—N | (b) | jsonb, usada em `meta.v_status_dataset` |
| `etl.recurso.parametros->>'produto_id'` → `meta.calendario.produto_id` | N—N | (b) | jsonb, usada em `meta.v_status_dataset` |
| `ibge.pib_municipal.edicao` → `meta.layout_ftp.edicao` | N—N | (b) | sem chave única só em `edicao` |
| `etl.exclusao` / `etl.historico` (`tabela` + `chave`) → qualquer tabela | — | (b) | genérica, jsonb |
| `inep.ies_local.co_ies` → `inep.ies` | N—1 | (a) | `06_inep_modelo.sql` |
| `inep.ies_local.co_municipio` → `ibge.municipio` | N—1 | (a) | `06_inep_modelo.sql` |
| `inep.curso` (`co_ies`, `co_municipio`) → `inep.ies_local` | N—1 | (a) | FK composta |
| `inep.curso_censo.co_curso` → `inep.curso` | N—1 | (a) | `06_inep_modelo.sql` |
| `inep.curso_censo.co_cine_rotulo` → `inep.cine_classificacao` | N—1 | (a) | `06_inep_modelo.sql` |
| `inep.regra_cti.co_cine_rotulo` → `inep.cine_classificacao` | 0..1—1 | (a) | `06_inep_modelo.sql` |
| `_execucao_id` (tabelas `inep.*`) → `etl.execucao` | 0..1—N | (a) | `06_inep_modelo.sql` |
| `inep.ies.co_municipio_sede` → `ibge.municipio` | N—0..1 | (b), **sem FK de propósito** | a sede pode ser fora da BA |
| `inep.curso_censo.ano` → `etl.execucao.escopo->>'ano'` | N—N | (b) | usado por `inep.ano_vigente()` |

## 4. Inconsistências e lacunas

1. ~~Nenhuma FK no schema `ibge` e `_execucao_id` sem FK~~: **resolvido em 24/11** (`04_fk_ibge.sql`, `06_inep_modelo.sql`). O município carrega antes das filhas, e o ETL não exclui município que tenha filhas.
2. ~~Soft delete × exclusão por escopo~~: **resolvido em 24/11**. O INEP não tem `ativo`; dimensões sem DELETE (`p_excluir => false`) e fato por ano com trava de 20%.
3. **Edição pela API × recarga do ETL.** A fonte vence nos valores; a curadoria (`oculto_curadoria`) é preservada. Decisão a confirmar (`PLANEJAMENTO_IBGE.md` §7C).
4. **A sede da IES pode ficar fora da BA**, então não há FK para `ibge.municipio`.
5. **`CO_MUNICIPIO` do INEP** pode chegar como float (`2919207.0`); o orquestrador converte para inteiro. Códigos CINE são texto (rótulo tem letra, área tem zero à esquerda).
6. **Ligação com o Supabase não existe.** O `id_ativo` do painel (campus) e o `id_municipio` serial ainda não têm tabela de correspondência com `co_ies` e `codigo_ibge`; a tabela `ies_alias` do plano não foi criada.
7. **Campus sem código próprio.** O `id_ativo` do painel não tem correspondência 1:1 garantida (dois campi no mesmo município viram um). O município do INEP manda (decisão de 24/11): os 5 cursos do UNIMAM ficam em Cruz das Almas, mesmo que o painel use outro.
8. **Um recurso por censo** (`inep_censo_superior_<ano>`): `meta.v_status_dataset` mostra uma linha por ano carregado.

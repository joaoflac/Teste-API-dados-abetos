# Orquestração ETL/ELT — Painel Territorial CT&I

Planejamento das cargas que vão alimentar o painel (repo `territorios_secti`, branch `redesign`).
Destino: VPS Ubuntu com **PostgreSQL 17** e **Apache Hop** em contêineres (`docker-compose.yml`).
Testes feitos em 19/11/2026 a partir desta máquina.

## 1. Princípio: verificar antes de baixar

Toda rodada começa pelo **Passo 0** (`scripts/etl_verificar_mudanca.py`). Ele não baixa dados: consulta só o identificador de mudança mais barato de cada fonte e compara com o último checkpoint. Só o que mudou segue adiante, e com **escopo**: quais períodos, quais municípios, quais arquivos dentro do ZIP.

```
cron/systemd ─► Hop workflow "principal"
                 ├─ Passo 0  verificar mudança ──► nada mudou? encerra (custo: segundos, poucos KB)
                 ├─ Passo 1  baixar só o escopo alterado
                 │            ETL_API      : JSON da API ──────────► stg.<tabela>
                 │            ELT_ARQUIVO  : CSV/ZIP ─► /files ─► COPY ─► stg.<tabela>
                 ├─ Passo 2  MERGE stg → tabela final (insere / atualiza / exclui só o necessário)
                 └─ Passo 3  etl.finalizar(): grava o novo checkpoint apenas se a carga deu 'ok'
```

Como o checkpoint só avança depois da carga, uma falha no meio faz a próxima rodada tentar de novo, sem perder a mudança.

## 2. Resultado dos testes de identificadores (`scripts/probe_identificadores_mudanca.py`)

| Fonte | Recurso | ETag | Last-Modified | 304 condicional | Outro identificador | Método escolhido |
|---|---|---|---|---|---|---|
| IBGE | API agregados (6579, 5938, 4709) | ✗ | ✗ | ✗ | **`/agregados/{id}/periodos` → `modificacao` por período** | `ibge_per` |
| IBGE | Localidades, malhas | ✗ | ✗ | ✗ | Corpo estável entre chamadas | `hash_corpo` (SHA-256) |
| IBGE | FTP PIB dos Municípios (ZIP) | ✓ | ✓ | ✓ | Edição nova = pasta nova (`2023_2024/`) | `http` + `novo_ano` |
| INEP | Microdados Censo Ed. Superior (ZIP 457 MB) | ✓ | ✓ | ✓ (via curl) | Ano novo = URL nova | `http` + `novo_ano` |
| ANATEL | Banda larga fixa (ZIP 1 GB) | ✓ | ✓ | ✓ | **CRC32 de cada arquivo interno, por HTTP Range (0,6 s)** | `zip_crc` |
| ANEEL | DEC/FEC (ZIP) | ✓ | ✓ | ✓ | CKAN `hash` + `last_modified` | `ckan` |
| ANEEL | Datastore INDGER, SIGA, P&D | ✗ | ✗ | ✗ | **CKAN `resource_show` → `hash` (MD5), `last_modified`** | `ckan` |
| BNDES | Datastore operações | ✗ | ✗ | ✗ | **CKAN `resource_show` → `hash`, `last_modified`, `size`** | `ckan` |
| SICONFI | DCA, RREO (ORDS) | ✓ (forte, hash do conteúdo) | ✗ | ✓ | **`extrato_entregas` → `data_status` por ente/entregável/período** | `siconfi` |
| ANATEL | Cobertura móvel 4G (dados.gov.br) | — | — | — | Não testado (portal exige chave de API) | pendente |

Arquivos gerados: `probe_identificadores_mudanca.csv` (cabeçalhos) e `probe_identificadores_mudanca_metadados.json` (respostas cruas de CKAN, IBGE e SICONFI).

### Observações por fonte

- **IBGE / SIDRA:** a API não manda validadores HTTP, mas `periodos` traz a data de modificação de cada ano. Exemplos: 6579 → 2025 e 2026 modificados em 28/08/2026; 5938 → 2021 a 2023 em 19/12/2025. Basta rebaixar os períodos cuja data mudou.
- **SICONFI:** o extrato de entregas dá a data de envio de cada DCA e RREO por município. Na VPS são 417 chamadas leves, e cada uma também aceita `If-None-Match`. Só se rebaixam os demonstrativos dos municípios que reenviaram.
- **ANATEL:** o ZIP de 1 GB guarda 27 CSVs (cerca de 12 GB descompactados). O diretório central do ZIP traz o CRC32 de cada um. Se só `Densidade_Banda_Larga_Fixa.csv` (71 MB) mudar, só ele é extraído por Range com `scripts/httpzip.py`.
- **CKAN (BNDES/ANEEL):** o `_id` do datastore é recriado sempre que o CSV é republicado, então **não serve como chave**. Use chave natural ou hash da linha (seção 3).
- **INEP:** o certificado tem cadeia incompleta e o Python às vezes tem a conexão derrubada. O verificador recorre ao `curl`. Na VPS, testar com o pacote `ca-certificates` do Ubuntu.
- **ANEEL:** o servidor derruba o TLS quando há SNI; o acesso é pelo IP `200.198.220.169` com cabeçalho `Host`. É preciso testar de novo a partir da VPS, porque pode ser um bloqueio de rede específico.

### Teste do verificador (3 rodadas)

1. **1ª rodada:** todos os recursos `NOVO` (carga inicial).
2. **2ª rodada:** todos `igual`. Nada a baixar.
3. **3ª rodada, com alterações simuladas:** só os recursos alterados apareceram, com escopo exato:
   - `ibge_6579_populacao` → `2025`
   - `siconfi_entregas_2025` → `2910800|Balanço Anual (DCA)|1` e `REMOVIDO:9999999|…`
   - `bndes_nao_automaticas` → `recurso inteiro`
   - `anatel_bl_fixa_zip` → `Densidade_Banda_Larga_Fixa.csv`

## 3. Carga incremental e exclusão pontual (`sql/`)

Arquivos: `sql/01_controle.sql` (controle), `sql/02_carga_incremental.sql` (padrão de carga) e `testes/03_teste_incremental.sql` (teste).

Cada tabela final tem colunas de controle: `_hash` (MD5 do conteúdo), `_carregado_em`, `_atualizado_em` e `_execucao_id`. A carga usa `MERGE` do PostgreSQL 17:

| Situação | Ação |
|---|---|
| Chave nova | `INSERT` |
| Chave existe e `_hash` mudou | `UPDATE` só dessa linha |
| Chave existe e `_hash` igual | nada (não reescreve) |
| Linha no banco, **dentro do escopo baixado**, ausente na fonte | `DELETE` só dela, registrado em `etl.exclusao` (chave e conteúdo) |
| Linha **fora do escopo** baixado | intocada. Baixar só 2025 nunca apaga 2024 |

A cláusula `WHEN NOT MATCHED BY SOURCE AND <escopo>` é o que garante a exclusão pontual. O escopo é o mesmo que o verificador calculou.

### Chave por fonte

| Fonte | Chave da linha | Escopo de exclusão |
|---|---|---|
| IBGE agregados | `codigo_ibge, variavel, ano` | anos alterados |
| IBGE localidades/malhas | `codigo_ibge` | recurso inteiro |
| SICONFI | `cod_ibge, exercicio, periodo, anexo, conta, coluna` | entes/períodos reenviados |
| INEP | `CO_IES` / `CO_CURSO, CO_MUNICIPIO` | ano do censo |
| ANATEL | `ano, mes, codigo_ibge, empresa, tecnologia, velocidade…` | arquivo interno alterado (ano) |
| ANEEL | SIGA `CodCEG`; P&D `DscCodProjeto`; INDGER `NumCNPJ, CodMunicipioIBGE, DatReferenciaInformada` | recurso (UF=BA) |
| BNDES | **sem chave natural** (`numero_do_contrato` se repete: 30 linhas → 16 contratos): `_hash + _ocorrencia` | UF=BA |

Quando não há chave natural, a identidade da linha é o próprio hash. Uma linha alterada vira exclusão da versão antiga e inserção da nova, e o restante não é tocado.

## 4. ETL × ELT

| Modo | Fontes | Como o Hop faz |
|---|---|---|
| **ETL_API** | IBGE, SICONFI, BNDES/ANEEL datastore | `REST Client` / `HTTP` → `JSON Input` → `Table Output` em `stg` → `SQL` chamando `etl.carga_*()` |
| **ELT_ARQUIVO** | INEP, ANATEL, ANEEL DEC/FEC, IBGE FTP | `HTTP` (ou script com Range) → `/files` → `PostgreSQL Bulk Loader` (COPY) bruto em `stg` → transformação em SQL dentro do banco → `etl.carga_*()` |

Arquivos baixados ficam no volume `downloads`, nomeados pelo ETag/CRC, e podem ser apagados depois do `COPY`.

## 5. Estrutura proposta no Hop (`orquestracao/hop/`, a criar)

```
hop/
  workflows/principal.hwf          Passo 0 → loop por recurso alterado → Passo 3
  workflows/recurso_<fonte>.hwf    um por fonte
  pipelines/stg_<recurso>.hpl      extração para staging
  metadata/                        conexão Postgres via variáveis (PG_HOST, PG_PASSWORD)
```

O Passo 0 pode ficar em Python (executado pelo Hop com a action *Shell*) ou ser reescrito com transforms `HTTP Client` e `JSON Input`. Começar com o Python, que já está testado.

## 6. Pendências

1. ~~**Teste do MERGE no Postgres**~~: feito em 19/11 com Postgres 17.6 portátil (`pg-portatil/pg.ps1`) e `orquestrador_simulado.py`. Para testar o Hop real em Docker:
   ```
   docker compose -f orquestracao/docker-compose.yml up -d postgres
   docker compose -f orquestracao/docker-compose.yml exec -T postgres psql -U etl -d painel -f /testes/03_teste_incremental.sql
   ```
2. **ANATEL 4G (dados.gov.br):** obter a chave de API do portal e testar os identificadores.
3. **SICONFI completo:** gerar o verificador para os 417 entes, com paralelismo moderado e respeitando o limite da API.
4. **Na VPS:** testar de novo ANEEL (SNI) e INEP (certificado) a partir da rede da VPS.
5. **Contrato com o painel:** definir quais tabelas e views do schema final o `territorios_secti` (branch `redesign`) vai consumir.

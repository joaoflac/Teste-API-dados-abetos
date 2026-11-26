# Pendências e perguntas em aberto

Atualizado em 24/11/2026. Lista o que ainda precisa de **decisão** (de quem e com qual recomendação), o que precisa ser **perguntado** a terceiros e o que é **trabalho técnico** pendente. Quando um item for resolvido, marcar `[x]` e registrar a decisão no documento indicado entre parênteses (e no registro de decisões de `PLANEJAMENTO_IBGE.md` §8).

Legenda de quem decide: **SECTI** (política de CT&I), **Dono** (dono do projeto), **Técnico** (pode ser feito sem decisão de política, depois de aprovado).

---

## A. Decisões de política de CT&I (INEP) — SECTI

Base: parecer do Opus de 24/11 (`PLANEJAMENTO_IBGE.md` §7D, `automacao-hop-postgres/PLANO.md` §9b). A regra fica em `inep.regra_cti` e mudar um status vale na hora, sem recarregar.

- [ ] **A1. Conceito de CT&I: estreito ou amplo?** Estreito = áreas CINE 05, 06 e 07 (a definição STEM da Eurostat). Amplo = inclui 08 (agricultura e veterinária) e 09 (saúde). **Hoje: amplo**, porque o painel tem 5 tipos de curso (05 a 09). Toda a regra abaixo depende desta resposta.
- [ ] **A2. Os 6 rótulos em `revisar`** (hoje fora do painel; 10 cursos e 765 matrículas em 2024):

  | Rótulo | Cursos / matrículas | Recomendação do Opus | Confiança |
  |---|---|---|---|
  | 0532G02 Geologia | 3 / 303 | incluir | alta |
  | 0521E01 Ecologia | 1 / 9 | incluir | alta |
  | 0811E01 Engenharia agrícola | 2 / 73 | incluir | alta |
  | 0731E03 Eng. de agrimensura e cartográfica | 1 / 98 | incluir | média-alta |
  | 0914O02 Optometria | 2 / 139 | excluir | média |
  | 0918S01 Saúde coletiva | 1 / 143 | **política: sem recomendação firme** | baixa |

  Efeito de incluir os 4 primeiros: +7 cursos e +483 matrículas (Ciências naturais +4/+312, Engenharia +1/+98, Agricultura +2/+73).
- [ ] **A3. Radiologia (0914R01)**: está `incluir` (11 cursos, 413 matrículas, quase todos tecnológicos e privados), mas é operação de equipamento em atendimento. Recomendação: excluir, para ficar coerente com Optometria e Enfermagem.
- [ ] **A4. Medicina veterinária entra (29 cursos, 6.755 matrículas) e Medicina não (40 cursos, 20.315).** Pelo critério de prática clínica as duas ficam do mesmo lado. É uma incoerência de política, não técnica.
- [ ] **A5. Arquitetura (23 cursos, 4.130 matrículas) está fora.** A definição STEM da Eurostat inclui a área 07 inteira, então a exclusão é escolha da SECTI.
- [ ] **A6. Itens de confiança média**, a confirmar: Biomedicina (41 cursos; mercado dominante é análise clínica), Interdisciplinares em saúde (5 cursos, todos públicos), Gestão ambiental e Gestão de TI (viés de gestão, efeito pequeno).
- [ ] **A7. Licenciaturas em ciências** (área 01: Biologia, Matemática, Química, Física, Computação; 78 cursos e 6.667 matrículas). Recomendação: **fora dos 5 tipos**; se quiserem, uma 6ª categoria "Formação de professores em ciências" com lista explícita de rótulos.
- [ ] **A8. EAD fora do painel** (só presencial). Nos rótulos incluídos, o EAD soma 43.006 matrículas em polos da BA. Confirmar que a decisão vale.
- [ ] **A9. Rótulo novo em censo futuro.** Proposta do Opus: herda a regra do rótulo antigo quando os mesmos `co_curso` vinham dele; sem herança, 05, 06 e 08 sugerem `incluir`, 07 sugere `incluir` (exceto 0731*, que vai para `revisar`) e 09 sugere `revisar`. A sugestão é só proposta e aparece no funil até alguém confirmar.

Decididos (não reabrir sem motivo): a **UNIVASF permanece** (`exigir_sede_ba = false`); o **dataset cru do INEP manda** em município, IES e curso (os 5 cursos do UNIMAM ficam em Cruz das Almas); o Supabase antigo é só referência.

## B. Perguntas a fazer à SECTI e ao consultor

- [ ] **B1.** Existe documento da regra original que montou a lista do Supabase? Hoje ela foi **reconstituída por inferência** (`PLANO.md` §9b). Perguntar em especial: filtraram pela sede da IES na BA? Optometria, Saúde coletiva e Agrimensura ficaram de fora de propósito ou por omissão? A UNIVASF foi excluída de propósito?
- [ ] **B2.** Qual município vale para os 5 cursos do UNIMAM (Governador Mangabeira no painel, Cruz das Almas no INEP)? A decisão atual é o INEP; confirmar com a SECTI.
- [ ] **B3.** O painel exibe **matrículas**? Se sim, a queda da UNIVASF em 2024 (de cerca de 1.600 para 121 matrículas, com ingressantes normais) parece erro do INEP e precisa de nota ou de conferência no censo 2025.
- [ ] **B4.** Quem na SECTI vai editar `regra_cti` e ocultar cursos (`oculto_curadoria`) pela API? Qual o fluxo de aprovação?
- [ ] **B5.** Qual é o **calendário de atualização** que o painel precisa (o INEP publica uma vez por ano; IBGE, SICONFI, ANATEL e ANEEL têm periodicidades próprias)? Isso define a frequência do verificador.
- [ ] **B6.** Há outras fontes com regra de CT&I a definir (BNDES, ANEEL P&D, SICONFI)? Os filtros em `categorias_cti/` e `RESULTADOS_AMOSTRAGEM.md` têm o mesmo problema de origem não documentada?

## C. Decisões técnicas e de produto — Dono

- [x] **C1. Decidido em 26/11: a pessoa vence, por coluna** (`PLANEJAMENTO_CRUD_CURADORIA.md` §0 e §3.5: linha duvidosa espera no CRUD; edição humana persiste nas recargas; exclusão da fonte em cascata, restaurável por 12 meses; pop-up de atualização da fonte; retenção de 12 meses, inclusive `etl.exclusao`). Texto original: Hoje: a edição pela API em dado que vem da fonte só é sobrescrita quando o ETL recarrega aquela partição (testado). A curadoria própria (`oculto_curadoria`) é preservada. Se a SECTI precisar de **correções manuais permanentes** em dado oficial, falta um campo de bloqueio (`_bloqueado_etl`) ou uma tabela de sobreposições (`PLANEJAMENTO_IBGE.md` §7C).
- [ ] **C2. Versão do Hop:** o `docker-compose.yml` fixa 2.10.0 (Java 17); o plano do INEP decidiu a estável mais recente (2.20.0, Java 21). Confirmar que a imagem existe e alinhar a tag. Nada disso foi executado: o Docker não roda nas máquinas de trabalho (falta *Virtual Machine Platform*, sem admin). Pedido à TI ainda não feito.
- [ ] **C3. VPS:** distribuição e versão do Linux (para fixar o `setup.sh`), exposição do Postgres (túnel SSH ou firewall), e o usuário de login do Hop e da API (hoje só existe o papel `api_crud` sem LOGIN; a senha e o LOGIN ficam fora do repositório).
- [ ] **C4. Contrato com o painel:** quais views o `TERRITORIOS_SECTI` (branch `redesign`) vai consumir e como migrar do Supabase. O painel hoje lê `lista_cursos_cti`, `cursos`, `tipo_cursos`, `stats_ti` etc. Propor mapeamento para `inep.v_curso_atual`, `inep.v_campus_com_curso` e as views `ibge`/`meta`.
- [ ] **C5. Ligação com o painel antigo:** criar a correspondência `id_ativo` (campus) ↔ (`co_ies`, `co_municipio`) e `id_municipio` serial ↔ `codigo_ibge` (a `ies_alias` do plano não foi criada).
- [ ] **C6. Log de auditoria:** política de retenção e partição de `audit.evento`; hoje cresce sem limite (cerca de 16 mil eventos só na carga inicial do IBGE e do INEP).
- [ ] **C7. PostGIS ou GeoJSON** para a malha (`ibge.malha`, hoje jsonb).
- [ ] **C8. Um recurso por censo** (`inep_censo_superior_<ano>`): `meta.v_status_dataset` mostra uma linha por ano carregado. Manter assim ou consolidar?

## D. Trabalho técnico pendente

Pode ser feito sem decisão de política, depois de aprovado.

- [ ] **D1. Série histórica por rótulo recodificado.** Entre 2023 e 2024 o INEP recodificou 7 rótulos (65 cursos); os códigos antigos não têm regra, então uma série 2021–2024 por tipo filtrada pela regra quebra. Carregar regras para os códigos antigos e fazer o rótulo novo herdar a regra do antigo (`orquestrador_inep.py`).
- [ ] **D2. Testar `baixar_zip`** do `orquestrador_inep.py` (nunca foi executada; usei `--zip` com arquivos já baixados).
- [ ] **D3. IBGE:** descobrir automaticamente a edição nova do FTP do PIB (`ftp.ibge.gov.br/Pib_Municipios/`; hoje `FTP_EDICAO = "2022_2023"` fixo); usar `meta.calendario` para agendar o verificador nas datas de divulgação; alertar quando o hash do `/metadados` mudar; avaliar as variáveis 5936 e 10605 do agregado 4709.
- [ ] **D4. Aposentar o verificador antigo** `scripts/etl_verificar_mudanca.py` (usa `estado_checkpoint.json`); o orquestrador usa `etl.checkpoint`.
- [ ] **D5. Validações gerais** para população, município e malha (417 municípios, código sem nulos, população não negativa, faixa de variação), como o INEP já tem.
- [ ] **D6. Alertas e notificação** de falha de carga; trava contra duas cargas simultâneas (lock consultivo).
- [ ] **D7. Testar quando sair o censo 2025:** `CO_CURSO` continua estável? A trava de 20% continua suficiente? A UNIVASF volta ao normal?
- [ ] **D11. APLs (MDIC, 26/11).** Plano em `PLANEJAMENTO_APL.md`; CRUD e fila de validação em `PLANEJAMENTO_CRUD_CURADORIA.md`. Carregam no Postgres com `orquestracao/orquestrador_apl.py --xlsx <planilha>` (56 APLs: os 54 da BA e 2 interestaduais. Os interestaduais entram com a sede original e só os municípios baianos, por decisão de 26/11: Vinhos do Vale do São Francisco, PE; BA, sede Petrolina; e Piscicultura do Sertão de Itaparica, PE; BA; AL, sede Jatobá. São 352 pares. **Confirmar se a Piscicultura também entra**, porque a decisão citou só o de Vinhos.) BrasilAPI (teste de 26/11): só 27 dos 54 têm CNPJ. Em 23 deles o CNPJ fica na cidade-polo e em 2 noutro município do APL. Em 1 o CNPJ fica fora do APL (Produção, Aquisição e Serviço: CNPJ em Feira de Santana, polo Irecê) e 1 CNPJ é inválido (Giló). A cooperativa de Pescados da BTS está INAPTA. Isso confere a sede, mas não a lista de municípios, que é onde estão os erros de digitação. (1) O gov.br responde com captcha a cliente automatizado: o download é manual, e o Hop só vigia a pasta. Perguntar ao MDIC se há link direto ou API. (2) Os nomes com erro são casados por aproximação, com `metodo_cruzamento = 'aproximado'` em `apl.apl_municipio`; o de-para fica só com Tancredo Neves e Capela. Conferido com o Supabase (só leitura, 26/11), onde o consultor decidiu os mesmos casos de forma independente: Iritinga → Biritinga e Mari → Mairi batem. "Capela" ficou de fora do Ser do Sertão no Supabase. Capela do Alto Alegre é do mesmo território (Bacia do Jacuípe), e a SECTI confirma. **Erro no Supabase:** as listas de municípios dos APLs de cacau estão trocadas. O "Litoral Sul" (sede Itabuna) aparece com Ipiaú, Jequié e Jitaúna, e o "Médio Rio de Contas" (sede Jequié) aparece com Itabuna, Uruçuca etc.; a planilha está certa. Os outros 49 APLs têm a mesma lista; os 417 nomes de `lista_municipioxterritorio` são idênticos aos do IBGE. Modelo igual ao do Supabase: `apl.apl(id_apl)` e `apl.apl_municipio(id_apl, codigo_ibge)`, mas os ids são gerados aqui, não os do Supabase. (3) A planilha é de outubro de 2022, e as datas por APL vão de 2020 a 2021. (4) Falta incluir o schema `apl` em `meta.v_linha_origem` e `meta.v_dicionario`.
- [ ] **D8. Próximas fontes**, no mesmo padrão (recurso em `etl.recurso`, dimensões e fatos, FKs para `ibge.municipio`, `audit.ativar`): BNDES, SICONFI (417 chamadas de `extrato_entregas`), ANATEL (CRC32 dentro do ZIP; falta a chave de API do 4G em dados.gov.br), ANEEL (TLS/SNI; testar da VPS).
- [ ] **D9. Graphify:** a extração semântica dos `.md` ainda não foi feita (`/graphify .` numa sessão; usa subagentes e consome tokens uma vez).
- [ ] **D10. TLS e rede na VPS:** testar de novo o INEP (cadeia de certificado) e a ANEEL (SNI) a partir da rede da VPS.

## E. O que já foi verificado e o que ainda não foi

**Verificado com dados reais (24/11):** carga completa do IBGE e dos censos INEP 2021 a 2024 em Postgres 17.6; a view do INEP reproduz os 547 cursos e 132 campi da simulação de 13/11 (552 e 133 com a UNIVASF); os 5 tipos do painel têm o mesmo nome das áreas CINE 05 a 09; as 30 colunas lidas do INEP existem nos 4 censos com os mesmos domínios de valores; a API (papel `api_crud`) não lê as tabelas-base, e a curadoria sobrevive à recarga; backup e restauração do banco incluem as permissões.

**Não verificado:** o Hop real (tudo roda no orquestrador Python); a API real do painel (o CRUD foi simulado com `api_crud` no psql); EAD; duas cargas simultâneas; o manual CINE Brasil do INEP (o servidor derrubou a conexão; os códigos e nomes dos rótulos estão confirmados pelos microdados, mas as definições de escopo das áreas detalhadas não); a lista própria de áreas STEM da OCDE (só a da Eurostat foi conferida); o censo 2025.

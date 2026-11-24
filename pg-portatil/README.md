# PostgreSQL portátil do repositório

PostgreSQL **17.6** sem instalação e sem permissão de administrador, usado para testar a orquestração do Painel Territorial CT&I.
Escuta só em `localhost:5433`. Banco `painel`, usuário `etl`.

## O que vai para o git e o que não vai

| Caminho | No git? | Por quê |
|---|---|---|
| `pg.ps1`, `README.md` | ✓ | scripts e instruções |
| `backup/painel.sql` | ✓ | **o banco inteiro em SQL texto**: é isto que garante não perder os dados |
| `pgsql/` (134 MB) | ✗ | binários oficiais da EDB, recriados com `instalar` |
| `data/` | ✗ | arquivos internos do banco, binários e mutáveis; commitá-los com o servidor ligado gera cópia corrompida |
| `pgpass.txt` | ✗ | senha local (segredo) |
| `postgres.log` | ✗ | log |

## Comandos (`powershell -File pg-portatil\pg.ps1 <acao>`)

| Ação | O que faz |
|---|---|
| `instalar` | baixa os binários (~330 MB, cerca de 1 min) e cria o cluster vazio com senha nova; não faz nada se já existir |
| `start` / `stop` / `status` | liga, desliga ou verifica o servidor. **Não sobe sozinho após reiniciar o Windows** |
| `psql` | abre o console no banco `painel` |
| `backup` | grava `backup/painel.sql` (sem as tabelas de staging). **Rodar antes de cada commit** |
| `restaurar` | apaga o banco `painel`, cria o papel `api_crud` (sem LOGIN) se faltar, e recria o banco a partir do backup, com as permissões (testado em 24/11 num cluster sem o papel) |

## Recuperar em máquina nova (ou se a pasta se perder)

```powershell
git pull
powershell -File pg-portatil\pg.ps1 instalar
powershell -File pg-portatil\pg.ps1 restaurar
```

Para recriar do zero a partir das fontes, sem o backup:

```powershell
# aplicar orquestracao/sql/01 a 06, nesta ordem (psql com PGCLIENTENCODING=UTF8, senão o 03 falha no Windows), e então:
py -3.12 orquestracao/orquestrador_simulado.py
```

O backup foi testado em 19/11/2026: restaurado num banco separado, reproduziu exatamente as contagens do original.

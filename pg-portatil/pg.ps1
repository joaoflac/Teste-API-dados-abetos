# PostgreSQL 17.6 portátil do repositório (sem instalação, sem admin). Escuta só em localhost:5433.
#
#   powershell -File pg-portatil\pg.ps1 <acao>
#     instalar   baixa os binários oficiais (EDB, ~330 MB) e cria o cluster vazio (só se não existirem)
#     start      liga o servidor              stop     desliga
#     status     verifica se está no ar       psql     abre o console no banco "painel"
#     backup     grava pg-portatil\backup\painel.sql (texto, VERSIONADO no git)
#     restaurar  recria o banco "painel" a partir do backup (apaga o atual)
#
# No git vão: este script, backup\painel.sql e README.md.
# Fora do git (.gitignore): pgsql\ (binários), data\ (arquivos internos do banco), pgpass.txt, *.log.
# Máquina nova ou arquivos perdidos:  instalar -> start -> restaurar
param([Parameter(Mandatory)][ValidateSet('instalar', 'start', 'stop', 'status', 'psql', 'backup', 'restaurar')][string]$acao)
$ErrorActionPreference = 'Stop'
$R = $PSScriptRoot
$B = Join-Path $R 'pgsql\bin'
$D = Join-Path $R 'data'
$PW = Join-Path $R 'pgpass.txt'
$LOG = Join-Path $R 'postgres.log'
$BK = Join-Path $R 'backup\painel.sql'
$URL = 'https://get.enterprisedb.com/postgresql/postgresql-17.6-1-windows-x64-binaries.zip'
$CON = @('-h', 'localhost', '-p', '5433', '-U', 'etl')

function Set-Senha { $env:PGPASSWORD = (Get-Content $PW -Raw).Trim() }
function Invoke-PgCtl([string[]]$a) {
    # Start-Process + WaitForExit: espera só o pg_ctl, não o servidor que ele deixa rodando
    $p = Start-Process -FilePath "$B\pg_ctl.exe" -ArgumentList $a -NoNewWindow -PassThru
    $null = $p.Handle   # PS 5.1: sem ler o Handle antes, ExitCode volta vazio
    $p.WaitForExit(); if ($p.ExitCode -ne 0) { throw "pg_ctl falhou ($($p.ExitCode)); veja $LOG" }
}

switch ($acao) {
    'instalar' {
        if (-not (Test-Path "$B\postgres.exe")) {
            $zip = Join-Path $env:TEMP 'pg17-binaries.zip'
            Write-Host "Baixando binários do PostgreSQL 17.6 (EDB)..."
            & curl.exe -s -o $zip $URL
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $z = [IO.Compression.ZipFile]::OpenRead($zip)
            foreach ($e in $z.Entries) {
                if ($e.FullName -match '^pgsql/(bin|lib|share)/' -and $e.Name) {
                    $dest = Join-Path $R $e.FullName
                    New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
                    [IO.Compression.ZipFileExtensions]::ExtractToFile($e, $dest, $true)
                }
            }
            $z.Dispose(); Remove-Item $zip
        }
        if (-not (Test-Path "$D\PG_VERSION")) {
            if (-not (Test-Path $PW)) {
                $bytes = New-Object byte[] 18; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
                [Convert]::ToBase64String($bytes).Replace('+', 'a').Replace('/', 'b') | Set-Content -NoNewline -Encoding ascii $PW
            }
            & "$B\initdb.exe" -D $D -U etl "--pwfile=$PW" -A scram-sha-256 -E UTF8 --locale=C | Out-Null
            Add-Content -Encoding ascii "$D\postgresql.conf" "`nlisten_addresses = 'localhost'`nport = 5433"
            Invoke-PgCtl @('-D', "`"$D`"", '-l', "`"$LOG`"", 'start', '-w')
            Set-Senha; & "$B\createdb.exe" @CON painel
            Write-Host "Cluster criado e banco 'painel' pronto. Para carregar dados: restaurar (backup) ou rodar o orquestrador."
        } else { Write-Host 'Já instalado.' }
    }
    'start'  { Invoke-PgCtl @('-D', "`"$D`"", '-l', "`"$LOG`"", 'start', '-w') }
    'stop'   { Invoke-PgCtl @('-D', "`"$D`"", 'stop', '-m', 'fast') }
    'status' { & "$B\pg_isready.exe" -h localhost -p 5433 }
    'psql'   { Set-Senha; & "$B\psql.exe" @CON -d painel }
    'backup' {
        Set-Senha; New-Item -ItemType Directory -Force (Split-Path $BK) | Out-Null
        & "$B\pg_dump.exe" @CON -d painel --no-owner --no-privileges --exclude-table-data='stg.*' -f $BK
        Write-Host ("Backup: {0} ({1:N0} KB). Faça commit deste arquivo." -f $BK, ((Get-Item $BK).Length / 1KB))
    }
    'restaurar' {
        Set-Senha
        & "$B\dropdb.exe" @CON --if-exists painel; & "$B\createdb.exe" @CON painel
        & "$B\psql.exe" @CON -d painel -q -v ON_ERROR_STOP=1 -f $BK
        Write-Host 'Banco painel restaurado a partir do backup.'
    }
}

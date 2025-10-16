# FastAPI Boilerplate Scripts for Windows PowerShell
# --------------------------------------------------

# Helper function to load environment variables from .env file
function Load-EnvVars {
    if (Test-Path .env) {
        Get-Content .env | Where-Object { $_ -notmatch '^#' -and $_ -match '=' } | ForEach-Object {
            $var = $_.Split('=', 2)
            if ($var.Count -eq 2) {
                $key = $var[0].Trim()
                $value = $var[1].Trim()
                # Remove quotes if present
                if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
    }
}

# Display help information
function Show-Help {
    Write-Host "Environment" -ForegroundColor Blue
    Write-Host "---------------------------------------------------------------" -ForegroundColor Blue
    
    $appName = (Get-Content pyproject.toml | Select-String -Pattern 'name.*=.*"([^"]*)"').Matches.Groups[1].Value
    $appVersion = (Get-Content pyproject.toml | Select-String -Pattern 'version.*=.*"([^"]*)"').Matches.Groups[1].Value
    $gitRevision = git rev-parse HEAD
    
    Write-Host "APP_NAME              $appName" -ForegroundColor Magenta
    Write-Host "APP_VERSION           $appVersion" -ForegroundColor Magenta
    Write-Host "GIT_REVISION          $gitRevision" -ForegroundColor Magenta
    Write-Host ""
    
    Write-Host "Development Targets" -ForegroundColor Blue
    Write-Host "---------------------------------------------------------------" -ForegroundColor Blue
    Write-Host "install               Install dependencies" -ForegroundColor Cyan
    Write-Host "start                 Starts the server" -ForegroundColor Cyan
    Write-Host "migrate               Run the migrations" -ForegroundColor Cyan
    Write-Host "rollback              Rollback migrations one level" -ForegroundColor Cyan
    Write-Host "reset-database        Rollback all migrations" -ForegroundColor Cyan
    Write-Host "generate-migration    Generate a new migration" -ForegroundColor Cyan
    Write-Host "celery-worker         Start celery worker" -ForegroundColor Cyan
    Write-Host "check                 Run code formatter check and linter" -ForegroundColor Cyan
    Write-Host "check-format          Dry-run code formatter" -ForegroundColor Cyan
    Write-Host "lint                  Run linter" -ForegroundColor Cyan
    Write-Host "format                Run code formatter" -ForegroundColor Cyan
    Write-Host "check-lockfile        Compares lock file with pyproject.toml" -ForegroundColor Cyan
    Write-Host "test                  Run the test suite" -ForegroundColor Cyan
}

# Install dependencies
function Install-Dependencies {
    uv sync
}

# Start the server
function Start-Server {
    Load-EnvVars
    uv run python main.py
}

# Run migrations
function Run-Migrations {
    Load-EnvVars
    uv run alembic upgrade head
}

# Rollback migrations one level
function Rollback-Migration {
    Load-EnvVars
    uv run alembic downgrade -1
}

# Rollback all migrations
function Reset-Database {
    Load-EnvVars
    uv run alembic downgrade base
}

# Generate a new migration
function Generate-Migration {
    Load-EnvVars
    $message = Read-Host "Enter migration message"
    uv run alembic revision --autogenerate -m "$message"
}

# Start celery worker
function Start-CeleryWorker {
    Load-EnvVars
    uv run celery -A worker worker -l info
}

# Run code formatter check and linter
function Check-Code {
    Check-Format
    Run-Lint
}

# Dry-run code formatter
function Check-Format {
    uv run black ./ --check
    uv run isort ./ --profile black --check
}

# Run linter
function Run-Lint {
    uv run pylint ./api ./app ./core
}

# Run code formatter
function Format-Code {
    uv run ruff format ./
}

# Compares lock file with pyproject.toml
function Check-Lockfile {
    uv lock --check
}

# Run the test suite
function Run-Tests {
    Load-EnvVars
    uv run pytest -vv -s --cache-clear ./
}

# Main script execution
if ($args.Count -eq 0) {
    Show-Help
    exit 0
}

switch ($args[0]) {
    "help" { Show-Help }
    "install" { Install-Dependencies }
    "start" { Start-Server }
    "migrate" { Run-Migrations }
    "rollback" { Rollback-Migration }
    "reset-database" { Reset-Database }
    "generate-migration" { Generate-Migration }
    "celery-worker" { Start-CeleryWorker }
    "check" { Check-Code }
    "check-format" { Check-Format }
    "lint" { Run-Lint }
    "format" { Format-Code }
    "check-lockfile" { Check-Lockfile }
    "test" { Run-Tests }
    default { 
        Write-Host "Unknown command: $($args[0])" -ForegroundColor Red
        Show-Help
    }
}
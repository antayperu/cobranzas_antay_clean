param(
    [int]$Port = 8501,
    [string]$EnvFile = ".env",
    [switch]$ConfirmProduction
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $ConfirmProduction) {
    Write-Host "Arranque cancelado para proteger PRODUCCION." -ForegroundColor Yellow
    Write-Host "Usa staging con: .\\start_staging.ps1" -ForegroundColor Yellow
    Write-Host "Si realmente deseas PROD, ejecuta: .\\start_prod.ps1 -ConfirmProduction" -ForegroundColor Red
    exit 1
}

function Set-EnvFromFile {
    param([string]$Path)

    Get-Content -Path $Path | ForEach-Object {
        $line = $_.Trim()

        if ([string]::IsNullOrWhiteSpace($line)) { return }
        if ($line.StartsWith("#")) { return }
        if (-not $line.Contains("=")) { return }

        $parts = $line.Split("=", 2)
        $name = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")

        if (-not [string]::IsNullOrWhiteSpace($name)) {
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

if (-not (Test-Path -Path $EnvFile)) {
    Write-Error "No se encontro $EnvFile en la carpeta actual."
}

Set-EnvFromFile -Path $EnvFile

$requiredVars = @("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
$missing = @($requiredVars | Where-Object {
    $currentValue = (Get-Item -Path ("env:" + $_) -ErrorAction SilentlyContinue).Value
    [string]::IsNullOrWhiteSpace($currentValue)
})
if ($missing.Count -gt 0) {
    Write-Error "Faltan variables requeridas en ${EnvFile}: $($missing -join ', ')"
}

if ([string]::IsNullOrWhiteSpace($env:NOTION_TOKEN)) {
    Write-Warning "NOTION_TOKEN no esta definido. Funciones de Notion pueden fallar."
}

Write-Host "Ambiente: PRODUCCION" -ForegroundColor Green
Write-Host "SUPABASE_URL: $($env:SUPABASE_URL)"
Write-Host "Puerto Streamlit: $Port"

Start-Process powershell -ArgumentList 'streamlit run app.py --server.port $Port'
Start-Sleep -Seconds 2
Start-Process "http://localhost:$Port"

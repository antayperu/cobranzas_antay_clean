param(
    [int]$Port = 8502,
    [string]$EnvFile = ".env.staging"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

Write-Host "Ambiente: STAGING" -ForegroundColor Yellow
Write-Host "SUPABASE_URL: $($env:SUPABASE_URL)"
Write-Host "Puerto Streamlit: $Port"

streamlit run app.py --server.port $Port

param(
    [switch]$NoClean,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$distDir = Join-Path $PSScriptRoot "dist\AutoService"
$buildDir = Join-Path $PSScriptRoot "build\AutoService"

Get-Process -Name "AutoService" -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Milliseconds 500

function Remove-WithRetry {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [int]$Attempts = 5,
        [int]$DelayMs = 600
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
            return
        }
        catch {
            if ($attempt -eq $Attempts) {
                throw "Unable to remove '$Path'. Close AutoService, Explorer preview, antivirus scans, and any terminal opened inside that folder, then run this script again. Original error: $($_.Exception.Message)"
            }

            Start-Sleep -Milliseconds ($DelayMs * $attempt)
        }
    }
}

if (-not $NoClean) {
    Remove-WithRetry -Path $distDir
    Remove-WithRetry -Path $buildDir
}

& $Python -m PyInstaller --noconfirm AutoService.spec

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Built: $distDir\AutoService.exe"

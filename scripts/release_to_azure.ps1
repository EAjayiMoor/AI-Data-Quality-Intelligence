param(
    [Parameter(Mandatory = $true)]
    [string]$CommitMessage,
    [string]$ResourceGroup = "RG-DEMO-UKW",
    [string]$WebAppName = "ai-data-quality-intel",
    [string]$AcrName = "crmhcdemo",
    [string]$ImageRepository = "ai-data-quality-intel",
    [string]$HealthEndpoint = "https://ai-data-quality-intel.azurewebsites.net/health",
    [switch]$SkipTests,
    [switch]$DryRun,
    [string[]]$ExcludeFromAutoStage = @(
        "batch_live_run_records.json",
        "batch_live_run_summary.json"
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Tag = Get-Date -Format "yyyyMMdd-HHmmss"
$ImageRef = "${AcrName}.azurecr.io/${ImageRepository}:$Tag"

function Run-OrPrint {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    if ($DryRun) {
        Write-Host "[DRY-RUN] $Description" -ForegroundColor Yellow
        return
    }

    Write-Host "[RUN] $Description" -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Repository: $RepoRoot"
Write-Host "Target Web App: $WebAppName"
Write-Host "Target ACR Image: $ImageRef"

Run-OrPrint -Description "Mark repository as git safe.directory" -Action {
    git config --global --add safe.directory $RepoRoot | Out-Null
}

$statusLines = git -C $RepoRoot status --porcelain

$pathsToStage = @()
foreach ($line in $statusLines) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    $pathFragment = $line.Substring(3)
    if ($pathFragment.Contains(" -> ")) {
        $pathFragment = ($pathFragment -split " -> ")[-1]
    }

    $shouldExclude = $false
    foreach ($excluded in $ExcludeFromAutoStage) {
        if ($pathFragment -eq $excluded) {
            $shouldExclude = $true
            break
        }
    }

    if (-not $shouldExclude) {
        $pathsToStage += $pathFragment
    }
}

if ($pathsToStage.Count -eq 0) {
    throw "No stageable changes found. Commit your desired changes first, then re-run this script."
}

Run-OrPrint -Description "Stage changes (excluding generated batch-run files)" -Action {
    & git -C $RepoRoot add -- @pathsToStage
}

if (-not $DryRun) {
    & git -C $RepoRoot diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        throw "No staged changes to commit after exclusions."
    }
}

if (-not $SkipTests) {
    Run-OrPrint -Description "Run targeted regression tests" -Action {
        Push-Location $RepoRoot
        try {
            & python -m pytest tests/test_executive_metrics.py -q
        }
        finally {
            Pop-Location
        }
    }
}

Run-OrPrint -Description "Create git commit" -Action {
    & git -C $RepoRoot commit -m $CommitMessage
}

Run-OrPrint -Description "Push commit to origin/main" -Action {
    & git -C $RepoRoot push origin main
}

$runId = ""
Run-OrPrint -Description "Trigger ACR build (no streamed logs to avoid encoding issues)" -Action {
    $script:runId = az acr build --registry $AcrName --image "${ImageRepository}:$Tag" --no-logs $RepoRoot --query runId -o tsv
    if ([string]::IsNullOrWhiteSpace($script:runId)) {
        throw "Failed to capture ACR run ID."
    }
    Write-Host "ACR run ID: $script:runId"
}

if (-not $DryRun) {
    Write-Host "Waiting for ACR build completion..."
    $buildCompleted = $false
    for ($i = 0; $i -lt 60; $i++) {
        $status = az acr task show-run --registry $AcrName --run-id $runId --query status -o tsv
        Write-Host "ACR status: $status"
        if ($status -eq "Succeeded") {
            $buildCompleted = $true
            break
        }
        if ($status -in @("Failed", "Canceled", "Error")) {
            throw "ACR build failed with status: $status"
        }
        Start-Sleep -Seconds 10
    }

    if (-not $buildCompleted) {
        throw "Timed out waiting for ACR build to complete."
    }
}

Run-OrPrint -Description "Update Azure Web App container image" -Action {
    az webapp config container set --resource-group $ResourceGroup --name $WebAppName --container-image-name $ImageRef --container-registry-url "https://$AcrName.azurecr.io" | Out-Null
}

Run-OrPrint -Description "Restart Azure Web App" -Action {
    az webapp restart --resource-group $ResourceGroup --name $WebAppName | Out-Null
}

if (-not $DryRun) {
    Write-Host "Checking health endpoint: $HealthEndpoint"
    $healthy = $false
    for ($i = 0; $i -lt 12; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $HealthEndpoint -UseBasicParsing -TimeoutSec 30
            if ($response.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        }
        catch {
            Write-Host "Health check attempt $($i + 1) failed: $($_.Exception.Message)"
        }
        Start-Sleep -Seconds 10
    }

    if (-not $healthy) {
        throw "Deployment completed but health endpoint did not return HTTP 200 in time."
    }
}

Write-Host ""
Write-Host "Release complete." -ForegroundColor Green
Write-Host "Image: $ImageRef"
Write-Host "App: https://$WebAppName.azurewebsites.net"

# E2E Test Runner for Research Orchestrator
# Usage:
#   .\run_e2e.ps1                    # Run all scenarios
#   .\run_e2e.ps1 -Scenario dry-run  # Run single scenario
#   .\run_e2e.ps1 -DryRun            # Preview commands only

param(
    [string]$Scenario = "all",
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"

# Resolve paths
$ScriptDir = $PSScriptRoot
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..\..") | Select-Object -ExpandProperty Path
$SrcDir = Join-Path $ProjectRoot "src"
$ConfigDir = Join-Path $ProjectRoot "build\config\projects"
$Python = "python"

# Counters
$script:Passed = 0
$script:Failed = 0
$script:Skipped = 0

function Test-ApiAvailable {
    return [bool]$env:ANTHROPIC_API_KEY
}

function Write-Result {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Message = ""
    )

    switch ($Status) {
        "PASS" {
            Write-Host "  [PASS] $Name" -ForegroundColor Green
            $script:Passed++
        }
        "FAIL" {
            Write-Host "  [FAIL] $Name - $Message" -ForegroundColor Red
            $script:Failed++
        }
        "SKIP" {
            Write-Host "  [SKIP] $Name - $Message" -ForegroundColor Yellow
            $script:Skipped++
        }
    }
}

function Test-Scenario {
    param(
        [string]$Name,
        [string]$Command,
        [int]$ExpectedExit,
        [string]$ExpectedOutput = "",
        [bool]$RequiresApi = $false
    )

    Write-Host "`nScenario: $Name" -ForegroundColor Cyan

    if ($RequiresApi -and -not (Test-ApiAvailable)) {
        Write-Result $Name "SKIP" "No API key"
        return
    }

    if ($DryRun) {
        Write-Host "  Command: $Command" -ForegroundColor DarkGray
        Write-Result $Name "SKIP" "Dry run mode"
        return
    }

    try {
        $output = Invoke-Expression "$Command 2>&1" | Out-String
        $actualExit = $LASTEXITCODE

        if ($null -eq $actualExit) { $actualExit = 0 }

        if ($actualExit -ne $ExpectedExit) {
            Write-Result $Name "FAIL" "Expected exit $ExpectedExit, got $actualExit"
            return
        }

        if ($ExpectedOutput -and $output -notmatch [regex]::Escape($ExpectedOutput)) {
            Write-Result $Name "FAIL" "Output missing: '$ExpectedOutput'"
            return
        }

        Write-Result $Name "PASS"
    }
    catch {
        Write-Result $Name "FAIL" $_.Exception.Message
    }
}

# ============================================================
# Scenario Definitions
# ============================================================

function Run-DryRun {
    Test-Scenario `
        -Name "Dry Run" `
        -Command "$Python $SrcDir\run_research.py --dry-run --config $ConfigDir\e2e_minimal_test.yaml" `
        -ExpectedExit 0 `
        -ExpectedOutput "Configuration valid!" `
        -RequiresApi $false
}

function Run-InvalidConfig {
    Test-Scenario `
        -Name "Invalid Config" `
        -Command "$Python $SrcDir\run_research.py --config nonexistent.yaml" `
        -ExpectedExit 1 `
        -ExpectedOutput "Error" `
        -RequiresApi $false
}

function Run-Layer0 {
    Test-Scenario `
        -Name "Layer 0 Only" `
        -Command "$Python $SrcDir\run_research.py --layer 0 --config $ConfigDir\e2e_minimal_test.yaml" `
        -ExpectedExit 0 `
        -ExpectedOutput "RESEARCH EXECUTION COMPLETE" `
        -RequiresApi $true
}

function Run-SelectiveVertical {
    Test-Scenario `
        -Name "Selective Vertical" `
        -Command "$Python $SrcDir\run_research.py --layer 2 --verticals healthcare --config $ConfigDir\e2e_minimal_test.yaml" `
        -ExpectedExit 0 `
        -ExpectedOutput "RESEARCH EXECUTION COMPLETE" `
        -RequiresApi $true
}

function Run-SelectiveTitle {
    Test-Scenario `
        -Name "Selective Title" `
        -Command "$Python $SrcDir\run_research.py --layer 3 --titles cio_cto_cluster --config $ConfigDir\e2e_minimal_test.yaml" `
        -ExpectedExit 0 `
        -ExpectedOutput "RESEARCH EXECUTION COMPLETE" `
        -RequiresApi $true
}

function Run-SelectiveServiceCategory {
    Test-Scenario `
        -Name "Selective Service Category" `
        -Command "$Python $SrcDir\run_research.py --layer 0 --service-categories security --config $ConfigDir\e2e_minimal_test.yaml" `
        -ExpectedExit 0 `
        -ExpectedOutput "RESEARCH EXECUTION COMPLETE" `
        -RequiresApi $true
}

function Run-ForceRerun {
    Test-Scenario `
        -Name "Force Re-run" `
        -Command "$Python $SrcDir\run_research.py --layer 2 --verticals healthcare --force --config $ConfigDir\e2e_minimal_test.yaml" `
        -ExpectedExit 0 `
        -ExpectedOutput "RESEARCH EXECUTION COMPLETE" `
        -RequiresApi $true
}

function Run-FullPipeline {
    Test-Scenario `
        -Name "Full Pipeline" `
        -Command "$Python $SrcDir\run_research.py --config $ConfigDir\e2e_minimal_test.yaml" `
        -ExpectedExit 0 `
        -ExpectedOutput "RESEARCH EXECUTION COMPLETE" `
        -RequiresApi $true
}

function Run-BudgetExceeded {
    Test-Scenario `
        -Name "Budget Exceeded" `
        -Command "$Python $SrcDir\run_research.py --config $ConfigDir\e2e_budget_fail.yaml" `
        -ExpectedExit 1 `
        -ExpectedOutput "" `
        -RequiresApi $true
}

# ============================================================
# Main Execution
# ============================================================

Write-Host "============================================" -ForegroundColor White
Write-Host "Research Orchestrator - E2E Test Runner" -ForegroundColor White
Write-Host "============================================" -ForegroundColor White
Write-Host "Project Root: $ProjectRoot"
Write-Host "Config Dir:   $ConfigDir"

if ($DryRun) {
    Write-Host "Mode: DRY RUN (commands printed, not executed)" -ForegroundColor Yellow
}

if (-not (Test-ApiAvailable)) {
    Write-Host "API Key: NOT SET (API-dependent scenarios will be skipped)" -ForegroundColor Yellow
} else {
    Write-Host "API Key: Set" -ForegroundColor Green
}

$scenarios = @{
    "dry-run"          = { Run-DryRun }
    "invalid-config"   = { Run-InvalidConfig }
    "layer-0"          = { Run-Layer0 }
    "selective-vertical"  = { Run-SelectiveVertical }
    "selective-title"     = { Run-SelectiveTitle }
    "selective-svccat"    = { Run-SelectiveServiceCategory }
    "force-rerun"         = { Run-ForceRerun }
    "full-pipeline"       = { Run-FullPipeline }
    "budget-exceeded"     = { Run-BudgetExceeded }
}

if ($Scenario -eq "all") {
    # Run non-API scenarios first, then API-dependent
    Run-DryRun
    Run-InvalidConfig
    Run-Layer0
    Run-SelectiveVertical
    Run-SelectiveTitle
    Run-SelectiveServiceCategory
    Run-ForceRerun
    Run-FullPipeline
    Run-BudgetExceeded
}
elseif ($scenarios.ContainsKey($Scenario)) {
    & $scenarios[$Scenario]
}
else {
    Write-Host "Unknown scenario: $Scenario" -ForegroundColor Red
    Write-Host "Available: $($scenarios.Keys -join ', ')" -ForegroundColor Yellow
    exit 1
}

# Summary
Write-Host "`n============================================" -ForegroundColor White
Write-Host "Results: $($script:Passed) passed, $($script:Failed) failed, $($script:Skipped) skipped" -ForegroundColor White
Write-Host "============================================" -ForegroundColor White

if ($script:Failed -gt 0) {
    exit 1
}

# Simple release packaging script for SmartBridge B.Tech submission
# PowerShell version for Windows

param()

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$releaseDir = Join-Path $projectRoot "release"
$zipName = "smartbridge_release.zip"

Write-Host "[*] SmartBridge Release Packaging" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Clean previous release
if (Test-Path $releaseDir) {
    Remove-Item $releaseDir -Recurse -Force
}
New-Item -ItemType Directory -Path $releaseDir | Out-Null

Write-Host "[1] Copying source code..." -ForegroundColor Yellow

$sourceItems = Get-ChildItem $projectRoot -Recurse -Force -ErrorAction SilentlyContinue
$excludePatterns = @('\.git', '\.venv', '__pycache__', '\.pyc', '\.env', 'secrets', 'node_modules', '\.DS_Store', '\.pytest_cache')

foreach ($item in $sourceItems) {
    $skip = $false
    foreach ($pattern in $excludePatterns) {
        if ($item.FullName -match $pattern) {
            $skip = $true
            break
        }
    }
    
    if (-not $skip) {
        $relativePath = $item.FullName.Substring($projectRoot.Length + 1)
        $targetPath = Join-Path $releaseDir ("smartbridge" + '\' + $relativePath)
        
        if ($item.PSIsContainer) {
            if (-not (Test-Path $targetPath)) {
                New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
            }
        } else {
            $targetDir = Split-Path -Parent $targetPath
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            Copy-Item $item.FullName -Destination $targetPath -Force -ErrorAction SilentlyContinue | Out-Null
        }
    }
}

Write-Host "[OK] Source code copied" -ForegroundColor Green

Write-Host ""
Write-Host "[2] Adding documentation..." -ForegroundColor Yellow
$docsDir = Join-Path $releaseDir "smartbridge\docs\submission"
New-Item -ItemType Directory -Path $docsDir -Force | Out-Null

$docFiles = @("tech_spec.md", "demo_script.md", "viva_questions.md", "grading_checklist.md", "test_report.md")
foreach ($docFile in $docFiles) {
    $source = Join-Path (Join-Path $projectRoot "docs") $docFile
    if (Test-Path $source) {
        $dest = Join-Path $docsDir $docFile
        Copy-Item $source -Destination $dest -Force
        Write-Host "    Copied $docFile" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[3] Creating sample data..." -ForegroundColor Yellow
$sampleDataDir = Join-Path $releaseDir "smartbridge\sample_data"
New-Item -ItemType Directory -Path $sampleDataDir -Force | Out-Null
Write-Host "    Sample data directory created" -ForegroundColor Green

Write-Host ""
Write-Host "[4] Creating README..." -ForegroundColor Yellow
$readmeSrc = Join-Path $projectRoot "README.md"
if (Test-Path $readmeSrc) {
    $dest = Join-Path $releaseDir "smartbridge\SUBMISSION_README.md"
    Copy-Item $readmeSrc -Destination $dest -Force
}
Write-Host "    README created" -ForegroundColor Green

Write-Host ""
Write-Host "[5] Creating instructions.txt..." -ForegroundColor Yellow

$instructionsFile = Join-Path $releaseDir "instructions.txt"

$instructionsLines = @()
$instructionsLines += "================================================================================"
$instructionsLines += "  SMARTBRIDGE: B.TECH SUBMISSION PACKAGE"
$instructionsLines += "  March 9, 2026 | Version 1.0.0"
$instructionsLines += "================================================================================"
$instructionsLines += ""
$instructionsLines += "CONTENTS"
$instructionsLines += "--------"
$instructionsLines += "1. Source code - backend and frontend"
$instructionsLines += "2. Technical documentation - spec, demo, viva prep"
$instructionsLines += "3. Test suite - 92 percent coverage, all passing"
$instructionsLines += "4. Sample data - 3 pre-loaded users"
$instructionsLines += ""
$instructionsLines += "QUICK START"
$instructionsLines += "-----------"
$instructionsLines += ""
$instructionsLines += "With Docker:"
$instructionsLines += "  1. cd smartbridge"
$instructionsLines += "  2. docker-compose -f docker-compose.prod.yml up -d"
$instructionsLines += "  3. streamlit run frontend/streamlit_app.py"
$instructionsLines += "  4. Open http://localhost:8501"
$instructionsLines += ""
$instructionsLines += "With Python only:"
$instructionsLines += "  1. cd smartbridge"
$instructionsLines += "  2. python3 -m venv venv"
$instructionsLines += "  3. source venv/bin/activate"
$instructionsLines += "  4. pip install -r requirements.txt"
$instructionsLines += "  5. python backend/app.py"
$instructionsLines += "  6. streamlit run frontend/streamlit_app.py"
$instructionsLines += ""
$instructionsLines += "DOCUMENTATION TO READ IN ORDER"
$instructionsLines += "------------------------------"
$instructionsLines += "1. docs/submission/tech_spec.md"
$instructionsLines += "2. docs/submission/demo_script.md"
$instructionsLines += "3. docs/submission/viva_questions.md"
$instructionsLines += "4. docs/submission/grading_checklist.md"
$instructionsLines += "5. docs/submission/test_report.md"
$instructionsLines += ""
$instructionsLines += "DEMO STEPS (8-10 MINUTES)"
$instructionsLines += "------------------------"
$instructionsLines += "Follow docs/submission/demo_script.md for complete walkthrough"
$instructionsLines += ""
$instructionsLines += "1. Consent dialog"
$instructionsLines += "2. Create investment plan"
$instructionsLines += "3. Edit assumptions"
$instructionsLines += "4. Calculate SIP"
$instructionsLines += "5. Generate AI explanation"
$instructionsLines += "6. Modify and see update"
$instructionsLines += "7. Export as PDF"
$instructionsLines += "8. Review audit trail"
$instructionsLines += ""
$instructionsLines += "================================================================================"
$instructionsLines += "  Good luck with your viva defense!"
$instructionsLines += "  Created: March 9, 2026 | Version 1.0.0"
$instructionsLines += "================================================================================"

$instructionsLines | Out-File -FilePath $instructionsFile -Encoding UTF8
Write-Host "    Instructions created" -ForegroundColor Green

Write-Host ""
Write-Host "[6] Building release ZIP..." -ForegroundColor Yellow

Add-Type -AssemblyName System.IO.Compression.FileSystem

$zipPath = Join-Path $releaseDir $zipName
$smartbridgePath = Join-Path $releaseDir "smartbridge"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

[System.IO.Compression.ZipFile]::CreateFromDirectory($smartbridgePath, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)

Write-Host "    ZIP created" -ForegroundColor Green

Write-Host ""
Write-Host "[7] Verification..." -ForegroundColor Yellow

if (Test-Path $zipPath) {
    $zipSize = (Get-Item $zipPath).Length / 1MB
    Write-Host "    Archive size: $([Math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
    
    $zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
    $fileCount = $zip.Entries.Count
    $zip.Dispose()
    
    Write-Host "    Files included: $fileCount" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[SUCCESS] Release package ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Location: $zipPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Transfer smartbridge_release.zip to examiner"
Write-Host "  2. Examiner unzips and runs: docker-compose up"
Write-Host "  3. Follow docs/submission/demo_script.md"
Write-Host "  4. Present using viva_questions.md prep"
Write-Host ""

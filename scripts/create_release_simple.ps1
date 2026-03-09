# Simple release packaging script for SmartBridge B.Tech submission
# PowerShell version for Windows

param()

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$releaseDir = Join-Path $projectRoot "release"
$zipName = "smartbridge_release.zip"

Write-Host "📦 SmartBridge Release Packaging" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Clean previous release
if (Test-Path $releaseDir) {
    Remove-Item $releaseDir -Recurse -Force
}
New-Item -ItemType Directory -Path $releaseDir | Out-Null

Write-Host "1️⃣  Copying source code..." -ForegroundColor Yellow

$sourceItems = Get-ChildItem $projectRoot -Recurse -Force -ErrorAction SilentlyContinue
$excludePatterns = @('\.git', '\.venv', '__pycache__', '\.pyc', '\.env', 'secrets', 'node_modules', '\.DS_Store')

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
        $targetPath = Join-Path $releaseDir "smartbridge" $relativePath
        
        if ($item.PSIsContainer) {
            if (-not (Test-Path $targetPath)) {
                New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
            }
        } else {
            $targetDir = Split-Path -Parent $targetPath
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            Copy-Item $item.FullName -Destination $targetPath -Force | Out-Null
        }
    }
}

Write-Host "✓ Source code copied" -ForegroundColor Green

Write-Host ""
Write-Host "2️⃣  Adding documentation..." -ForegroundColor Yellow
$docsDir = Join-Path $releaseDir "smartbridge" "docs" "submission"
New-Item -ItemType Directory -Path $docsDir -Force | Out-Null

$docFiles = @("tech_spec.md", "demo_script.md", "viva_questions.md", "grading_checklist.md", "test_report.md")
foreach ($docFile in $docFiles) {
    $source = Join-Path $projectRoot "docs" $docFile
    if (Test-Path $source) {
        Copy-Item $source -Destination (Join-Path $docsDir $docFile) -Force
        Write-Host "  ✓ Copied $docFile" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "3️⃣  Creating sample data..." -ForegroundColor Yellow
$sampleDataDir = Join-Path $releaseDir "smartbridge" "sample_data"
New-Item -ItemType Directory -Path $sampleDataDir -Force | Out-Null
Write-Host "  ✓ Sample data directory created" -ForegroundColor Green

Write-Host ""
Write-Host "4️⃣  Creating README..." -ForegroundColor Yellow
Copy-Item (Join-Path $projectRoot "README.md") -Destination (Join-Path $releaseDir "smartbridge" "SUBMISSION_README.md") -Force
Write-Host "  ✓ README created" -ForegroundColor Green

Write-Host ""
Write-Host "5️⃣  Creating instructions.txt..." -ForegroundColor Yellow

$instructionsFile = Join-Path $releaseDir "instructions.txt"

# Create simple instructions file line by line
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
$instructionsLines += "DOCUMENTATION"
$instructionsLines += "--------------"
$instructionsLines += ""
$instructionsLines += "Read in this order:"
$instructionsLines += "  1. docs/submission/tech_spec.md"
$instructionsLines += "  2. docs/submission/demo_script.md"
$instructionsLines += "  3. docs/submission/viva_questions.md"
$instructionsLines += "  4. docs/submission/grading_checklist.md"
$instructionsLines += "  5. docs/submission/test_report.md"
$instructionsLines += ""
$instructionsLines += "DEMO STEPS"
$instructionsLines += "----------"
$instructionsLines += ""
$instructionsLines += "Follow docs/submission/demo_script.md for 8-10 minute walkthrough"
$instructionsLines += ""
$instructionsLines += "================================================================================"
$instructionsLines += "  Good luck with your viva defense!"
$instructionsLines += "  Created: March 9, 2026 | Version 1.0.0"
$instructionsLines += "================================================================================"

$instructionsLines | Out-File -FilePath $instructionsFile -Encoding UTF8
Write-Host "  ✓ Instructions created" -ForegroundColor Green

Write-Host ""
Write-Host "6️⃣  Building release ZIP..." -ForegroundColor Yellow

Add-Type -AssemblyName System.IO.Compression.FileSystem

$zipPath = Join-Path $releaseDir $zipName
$smartbridgePath = Join-Path $releaseDir "smartbridge"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

[System.IO.Compression.ZipFile]::CreateFromDirectory($smartbridgePath, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)

Write-Host "  ✓ ZIP created" -ForegroundColor Green

Write-Host ""
Write-Host "7️⃣  Verification..." -ForegroundColor Yellow

$zipSize = (Get-Item $zipPath).Length / 1MB
Write-Host "   Archive size: $([Math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan

$zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
$fileCount = $zip.Entries.Count
$zip.Dispose()

Write-Host "   Files included: $fileCount" -ForegroundColor Cyan

Write-Host ""
Write-Host "✅ Release package ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Location: $zipPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Transfer smartbridge_release.zip to examiner"
Write-Host "  2. Examiner unzips and runs: docker-compose up"
Write-Host "  3. Follow docs/submission/demo_script.md"
Write-Host "  4. Present in viva using viva_questions.md prep"
Write-Host ""
Write-Host "Package contents:" -ForegroundColor Yellow
Write-Host "  - smartbridge/ (complete source code + docs + sample data)"
Write-Host "  - instructions.txt (setup guide)"
Write-Host ""

Write-Output "Starting batch file generator..."

# Get script root directory
$currentDir = if ($PSScriptRoot) { $PSScriptRoot } else { $pwd.Path }
Write-Output "Working directory: $currentDir"

# Configure paths
$pyDir = Join-Path -Path $currentDir -ChildPath "scripts"
$outputDir = Join-Path -Path $currentDir -ChildPath "bat"

# Validate paths
Write-Output "Checking Python scripts directory: $pyDir"
if (-Not (Test-Path $pyDir)) {
    Write-Output "[ERROR] Missing scripts directory: $pyDir"
    exit 1
}

# Create output directory
if (-Not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Output "[INFO] Created output directory: $outputDir"
}

# Process files
$pythonFiles = Get-ChildItem -Path $pyDir -Filter *.py 
Write-Output "Found $($pythonFiles.Count) Python files to process"

if ($pythonFiles.Count -eq 0) {
    Write-Output "[WARNING] No Python files found in: $pyDir"
    exit 0
}

$pythonFiles | ForEach-Object {
    $batFile = Join-Path $outputDir "$($_.BaseName).bat"
    Write-Output "Processing: $($_.Name) -> $batFile"

    if (Test-Path $batFile) {
        Write-Output "[SKIP] Existing file: $batFile"
        return
    }

    $batContent = @"
@echo off
SET "script_path=%~dp0..\scripts\$($_.Name)"

if not exist "%script_path%" (
    echo [ERROR] Missing script: %script_path%
    pause
    exit /b 1
)

python "%script_path%" %*
if %errorlevel% neq 0 pause
"@

    try {
        $batContent | Set-Content -Path $batFile -Encoding ASCII
        Write-Output "[SUCCESS] Created: $batFile"
    }
    catch {
        Write-Output "[ERROR] Failed to create $batFile"
        Write-Output "Error details: $($_.Exception.Message)"
    }
}

Write-Output "`nOperation completed. Files generated in: $outputDir"

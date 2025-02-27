# Auto-generate batch files for all .py scripts in the parent directory (skip existing .bat)
Write-Output "Checking and generating batch files..."

# Define the output directory for .bat files
$outputDir = Join-Path -Path $PWD -ChildPath "bat"

# Create the output directory if it doesn't exist
if (-Not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir
    Write-Output "Created output directory: $outputDir"
}

# Get all .py files in the parent directory
Get-ChildItem -Path . -Filter *.py | ForEach-Object {
    # Construct the .bat file name and path
    $batName = $_.BaseName + ".bat"
    $batPath = Join-Path -Path $outputDir -ChildPath $batName
    $pyFileName = $_.Name
    
    # Skip if .bat already exists
    if (Test-Path $batPath) {
        Write-Output "Skipped: $batPath (file already exists)"
        return
    }
    
    # Define the content of the batch file
    $batContent = @"
@echo off
python "%~dp0..\$pyFileName" %*
"@
    
    # Create new .bat file with the defined content
    $batContent | Set-Content -Path $batPath -Encoding ASCII
    Write-Output "Created: $batPath"
}

# Output completion message
Write-Output "Process completed! No existing files were overwritten."
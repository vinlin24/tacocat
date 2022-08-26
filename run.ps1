<#
Script for automating common tasks.
#>

$ROOT_NAME = "tacocat"

# Assert that script is being run at project root
$currentDir = Split-Path -Path (Get-Location) -Leaf
if ($currentDir -ne $ROOT_NAME) {
    Write-Host "Script must be run at project root, aborted." -ForegroundColor Red
    exit 1
}

# Bot runtime entry point
try { python bot/main.py }
# Cleanup
finally { Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse }

exit 0

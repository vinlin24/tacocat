<#
Script for automating common tasks.
#>

param (
    [Parameter()]
    [string] $TaskName
)

$SCRIPT_NAME = "run.ps1"
$ROOT_NAME = "tacocat"
$ROOT_PARENT_NAME = "repos"

$TEST_FILE_PATH = "temp/test.py"

# Assert that script is being run at project root
$currentDir = Split-Path (Get-Location) -Leaf
$dirPart = Split-Path (Get-Location) -Parent
$parentDir = Split-Path $dirPart -Leaf
if ($currentDir -ne $ROOT_NAME -or $parentDir -ne $ROOT_PARENT_NAME) {
    Write-Host "Script must be run at project root, aborted." -ForegroundColor Red
    exit 1
}

$VENV_PATH = Join-Path (Get-Location) ".venv"

# Assert that script is being run within project's venv
if ($env:VIRTUAL_ENV -ne $VENV_PATH) {
    Write-Host "Script must be run within project's venv, aborted." -ForegroundColor Red
    exit 1
}

<#
Helper function for setting focus to another open window.
Directly from: https://stackoverflow.com/a/58548853/14226122
#>
function Show-Window {
    param(
        [Parameter(Mandatory)]
        [string] $ProcessName
    )
  
    # As a courtesy, strip '.exe' from the name, if present.
    $ProcessName = $ProcessName -replace "\.exe$"
  
    # Get the ID of the first instance of a process with the given name
    # that has a non-empty window title.
    # NOTE: If multiple instances have visible windows, it is undefined
    #       which one is returned.
    $procId = (Get-Process -ErrorAction Ignore $ProcessName).Where({ $_.MainWindowTitle }, "First").Id
  
    if (-not $procId) { Throw "No $ProcessName process with a non-empty window title found." }
  
    # Note: 
    #  * This can still fail, because the window could have been closed since
    #    the title was obtained.
    #  * If the target window is currently minimized, it gets the *focus*, but is
    #    *not restored*.
    #  * The return value is $true only if the window still existed and was *not
    #    minimized*; this means that returning $false can mean EITHER that the
    #    window doesn't exist OR that it just happened to be minimized.
    $null = (New-Object -ComObject WScript.Shell).AppActivate($procId)
}

<# Run Discord bot #>
function Start-BotScript {
    Write-Host "TASK: Running bot script..." -ForegroundColor Yellow
    try {
        # Try moving focus to Discord to prepare for testing
        Show-Window "Discord"
        # Bot runtime entry point
        python -m bot
    }
    finally {
        # Cleanup
        Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse
        # Return to VS Code
        Show-Window "Code"
    }
}

<# Run test module #>
function Start-TestScript {
    Write-Host "TASK: Running $TEST_FILE_PATH..." -ForegroundColor Yellow
    python $TEST_FILE_PATH
}

<# Run unit tests #>
function Start-UnitTests {
    Write-Host "TASK: Running unit tests..." -ForegroundColor Yellow
    python -m unittest discover -s .\tests
}

<# Run pre-commit checklist #>
function Start-CommitCheck {
    Write-Host "TASK: Running pre-commit checklist..." -ForegroundColor Yellow
    # Update requirements
    try {
        pip freeze | Out-File -Encoding utf8 "requirements.txt" 
        Write-Host "Updated requirements.txt with state of current venv."
    }
    catch {
        Write-Host "Couldn't complete checklist." -ForegroundColor Red
    }
}

<# -------------------- MAIN PROCESS HERE -------------------- #>

# Determine which task caller wants to run
switch ($TaskName) {
    "" { $taskFunction = "Start-BotScript" }
    "Run" { $taskFunction = "Start-BotScript" }
    "Test" { $taskFunction = "Start-TestScript" }
    "Unittest" { $taskFunction = "Start-Unittests" }
    "Commit" { $taskFunction = "Start-CommitCheck" }
    default {
        Write-Host "Unrecognized task name '$TaskName', aborted." -ForegroundColor Red
        exit 1
    }
}

# Run the task
& $taskFunction

Write-Host "Finished running $SCRIPT_NAME." -ForegroundColor Green
exit 0

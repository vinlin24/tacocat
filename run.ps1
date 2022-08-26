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

<# -------------------- MAIN PROCESS HERE -------------------- #>

try {
    # Try moving focus to Discord to prepare for testing
    Show-Window "Discord"
    # Bot runtime entry point
    python bot/main.py
}
finally {
    # Cleanup
    Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse
    # Return to VS Code
    Show-Window "Code"
}

exit 0

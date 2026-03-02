$ErrorActionPreference = "Stop"

function Invoke-CheckedCommand {
  param(
    [Parameter(Mandatory = $true)]
    [scriptblock]$Command
  )

  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed with exit code $LASTEXITCODE"
  }
}

Write-Host "[1/3] Backend unit tests"
Invoke-CheckedCommand { & ".\.venv\Scripts\python.exe" -m unittest discover -s backend/tests -p "test_*.py" }

Write-Host "[2/3] Frontend build"
Push-Location frontend
Invoke-CheckedCommand { & "npm.cmd" run build }
Pop-Location

Write-Host "[3/3] Done"
Write-Host "Smoke check passed."

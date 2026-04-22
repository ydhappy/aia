param(
    [string]$Python = ".\.venv\Scripts\python.exe",
    [string]$Java8 = "C:\Program Files\Java\jdk1.8.0_211\bin\javac.exe"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (!(Test-Path $Python)) {
    throw "Python executable not found: $Python"
}

& $Python -m compileall -q app scripts integration tests
if ($LASTEXITCODE -ne 0) {
    throw "compileall failed: $LASTEXITCODE"
}
Write-Output "COMPILEALL_EXIT=0"

& $Python -m pytest
if ($LASTEXITCODE -ne 0) {
    throw "pytest failed: $LASTEXITCODE"
}
Write-Output "PYTEST_EXIT=0"

& $Python -m pip check
if ($LASTEXITCODE -ne 0) {
    throw "pip check failed: $LASTEXITCODE"
}
Write-Output "PIP_CHECK_EXIT=0"

if (Test-Path $Java8) {
    & $Java8 -encoding UTF-8 integration\java8\*.java
    if ($LASTEXITCODE -ne 0) {
        throw "Java 8 integration compile failed: $LASTEXITCODE"
    }
    Get-ChildItem -Path integration\java8 -Filter *.class | Remove-Item -Force
    Write-Output "JAVA8_INTEGRATION_COMPILE=0"
} else {
    Write-Output "JAVA8_INTEGRATION_COMPILE=SKIPPED_JAVAC_NOT_FOUND"
}

Write-Output "AIA_QUALITY_GATES=PASS"

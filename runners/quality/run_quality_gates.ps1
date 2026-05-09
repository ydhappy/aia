param(
    [string]$Python = ".\.venv\Scripts\python.exe",
    [string]$Java8 = "C:\Program Files\Java\jdk1.8.0_211\bin\javac.exe"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

if (!(Test-Path $Python)) {
    throw "Python executable not found: $Python"
}

& $Python -m compileall -q app runners tests
if ($LASTEXITCODE -ne 0) {
    throw "compileall failed: $LASTEXITCODE"
}
Write-Output "COMPILEALL_EXIT=0"

& $Python -m pytest tests/test_robot_crud_api.py
if ($LASTEXITCODE -ne 0) {
    throw "robot CRUD API pytest failed: $LASTEXITCODE"
}
Write-Output "ROBOT_CRUD_PYTEST_EXIT=0"

& $Python -m pytest tests/test_robot_spawn_request_api.py
if ($LASTEXITCODE -ne 0) {
    throw "robot spawn request API pytest failed: $LASTEXITCODE"
}
Write-Output "ROBOT_SPAWN_REQUEST_API_PYTEST_EXIT=0"

& $Python -m pytest tests/test_spawn_request_dashboard.py
if ($LASTEXITCODE -ne 0) {
    throw "spawn request dashboard pytest failed: $LASTEXITCODE"
}
Write-Output "SPAWN_REQUEST_DASHBOARD_PYTEST_EXIT=0"

& $Python -m pytest tests/test_mysql55_schema_compat.py
if ($LASTEXITCODE -ne 0) {
    throw "MySQL 5.5 schema compatibility pytest failed: $LASTEXITCODE"
}
Write-Output "MYSQL55_SCHEMA_COMPAT_PYTEST_EXIT=0"

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
    $javaFiles = @()
    $javaFiles += Get-ChildItem -Path integration\java8 -Filter *.java | ForEach-Object { $_.FullName }
    if (Test-Path examples\java8) {
        $javaFiles += Get-ChildItem -Path examples\java8 -Filter *.java | ForEach-Object { $_.FullName }
    }
    & $Java8 -encoding UTF-8 @javaFiles
    if ($LASTEXITCODE -ne 0) {
        throw "Java 8 compile failed: $LASTEXITCODE"
    }
    Get-ChildItem -Path integration\java8 -Filter *.class | Remove-Item -Force
    if (Test-Path examples\java8) {
        Get-ChildItem -Path examples\java8 -Filter *.class | Remove-Item -Force
    }
    Write-Output "JAVA8_COMPILE=0"
} else {
    Write-Output "JAVA8_COMPILE=SKIPPED_JAVAC_NOT_FOUND"
}

Write-Output "AIA_QUALITY_GATES=PASS"

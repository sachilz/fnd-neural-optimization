<#
.SYNOPSIS
Single-command Windows native startup for Fake News Detection.
#>

$ErrorActionPreference = "Stop"

# 1. Detect project root
$DIR = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "                 FND" -ForegroundColor Cyan
Write-Host "          Fake News Detection" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 2. Verify virtual environment
$VENV_PATH = Join-Path $DIR ".venv"
$PYTHON_EXE = Join-Path $VENV_PATH "Scripts\python.exe"
$UVICORN_EXE = Join-Path $VENV_PATH "Scripts\uvicorn.exe"

if (-Not (Test-Path $VENV_PATH)) {
    Write-Host "ERROR: Python virtual environment not found at $VENV_PATH" -ForegroundColor Red
    Write-Host "Please create it and install requirements:"
    Write-Host "  py -m venv .venv"
    Write-Host "  .\.venv\Scripts\python.exe -m pip install --upgrade pip"
    Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

if (-Not (Test-Path $PYTHON_EXE) -Or -Not (Test-Path $UVICORN_EXE)) {
    Write-Host "ERROR: python or uvicorn not found in .venv\Scripts" -ForegroundColor Red
    Write-Host "Please ensure you have installed the requirements:"
    Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

# 3. Verify Node and npm
if (-Not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: node is not installed or not in PATH." -ForegroundColor Red
    exit 1
}
if (-Not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: npm is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# 4. Verify ports
$port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "ERROR: Port 8000 is currently occupied. Please free this port for the backend." -ForegroundColor Red
    exit 1
}

$port5173 = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
if ($port5173) {
    Write-Host "ERROR: Port 5173 is currently occupied. Please free this port for the frontend." -ForegroundColor Red
    exit 1
}

# 5. Create runtime directory
$RUNTIME_DIR = Join-Path $DIR ".runtime"
if (-Not (Test-Path $RUNTIME_DIR)) {
    New-Item -ItemType Directory -Force -Path $RUNTIME_DIR | Out-Null
}

$BACKEND_LOG = Join-Path $RUNTIME_DIR "backend.log"
$FRONTEND_LOG = Join-Path $RUNTIME_DIR "frontend.log"

Write-Host "Starting FND services... (Logs saved to .runtime/)"

# Start Backend
$backendProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
$backendProcessInfo.FileName = $PYTHON_EXE
$backendProcessInfo.Arguments = "-m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --app-dir `"$DIR`""
$backendProcessInfo.RedirectStandardOutput = $true
$backendProcessInfo.RedirectStandardError = $true
$backendProcessInfo.UseShellExecute = $false
$backendProcessInfo.CreateNoWindow = $true

$backendProcess = New-Object System.Diagnostics.Process
$backendProcess.StartInfo = $backendProcessInfo
[void]$backendProcess.Start()

# Log backend
$backendOut = { Out-File -FilePath $BACKEND_LOG -InputObject $args[0].Data -Append }
Register-ObjectEvent -InputObject $backendProcess -EventName OutputDataReceived -Action $backendOut | Out-Null
Register-ObjectEvent -InputObject $backendProcess -EventName ErrorDataReceived -Action $backendOut | Out-Null
$backendProcess.BeginOutputReadLine()
$backendProcess.BeginErrorReadLine()

# Wait for Backend Health
Write-Host -NoNewline "Waiting for backend..."
$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -ErrorAction Stop
        if ($response.status -eq "ok") {
            $backendReady = $true
            break
        }
    } catch {
        # Ignore and keep polling
    }
    
    if ($backendProcess.HasExited) {
        break
    }
    
    Start-Sleep -Seconds 1
    Write-Host -NoNewline "."
}
Write-Host ""

if (-Not $backendReady) {
    Write-Host "ERROR: Backend failed to start!" -ForegroundColor Red
    Write-Host "--- BACKEND LOG ---" -ForegroundColor Red
    Get-Content $BACKEND_LOG
    exit 1
}

# Start Frontend
$frontendDir = Join-Path $DIR "frontend"
$npmCommand = Get-Command "npm" | Select-Object -ExpandProperty Source

if (-Not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies... (this might take a minute)"
    $installProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm install" -WorkingDirectory $frontendDir -Wait -NoNewWindow -PassThru
    if ($installProcess.ExitCode -ne 0) {
        Write-Host "ERROR: Failed to install frontend dependencies." -ForegroundColor Red
        exit 1
    }
}

$frontendProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
$frontendProcessInfo.FileName = "cmd.exe"
$frontendProcessInfo.Arguments = "/c npm run dev"
$frontendProcessInfo.WorkingDirectory = $frontendDir
$frontendProcessInfo.RedirectStandardOutput = $true
$frontendProcessInfo.RedirectStandardError = $true
$frontendProcessInfo.UseShellExecute = $false
$frontendProcessInfo.CreateNoWindow = $true

$frontendProcess = New-Object System.Diagnostics.Process
$frontendProcess.StartInfo = $frontendProcessInfo
[void]$frontendProcess.Start()

# Log frontend
$frontendOut = { Out-File -FilePath $FRONTEND_LOG -InputObject $args[0].Data -Append }
Register-ObjectEvent -InputObject $frontendProcess -EventName OutputDataReceived -Action $frontendOut | Out-Null
Register-ObjectEvent -InputObject $frontendProcess -EventName ErrorDataReceived -Action $frontendOut | Out-Null
$frontendProcess.BeginOutputReadLine()
$frontendProcess.BeginErrorReadLine()

# Wait for Frontend
Write-Host -NoNewline "Waiting for frontend..."
$frontendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    $port5173Check = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    if ($port5173Check) {
        $frontendReady = $true
        break
    }
    
    if ($frontendProcess.HasExited) {
        break
    }
    
    Start-Sleep -Seconds 1
    Write-Host -NoNewline "."
}
Write-Host ""

if (-Not $frontendReady) {
    Write-Host "ERROR: Frontend failed to start!" -ForegroundColor Red
    Write-Host "--- FRONTEND LOG ---" -ForegroundColor Red
    Get-Content $FRONTEND_LOG
    
    # Cleanup backend
    $backendProcess.Kill()
    exit 1
}

Write-Host "✓ Backend ready" -ForegroundColor Green
Write-Host "✓ Frontend ready" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "             FND IS READY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Web UI:" -ForegroundColor White
Write-Host "http://localhost:5173" -ForegroundColor Blue
Write-Host ""
Write-Host "API:" -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Blue
Write-Host ""
Write-Host "Health:" -ForegroundColor White
Write-Host "http://localhost:8000/health" -ForegroundColor Blue
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow

try {
    # Keep script alive until Ctrl+C
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`nShutting down FND..." -ForegroundColor Yellow
    if ($backendProcess -and -Not $backendProcess.HasExited) {
        $backendProcess.Kill()
    }
    if ($frontendProcess -and -Not $frontendProcess.HasExited) {
        # Taskkill to ensure all child node processes from npm are terminated on Windows
        & taskkill /F /T /PID $frontendProcess.Id | Out-Null
    }
}
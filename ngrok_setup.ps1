# Goethe Bot - ngrok setup for instant public URL
# Run this in PowerShell to expose your local bot to the internet
#
# Prerequisites: Download ngrok from https://ngrok.com/download
# 1. Unzip ngrok.exe anywhere
# 2. Run: ngrok config add-authtoken YOUR_TOKEN (free signup at ngrok.com)
# 3. Then run this script

Write-Host "=== Goethe Bot - ngrok Public URL Setup ===" -ForegroundColor Cyan
Write-Host ""

$projectDir = "C:\Users\brosp\AppData\Local\Temp\opencode\goethe-bot"

# Check ngrok
$ngrok = Get-Command "ngrok.exe" -ErrorAction SilentlyContinue
if (-not $ngrok) {
    # Common locations
    $paths = @(
        ".\ngrok.exe",
        "C:\tools\ngrok.exe",
        "$env:USERPROFILE\Downloads\ngrok.exe",
        "$env:USERPROFILE\ngrok.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) { $ngrok = $p; break }
    }
}

if (-not $ngrok) {
    Write-Host "ngrok not found!" -ForegroundColor Yellow
    Write-Host "Download from: https://ngrok.com/download" -ForegroundColor Yellow
    Write-Host "Then place ngrok.exe in this folder or your PATH." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Quick setup:"
    Write-Host "  1. Go to https://ngrok.com and sign up (free)"
    Write-Host "  2. Download ngrok.exe"
    Write-Host "  3. Run: ngrok config add-authtoken YOUR_TOKEN"
    Write-Host "  4. Run this script again"
    pause
    exit
}

Write-Host "Starting bot server..." -ForegroundColor Green

# Kill any previous instances
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*webapp.py*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Start Flask in background
$job = Start-Job -ScriptBlock {
    param($dir)
    cd $dir
    $env:PYTHONIOENCODING = "utf-8"
    python webapp.py
} -ArgumentList $projectDir

Start-Sleep -Seconds 3

# Check if Flask started
$test = Invoke-WebRequest -Uri "http://localhost:5000/" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
if (-not $test -or $test.StatusCode -ne 200) {
    Write-Host "Failed to start bot server!" -ForegroundColor Red
    Stop-Job $job
    Remove-Job $job
    pause
    exit
}

Write-Host "Bot server is running on http://localhost:5000" -ForegroundColor Green
Write-Host ""
Write-Host "Starting ngrok tunnel..." -ForegroundColor Green

# Start ngrok
Start-Process -WindowStyle Hidden -FilePath "ngrok.exe" -ArgumentList "http http://localhost:5000 --log=stdout"

Start-Sleep -Seconds 4

# Get the public URL
try {
    $ngrokApi = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 5
    $publicUrl = $ngrokApi.tunnels[0].public_url
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host "  YOUR PUBLIC URL:" -ForegroundColor Cyan
    Write-Host "  $publicUrl" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Send this link to anyone to access the bot!" -ForegroundColor White
    Write-Host "Press Ctrl+C to stop" -ForegroundColor White

    # Keep running
    while ($true) {
        Start-Sleep -Seconds 10
    }
}
catch {
    Write-Host "Failed to get ngrok URL. Check http://127.0.0.1:4040" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    pause
}

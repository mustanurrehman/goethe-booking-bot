# Goethe Booking Bot - Windows Setup Script
# Run this in PowerShell to set up the environment

Write-Host "=== Goethe Booking Bot Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found! Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "  Make sure to check 'Add Python to PATH' during installation."
    exit 1
}

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n✗ Installation failed. Please check the errors above." -ForegroundColor Red
    exit 1
}

# Check Chrome
try {
    $chromePath = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" -ErrorAction SilentlyContinue
    if ($chromePath) {
        Write-Host "✓ Google Chrome found" -ForegroundColor Green
    } else {
        Write-Host "⚠ Google Chrome not found in registry. Please install from https://www.google.com/chrome/" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not verify Chrome installation. Make sure Chrome is installed." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the bot:"
Write-Host "  1. Edit config.csv with your students' real details"
Write-Host "  2. Run: python booking_helper.py --config config.csv"
Write-Host ""
Write-Host "Optional - Telegram notifications:"
Write-Host "  set TELEGRAM_BOT_TOKEN=your_bot_token"
Write-Host "  set TELEGRAM_CHAT_ID=your_chat_id"
Write-Host "  python booking_helper.py --config config.csv"
Write-Host ""

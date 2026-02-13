# VS Code Marketplace Preparation Script
# Fixes critical issues before publishing (Windows PowerShell version)

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "AWX MCP Extension - Marketplace Prep" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check we're in the right directory
if (-not (Test-Path "package.json")) {
    Write-Host "❌ Error: Must run from vscode-extension directory" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Found package.json" -ForegroundColor Green
Write-Host ""

# 1. Check for icon
Write-Host "📸 Checking icon..." -ForegroundColor Yellow
if (-not (Test-Path "resources\icon.png")) {
    Write-Host "⚠️  WARNING: No icon.png found!" -ForegroundColor Red
    Write-Host "   Action needed:"
    Write-Host "   1. Create a 256x256 PNG icon"
    Write-Host "   2. Save as resources\icon.png"
    Write-Host "   3. Re-run this script"
    Write-Host ""
    
    if (Test-Path "resources\awx-mcp.svg") {
        Write-Host "   Found SVG at resources\awx-mcp.svg"
        Write-Host "   You can use an online converter: https://cloudconvert.com/svg-to-png"
    }
    Write-Host ""
    
    $response = Read-Host "❓ Do you have an icon.png ready? (y/n)"
    if ($response -ne 'y') {
        Write-Host "❌ Cannot proceed without icon" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ Icon check passed" -ForegroundColor Green
Write-Host ""

# 2. Check publisher
Write-Host "👤 Checking publisher..." -ForegroundColor Yellow
$packageJson = Get-Content "package.json" -Raw | ConvertFrom-Json
$publisher = $packageJson.publisher

Write-Host "   Current publisher: $publisher"

if ($publisher -eq "awx-mcp-team") {
    Write-Host "⚠️  WARNING: Using placeholder publisher!" -ForegroundColor Red
    Write-Host "   This publisher ID doesn't exist on VS Code Marketplace"
    Write-Host ""
    Write-Host "   Action needed:"
    Write-Host "   1. Go to: https://marketplace.visualstudio.com/manage"
    Write-Host "   2. Create a publisher account"
    Write-Host "   3. Update package.json with your real publisher ID"
    Write-Host ""
    
    $response = Read-Host "❓ Have you registered a publisher? (y/n)"
    if ($response -ne 'y') {
        Write-Host "❌ Cannot publish without registered publisher" -ForegroundColor Red
        exit 1
    }
    
    $newPublisher = Read-Host "Enter your registered publisher ID"
    Write-Host "⚠️  Please manually update package.json:" -ForegroundColor Yellow
    Write-Host "   `"publisher`": `"$newPublisher`""
    Write-Host ""
}

Write-Host "✓ Publisher check passed" -ForegroundColor Green
Write-Host ""

# 3. Check repository URL
Write-Host "🔗 Checking repository URL..." -ForegroundColor Yellow
$repoUrl = $packageJson.repository.url
Write-Host "   Current URL: $repoUrl"

if ($repoUrl -like "*your-org*") {
    Write-Host "⚠️  WARNING: Using placeholder repository URL!" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Action needed:"
    Write-Host "   1. Create a GitHub repository"
    Write-Host "   2. Push your code: git push origin main"
    Write-Host "   3. Update package.json with real URLs"
    Write-Host ""
    
    $response = Read-Host "❓ Have you created a GitHub repo? (y/n)"
    if ($response -ne 'y') {
        Write-Host "⚠️  You can proceed, but it's strongly recommended to have a real repo" -ForegroundColor Yellow
    }
}

Write-Host "✓ Repository check passed" -ForegroundColor Green
Write-Host ""

# 4. Compile TypeScript
Write-Host "🔨 Compiling TypeScript..." -ForegroundColor Yellow
try {
    npm run compile
    Write-Host "✓ Compilation successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Compilation failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 5. Run linter
Write-Host "🔍 Running linter..." -ForegroundColor Yellow
try {
    npm run lint
    Write-Host "✓ Linter passed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Linter found issues (non-blocking)" -ForegroundColor Yellow
}
Write-Host ""

# 6. Check if vsce is installed
Write-Host "📦 Checking vsce..." -ForegroundColor Yellow
if (-not (Get-Command vsce -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  vsce not found, installing..." -ForegroundColor Yellow
    npm install -g @vscode/vsce
}
Write-Host "✓ vsce is available" -ForegroundColor Green
Write-Host ""

# 7. Package extension
Write-Host "📦 Packaging extension..." -ForegroundColor Yellow
try {
    vsce package
    Write-Host "✓ Package created successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Packaging failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 8. List packaged files
Write-Host "📋 Packaged files:" -ForegroundColor Yellow
vsce ls
Write-Host ""

# 9. Final summary
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "✅ MARKETPLACE PREP COMPLETE!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Test the .vsix file:"
Write-Host "   code --install-extension awx-mcp-extension-1.0.0.vsix"
Write-Host ""
Write-Host "2. If test passes, publish:"
Write-Host "   vsce login <your-publisher>"
Write-Host "   vsce publish"
Write-Host ""
Write-Host "3. Monitor marketplace:"
Write-Host "   https://marketplace.visualstudio.com/items?itemName=<publisher>.awx-mcp-extension"
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan

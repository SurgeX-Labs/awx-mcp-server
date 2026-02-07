param(
    [switch]$Clean,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "Building AWX MCP Extension" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Change to extension directory
$ExtensionDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ExtensionDir

# Clean if requested
if ($Clean) {
    Write-Host "`nCleaning build artifacts..." -ForegroundColor Yellow
    if (Test-Path "out") { Remove-Item -Recurse -Force "out" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "*.vsix") { Remove-Item -Force "*.vsix" }
    
    # Clean Python build artifacts
    $ServerPath = Join-Path $ExtensionDir "bundled\awx-mcp-server"
    if (Test-Path $ServerPath) {
        Push-Location $ServerPath
        if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
        if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
        if (Test-Path "libs") { Remove-Item -Recurse -Force "libs" }
        Get-ChildItem -Path . -Recurse -Include "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Recurse -Include "__pycache__","*.pyc","*.pyo","*.pyd" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Pop-Location
    }
    
    Write-Host "Clean complete" -ForegroundColor Green
}

# Install npm dependencies
Write-Host "`nInstalling npm dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install npm dependencies"
    exit 1
}
Write-Host "Dependencies installed" -ForegroundColor Green

# Verify bundled server exists
Write-Host "`nVerifying bundled Python server..." -ForegroundColor Yellow
$ServerPath = Join-Path $ExtensionDir "bundled"
$ServerPath = Join-Path $ServerPath "awx-mcp-server"
$PyProjectPath = Join-Path $ServerPath "pyproject.toml"

if (-not (Test-Path $PyProjectPath)) {
    Write-Error "Bundled server not found at: $ServerPath"
    Write-Host "Run the copy-server script first!" -ForegroundColor Red
    exit 1
}
Write-Host "Bundled server found" -ForegroundColor Green

# Build Python package
Write-Host "`nBuilding Python MCP server package..." -ForegroundColor Yellow

# Check if Python is available
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Error "Python not found. Please install Python 3.10 or later."
    exit 1
}

# Check Python version
$PythonVersion = & python --version 2>&1
Write-Host "Using $PythonVersion" -ForegroundColor Gray

# Install build dependencies if needed
Write-Host "Installing Python build tools..." -ForegroundColor Gray
& python -m pip install --upgrade pip build wheel setuptools --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to install build tools, but continuing..."
}

# Build the Python package
Push-Location $ServerPath
try {
    Write-Host "Building wheel package..." -ForegroundColor Gray
    & python -m build --wheel --outdir dist
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build Python package"
        Pop-Location
        exit 1
    }
    
    # Clean up build artifacts
    Write-Host "Cleaning build artifacts..." -ForegroundColor Gray
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "*.egg-info") { Remove-Item -Recurse -Force "*.egg-info" }
    
    # Remove Python cache files
    Get-ChildItem -Path . -Recurse -Include "__pycache__","*.pyc","*.pyo","*.pyd" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Host "Python package built successfully" -ForegroundColor Green
    
    # Show wheel info
    $WheelFile = Get-ChildItem -Path "dist" -Filter "*.whl" | Select-Object -First 1
    if ($WheelFile) {
        $wheelSizeMB = [math]::Round($WheelFile.Length / 1MB, 2)
        $wheelMsg = '   Wheel: {0} ({1} MB)' -f $WheelFile.Name, $wheelSizeMB
        Write-Host $wheelMsg -ForegroundColor White
    }
}
finally {
    Pop-Location
}

# Bundle Python dependencies
Write-Host "`nBundling Python dependencies..." -ForegroundColor Yellow
$LibsPath = Join-Path $ServerPath "libs"

# Create libs directory if it doesn't exist
if (-not (Test-Path $LibsPath)) {
    New-Item -ItemType Directory -Path $LibsPath | Out-Null
}

# Install dependencies to libs directory
Push-Location $ServerPath
try {
    Write-Host "Installing dependencies to libs/ directory..." -ForegroundColor Gray
    
    # Install the package and its dependencies
    & python -m pip install --target libs --upgrade .
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Failed to install dependencies, but continuing..."
    }
    
    # Clean up unnecessary files from libs
    Write-Host "Cleaning libs directory..." -ForegroundColor Gray
    Get-ChildItem -Path "libs" -Recurse -Directory -Include "__pycache__","tests","test","*.dist-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path "libs" -Recurse -File -Include "*.pyc","*.pyo","*.pyd" | Remove-Item -Force -ErrorAction SilentlyContinue
    
    $libsSizeMB = [math]::Round((Get-ChildItem -Path "libs" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
    $bundleMsg = 'Dependencies bundled successfully ({0} MB)' -f $libsSizeMB
    Write-Host $bundleMsg -ForegroundColor Green
}
catch {
    Write-Warning "Dependency bundling encountered errors: $_"
    Write-Host "Extension will rely on runtime installation" -ForegroundColor Yellow
}
finally {
    Pop-Location
}

# Compile TypeScript
Write-Host "`nCompiling TypeScript..." -ForegroundColor Yellow
npm run compile
if ($LASTEXITCODE -ne 0) {
    Write-Error "TypeScript compilation failed"
    exit 1
}
Write-Host "TypeScript compiled" -ForegroundColor Green

# Run linter
Write-Host "`nRunning ESLint..." -ForegroundColor Yellow
npm run lint
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Linting found issues - continuing anyway"
} else {
    Write-Host "Linting passed" -ForegroundColor Green
}

# Run tests
if (-not $SkipTests) {
    Write-Host "`nRunning tests..." -ForegroundColor Yellow
    Write-Host "Tests skipped - not implemented yet" -ForegroundColor Gray
}

# Create dist directory
if (-not (Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

# Validate bundled content
Write-Host "`nValidating bundled content..." -ForegroundColor Yellow
$ServerPath = Join-Path $ExtensionDir "bundled\awx-mcp-server"

$ValidationItems = @(
    @{Path = Join-Path $ServerPath "src\awx_mcp_server"; Name = "MCP Server source"; Required = $true},
    @{Path = Join-Path $ServerPath "dist"; Name = "Python wheel"; Required = $false},
    @{Path = Join-Path $ServerPath "libs"; Name = "Bundled dependencies"; Required = $false},
    @{Path = Join-Path $ServerPath "pyproject.toml"; Name = "Package metadata"; Required = $true}
)

$ValidationPassed = $true
foreach ($item in $ValidationItems) {
    if (Test-Path $item.Path) {
        Write-Host "   [OK] $($item.Name)" -ForegroundColor Green
    } else {
        if ($item.Required) {
            Write-Host "   [ERROR] $($item.Name) (MISSING - REQUIRED)" -ForegroundColor Red
            $ValidationPassed = $false
        } else {
            Write-Host "   [WARN] $($item.Name) (not found - optional)" -ForegroundColor Yellow
        }
    }
}

if (-not $ValidationPassed) {
    Write-Error "Validation failed - required files are missing"
    exit 1
}

Write-Host "Validation passed" -ForegroundColor Green

# Package extension
Write-Host "`nPackaging extension..." -ForegroundColor Yellow
npm run package
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to package extension"
    exit 1
}
Write-Host "Extension packaged" -ForegroundColor Green

# Show results
Write-Host "`nBuild complete!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan

$VsixFiles = Get-ChildItem -Path "dist" -Filter "*.vsix"
if ($VsixFiles) {
    Write-Host "`nPackage created:" -ForegroundColor Cyan
    foreach ($file in $VsixFiles) {
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-Host "   Name: $($file.Name)" -ForegroundColor White
        $sizeMsg = '   Size: {0} MB' -f $sizeMB
        Write-Host $sizeMsg -ForegroundColor White
        Write-Host "   Path: $($file.FullName)" -ForegroundColor Gray
    }
    
    # Show bundled content summary
    Write-Host "`nBundled content:" -ForegroundColor Cyan
    $ServerPath = Join-Path $ExtensionDir "bundled\awx-mcp-server"
    
    $WheelFile = Get-ChildItem -Path "$ServerPath\dist" -Filter "*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($WheelFile) {
        Write-Host "   Python wheel: $($WheelFile.Name)" -ForegroundColor White
    }
    
    if (Test-Path "$ServerPath\libs") {
        $libsCount = (Get-ChildItem -Path "$ServerPath\libs" -Recurse -File).Count
        $libsSizeMB = [math]::Round((Get-ChildItem -Path "$ServerPath\libs" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
        $depsMsg = '   Dependencies: {0} files ({1} MB)' -f $libsCount, $libsSizeMB
        Write-Host $depsMsg -ForegroundColor White
    }
    
    $srcFiles = (Get-ChildItem -Path "$ServerPath\src" -Recurse -File -Include "*.py").Count
    Write-Host "   Source files: $srcFiles Python files" -ForegroundColor White
    
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    $firstFile = $VsixFiles[0].Name
    Write-Host "   1. Test locally: code --install-extension dist\$firstFile" -ForegroundColor White
    Write-Host "   2. Publish to marketplace: npm run publish" -ForegroundColor White
    Write-Host "   3. Or upload manually to: https://marketplace.visualstudio.com/manage" -ForegroundColor White
} else {
    Write-Warning "No VSIX file found in dist directory"
}

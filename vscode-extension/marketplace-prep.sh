#!/bin/bash

# VS Code Marketplace Preparation Script
# Fixes critical issues before publishing

set -e

echo "===================================="
echo "AWX MCP Extension - Marketplace Prep"
echo "===================================="
echo ""

# Check we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Must run from vscode-extension directory"
    exit 1
fi

echo "✓ Found package.json"
echo ""

# 1. Check for icon
echo "📸 Checking icon..."
if [ ! -f "resources/icon.png" ]; then
    echo "⚠️  WARNING: No icon.png found!"
    echo "   Action needed:"
    echo "   1. Create a 256x256 PNG icon"
    echo "   2. Save as resources/icon.png"
    echo "   3. Re-run this script"
    echo ""
    if [ -f "resources/awx-mcp.svg" ]; then
        echo "   Found SVG at resources/awx-mcp.svg"
        echo "   Convert with: convert resources/awx-mcp.svg -resize 256x256 resources/icon.png"
    fi
    echo ""
    read -p "❓ Do you have an icon.png ready? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cannot proceed without icon"
        exit 1
    fi
fi

echo "✓ Icon check passed"
echo ""

# 2. Check publisher
echo "👤 Checking publisher..."
PUBLISHER=$(grep -o '"publisher": *"[^"]*"' package.json | cut -d'"' -f4)
echo "   Current publisher: $PUBLISHER"

if [ "$PUBLISHER" == "awx-mcp-team" ]; then
    echo "⚠️  WARNING: Using placeholder publisher!"
    echo "   This publisher ID doesn't exist on VS Code Marketplace"
    echo ""
    echo "   Action needed:"
    echo "   1. Go to: https://marketplace.visualstudio.com/manage"
    echo "   2. Create a publisher account"
    echo "   3. Update package.json with your real publisher ID"
    echo ""
    read -p "❓ Have you registered a publisher? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cannot publish without registered publisher"
        exit 1
    fi
    
    read -p "Enter your registered publisher ID: " NEW_PUBLISHER
    # Update package.json (requires jq or manual edit)
    echo "⚠️  Please manually update package.json:"
    echo '   "publisher": "'$NEW_PUBLISHER'"'
    echo ""
fi

echo "✓ Publisher check passed"
echo ""

# 3. Check repository URL
echo "🔗 Checking repository URL..."
REPO_URL=$(grep -o '"url": *"https://github.com/[^"]*"' package.json | head -1 | cut -d'"' -f4)
echo "   Current URL: $REPO_URL"

if [[ "$REPO_URL" == *"your-org"* ]]; then
    echo "⚠️  WARNING: Using placeholder repository URL!"
    echo ""
    echo "   Action needed:"
    echo "   1. Create a GitHub repository"
    echo "   2. Push your code: git push origin main"
    echo "   3. Update package.json with real URLs"
    echo ""
    read -p "❓ Have you created a GitHub repo? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "⚠️  You can proceed, but it's strongly recommended to have a real repo"
    fi
fi

echo "✓ Repository check passed"
echo ""

# 4. Compile TypeScript
echo "🔨 Compiling TypeScript..."
if ! npm run compile; then
    echo "❌ Compilation failed"
    exit 1
fi
echo "✓ Compilation successful"
echo ""

# 5. Run linter
echo "🔍 Running linter..."
if ! npm run lint; then
    echo "⚠️  Linter found issues (non-blocking)"
else
    echo "✓ Linter passed"
fi
echo ""

# 6. Check if vsce is installed
echo "📦 Checking vsce..."
if ! command -v vsce &> /dev/null; then
    echo "⚠️  vsce not found, installing..."
    npm install -g @vscode/vsce
fi
echo "✓ vsce is available"
echo ""

# 7. Package extension
echo "📦 Packaging extension..."
if ! vsce package; then
    echo "❌ Packaging failed"
    exit 1
fi
echo "✓ Package created successfully"
echo ""

# 8. List packaged files
echo "📋 Packaged files:"
vsce ls
echo ""

# 9. Final summary
echo "===================================="
echo "✅ MARKETPLACE PREP COMPLETE!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Test the .vsix file:"
echo "   code --install-extension awx-mcp-extension-*.vsix"
echo ""
echo "2. If test passes, publish:"
echo "   vsce login <your-publisher>"
echo "   vsce publish"
echo ""
echo "3. Monitor marketplace:"
echo "   https://marketplace.visualstudio.com/items?itemName=<publisher>.awx-mcp-extension"
echo ""
echo "===================================="

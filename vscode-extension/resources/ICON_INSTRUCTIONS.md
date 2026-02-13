# Icon Creation Instructions

## You Need a 256x256 PNG Icon

The VS Code Marketplace **requires** a square PNG icon. Your extension currently has:
- ✅ `resources/awx-mcp.svg` (vector file)
- ✅ `resources/images.png` (but might not be the right size)

## Quick Fix Options

### Option 1: Convert Your SVG (Recommended)

**Online Converter (Easiest):**
1. Go to https://cloudconvert.com/svg-to-png
2. Upload `resources/awx-mcp.svg`
3. Set dimensions to 256x256 pixels
4. Download and save as `resources/icon.png`

**Using ImageMagick (if installed):**
```bash
convert resources/awx-mcp.svg -resize 256x256 resources/icon.png
```

**Using Inkscape (if installed):**
```bash
inkscape resources/awx-mcp.svg --export-type=png --export-width=256 --export-height=256 --export-filename=resources/icon.png
```

### Option 2: Use Free Icon Tools

**Canva (Free):**
1. Go to https://www.canva.com
2. Create 256x256 design
3. Use AWX/Ansible branding colors (red #EE0000)
4. Add text/shapes to represent AWX + AI
5. Download as PNG to `resources/icon.png`

**Figma (Free):**
1. Go to https://www.figma.com
2. Create 256x256 frame
3. Design icon
4. Export as PNG to `resources/icon.png`

### Option 3: Use Existing Image

If you have `resources/images.png`, check if it's square and at least 128x128:

**Check dimensions (PowerShell):**
```powershell
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("resources/images.png")
Write-Host "Width: $($img.Width), Height: $($img.Height)"
$img.Dispose()
```

If it's square and >= 128x128, you can use it:
```powershell
Copy-Item resources/images.png resources/icon.png
```

## Icon Design Tips

**Do:**
- ✅ Use square dimensions (256x256 recommended, 128x128 minimum)
- ✅ Simple, recognizable design
- ✅ High contrast for visibility
- ✅ Use brand colors (AWX red #EE0000)
- ✅ PNG format with transparency

**Don't:**
- ❌ Use rectangular dimensions
- ❌ Make it too detailed (hard to see when small)
- ❌ Use text (illegible at small sizes)
- ❌ Use low resolution (<128x128)

## Design Ideas for AWX MCP Icon

Combine these elements:
- 🤖 Robot/AI symbol (for MCP/Copilot)
- ⚙️ Gear/automation symbol (for Ansible)
- 📡 Network/connection symbol (for AWX)
- 🔴 AWX red color (#EE0000)
- 🔵 VS Code blue accent (#007ACC)

## After Creating Icon

1. Save as `resources/icon.png`
2. Verify it's added to package.json:
   ```json
   "icon": "resources/icon.png"
   ```
3. Run marketplace prep script:
   ```powershell
   .\marketplace-prep.ps1
   ```

## Placeholder Icon (Temporary)

If you need to test packaging without a real icon, create a simple colored square:

**PowerShell:**
```powershell
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap(256, 256)
$graphics = [System.Drawing.Graphics]::FromImage($bmp)
$brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(238, 0, 0))
$graphics.FillRectangle($brush, 0, 0, 256, 256)
$bmp.Save("resources\icon.png", [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bmp.Dispose()
```

**But use a real icon before publishing!**

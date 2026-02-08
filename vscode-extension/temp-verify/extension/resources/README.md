# AWX MCP Extension Resources

This directory contains resources for the VS Code extension.

## Required Files

### Icon (`icon.png`)
- **Size**: 128x128 pixels
- **Format**: PNG
- **Purpose**: Extension icon shown in marketplace and VS Code
- **Design**: Should represent AWX/Ansible branding

### Banner (configured in package.json)
- **Color**: Specified in package.json `galleryBanner.color`
- **Theme**: `dark` or `light`
- **Purpose**: Background banner in marketplace

### AWX Icon (`awx-icon.svg`)
- **Format**: SVG
- **Purpose**: Activity bar icon
- **Usage**: Referenced in package.json views

## Creating Icons

### Using Online Tools
1. [Figma](https://figma.com) - Design tool
2. [Canva](https://canva.com) - Template-based design
3. [GIMP](https://gimp.org) - Free image editor

### Icon Guidelines
- Use AWX/Ansible brand colors
- Simple, recognizable design
- Works at small sizes (16x16)
- Use PNG for bitmap, SVG for scalable

### Example SVG Icon

Create `awx-icon.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect width="128" height="128" fill="#EE0000"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" 
        font-family="Arial, sans-serif" font-size="60" font-weight="bold" fill="white">
    AWX
  </text>
</svg>
```

## Temporary Placeholder

If you don't have icons ready, you can temporarily:

1. Use a simple colored square
2. Add text overlay with "AWX"
3. Publish without icon (not recommended for marketplace)

## Notes

- Icons are required for marketplace publishing
- Banner color should match your branding
- SVG is preferred for scalability
- Test icons at different sizes

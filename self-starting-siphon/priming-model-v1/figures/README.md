# Figures Directory

This folder contains diagrams for the siphon model.

## Files

### Original Image
- **siphon_diagram.png** (1.4 MB) - Original Gemini-generated diagram showing the siphon setup with labeled points A, B, C, D, E

### Professional SVG Alternatives

1. **siphon_schematic.svg** (3.5 KB)
   - Clean, minimalist schematic
   - Shows basic geometry with labeled points
   - Includes water level and flow direction
   - Good for presentations

2. **siphon_detailed.svg** (6.2 KB)
   - Comprehensive annotated diagram
   - All geometric parameters labeled (L₁, L₂, L₃, L₄, A, A₀, D, h_c(t))
   - Coordinate labels for all points
   - Professional styling suitable for publications
   - Includes title and complete annotations

## Usage in LaTeX

The document currently uses `siphon_diagram.png`. To use SVG versions:

1. Convert SVG to PDF:
   ```bash
   inkscape --export-filename=siphon_detailed.pdf siphon_detailed.svg
   ```

2. Update LaTeX to use PDF:
   ```latex
   \includegraphics[width=0.7\textwidth]{figures/siphon_detailed.pdf}
   ```

## Customization

The SVG files can be edited with:
- Inkscape (recommended, free)
- Adobe Illustrator
- Any text editor (they're XML-based)

To modify colors, dimensions, or labels, open the SVG file in a text editor and adjust the relevant parameters.

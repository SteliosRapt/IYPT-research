# IYPT_4 - Self-starting Siphon Priming Model

Physics/mathematics document for IYPT on self-starting siphon dynamics.

## Current Documents

- **math_1_v2.tex** - Latest LaTeX source file
- **math_1_v2.pdf** - Latest compiled PDF (11 pages)

## Folder Structure

```
IYPT_4/
├── math_1_v2.tex              # Main LaTeX source
├── math_1_v2.pdf              # Main PDF output
├── build/                     # LaTeX auxiliary files (.aux, .log, .out)
├── bibliography_data/         # Citation metadata (JSON files from CrossRef)
├── web_searches/              # Research HTML files
├── older_document_versions/   # Previous versions (math_1.tex/pdf)
└── scripts/                   # Utility scripts (convert_to_pdf.py)
```

## Compiling

To compile the document:
```bash
pdflatex math_1_v2.tex
pdflatex math_1_v2.tex  # Run twice for cross-references
```

Or using the full path on Windows:
```bash
"C:\Users\user\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe" math_1_v2.tex
```

## Content Summary

The document presents a mathematical model for self-starting siphon priming with:
- Geometry and lossless equations of motion
- Darcy-Weisbach distributed friction losses
- Local (minor) losses at fittings
- Phase-split dynamics (filling vs draining phases)
- Nondimensionalization and key parameters

## References

Includes citations to:
- Classical fluid mechanics (White, Colebrook, Moody, Crane)
- Siphon-specific research (Potter, Jumper, Zheng, Ortloff, Sedlar)
- Numerical methods (Hairer et al.)

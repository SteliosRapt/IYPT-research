# Flipo Flips

Interactive web-based simulation and visualization tool for studying the physics of the "Flipo flip" toy — a rectangular prism with Steinmetz bicylinder spherical caps. Built for **IYPT 2026, Problem #6**.

## What Is It?

The toy consists of a rectangular prism (width `w`, height `h`) with two spherical cap patches cut from a Steinmetz bicylinder (radius `R`) attached to the top and bottom faces. This creates a shape that rolls on a flat surface in complex, non-circular patterns through a 6-phase motion cycle combining pure rolling and edge pivoting.

## Features

- **4 synchronized viewports**: 3D toy geometry, Steinmetz intersection, 2D phase canvas, and animated 3D rolling on a ground plane
- **Adjustable parameters**: Radius (R), Width (w), Height (h), mesh detail
- **6-phase rolling cycle simulation** with play/pause, speed control (0.1–4x), manual phase slider, and loop mode
- **STL export** for 3D printing
- **Research figure generation** via Python (matplotlib + Playwright)
- **LaTeX paper** with full theoretical treatment

## Project Structure

```
├── flipo_flip_simulation.html   # Main web application
├── start_https_server.py        # Python dev server
├── generate_figures.py          # Figure generation for the paper
├── flipo flip theory.tex/pdf    # LaTeX research paper
├── js/                          # Modular JS simulation code
│   ├── simulation-app.js        # Main orchestrator
│   ├── flipo-model.js           # Core geometry model
│   ├── phases-cycle.js          # Motion phase state machine
│   ├── steinmetz.js             # Steinmetz bicylinder geometry
│   ├── toy-builder.js           # 3D mesh construction
│   └── ...                      # Rendering, helpers, utilities
├── figures/                     # Generated figures for paper
└── archives/                    # Previous versions
```

## Running

### Web Application

```bash
py start_https_server.py
```

Opens at `http://localhost:8000/`. Navigate to `flipo_flip_simulation.html`.

Optional flags: `--host 0.0.0.0 --port 8080 --dir .`

Alternatively, open `flipo_flip_simulation.html` directly in a modern browser (requires ES6 modules and import maps support).

### Figure Generation

```bash
pip install numpy matplotlib playwright
playwright install chromium
py generate_figures.py
```

## Technologies

- **Three.js** (v0.160.1) — 3D rendering, OrbitControls, STL export
- **HTML5 Canvas** — 2D phase visualization
- **Python** — Dev server (`http.server`), figure generation (`numpy`, `matplotlib`, `playwright`)
- **LaTeX** — Research paper

## Default Parameters

| Parameter | Default |
|-----------|---------|
| R (bicylinder radius) | 18 cm |
| w (square width) | 13 cm |
| h (prism height) | 1 cm |
| Mesh detail | 1.8 |
| Playback speed | 1.0x |
| Cycle duration | 8 s |

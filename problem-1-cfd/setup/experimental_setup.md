# Experimental Setup — Detailed Configuration

## 1. Overview

The setup consists of a **rectangular container** (open-top box) that extends from the left wall (x = S₀) to the x-coordinate of point P₂ (x = X₂), with a **hollow glass tube** (pipe for water flow) routed in a zig-zag path. The tube **starts at P₁ and ends at P₅**, passing through peaks and valleys with **rounded bends** at P₂, P₃, and P₄ (each bend passes exactly through the labelled point). The tube is supported by **holders** at intermediate positions (but not at the tube endpoints P₁, P₅, or at P₂ which is fixed to the container wall). The highest peak (P₄) is supported by a column structure with two vertical prisms at the **edges of the container width**, connected to the container by beams at h₀ and floor level. The entire configuration is **symmetric about its centre plane** (perpendicular to the container width).

The coordinate system has:
- **x-axis**: horizontal, running left-to-right
- **y-axis**: vertical, running bottom-to-top
- **Origin O**: on the bottom edge, at the x-position of point P₁

---

## 2. Key Points

| Point | Coordinates | Role |
|-------|------------|------|
| **W₀** | (S₀, h₀) | Top-left corner of the container (reference only — tube does NOT pass here) |
| **P₁** | (0, h₁) | **Tube start**. Located \|S₀\| to the right of the left container wall. No holder here. |
| **W₁** | (S₁, C₁) | First tube holder centre (on the straight segment P₁→P₂) |
| **P₂** | (X₂, h₂) | First peak — **rounded bend**. Fixed to container wall (no holder needed). Also the x-coordinate where the container ends. |
| **P₃** | (X₃, h₃) | Valley — **rounded bend** |
| **P₄** | (X₄, h₄) | Highest peak — **rounded bend**, supported by column structure |
| **W₂** | (S₂, C₂) | Second tube holder centre (on the straight segment P₄→P₅) |
| **P₅** | (X₅, h₅) | **Tube end**. No holder here. |

**Tube path**: P₁ → (W₁) → P₂ → P₃ → P₄ → (W₂) → P₅

- The tube does **not** connect to W₀. W₀ is only a container reference point.
- W₁ and W₂ are **reference positions** — the centres of tube holders along the straight segments (not separate deflection points).
- **No holders at P₁, P₂, or P₅** — P₁ and P₅ are open tube endpoints; P₂ is fixed to the container wall.

---

## 3. Free Parameters

### Primary geometric parameters (vary between simulations):

| Parameter | Meaning |
|-----------|---------|
| A₀ | Container area (footprint, used to derive S₀) |
| h₀ | Container height (to the main horizontal level) |
| h₁ | Height of point P₁ (tube start) |
| h₃ | Height of point P₃ (valley) |
| h₅ | Height of point P₅ (tube end) |
| W₁ | Horizontal position of first holder centre (= S₁) |
| W₂ | Used to derive S₂ via S₂ = X₅ − W₂ |
| Y₂ | Vertical drop from h₀ to P₂ (h₂ = h₀ − Y₂) |
| Y₄ | Vertical rise from h₀ to P₄ (h₄ = h₀ + Y₄) |
| L₁ | Tube centreline length from P₁ to P₂ |
| L₂ | Tube centreline length from P₂ to P₃ |
| L₃ | Tube centreline length from P₃ to P₄ |
| L₄ | Tube centreline length from P₄ to P₅ |
| A | Tube cross-sectional area (hollow pipe) |
| W | Container width (depth, into the page) |

### Structural parameters (likely constant across simulations):

| Parameter | Meaning |
|-----------|---------|
| α | Triangle base length (equal for all holders) |
| Ct | Container wall thickness |
| ht | Tube holder thickness |
| P4t | P₄ column thickness/width (= α) |
| P24t | Sideways connecting beam width (connecting container wall at X₂ with P₄ column) |
| hw | Tube holders' width |
| h_a | Excess height of container walls above h₀ |

All thickness/width parameters extend **from the centre in both directions**, so the total extent equals the parameter value (half on each side).

---

## 4. Calculated (Derived) Parameters

| Parameter | Formula | Description |
|-----------|---------|-------------|
| S₀ | $S_0 = X_2 - \frac{A_0}{W}$ | x-position of container's left wall (S₀ < 0) |
| S₁ | $S_1 = W_1$ | x-position of first holder centre |
| h₂ | $h_2 = h_0 - Y_2$ | Height of P₂ |
| h₄ | $h_4 = h_0 + Y_4$ | Height of P₄ |
| X₂ | $X_2 = \sqrt{L_1^2 - (h_2 - h_1)^2}$ | x-position of P₂ (also container right wall) |
| X₃ | $X_3 = \sqrt{L_2^2 - (h_3 - h_2)^2} + X_2$ | x-position of P₃ |
| X₄ | $X_4 = \sqrt{L_3^2 - (h_4 - h_3)^2} + X_3$ | x-position of P₄ |
| X₅ | $X_5 = \sqrt{L_4^2 - (h_5 - h_4)^2} + X_4$ | x-position of P₅ |
| C₁ | $C_1 = \frac{h_2 - h_1}{X_2} \cdot S_1 + h_1$ | Height of W₁ (interpolated on P₁→P₂) |
| C₂ | $C_2 = \frac{h_5 - h_4}{X_5 - X_4} \cdot (S_2 - X_4) + h_4$ | Height of W₂ (interpolated on P₄→P₅) |
| S₂ | $S_2 = X_5 - W_2$ | x-position of second holder centre |

---

## 5. Constraints

### 5.1 Sign & Positivity
- $S_0 < 0$ (the container's left wall is to the left of the origin)
- All other parameters are strictly positive (> 0)

### 5.2 Ordering (horizontal positions)
$$
S_0 < 0 < S_1 < X_2 < X_3 < X_4 < S_2 < X_5
$$

### 5.3 Height constraints
- $h_1, h_2, h_3, h_5 < h_0$ (all tube points are below container height)
- $h_1, h_3 < h_2$ (valleys are below the first peak)
- $h_2 < h_4$ (P₄ is the highest peak)

### 5.4 Clearance constraints

| Constraint | Formula | Meaning |
|------------|---------|---------|
| Left wall clearance | $\|S_0\| \geq \sqrt{\frac{A}{\pi}} + \frac{C_t}{2}$ | Tube radius + half wall thickness must fit |
| S₁ clearance | $S_1 \geq \sqrt{\frac{A}{\pi}} + \frac{\alpha}{2}$ | First holder must clear tube radius at P₁ |
| X₂ vs S₁ | $X_2 \geq S_1 + \frac{\alpha}{2} + \frac{C_t}{2}$ | P₂ must clear holder + container wall |
| X₃ vs X₂ | $X_3 \geq X_2 + \frac{\alpha}{2} + \frac{C_t}{2}$ | P₃ must clear container wall at X₂ |
| X₄ vs X₃ | $X_4 \geq X_3 + \alpha$ | P₄ must clear P₃ by a full triangle base |
| S₂ vs X₄ | $S_2 \geq X_4 + \alpha + \sqrt{\frac{A}{\pi}}$ | Second holder must clear P₄ column + tube radius |
| X₅ vs S₂ | $X_5 \geq \frac{\alpha}{2} + S_2$ | P₅ must clear second holder |

### 5.5 Structural constraints
- $\alpha \geq C_t$
- $\alpha \geq \frac{5}{2}\sqrt{\frac{A}{\pi}}$ (triangle base must be large enough relative to tube radius)
- $P_{4t} = \alpha$
- $P_{24t} \leq \alpha$
- All "other areas" have thickness $C_t$ and width $\alpha$
- The **rightmost structure ends exactly at X₅**

### 5.6 Square root reality constraints
- $L_1^2 \geq (h_2 - h_1)^2$
- $L_2^2 \geq (h_3 - h_2)^2$
- $L_3^2 \geq (h_4 - h_3)^2$
- $L_4^2 \geq (h_5 - h_4)^2$

---

## 6. Structural Details

### 6.1 Container
- Rectangular box from **x = S₀** to **x = X₂** (stops at P₂)
- Width **W** (into the page), height **h₀ + h_a**
- **Open top** — no lid on the container
- Wall thickness: **Ct** (uniform)
- The excess height **h_a** is added only to the container walls above h₀
- The **right wall** (at x = X₂) has a circular hole of radius $r = \sqrt{A/\pi}$ at height h₂ where the tube passes through to the external structure

### 6.2 Tube (Hollow Glass Pipe)
- Cross-sectional area **A**, outer radius $r = \sqrt{A/\pi}$
- **Hollow glass tube** — the interior is empty, water flows through it
- The tube passes through the container's right wall via a circular opening
- Runs along the **centre plane** of the setup
- **Starts at P₁**, ends at P₅
- Straight-line segments: P₁ → P₂ → P₃ → P₄ → P₅
- **Rounded bends** at P₂, P₃, and P₄: smooth curves where the midpoint of each bend passes exactly through the labelled point's coordinates. The cross-sectional area remains constant **A** throughout bends — no leaks, no cross-section distortion.

### 6.3 Triangular Tube Holders
- Ground-level holders at: **W₁, P₃, W₂** — base at y = 0
- **P₄ holder** sits on the column platform — base at y = h₀
- **No holders at P₁, P₂, or P₅**: P₁ and P₅ are tube endpoints; P₂ is fixed to the container wall

Each holder consists of two components:
1. **Two triangular supports** at the edges of the holder width (z = ±hw/2), each with base **α** and height **α**, thickness **ht**
2. **A vertical plate** in the yz-plane (centred at the holder's x-position), spanning the full holder width **hw** in z, rising from the base to the **height of the relevant point**. The plate has a small thickness (Ct in x-direction).

The full volume of the tube (outer radius $r = \sqrt{A/\pi}$) is **subtracted** from all holder components — any material inside the tube cylinder is removed, so the tube passes cleanly through the plate and any triangular support geometry it intersects.

### 6.4 P₄ Column & Support Structure
- **P₄ Platform**: at height **h₀**, width **α** (x-direction), thickness **Ct** (y-direction), spans full container width **W** (z-direction)
- **Two columns**: starting from the **edges of the container width** (at z = ±W/2), extending **inward** by length **α** (z-direction). Each column has width **α** (x-direction) and height **h₀**. They perfectly align with the platform.
- **Two connecting beams at h₀ level**: run from the container right wall (X₂) to the P₄ columns. Width **α** (z-direction), same thickness as the platform (**Ct**). Positioned at the same z-locations as the columns. Do not extend above h₀.
- **Floor-level mirror**: identical structure at **y = 0** — a floor platform (α × Ct × W) at X₄, and two floor-level beams from X₂ to X₄ at the same z-positions as the columns.
- **Centre rail**: a horizontal beam from **X₂ to X₅** at floor level (y = 0), running through the centre (z = 0), width **α**, thickness **Ct**. Holds the P₃ and W₂ holders in place.

### 6.5 Symmetry
- Symmetric about centre plane (plane of the tube path)
- Tube is exactly at the centre of the 3D object

---
name: pixel-art
description: Hand-authored game pixel art via deterministic build scripts, hard pixel edges, limited hue-shifted palettes, selective outlines, and a see-critique-fix loop. Use for sprites, items, tiles, icons, and atlas tiles.
---

# Pixel Art

Every pixel is placed on purpose. Work at true resolution, then scale only for preview/export.

## Loop

1. **Brief**: canvas size, palette budget, light direction, outline rule, where it is seen.
2. **Build script**: deterministic Python/Pillow (or digit grids) that regenerates every tile.
3. **Render preview** at an integer scale, look at it.
4. **Critique** against:
   - silhouette readable at 1x
   - one light direction, consistent 3-tone ramps (shadow cooler, highlight warmer)
   - no pillow shading, no banding, no orphan pixels
   - clean outline with no doubles/jaggies
   - few colors, clustered detail, no noise
5. **Fix** the build script and repeat, minimum two passes.

## Rules

- 1x source, integer nearest-neighbor scaling only.
- Palette: 4-8 colors per material; hue-shift ramps, not just darker/lighter.
- Temporary canvas: 16x16 icons, 32x32 items, 32-64 sprites.
- Outline: either all edges or none; dark tinted outline, not pure black.
- Light from top-left; highlights on light-facing edges, shadow on the opposite.
- Tools face diagonally; handle and head must read as separate shapes.
- Keep 1px margins so outlines never clip.

## Deliver

Master PNG at 1x, preview at 4-8x, and the build script as source of truth.

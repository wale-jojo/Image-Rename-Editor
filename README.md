# Image Rename Editor

A Tkinter-based image rename tool with thumbnail selection, drag-to-reorder, and flexible renaming rules.

## Requirements

- Python 3.10+
- Optional (recommended): Pillow for JPG/WEBP/TIFF thumbnails

Install Pillow:

```
pip install pillow
```

## Run

From the folder containing the script:

```
python rename_gui.py
```

## Basic Workflow

1. Click **Browse** and choose a folder.
2. Click **Load** to scan images (filtered by Extensions).
3. Select images (click, Ctrl+click, Shift+click, or drag a selection box).
4. Choose a **Rule** and configure its inputs.
5. Check **Rename selected only** if you want to rename only the selected images.
6. Review the **Preview new names** list.
7. Click **Rename** to apply.

## Renaming Rules

- **Pattern**: Use tokens like `{index}`, `{index0}`, `{stem}`, `{ext}`. Example: `image_{index:03d}`
- **Prefix + Original**: Adds Prefix before the current name (without extension).
- **Original + Suffix**: Adds Suffix after the current name (without extension).
- **Replace text**: Replaces text inside the current name (without extension).
- **Index only**: Uses the **Index format** field (e.g. `{index:03d}`).

If **Keep original extension** is checked, the extension is preserved unless `{ext}` is included in the pattern.

## Selection and Reorder Shortcuts

- **Single select**: Left click on a thumbnail.
- **Multi-select**: Ctrl + click.
- **Range select**: Shift + click.
- **Box select**: Drag a rectangle on empty space in the thumbnail area to select all thumbnails inside.
  - Hold **Ctrl** while box-selecting to add to the current selection.
- **Reorder**: Drag any selected thumbnail to reorder. If multiple are selected, they move together.

## Notes

- Without Pillow, thumbnails work for PNG/GIF/BMP. JPG/WEBP/TIFF previews require Pillow.
- The preview list shows the new names before you rename.
- Duplicate target names are blocked.

## Files

- `rename_gui.py` - main application
- `README.md` - usage guide

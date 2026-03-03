# Image Rename Editor

A comprehensive Tkinter-based image rename tool with advanced selection, drag-to-reorder, and flexible renaming rules.

![Image Rename Editor Screenshot](Python%203.12%202026_3_2%2014_02_29.png)

## Version Information

**Version:** 2.0.0  
**Release Date:** March 3, 2026  
**Code Size:** 852+ lines  
**Python Version:** 3.10+

### Feature Summary
- ✅ **Visual Thumbnail Browser** - Windows-style grid layout with image previews
- ✅ **Advanced Selection** - Single, multi-select (Ctrl), range (Shift), rubber band drag selection
- ✅ **Drag & Drop Reordering** - Visual drag-to-reorder with insertion line preview
- ✅ **Flexible Renaming Rules** - Pattern templates, prefix/suffix, text replacement, index-only
- ✅ **Selective Renaming** - Choose which files to rename with visual preview indicators
- ✅ **Cut/Paste Operations** - Right-click context menu with batch position insertion
- ✅ **Toolbar Actions** - Quick buttons for selection and move operations
- ✅ **Multi-Format Support** - JPG, PNG, GIF, BMP, WEBP, TIFF (with optional Pillow)
- ✅ **Smart Collision Detection** - Prevents duplicate names and file conflicts
- ✅ **Live Preview** - Real-time preview of new names before applying changes

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

- `rename_gui.py` - Main application (852 lines)
- `README.md` - Usage guide and documentation

## Technical Details

- **GUI Framework:** Tkinter with ttk widgets for modern appearance
- **Image Processing:** PIL/Pillow (optional) for enhanced thumbnail support
- **File Operations:** pathlib for cross-platform file handling
- **Key Components:**
  - Canvas-based scrollable thumbnail grid
  - Drag & drop system with modifier key detection
  - Rubber band selection with coordinate transformation
  - Multi-threaded safe file operations with collision detection
  - Pattern-based renaming engine with template substitution

## Version History

### v2.0.0 (March 3, 2026)
- Added selective renaming with visual indicators ([RENAME]/[SKIP] prefixes)
- Enhanced preview system showing all files with rename status
- Improved confirmation dialogs with skip count information
- Fixed toolbar button spacing and alignment issues
- Comprehensive code review and bug fixes

### v1.5.0 (Previous)
- Implemented rubber band selection (drag to select multiple files)
- Added cut/paste operations with right-click context menus
- Enhanced drag preview with insertion line indicators
- Added toolbar buttons for quick move operations
- Improved multi-column grid layout for better file organization

### v1.0.0 (Initial)
- Basic thumbnail browser with file loading
- Core renaming functionality with multiple rule types
- Single and multi-select capabilities
- Drag and drop reordering
- Pattern-based renaming with template support

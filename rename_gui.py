import math
import tkinter as tk
import uuid
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Version information
__version__ = "2.0.0"
__date__ = "2026-03-03"
__author__ = "Image Rename Editor"

# Import modifier key constants
try:
	from tkinter.constants import CONTROL_MASK, SHIFT_MASK
except ImportError:
	# Fallback values if constants not available
	CONTROL_MASK = 0x04
	SHIFT_MASK = 0x01

try:
	from PIL import Image, ImageTk
except ImportError:  # pragma: no cover - optional dependency
	Image = None
	ImageTk = None


@dataclass
class RenameItem:
	path: Path
	new_name: str = ""


class ImageRenameApp(tk.Tk):
	def __init__(self) -> None:
		super().__init__()
		self.title(f"Image Rename Editor v{__version__}")
		self.geometry("980x640")
		self.minsize(860, 520)

		self.folder_var = tk.StringVar()
		self.ext_var = tk.StringVar(value="jpg,jpeg,png,gif,bmp,webp,tif,tiff")
		self.pattern_var = tk.StringVar(value="image_{index:03d}")
		self.start_index_var = tk.IntVar(value=1)
		self.keep_ext_var = tk.BooleanVar(value=True)
		self.rename_selected_var = tk.BooleanVar(value=False)

		self.rule_var = tk.StringVar(value="Pattern")
		self.prefix_var = tk.StringVar(value="")
		self.suffix_var = tk.StringVar(value="")
		self.find_var = tk.StringVar(value="")
		self.replace_var = tk.StringVar(value="")
		self.index_format_var = tk.StringVar(value="{index:03d}")

		self.items: list[RenameItem] = []
		self.original_items: list[RenameItem] = []
		self.selected_indices: set[int] = set()
		self._last_selected_index: int | None = None
		self._item_widgets: list[tk.Frame] = []
		self._thumb_images: list[tk.PhotoImage] = []
		self.thumb_size = 128
		self._columns = 1
		self._cell_width = self.thumb_size + 40
		self._cell_height = self.thumb_size + 60

		self._drag_index: int | None = None
		self._drag_start: tuple[int, int] | None = None
		self._drag_target_index: int | None = None
		self._dragging = False
		self._rubberband_start: tuple[int, int] | None = None
		self._rubberband_rect: int | None = None
		self._rubberband_additive = False
		self._insertion_line: int | None = None
		self._clipboard_indices: set[int] = set()

		self._build_ui()

	def _build_ui(self) -> None:
		top = ttk.Frame(self)
		top.pack(fill=tk.X, padx=10, pady=8)

		ttk.Label(top, text="Folder:").pack(side=tk.LEFT)
		folder_entry = ttk.Entry(top, textvariable=self.folder_var)
		folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
		ttk.Button(top, text="Browse", command=self._choose_folder).pack(side=tk.LEFT)
		ttk.Button(top, text="Load", command=self._load_folder).pack(side=tk.LEFT, padx=(6, 0))

		options = ttk.Frame(self)
		options.pack(fill=tk.X, padx=10)

		ttk.Label(options, text="Extensions:").grid(row=0, column=0, sticky="w")
		ttk.Entry(options, textvariable=self.ext_var, width=40).grid(row=0, column=1, sticky="we", padx=6)
		ttk.Label(options, text="Rule:").grid(row=0, column=2, sticky="w")
		rule_box = ttk.Combobox(
			options,
			textvariable=self.rule_var,
			values=[
				"Pattern",
				"Prefix + Original",
				"Original + Suffix",
				"Replace text",
				"Index only",
			],
			state="readonly",
			width=20,
		)
		rule_box.grid(row=0, column=3, sticky="w", padx=6)
		ttk.Label(options, text="Start index:").grid(row=0, column=4, sticky="w")
		ttk.Spinbox(options, from_=1, to=10_000_000, textvariable=self.start_index_var, width=8).grid(
			row=0,
			column=5,
			sticky="w",
			padx=(6, 0),
		)
		ttk.Checkbutton(options, text="Keep original extension", variable=self.keep_ext_var).grid(
			row=0, column=6, sticky="w", padx=10
		)

		ttk.Label(options, text="Pattern:").grid(row=1, column=0, sticky="w", pady=(6, 0))
		ttk.Entry(options, textvariable=self.pattern_var, width=40).grid(
			row=1, column=1, sticky="we", padx=6, pady=(6, 0)
		)
		ttk.Label(options, text="Prefix:").grid(row=1, column=2, sticky="w", pady=(6, 0))
		ttk.Entry(options, textvariable=self.prefix_var, width=20).grid(
			row=1, column=3, sticky="we", padx=6, pady=(6, 0)
		)
		ttk.Label(options, text="Suffix:").grid(row=1, column=4, sticky="w", pady=(6, 0))
		ttk.Entry(options, textvariable=self.suffix_var, width=20).grid(
			row=1, column=5, sticky="we", padx=6, pady=(6, 0)
		)
		ttk.Label(options, text="Index format:").grid(row=1, column=6, sticky="w", pady=(6, 0))
		ttk.Entry(options, textvariable=self.index_format_var, width=18).grid(
			row=1, column=7, sticky="w", padx=6, pady=(6, 0)
		)

		ttk.Label(options, text="Find:").grid(row=2, column=0, sticky="w", pady=(6, 0))
		ttk.Entry(options, textvariable=self.find_var, width=20).grid(
			row=2, column=1, sticky="we", padx=6, pady=(6, 0)
		)
		ttk.Label(options, text="Replace:").grid(row=2, column=2, sticky="w", pady=(6, 0))
		ttk.Entry(options, textvariable=self.replace_var, width=20).grid(
			row=2, column=3, sticky="we", padx=6, pady=(6, 0)
		)
		ttk.Checkbutton(options, text="Rename selected only", variable=self.rename_selected_var).grid(
			row=2, column=4, sticky="w", padx=(6, 0), pady=(6, 0)
		)

		options.columnconfigure(1, weight=1)
		options.columnconfigure(3, weight=1)
		options.columnconfigure(5, weight=1)

		hint = ttk.Label(
			self,
			text="Pattern supports {index}, {index0}, {stem}, {ext}. Example: image_{index:03d}",
			foreground="#555555",
		)
		hint.pack(fill=tk.X, padx=10, pady=(4, 6))

		middle = ttk.Frame(self)
		middle.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

		left_frame = ttk.LabelFrame(middle, text="Drag to reorder")
		left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
		right_frame = ttk.LabelFrame(middle, text="Preview new names")
		right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

		self.canvas = tk.Canvas(left_frame, highlightthickness=0)
		self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		left_scroll = ttk.Scrollbar(left_frame, command=self.canvas.yview)
		left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
		self.canvas.configure(yscrollcommand=left_scroll.set)
		self.canvas_frame = ttk.Frame(self.canvas)
		self.canvas_window = self.canvas.create_window((0, 0), window=self.canvas_frame, anchor="nw")
		self.canvas_frame.bind("<Configure>", self._on_canvas_configure)
		self.canvas.bind("<Configure>", self._on_canvas_resize)
		self.canvas.bind("<MouseWheel>", self._on_mousewheel)
		self.canvas.bind("<Button-1>", self._on_canvas_click)
		self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
		self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
		self.canvas.bind("<Button-3>", self._on_canvas_right_click)

		self.preview_listbox = tk.Listbox(right_frame, selectmode=tk.BROWSE)
		self.preview_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		right_scroll = ttk.Scrollbar(right_frame, command=self.preview_listbox.yview)
		right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
		self.preview_listbox.configure(yscrollcommand=right_scroll.set)


		actions = ttk.Frame(self)
		actions.pack(fill=tk.X, padx=10, pady=(0, 8))
		ttk.Button(actions, text="Select all", command=self._select_all).pack(side=tk.LEFT)
		ttk.Button(actions, text="Select none", command=self._select_none).pack(side=tk.LEFT, padx=6)
		ttk.Button(actions, text="Invert selection", command=self._select_invert).pack(side=tk.LEFT)
		tk.Button(actions, text="Move up", command=self._move_up).pack(side=tk.LEFT, padx=(12, 0))
		tk.Button(actions, text="Move down", command=self._move_down).pack(side=tk.LEFT, padx=6)
		tk.Button(actions, text="Move to start", command=self._move_to_start).pack(side=tk.LEFT)
		ttk.Button(actions, text="Update preview", command=self._update_preview).pack(side=tk.LEFT, padx=12)
		ttk.Button(actions, text="Reset order", command=self._reset_order).pack(side=tk.LEFT, padx=6)
		ttk.Button(actions, text="Rename", command=self._apply_rename).pack(side=tk.RIGHT)

		self.status_var = tk.StringVar(value="Select a folder to begin.")
		status = ttk.Label(self, textvariable=self.status_var, anchor="w")
		status.pack(fill=tk.X, padx=10, pady=(0, 8))

		self.pattern_var.trace_add("write", lambda *_: self._update_preview())
		self.start_index_var.trace_add("write", lambda *_: self._update_preview())
		self.keep_ext_var.trace_add("write", lambda *_: self._update_preview())
		self.rename_selected_var.trace_add("write", lambda *_: self._update_preview())
		self.rule_var.trace_add("write", lambda *_: self._update_preview())
		self.prefix_var.trace_add("write", lambda *_: self._update_preview())
		self.suffix_var.trace_add("write", lambda *_: self._update_preview())
		self.find_var.trace_add("write", lambda *_: self._update_preview())
		self.replace_var.trace_add("write", lambda *_: self._update_preview())
		self.index_format_var.trace_add("write", lambda *_: self._update_preview())

	def _choose_folder(self) -> None:
		folder = filedialog.askdirectory()
		if folder:
			self.folder_var.set(folder)
			self._load_folder()

	def _parse_extensions(self) -> set[str]:
		raw = self.ext_var.get()
		parts = [p.strip().lower() for p in raw.replace(";", ",").split(",")]
		exts: set[str] = set()
		for part in parts:
			if not part:
				continue
			if not part.startswith("."):
				part = f".{part}"
			exts.add(part)
		return exts

	def _load_folder(self) -> None:
		folder = Path(self.folder_var.get())
		if not folder.exists() or not folder.is_dir():
			messagebox.showerror("Invalid folder", "Please select a valid folder.")
			return

		exts = self._parse_extensions()
		files = [p for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in exts]

		self.items = [RenameItem(path=p) for p in files]
		self.original_items = [RenameItem(path=p) for p in files]
		self.selected_indices.clear()
		self._last_selected_index = None
		self._refresh_listboxes()
		self._update_preview()
		self.status_var.set(f"Loaded {len(self.items)} images from {folder}.")

	def _refresh_listboxes(self) -> None:
		selected_indices = set(self.selected_indices)
		self.preview_listbox.delete(0, tk.END)
		for child in self.canvas_frame.winfo_children():
			child.destroy()
		self._item_widgets = []
		self._thumb_images = []

		if not self.items:
			placeholder = ttk.Label(self.canvas_frame, text="No images loaded")
			placeholder.pack(padx=8, pady=8)
			self.selected_indices = set()
			return

		for index, item in enumerate(self.items):
			frame = tk.Frame(self.canvas_frame, bd=1, relief="flat")
			thumb = self._load_thumbnail(item.path)
			if thumb is not None:
				image_label = tk.Label(frame, image=thumb)
				self._thumb_images.append(thumb)
			else:
				image_label = tk.Label(frame, text="No preview", width=12, height=8)
			name_label = tk.Label(
				frame,
				text=item.path.name,
				wraplength=self.thumb_size + 20,
				justify="center",
			)

			for widget in (frame, image_label, name_label):
				widget.bind("<Button-1>", lambda event, idx=index: self._on_item_click(event, idx))
				widget.bind("<ButtonRelease-1>", self._end_drag)
				widget.bind("<B1-Motion>", self._drag_move)
				widget.bind("<Button-3>", lambda event, idx=index: self._on_item_right_click(event, idx))

			image_label.pack(padx=8, pady=(8, 4))
			name_label.pack(padx=8, pady=(0, 8))
			self._item_widgets.append(frame)

		self._layout_items()

		self.selected_indices = {idx for idx in selected_indices if idx < len(self.items)}
		self._update_item_styles()

	def _reset_order(self) -> None:
		self.items = [RenameItem(path=item.path) for item in self.original_items]
		self._refresh_listboxes()
		self._update_preview()

	def _on_item_click(self, event: tk.Event, index: int) -> None:
		# Prevent rubber band selection when clicking on items
		self._rubberband_start = None
		if self._rubberband_rect is not None:
			self.canvas.delete(self._rubberband_rect)
			self._rubberband_rect = None
			
		self._drag_index = index
		self._drag_start = (event.x_root, event.y_root)
		self._drag_target_index = None
		self._dragging = False
		
		# Check for Control key (multi-select)
		if event.state & 4:  # Control key
			if index in self.selected_indices:
				self.selected_indices.remove(index)
			else:
				self.selected_indices.add(index)
			self._last_selected_index = index
		# Check for Shift key (range select)
		elif event.state & 1 and self._last_selected_index is not None:  # Shift key
			start = min(self._last_selected_index, index)
			end = max(self._last_selected_index, index)
			self.selected_indices.update(range(start, end + 1))
		# Normal click (single select)
		else:
			self.selected_indices = {index}
			self._last_selected_index = index

		self._update_item_styles()
		self._update_preview()

	def _end_drag(self, _event: tk.Event) -> None:
		if self._dragging and self._drag_index is not None and self._drag_target_index is not None:
			self._apply_reorder(self._drag_index, self._drag_target_index)
		self._clear_insertion_line()
		self._drag_index = None
		self._drag_start = None
		self._drag_target_index = None
		self._dragging = False

	def _drag_move(self, event: tk.Event) -> None:
		if self._drag_index is None:
			return
		if self._drag_start is not None:
			dx = abs(event.x_root - self._drag_start[0])
			dy = abs(event.y_root - self._drag_start[1])
			if dx < 6 and dy < 6:
				return
		self._dragging = True
		new_index = self._index_from_root_xy(event.x_root, event.y_root)
		if new_index is None:
			return
		self._drag_target_index = new_index
		self._show_insertion_line(new_index)

	def _apply_reorder(self, drag_index: int, target_index: int) -> None:
		if target_index == drag_index:
			return
		if drag_index in self.selected_indices and self.selected_indices:
			selected_indices = sorted(self.selected_indices)
			selected_items = [self.items[i] for i in selected_indices]
			remaining = [itm for i, itm in enumerate(self.items) if i not in self.selected_indices]
			shift = sum(1 for i in selected_indices if i < target_index)
			insert_at = max(0, target_index - shift)
			self.items = remaining[:insert_at] + selected_items + remaining[insert_at:]
			self.selected_indices = set(range(insert_at, insert_at + len(selected_items)))
		else:
			selected_paths = {self.items[i].path for i in self.selected_indices}
			item = self.items.pop(drag_index)
			self.items.insert(target_index, item)
			self.selected_indices = {i for i, itm in enumerate(self.items) if itm.path in selected_paths}
		self._refresh_listboxes()
		self._update_preview()

	def _select_all(self) -> None:
		self.selected_indices = set(range(len(self.items)))
		self._update_preview()
		self._update_item_styles()

	def _select_none(self) -> None:
		self.selected_indices.clear()
		self._update_preview()
		self._update_item_styles()

	def _select_invert(self) -> None:
		current = set(self.selected_indices)
		self.selected_indices = {i for i in range(len(self.items)) if i not in current}
		self._update_preview()
		self._update_item_styles()

	def _get_selected_indices(self) -> list[int]:
		return sorted(self.selected_indices)


	def _restore_selection(self, indices: list[int]) -> None:
		self.selected_indices = {index for index in indices if 0 <= index < len(self.items)}
		self._update_item_styles()

	def _get_active_items(self) -> list[RenameItem]:
		if not self.rename_selected_var.get():
			return self.items
		return [item for i, item in enumerate(self.items) if i in self.selected_indices]

	def _on_canvas_configure(self, _event: tk.Event) -> None:
		self.canvas.configure(scrollregion=self.canvas.bbox("all"))

	def _on_canvas_resize(self, event: tk.Event) -> None:
		self.canvas.itemconfigure(self.canvas_window, width=event.width)
		self._layout_items()

	def _on_mousewheel(self, event: tk.Event) -> None:
		if event.delta:
			self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

	def _on_canvas_click(self, event: tk.Event) -> None:
		if event.widget is not self.canvas:
			return
		# Only start rubber band if clicking on empty canvas area
		self._drag_index = None
		self._drag_start = None
		self._rubberband_start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
		self._rubberband_additive = bool(event.state & 4)  # Control key
		if self._rubberband_rect is not None:
			self.canvas.delete(self._rubberband_rect)
			self._rubberband_rect = None
		if not self._rubberband_additive:
			self.selected_indices.clear()
			self._update_item_styles()

	def _on_canvas_drag(self, event: tk.Event) -> None:
		if self._rubberband_start is None:
			return
		x0, y0 = self._rubberband_start
		x1, y1 = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
		if self._rubberband_rect is None:
			self._rubberband_rect = self.canvas.create_rectangle(
				x0, y0, x1, y1,
				outline="#0078d4",
				width=2,
				fill="#0078d430",  # Semi-transparent fill
				dash=(3, 3),
			)
		else:
			self.canvas.coords(self._rubberband_rect, x0, y0, x1, y1)
		self._apply_rubberband_selection(x0, y0, x1, y1, preview_only=True)

	def _on_canvas_release(self, event: tk.Event) -> None:
		if self._rubberband_start is None:
			return
		x0, y0 = self._rubberband_start
		x1, y1 = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
		self._apply_rubberband_selection(x0, y0, x1, y1, preview_only=False)
		if self._rubberband_rect is not None:
			self.canvas.delete(self._rubberband_rect)
			self._rubberband_rect = None
		self._rubberband_start = None
		self._update_preview()

	def _apply_rubberband_selection(
		self,
		x0: float,
		y0: float,
		x1: float,
		y1: float,
		preview_only: bool,
	) -> None:
		left = min(x0, x1)
		right = max(x0, x1)
		top = min(y0, y1)
		bottom = max(y0, y1)
		selection = set(self.selected_indices) if self._rubberband_additive else set()

		for idx, widget in enumerate(self._item_widgets):
			# Use canvas coordinates for consistent calculation
			wx = widget.winfo_x()
			wy = widget.winfo_y()
			ww = widget.winfo_width()
			wh = widget.winfo_height()
			if wx < right and wx + ww > left and wy < bottom and wy + wh > top:
				selection.add(idx)

		self.selected_indices = selection
		self._update_item_styles()
		if not preview_only:
			self._update_preview()

	def _layout_items(self) -> None:
		if not self._item_widgets:
			return
		self.update_idletasks()
		available = max(self.canvas.winfo_width(), self.thumb_size + 40)
		self._cell_width = self.thumb_size + 40
		self._cell_height = max(self.thumb_size + 60, self._item_widgets[0].winfo_height())
		self._columns = max(1, available // self._cell_width)
		for idx, frame in enumerate(self._item_widgets):
			row = idx // self._columns
			col = idx % self._columns
			frame.grid(row=row, column=col, padx=6, pady=6, sticky="n")
		for col in range(self._columns):
			self.canvas_frame.grid_columnconfigure(col, weight=1)

	def _load_thumbnail(self, path: Path) -> tk.PhotoImage | None:
		max_size = (self.thumb_size, self.thumb_size)
		try:
			if Image is not None and ImageTk is not None:
				image = Image.open(path)
				image.thumbnail(max_size)
				return ImageTk.PhotoImage(image)
			photo = tk.PhotoImage(file=str(path))
			scale = max(photo.width() / max_size[0], photo.height() / max_size[1], 1)
			if scale > 1:
				factor = int(math.ceil(scale))
				photo = photo.subsample(factor, factor)
			return photo
		except Exception:  # noqa: BLE001
			return None

	def _update_item_styles(self) -> None:
		default_bg = "white"
		selected_bg = "#0078d4"  # Windows 10/11 selection blue
		selected_fg = "white"
		default_fg = "black"
		
		for idx, frame in enumerate(self._item_widgets):
			is_selected = idx in self.selected_indices
			bg = selected_bg if is_selected else default_bg
			fg = selected_fg if is_selected else default_fg
			
			frame.configure(
				bg=bg,
				relief="solid" if is_selected else "flat",
				bd=2 if is_selected else 0,
				highlightbackground=selected_bg if is_selected else default_bg,
				highlightthickness=1 if is_selected else 0,
			)
			for child in frame.winfo_children():
				if isinstance(child, tk.Label):
					child.configure(bg=bg, fg=fg)
				else:
					child.configure(bg=bg)

	def _index_from_root_xy(self, x_root: int, y_root: int) -> int | None:
		if not self._item_widgets:
			return None
		# Convert to canvas coordinates to handle scrolling
		canvas_x = self.canvas.winfo_rootx()
		canvas_y = self.canvas.winfo_rooty()
		rel_x = x_root - canvas_x
		rel_y = y_root - canvas_y
		canvas_coord_x = self.canvas.canvasx(rel_x)
		canvas_coord_y = self.canvas.canvasy(rel_y)
		
		col = min(self._columns - 1, max(0, int(canvas_coord_x // self._cell_width)))
		row = max(0, int(canvas_coord_y // self._cell_height))
		index = int(row * self._columns + col)
		if index >= len(self._item_widgets):
			return len(self._item_widgets) - 1
		return index

	def _show_insertion_line(self, target_index: int) -> None:
		self._clear_insertion_line()
		if not self._item_widgets or target_index >= len(self._item_widgets):
			return
		
		row = target_index // self._columns
		col = target_index % self._columns
		
		# Calculate line position
		if col == 0:  # Start of row
			x = 0
			y = row * self._cell_height
			width = self._cell_width
			height = 3
		else:  # Between items in row
			x = col * self._cell_width - 3
			y = row * self._cell_height + 10
			width = 6
			height = self._cell_height - 20
		
		self._insertion_line = self.canvas.create_rectangle(
			x, y, x + width, y + height,
			fill="#0078d4", outline="#0078d4", width=0
		)

	def _clear_insertion_line(self) -> None:
		if self._insertion_line is not None:
			self.canvas.delete(self._insertion_line)
			self._insertion_line = None

	def _on_canvas_right_click(self, event: tk.Event) -> None:
		if event.widget is not self.canvas:
			return
		menu = tk.Menu(self, tearoff=0)
		if self._clipboard_indices:
			menu.add_command(label="Paste here", command=lambda: self._paste_at_position(event.x, event.y))
		else:
			menu.add_command(label="(Nothing to paste)", state="disabled")
		try:
			menu.tk_popup(event.x_root, event.y_root)
		finally:
			menu.grab_release()

	def _on_item_right_click(self, event: tk.Event, index: int) -> None:
		if index not in self.selected_indices:
			self.selected_indices = {index}
			self._update_item_styles()
			
		menu = tk.Menu(self, tearoff=0)
		menu.add_command(label="Cut", command=self._cut_selected)
		menu.add_separator()
		if self._clipboard_indices:
			menu.add_command(label="Paste here", command=lambda: self._paste_at_index(index))
		else:
			menu.add_command(label="(Nothing to paste)", state="disabled")
		try:
			menu.tk_popup(event.x_root, event.y_root)
		finally:
			menu.grab_release()

	def _cut_selected(self) -> None:
		self._clipboard_indices = set(self.selected_indices)
		if self._clipboard_indices:
			self.status_var.set(f"Cut {len(self._clipboard_indices)} items. Right-click to paste.")

	def _paste_at_position(self, x: int, y: int) -> None:
		canvas_x = self.canvas.canvasx(x)
		canvas_y = self.canvas.canvasy(y)
		col = min(self._columns - 1, max(0, int(canvas_x // self._cell_width)))
		row = max(0, int(canvas_y // self._cell_height))
		index = min(len(self.items), int(row * self._columns + col))
		self._paste_at_index(index)

	def _paste_at_index(self, target_index: int) -> None:
		if not self._clipboard_indices:
			return
		
		clipboard_items = [self.items[i] for i in sorted(self._clipboard_indices)]
		remaining_items = [item for i, item in enumerate(self.items) if i not in self._clipboard_indices]
		
		# Adjust target index for removed items
		shift = sum(1 for i in self._clipboard_indices if i < target_index)
		insert_at = max(0, target_index - shift)
		
		self.items = remaining_items[:insert_at] + clipboard_items + remaining_items[insert_at:]
		self.selected_indices = set(range(insert_at, insert_at + len(clipboard_items)))
		self._clipboard_indices.clear()
		
		self._refresh_listboxes()
		self._update_preview()
		self.status_var.set("Pasted successfully.")

	def _move_up(self) -> None:
		if not self.selected_indices:
			return
		min_index = min(self.selected_indices)
		if min_index > 0:
			self._move_selected_to(min_index - 1)

	def _move_down(self) -> None:
		if not self.selected_indices:
			return
		max_index = max(self.selected_indices)
		if max_index < len(self.items) - 1:
			self._move_selected_to(max_index + 2)

	def _move_to_start(self) -> None:
		if self.selected_indices:
			self._move_selected_to(0)

	def _move_selected_to(self, target_index: int) -> None:
		if not self.selected_indices:
			return
		
		selected_items = [self.items[i] for i in sorted(self.selected_indices)]
		remaining_items = [item for i, item in enumerate(self.items) if i not in self.selected_indices]
		
		shift = sum(1 for i in self.selected_indices if i < target_index)
		insert_at = max(0, min(len(remaining_items), target_index - shift))
		
		self.items = remaining_items[:insert_at] + selected_items + remaining_items[insert_at:]
		self.selected_indices = set(range(insert_at, insert_at + len(selected_items)))
		
		self._refresh_listboxes()
		self._update_preview()

	def _format_index(self, index: int) -> str:
		fmt = self.index_format_var.get().strip()
		if not fmt:
			raise ValueError("Index format cannot be empty.")
		return fmt.format_map({"index": index, "index0": index - 1})

	def _compute_new_name(self, item: RenameItem, index: int) -> str:
		ext = item.path.suffix
		rule = self.rule_var.get()
		values = {
			"index": index,
			"index0": index - 1,
			"stem": item.path.stem,
			"ext": ext.lstrip("."),
		}

		if rule == "Pattern":
			pattern = self.pattern_var.get().strip()
			if not pattern:
				raise ValueError("Pattern cannot be empty.")
			new_base = pattern.format_map(values)
			keep_ext = self.keep_ext_var.get() and "{ext}" not in pattern
		elif rule == "Prefix + Original":
			new_base = f"{self.prefix_var.get()}{item.path.stem}"
			keep_ext = self.keep_ext_var.get()
		elif rule == "Original + Suffix":
			new_base = f"{item.path.stem}{self.suffix_var.get()}"
			keep_ext = self.keep_ext_var.get()
		elif rule == "Replace text":
			find_text = self.find_var.get()
			replace_text = self.replace_var.get()
			if not find_text:
				raise ValueError("Find text cannot be empty.")
			new_base = item.path.stem.replace(find_text, replace_text)
			keep_ext = self.keep_ext_var.get()
		elif rule == "Index only":
			new_base = self._format_index(index)
			keep_ext = self.keep_ext_var.get()
		else:
			raise ValueError("Unknown rule.")

		if keep_ext:
			return f"{new_base}{ext}"
		return new_base

	def _update_preview(self) -> int:
		self.preview_listbox.delete(0, tk.END)
		if not self.items:
			return 0

		active_items = self._get_active_items()
		select_mode = self.rename_selected_var.get()
		
		if select_mode and not active_items:
			self.status_var.set("No images selected for renaming.")
			# Still show all files in preview, but indicate none will be renamed
			for item in self.items:
				self.preview_listbox.insert(tk.END, f"[SKIP] {item.path.name}")
			return 0

		start = self.start_index_var.get()
		errors = 0
		new_names: list[str] = []
		active_indices = {self.items.index(item) for item in active_items} if select_mode else set()

		for i, item in enumerate(self.items):
			if select_mode and i not in active_indices:
				# Show skipped files in selection mode
				self.preview_listbox.insert(tk.END, f"[SKIP] {item.path.name}")
				item.new_name = ""  # Clear new_name for skipped items
			else:
				# This item will be renamed
				try:
					rename_index = len([x for x in active_items if self.items.index(x) <= i]) + start - 1
					new_name = self._compute_new_name(item, rename_index)
					item.new_name = new_name
					new_names.append(new_name)
					prefix = "[RENAME] " if select_mode else ""
					self.preview_listbox.insert(tk.END, f"{prefix}{new_name}")
				except Exception as exc:  # noqa: BLE001
					errors += 1
					item.new_name = ""
					prefix = "[ERROR] " if select_mode else ""
					self.preview_listbox.insert(tk.END, f"{prefix}Error: {exc}")

		if errors:
			self.status_var.set("Preview has errors. Fix the pattern before renaming.")
		else:
			if select_mode:
				skipped_count = len(self.items) - len(active_items)
				self.status_var.set(f"Preview ready: {len(new_names)} files to rename, {skipped_count} files skipped.")
			else:
				self.status_var.set(f"Preview ready for {len(new_names)} files.")
		return errors

	def _apply_rename(self) -> None:
		if not self.items:
			messagebox.showinfo("Nothing to rename", "No images loaded.")
			return

		active_items = self._get_active_items()
		if self.rename_selected_var.get() and not active_items:
			messagebox.showinfo("Nothing selected", "Select images to rename or turn off selection mode.")
			return

		errors = self._update_preview()
		if errors:
			messagebox.showerror("Invalid preview", "Please fix the preview errors first.")
			return
		targets = []
		source_names = {item.path.name for item in active_items}

		for item in active_items:
			if not item.new_name:
				messagebox.showerror("Invalid preview", "Please fix the preview errors first.")
				return
			targets.append(item.new_name)

		if len(targets) != len(set(targets)):
			messagebox.showerror("Duplicate names", "The preview contains duplicate names.")
			return

		for item in active_items:
			target_path = item.path.with_name(item.new_name)
			if target_path.exists() and target_path.name not in source_names:
				messagebox.showerror(
					"Name conflict",
					f"Target file already exists: {target_path.name}",
				)
				return

		if not messagebox.askyesno(
			"Confirm rename", 
			f"Rename {len(active_items)} files?" + 
			(f"\n({len(self.items) - len(active_items)} files will be skipped)" if self.rename_selected_var.get() and len(active_items) < len(self.items) else "")
		):
			return

		temp_paths: list[Path] = []
		try:
			for i, item in enumerate(active_items):
				if item.path.name == item.new_name:
					temp_paths.append(item.path)
					continue
				while True:
					tmp_name = f"{item.path.stem}.renametmp_{uuid.uuid4().hex}{item.path.suffix}"
					tmp_path = item.path.with_name(tmp_name)
					if not tmp_path.exists():
						break
				item.path.rename(tmp_path)
				temp_paths.append(tmp_path)

			for item, tmp_path in zip(active_items, temp_paths, strict=True):
				target_path = tmp_path.with_name(item.new_name)
				if tmp_path.name != item.new_name:
					tmp_path.rename(target_path)
				item.path = target_path

		except OSError as exc:
			messagebox.showerror("Rename failed", f"Rename failed: {exc}")
			return

		self.original_items = [RenameItem(path=item.path) for item in self.items]
		self._refresh_listboxes()
		self._update_preview()
		self.status_var.set("Rename complete.")


if __name__ == "__main__":
	app = ImageRenameApp()
	app.mainloop()

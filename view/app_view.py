import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from controller.app_controller import AppController


class AppView(tk.Tk):
    """Main GUI for the File Search Indexer."""

    def __init__(self, controller: AppController):
        super().__init__()
        self.controller = controller
        self.title("File Search Indexer")
        self.geometry("1000x640")
        self.resizable(True, True)
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.configure(padx=12, pady=12)

        # Top bar — scan section
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))

        self.dir_var = tk.StringVar(value="No directory selected")
        ttk.Label(top, textvariable=self.dir_var,
                  foreground="gray").pack(side="left", fill="x", expand=True)
        ttk.Button(top, text="Browse…",
                   command=self._on_browse).pack(side="right", padx=(6, 0))
        self.btn_scan = ttk.Button(top, text="⟳ Scan",
                                   command=self._on_scan, state="disabled")
        self.btn_scan.pack(side="right")

        # Status bar
        self.status_var = tk.StringVar(value="No index loaded.")
        ttk.Label(self, textvariable=self.status_var,
                  foreground="gray", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 8))

        # Notebook — tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self._build_search_tab()
        self._build_recent_tab()
        self._build_duplicates_tab()

    def _build_search_tab(self) -> None:
        """Search tab with filters and results table."""
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="🔍 Search")

        # Filters row
        filters = ttk.Frame(tab)
        filters.pack(fill="x", pady=(0, 8))

        ttk.Label(filters, text="Name:").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(filters, textvariable=self.search_var, width=20).pack(side="left", padx=(4, 12))

        ttk.Label(filters, text="Extension:").pack(side="left")
        self.ext_var = tk.StringVar()
        ttk.Entry(filters, textvariable=self.ext_var, width=8).pack(side="left", padx=(4, 12))

        ttk.Label(filters, text="Sort by:").pack(side="left")
        self.sort_var = tk.StringVar(value="name")
        ttk.Combobox(filters, textvariable=self.sort_var,
                     values=["name", "size", "date"],
                     width=8, state="readonly").pack(side="left", padx=(4, 12))

        ttk.Button(filters, text="Search",
                   command=self._on_search).pack(side="left", padx=(0, 6))
        ttk.Button(filters, text="Clear",
                   command=self._on_clear_search).pack(side="left")

        self.results_count_var = tk.StringVar(value="")
        ttk.Label(filters, textvariable=self.results_count_var,
                  foreground="gray").pack(side="right")

        # Results table
        cols = ("Name", "Extension", "Size", "Date Modified", "Path")
        self.tree = ttk.Treeview(tab, columns=cols, show="headings", height=18)

        for col in cols:
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._on_sort_column(c))
        self.tree.column("Name",          width=200)
        self.tree.column("Extension",     width=80,  anchor="center")
        self.tree.column("Size",          width=90,  anchor="e")
        self.tree.column("Date Modified", width=150, anchor="center")
        self.tree.column("Path",          width=380)

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _build_recent_tab(self) -> None:
        """Recently added files tab."""
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="🕐 Recently Added")

        ttk.Button(tab, text="Refresh",
                   command=self._on_refresh_recent).pack(anchor="w", pady=(0, 8))

        cols = ("Name", "Extension", "Size", "Date Modified", "Path")
        self.recent_tree = ttk.Treeview(tab, columns=cols, show="headings", height=20)
        for col in cols:
            self.recent_tree.heading(col, text=col)
        self.recent_tree.column("Name",          width=200)
        self.recent_tree.column("Extension",     width=80,  anchor="center")
        self.recent_tree.column("Size",          width=90,  anchor="e")
        self.recent_tree.column("Date Modified", width=150, anchor="center")
        self.recent_tree.column("Path",          width=380)

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scroll.set)
        self.recent_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _build_duplicates_tab(self) -> None:
        """Duplicate files tab."""
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="📋 Duplicates")

        ttk.Button(tab, text="Find Duplicates",
                   command=self._on_find_duplicates).pack(anchor="w", pady=(0, 8))

        self.dup_count_var = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.dup_count_var,
                  foreground="gray").pack(anchor="w", pady=(0, 4))

        cols = ("Group", "Name", "Size", "Path")
        self.dup_tree = ttk.Treeview(tab, columns=cols, show="headings", height=20)
        for col in cols:
            self.dup_tree.heading(col, text=col)
        self.dup_tree.column("Group", width=60,  anchor="center")
        self.dup_tree.column("Name",  width=200)
        self.dup_tree.column("Size",  width=90,  anchor="e")
        self.dup_tree.column("Path",  width=560)

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.dup_tree.yview)
        self.dup_tree.configure(yscrollcommand=scroll.set)
        self.dup_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _populate_tree(self, tree, entries) -> None:
        tree.delete(*tree.get_children())
        for e in entries:
            tree.insert("", "end", values=(
                e.name,
                e.extension,
                self.controller.format_size(e.size),
                e.date_modified.strftime("%Y-%m-%d %H:%M"),
                e.path,
            ))

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_browse(self) -> None:
        folder = filedialog.askdirectory(title="Select directory to index")
        if folder:
            self.selected_folder = folder
            self.dir_var.set(folder)
            self.btn_scan.config(state="normal")

    def _on_scan(self) -> None:
        folder = self.dir_var.get()
        if not folder or folder == "No directory selected":
            messagebox.showwarning("Warning", "Please select a directory first.")
            return

        self.status_var.set("Scanning... please wait.")
        self.update()

        total, indexed, error = self.controller.scan(folder)

        if error:
            messagebox.showerror("Scan Error", error)
            self.status_var.set("Scan failed.")
            return

        self.status_var.set(
            f"Index ready — {indexed} files indexed "
            f"({total - indexed} skipped) from: {folder}"
        )
        self._on_search()

    def _on_search(self) -> None:
        keyword = self.search_var.get().strip()
        ext = self.ext_var.get().strip()
        sort_by = self.sort_var.get()

        results = self.controller.search(
            keyword=keyword,
            extension=ext,
            sort_by=sort_by,
        )
        self._populate_tree(self.tree, results)
        self.results_count_var.set(f"{len(results)} result(s)")

    def _on_clear_search(self) -> None:
        self.search_var.set("")
        self.ext_var.set("")
        self.sort_var.set("name")
        self._on_search()

    def _on_sort_column(self, col: str) -> None:
        mapping = {"Name": "name", "Size": "size", "Date Modified": "date"}
        sort_by = mapping.get(col, "name")
        self.sort_var.set(sort_by)
        self._on_search()

    def _on_refresh_recent(self) -> None:
        recent = self.controller.get_recently_added()
        self._populate_tree(self.recent_tree, recent)

    def _on_find_duplicates(self) -> None:
        groups = self.controller.get_duplicates()
        self.dup_tree.delete(*self.dup_tree.get_children())

        if not groups:
            self.dup_count_var.set("No duplicates found.")
            return

        total = sum(len(g) for g in groups)
        self.dup_count_var.set(f"{len(groups)} duplicate group(s) — {total} files")

        for i, group in enumerate(groups, 1):
            for entry in group:
                self.dup_tree.insert("", "end", values=(
                    f"#{i}",
                    entry.name,
                    self.controller.format_size(entry.size),
                    entry.path,
                ))

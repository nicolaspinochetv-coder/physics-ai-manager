from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .deployment import (
    DeploymentError,
    DeploymentRequest,
    deploy_project,
    doctor_project,
    inspect_project,
    load_manifest,
    slugify,
)
from .paths import APP_NAME, find_library_root, icon_path, load_config, save_config


class PhysicsAIManager(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("900x760")
        self.minsize(820, 680)
        self._set_window_icon()

        self.config_data = load_config()
        try:
            self.library_root = find_library_root(self.config_data)
            self.manifest = load_manifest(self.library_root)
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            self.destroy()
            return

        self.project_types = self.manifest["project_types"]
        self.agents = self.manifest["agents"]
        self.modes = list(self.manifest["mode_scaffolds"].keys())
        self._build_style()
        self._build_ui()

    def _set_window_icon(self) -> None:
        path = icon_path()
        if not path.is_file():
            return
        try:
            self._icon_image = tk.PhotoImage(file=str(path))
            self.iconphoto(True, self._icon_image)
        except tk.TclError:
            pass

    def _build_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("TkDefaultFont", 17, "bold"))
        style.configure("Subtitle.TLabel", font=("TkDefaultFont", 10))
        style.configure("Section.TLabelframe.Label", font=("TkDefaultFont", 10, "bold"))
        style.configure("Primary.TButton", padding=(14, 8))

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=16)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Physics AI Manager", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Create and maintain portable AI workspaces for physics research, coding, writing, learning, and assistance.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 12))

        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)
        self.new_tab = ttk.Frame(notebook, padding=12)
        self.manage_tab = ttk.Frame(notebook, padding=12)
        notebook.add(self.new_tab, text="New project")
        notebook.add(self.manage_tab, text="Manage project")
        self._build_new_tab()
        self._build_manage_tab()

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(8, 0))
        version = self.manifest.get("library_version", "?")
        ttk.Label(footer, text=f"Blueprint library {version}  •  {self.library_root}").pack(side="left")
        ttk.Button(footer, text="Open library folder", command=lambda: self._open_folder(self.library_root)).pack(side="right")

    def _build_new_tab(self) -> None:
        tab = self.new_tab
        tab.columnconfigure(1, weight=1)

        self.title_var = tk.StringVar()
        self.parent_var = tk.StringVar(value=self.config_data.get("last_parent", str(Path.home())))
        self.slug_var = tk.StringVar()
        self.slug_var.trace_add("write", lambda *_: self._update_preview())
        self.type_var = tk.StringVar(value="research")
        self.primary_var = tk.StringVar(value="RESEARCH")
        self.git_var = tk.BooleanVar(value=self.config_data.get("git_init", True))
        self.allow_existing_var = tk.BooleanVar(value=False)
        self.mode_vars = {m: tk.BooleanVar(value=(m == "RESEARCH")) for m in self.modes}
        default_agent = self.config_data.get("last_agent", "claude")
        self.agent_vars = {a: tk.BooleanVar(value=(a == default_agent)) for a in self.agents}
        self.new_document_paths: list[Path] = []

        row = 0
        ttk.Label(tab, text="Project title").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        title_entry = ttk.Entry(tab, textvariable=self.title_var)
        title_entry.grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        title_entry.bind("<KeyRelease>", self._title_changed)
        row += 1

        ttk.Label(tab, text="Parent directory").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        ttk.Entry(tab, textvariable=self.parent_var).grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Button(tab, text="Browse…", command=self._browse_parent).grid(row=row, column=2, sticky="ew", padx=(8, 0), pady=6)
        row += 1

        ttk.Label(tab, text="Folder name").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        ttk.Entry(tab, textvariable=self.slug_var).grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Label(tab, text="Project profile").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        values = [f"{k} — {v['label']}" for k, v in self.project_types.items()]
        self.type_combo = ttk.Combobox(tab, state="readonly", values=values)
        self.type_combo.current(list(self.project_types).index("research"))
        self.type_combo.grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        self.type_combo.bind("<<ComboboxSelected>>", self._project_type_changed)
        row += 1

        mode_box = ttk.LabelFrame(tab, text="Modes", style="Section.TLabelframe", padding=10)
        mode_box.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(8, 6))
        for idx, mode in enumerate(self.modes):
            ttk.Checkbutton(mode_box, text=mode.title(), variable=self.mode_vars[mode], command=self._modes_changed).grid(
                row=idx // 3, column=idx % 3, sticky="w", padx=(0, 20), pady=3
            )
        row += 1

        agent_box = ttk.LabelFrame(tab, text="AI environments", style="Section.TLabelframe", padding=10)
        agent_box.grid(row=row, column=0, columnspan=3, sticky="ew", pady=6)
        for idx, (key, spec) in enumerate(self.agents.items()):
            ttk.Checkbutton(agent_box, text=spec["label"], variable=self.agent_vars[key]).grid(
                row=idx // 3, column=idx % 3, sticky="w", padx=(0, 20), pady=3
            )
        row += 1

        ttk.Label(tab, text="Primary mode").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        self.primary_combo = ttk.Combobox(tab, state="readonly", textvariable=self.primary_var, values=self.modes)
        self.primary_combo.grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        row += 1

        self.new_documents_listbox = self._build_documents_box(
            tab, row, "Import documents (optional)", self.new_document_paths,
            lambda: self._add_documents(self.new_document_paths, self.new_documents_listbox),
            lambda: self._remove_selected_documents(self.new_document_paths, self.new_documents_listbox),
        )
        row += 1

        ttk.Label(tab, text="Initial objective").grid(row=row, column=0, sticky="nw", padx=(0, 12), pady=6)
        self.objective_text = ScrolledText(tab, height=5, wrap="word")
        self.objective_text.grid(row=row, column=1, columnspan=2, sticky="nsew", pady=6)
        tab.rowconfigure(row, weight=1)
        row += 1

        options = ttk.Frame(tab)
        options.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(6, 8))
        ttk.Checkbutton(options, text="Initialize Git repository", variable=self.git_var).pack(side="left")
        ttk.Checkbutton(
            options,
            text="Allow deployment into a non-empty unmanaged folder",
            variable=self.allow_existing_var,
        ).pack(side="left", padx=(24, 0))
        row += 1

        action = ttk.Frame(tab)
        action.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        self.preview_label = ttk.Label(action, text="")
        self.preview_label.pack(side="left", fill="x", expand=True)
        ttk.Button(action, text="Create Project", style="Primary.TButton", command=self._create_project).pack(side="right")
        self._update_preview()

    def _build_manage_tab(self) -> None:
        tab = self.manage_tab
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(6, weight=1)
        self.manage_path_var = tk.StringVar()
        self.manage_info_var = tk.StringVar(value="Choose an existing Physics AI project.")
        self.manage_refresh_var = tk.BooleanVar(value=False)
        self.manage_reset_var = tk.BooleanVar(value=False)
        self.manage_mode_vars = {m: tk.BooleanVar(value=False) for m in self.modes}
        self.manage_agent_vars = {a: tk.BooleanVar(value=False) for a in self.agents}
        self.manage_document_paths: list[Path] = []

        ttk.Label(tab, text="Project folder").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=6)
        ttk.Entry(tab, textvariable=self.manage_path_var).grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Button(tab, text="Browse…", command=self._browse_manage).grid(row=0, column=2, sticky="ew", padx=(8, 0), pady=6)
        ttk.Button(tab, text="Load", command=self._load_manage).grid(row=0, column=3, sticky="ew", padx=(8, 0), pady=6)

        ttk.Label(tab, textvariable=self.manage_info_var, wraplength=760).grid(row=1, column=0, columnspan=4, sticky="w", pady=(4, 10))

        mode_box = ttk.LabelFrame(tab, text="Installed / add modes", style="Section.TLabelframe", padding=10)
        mode_box.grid(row=2, column=0, columnspan=4, sticky="ew", pady=6)
        for idx, mode in enumerate(self.modes):
            ttk.Checkbutton(mode_box, text=mode.title(), variable=self.manage_mode_vars[mode]).grid(
                row=idx // 3, column=idx % 3, sticky="w", padx=(0, 20), pady=3
            )

        agent_box = ttk.LabelFrame(tab, text="Installed / add AI environments", style="Section.TLabelframe", padding=10)
        agent_box.grid(row=3, column=0, columnspan=4, sticky="ew", pady=6)
        for idx, (key, spec) in enumerate(self.agents.items()):
            ttk.Checkbutton(agent_box, text=spec["label"], variable=self.manage_agent_vars[key]).grid(
                row=idx // 3, column=idx % 3, sticky="w", padx=(0, 20), pady=3
            )

        self.manage_documents_listbox = self._build_documents_box(
            tab, 4, "Import documents (optional)", self.manage_document_paths,
            lambda: self._add_documents(self.manage_document_paths, self.manage_documents_listbox),
            lambda: self._remove_selected_documents(self.manage_document_paths, self.manage_documents_listbox),
            columnspan=4,
        )

        opts = ttk.Frame(tab)
        opts.grid(row=5, column=0, columnspan=4, sticky="ew", pady=6)
        ttk.Checkbutton(opts, text="Refresh managed blueprints", variable=self.manage_refresh_var).pack(side="left")
        ttk.Checkbutton(opts, text="Reset session file", variable=self.manage_reset_var).pack(side="left", padx=(20, 0))

        self.manage_output = ScrolledText(tab, height=12, wrap="word", state="disabled")
        self.manage_output.grid(row=6, column=0, columnspan=4, sticky="nsew", pady=8)

        buttons = ttk.Frame(tab)
        buttons.grid(row=7, column=0, columnspan=4, sticky="ew")
        ttk.Button(buttons, text="Doctor", command=self._doctor).pack(side="left")
        ttk.Button(buttons, text="Open Folder", command=self._open_manage_folder).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Apply Changes", style="Primary.TButton", command=self._apply_manage).pack(side="right")

    def _build_documents_box(self, tab, row, label_text, paths, on_add, on_remove, *, columnspan=3):
        box = ttk.LabelFrame(tab, text=label_text, style="Section.TLabelframe", padding=10)
        box.grid(row=row, column=0, columnspan=columnspan, sticky="ew", pady=6)
        box.columnconfigure(0, weight=1)

        listbox = tk.Listbox(box, height=4, selectmode="extended")
        listbox.grid(row=0, column=0, sticky="ew")
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        listbox.configure(yscrollcommand=scrollbar.set)

        button_row = ttk.Frame(box)
        button_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Button(button_row, text="Add files…", command=on_add).pack(side="left")
        ttk.Button(button_row, text="Remove selected", command=on_remove).pack(side="left", padx=(8, 0))
        ttk.Label(
            button_row,
            text="Copied into documents/ when the project is created or updated; originals are left untouched.",
        ).pack(side="left", padx=(12, 0))

        self._refresh_document_listbox(paths, listbox)
        return listbox

    def _selected_project_key(self) -> str:
        value = self.type_combo.get()
        return value.split(" — ", 1)[0] if " — " in value else value

    def _title_changed(self, _event=None) -> None:
        current = self.slug_var.get().strip()
        # Keep auto-updating while the folder is empty or looks like a generated slug.
        if not current or current == getattr(self, "_last_auto_slug", ""):
            auto = slugify(self.title_var.get())
            self.slug_var.set(auto)
            self._last_auto_slug = auto
        self._update_preview()

    def _browse_parent(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.parent_var.get() or str(Path.home()))
        if chosen:
            self.parent_var.set(chosen)
            self._update_preview()

    def _add_documents(self, paths: list[Path], listbox: tk.Listbox) -> None:
        chosen = filedialog.askopenfilenames(title="Select documents to import")
        if not chosen:
            return
        existing = set(paths)
        for item in chosen:
            candidate = Path(item)
            if candidate not in existing:
                paths.append(candidate)
                existing.add(candidate)
        self._refresh_document_listbox(paths, listbox)

    def _remove_selected_documents(self, paths: list[Path], listbox: tk.Listbox) -> None:
        for index in reversed(listbox.curselection()):
            del paths[index]
        self._refresh_document_listbox(paths, listbox)

    @staticmethod
    def _refresh_document_listbox(paths: list[Path], listbox: tk.Listbox) -> None:
        listbox.delete(0, "end")
        for path in paths:
            listbox.insert("end", str(path))

    def _project_type_changed(self, _event=None) -> None:
        key = self._selected_project_key()
        self.type_var.set(key)
        primary = self.project_types[key].get("primary_mode")
        if key != "hybrid" and primary:
            for mode, var in self.mode_vars.items():
                var.set(mode == primary)
            self.primary_var.set(primary)
        self._modes_changed()

    def _modes_changed(self) -> None:
        selected = [m for m, v in self.mode_vars.items() if v.get()]
        if self.primary_var.get() not in selected and selected:
            self.primary_var.set(selected[0])
        self.primary_combo.configure(values=selected or self.modes)

    def _update_preview(self) -> None:
        parent = Path(self.parent_var.get()).expanduser() if self.parent_var.get().strip() else Path.home()
        slug = self.slug_var.get().strip() or "<project-folder>"
        self.preview_label.configure(text=f"Destination: {parent / slug}")

    def _create_project(self) -> None:
        title = self.title_var.get().strip()
        parent = self.parent_var.get().strip()
        folder = self.slug_var.get().strip()
        modes = [m for m, v in self.mode_vars.items() if v.get()]
        agents = [a for a, v in self.agent_vars.items() if v.get()]
        if not title:
            messagebox.showwarning(APP_NAME, "Enter a project title.")
            return
        if not parent or not folder:
            messagebox.showwarning(APP_NAME, "Choose a parent directory and project folder name.")
            return
        if not modes:
            messagebox.showwarning(APP_NAME, "Select at least one mode.")
            return
        if not agents:
            messagebox.showwarning(APP_NAME, "Select at least one AI environment.")
            return
        primary = self.primary_var.get()
        if primary not in modes:
            messagebox.showwarning(APP_NAME, "The primary mode must be one of the selected modes.")
            return

        project_type = self._selected_project_key()
        if len(modes) > 1:
            project_type = "hybrid"
        objective = self.objective_text.get("1.0", "end").strip()
        target = Path(parent).expanduser() / folder

        request = DeploymentRequest(
            path=target,
            title=title,
            project_type=project_type,
            agents=agents,
            modes=modes,
            primary_mode=primary,
            objective=objective,
            git_init=self.git_var.get(),
            existing_project=self.allow_existing_var.get(),
            import_documents=list(self.new_document_paths),
        )
        try:
            result = deploy_project(request, self.library_root)
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return

        self.config_data["last_parent"] = str(Path(parent).expanduser())
        self.config_data["git_init"] = self.git_var.get()
        self.config_data["last_agent"] = agents[0]
        save_config(self.config_data)
        self.new_document_paths.clear()
        self._refresh_document_listbox(self.new_document_paths, self.new_documents_listbox)

        details = [
            f"Created: {result.path}",
            f"Primary mode: {result.primary_mode}",
            "Modes: " + ", ".join(result.installed_modes),
            "AI environments: " + ", ".join(self.agents[a]["label"] for a in result.installed_agents),
        ]
        if result.notes:
            details += ["", *result.notes]
        messagebox.showinfo(APP_NAME, "\n".join(details))
        if messagebox.askyesno(APP_NAME, "Project created successfully. Open its folder now?"):
            self._open_folder(result.path)

    def _browse_manage(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.manage_path_var.get() or self.config_data.get("last_parent", str(Path.home())))
        if chosen:
            self.manage_path_var.set(chosen)
            self._load_manage()

    def _load_manage(self) -> None:
        try:
            info = inspect_project(Path(self.manage_path_var.get()))
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        for m, var in self.manage_mode_vars.items():
            var.set(m in info.modes)
        for a, var in self.manage_agent_vars.items():
            var.set(a in info.agents)
        self.manage_info_var.set(
            f"{info.title}  •  type: {info.project_type}  •  primary: {info.primary_mode}  •  "
            f"blueprints: {info.library_version or 'unknown'}  •  management is additive"
        )
        self._set_manage_output("Project loaded. Check additional modes/agents, or run Doctor.\n")

    def _apply_manage(self) -> None:
        path = Path(self.manage_path_var.get()).expanduser()
        try:
            info = inspect_project(path)
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        selected_modes = [m for m, v in self.manage_mode_vars.items() if v.get()]
        selected_agents = [a for a, v in self.manage_agent_vars.items() if v.get()]
        # Management is intentionally additive; unchecking does not remove an installed component.
        modes = list(dict.fromkeys(info.modes + selected_modes))
        agents = list(dict.fromkeys(info.agents + selected_agents))
        managed_type = "hybrid" if len(modes) > 1 else info.project_type
        try:
            result = deploy_project(
                DeploymentRequest(
                    path=path,
                    title=info.title,
                    project_type=managed_type,
                    agents=agents,
                    modes=modes,
                    primary_mode=info.primary_mode,
                    git_init=False,
                    existing_project=True,
                    refresh_blueprints=self.manage_refresh_var.get(),
                    reset_session=self.manage_reset_var.get(),
                    import_documents=list(self.manage_document_paths),
                ),
                self.library_root,
            )
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        lines = ["Changes applied successfully.", "Modes: " + ", ".join(result.installed_modes), "Agents: " + ", ".join(result.installed_agents)]
        if result.conflicts:
            lines += ["", "Refresh conflicts:", *[f"• {x}" for x in result.conflicts]]
        if result.notes:
            lines += ["", *[f"• {x}" for x in result.notes]]
        self._set_manage_output("\n".join(lines) + "\n")
        self.manage_refresh_var.set(False)
        self.manage_reset_var.set(False)
        self.manage_document_paths.clear()
        self._refresh_document_listbox(self.manage_document_paths, self.manage_documents_listbox)
        updated = inspect_project(path)
        self.manage_info_var.set(
            f"{updated.title}  •  type: {updated.project_type}  •  primary: {updated.primary_mode}  •  "
            f"blueprints: {updated.library_version or 'unknown'}  •  management is additive"
        )
        for m, var in self.manage_mode_vars.items():
            var.set(m in updated.modes)
        for a, var in self.manage_agent_vars.items():
            var.set(a in updated.agents)

    def _doctor(self) -> None:
        path = Path(self.manage_path_var.get()).expanduser()
        try:
            checks = doctor_project(path, self.library_root)
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        symbols = {"ok": "✓", "missing": "✗", "warning": "!", "modified": "~"}
        lines = [f"{symbols.get(status, '?')} {item}" for status, item in checks]
        missing = sum(1 for s, _ in checks if s == "missing")
        modified = sum(1 for s, _ in checks if s == "modified")
        if missing == 0 and modified == 0:
            summary = "Project is healthy."
        elif missing:
            summary = f"{missing} required item(s) are missing; {modified} managed file(s) are locally modified."
        else:
            summary = f"Project structure is complete; {modified} managed file(s) are locally modified."
        lines += ["", summary]
        self._set_manage_output("\n".join(lines) + "\n")

    def _set_manage_output(self, text: str) -> None:
        self.manage_output.configure(state="normal")
        self.manage_output.delete("1.0", "end")
        self.manage_output.insert("1.0", text)
        self.manage_output.configure(state="disabled")

    def _open_manage_folder(self) -> None:
        value = self.manage_path_var.get().strip()
        if value:
            self._open_folder(Path(value))

    @staticmethod
    def _open_folder(path: Path) -> None:
        path = Path(path).expanduser().resolve()
        try:
            if sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Could not open folder:\n{exc}")


def run() -> None:
    app = PhysicsAIManager()
    if app.winfo_exists():
        app.mainloop()

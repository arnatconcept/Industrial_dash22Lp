#!/usr/bin/env python3
# dj_model_builder.py
# GUI simple en Tkinter para crear modelos Django y generar serializers/views/urls.
# Prototipo: suficiente para crear modelos con campos básicos, ForeignKey y ManyToMany,
# y generar archivos Django (models.py, serializers.py, views.py, urls.py).

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import textwrap
import json
import os

FIELD_TYPES = [
    "CharField",
    "TextField",
    "IntegerField",
    "PositiveIntegerField",
    "FloatField",
    "BooleanField",
    "DateField",
    "DateTimeField",
    "TimeField",
    "ForeignKey",
    "ManyToManyField",
    "OneToOneField",
    "JSONField",
    "FileField",
    "ImageField",
    "GenericIPAddressField",
]

DEFAULT_IMPORTS = [
    "from django.db import models",
    "from django.core.exceptions import ValidationError",
    "from django.conf import settings",
]

DRF_IMPORTS = [
    "from rest_framework import serializers, viewsets, routers",
    "from rest_framework.routers import DefaultRouter",
]

EXAMPLE_SAMPLE = """# Sample minimal subset loaded from user-provided models (abbreviated)
Turno:
  - nombre: CharField(max_length=50, unique=True)
  - hora_inicio: TimeField()
  - hora_fin: TimeField()

LineaProduccion:
  - nombre: CharField(max_length=100, unique=True)
  - descripcion: TextField(blank=True, null=True)

Sector:
  - nombre: CharField(max_length=100)
  - linea: ForeignKey(LineaProduccion, on_delete=models.CASCADE, related_name='sectores')
"""

# ---- Data structures ----
class FieldDef:
    def __init__(self, name="campo", ftype="CharField", args=None, kwargs=None):
        self.name = name
        self.ftype = ftype
        self.args = args or []
        self.kwargs = kwargs or {}

    def to_code(self):
        args_part = ", ".join(self.args) if self.args else ""
        kwargs_list = []
        for k, v in self.kwargs.items():
            if isinstance(v, str) and not v.startswith(("'", '"')) and not v.endswith((')',']')):
                # Keep raw names like models.CASCADE or True/False
                kwargs_list.append(f"{k}={v}")
            else:
                kwargs_list.append(f"{k}={repr(v)}")
        kwargs_part = ", ".join(kwargs_list)
        sep = ", " if args_part and kwargs_part else ""
        return f"{self.name} = models.{self.ftype}({args_part}{sep}{kwargs_part})"

class ModelDef:
    def __init__(self, name):
        self.name = name
        self.fields = []  # list of FieldDef
        self.meta = {}    # dict for Meta options (unique_together, abstract, ordering, etc.)
        self.extra_imports = set()

    def add_field(self, field: FieldDef):
        self.fields.append(field)

    def to_code(self):
        lines = [f"class {self.name}(models.Model):"]
        if not self.fields:
            lines.append("    pass")
        else:
            for f in self.fields:
                code = f.to_code()
                lines.append("    " + code)
        # Meta
        if self.meta:
            lines.append("")
            lines.append("    class Meta:")
            for k, v in self.meta.items():
                # v could be list, tuple, bool, string
                if isinstance(v, (list, tuple)):
                    lines.append(f"        {k} = {repr(v)}")
                else:
                    lines.append(f"        {k} = {repr(v)}")
        lines.append("")
        return "\n".join(lines)

# ---- Generator functions ----

def generate_models_py(models_list):
    imports = set(DEFAULT_IMPORTS)
    body = []
    for m in models_list:
        body.append(m.to_code())
    header = "\n".join(sorted(imports)) + "\n\n\n"
    return header + "\n\n".join(body)

def generate_serializers_py(models_list, auth_model_name=None):
    lines = []
    lines.extend([
        "from rest_framework import serializers",
        "from .models import " + ", ".join(m.name for m in models_list),
        "",
    ])
    for m in models_list:
        lines.append(f"class {m.name}Serializer(serializers.ModelSerializer):")
        lines.append("    class Meta:")
        lines.append(f"        model = {m.name}")
        lines.append("        fields = '__all__'")
        lines.append("")
    return "\n".join(lines)

def generate_views_py(models_list):
    lines = []
    lines.extend([
        "from rest_framework import viewsets",
        "from .models import " + ", ".join(m.name for m in models_list),
        "from .serializers import " + ", ".join(f"{m.name}Serializer" for m in models_list),
        "",
    ])
    for m in models_list:
        lines.append(f"class {m.name}ViewSet(viewsets.ModelViewSet):")
        lines.append(f"    queryset = {m.name}.objects.all()")
        lines.append(f"    serializer_class = {m.name}Serializer")
        lines.append("")
    return "\n".join(lines)

def generate_urls_py(models_list):
    lines = []
    lines.append("from rest_framework.routers import DefaultRouter")
    lines.append("from .views import " + ", ".join(f"{m.name}ViewSet" for m in models_list))
    lines.append("")
    lines.append("router = DefaultRouter()")
    for m in models_list:
        route = camel_to_snake(m.name)
        lines.append(f"router.register(r'{route}', {m.name}ViewSet)")
    lines.append("")
    lines.append("urlpatterns = router.urls")
    lines.append("")
    return "\n".join(lines)

def camel_to_snake(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

# ---- GUI ----

class App:
    def __init__(self, root):
        self.root = root
        root.title("Django Model Builder (Tkinter)")
        self.models = []  # list of ModelDef

        # Left: listbox models
        left = ttk.Frame(root, padding=6)
        left.grid(row=0, column=0, sticky="ns")
        ttk.Label(left, text="Models").pack(anchor="w")
        self.model_listbox = tk.Listbox(left, width=28, height=20)
        self.model_listbox.pack(side="left", fill="y")
        self.model_listbox.bind("<<ListboxSelect>>", self.on_model_select)
        lb_buttons = ttk.Frame(left)
        lb_buttons.pack(fill="x", pady=6)
        ttk.Button(lb_buttons, text="Add Model", command=self.add_model_dialog).pack(side="left", padx=2)
        ttk.Button(lb_buttons, text="Remove", command=self.remove_model).pack(side="left", padx=2)
        ttk.Button(lb_buttons, text="Load Sample", command=self.load_sample).pack(side="left", padx=2)

        # Middle: model editor
        mid = ttk.Frame(root, padding=6)
        mid.grid(row=0, column=1, sticky="nsew")
        root.columnconfigure(1, weight=1)
        ttk.Label(mid, text="Model Editor").grid(row=0, column=0, sticky="w")
        self.model_name_var = tk.StringVar()
        ttk.Entry(mid, textvariable=self.model_name_var, width=40).grid(row=1, column=0, sticky="w")
        ttk.Button(mid, text="Rename", command=self.rename_model).grid(row=1, column=1, padx=6)

        # Fields tree
        self.fields_tree = ttk.Treeview(mid, columns=("type", "opts"), show="headings", height=12)
        self.fields_tree.heading("type", text="Type")
        self.fields_tree.heading("opts", text="Options")
        self.fields_tree.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=6)
        mid.rowconfigure(2, weight=1)
        # Field controls
        fctrl = ttk.Frame(mid)
        fctrl.grid(row=3, column=0, sticky="w", pady=4)
        ttk.Button(fctrl, text="Add Field", command=self.add_field_dialog).pack(side="left", padx=2)
        ttk.Button(fctrl, text="Edit Field", command=self.edit_selected_field).pack(side="left", padx=2)
        ttk.Button(fctrl, text="Remove Field", command=self.remove_selected_field).pack(side="left", padx=2)

        # Right: generated code preview + actions
        right = ttk.Frame(root, padding=6)
        right.grid(row=0, column=2, sticky="nsew")
        root.columnconfigure(2, weight=1)
        ttk.Label(right, text="Generated Files").pack(anchor="w")
        self.preview_nb = ttk.Notebook(right)
        self.models_preview = tk.Text(self.preview_nb, width=80, height=20)
        self.serializers_preview = tk.Text(self.preview_nb, width=80, height=20)
        self.views_preview = tk.Text(self.preview_nb, width=80, height=20)
        self.urls_preview = tk.Text(self.preview_nb, width=80, height=10)
        self.preview_nb.add(self.models_preview, text="models.py")
        self.preview_nb.add(self.serializers_preview, text="serializers.py")
        self.preview_nb.add(self.views_preview, text="views.py")
        self.preview_nb.add(self.urls_preview, text="urls.py")
        self.preview_nb.pack(fill="both", expand=True)

        gen_frame = ttk.Frame(right)
        gen_frame.pack(fill="x", pady=6)
        ttk.Button(gen_frame, text="Generate Previews", command=self.generate_previews).pack(side="left", padx=4)
        ttk.Button(gen_frame, text="Save Files...", command=self.save_files).pack(side="left", padx=4)
        ttk.Button(gen_frame, text="Export JSON", command=self.export_json).pack(side="left", padx=4)
        ttk.Button(gen_frame, text="Import JSON", command=self.import_json).pack(side="left", padx=4)

        # Initialize with a default model
        self.add_model("Turno")
        self.select_model_by_name("Turno")
        # Fill with sample content if desired later

    # ---- Model management ----
    def add_model(self, name=None):
        if not name:
            name = self.simple_input("New model name", "Model name:")
            if not name:
                return
        if any(m.name == name for m in self.models):
            messagebox.showerror("Error", "Ya existe un modelo con ese nombre.")
            return
        m = ModelDef(name)
        self.models.append(m)
        self.model_listbox.insert("end", name)
        self.model_listbox.selection_clear(0, "end")
        idx = self.model_listbox.size() - 1
        self.model_listbox.selection_set(idx)
        self.on_model_select()

    def add_model_dialog(self):
        self.add_model(None)

    def remove_model(self):
        sel = self.model_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        name = self.model_listbox.get(idx)
        if messagebox.askyesno("Confirm", f"Eliminar modelo {name}?"):
            self.model_listbox.delete(idx)
            del self.models[idx]
            # clear editor
            self.fields_tree.delete(*self.fields_tree.get_children())
            self.model_name_var.set("")
            self.generate_previews()

    def select_model_by_name(self, name):
        for i in range(self.model_listbox.size()):
            if self.model_listbox.get(i) == name:
                self.model_listbox.selection_clear(0, "end")
                self.model_listbox.selection_set(i)
                self.on_model_select()
                return

    def on_model_select(self, event=None):
        sel = self.model_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        m = self.models[idx]
        self.model_name_var.set(m.name)
        # populate fields
        self.fields_tree.delete(*self.fields_tree.get_children())
        for f in m.fields:
            opts = []
            for k,v in f.kwargs.items():
                opts.append(f"{k}={v}")
            if f.args:
                opts.insert(0, ", ".join(f.args))
            opts_text = "; ".join(opts)
            self.fields_tree.insert("", "end", values=(f.ftype, opts_text), text=f.name, iid=f.name)
        self.generate_previews()

    def rename_model(self):
        sel = self.model_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        newname = self.model_name_var.get().strip()
        if not newname:
            messagebox.showerror("Error", "Nombre vacío")
            return
        if any(m.name == newname and m is not self.models[idx] for m in self.models):
            messagebox.showerror("Error", "Ya existe un modelo con ese nombre.")
            return
        self.models[idx].name = newname
        self.model_listbox.delete(idx)
        self.model_listbox.insert(idx, newname)
        self.model_listbox.selection_set(idx)
        self.on_model_select()

    # ---- Field dialogs ----
    def add_field_dialog(self):
        sel = self.model_listbox.curselection()
        if not sel:
            messagebox.showerror("Error", "Selecciona un modelo primero.")
            return
        idx = sel[0]
        dlg = FieldDialog(self.root, self.models, None)
        self.root.wait_window(dlg.top)
        if dlg.result:
            self.models[idx].add_field(dlg.result)
            self.on_model_select()

    def edit_selected_field(self):
        sel = self.model_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        model = self.models[idx]
        sel_items = self.fields_tree.selection()
        if not sel_items:
            messagebox.showinfo("Info", "Selecciona un campo.")
            return
        fname = sel_items[0]
        field = next((f for f in model.fields if f.name == fname), None)
        if not field:
            return
        dlg = FieldDialog(self.root, self.models, field)
        self.root.wait_window(dlg.top)
        if dlg.result:
            # replace field
            for i,f in enumerate(model.fields):
                if f.name == fname:
                    model.fields[i] = dlg.result
                    break
            self.on_model_select()

    def remove_selected_field(self):
        sel = self.model_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        model = self.models[idx]
        sel_items = self.fields_tree.selection()
        if not sel_items:
            return
        fname = sel_items[0]
        model.fields = [f for f in model.fields if f.name != fname]
        self.on_model_select()

    # ---- Previews and IO ----
    def generate_previews(self):
        models_py = generate_models_py(self.models)
        serializers_py = generate_serializers_py(self.models)
        views_py = generate_views_py(self.models)
        urls_py = generate_urls_py(self.models)

        for widget, content in [
            (self.models_preview, models_py),
            (self.serializers_preview, serializers_py),
            (self.views_preview, views_py),
            (self.urls_preview, urls_py),
        ]:
            widget.config(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", content)
            widget.config(state="disabled")

    def save_files(self):
        if not self.models:
            messagebox.showerror("Error", "No hay modelos para guardar.")
            return
        folder = filedialog.askdirectory(title="Seleccionar carpeta para guardar archivos")
        if not folder:
            return
        files = {
            "models.py": generate_models_py(self.models),
            "serializers.py": generate_serializers_py(self.models),
            "views.py": generate_views_py(self.models),
            "urls.py": generate_urls_py(self.models),
        }
        for fname, content in files.items():
            path = os.path.join(folder, fname)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        messagebox.showinfo("Guardado", f"Archivos guardados en {folder}")

    def export_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not path:
            return
        data = []
        for m in self.models:
            mdata = {"name": m.name, "fields": [] , "meta": m.meta}
            for f in m.fields:
                mdata["fields"].append({
                    "name": f.name,
                    "ftype": f.ftype,
                    "args": f.args,
                    "kwargs": f.kwargs
                })
            data.append(mdata)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Export", f"Exportado a {path}")

    def import_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.models.clear()
        self.model_listbox.delete(0, "end")
        for mdata in data:
            m = ModelDef(mdata["name"])
            m.meta = mdata.get("meta", {})
            for fd in mdata.get("fields", []):
                f = FieldDef(fd["name"], fd["ftype"], fd.get("args", []), fd.get("kwargs", {}))
                m.add_field(f)
            self.models.append(m)
            self.model_listbox.insert("end", m.name)
        self.on_model_select()
        self.generate_previews()

    def load_sample(self):
        # Simple parser for the EXAMPLE_SAMPLE string; creates 3 models as demo
        # For real use, you can paste more detailed JSON via Import JSON
        self.models.clear()
        self.model_listbox.delete(0, "end")
        # Minimal sample mapping
        t = ModelDef("Turno")
        t.add_field(FieldDef("nombre", "CharField", args=[], kwargs={"max_length":50, "unique":True}))
        t.add_field(FieldDef("hora_inicio", "TimeField"))
        t.add_field(FieldDef("hora_fin", "TimeField"))
        lp = ModelDef("LineaProduccion")
        lp.add_field(FieldDef("nombre", "CharField", kwargs={"max_length":100, "unique":True}))
        lp.add_field(FieldDef("descripcion", "TextField", kwargs={"blank":True, "null":True}))
        s = ModelDef("Sector")
        s.add_field(FieldDef("nombre", "CharField", kwargs={"max_length":100}))
        s.add_field(FieldDef("linea", "ForeignKey", args=["'LineaProduccion'"], kwargs={"on_delete":"models.CASCADE", "related_name":"'sectores'"}))
        for m in (t, lp, s):
            self.models.append(m)
            self.model_listbox.insert("end", m.name)
        self.select_model_by_name("Turno")
        self.generate_previews()

    # ---- utilities ----
    def simple_input(self, title, prompt):
        win = tk.Toplevel(self.root)
        win.transient(self.root)
        win.grab_set()
        ttk.Label(win, text=prompt).pack(padx=10, pady=6)
        v = tk.StringVar()
        e = ttk.Entry(win, textvariable=v)
        e.pack(padx=10, pady=6)
        v.set("")
        res = {"val": None}
        def ok():
            res["val"] = v.get().strip()
            win.destroy()
        def cancel():
            win.destroy()
        b = ttk.Frame(win)
        b.pack(pady=6)
        ttk.Button(b, text="OK", command=ok).pack(side="left", padx=6)
        ttk.Button(b, text="Cancel", command=cancel).pack(side="left", padx=6)
        self.root.wait_window(win)
        return res["val"]

# ---- Field Dialog ----

class FieldDialog:
    def __init__(self, parent, models_list, field: FieldDef or None):
        self.parent = parent
        self.models_list = models_list
        self.result = None
        top = self.top = tk.Toplevel(parent)
        top.transient(parent)
        top.grab_set()
        top.title("Field Editor")
        # name
        ttk.Label(top, text="Field name").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.name_var = tk.StringVar(value=(field.name if field else "campo"))
        ttk.Entry(top, textvariable=self.name_var).grid(row=0, column=1, padx=6, pady=4)
        # type
        ttk.Label(top, text="Field Type").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.type_var = tk.StringVar(value=(field.ftype if field else "CharField"))
        cb = ttk.Combobox(top, textvariable=self.type_var, values=FIELD_TYPES, state="readonly")
        cb.grid(row=1, column=1, padx=6, pady=4)
        # args (comma separated)
        ttk.Label(top, text="Args (comma separated)").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        args_text = ", ".join(field.args) if (field and field.args) else ""
        self.args_var = tk.StringVar(value=args_text)
        ttk.Entry(top, textvariable=self.args_var).grid(row=2, column=1, padx=6, pady=4)
        # kwargs as JSON
        ttk.Label(top, text="Options (JSON)")
        ttk.Label(top, text="(ej: {\"max_length\":100, \"blank\":True})").grid(row=3, column=0, sticky="w", padx=6)
        kwargs_text = json.dumps(field.kwargs, ensure_ascii=False) if (field and field.kwargs) else "{}"
        self.kwargs_text = tk.Text(top, height=4, width=40)
        self.kwargs_text.grid(row=4, column=0, columnspan=2, padx=6)
        self.kwargs_text.insert("1.0", kwargs_text)
        btns = ttk.Frame(top)
        btns.grid(row=5, column=0, columnspan=2, pady=6)
        ttk.Button(btns, text="OK", command=self.on_ok).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel", command=self.on_cancel).pack(side="left", padx=6)
        # Prepopulate convenience for FK selecting existing model names
        ttk.Button(top, text="Insert FK to model...", command=self.insert_fk_helper).grid(row=6, column=0, columnspan=2, pady=6)

    def insert_fk_helper(self):
        # choose existing model
        names = [m.name for m in self.models_list]
        if not names:
            messagebox.showinfo("Info", "No hay modelos definidos aun.")
            return
        sel = simple_choice_dialog(self.top, "Select target model", names)
        if sel:
            # automatically set type and args
            self.type_var.set("ForeignKey")
            self.args_var.set(f"'{sel}'")
            # add default kwargs if blank
            try:
                kwargs = json.loads(self.kwargs_text.get("1.0", "end").strip() or "{}")
            except Exception:
                kwargs = {}
            if "on_delete" not in kwargs:
                kwargs["on_delete"] = "models.CASCADE"
            if "related_name" not in kwargs:
                kwargs["related_name"] = f"'{camel_to_snake(sel)}s'"
            self.kwargs_text.delete("1.0", "end")
            self.kwargs_text.insert("1.0", json.dumps(kwargs))

    def on_ok(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Nombre vacío")
            return
        ftype = self.type_var.get().strip()
        args_raw = self.args_var.get().strip()
        args = [a.strip() for a in args_raw.split(",")] if args_raw else []
        try:
            kwargs_text = self.kwargs_text.get("1.0", "end").strip()
            kwargs = json.loads(kwargs_text) if kwargs_text else {}
        except Exception as e:
            messagebox.showerror("Error", f"JSON inválido en Options: {e}")
            return
        # Build FieldDef; allow keeping models.CASCADE raw by leaving as string "models.CASCADE"
        f = FieldDef(name, ftype, args, kwargs)
        self.result = f
        self.top.destroy()

    def on_cancel(self):
        self.top.destroy()

def simple_choice_dialog(parent, title, options):
    top = tk.Toplevel(parent)
    top.transient(parent)
    top.grab_set()
    top.title(title)
    v = tk.StringVar()
    lb = tk.Listbox(top)
    for o in options:
        lb.insert("end", o)
    lb.pack(padx=6, pady=6)
    res = {"val": None}
    def ok():
        sel = lb.curselection()
        if not sel:
            return
        res["val"] = lb.get(sel[0])
        top.destroy()
    def cancel():
        top.destroy()
    b = ttk.Frame(top)
    b.pack(pady=6)
    ttk.Button(b, text="OK", command=ok).pack(side="left", padx=6)
    ttk.Button(b, text="Cancel", command=cancel).pack(side="left", padx=6)
    parent.wait_window(top)
    return res["val"]

# ---- Main ----
def main():
    root = tk.Tk()
    app = App(root)
    root.geometry("1200x700")
    root.mainloop()

if __name__ == "__main__":
    main()

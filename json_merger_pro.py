import sys
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, Menu
import os
from datetime import datetime
import queue


# ================================================================
# INSTALADOR ROBUSTO
# ================================================================
def check_packages():
    """Devuelve lista de paquetes que faltan."""
    missing = []
    for pkg in ["customtkinter", "pyperclip"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


def try_install(pkg: str) -> tuple:
    strategies = [
        [sys.executable, "-m", "pip", "install", pkg],
        [sys.executable, "-m", "pip", "install", pkg, "--user"],
        [sys.executable, "-m", "pip", "install", pkg, "--break-system-packages"],
    ]
    last_err = ""
    for cmd in strategies:
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                return True, ""
            last_err = result.stderr.strip() or result.stdout.strip()
        except subprocess.TimeoutExpired:
            last_err = "Tiempo de espera agotado (sin conexion a internet?)"
        except FileNotFoundError:
            last_err = "No se encontro pip en el sistema."
        except Exception as e:
            last_err = str(e)
    return False, last_err


def install_window(missing: list) -> bool:
    log_queue    = queue.Queue()
    status_queue = queue.Queue()
    done_queue   = queue.Queue()

    root = tk.Tk()
    root.title("JSON Merger — Instalando dependencias")
    root.geometry("560x420")
    root.resizable(False, False)
    root.configure(bg="#1a1a2e")

    tk.Label(root, text="Preparando JSON Merger Pro",
             font=("Arial", 13, "bold"),
             bg="#1a1a2e", fg="#e0e0e0").pack(pady=(20, 4))

    tk.Label(root, text=f"Paquetes necesarios: {', '.join(missing)}",
             font=("Consolas", 10),
             bg="#1a1a2e", fg="#00b894").pack(pady=(0, 12))

    progress = ttk.Progressbar(root, length=480, mode="indeterminate")
    progress.pack(pady=6)
    progress.start(10)

    status_var = tk.StringVar(value="Iniciando...")
    tk.Label(root, textvariable=status_var,
             font=("Arial", 10), bg="#1a1a2e", fg="#aaaaaa").pack()

    tk.Label(root, text="Registro:", font=("Arial", 9),
             bg="#1a1a2e", fg="#666666").pack(anchor="w", padx=40, pady=(12, 2))

    log_box = scrolledtext.ScrolledText(
        root, height=8, font=("Consolas", 9),
        bg="#0d0d1a", fg="#cccccc", insertbackground="white",
        state="disabled", borderwidth=0)
    log_box.pack(padx=40, fill="x")

    manual_frame = tk.Frame(root, bg="#1a1a2e")
    manual_frame.pack(pady=8, fill="x", padx=40)

    def log_append(msg: str):
        log_box.configure(state="normal")
        log_box.insert("end", msg + "\n")
        log_box.see("end")
        log_box.configure(state="disabled")

    def do_install():
        success = True
        for pkg in missing:
            status_queue.put(f"Instalando {pkg}...")
            log_queue.put(f">> pip install {pkg}")
            ok, err = try_install(pkg)
            if ok:
                log_queue.put(f"   OK: {pkg} instalado correctamente.")
            else:
                success = False
                log_queue.put(f"   ERROR al instalar {pkg}:")
                for line in err.splitlines():
                    log_queue.put(f"     {line}")
        done_queue.put(success)

    threading.Thread(target=do_install, daemon=True).start()

    success_result = [None]

    def poll():
        while not status_queue.empty():
            status_var.set(status_queue.get_nowait())
        while not log_queue.empty():
            log_append(log_queue.get_nowait())

        if not done_queue.empty():
            success = done_queue.get_nowait()
            success_result[0] = success
            progress.stop()

            if success:
                status_var.set("Instalacion completada. Iniciando aplicacion...")
                log_append("\nTodo listo. La aplicacion se abrira en un momento.")
                root.after(1200, root.destroy)
            else:
                status_var.set("La instalacion automatica fallo.")
                log_append("\n" + "=" * 55)
                log_append("INSTRUCCIONES PARA INSTALAR MANUALMENTE:")
                log_append("  Abre una terminal y ejecuta:")
                log_append("")
                for pkg in missing:
                    log_append(f"    pip install {pkg}")
                log_append("")
                for pkg in missing:
                    log_append(f"    pip install {pkg} --user")
                log_append("=" * 55)

                tk.Label(manual_frame,
                         text="Copia el comando de arriba en una terminal y vuelve a ejecutar este archivo.",
                         font=("Arial", 9), bg="#1a1a2e", fg="#f39c12",
                         wraplength=480, justify="left").pack(anchor="w")
                tk.Button(manual_frame, text="Cerrar",
                          command=root.destroy,
                          bg="#e74c3c", fg="white",
                          font=("Arial", 10, "bold"),
                          relief="flat", padx=20, pady=6).pack(pady=8)
            return

        root.after(50, poll)

    root.after(50, poll)
    root.mainloop()
    return success_result[0] is True


def ensure_dependencies() -> bool:
    missing = check_packages()
    if not missing:
        return True
    return install_window(missing)


if not ensure_dependencies():
    sys.exit(1)


# ================================================================
# IMPORTACIONES PRINCIPALES
# ================================================================
import webbrowser
import customtkinter as ctk
import json
import pyperclip
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

GITHUB_URL = "https://github.com/aisurf3r/Json-Merger"


# ================================================================
# TOOLTIP UNIVERSAL
# ================================================================
class Tooltip:
    DELAY_MS = 600
    WRAP_PX  = 270

    def __init__(self, widget, text: str):
        self._widget  = widget
        self._text    = text
        self._tip_win = None
        self._job_id  = None
        self._last_ev = None
        self._polling = False
        self._inside  = False

        try:
            widget.bind("<Enter>",  self._schedule,  add="+")
            widget.bind("<Leave>",  self._cancel,    add="+")
            widget.bind("<Motion>", self._on_motion, add="+")
        except (NotImplementedError, tk.TclError):
            self._bind_via_hover(widget)

    def _bind_via_hover(self, widget):
        self._widget_ref = widget
        self._polling    = True
        widget.after(100, self._poll_hover)

    def _poll_hover(self):
        if not self._polling:
            return
        try:
            wx = self._widget_ref.winfo_rootx()
            wy = self._widget_ref.winfo_rooty()
            ww = self._widget_ref.winfo_width()
            wh = self._widget_ref.winfo_height()
            mx = self._widget_ref.winfo_pointerx()
            my = self._widget_ref.winfo_pointery()
            inside = wx <= mx <= wx + ww and wy <= my <= wy + wh
            if inside and not self._inside:
                self._inside  = True
                self._last_ev = None
                self._schedule()
            elif not inside and self._inside:
                self._inside = False
                self._cancel()
            self._widget_ref.after(120, self._poll_hover)
        except tk.TclError:
            self._polling = False

    def _screen_xy(self):
        ev = self._last_ev
        if ev:
            return ev.x_root, ev.y_root
        w = self._widget
        return w.winfo_rootx() + 20, w.winfo_rooty() + w.winfo_height() + 4

    def _schedule(self, event=None):
        self._cancel_job()
        if event:
            self._last_ev = event
        self._job_id = self._widget.after(self.DELAY_MS, self._show)

    def _on_motion(self, event):
        self._last_ev = event

    def _cancel(self, event=None):
        self._cancel_job()
        self._hide()

    def _cancel_job(self):
        if self._job_id:
            try:
                self._widget.after_cancel(self._job_id)
            except tk.TclError:
                pass
            self._job_id = None

    def _show(self):
        self._hide()
        try:
            x, y = self._screen_xy()
        except tk.TclError:
            return
        win = tk.Toplevel(self._widget)
        win.wm_overrideredirect(True)
        win.wm_attributes("-topmost", True)
        win.wm_geometry(f"+{x + 16}+{y + 20}")
        outer = tk.Frame(win, bg="#3a3a3a", padx=1, pady=1)
        outer.pack()
        tk.Label(outer, text=self._text, justify="left",
                 bg="#2b2b2b", fg="#e0e0e0",
                 font=("Segoe UI", 9),
                 wraplength=self.WRAP_PX,
                 padx=10, pady=7).pack()
        self._tip_win = win

    def _hide(self):
        if self._tip_win:
            try:
                self._tip_win.destroy()
            except Exception:
                pass
            self._tip_win = None


def tip(widget, text: str) -> Tooltip:
    return Tooltip(widget, text)


# ================================================================
# VENTANA "ACERCA DE"
# ================================================================
class AboutWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Acerca de JSON Merger Pro")
        self.geometry("420x310")
        self.resizable(False, False)
        self.after(50, self._bring_to_front)

        ctk.CTkLabel(self, text="JSON Merger Pro",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(28, 4))

        ctk.CTkLabel(self, text="v1.0  ·  by Aisurf3r",
                     font=ctk.CTkFont(size=13), text_color="#a0a0a0").pack(pady=(0, 18))

        desc = (
            "Herramienta para combinar, filtrar y deduplicar\n"
            "archivos JSON de forma rapida y sencilla.\n\n"
            "Soporta fusion en array o en objeto, exportacion\n"
            "a CSV y copia directa al portapapeles."
        )
        ctk.CTkLabel(self, text=desc,
                     font=ctk.CTkFont(size=13),
                     justify="center",
                     wraplength=360).pack(pady=(0, 22))

        ctk.CTkFrame(self, height=1, fg_color=("#c0c0c0", "#3a3a3a")).pack(
            fill="x", padx=30, pady=(0, 18))

        gh_btn = ctk.CTkButton(
            self,
            text="⭐  Ver en GitHub",
            command=lambda: webbrowser.open(GITHUB_URL),
            fg_color="#24292e", hover_color="#3a3a3a",
            height=38, width=200,
            font=ctk.CTkFont(size=13))
        gh_btn.pack(pady=(0, 20))
        tip(gh_btn, "Abre el repositorio en tu navegador.\ngithub.com/aisurf3r/Json-Merger")

    def _bring_to_front(self):
        self.lift()
        self.focus_force()


# ================================================================
# VENTANA DE DEDUPLICACION
# ================================================================
class DeduplicateWindow(ctk.CTkToplevel):
    def __init__(self, parent, data: list):
        super().__init__(parent)
        self.title("Deduplicar Registros")
        self.geometry("540x460")
        self.resizable(False, False)
        self.result = None
        self.data   = data
        seen_keys: dict = {}
        for item in data:
            if isinstance(item, dict):
                for k in item.keys():
                    seen_keys[k] = None
        self.keys = list(seen_keys.keys())

        self.after(50, self._bring_to_front)

        ctk.CTkLabel(self, text="Deduplicar Registros",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        ctk.CTkLabel(self, text=f"Registros antes de deduplicar: {len(data)}",
                     font=ctk.CTkFont(size=13)).pack(pady=5)
        ctk.CTkLabel(self, text="Modo de deduplicacion:",
                     font=ctk.CTkFont(size=13)).pack(anchor="w", padx=30, pady=(15, 5))

        self.mode_var = ctk.StringVar(value="exact")

        rb1 = ctk.CTkRadioButton(self,
                                  text="Exacto — el registro completo debe ser identico",
                                  variable=self.mode_var, value="exact",
                                  command=self.update_key_state)
        rb1.pack(anchor="w", padx=50, pady=3)
        tip(rb1, "Elimina filas donde TODOS los campos son iguales.\nUtil cuando los archivos se solapan completamente.")

        rb2 = ctk.CTkRadioButton(self,
                                  text="Por clave — solo compara un campo concreto",
                                  variable=self.mode_var, value="key",
                                  command=self.update_key_state)
        rb2.pack(anchor="w", padx=50, pady=3)
        tip(rb2, "Elimina filas con el mismo valor en el campo elegido,\naunque el resto de campos sean distintos.\nEj: deduplicar por 'id' o 'email'.")

        ctk.CTkLabel(self, text="Clave para deduplicar:",
                     font=ctk.CTkFont(size=13)).pack(anchor="w", padx=30, pady=(15, 5))

        self.key_combo = ctk.CTkComboBox(
            self, values=self.keys if self.keys else ["(sin claves)"],
            state="disabled", width=300)
        self.key_combo.pack(padx=30, pady=5)
        if self.keys:
            self.key_combo.set(self.keys[0])
        tip(self.key_combo, "Selecciona el campo JSON cuyo valor se usara\npara detectar duplicados.")

        self.preview_label = ctk.CTkLabel(self, text="",
                                          font=ctk.CTkFont(size=13),
                                          text_color="#00b894")
        self.preview_label.pack(pady=10)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20, padx=30, fill="x")

        b_prev = ctk.CTkButton(btn_frame, text="Previsualizar",
                               command=self.preview, width=180)
        b_prev.pack(side="left", padx=5, expand=True, fill="x")
        tip(b_prev, "Muestra cuantos duplicados se eliminarian\nsin aplicar los cambios todavia.")

        b_apply = ctk.CTkButton(btn_frame, text="Aplicar",
                                command=self.apply,
                                fg_color="#00b894", hover_color="#00a085", width=180)
        b_apply.pack(side="left", padx=5, expand=True, fill="x")
        tip(b_apply, "Aplica la deduplicacion y vuelve a la pantalla\nprincipal con los datos ya limpios.")

        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy,
                      fg_color="#e74c3c", hover_color="#c0392b", width=120
                      ).pack(side="left", padx=5)

    def _bring_to_front(self):
        self.lift()
        self.focus_force()

    def update_key_state(self):
        state = "normal" if self.mode_var.get() == "key" and self.keys else "disabled"
        self.key_combo.configure(state=state)

    def _safe_hash(self, item) -> str:
        """
        Genera una clave de hash robusta para cualquier valor JSON.
        - Dicts y listas: json.dumps con sort_keys para orden canónico.
        - Primitivos (str, int, float, bool, None): json.dumps sin sort_keys
          (más rápido, no hay claves que ordenar).
        - Tipos no serializables (rarísimo en JSONs reales): repr() + type()
          para evitar colisiones entre tipos distintos con el mismo repr.
        """
        try:
            if isinstance(item, (dict, list)):
                return json.dumps(item, sort_keys=True, ensure_ascii=False)
            else:
                return json.dumps(item, ensure_ascii=False)
        except (TypeError, ValueError):
            # Fallback: incluye el tipo para evitar colisiones (ej: 1 vs "1")
            return repr(item) + str(type(item))

    def _deduplicate(self):
        if self.mode_var.get() == "exact":
            seen = set()
            out  = []
            for item in self.data:
                k = self._safe_hash(item)
                if k not in seen:
                    seen.add(k)
                    out.append(item)
            return out
        else:
            field = self.key_combo.get()
            if not field or field == "(sin claves)":
                messagebox.showwarning("Sin clave",
                    "Selecciona una clave valida para deduplicar.")
                return None
            seen              = set()
            out               = []
            missing_key_items = []
            for item in self.data:
                if not isinstance(item, dict) or field not in item:
                    missing_key_items.append(item)
                    continue
                val_key = self._safe_hash(item[field])
                if val_key not in seen:
                    seen.add(val_key)
                    out.append(item)
            # Los registros sin la clave se añaden al final (comportamiento documentado)
            out.extend(missing_key_items)
            return out

    def preview(self):
        d = self._deduplicate()
        if d is not None:
            eliminados = len(self.data) - len(d)
            self.preview_label.configure(
                text=f"Se eliminarian {eliminados} duplicados  →  quedarian {len(d)} registros")

    def apply(self):
        result = self._deduplicate()
        if result is None:
            return
        self.result = result
        self.destroy()


# ================================================================
# VENTANA DE FILTRADO
# ================================================================
class FilterWindow(ctk.CTkToplevel):
    OPERATORS = ["igual a", "contiene", "empieza con", "termina con",
                 "mayor que", "menor que", "existe"]
    OP_TIPS   = {
        "igual a":     "El campo debe ser exactamente igual al valor escrito.",
        "contiene":    "El campo debe incluir el valor (sin distinguir mayusculas).",
        "empieza con": "El campo debe comenzar con el valor escrito.",
        "termina con": "El campo debe terminar con el valor escrito.",
        "mayor que":   "El campo numerico debe ser mayor que el valor escrito.",
        "menor que":   "El campo numerico debe ser menor que el valor escrito.",
        "existe":      "Solo muestra registros que tengan la clave,\nsea cual sea su valor.",
    }

    def __init__(self, parent, data: list):
        super().__init__(parent)
        self.title("Filtrar Registros")
        self.geometry("510x490")
        self.resizable(False, False)
        self.result = None
        self.data   = data
        seen_keys: dict = {}
        for item in data:
            if isinstance(item, dict):
                for k in item.keys():
                    seen_keys[k] = None
        self.keys = list(seen_keys.keys())

        self.after(50, self._bring_to_front)

        ctk.CTkLabel(self, text="Filtrar Registros",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        ctk.CTkLabel(self, text=f"Registros disponibles: {len(data)}",
                     font=ctk.CTkFont(size=13)).pack(pady=5)

        form = ctk.CTkFrame(self)
        form.pack(padx=30, pady=10, fill="x")

        ctk.CTkLabel(form, text="Clave:", font=ctk.CTkFont(size=13)
                     ).grid(row=0, column=0, sticky="w", pady=6, padx=10)
        self.key_combo = ctk.CTkComboBox(
            form,
            values=self.keys if self.keys else ["(sin claves)"],
            width=290,
            command=self._on_key_change)
        self.key_combo.grid(row=0, column=1, pady=6, padx=10)
        if self.keys:
            self.key_combo.set(self.keys[0])
        tip(self.key_combo, "El campo del JSON sobre el que quieres filtrar.\nEj: 'nombre', 'edad', 'ciudad'.")

        ctk.CTkLabel(form, text="Operador:", font=ctk.CTkFont(size=13)
                     ).grid(row=1, column=0, sticky="w", pady=6, padx=10)
        self.op_combo = ctk.CTkComboBox(
            form, values=self.OPERATORS, width=290,
            command=self._update_op_tip)
        self.op_combo.set("igual a")
        self.op_combo.grid(row=1, column=1, pady=6, padx=10)

        self.op_tip_lbl = ctk.CTkLabel(
            form, text=self.OP_TIPS["igual a"],
            font=ctk.CTkFont(size=11), text_color="#a0a0a0", wraplength=340)
        self.op_tip_lbl.grid(row=2, column=0, columnspan=2,
                              sticky="w", pady=(0, 4), padx=10)

        ctk.CTkLabel(form, text="Valor:", font=ctk.CTkFont(size=13)
                     ).grid(row=3, column=0, sticky="w", pady=6, padx=10)
        self.value_entry = ctk.CTkEntry(form, width=290,
                                        placeholder_text="Valor a buscar")
        self.value_entry.grid(row=3, column=1, pady=6, padx=10)
        tip(self.value_entry,
            "Escribe el valor con el que comparar.\nNo hace falta para el operador 'existe'.")

        self.field_type_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=11), text_color="#a0a0a0")
        self.field_type_label.pack(pady=(2, 0))
        self._update_field_type_hint()

        # ── FIX: label de aviso para campos no numéricos ──────────
        self.numeric_warn_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=11), text_color="#e74c3c")
        self.numeric_warn_label.pack(pady=(0, 2))

        self.result_label = ctk.CTkLabel(self, text="",
                                          font=ctk.CTkFont(size=13),
                                          text_color="#00b894")
        self.result_label.pack(pady=6)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15, padx=30, fill="x")

        b_prev = ctk.CTkButton(btn_frame, text="Previsualizar",
                               command=self.preview, width=180)
        b_prev.pack(side="left", padx=5, expand=True, fill="x")
        tip(b_prev, "Cuenta cuantos registros cumplen el filtro\nsin modificar los datos todavia.")

        b_apply = ctk.CTkButton(btn_frame, text="Aplicar Filtro",
                                command=self.apply,
                                fg_color="#00b894", hover_color="#00a085", width=180)
        b_apply.pack(side="left", padx=5, expand=True, fill="x")
        tip(b_apply, "Aplica el filtro y vuelve con solo los registros\nque cumplen la condicion.")

        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy,
                      fg_color="#e74c3c", hover_color="#c0392b", width=120
                      ).pack(side="left", padx=5)

    def _bring_to_front(self):
        self.lift()
        self.focus_force()

    def _on_key_change(self, choice):
        self._update_field_type_hint()
        self.numeric_warn_label.configure(text="")  # limpiar aviso al cambiar clave

    def _update_field_type_hint(self):
        key = self.key_combo.get()
        if not self.data or not key or key == "(sin claves)":
            self.field_type_label.configure(text="")
            return
        samples = []
        for item in self.data[:5]:
            if isinstance(item, dict) and key in item:
                samples.append(type(item[key]).__name__)
        if samples:
            tipos = list(dict.fromkeys(samples))
            self.field_type_label.configure(
                text=f"Tipo detectado en '{key}': {', '.join(tipos)}")
        else:
            self.field_type_label.configure(
                text=f"'{key}' no encontrada en los primeros registros")

    def _update_op_tip(self, choice):
        self.op_tip_lbl.configure(text=self.OP_TIPS.get(choice, ""))
        self.numeric_warn_label.configure(text="")  # limpiar aviso al cambiar operador

    def _check_numeric_field(self, key: str, op: str) -> bool:
        """
        FIX: Comprueba si el campo parece numérico antes de aplicar
        operadores 'mayor que' / 'menor que'.
        Devuelve True si es seguro continuar, False si hay un problema
        y ya ha mostrado el aviso al usuario.
        """
        if op not in ("mayor que", "menor que"):
            return True

        # Examinar una muestra de hasta 10 registros
        non_numeric_found = False
        for item in self.data[:10]:
            if isinstance(item, dict) and key in item:
                val = item[key]
                if val is not None:
                    try:
                        float(val)
                    except (TypeError, ValueError):
                        non_numeric_found = True
                        break

        if non_numeric_found:
            self.numeric_warn_label.configure(
                text=f"⚠ '{key}' no parece numerico. El operador '{op}' puede no dar resultados.")
            return True  # Permitir continuar pero con aviso visible

        self.numeric_warn_label.configure(text="")
        return True

    def _apply_filter(self):
        key = self.key_combo.get()
        op  = self.op_combo.get()
        val = self.value_entry.get()

        if not key or key == "(sin claves)":
            messagebox.showwarning("Sin clave", "Selecciona una clave valida.")
            return None

        # FIX: Validar valor numérico con mensaje claro
        if op in ("mayor que", "menor que"):
            if not val.strip():
                messagebox.showwarning("Valor requerido",
                    f"El operador '{op}' requiere un numero.\nEl campo de valor esta vacio.")
                return None
            try:
                float(val)
            except ValueError:
                messagebox.showwarning("Valor invalido",
                    f"El operador '{op}' requiere un numero valido.\n"
                    f"Valor introducido: '{val}'\n\n"
                    f"Ejemplo de valores validos: 42, 3.14, -10")
                return None

        # Comprobar si el campo es numérico y mostrar aviso si no lo parece
        self._check_numeric_field(key, op)

        out = []
        for item in self.data:
            if not isinstance(item, dict):
                continue
            iv  = item.get(key)
            ivs = str(iv) if iv is not None else ""
            m   = False
            if   op == "igual a":     m = ivs == val
            elif op == "contiene":    m = val.lower() in ivs.lower()
            elif op == "empieza con": m = ivs.lower().startswith(val.lower())
            elif op == "termina con": m = ivs.lower().endswith(val.lower())
            elif op == "mayor que":
                try:    m = float(iv) > float(val)
                except (TypeError, ValueError): m = False
            elif op == "menor que":
                try:    m = float(iv) < float(val)
                except (TypeError, ValueError): m = False
            elif op == "existe":      m = key in item
            if m:
                out.append(item)
        return out

    def preview(self):
        f = self._apply_filter()
        if f is not None:
            self.result_label.configure(
                text=f"Resultado: {len(f)} registros coinciden de {len(self.data)}")

    def apply(self):
        result = self._apply_filter()
        if result is None:
            return
        if len(result) == 0:
            if not messagebox.askyesno("Sin resultados",
                    "El filtro no devuelve ningun registro.\n"
                    "¿Aplicar igualmente? (quedara la lista vacia)"):
                return
        self.result = result
        self.destroy()


# ================================================================
# WIDGET DE TEXTO CON RESALTADO DE SINTAXIS JSON
# ================================================================
class JsonHighlightText(tk.Frame):
    """
    Reemplaza CTkTextbox: tk.Text con scrollbars propias y resaltado
    de sintaxis JSON. Soporta cambio de tema (oscuro / claro).
    """

    # Paleta oscura
    DARK = {
        "bg":        "#1e1e2e",
        "fg":        "#cdd6f4",
        "key":       "#89b4fa",
        "string":    "#a6e3a1",
        "number":    "#fab387",
        "bool_null": "#cba6f7",
        "punct":     "#6c7086",
        "cursor":    "#cdd6f4",
        "select_bg": "#313244",
        "sb_bg":     "#181825",
        "sb_fg":     "#45475a",
        "sb_active": "#585b70",
    }
    # Paleta clara
    LIGHT = {
        "bg":        "#ffffff",
        "fg":        "#333333",
        "key":       "#0550ae",
        "string":    "#116329",
        "number":    "#953800",
        "bool_null": "#8250df",
        "punct":     "#888888",
        "cursor":    "#333333",
        "select_bg": "#dbe9ff",
        "sb_bg":     "#f0f0f0",
        "sb_fg":     "#b0b0b0",
        "sb_active": "#888888",
    }

    _HIGHLIGHT_CHAR_LIMIT = 40_000
    _WIDGET_CHAR_LIMIT    = 120_000

    def __init__(self, master, height=270, font=None, **kwargs):
        super().__init__(master, **kwargs)
        self._font    = font or ("Consolas", 11)
        self._palette = self.DARK

        self.configure(bg=self._palette["bg"])

        self._vsb_style = ttk.Style()
        self._vsb_style.theme_use("default")
        self._apply_scrollbar_style()

        self._vsb = ttk.Scrollbar(self, orient="vertical",
                                  style="JsonMerger.Vertical.TScrollbar")
        self._hsb = ttk.Scrollbar(self, orient="horizontal",
                                  style="JsonMerger.Horizontal.TScrollbar")

        self._text = tk.Text(
            self,
            font=self._font,
            wrap="none",
            bg=self._palette["bg"],
            fg=self._palette["fg"],
            insertbackground=self._palette["cursor"],
            selectbackground=self._palette["select_bg"],
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=8,
            yscrollcommand=self._vsb.set,
            xscrollcommand=self._hsb.set,
            state="normal",
        )

        self._vsb.configure(command=self._text.yview)
        self._hsb.configure(command=self._text.xview)

        self._vsb.pack(side="right",  fill="y")
        self._hsb.pack(side="bottom", fill="x")
        self._text.pack(side="left",  fill="both", expand=True)

        self._define_tags()

    def _apply_scrollbar_style(self):
        p = self._palette
        # Estilo moderno tipo CTkScrollableFrame:
        # thumb fino (8px), flechas invisibles, sin relieve ni bordes visibles.
        # El color del thumb y del trough responden correctamente al cambio de tema.
        for name in ("JsonMerger.Vertical.TScrollbar",
                     "JsonMerger.Horizontal.TScrollbar"):
            self._vsb_style.configure(
                name,
                background=p["sb_fg"],       # color del thumb
                troughcolor=p["sb_bg"],      # canal de fondo
                bordercolor=p["sb_bg"],      # borde = fondo -> invisible
                arrowcolor=p["sb_bg"],       # flechas = fondo -> invisibles
                arrowsize=0,                 # sin flechas
                relief="flat",
                borderwidth=0,
                width=8,                     # thumb estrecho como en CTk
            )
            self._vsb_style.map(
                name,
                background=[
                    ("active",  p["sb_active"]),   # hover/arrastre
                    ("!active", p["sb_fg"]),
                ],
                troughcolor=[
                    ("active",  p["sb_bg"]),
                    ("!active", p["sb_bg"]),
                ],
            )

    def _define_tags(self):
        p = self._palette
        self._text.tag_configure("key",       foreground=p["key"])
        self._text.tag_configure("string",    foreground=p["string"])
        self._text.tag_configure("number",    foreground=p["number"])
        self._text.tag_configure("bool_null", foreground=p["bool_null"])
        self._text.tag_configure("punct",     foreground=p["punct"])
        self._text.tag_configure("truncate_notice",
                                 foreground="#f39c12",
                                 font=(self._font[0], self._font[1], "italic"))

    def set_theme(self, dark: bool):
        self._palette = self.DARK if dark else self.LIGHT
        self.configure(bg=self._palette["bg"])
        self._apply_scrollbar_style()
        self._text.configure(
            bg=self._palette["bg"],
            fg=self._palette["fg"],
            insertbackground=self._palette["cursor"],
            selectbackground=self._palette["select_bg"],
        )
        self._define_tags()
        current = self._text.get("1.0", "end-1c")
        if current.strip():
            self._insert_highlighted(current)

    def delete(self, index1, index2=None):
        self._text.configure(state="normal")
        self._text.delete(index1, index2)

    def insert(self, index, chars, *args):
        self._text.configure(state="normal")
        self._text.insert(index, chars, *args)

    def get(self, index1, index2=None):
        return self._text.get(index1, index2)

    def configure(self, **kwargs):
        super().configure(**{k: v for k, v in kwargs.items()
                             if k in ("bg", "relief", "borderwidth",
                                      "highlightthickness", "padx", "pady")})

    def set_content(self, text: str):
        """Limpia y rellena con resaltado de sintaxis (con límite de seguridad)."""
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        if not text:
            self._text.configure(state="disabled")
            return

        if len(text) > self._WIDGET_CHAR_LIMIT:
            text = text[:self._WIDGET_CHAR_LIMIT] + \
                   "\n\n// [Widget: texto recortado a 120 KB para evitar bloqueo]"

        self._insert_highlighted(text)

    def _insert_highlighted(self, text: str):
        import re

        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        if len(text) > self._HIGHLIGHT_CHAR_LIMIT:
            lines = text.split("\n")
            for line in lines:
                stripped = line.lstrip()
                if stripped.startswith("//"):
                    self._text.insert("end", line + "\n", "truncate_notice")
                else:
                    self._text.insert("end", line + "\n")
            self._text.configure(state="disabled")
            return

        TOKEN_RE = re.compile(
            r'("(?:[^"\\]|\\.)*")'
            r'|(\btrue\b|\bfalse\b|\bnull\b)'
            r'|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)'
            r'|([{}\[\],:])'
            r'|(\s+)'
            r'|(.[^"{\[\]},:\s]*)'
        )

        context_stack = []

        for m in TOKEN_RE.finditer(text):
            s   = m.group(0)
            tag = None

            if m.group(1):
                rest  = text[m.end():]
                after = rest.lstrip()
                if after.startswith(":") and context_stack and context_stack[-1] == "object":
                    tag = "key"
                else:
                    if s.startswith('"//'):
                        tag = "truncate_notice"
                    else:
                        tag = "string"
            elif m.group(2):
                tag = "bool_null"
            elif m.group(3):
                tag = "number"
            elif m.group(4):
                tag = "punct"
                c = s.strip()
                if c == "{":
                    context_stack.append("object")
                elif c == "[":
                    context_stack.append("array")
                elif c in ("}", "]") and context_stack:
                    context_stack.pop()

            if tag:
                self._text.insert("end", s, tag)
            else:
                stripped = s.lstrip()
                if stripped.startswith("//"):
                    self._text.insert("end", s, "truncate_notice")
                else:
                    self._text.insert("end", s)

        self._text.configure(state="disabled")


# ================================================================
# SELECTOR DE ARRAY ANIDADO
# ================================================================
class NestedArraySelector(ctk.CTkToplevel):
    def __init__(self, parent, data: dict):
        super().__init__(parent)
        self.title("Seleccionar datos")
        self.geometry("520x480")
        self.resizable(False, False)
        self.result      = None
        self.result_path = None
        self._data       = data
        self._arrays     = {}

        self._scan(data, path=[])
        self.after(50, self._bring_to_front)
        self._build_ui()

    def _scan(self, obj, path: list, depth: int = 0):
        if depth > 8:
            return
        if isinstance(obj, dict):
            for key, val in obj.items():
                if isinstance(val, list) and val:
                    if any(isinstance(item, dict) for item in val):
                        ruta = " → ".join(path + [key])
                        if ruta not in self._arrays:
                            self._arrays[ruta] = []
                        self._arrays[ruta].extend(val)
                    for item in val:
                        self._scan(item, path + [key], depth + 1)
                elif isinstance(val, dict):
                    self._scan(val, path + [key], depth + 1)

    def _build_ui(self):
        ctk.CTkLabel(self,
                     text="Este archivo tiene datos anidados",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(22, 4))

        ctk.CTkLabel(self,
                     text="¿Con qué datos quieres trabajar?",
                     font=ctk.CTkFont(size=13),
                     text_color="#a0a0a0").pack(pady=(0, 16))

        if not self._arrays:
            ctk.CTkLabel(self,
                         text="No se encontraron listas de objetos en este archivo.",
                         font=ctk.CTkFont(size=13),
                         text_color="#e74c3c").pack(pady=20)
            ctk.CTkButton(self, text="Cerrar", command=self.destroy,
                          fg_color="#7f8c8d", hover_color="#636e72").pack(pady=10)
            return

        scroll = ctk.CTkScrollableFrame(self, height=280)
        scroll.pack(padx=30, fill="x", expand=False)

        self._radio_var = ctk.StringVar(value="0")
        self._radio_map = {}

        for i, (ruta, arr) in enumerate(self._arrays.items()):
            idx_str = str(i)
            self._radio_map[idx_str] = (ruta, arr)

            sample    = arr[0] if arr else {}
            campos    = list(sample.keys()) if isinstance(sample, dict) else []
            campos_str = ", ".join(campos[:4])
            if len(campos) > 4:
                campos_str += f"  (+{len(campos)-4} más)"

            row = ctk.CTkFrame(scroll, fg_color=("#e8e8e8", "#2a2a3e"),
                               corner_radius=8)
            row.pack(fill="x", pady=4, padx=4)

            ctk.CTkRadioButton(
                row,
                text=f"  {ruta}",
                variable=self._radio_var,
                value=idx_str,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w", padx=14, pady=(10, 2))

            ctk.CTkLabel(
                row,
                text=f"  {len(arr)} registros   ·   campos: {campos_str}",
                font=ctk.CTkFont(size=11),
                text_color="#a0a0a0"
            ).pack(anchor="w", padx=28, pady=(0, 10))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=18, padx=30, fill="x")

        ctk.CTkButton(
            btn_frame, text="Usar estos datos",
            command=self._confirm,
            fg_color="#00b894", hover_color="#00a085",
            height=42, font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", expand=True, fill="x", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="Cancelar",
            command=self.destroy,
            fg_color="#e74c3c", hover_color="#c0392b",
            height=42
        ).pack(side="left", padx=(0, 0))

    def _confirm(self):
        idx = self._radio_var.get()
        if idx not in self._radio_map:
            return
        ruta, arr        = self._radio_map[idx]
        self.result      = arr
        self.result_path = ruta
        self.destroy()

    def _bring_to_front(self):
        self.lift()
        self.focus_force()


# ================================================================
# APLICACION PRINCIPAL
# ================================================================
class JSONMergerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("JSON Merger Pro")
        self.geometry("1140x900")
        self.minsize(900, 700)
        self.resizable(True, True)
        self.files: list        = []
        self.invalid_files: set = set()
        self.pending_data       = None
        self._dark_mode         = True
        self.create_widgets()

    MAX_PREVIEW_LINES = 500
    MAX_PREVIEW_CHARS = 80_000

    # ── Construccion de la interfaz ───────────────────────────────
    def create_widgets(self):

        # ── Cabecera ──────────────────────────────────────────────
        hdr = ctk.CTkFrame(self)
        hdr.pack(pady=12, padx=55, fill="x")

        self.info_label = ctk.CTkLabel(
            hdr, text="Archivos cargados: 0 | Tamanio total: 0.00 KB",
            font=ctk.CTkFont(size=14))
        self.info_label.pack(side="left", pady=8)
        tip(self.info_label,
            "Numero de archivos JSON en la lista\ny su tamanio combinado en disco.")

        self.about_btn = ctk.CTkButton(
            hdr, text="ℹ",
            command=self.open_about,
            width=34, height=34,
            font=ctk.CTkFont(size=16),
            fg_color="#00b894",
            hover_color="#00a085",
            border_width=0)
        self.about_btn.pack(side="right", pady=8, padx=(0, 6))
        tip(self.about_btn, "Acerca de JSON Merger Pro")

        self.theme_switch = ctk.CTkSwitch(
            hdr, text="☀️", command=self.toggle_theme,
            font=ctk.CTkFont(size=16))
        self.theme_switch.pack(side="right", pady=8, padx=(0, 4))
        tip(self.theme_switch, "Alterna entre tema oscuro (🌙) y claro (☀️).")

        ctk.CTkLabel(self, text="JSON Merger Pro",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(pady=8)

        # ── Botones de carga ──────────────────────────────────────
        bf = ctk.CTkFrame(self)
        bf.pack(pady=8, padx=55, fill="x")

        b = ctk.CTkButton(bf, text="Seleccionar Archivos",
                          command=self.select_files, width=240, height=44,
                          font=ctk.CTkFont(size=14, weight="bold"))
        b.pack(side="left", padx=6)
        tip(b, "Abre un explorador para elegir uno o varios\narchivos con estructura json valida.")

        b = ctk.CTkButton(bf, text="Cargar Carpeta",
                          command=self.load_folder, width=185, height=44,
                          fg_color="#8e44ad", hover_color="#7d3c98")
        b.pack(side="left", padx=6)
        tip(b, "Carga automaticamente TODOS los .json\nde la carpeta elegida.")

        b = ctk.CTkButton(bf, text="Limpiar Todo",
                          command=self.clear_all, width=155, height=44,
                          fg_color="#e74c3c", hover_color="#c0392b")
        b.pack(side="left", padx=6)
        tip(b, "Elimina todos los archivos de la lista\ny resetea filtros y deduplicacion activos.")

        # ── Ordenado ──────────────────────────────────────────────
        sf = ctk.CTkFrame(self)
        sf.pack(pady=6, padx=55, fill="x")

        sl = ctk.CTkLabel(sf, text="Ordenar por:", font=ctk.CTkFont(size=13))
        sl.pack(side="left", padx=(0, 10))
        tip(sl, "Cambia el orden de los archivos en la lista.")

        self.sort_var = ctk.StringVar(value="Alfabeticamente")
        ss = ctk.CTkSegmentedButton(sf,
            values=["Alfabeticamente", "Por Fecha", "Por Tamanio"],
            variable=self.sort_var, command=self.sort_list, height=36)
        ss.pack(side="left", padx=8)
        tip(ss, "Alfabeticamente -> A-Z.\nPor Fecha -> mas reciente primero.\nPor Tamanio -> mas grande primero.")

        # ── Lista de archivos ─────────────────────────────────────
        ll = ctk.CTkLabel(self, text="Archivos cargados:", font=ctk.CTkFont(size=14))
        ll.pack(anchor="w", padx=55, pady=(12, 4))
        tip(ll, "Lista de archivos JSON listos para unir.\nRojo = JSON invalido.\nClic izq -> ver contenido.  Clic der -> opciones.")

        lscroll = ctk.CTkScrollableFrame(self, height=175)
        lscroll.pack(pady=6, padx=55, fill="both", expand=True)

        self.file_listbox = tk.Listbox(
            lscroll, height=10, font=("Consolas", 12),
            selectbackground="#00b894", activestyle="none",
            borderwidth=0, bg="#1e1e1e", fg="#ffffff")
        self.file_listbox.pack(pady=6, padx=8, fill="both", expand=True)

        self.file_listbox.bind("<<ListboxSelect>>", self.show_file_info)
        self.file_listbox.bind("<Button-3>",        self.show_context_menu)

        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Eliminar archivo",    command=self.delete_selected)
        self.context_menu.add_command(label="Abrir en explorador", command=self.open_in_explorer)

        # ── Estadisticas ──────────────────────────────────────────
        self.stats_label = ctk.CTkLabel(
            self, text="Estadisticas: Ningun archivo seleccionado",
            font=ctk.CTkFont(size=13), text_color="#a0a0a0")
        self.stats_label.pack(anchor="w", padx=60, pady=6)
        tip(self.stats_label,
            "Informacion del archivo seleccionado:\n"
            "tipo, numero de elementos y tamanio en disco.")

        # ── Modo de union ─────────────────────────────────────────
        opt = ctk.CTkFrame(self)
        opt.pack(pady=10, padx=55, fill="x")

        ml = ctk.CTkLabel(opt, text="Modo de union:", font=ctk.CTkFont(size=13))
        ml.pack(side="left", padx=(10, 16))
        tip(ml, "Define la estructura del JSON resultante.")

        self.merge_type = ctk.StringVar(value="array")

        rb = ctk.CTkRadioButton(opt, text="Array  [ ]  — lista de elementos",
                                variable=self.merge_type, value="array")
        rb.pack(side="left", padx=18)
        tip(rb, "Une todo en una lista [ ... ].\nIdeal para colecciones: usuarios, productos, etc.")

        rb = ctk.CTkRadioButton(opt, text="Objeto  { }  — claves combinadas",
                                variable=self.merge_type, value="object")
        rb.pack(side="left", padx=18)
        tip(rb, "Fusiona en un objeto { ... }.\nSi hay claves repetidas, gana el ultimo archivo.\nIdeal para archivos de configuracion.")

        # ── Herramientas ──────────────────────────────────────────
        tools = ctk.CTkFrame(self)
        tools.pack(pady=6, padx=55, fill="x")

        tl = ctk.CTkLabel(tools, text="Herramientas:", font=ctk.CTkFont(size=13))
        tl.pack(side="left", padx=(0, 10))
        tip(tl, "Operaciones opcionales antes de guardar el resultado.")

        b = ctk.CTkButton(tools, text="Filtrar Registros",
                          command=self.open_filter, height=38, width=190,
                          fg_color="#2980b9", hover_color="#1a6fa0")
        b.pack(side="left", padx=6)
        tip(b, "Queda solo con los registros que cumplan\nuna condicion (ej: ciudad='Madrid').\nSolo disponible para arrays de objetos.")

        b = ctk.CTkButton(tools, text="Deduplicar",
                          command=self.open_deduplicate, height=38, width=165,
                          fg_color="#8e44ad", hover_color="#7d3c98")
        b.pack(side="left", padx=6)
        tip(b, "Elimina registros duplicados.\nPuedes comparar el registro completo\no solo una clave concreta (ej: 'id').")

        b = ctk.CTkButton(tools, text="Copiar al Portapapeles",
                          command=self.copy_to_clipboard, height=38, width=210,
                          fg_color="#16a085", hover_color="#117a65")
        b.pack(side="left", padx=6)
        tip(b, "Copia el JSON resultante al portapapeles\npara pegarlo donde necesites.")

        b = ctk.CTkButton(tools, text="Resetear Filtros",
                          command=self.reset_pending, height=38, width=165,
                          fg_color="#7f8c8d", hover_color="#636e72")
        b.pack(side="left", padx=6)
        tip(b, "Descarta el filtro o deduplicacion activos\ny vuelve a los datos originales completos.")

        self.pending_label = ctk.CTkLabel(tools, text="",
                                          font=ctk.CTkFont(size=12),
                                          text_color="#f39c12")
        self.pending_label.pack(side="left", padx=10)
        tip(self.pending_label,
            "Aviso: hay un filtro o deduplicacion activos.\n"
            "El archivo guardado usara esos datos modificados,\nno los originales.")

        # ── Acciones principales ──────────────────────────────────
        act = ctk.CTkFrame(self)
        act.pack(pady=16, padx=55, fill="x")

        b = ctk.CTkButton(act, text="Vista Previa Final",
                          command=self.preview_final_result,
                          fg_color="#3498db", height=50,
                          font=ctk.CTkFont(size=15))
        b.pack(side="left", padx=8, expand=True, fill="x")
        tip(b, "Muestra como quedara el JSON final\nantes de guardar. No escribe ningun archivo.")

        b = ctk.CTkButton(act, text="UNIR Y GUARDAR",
                          command=self.merge_json,
                          fg_color="#00b894", hover_color="#00a085",
                          height=50, font=ctk.CTkFont(size=16, weight="bold"))
        b.pack(side="left", padx=8, expand=True, fill="x")
        tip(b, "Une todos los archivos y guarda el resultado\ncomo un nuevo .json. Aplica filtros/dedup si estan activos.")

        b = ctk.CTkButton(act, text="Exportar CSV",
                          command=self.export_csv,
                          fg_color="#e67e22", hover_color="#d35400",
                          height=50, font=ctk.CTkFont(size=14))
        b.pack(side="left", padx=8, expand=True, fill="x")
        tip(b, "Exporta el resultado a .csv compatible con\nExcel y Google Sheets.\nSolo funciona con arrays de objetos planos.")

        # ── Panel de vista previa (SIN tooltip — eliminado) ───────
        preview_header = ctk.CTkFrame(self, fg_color="transparent")
        preview_header.pack(anchor="w", padx=55, pady=(8, 2), fill="x")

        pl = ctk.CTkLabel(preview_header, text="Vista previa",
                          font=ctk.CTkFont(size=15, weight="bold"))
        pl.pack(side="left")

        self.preview_limit_label = ctk.CTkLabel(
            preview_header,
            text=f"(máx. {self.MAX_PREVIEW_LINES} líneas — el archivo completo se guarda íntegro)",
            font=ctk.CTkFont(size=11),
            text_color="#6c7086")
        self.preview_limit_label.pack(side="left", padx=(12, 0))

        # ── FIX: tooltip eliminado del panel de preview ───────────
        self.preview_text = JsonHighlightText(
            self,
            height=270,
            font=("Consolas", 11),
            bg="#1e1e2e",
            relief="flat",
            borderwidth=0,
        )
        self.preview_text.pack(pady=8, padx=55, fill="both", expand=True)
        # (tooltip eliminado intencionalmente — no es necesario aquí)

    # ── Ventana Acerca de ─────────────────────────────────────────
    def open_about(self):
        win = AboutWindow(self)
        win.lift()
        win.focus_force()
        win.grab_set()

    # ── Tema ──────────────────────────────────────────────────────
    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            self._dark_mode = False
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="🌙")
            self.file_listbox.configure(bg="#f0f0f0", fg="#000000")
            self.about_btn.configure(fg_color="#1a1a1a", hover_color="#333333")
        else:
            self._dark_mode = True
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="☀️")
            self.file_listbox.configure(bg="#1e1e1e", fg="#ffffff")
            self.about_btn.configure(fg_color="#00b894", hover_color="#00a085")

        self.update_list()
        self.preview_text.set_theme(self._dark_mode)

    # ── FIX: Lectura de archivo con fallback de encoding ─────────
    def _load_json_file(self, path: str):
        """
        Intenta leer un archivo JSON probando varios encodings en orden.
        Devuelve el objeto Python parseado o lanza excepción si falla todo.
        """
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        last_err  = None
        for enc in encodings:
            try:
                with open(path, "r", encoding=enc) as f:
                    return json.load(f)
            except UnicodeDecodeError:
                last_err = Exception(f"No se pudo decodificar con {enc}")
                continue
            except json.JSONDecodeError as e:
                # Caso especial: un archivo UTF-8 con BOM produce JSONDecodeError
                # en lugar de UnicodeDecodeError — intentar con utf-8-sig
                if "BOM" in str(e) and enc == "utf-8":
                    last_err = e
                    continue
                raise e  # JSON realmente inválido → propagar
        raise last_err

    # ── Validacion silenciosa ─────────────────────────────────────
    def _validate_file(self, path: str) -> tuple:
        ext_no_estandar = not path.lower().endswith(".json")
        try:
            self._load_json_file(path)
            return True, ext_no_estandar
        except Exception:
            return False, ext_no_estandar

    # ── FIX: reset de pending_data al cargar nuevos archivos ──────
    def _reset_pending_if_active(self):
        """
        Si hay un filtro/dedup activo cuando el usuario añade archivos,
        lo resetea automáticamente y avisa, para evitar confusión.
        """
        if self.pending_data is not None:
            self.pending_data = None
            self.pending_label.configure(text="")
            self.stats_label.configure(
                text="⚠ Filtro/dedup reseteado al añadir nuevos archivos.")

    # ── Carga de archivos ─────────────────────────────────────────
    def select_files(self):
        paths = filedialog.askopenfilenames(
            filetypes=[
                ("Archivos JSON", "*.json"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if paths:
            nuevos = [p for p in paths if p not in self.files]
            if nuevos:
                self._reset_pending_if_active()   # FIX
                self.files.extend(nuevos)
                self.update_list()
                self.stats_label.configure(
                    text=f"{len(nuevos)} archivo(s) nuevo(s) aniadido(s)")

    def load_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta con archivos JSON")
        if not folder:
            return
        found = [os.path.join(folder, f)
                 for f in os.listdir(folder) if f.lower().endswith(".json")]
        if not found:
            messagebox.showinfo("Sin archivos",
                "No se encontraron archivos JSON en esa carpeta.")
            return
        nuevos = [p for p in found if p not in self.files]
        if nuevos:
            self._reset_pending_if_active()       # FIX
            self.files.extend(nuevos)
            self.update_list()
            self.stats_label.configure(
                text=f"Carpeta cargada: {len(nuevos)} archivos nuevos aniadidos")

    # ── Gestion de la lista ───────────────────────────────────────
    def update_list(self):
        self.file_listbox.delete(0, tk.END)
        self.invalid_files.clear()

        if self._dark_mode:
            valid_fg   = "#ffffff"
            warn_fg    = "#f39c12"
            warn_bg    = "#2d2510"
            invalid_fg = "#ff6b6b"
            invalid_bg = "#2d1b1b"
        else:
            valid_fg   = "#000000"
            warn_fg    = "#b7600a"
            warn_bg    = "#fff8e1"
            invalid_fg = "#cc0000"
            invalid_bg = "#fff0f0"

        for idx, path in enumerate(self.files):
            basename = os.path.basename(path)
            is_valid, ext_warn = self._validate_file(path)

            if not is_valid:
                self.invalid_files.add(path)
                label = f"  ✗ {basename}  [JSON invalido]"
                self.file_listbox.insert(tk.END, label)
                self.file_listbox.itemconfig(idx, fg=invalid_fg, bg=invalid_bg)
            elif ext_warn:
                label = f"  ⚠ {basename}  [extension no estandar]"
                self.file_listbox.insert(tk.END, label)
                self.file_listbox.itemconfig(idx, fg=warn_fg, bg=warn_bg)
            else:
                label = f"  {basename}"
                self.file_listbox.insert(tk.END, label)
                self.file_listbox.itemconfig(idx, fg=valid_fg)

        self._update_header()

    def _update_header(self):
        if not self.files:
            self.info_label.configure(
                text="Archivos cargados: 0 | Tamanio total: 0.00 KB")
            return
        total_kb = sum(
            os.path.getsize(f) for f in self.files
            if os.path.exists(f) and f not in self.invalid_files) / 1024
        n_invalid = len(self.invalid_files)
        if n_invalid:
            extra = f" | ⚠ {n_invalid} invalido(s)"
        else:
            extra = ""
        self.info_label.configure(
            text=f"Archivos cargados: {len(self.files)} | Tamanio total: {total_kb:.2f} KB{extra}")

    def sort_list(self, choice):
        if not self.files:
            return
        if   choice == "Alfabeticamente":
            self.files.sort(key=lambda x: os.path.basename(x).lower())
        elif choice == "Por Fecha":
            self.files.sort(key=os.path.getmtime, reverse=True)
        elif choice == "Por Tamanio":
            self.files.sort(key=os.path.getsize,  reverse=True)
        self.update_list()

    def show_context_menu(self, event):
        idx = self.file_listbox.nearest(event.y)
        if idx >= 0:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(idx)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def delete_selected(self):
        sel = self.file_listbox.curselection()
        if not sel:
            return
        del self.files[sel[0]]
        self.update_list()
        self.preview_text.set_content("")
        self.stats_label.configure(text="Estadisticas: Archivo eliminado")

    def open_in_explorer(self):
        sel = self.file_listbox.curselection()
        if not sel:
            return
        folder = os.path.dirname(self.files[sel[0]])
        try:
            if   sys.platform == "win32":  os.startfile(folder)
            elif sys.platform == "darwin": subprocess.Popen(["open",     folder])
            else:                          subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Error al abrir explorador", str(e))

    def clear_all(self):
        if messagebox.askyesno("Confirmar", "Eliminar todos los archivos de la lista?"):
            self.files.clear()
            self.invalid_files.clear()
            self.pending_data = None
            self.pending_label.configure(text="")
            self.update_list()
            self.preview_text.set_content("")
            self.stats_label.configure(text="Estadisticas: Lista vaciada")

    def show_file_info(self, event=None):
        sel = self.file_listbox.curselection()
        if not sel:
            return
        path = self.files[sel[0]]
        try:
            data    = self._load_json_file(path)          # FIX: usa encoding robusto
            size_kb = os.path.getsize(path) / 1024
            if   isinstance(data, list): stat = f"Array | {len(data)} elementos | {size_kb:.1f} KB"
            elif isinstance(data, dict): stat = f"Objeto | {len(data)} claves | {size_kb:.1f} KB"
            else:                        stat = f"{type(data).__name__} | {size_kb:.1f} KB"
            self.stats_label.configure(text=f"Estadisticas: {stat}")
            self._set_preview(data)
        except json.JSONDecodeError as e:
            self.stats_label.configure(text="Error: JSON invalido en este archivo")
            self.preview_text.set_content(f"// JSON invalido:\n// {e}")
        except Exception as e:
            self.stats_label.configure(text="Error al leer archivo")
            self.preview_text.set_content(f"// Error: {e}")

    # ── Utilidades internas ───────────────────────────────────────
    def _set_preview(self, data):
        text  = json.dumps(data, indent=3, ensure_ascii=False)
        lines = text.splitlines()
        total_lines = len(lines)
        truncated   = False

        if total_lines > self.MAX_PREVIEW_LINES:
            lines     = lines[:self.MAX_PREVIEW_LINES]
            truncated = True

        truncated_text = "\n".join(lines)

        if len(truncated_text) > self.MAX_PREVIEW_CHARS:
            truncated_text = truncated_text[:self.MAX_PREVIEW_CHARS]
            truncated      = True

        if truncated:
            truncated_text += (
                f"\n\n"
                f"// ─── VISTA PREVIA TRUNCADA ─────────────────────────────\n"
                f"// Mostrando las primeras {min(self.MAX_PREVIEW_LINES, total_lines)}"
                f" líneas de {total_lines} totales.\n"
                f"// El archivo guardado con 'UNIR Y GUARDAR' contiene todos los datos."
            )

        self.preview_text.set_content(truncated_text)

    def _build_merged_data(self):
        all_data = []
        for path in self.files:
            if path in self.invalid_files:
                continue
            d = self._load_json_file(path)               # FIX: usa encoding robusto
            if   isinstance(d, list): all_data.extend(d)
            elif isinstance(d, dict): all_data.append(d)
            else:                     all_data.append(d)
        if self.merge_type.get() == "array":
            return all_data
        result = {}
        for item in all_data:
            if isinstance(item, dict):
                result.update(item)
        return result

    def _get_data(self):
        return self.pending_data if self.pending_data is not None \
               else self._build_merged_data()

    def reset_pending(self):
        if self.pending_data is None:
            self.stats_label.configure(text="No hay filtro ni deduplicacion activos.")
            return
        self.pending_data = None
        self.pending_label.configure(text="")
        self.stats_label.configure(text="Filtros reseteados. Usando datos originales.")
        self.preview_text.set_content("")

    # ── Acciones principales ──────────────────────────────────────
    def preview_final_result(self):
        if not self.files:
            messagebox.showwarning("Vacio", "No hay archivos cargados")
            return
        if self.invalid_files:
            invalidos = [os.path.basename(p) for p in self.invalid_files]
            messagebox.showwarning(
                "Archivos invalidos ignorados",
                f"Los siguientes archivos tienen JSON invalido y seran ignorados:\n\n"
                + "\n".join(invalidos))
        try:
            data = self._get_data()

            # FIX: mensaje claro si todos los archivos son inválidos
            if not data and isinstance(data, list) and \
               len(self.invalid_files) == len(self.files):
                messagebox.showerror(
                    "Sin datos validos",
                    "Todos los archivos cargados son invalidos.\n"
                    "No hay datos que previsualizar.\n\n"
                    "Por favor, carga al menos un archivo JSON valido.")
                return

            self._set_preview(data)
            n    = len(data) if isinstance(data, (list, dict)) else 1
            tipo = ("elementos" if isinstance(data, list)
                    else "claves" if isinstance(data, dict) else "valor")
            self.stats_label.configure(text=f"Vista previa final  •  {n} {tipo}")
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON invalido",
                f"Uno de los archivos tiene JSON invalido:\n{e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def merge_json(self):
        if not self.files:
            messagebox.showwarning("Advertencia", "No hay archivos para unir")
            return

        # FIX: mensaje claro si todos los archivos son inválidos
        if len(self.invalid_files) == len(self.files):
            messagebox.showerror(
                "Sin datos validos",
                "Todos los archivos cargados son invalidos.\n"
                "No hay nada que guardar.\n\n"
                "Por favor, carga al menos un archivo JSON valido.")
            return

        if self.invalid_files:
            invalidos = [os.path.basename(p) for p in self.invalid_files]
            if not messagebox.askyesno(
                    "Archivos invalidos",
                    f"Hay {len(self.invalid_files)} archivo(s) invalido(s) que seran ignorados:\n\n"
                    + "\n".join(invalidos)
                    + "\n\n¿Continuar con los validos?"):
                return
        try:
            result = self._get_data()
            name   = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            path   = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
                initialfile=name)
            if not path:
                return
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            self.pending_data = None
            self.pending_label.configure(text="")
            messagebox.showinfo("Exito",
                f"Archivos unidos correctamente.\n\nGuardado en:\n{path}")
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON invalido",
                f"Uno de los archivos tiene JSON invalido:\n{e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_csv(self):
        if not self.files:
            messagebox.showwarning("Advertencia", "No hay archivos cargados")
            return
        try:
            import csv
            data = self._get_data()
            if not isinstance(data, list) or not data:
                messagebox.showwarning("No compatible",
                    "Solo se puede exportar a CSV un array de objetos.")
                return
            headers = []
            for item in data:
                if isinstance(item, dict):
                    for k in item:
                        if k not in headers:
                            headers.append(k)
            if not headers:
                messagebox.showwarning("Sin claves",
                    "Los datos no tienen claves exportables.")
                return
            name = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv")],
                initialfile=name)
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
                w.writeheader()
                for item in data:
                    if isinstance(item, dict):
                        row = {k: (json.dumps(v, ensure_ascii=False)
                                   if isinstance(v, (dict, list)) else v)
                               for k, v in item.items()}
                        w.writerow(row)
            messagebox.showinfo("CSV Exportado", f"Exportado correctamente:\n{path}")
        except Exception as e:
            messagebox.showerror("Error al exportar", str(e))

    def copy_to_clipboard(self):
        if not self.files:
            messagebox.showwarning("Vacio", "No hay archivos cargados")
            return
        try:
            pyperclip.copy(
                json.dumps(self._get_data(), indent=4, ensure_ascii=False))
            self.stats_label.configure(text="JSON copiado al portapapeles")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_filter(self):
        if not self.files:
            messagebox.showwarning("Vacio", "No hay archivos cargados")
            return
        try:
            # Siempre trabajar sobre los datos originales (sin pending) para el
            # selector de array anidado. Así el usuario siempre ve la estructura
            # completa, no solo los datos ya filtrados/deduplicados.
            base = self._build_merged_data()

            if isinstance(base, dict):
                sel = NestedArraySelector(self, base)
                sel.lift()
                sel.focus_force()
                sel.grab_set()
                self.wait_window(sel)
                if sel.result is None:
                    return
                base = sel.result
                self.stats_label.configure(
                    text=f"Trabajando con: {sel.result_path}  ({len(base)} registros)")

            if not isinstance(base, list):
                messagebox.showwarning("No compatible",
                    "El filtrado solo esta disponible para arrays.")
                return
            if not base:
                messagebox.showwarning("Lista vacia",
                    "No hay registros que filtrar.")
                return
            win = FilterWindow(self, base)
            win.lift()
            win.focus_force()
            win.grab_set()
            self.wait_window(win)
            if win.result is not None:
                self.pending_data = win.result
                self.pending_label.configure(
                    text=f"⚑ Filtro activo: {len(win.result)} reg.")
                self._set_preview(win.result)
                self.stats_label.configure(
                    text=f"Filtro aplicado: {len(win.result)} registros coinciden")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_deduplicate(self):
        if not self.files:
            messagebox.showwarning("Vacio", "No hay archivos cargados")
            return
        try:
            # Siempre trabajar sobre los datos originales (sin pending) para el
            # selector de array anidado. Así el usuario siempre ve la estructura
            # completa, no solo los datos ya filtrados/deduplicados.
            base = self._build_merged_data()

            if isinstance(base, dict):
                sel = NestedArraySelector(self, base)
                sel.lift()
                sel.focus_force()
                sel.grab_set()
                self.wait_window(sel)
                if sel.result is None:
                    return
                base = sel.result
                self.stats_label.configure(
                    text=f"Trabajando con: {sel.result_path}  ({len(base)} registros)")

            if not isinstance(base, list):
                messagebox.showwarning("No compatible",
                    "La deduplicacion solo esta disponible para arrays.")
                return
            if not base:
                messagebox.showwarning("Lista vacia",
                    "No hay registros que deduplicar.")
                return
            win = DeduplicateWindow(self, base)
            win.lift()
            win.focus_force()
            win.grab_set()
            self.wait_window(win)
            if win.result is not None:
                removed = len(base) - len(win.result)
                self.pending_data = win.result
                self.pending_label.configure(
                    text=f"⚑ Dedup activo: {len(win.result)} reg.")
                self._set_preview(win.result)
                self.stats_label.configure(
                    text=f"Deduplicacion: {removed} duplicados eliminados  →  {len(win.result)} registros")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ================================================================
# ENTRY POINT
# ================================================================
if __name__ == "__main__":
    app = JSONMergerApp()
    app.mainloop()

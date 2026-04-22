import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import json
import os
import sys
import threading
import platform
import shutil
from pathlib import Path
import uuid

# ─────────────────────────────────────────────
#  CONSTANTS & PATHS
# ─────────────────────────────────────────────
APP_TITLE = "VM Manager Pro"
CONFIG_FILE = "vm_config.json"
QEMU_EXECUTABLES = ["qemu-system-x86_64", "qemu-system-x86_64.exe"]
VBOXMANAGE = "VBoxManage"

# ─────────────────────────────────────────────
#  COLORS & FONTS
# ─────────────────────────────────────────────
BG        = "#0D0F14"
CARD      = "#13161E"
CARD2     = "#1A1E2A"
ACCENT    = "#00D4FF"
ACCENT2   = "#7C3AED"
SUCCESS   = "#00E676"
DANGER    = "#FF3D5A"
WARNING   = "#FFB300"
TEXT      = "#E8EAED"
TEXT_DIM  = "#6B7280"
BORDER    = "#252A37"

FONT_HEAD = ("Segoe UI", 22, "bold")
FONT_SUB  = ("Segoe UI", 11)
FONT_BODY = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 9)
FONT_BTN  = ("Segoe UI", 10, "bold")
FONT_TINY = ("Segoe UI", 8)


# ─────────────────────────────────────────────
#  VM CONFIG MANAGER
# ─────────────────────────────────────────────
class VMConfig:
    def __init__(self):
        self.vms = {}
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.vms = json.load(f)
            except Exception:
                self.vms = {}

    def save(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.vms, f, indent=2)

    def add_vm(self, vm):
        self.vms[vm["id"]] = vm
        self.save()

    def remove_vm(self, vm_id):
        self.vms.pop(vm_id, None)
        self.save()

    def update_vm(self, vm_id, data):
        if vm_id in self.vms:
            self.vms[vm_id].update(data)
            self.save()

    def list_vms(self):
        return list(self.vms.values())


# ─────────────────────────────────────────────
#  QEMU LAUNCHER
# ─────────────────────────────────────────────
class QEMULauncher:
    @staticmethod
    def find_qemu():
        for exe in QEMU_EXECUTABLES:
            path = shutil.which(exe)
            if path:
                return path
        return None

    @staticmethod
    def build_command(vm):
        qemu = QEMULauncher.find_qemu()
        if not qemu:
            return None, "QEMU introuvable. Installez QEMU et ajoutez-le au PATH."

        cmd = [qemu]

        # RAM
        ram = vm.get("ram", 2048)
        cmd += ["-m", str(ram)]

        # CPU cores
        cpu = vm.get("cpu", 2)
        cmd += ["-smp", str(cpu)]

        # Disk image
        disk = vm.get("disk", "")
        if disk and os.path.exists(disk):
            cmd += ["-hda", disk]

        # ISOs (boot ISO first, then extra ISOs as CD drives)
        isos = vm.get("isos", [])
        if isos:
            cmd += ["-cdrom", isos[0]]
            if len(isos) > 1:
                for i, iso in enumerate(isos[1:], start=1):
                    cmd += [
                        f"-drive",
                        f"file={iso},media=cdrom,index={i+1}",
                    ]

        # Boot order
        boot = vm.get("boot_order", "dc")
        cmd += ["-boot", boot]

        # Network
        net = vm.get("network", "user")
        if net == "user":
            cmd += ["-net", "nic", "-net", "user"]
        elif net == "none":
            cmd += ["-net", "none"]

        # Display
        display = vm.get("display", "sdl")
        cmd += ["-display", display]

        # Enable KVM on Linux if available
        if platform.system() == "Linux" and os.path.exists("/dev/kvm"):
            cmd += ["-enable-kvm"]

        # USB
        if vm.get("usb", True):
            cmd += ["-usb", "-device", "usb-tablet"]

        # Audio
        if vm.get("audio", False):
            cmd += ["-audiodev", "pa,id=snd0", "-device", "intel-hda",
                    "-device", "hda-duplex,audiodev=snd0"]

        return cmd, None

    @staticmethod
    def launch(vm, on_done=None):
        cmd, err = QEMULauncher.build_command(vm)
        if err:
            if on_done:
                on_done(False, err)
            return

        def run():
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if platform.system() == "Windows" else 0,
                )
                _, stderr = proc.communicate()
                if on_done:
                    if proc.returncode != 0:
                        on_done(False, stderr.decode(errors="ignore"))
                    else:
                        on_done(True, "")
            except Exception as e:
                if on_done:
                    on_done(False, str(e))

        t = threading.Thread(target=run, daemon=True)
        t.start()


# ─────────────────────────────────────────────
#  STYLED WIDGETS
# ─────────────────────────────────────────────
def make_btn(parent, text, command=None, color=ACCENT, width=14):
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg=BG if color in (ACCENT, SUCCESS, WARNING) else TEXT,
        activebackground=color,
        activeforeground=BG,
        relief="flat",
        font=FONT_BTN,
        cursor="hand2",
        width=width,
        padx=6,
        pady=5,
        bd=0,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=_lighten(color)))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def _lighten(hex_color):
    """Slightly brighten a hex color."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    r = min(255, r + 30)
    g = min(255, g + 30)
    b = min(255, b + 30)
    return f"#{r:02x}{g:02x}{b:02x}"


def label(parent, text, font=FONT_BODY, fg=TEXT, bg=None):
    bg = bg or parent.cget("bg")
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg)


def separator(parent):
    return tk.Frame(parent, bg=BORDER, height=1)


# ─────────────────────────────────────────────
#  VM CARD WIDGET
# ─────────────────────────────────────────────
class VMCard(tk.Frame):
    def __init__(self, parent, vm, on_launch, on_edit, on_delete, **kw):
        super().__init__(parent, bg=CARD, padx=14, pady=12, **kw)
        self.vm = vm
        self._build(on_launch, on_edit, on_delete)

    def _build(self, on_launch, on_edit, on_delete):
        # OS icon (emoji)
        os_type = self.vm.get("os_type", "linux").lower()
        icon = {"windows": "🪟", "linux": "🐧", "macos": "🍎",
                "other": "💿"}.get(os_type, "💿")

        top = tk.Frame(self, bg=CARD)
        top.pack(fill="x")

        icon_lbl = tk.Label(top, text=icon, font=("Segoe UI Emoji", 22),
                            bg=CARD, fg=TEXT)
        icon_lbl.pack(side="left", padx=(0, 10))

        info = tk.Frame(top, bg=CARD)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=self.vm.get("name", "VM"), font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w")

        details = (
            f"RAM: {self.vm.get('ram', 2048)} MB  •  "
            f"CPU: {self.vm.get('cpu', 2)} cores  •  "
            f"ISO(s): {len(self.vm.get('isos', []))}"
        )
        tk.Label(info, text=details, font=FONT_TINY, fg=TEXT_DIM, bg=CARD).pack(anchor="w")

        # Status dot
        isos = self.vm.get("isos", [])
        ready = any(os.path.exists(i) for i in isos) if isos else bool(self.vm.get("disk"))
        dot_color = SUCCESS if ready else WARNING
        tk.Label(top, text="●", fg=dot_color, bg=CARD,
                 font=("Segoe UI", 14)).pack(side="right", padx=4)

        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x", pady=(10, 8))

        # Buttons
        btns = tk.Frame(self, bg=CARD)
        btns.pack(fill="x")

        make_btn(btns, "▶  Démarrer", lambda: on_launch(self.vm),
                 color=SUCCESS, width=12).pack(side="left", padx=(0, 6))
        make_btn(btns, "✎  Modifier", lambda: on_edit(self.vm),
                 color=ACCENT2, width=10).pack(side="left", padx=(0, 6))
        make_btn(btns, "✕  Supprimer", lambda: on_delete(self.vm),
                 color=DANGER, width=10).pack(side="left")

        # ISOs list
        if isos:
            iso_frame = tk.Frame(self, bg=CARD)
            iso_frame.pack(fill="x", pady=(8, 0))
            tk.Label(iso_frame, text="ISOs :", font=FONT_TINY, fg=TEXT_DIM, bg=CARD).pack(anchor="w")
            for iso in isos[:3]:
                name = os.path.basename(iso)
                color = ACCENT if os.path.exists(iso) else DANGER
                tk.Label(iso_frame, text=f"  💿 {name}", font=FONT_MONO,
                         fg=color, bg=CARD).pack(anchor="w")
            if len(isos) > 3:
                tk.Label(iso_frame, text=f"  … +{len(isos)-3} ISO(s)",
                         font=FONT_TINY, fg=TEXT_DIM, bg=CARD).pack(anchor="w")


# ─────────────────────────────────────────────
#  VM CREATION / EDIT DIALOG
# ─────────────────────────────────────────────
class VMDialog(tk.Toplevel):
    def __init__(self, parent, config_manager, vm=None, on_save=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.existing_vm = vm
        self.on_save = on_save
        self.isos = list(vm.get("isos", [])) if vm else []
        self.title("Modifier la VM" if vm else "Nouvelle Machine Virtuelle")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self.geometry("620x700")
        self._center()

    def _center(self):
        self.update_idletasks()
        x = self.winfo_screenwidth() // 2 - 310
        y = self.winfo_screenheight() // 2 - 350
        self.geometry(f"+{x}+{y}")

    def _section(self, parent, title):
        tk.Label(parent, text=title, font=("Segoe UI", 10, "bold"),
                 fg=ACCENT, bg=BG).pack(anchor="w", pady=(14, 2))
        tk.Frame(parent, bg=ACCENT, height=1).pack(fill="x", pady=(0, 8))

    def _row(self, parent, label_text, widget):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label_text, font=FONT_BODY, fg=TEXT_DIM,
                 bg=BG, width=18, anchor="w").pack(side="left")
        widget_frame = tk.Frame(row, bg=BG)
        widget_frame.pack(side="left", fill="x", expand=True)
        widget.place_in = widget_frame
        widget.pack(in_=widget_frame, fill="x")
        return row

    def _entry(self, parent, default=""):
        e = tk.Entry(parent, bg=CARD2, fg=TEXT, insertbackground=ACCENT,
                     relief="flat", font=FONT_BODY, bd=4)
        if default:
            e.insert(0, str(default))
        return e

    def _combo(self, parent, values, default):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                        fieldbackground=CARD2, background=CARD2,
                        foreground=TEXT, arrowcolor=ACCENT,
                        selectbackground=CARD2, selectforeground=TEXT)
        c = ttk.Combobox(parent, values=values, state="readonly",
                         style="Dark.TCombobox", font=FONT_BODY)
        if default in values:
            c.set(default)
        else:
            c.current(0)
        return c

    def _build(self):
        vm = self.existing_vm or {}

        # Scrollable canvas
        canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG, padx=24, pady=16)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())

        inner.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_configure)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Header
        tk.Label(inner, text="🖥  Configuration VM",
                 font=("Segoe UI", 14, "bold"), fg=TEXT, bg=BG).pack(anchor="w")

        # ── Identité ──────────────────────────
        self._section(inner, "IDENTITÉ")

        name_e = self._entry(inner, vm.get("name", "Ma VM"))
        self._row(inner, "Nom de la VM", name_e)
        self.name_var = name_e

        os_types = ["windows", "linux", "macos", "other"]
        os_combo = self._combo(inner, os_types, vm.get("os_type", "linux"))
        self._row(inner, "Système d'exploitation", os_combo)
        self.os_combo = os_combo

        # ── Ressources ────────────────────────
        self._section(inner, "RESSOURCES")

        ram_e = self._entry(inner, vm.get("ram", 2048))
        self._row(inner, "RAM (Mo)", ram_e)
        self.ram_var = ram_e

        cpu_e = self._entry(inner, vm.get("cpu", 2))
        self._row(inner, "CPU (cœurs)", cpu_e)
        self.cpu_var = cpu_e

        # ── Disque ────────────────────────────
        self._section(inner, "DISQUE")

        disk_row = tk.Frame(inner, bg=BG)
        disk_row.pack(fill="x", pady=3)
        tk.Label(disk_row, text="Image disque (.img/.qcow2)",
                 font=FONT_BODY, fg=TEXT_DIM, bg=BG, width=28, anchor="w").pack(side="left")
        self.disk_var = tk.StringVar(value=vm.get("disk", ""))
        disk_e = tk.Entry(disk_row, textvariable=self.disk_var, bg=CARD2,
                          fg=TEXT, insertbackground=ACCENT, relief="flat",
                          font=FONT_MONO, bd=4, width=28)
        disk_e.pack(side="left", fill="x", expand=True, padx=(0, 6))
        make_btn(disk_row, "Parcourir", self._pick_disk, color=ACCENT, width=9).pack(side="left")

        # Créer image
        create_row = tk.Frame(inner, bg=BG)
        create_row.pack(fill="x", pady=(2, 0))
        tk.Label(create_row, text="", bg=BG, width=28).pack(side="left")
        self.disk_size_var = tk.StringVar(value="20")
        size_e = tk.Entry(create_row, textvariable=self.disk_size_var, bg=CARD2,
                          fg=TEXT, insertbackground=ACCENT, relief="flat",
                          font=FONT_BODY, bd=4, width=6)
        size_e.pack(side="left", padx=(0, 4))
        tk.Label(create_row, text="Go", font=FONT_BODY, fg=TEXT_DIM, bg=BG).pack(side="left", padx=(0, 8))
        make_btn(create_row, "Créer image", self._create_disk, color=CARD2, width=11).pack(side="left")

        # ── ISOs ──────────────────────────────
        self._section(inner, "IMAGES ISO")

        iso_header = tk.Frame(inner, bg=BG)
        iso_header.pack(fill="x")
        tk.Label(iso_header, text="Vous pouvez ajouter plusieurs ISOs (boot, pilotes, outils…)",
                 font=FONT_TINY, fg=TEXT_DIM, bg=BG).pack(side="left")
        make_btn(iso_header, "+ Ajouter ISO", self._add_iso, color=ACCENT, width=12).pack(side="right")

        self.iso_list_frame = tk.Frame(inner, bg=BG)
        self.iso_list_frame.pack(fill="x", pady=(6, 0))
        self._refresh_iso_list()

        # ── Réseau & Affichage ─────────────────
        self._section(inner, "RÉSEAU & AFFICHAGE")

        net_opts = ["user", "none"]
        net_combo = self._combo(inner, net_opts, vm.get("network", "user"))
        self._row(inner, "Réseau", net_combo)
        self.net_combo = net_combo

        display_opts = ["sdl", "gtk", "vnc", "none"]
        disp_combo = self._combo(inner, display_opts, vm.get("display", "sdl"))
        self._row(inner, "Affichage", disp_combo)
        self.disp_combo = disp_combo

        boot_opts = ["dc", "cd", "d", "c"]
        boot_combo = self._combo(inner, boot_opts, vm.get("boot_order", "dc"))
        self._row(inner, "Ordre de boot", boot_combo)
        self.boot_combo = boot_combo

        # ── Options ───────────────────────────
        self._section(inner, "OPTIONS")

        self.usb_var = tk.BooleanVar(value=vm.get("usb", True))
        self.audio_var = tk.BooleanVar(value=vm.get("audio", False))

        opts_row = tk.Frame(inner, bg=BG)
        opts_row.pack(anchor="w")
        for text, var in [("USB (tablet)", self.usb_var), ("Audio", self.audio_var)]:
            cb = tk.Checkbutton(opts_row, text=text, variable=var,
                                bg=BG, fg=TEXT, selectcolor=CARD2,
                                activebackground=BG, activeforeground=TEXT,
                                font=FONT_BODY)
            cb.pack(side="left", padx=(0, 20))

        # ── Save button ───────────────────────
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(20, 14))
        save_row = tk.Frame(inner, bg=BG)
        save_row.pack(fill="x")
        make_btn(save_row, "💾  Enregistrer", self._save, color=ACCENT, width=16).pack(side="right")
        make_btn(save_row, "Annuler", self.destroy, color=CARD2, width=10).pack(side="right", padx=(0, 8))

    def _refresh_iso_list(self):
        for w in self.iso_list_frame.winfo_children():
            w.destroy()
        for i, iso in enumerate(self.isos):
            row = tk.Frame(self.iso_list_frame, bg=CARD, padx=8, pady=4)
            row.pack(fill="x", pady=2)
            name = os.path.basename(iso)
            color = ACCENT if os.path.exists(iso) else DANGER
            tk.Label(row, text=f"💿 {name}", font=FONT_MONO, fg=color,
                     bg=CARD).pack(side="left", fill="x", expand=True)
            if i == 0:
                tk.Label(row, text="[BOOT]", font=FONT_TINY, fg=SUCCESS,
                         bg=CARD).pack(side="left", padx=6)
            idx = i
            make_btn(row, "✕", lambda _, x=idx: self._remove_iso(x),
                     color=DANGER, width=3).pack(side="right")

    def _add_iso(self):
        paths = filedialog.askopenfilenames(
            title="Sélectionner des fichiers ISO",
            filetypes=[("Images ISO", "*.iso *.img"), ("Tous", "*.*")],
        )
        for p in paths:
            if p not in self.isos:
                self.isos.append(p)
        self._refresh_iso_list()

    def _remove_iso(self, idx):
        if 0 <= idx < len(self.isos):
            self.isos.pop(idx)
        self._refresh_iso_list()

    def _pick_disk(self):
        p = filedialog.askopenfilename(
            title="Sélectionner une image disque",
            filetypes=[("Images disque", "*.img *.qcow2 *.vmdk *.vhd *.raw"),
                       ("Tous", "*.*")],
        )
        if p:
            self.disk_var.set(p)

    def _create_disk(self):
        size = self.disk_size_var.get().strip()
        try:
            size = int(size)
        except ValueError:
            messagebox.showerror("Erreur", "Taille invalide.")
            return

        path = filedialog.asksaveasfilename(
            title="Emplacement de l'image disque",
            defaultextension=".qcow2",
            filetypes=[("QCOW2", "*.qcow2"), ("RAW", "*.img")],
        )
        if not path:
            return

        qimg = shutil.which("qemu-img")
        if not qimg:
            messagebox.showerror("Erreur",
                                 "qemu-img introuvable. Installez QEMU pour créer des images.")
            return

        fmt = "qcow2" if path.endswith(".qcow2") else "raw"
        try:
            subprocess.run([qimg, "create", "-f", fmt, path, f"{size}G"],
                           check=True, capture_output=True)
            self.disk_var.set(path)
            messagebox.showinfo("Succès", f"Image disque créée :\n{path}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erreur", e.stderr.decode(errors="ignore"))

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Le nom de la VM est obligatoire.")
            return
        try:
            ram = int(self.ram_var.get())
            cpu = int(self.cpu_var.get())
        except ValueError:
            messagebox.showerror("Erreur", "RAM et CPU doivent être des entiers.")
            return

        vm_id = self.existing_vm["id"] if self.existing_vm else str(uuid.uuid4())[:8]
        vm = {
            "id": vm_id,
            "name": name,
            "os_type": self.os_combo.get(),
            "ram": ram,
            "cpu": cpu,
            "disk": self.disk_var.get(),
            "isos": self.isos,
            "network": self.net_combo.get(),
            "display": self.disp_combo.get(),
            "boot_order": self.boot_combo.get(),
            "usb": self.usb_var.get(),
            "audio": self.audio_var.get(),
        }
        self.config_manager.add_vm(vm)
        if self.on_save:
            self.on_save()
        self.destroy()


# ─────────────────────────────────────────────
#  QUICK LAUNCH DIALOG (juste une ISO)
# ─────────────────────────────────────────────
class QuickLaunchDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Démarrage rapide — ISO")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.isos = []
        self._build()
        self.geometry("520x380")
        x = self.winfo_screenwidth() // 2 - 260
        y = self.winfo_screenheight() // 2 - 190
        self.geometry(f"+{x}+{y}")

    def _build(self):
        tk.Label(self, text="🚀  Démarrage rapide", font=("Segoe UI", 13, "bold"),
                 fg=TEXT, bg=BG).pack(pady=(20, 4), padx=24, anchor="w")
        tk.Label(self, text="Lancez une ISO directement sans créer de VM.",
                 font=FONT_BODY, fg=TEXT_DIM, bg=BG).pack(padx=24, anchor="w")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", pady=14, padx=24)

        iso_row = tk.Frame(self, bg=BG, padx=24)
        iso_row.pack(fill="x")
        make_btn(iso_row, "+ Ajouter ISO(s)", self._add_isos, color=ACCENT, width=14).pack(side="left")

        self.iso_frame = tk.Frame(self, bg=BG, padx=24)
        self.iso_frame.pack(fill="x", pady=8)

        # RAM / CPU quick
        opt_row = tk.Frame(self, bg=BG, padx=24)
        opt_row.pack(fill="x", pady=4)
        tk.Label(opt_row, text="RAM (Mo):", font=FONT_BODY, fg=TEXT_DIM, bg=BG).pack(side="left")
        self.ram_e = tk.Entry(opt_row, bg=CARD2, fg=TEXT, insertbackground=ACCENT,
                              relief="flat", font=FONT_BODY, bd=4, width=7)
        self.ram_e.insert(0, "2048")
        self.ram_e.pack(side="left", padx=(4, 20))
        tk.Label(opt_row, text="CPU:", font=FONT_BODY, fg=TEXT_DIM, bg=BG).pack(side="left")
        self.cpu_e = tk.Entry(opt_row, bg=CARD2, fg=TEXT, insertbackground=ACCENT,
                              relief="flat", font=FONT_BODY, bd=4, width=4)
        self.cpu_e.insert(0, "2")
        self.cpu_e.pack(side="left", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", pady=14, padx=24)

        btn_row = tk.Frame(self, bg=BG, padx=24)
        btn_row.pack(fill="x")
        make_btn(btn_row, "▶  Lancer", self._launch, color=SUCCESS, width=12).pack(side="right")
        make_btn(btn_row, "Annuler", self.destroy, color=CARD2, width=9).pack(side="right", padx=(0, 8))

    def _add_isos(self):
        paths = filedialog.askopenfilenames(
            title="Choisir ISOs",
            filetypes=[("ISO", "*.iso *.img"), ("Tous", "*.*")],
        )
        for p in paths:
            if p not in self.isos:
                self.isos.append(p)
        self._refresh()

    def _refresh(self):
        for w in self.iso_frame.winfo_children():
            w.destroy()
        for iso in self.isos:
            tk.Label(self.iso_frame, text=f"💿 {os.path.basename(iso)}",
                     font=FONT_MONO, fg=ACCENT, bg=BG).pack(anchor="w")

    def _launch(self):
        if not self.isos:
            messagebox.showwarning("Attention", "Ajoutez au moins une ISO.")
            return
        try:
            ram = int(self.ram_e.get())
            cpu = int(self.cpu_e.get())
        except ValueError:
            messagebox.showerror("Erreur", "Valeurs RAM/CPU invalides.")
            return

        vm = {
            "id": "quick",
            "name": "Démarrage rapide",
            "os_type": "other",
            "ram": ram,
            "cpu": cpu,
            "disk": "",
            "isos": self.isos,
            "network": "user",
            "display": "sdl",
            "boot_order": "d",
            "usb": True,
            "audio": False,
        }
        self.destroy()

        def done(ok, err):
            if not ok:
                messagebox.showerror("Erreur QEMU", err or "Echec du lancement.")

        QEMULauncher.launch(vm, on_done=done)


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class VMManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_manager = VMConfig()
        self.title(APP_TITLE)
        self.configure(bg=BG)
        self.geometry("960x680")
        self.minsize(760, 500)
        self._build_ui()
        self._check_qemu()
        self.refresh_vm_list()

    def _check_qemu(self):
        if not QEMULauncher.find_qemu():
            self.status_bar.config(
                text="⚠  QEMU non détecté — installez QEMU et ajoutez-le au PATH pour lancer des VMs.",
                fg=WARNING,
            )

    # ── Layout ────────────────────────────────
    def _build_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=CARD, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Main area
        main = tk.Frame(self, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        # Topbar
        topbar = tk.Frame(main, bg=CARD, height=56)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        self._build_topbar(topbar)

        # Content (scrollable)
        self.content_canvas = tk.Canvas(main, bg=BG, bd=0, highlightthickness=0)
        vsb = tk.Scrollbar(main, orient="vertical", command=self.content_canvas.yview)
        self.content_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.content_canvas.pack(fill="both", expand=True)

        self.content_frame = tk.Frame(self.content_canvas, bg=BG, padx=24, pady=20)
        self._cwin = self.content_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        self.content_frame.bind("<Configure>", self._on_content_configure)
        self.content_canvas.bind("<Configure>", self._on_canvas_resize)
        self.content_canvas.bind_all("<MouseWheel>",
            lambda e: self.content_canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Status bar
        self.status_bar = tk.Label(main, text="Prêt.", font=FONT_TINY,
                                   fg=TEXT_DIM, bg=CARD, anchor="w", padx=12, pady=4)
        self.status_bar.pack(fill="x", side="bottom")

    def _on_content_configure(self, event):
        self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.content_canvas.itemconfig(self._cwin, width=event.width)

    def _build_sidebar(self):
        # Logo
        logo_frame = tk.Frame(self.sidebar, bg=CARD, pady=20)
        logo_frame.pack(fill="x")
        tk.Label(logo_frame, text="VM", font=("Consolas", 28, "bold"),
                 fg=ACCENT, bg=CARD).pack()
        tk.Label(logo_frame, text="Manager Pro", font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=CARD).pack()

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=16)

        # Nav items
        nav_items = [
            ("🖥  Mes VMs", self._show_vms),
            ("🚀  Lancement rapide", self._quick_launch),
            ("➕  Nouvelle VM", self._new_vm),
        ]
        for text, cmd in nav_items:
            btn = tk.Button(self.sidebar, text=text, command=cmd,
                            bg=CARD, fg=TEXT, activebackground=CARD2,
                            activeforeground=ACCENT, relief="flat",
                            font=FONT_SUB, cursor="hand2", anchor="w",
                            padx=18, pady=10, bd=0)
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=CARD2, fg=ACCENT))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=CARD, fg=TEXT))

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=10)

        # QEMU status
        qemu = QEMULauncher.find_qemu()
        qemu_text = "✅ QEMU détecté" if qemu else "❌ QEMU absent"
        qemu_color = SUCCESS if qemu else DANGER
        tk.Label(self.sidebar, text=qemu_text, font=FONT_TINY,
                 fg=qemu_color, bg=CARD, wraplength=180, justify="left",
                 padx=18).pack(anchor="w", pady=4)

        if qemu:
            short = os.path.basename(qemu)
            tk.Label(self.sidebar, text=short, font=FONT_MONO,
                     fg=TEXT_DIM, bg=CARD, padx=18).pack(anchor="w")

    def _build_topbar(self, bar):
        tk.Label(bar, text=APP_TITLE, font=("Segoe UI", 13, "bold"),
                 fg=TEXT, bg=CARD).pack(side="left", padx=20)

        make_btn(bar, "➕ Nouvelle VM", self._new_vm,
                 color=ACCENT, width=14).pack(side="right", padx=12, pady=10)
        make_btn(bar, "🚀 Rapide", self._quick_launch,
                 color=ACCENT2, width=10).pack(side="right", pady=10)

    # ── VM List ───────────────────────────────
    def _show_vms(self):
        pass  # current view

    def refresh_vm_list(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

        vms = self.config_manager.list_vms()

        if not vms:
            empty = tk.Frame(self.content_frame, bg=BG)
            empty.pack(expand=True, fill="both", pady=60)
            tk.Label(empty, text="🖥", font=("Segoe UI Emoji", 48),
                     bg=BG, fg=TEXT_DIM).pack()
            tk.Label(empty, text="Aucune machine virtuelle",
                     font=("Segoe UI", 14, "bold"), fg=TEXT_DIM, bg=BG).pack(pady=4)
            tk.Label(empty, text="Créez votre première VM ou faites un démarrage rapide.",
                     font=FONT_BODY, fg=TEXT_DIM, bg=BG).pack()
            make_btn(empty, "➕ Créer une VM", self._new_vm,
                     color=ACCENT, width=16).pack(pady=16)
            return

        tk.Label(self.content_frame, text=f"Mes machines virtuelles  ({len(vms)})",
                 font=("Segoe UI", 13, "bold"), fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 16))

        for vm in vms:
            card = VMCard(
                self.content_frame, vm,
                on_launch=self._launch_vm,
                on_edit=self._edit_vm,
                on_delete=self._delete_vm,
            )
            card.pack(fill="x", pady=(0, 10))

    # ── Actions ───────────────────────────────
    def _new_vm(self):
        VMDialog(self, self.config_manager, on_save=self.refresh_vm_list)

    def _edit_vm(self, vm):
        VMDialog(self, self.config_manager, vm=vm, on_save=self.refresh_vm_list)

    def _delete_vm(self, vm):
        if messagebox.askyesno("Supprimer",
                               f"Supprimer la VM « {vm['name']} » ?\n(Les fichiers ne seront pas supprimés.)"):
            self.config_manager.remove_vm(vm["id"])
            self.refresh_vm_list()

    def _launch_vm(self, vm):
        self.status_bar.config(text=f"⏳  Démarrage de « {vm['name']} »…", fg=WARNING)

        def done(ok, err):
            if ok:
                self.status_bar.config(text=f"✅  « {vm['name']} » s'est terminé normalement.", fg=SUCCESS)
            else:
                self.status_bar.config(text=f"❌  Erreur : {err[:80]}", fg=DANGER)
                messagebox.showerror("Erreur QEMU", err or "Impossible de démarrer la VM.")

        QEMULauncher.launch(vm, on_done=done)

    def _quick_launch(self):
        QuickLaunchDialog(self)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = VMManagerApp()
    app.mainloop()

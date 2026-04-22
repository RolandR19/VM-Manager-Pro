"""
Build script — compile vm_manager.py en exécutable .exe (Windows) ou binaire Linux.
Usage :
  pip install pyinstaller
  python build.py
"""

import subprocess
import sys
import os
import platform

SCRIPT = "vm_manager.py"
APP_NAME = "VM Manager Pro"
ICON = "icon.ico"  # optionnel : placez un .ico ici

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",            # tout en un seul .exe
    "--windowed",           # pas de console (GUI uniquement)
    "--name", APP_NAME,
    "--clean",
]

# Icône (optionnel)
if os.path.exists(ICON) and platform.system() == "Windows":
    cmd += ["--icon", ICON]

# Fichier principal
cmd.append(SCRIPT)

print("=" * 60)
print(f"  Build : {APP_NAME}")
print(f"  OS    : {platform.system()}")
print("=" * 60)

result = subprocess.run(cmd)

if result.returncode == 0:
    out = os.path.join("dist", APP_NAME + (".exe" if platform.system() == "Windows" else ""))
    print(f"\n✅  Succès ! Exécutable : {out}")
else:
    print("\n❌  Échec du build. Vérifiez que PyInstaller est installé.")
    print("    pip install pyinstaller")

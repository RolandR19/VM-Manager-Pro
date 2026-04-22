# VM Manager Pro 🖥

Gestionnaire de machines virtuelles avec interface graphique moderne, basé sur **QEMU**.

---

## Fonctionnalités

- ✅ Créer, modifier, supprimer des VMs
- 💿 Ouvrir **plusieurs ISOs** simultanément (boot + pilotes + outils)
- 🚀 **Démarrage rapide** : lancer une ISO sans créer de VM
- ⚙️ Configuration complète : RAM, CPU, disque, réseau, affichage
- 🗂 Création d'images disque QCOW2 / RAW intégrée
- 💾 Sauvegarde automatique des configs en JSON
- 🎨 Interface sombre moderne

---

## Prérequis

### 1. Python 3.8+
https://www.python.org/downloads/

### 2. QEMU
**Windows :** https://www.qemu.org/download/#windows  
Installez et **ajoutez QEMU au PATH** (ex : `C:\Program Files\qemu`)

**Linux :**
```bash
sudo apt install qemu-system-x86
```

**macOS :**
```bash
brew install qemu
```

---

## Lancer l'application

```bash
python vm_manager.py
```

---

## Compiler en .exe (Windows)

```bash
pip install pyinstaller
python build.py
```

L'exécutable sera dans le dossier `dist/`.

---

## Créer une VM — Guide rapide

1. Cliquez **➕ Nouvelle VM**
2. Donnez un nom, choisissez l'OS
3. Ajoutez votre ISO avec **+ Ajouter ISO**
4. (Optionnel) Créez une image disque avec **Créer image**
5. Cliquez **Enregistrer**
6. Dans la liste, cliquez **▶ Démarrer**

---

## Démarrage rapide

Cliquez **🚀 Rapide** pour lancer directement une ou plusieurs ISOs  
sans créer de VM sauvegardée.

---

## Structure des fichiers

```
vm_manager.py    # Application principale
build.py         # Script de compilation .exe
vm_config.json   # Configuration des VMs (auto-généré)
```

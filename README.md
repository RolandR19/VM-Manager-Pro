# VM Manager Pro 🖥️

A modern graphical virtual machine manager based on **QEMU**.

---

## Features

- ✅ **Manage VMs:** Create, edit, and delete virtual machines with ease.
- 💿 **Multi-ISO Support:** Open multiple ISO files simultaneously (boot, drivers, tools).
- 🚀 **Quick Start:** Launch an ISO instantly without creating a permanent VM.
- ⚙️ **Full Configuration:** Custom RAM, CPU, disk, network, and display settings.
- 🗂 **Integrated Storage:** Built-in QCOW2 and RAW disk image creation.
- 💾 **Auto-Save:** VM configurations are automatically saved in JSON format.
- 🎨 **Modern UI:** Sleek dark-mode interface.

---

## Prerequisites

### 1. Python 3.8+
[Download Python](https://www.python.org/downloads/)

### 2. QEMU
**Windows:** [Download QEMU for Windows](https://www.qemu.org/download/#windows)  
Install and **add QEMU to your PATH** (e.g., `C:\Program Files\qemu`).

**Linux:**
```bash
sudo apt install qemu-system-x86
```

**macOS:**
```bash
brew install qemu
```

---

## Running the Application

```bash
python vm_manager.py
```

---

## Building the .exe (Windows)

```bash
pip install pyinstaller
python build.py
```

The executable will be located in the `dist/` folder.

---

## Quick Start Guide: Creating a VM

1. Click **➕ New VM**.
2. Name your machine and choose the OS.
3. Attach your ISO via **+ Add ISO**.
4. (Optional) Create a disk image using **Create Image**.
5. Click **Save**.
6. Select your VM from the list and click **▶ Start**.

---

## Adding QEMU to the Windows "PATH"
This step ensures the Python script can locate QEMU automatically without manual code modifications.

1. Press the **Windows Key** and type "Environment Variables."
2. Select **"Edit the system environment variables."**
3. In the window that appears, click the **Environment Variables** button at the bottom right.
4. Under **System variables** (the bottom section), find the **Path** variable and click **Edit**.
5. Click **New** on the right side.
6. Paste the following path: `C:\Program Files\qemu` (or the folder where QEMU was installed).
7. Click **OK** on all windows to save changes.

> **Note:** Restart your code editor (VS Code, PyCharm) or terminal for the changes to take effect.

---

## Instant Launch

Click **🚀 Quick** to directly boot one or more ISOs without saving a VM configuration.

---

## File Structure

```text
vm_manager.py    # Main application
build.py         # Compilation script for .exe
vm_config.json   # VM configurations (auto-generated)
```

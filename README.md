# Cyanide Installer

A robust, thread-safe Python backend and D-Bus daemon for installing Arch Linux. This project provides a standalone CLI and a D-Bus API designed to be driven by a GUI frontend (like a Vala application).

## Features

- **D-Bus Daemon**: Asynchronous architecture preventing GUI blocking during long-running tasks.
- **Declarative JSON Config**: Defines the entire installation state (partitions, locale, users, packages).
- **Offline Support**: Extracts `airootfs.sfs` natively with `unsquashfs` when in offline mode.
- **Smart Partitioning**: Handles standard, NVMe, and Loop device naming schemas dynamically.
- **Hierarchical Mounting**: Mounts and unmounts systems based on path depth to prevent collision.

## Requirements

Before running the installer, ensure the host environment (or Arch Live ISO) has the following packages installed:
```bash
# Example for Arch Linux
pacman -Sy python python-pydantic python-gobject parted squashfs-tools
```
*(Note: `python-pydbus` may also be required depending on how you expose the D-Bus interface, though `python-gobject` provides the foundational bindings).*

## Setup & Execution

### 1. D-Bus Policies

To allow the GUI (running as a live user) to talk to the installer daemon (running as root), copy the D-Bus policy to your system directory:

```bash
sudo cp dbus/org.archinstaller.conf /etc/dbus-1/system.d/
sudo systemctl reload dbus
```

### 2. Running the Daemon

Start the installer backend in daemon mode. This will bind to `org.archinstaller` on the system bus. It must be run as root.

```bash
sudo python daemon.py
```

### 3. Testing with the CLI

You can bypass the daemon and run an installation directly via the CLI using a JSON configuration file. 

```bash
sudo python cli.py example_install.json
```

To list available storage devices for testing:
```bash
sudo python cli.py --list-disks
```

## Configuration Format

See `example_install.json` for a fully functional demonstrational install configuration. 

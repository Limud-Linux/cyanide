import subprocess
import json
import time
import os
from .events import ProgressObserver
from .config import InstallConfig, Partition

def get_partition_path(disk: str, index: int) -> str:
    """Safely determines the partition node path."""
    if disk[-1].isdigit() or "loop" in disk or "nvme" in disk:
        return f"{disk}p{index}"
    return f"{disk}{index}"

def list_disks() -> str:
    """Returns JSON array of block devices."""
    try:
        result = subprocess.run(
            ["lsblk", "-J", "-b", "-p", "-o", "NAME,SIZE,TYPE,MODEL,TRAN"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        disks = [d for d in data.get("blockdevices", []) if d.get("type") in ("disk", "loop")]
        return json.dumps(disks)
    except Exception:
        return "[]"

def partition_disk(config: InstallConfig, observer: ProgressObserver):
    disk = config.disk
    observer.on_progress(5, "partitioning", f"Wiping disk {disk}")
    subprocess.run(["wipefs", "-a", disk], check=True)
    subprocess.run(["parted", "-s", disk, "mklabel", "gpt"], check=True)
    
    sfdisk_script = "label: gpt\n"
    type_map = {
        "efi": "C12A7328-F81F-11D2-BA4B-00A0C93EC93B",
        "swap": "0657FD6D-A4AB-43C4-84E5-0933C84B4F4F",
        "root": "4F68BCE3-E8CD-4DB1-96E7-FBCAF984B709",
        "home": "933AC7E1-2EB4-4F13-B844-0E14E2AEF915"
    }

    for part in config.partitions:
        ptype = type_map.get(part.type, "0FC63DAF-8483-4772-8E79-3D69D8477DE4")
        if part.size == "100%":
            sfdisk_script += f"size=+, type={ptype}\n"
        else:
            sfdisk_script += f"size={part.size}, type={ptype}\n"
            
    observer.on_progress(10, "partitioning", "Creating partition table")
    
    # Use --wipe always to destroy old filesystem signatures on the new partitions
    subprocess.run(["sfdisk", "--wipe", "always", disk], input=sfdisk_script, text=True, check=True)
    
    # Force kernel to re-read and udev to settle so device nodes (/dev/sda1) are ready
    subprocess.run(["partprobe", disk], check=False)
    subprocess.run(["udevadm", "settle"], check=False)
    time.sleep(2)
    
    for i, part in enumerate(config.partitions):
        part_index = i + 1
        path = get_partition_path(disk, part_index)
        observer.on_progress(15 + i*2, "formatting", f"Formatting {path} as {part.fs}")
        
        if part.fs == "fat32":
            subprocess.run(["mkfs.fat", "-F32", path], check=True)
        elif part.fs == "swap":
            subprocess.run(["mkswap", path], check=True)
        elif part.fs == "ext4":
            subprocess.run(["mkfs.ext4", "-F", path], check=True)
        elif part.fs == "btrfs":
            subprocess.run(["mkfs.btrfs", "-f", path], check=True)

def mount_partitions(config: InstallConfig, observer: ProgressObserver):
    mounts = []
    for i, part in enumerate(config.partitions):
        if part.mountpoint and part.mountpoint != "none":
            path = get_partition_path(config.disk, i + 1)
            mounts.append((part.mountpoint, path))
            
    # Sort mounts by path depth, so "/" mounts before "/boot"
    mounts.sort(key=lambda x: x[0])
    
    for mountpoint, device_path in mounts:
        target = f"/mnt{mountpoint}"
        observer.on_progress(25, "mounting", f"Mounting {device_path} to {target}")
        os.makedirs(target, exist_ok=True)
        subprocess.run(["mount", device_path, target], check=True)
        
def unmount_partitions(observer: ProgressObserver):
    observer.on_progress(95, "unmounting", "Unmounting filesystems")
    subprocess.run(["umount", "-R", "/mnt"], check=False)

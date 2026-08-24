from pydantic import BaseModel
from typing import List, Optional

class Partition(BaseModel):
    type: str          # 'efi', 'swap', 'root', 'home', etc.
    size: str          # '512M', '4G', '100%'
    fs: str            # 'fat32', 'swap', 'ext4', 'btrfs'
    mountpoint: str = "none" # e.g., '/boot', '/', 'none' for swap

class User(BaseModel):
    username: str
    password: str
    sudo: bool = False

class InstallConfig(BaseModel):
    disk: str
    partitions: List[Partition]
    locale: str = "en_US.UTF-8"
    timezone: str = "UTC"
    hostname: str = "archlinux"
    root_password: str
    users: List[User] = []
    bootloader: str = "grub" # 'grub' or 'systemd-boot'
    packages: List[str] = ["base", "linux", "linux-firmware"]
    services: List[str] = []
    offline_mode: bool = False

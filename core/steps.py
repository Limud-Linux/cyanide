import subprocess
import os
from .events import ProgressObserver
from .config import InstallConfig

def install_base(config: InstallConfig, observer: ProgressObserver):
    airootfs_path = "/run/archiso/bootmnt/arch/x86_64/airootfs.sfs"
    if config.offline_mode and os.path.exists(airootfs_path):
        observer.on_progress(30, "install_base", "Extracting squashfs (offline mode)")
        subprocess.run(["unsquashfs", "-f", "-d", "/mnt", airootfs_path], check=True)
    else:
        observer.on_progress(30, "install_base", "Running pacstrap")
        cmd = ["pacstrap", "-K", "/mnt"] + config.packages
        subprocess.run(cmd, check=True)

def configure_system(config: InstallConfig, observer: ProgressObserver):
    observer.on_progress(60, "configure", "Configuring system settings")
    
    # Generate fstab
    with open("/mnt/etc/fstab", "w") as f:
        subprocess.run(["genfstab", "-U", "/mnt"], stdout=f, check=True)

    def chroot(cmd: list[str]):
        subprocess.run(["arch-chroot", "/mnt"] + cmd, check=True)

    # Timezone
    chroot(["ln", "-sf", f"/usr/share/zoneinfo/{config.timezone}", "/etc/localtime"])
    chroot(["hwclock", "--systohc"])
    
    # Locale
    with open("/mnt/etc/locale.gen", "a") as f:
        f.write(f"\n{config.locale} UTF-8\n")
    chroot(["locale-gen"])
    with open("/mnt/etc/locale.conf", "w") as f:
        f.write(f"LANG={config.locale}\n")

    # Hostname
    with open("/mnt/etc/hostname", "w") as f:
        f.write(config.hostname + "\n")

    # Users
    observer.on_progress(70, "users", "Configuring users")
    
    # Root password via chpasswd
    subprocess.run(["arch-chroot", "/mnt", "chpasswd"], input=f"root:{config.root_password}\n", text=True, check=True)

    for user in config.users:
        chroot(["useradd", "-m", "-G", "wheel", user.username])
        subprocess.run(["arch-chroot", "/mnt", "chpasswd"], input=f"{user.username}:{user.password}\n", text=True, check=True)
        if user.sudo:
            # Enable wheel group in sudoers safely
            sudoers_d_file = f"/mnt/etc/sudoers.d/{user.username}"
            with open(sudoers_d_file, "w") as f:
                f.write(f"{user.username} ALL=(ALL:ALL) ALL\n")

    # Services
    for service in config.services:
        chroot(["systemctl", "enable", service])

    # Kernel Modules / Initramfs (Crucial for offline mode)
    observer.on_progress(80, "mkinitcpio", "Generating initramfs")
    chroot(["mkinitcpio", "-P"])

def install_bootloader(config: InstallConfig, observer: ProgressObserver):
    observer.on_progress(85, "bootloader", f"Installing {config.bootloader}")
    
    def chroot(cmd: list[str]):
        subprocess.run(["arch-chroot", "/mnt"] + cmd, check=True)

    if config.bootloader == "grub":
        # pacman might fail in offline mode without internet, but standard squashfs might have it
        # Assume it's available or we install it if online
        chroot(["pacman", "-S", "--noconfirm", "--needed", "grub", "efibootmgr"])
        chroot(["grub-install", "--target=x86_64-efi", "--efi-directory=/boot", "--bootloader-id=GRUB"])
        chroot(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"])
    elif config.bootloader == "systemd-boot":
        chroot(["bootctl", "install"])
        # Simplified systemd-boot config
        pass

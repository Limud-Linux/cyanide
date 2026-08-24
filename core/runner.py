from .config import InstallConfig
from .events import ProgressObserver
from . import disk
from . import steps
import traceback

class Runner:
    def __init__(self, config: InstallConfig, observer: ProgressObserver):
        self.config = config
        self.observer = observer

    def run(self):
        try:
            self.observer.on_progress(1, "start", "Starting installation")
            
            disk.partition_disk(self.config, self.observer)
            disk.mount_partitions(self.config, self.observer)
            
            steps.install_base(self.config, self.observer)
            steps.configure_system(self.config, self.observer)
            steps.install_bootloader(self.config, self.observer)
            
            disk.unmount_partitions(self.observer)
            
            self.observer.on_progress(100, "done", "Finished all steps")
            self.observer.on_finished(True, "Installation complete.")
            
        except Exception as e:
            error_details = traceback.format_exc()
            try:
                disk.unmount_partitions(self.observer)
            except Exception:
                pass
            self.observer.on_finished(False, f"Error: {str(e)}\n{error_details}")

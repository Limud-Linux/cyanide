import sys
import json
import threading
from pydantic import ValidationError

import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib

# We use pydbus for clean D-Bus publishing, but raw PyGObject is possible too.
# pydbus dynamically inspects the XML docstring.
from pydbus import SystemBus

from core.config import InstallConfig
from core.events import ProgressObserver
from core.runner import Runner
from core import disk

class DBusObserver(ProgressObserver):
    def __init__(self, service):
        self.service = service

    def on_progress(self, percent: int, stage: str, message: str):
        # Thread-safe signal emission via GLib main loop
        GLib.idle_add(self.service.Progress, percent, stage, message)

    def on_finished(self, success: bool, details: str):
        GLib.idle_add(self.service.Finished, success, details)

class InstallerService:
    """
    <node>
        <interface name='org.cyanide.Service'>
            <method name='ListDisks'>
                <arg type='s' name='disks_json' direction='out'/>
            </method>
            <method name='StartInstall'>
                <arg type='s' name='config_json' direction='in'/>
                <arg type='b' name='started' direction='out'/>
            </method>
            <method name='CancelInstall'>
                <arg type='b' name='cancelled' direction='out'/>
            </method>
            <signal name='Progress'>
                <arg type='i' name='percent'/>
                <arg type='s' name='stage'/>
                <arg type='s' name='message'/>
            </signal>
            <signal name='Finished'>
                <arg type='b' name='success'/>
                <arg type='s' name='details'/>
            </signal>
        </interface>
    </node>
    """
    
    def __init__(self):
        self._thread = None

    def ListDisks(self) -> str:
        return disk.list_disks()

    def StartInstall(self, config_json: str) -> bool:
        if self._thread and self._thread.is_alive():
            return False # Installation already in progress

        try:
            data = json.loads(config_json)
            config = InstallConfig(**data)
        except Exception as e:
            # Emit Finished with error in next idle loop if parsing fails,
            # so the caller who receives 'True' from StartInstall gets the error right after.
            # However, if parsing fails, we could just return False.
            # But the UI might expect a signal if it returns True. Let's return False here.
            return False

        observer = DBusObserver(self)
        runner = Runner(config, observer)
        
        self._thread = threading.Thread(target=runner.run, daemon=True)
        self._thread.start()
        
        return True

    def CancelInstall(self) -> bool:
        # Proper cancellation requires subprocess killing and thread signaling.
        # Stubbed for now.
        return False

def main():
    bus = SystemBus()
    
    try:
        bus.publish("org.cyanide", InstallerService())
    except Exception as e:
        print(f"Failed to publish service. Ensure you are running as root and D-Bus policies are installed: {e}", file=sys.stderr)
        sys.exit(1)

    print("D-Bus service 'org.cyanide' is running.")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Shutting down daemon.")

if __name__ == "__main__":
    main()

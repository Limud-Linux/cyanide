import argparse
import json
import sys
from pydantic import ValidationError
from core.config import InstallConfig
from core.events import ProgressObserver
from core.runner import Runner
from core import disk

class CLIObserver(ProgressObserver):
    def on_progress(self, percent: int, stage: str, message: str):
        print(f"[{percent:3d}%] {stage.upper()}: {message}")

    def on_finished(self, success: bool, details: str):
        if success:
            print(f"\nSUCCESS: {details}")
            sys.exit(0)
        else:
            print(f"\nFAILED: {details}", file=sys.stderr)
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Arch Linux Installer CLI")
    parser.add_argument("config", nargs='?', help="Path to JSON config file")
    parser.add_argument("--list-disks", action="store_true", help="List available disks and exit")
    args = parser.parse_args()

    if args.list_disks:
        print(disk.list_disks())
        sys.exit(0)

    if not args.config:
        parser.print_help()
        sys.exit(1)

    with open(args.config, "r") as f:
        try:
            data = json.load(f)
            config = InstallConfig(**data)
        except ValidationError as e:
            print("Configuration Validation Error:")
            print(e)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading config: {e}")
            sys.exit(1)

    observer = CLIObserver()
    runner = Runner(config, observer)
    runner.run()

if __name__ == "__main__":
    main()

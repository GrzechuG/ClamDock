import argparse
import subprocess
import os
import sqlite3
import time
import sys
import tkinter
from tkinter import messagebox
import json

class DockerDefender:
    def __init__(self):
        self.db_path = "docker_defender.db"
        self.scan_command = self.detect_clamav()  # Detect best scanning method
        self.static_scan_params = ["--fdpass"] if self.scan_command == "clamdscan" else []
        self.check_if_root()
        self.create_db()

    def run_scan_command(self, scan_command, prefix):
        return self.remove_docker_paths_from_output(subprocess.run(scan_command + self.static_scan_params, capture_output=True, text=True).stdout, prefix)

    def detect_clamav(self):
        """Detects if clamscan or clamdscan is available and sets the best scanning method."""
        try:
            subprocess.run(["clamdscan", "--version"], capture_output=True, text=True, check=True)
            print("✔ Using clamdscan (recommended for better performance).")
            return "clamdscan"
        except subprocess.CalledProcessError:
            try:
                subprocess.run(["clamscan", "--version"], capture_output=True, text=True, check=True)
                print("✔ Using clamscan.")
                print("⚠️ Warning: clamdscan is faster and recommended. Install it for better performance.")
                return "clamscan"
            except subprocess.CalledProcessError:
                print("❌ ClamAV is not installed. Please install it before using DockerDefender.")
                sys.exit(1)

    def check_if_root(self):
        """Checks if the script is running as root."""
        if os.geteuid() != 0:
            print("❌ This script must be run as root or with sudo privileges.")
            sys.exit(1)

    def create_db(self):
        """Creates the SQLite database for storing file paths if it does not exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                container_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def get_running_containers(self):
        """Returns a list of running Docker container IDs."""
        result = subprocess.run(["docker", "ps", "--format", "{{.ID}}"], capture_output=True, text=True)
        return result.stdout.strip().split("\n") if result.stdout else []

    def get_container_folders(self, container_id):
        """Gets the overlay mounted paths for a given container."""
        try:
            inspect_cmd = ["docker", "container", "inspect", "--format", "{{json .GraphDriver.Data }}", container_id]
            result = subprocess.run(inspect_cmd, capture_output=True, text=True, check=True)
            graph_data = json.loads(result.stdout.strip())
            return {
                "LowerDir": graph_data.get("LowerDir"),
                "MergedDir": graph_data.get("MergedDir"),
                "UpperDir": graph_data.get("UpperDir"),
                "WorkDir": graph_data.get("WorkDir")
            }
        except subprocess.CalledProcessError:
            print(f"❌ Error inspecting container {container_id}.")
            return None

    def list_files_in_directory(self, directory):
        """Recursively lists all files under a given directory."""
        file_paths = []
        for root, _, files in os.walk(directory):
            for file in files:
                file_paths.append(os.path.join(root, file))
        return file_paths

    def remove_docker_paths_from_output(self, output, prefix):
        lst = output.split("\n")
        return "\n".join([line if not line.startswith(prefix) else line.replace(prefix, "") for line in lst ])


    def store_file_paths(self, container_id, file_paths):
        """Stores new file paths in the database and removes deleted ones."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get existing files from the DB
        cursor.execute("SELECT file_path FROM files WHERE container_id = ?", (container_id,))
        existing_files = {row[0] for row in cursor.fetchall()}

        new_files = [file for file in file_paths if file not in existing_files]
        deleted_files = [file for file in existing_files if file not in file_paths]

        # Add new files
        for file_path in new_files:
            cursor.execute("INSERT INTO files (container_id, file_path) VALUES (?, ?)", (container_id, file_path))

        # Remove deleted files
        for file_path in deleted_files:
            cursor.execute("DELETE FROM files WHERE container_id = ? AND file_path = ?", (container_id, file_path))

        conn.commit()
        conn.close()

    def detect_new_files(self, container_id, current_file_paths):
        """Detects newly created files in a container."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM files WHERE container_id = ?", (container_id,))
        existing_files = {row[0] for row in cursor.fetchall()}
        conn.close()
        return [file for file in current_file_paths if file not in existing_files]

    def scan_container(self, container_id, auto_delete=False):
        """Scans a Docker container using ClamAV."""
        print(f"🔍 Scanning container: {container_id}...")
        folders = self.get_container_folders(container_id)
        merged = folders["MergedDir"]

        scan_command = [self.scan_command, "-ri", merged]
        if auto_delete:
            scan_command.append("--remove")

        result = result = self.run_scan_command(scan_command, merged)
        print(result)
        if "FOUND" in result:
            print(f"⚠️ Malware detected in container {container_id}!")
            return result
        print(f"✅ No threats found in container {container_id}.")
        return None

    def scan_all_containers(self, auto_delete=False, popup=False):
        """Scans all running containers."""
        containers = self.get_running_containers()
        if not containers:
            print("⚠️ No running containers found.")
            return
        for container_id in containers:
            detection = self.scan_container(container_id, auto_delete)
            if detection and popup:
                self.show_popup(f"Malware detected in container {container_id}!")

    def scan_new_files(self, container_id, auto_delete=False, popup=False):
        """Scans newly created files in a container."""
        folders = self.get_container_folders(container_id)
        merged = folders["MergedDir"]
        current_files = self.list_files_in_directory(merged)
        new_files = self.detect_new_files(container_id, current_files)

        if new_files:
            print(f"🔍 Scanning new files in container {container_id}...")
            with open("/tmp/file-list.txt", "w") as f:
                f.writelines(f"{file}\n" for file in new_files)

            scan_command = [self.scan_command, "-i", "--file-list=/tmp/file-list.txt"]
            if auto_delete:
                scan_command.append("--remove")

            result = self.run_scan_command(scan_command, merged)
            if "FOUND" in result:
                print(f"⚠️ Malware detected in container {container_id}!")
                if popup:
                    self.show_popup(f"Malware detected in {container_id}!")

            print(result)

        self.store_file_paths(container_id, current_files)

    def monitor_containers(self, interval=60, popup=False, auto_delete=False):
        """Continuously monitors running containers for new files and scans them."""
        print("🔄 Monitoring containers for threats. Press Ctrl+C to stop.")
        try:
            while True:
                for container_id in self.get_running_containers():
                    self.scan_new_files(container_id, auto_delete, popup)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped.")

    def show_popup(self, message):
        """Displays a popup notification."""
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showwarning("DockerDefender Alert", message)
        root.destroy()

def main():
    defender = DockerDefender()
    
    parser = argparse.ArgumentParser(description="DockerDefender - Docker Malware Scanner")
    parser.add_argument("command", choices=["scan", "monitor", "defend"], help="Choose a mode")
    parser.add_argument("--popup", action="store_true", help="Show popup on detection")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring interval (default: 60s)")

    args = parser.parse_args()
    
    if args.command == "scan":
        defender.scan_all_containers()
    elif args.command == "monitor":
        defender.monitor_containers(args.interval, args.popup)
    elif args.command == "defend":
        defender.scan_all_containers(auto_delete=True)

if __name__ == "__main__":
    main()

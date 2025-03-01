import argparse
import subprocess
import time
import os
import sys
import tkinter
from tkinter import messagebox

# Function to check if clamscan is installed
def check_clamscan():
    try:
        result = subprocess.run(["clamscan", "--version"], capture_output=True, text=True, check=True)
        print(f"✔ ClamAV Installed: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ ClamAV is not installed. Please install it before using DockerDefender.")
        sys.exit(1)

# Function to check if script is running as root
def check_if_root():
    if os.geteuid() != 0:
        print("❌ This script must be run as root or with sudo privileges.")
        sys.exit(1)

# Function to get all running Docker container IDs
def get_running_containers():
    result = subprocess.run(["docker", "ps", "--format", "{{.ID}}"], capture_output=True, text=True)
    return result.stdout.strip().split("\n") if result.stdout else []

import subprocess
import json

# Function to get folder mappings for a container ID
def get_container_folders(container_id):
    try:
        # Inspect container and get its GraphDriver data in JSON format
        inspect_cmd = [
            "docker", "container", "inspect", 
            "--format", "{{json .GraphDriver.Data }}", container_id
        ]
        result = subprocess.run(inspect_cmd, capture_output=True, text=True, check=True)
        
        # Parse the JSON result
        graph_data = json.loads(result.stdout.strip())
        
        # Return a dictionary of folder paths (LowerDir, MergedDir, UpperDir, WorkDir)
        return {
            "LowerDir": graph_data.get("LowerDir"),
            "MergedDir": graph_data.get("MergedDir"),
            "UpperDir": graph_data.get("UpperDir"),
            "WorkDir": graph_data.get("WorkDir")
        }
    
    except subprocess.CalledProcessError as e:
        print(f"Error inspecting container {container_id}: {e}")
        return None


# Function to scan a specific Docker container
def scan_container(container_id, auto_delete=False):
    print(f"🔍 Scanning container: {container_id}...")
    folders = get_container_folders(container_id)
    merged = folders["MergedDir"]

    # Run clamscan inside the container
    scan_command = ["clamscan", "-ri", merged]
    if auto_delete:
        scan_command.append("--remove")  # Enable auto-delete if 'defend' mode is on

    result = subprocess.run(scan_command, capture_output=True, text=True)
    print(result.stdout)
    if "FOUND" in result.stdout:
        print(f"⚠️ Malware detected in container {container_id}:\n{result.stdout}")
        return result.stdout
    else:
        print(f"✅ No threats found in container {container_id}.")
        return None

# Function to show a popup notification
def show_popup(message):
    root = tkinter.Tk()
    root.withdraw()
    messagebox.showwarning("DockerDefender Alert", message)
    root.destroy()

# Function to scan all running containers
def scan_all_containers(auto_delete=False, popup=False):
    containers = get_running_containers()
    if not containers:
        print("⚠️ No running containers found.")
        return
    
    for container_id in containers:
        detection = scan_container(container_id, auto_delete)
        if detection and popup:
            show_popup(f"Malware detected in container {container_id}!")

# Function to monitor containers in a loop
def monitor_containers(interval=60, popup=False, auto_delete=False):
    print("🔄 Monitoring containers for threats. Press Ctrl+C to stop.")
    try:
        while True:
            scan_all_containers(auto_delete, popup)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped.")

# Main function to handle command-line arguments
def main():
    parser = argparse.ArgumentParser(description="DockerDefender - Docker Malware Scanner using ClamAV")
    
    parser.add_argument("command", choices=["scan", "monitor", "defend"], help="Choose a mode to run DockerDefender")
    parser.add_argument("--popup", action="store_true", help="Show a popup notification when malware is detected")
    parser.add_argument("--interval", type=int, default=60, help="Interval for monitoring mode (default: 60 seconds)")
    
    args = parser.parse_args()
    
    check_if_root()
    check_clamscan()  # Ensure ClamAV is installed
    
    if args.command == "scan":
        scan_all_containers()
    
    elif args.command == "monitor":
        monitor_containers(args.interval, args.popup)

    elif args.command == "defend":
        scan_all_containers(auto_delete=True)

if __name__ == "__main__":
    main()

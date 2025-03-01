import argparse
import subprocess
import os
import sqlite3
import time
import sys
import tkinter
from tkinter import messagebox
import json

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

# Function to create SQLite database for storing file paths
def create_db():
    conn = sqlite3.connect('docker_defender.db')
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

# Function to store file paths in SQLite database, add new ones and remove deleted ones
def store_file_paths(container_id, file_paths):
    conn = sqlite3.connect('docker_defender.db')
    cursor = conn.cursor()

    # Fetch existing file paths for the container from the database
    cursor.execute('''
        SELECT file_path FROM files WHERE container_id = ?
    ''', (container_id,))
    existing_files = {row[0] for row in cursor.fetchall()}

    # Identify new files (that are in the current snapshot but not in the DB)
    new_files = [file_path for file_path in file_paths if file_path not in existing_files]
    
    # Identify deleted files (that are in the DB but not in the current snapshot)
    deleted_files = [file_path for file_path in existing_files if file_path not in file_paths]
    
    # Add new files to the database
    for file_path in new_files:
        cursor.execute('''
            INSERT INTO files (container_id, file_path) 
            VALUES (?, ?)
        ''', (container_id, file_path))

    # Remove deleted files from the database
    for file_path in deleted_files:
        cursor.execute('''
            DELETE FROM files WHERE container_id = ? AND file_path = ?
        ''', (container_id, file_path))

    conn.commit()
    conn.close()

# Function to get the overlay mounted paths for a container
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

# Function to list all files under a given directory recursively
def list_files_in_directory(directory):
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths

# Function to detect newly created files by comparing with the DB
def detect_new_files(container_id, current_file_paths):
    conn = sqlite3.connect('docker_defender.db')
    cursor = conn.cursor()
    
    # Get existing files for this container from the DB
    cursor.execute('''
        SELECT file_path FROM files WHERE container_id = ?
    ''', (container_id,))
    existing_files = {row[0] for row in cursor.fetchall()}
    
    # Compare current file paths with existing ones
    new_files = [file_path for file_path in current_file_paths if file_path not in existing_files]
    
    conn.close()
    return new_files

def remove_docker_paths_from_output(output, prefix):
    lst = output.split("\n")
    return "\n".join([line if not line.startswith(prefix) else line.replace(prefix, "") for line in lst ])


# Function to scan a specific Docker container
def scan_container(container_id, auto_delete=False):
    print(f"🔍 Scanning container: {container_id}...")
    folders = get_container_folders(container_id)
    merged = folders["MergedDir"]

    # Run clamscan inside the container on the merged directory
    scan_command = ["clamscan", "-ri", merged]
    if auto_delete:
        scan_command.append("--remove")  # Enable auto-delete if 'defend' mode is on

    result = remove_docker_paths_from_output(ubprocess.run(scan_command, capture_output=True, text=True).stdout, merged)
    print(result)
    if "FOUND" in result:
        print(f"⚠️ Malware detected in container {container_id}")
        return result
    else:
        print(f"✅ No threats found in container {container_id}.")
        return None

# Function to show a popup notification
def show_popup(message):
    root = tkinter.Tk()
    root.withdraw()
    messagebox.showwarning("DockerDefender Alert", message)
    root.destroy()

# Function to scan newly created files
def scan_new_files(container_id, auto_delete=False, popup=False):
    # Get the current files in the container
    folders = get_container_folders(container_id)
    merged = folders["MergedDir"]
    
    # List all files under MergedDir
    current_file_paths = list_files_in_directory(merged)
    
    # Detect new files by comparing with the DB
    new_files = detect_new_files(container_id, current_file_paths)
    
    print("New files found:", new_files)

    open("/tmp/file-list.txt", "w+").write("")

    with open("/tmp/file-list.txt", "r+") as f:
        for file in new_files:
            f.write(file + "\n")



    if new_files:
        print(f"🔍 New files detected in container {container_id}. Scanning...")
        
        # Run clamscan on each new file
        scan_command = ["clamscan", "-i", "--file-list=/tmp/file-list.txt"]
        if auto_delete:
            scan_command.append("--remove")
        result = remove_docker_paths_from_output(subprocess.run(scan_command, capture_output=True, text=True).stdout, merged)

        
        if "FOUND" in result:
            print(f"⚠️ Malware detected in container {container_id}")
            if popup:
                show_popup(f"Malware detected in {file} in container {container_id}!")
        
        print(result)


    else:
        print(f"✅ No new files detected in container {container_id}.")

    # Store the file paths in the database
    store_file_paths(container_id, current_file_paths)

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
    containers = get_running_containers()
    try:
        while True:
            for container_id in containers:
                scan_new_files(container_id, auto_delete, popup)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped.")

# Function to get all running Docker container IDs
def get_running_containers():
    result = subprocess.run(["docker", "ps", "--format", "{{.ID}}"], capture_output=True, text=True)
    return result.stdout.strip().split("\n") if result.stdout else []

# Main function to handle command-line arguments
def main():
    check_if_root()  # Ensure the script is run as root
    
    parser = argparse.ArgumentParser(description="DockerDefender - Docker Malware Scanner using ClamAV")
    
    parser.add_argument("command", choices=["scan", "monitor", "defend"], help="Choose a mode to run DockerDefender")
    parser.add_argument("--popup", action="store_true", help="Show a popup notification when malware is detected")
    parser.add_argument("--interval", type=int, default=60, help="Interval for monitoring mode (default: 60 seconds)")
    
    args = parser.parse_args()
    
    create_db()  # Create the database to store file paths
    
    check_clamscan()  # Ensure ClamAV is installed
    
    if args.command == "scan":
        scan_all_containers()
    
    elif args.command == "monitor":
        monitor_containers(args.interval, args.popup)

    elif args.command == "defend":
        scan_all_containers(auto_delete=True)

if __name__ == "__main__":
    main()

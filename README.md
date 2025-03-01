# DockerDefender 🚀🔍  
**A Malware Scanner for Active Docker Containers**  

## 📖 Overview  
DockerDefender is a security tool designed to scan actively running Docker containers for malware. It integrates with **ClamAV** to detect threats in containerized environments and supports:  
- **Full container scans**  
- **Real-time monitoring** of new files  
- **Automatic removal** of detected malware  
- **Database tracking** of container file changes  
- **Popup alerts** for malware detection  

## 🎯 Features  
✅ Scans all running containers for malware  
✅ Supports **ClamAV** (`clamscan` or `clamdscan`) for detection  
✅ Tracks newly created files inside containers  
✅ Periodic monitoring for continuous security  
✅ Optional **automatic deletion** of infected files  
✅ SQLite database for tracking scanned files  
✅ Popup alerts for immediate threat notifications  

---

## 🚀 Installation  

### 1️⃣ Install Dependencies  
Ensure Docker and ClamAV are installed on your system.  

#### 📌 Install Docker  
[Follow Docker Installation Guide](https://docs.docker.com/get-docker/)  

#### 📌 Install ClamAV  
On **Ubuntu/Debian**:  
```sh
sudo apt update && sudo apt install clamav clamav-daemon -y
```
On **CentOS/RHEL**:  
```sh
sudo yum install epel-release -y
sudo yum install clamav clamav-update -y
```
On **Mac (Homebrew)**:  
```sh
brew install clamav
```

### 2️⃣ Clone the Repository  
```sh
git clone https://github.com/yourrepo/docker-defender.git
cd docker-defender
```

### 3️⃣ Run DockerDefender  
```sh
sudo python3 docker_defender.py scan
```

---

## 🔥 Usage  

DockerDefender provides three main modes:  

### 🔎 **Scan Running Containers**
Scans all actively running containers for malware.  
```sh
sudo python3 docker_defender.py scan
```

### 🔄 **Monitor Containers for New Files**
Continuously monitors running containers for new files and scans them at a set interval.  
```sh
sudo python3 docker_defender.py monitor --interval 30
```
- `--interval <seconds>`: Time between scans (default: 60s)  
- `--popup`: Show a popup alert if malware is found  

### 🛡️ **Defend Containers (Auto-Delete Malware)**
Automatically removes detected malware from all running containers.  
```sh
sudo python3 docker_defender.py defend
```

---

## 🛠️ How It Works  

1. **Detects Running Containers**  
   Uses `docker ps` to list all active containers.  

2. **Extracts Container Filesystem Paths**  
   Retrieves `MergedDir` from `docker inspect`, which represents the container's overlay filesystem.  

3. **Scans Files for Malware**  
   Runs **ClamAV** (`clamdscan` or `clamscan`) on container files.  

4. **Tracks File Changes**  
   Uses an **SQLite database** to track existing files and detect newly created ones.  

5. **Alerts on Detection**  
   Shows warnings in the terminal and optionally **triggers a popup alert**.  

6. **Auto-Removes Infected Files** (if enabled)  

---

## 📝 Example Output  

### **Scanning Containers**
```sh
sudo python3 docker_defender.py scan
```
🔍 Scanning container: **3b2ac6a7d1f5**...  
✅ No threats found in container **3b2ac6a7d1f5**.  
🔍 Scanning container: **8f4c2b9e0c21**...  
⚠️ Malware detected in container **8f4c2b9e0c21**!  
```

### **Monitoring for New Files**
```sh
sudo python3 docker_defender.py monitor --interval 30
```
🔄 Monitoring containers for threats...  
📂 New files detected in container **3b2ac6a7d1f5**! Scanning...  
✅ No threats found.  
📂 New files detected in container **8f4c2b9e0c21**! Scanning...  
⚠️ Malware found in **/merged/path/malicious.sh**!  
```

### **Auto-Deleting Infected Files**
```sh
sudo python3 docker_defender.py defend
```
🛡️ Scanning container: **8f4c2b9e0c21**...  
🗑️ Infected file **/merged/path/malicious.sh** removed!  

---

## 👨‍💻 Developer Guide  

### 🏗️ Running in a Virtual Environment  
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 🛠️ Debug Mode  
Add `--verbose` to enable debug logging.  

---

## 🏆 Why Use DockerDefender?  

✔️ **Lightweight & Fast** – Uses **ClamAV** for efficient scanning  
✔️ **Works with Any Docker Container**  
✔️ **Automated Security** – Monitors for new threats  
✔️ **Simple to Use** – Just **one command** to secure containers  

---

## ⚠️ Disclaimer  
DockerDefender helps detect and remove malware, but **it is not a replacement for complete security measures**. Always follow best security practices for containerized applications.  

---

## 🤝 Contributing  
We welcome contributions! Feel free to open issues or pull requests on GitHub.  

---

## 📜 License  
MIT License © 2025  

---

🔗 **GitHub Repository**: [https://github.com/yourrepo/docker-defender](https://github.com/yourrepo/docker-defender) 🚀

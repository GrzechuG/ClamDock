# DockerDefender <img src="https://github.com/user-attachments/assets/61fcc5cc-cdd9-43de-95aa-1d51e989a48d" width="200">
**A Host-Based Malware Scanner for active Docker Containers** 



## 📖 Overview  
DockerDefender is a security tool that runs on the **host system**, scanning actively running Docker containers for malware **from outside the containerized environment**. It integrates with **ClamAV** to detect threats in containers without needing to run inside them. Key features include:  
- **Full container scans** from the host system  
- **Real-time scanning** of new files inside containers  
- **Automatic removal** of detected malware  
- **Popup alerts** for malware detection  

## 🎯 Features  
✅ Scans all running containers for malware **from the host system**  
✅ Runs **outside of containers** for enhanced security  
✅ Supports **ClamAV** (`clamscan` or `clamdscan`) for detection  
✅ Tracks newly created files inside containers  
✅ Periodic monitoring for continuous security  
✅ Optional **automatic deletion** of infected files  
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

4. **Tracks new Files**  
   Uses an **SQLite database** to track and detect newly created files.  

5. **Alerts on Detection**  
   Shows warnings in the terminal and optionally **triggers a popup alert**.  

6. **Auto-Removes Infected Files** (if enabled)  

---

## 📝 Example Output  

### Scanning Containers
```sh
sudo python3 docker_defender.py scan
```

![image](https://github.com/user-attachments/assets/5e717ea4-f2c2-427b-908e-3eb39e611feb)



### Monitoring for New Files

```sh
sudo python3 docker_defender.py monitor --interval 10
```
![image](https://github.com/user-attachments/assets/fb8b6e5f-a35c-4a03-b4e5-0c3daca05572)



### Auto-Deleting Infected Files

```sh
sudo python3 docker_defender.py defend
```
![image](https://github.com/user-attachments/assets/773bd036-207a-40b7-99d1-b3300f69866a)


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
[Custom License](https://github.com/GrzechuG/DockerDefender/tree/main?tab=License-1-ov-file)

---



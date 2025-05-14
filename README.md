# SFTP Log Dashboard

This project automates SFTP file‐exchange between three Vagrant VMs, collects logs on the host, and provides a lightweight Flask web dashboard (Dockerized) to visualize per‐host and per‐user transfer statistics with interactive charts.

---

## 🔧 Prerequisites

- **Host OS**: Windows / macOS / Linux  
- **Vagrant** (≥ 2.2)  
- **VirtualBox** (or other Vagrant provider)  
- **Docker** (Docker Desktop or Engine)
- **Python 3.8.10**   

---

## 🚀 1. Bring up SFTP VMs with Vagrant

1. Clone or unzip this repo:
   ```bash
   git clone https://…/your-repo.git
   cd your-repo

2. Inspect and customize your Vagrantfile if needed (SSH keys, network, etc.). Generate SSH keys
3. Start three VMs with SFTP configure:
   ```bash
   vagrant up
4. Verify you can vagrant ssh sftp1 and run the provisioning scripts. Logs will be written into the shared folder on your host, e.g.:
   ```bash
   project-root/logs/sftp1.log
   project-root/logs/sftp2.log
   project-root/logs/sftp3.log

## 🛠 2. Prepare your host logs directory
By default we mount:
   ```bash
   project-root/logs

into the Docker container at /app/logs. Make sure it exists and contains your .log files:
   ```bash
   ls logs/*.log

## 📦 3. Build the Dockerized Flask dashboard
Ensure you have requirements.txt, logcollect.py, templates/ and static/ in the project root.

Build the Alpine‐based Docker image:
   ```bash
   docker build -t logdashboard:latest .
Verify the image size:
   ```bash
   docker images logdashboard:latest

## ▶️ 4. Run the container
Mount your host logs, set the env-var, and expose port 5000:
   ```bash
   docker run -d \
     --name logdashboard \
     -p 5000:5000 \
     -e LOG_DIR=/app/logs \
     -v "$(pwd)/logs:/app/logs" \
     logdashboard:latest
   -v "$(pwd)/logs:/app/logs"
mounts your host folder containing .log files into the container.
   ```bash
   -e LOG_DIR=/app/logs"

tells the app where to read logs inside the container.

## 🌐 5. View the Dashboard
Open your browser at:
http://localhost:5000/
You will see:
Summary page
Filters for Hostname, IP, Date from/to
Interactive bar chart of “Files Sent” by host/IP
Table of totals
Per-User page
Click any hostname link to view its detailed page
Filters for IP, Date from/to
Interactive bar chart of that user’s transfers
Table of every put event with timestamp, filename, IP





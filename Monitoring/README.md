# Monitoring

**Monitoring** is a service that supervises the operation of a MySQL database and sends messages to a Telegram channel when:

- The database status changes.
- CPU or memory usage exceeds a reference threshold (70%).

If the database status changes to "stopped," the service attempts to restart it automatically and notifies the result.

## Features

- **Database Status Monitoring:** Detects changes in the status of a MySQL database and sends an alert.
- **Automatic Restart:** If the database stops, the service restarts it and notifies the Telegram channel.
- **System Resource Monitoring:** Sends an alert if CPU or memory usage exceeds 70%.

## Manual Service Installation  
Follow these steps on each host:

### 1. Install eBPF Tools

#### For Ubuntu-based systems:
```bash
apt update
apt install bpfcc-tools linux-headers-$(uname -r)
```

### 2: Install python tools
#### For Ubuntu-based systems
```bash
apt install python3-bpfcc
apt install python3-pip
pip3 install bcc
pip3 install psutil
pip3 install requests
```

### 3: Monitoring file
Place the monitoring.py template in the path /root/monitoring/monitoring.py on the hosts and update the values as needed.


### 4: Systemd Integration:
Convert the script into a systemd service to ensure it runs in the background.

1. Create the service file: 
```bash
nano /etc/systemd/system/monitoring.service
```

2.	Add the following content:
```shell
[Unit]
Description=MySQL Monitor
After=network.target

[Service]
ExecStart=/usr/bin/python3 /root/monitoring/monitoring.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5: Enable Monitoring Service
sudo systemctl enable monitoring

### 6: Start Monitoring Service
sudo systemctl start monitoring

---

## Installation via Pipeline

Use the ansible-echo playbook as an example, which is managed by the .github/workflow/echo.yml pipeline.

1.	Update the inventory step in the echo.yml file to include the new hosts along with their SSH keys or passwords.
2.	If necessary, add new secrets to the GitHub Actions secrets store.
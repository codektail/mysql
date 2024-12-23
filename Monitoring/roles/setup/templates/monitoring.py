import psutil
import requests
import socket
import threading
import time
import subprocess
from bcc import BPF

# Configuration
MYSQL_PROCESS_NAME = "mysqld"
TELEGRAM_BOT_TOKEN = "{{ telegram_bot_token }}"
TELEGRAM_CHANNEL_ID = "{{ telegram_channel_id }}"
CPU_THRESHOLD = {{ cpu_threshold }}  # CPU usage threshold in percentage
MEMORY_THRESHOLD = {{ memory_threshold }}  # Memory usage threshold in percentage
CHECK_INTERVAL = 10  # Check interval in seconds

# Get hostname
HOSTNAME = socket.gethostname()

# eBPF program
program = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

BPF_HASH(process_info, u32);

// Capture process exit
int trace_exit(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    char comm[16] = {};
    int ret = bpf_get_current_comm(&comm, sizeof(comm));
    if (ret != 0) {
        return 0;  // Exit if unable to get the process name
    }
    
    if (comm[0] == 'm' && comm[1] == 'y' && comm[2] == 's' && comm[3] == 'q' && comm[4] == 'l' && comm[5] == 'd') {
        bpf_trace_printk("MySQL process exited: PID=%d\\n", pid);
    }
    return 0;
}
"""

# Initialize BPF
b = BPF(text=program)
b.attach_kprobe(event="do_exit", fn_name="trace_exit")

# Function to send an alert to Telegram
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")

# Function to check MySQL service status
def is_mysql_service_active():
    try:
        status = subprocess.run(["systemctl", "is-active", "mysql"], capture_output=True, text=True, check=False)
        return status.stdout.strip() == "active"
    except Exception as e:
        print(f"Error checking MySQL service status: {e}")
        return False

# Function to restart MySQL service if inactive
def restart_mysql_service():
    if not is_mysql_service_active():
        try:
            subprocess.run(["sudo", "systemctl", "restart", "mysql"], check=True)
            send_telegram_alert(f"✅ MySQL service has been restarted on {HOSTNAME}.")
            print("MySQL service restarted successfully.")
        except subprocess.CalledProcessError as e:
            send_telegram_alert(f"❌ Failed to restart MySQL service on {HOSTNAME}. Error: {e}")
            print(f"Error restarting MySQL service: {e}")
    else:
        print("MySQL service is already active. No restart needed.")

# Function to monitor MySQL resource usage
def monitor_mysql_resources():
    for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
        try:
            if proc.info['name'] == MYSQL_PROCESS_NAME:
                cpu_usage = proc.cpu_percent(interval=1)
                memory_usage = proc.memory_percent()
                
                # Check thresholds
                if cpu_usage > CPU_THRESHOLD:
                    send_telegram_alert(
                        f"⚠️ ALERT: CPU\nHostname: {HOSTNAME}\nHigh CPU usage detected.\nProcess {MYSQL_PROCESS_NAME}: {cpu_usage:.2f}% \n(Threshold: {CPU_THRESHOLD}%)"
                    )
                if memory_usage > MEMORY_THRESHOLD:
                    send_telegram_alert(
                        f"⚠️ ALERT: MEMORY\nHostname: {HOSTNAME}\nHigh memory usage detected.\nProcess {MYSQL_PROCESS_NAME}: {memory_usage:.2f}% \n(Threshold: {MEMORY_THRESHOLD}%)"
                    )
        except psutil.NoSuchProcess:
            continue

# Monitor MySQL process exit
def monitor_mysql_exit():
    while True:
        try:
            line = b.trace_readline().decode()
            print(f"Debug: {line}")
            if "MySQL process exited" in line:
                if not is_mysql_service_active():
                   send_telegram_alert(f"💔 ALERT: MySQL state change to down\nHostname: {HOSTNAME}\nMySQL has changed its state.")
                   restart_mysql_service()  # Restart MySQL service if inactive
                else:
                   send_telegram_alert(f"⚠️ ALERT: MySQL state change to active\nHostname: {HOSTNAME}\nMySQL has changed its state.")
        except KeyboardInterrupt:
            print("Monitoring stopped.")
            exit()
        except Exception as e:
            print(f"Error in monitor_mysql_exit: {e}")

# Main loop
if __name__ == "__main__":
    exit_thread = threading.Thread(target=monitor_mysql_exit, daemon=True)
    exit_thread.start()
    while True:
        monitor_mysql_resources()
        time.sleep(CHECK_INTERVAL)
from bcc import BPF
import psutil
import requests
import socket
import time

# Configuración
MYSQL_PROCESS_NAME = "mysqld"
TELEGRAM_BOT_TOKEN = "7553348867:AAGpcoUQvNs0Fh1B0nODUW-3pH3ZhSK4CrU"  
TELEGRAM_CHANNEL_ID = "-2355753280"   
CPU_THRESHOLD = 80  # Umbral de uso de CPU en porcentaje
MEMORY_THRESHOLD = 80  # Umbral de uso de memoria en porcentaje
CHECK_INTERVAL = 10  # Intervalo de verificación en segundos

# Obtener hostname
HOSTNAME = socket.gethostname()

# Programa eBPF
program = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

BPF_HASH(process_info, u32, char[16]);

int trace_exit(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    char comm[16];
    
    // Get the current process name
    bpf_get_current_comm(&comm, sizeof(comm));
    
    // Check if the process name matches "mysqld"
    if (__builtin_memcmp(comm, "mysqld", 6) == 0) {
        bpf_trace_printk("MySQL process exited: PID=%d\n", pid);
        process_info.update(&pid, &comm);
    }
    return 0;
}
"""

# Inicializar BPF
b = BPF(text=program)
b.attach_kprobe(event="do_exit", fn_name="trace_exit")

# Función para enviar una alerta a Telegram
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message
    }
    try:
        requests.post(url, json=payload)
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje a Telegram: {e}")

# Función para monitorear el uso de recursos de MySQL
def monitor_mysql_resources():
    for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
        if proc.info['name'] == MYSQL_PROCESS_NAME:
            cpu_usage = proc.info['cpu_percent']
            memory_usage = proc.info['memory_percent']
            
            # Verificar umbrales
            if cpu_usage > CPU_THRESHOLD:
                send_telegram_alert(
                    f"⚠️ \nHostname: {HOSTNAME}\nUso alto de CPU detectado. \nProcess {MYSQL_PROCESS_NAME}: {cpu_usage:.2f}% \n(Umbral: {CPU_THRESHOLD}%)"
                )
            if memory_usage > MEMORY_THRESHOLD:
                send_telegram_alert(
                    f"⚠️ \nHostname: {HOSTNAME}\nUso alto de memoria detectado. \nProcess {MYSQL_PROCESS_NAME}: {memory_usage:.2f}% \n(Umbral: {MEMORY_THRESHOLD}%)"
                )

# Monitorear la salida de procesos MySQL
def monitor_mysql_exit():
    while True:
        try:
            b.trace_print(fmt="{5}")  # Imprime mensajes de salida del programa eBPF
            line = line.decode()
            if "MySQL process started" in line:
                send_telegram_alert(f"MySQL inició en {HOSTNAME}")
            elif "MySQL process killed" in line:
                signal = line.split("Signal=")[-1].strip()
                send_telegram_alert(f"MySQL recibió una señal de terminación en {HOSTNAME}: Señal {signal}")
            elif "MySQL process exited" in line:
                send_telegram_alert(f"MySQL finalizó en {HOSTNAME}")

        except KeyboardInterrupt:
            print("Monitoreo terminado.")
            exit()

# Bucle principal de monitoreo
def main():
    print("Iniciando monitoreo...")
    while True:
        monitor_mysql_resources()  # Verifica el uso de CPU y memoria
        time.sleep(CHECK_INTERVAL)

# Ejecutar monitoreo en paralelo
import threading
if __name__ == "__main__":
    exit_thread = threading.Thread(target=monitor_mysql_exit, daemon=True)
    exit_thread.start()
    main()
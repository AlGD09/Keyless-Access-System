#!/usr/bin/env python3
# main.py – Testprogramm für RCU-Funktionalität

import os
import time
from datetime import datetime

def main():
    print("=== RCU Testprogramm gestartet ===")

    # 1. Systeminformationen anzeigen
    print(f"Benutzer: {os.getlogin()}")
    print(f"Aktuelles Verzeichnis: {os.getcwd()}")
    print(f"Python-Version: {os.sys.version}")

    # 2. Eine Logdatei erstellen oder erweitern
    log_path = "/root/keyless-system/logs/rcu_test.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "a") as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{now}] Testlauf erfolgreich gestartet.\n")

    # 3. Eine kleine Schleife als Laufzeit-Test
    for i in range(5):
        print(f"Lauf {i+1}/5: System arbeitet...")
        time.sleep(1)

    print("=== Testprogramm erfolgreich abgeschlossen ===")

if __name__ == "__main__":
    main()

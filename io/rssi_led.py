#!/usr/bin/env python3
# rssi_led.py – Interaktiver DIO6-Test über Test_owa4x (für neuere Versionen)

import pexpect
import time

def dio6_set(value: int):
    """Setzt den Digital Output 6 auf 0 oder 1."""
    try:
        child = pexpect.spawn("Test_owa4x", encoding="utf-8", timeout=5)
        child.expect(">>")
        cmd = f"IOSet DIGOUT 6 {value}"
        child.sendline(cmd)
        child.expect(">>")
        child.sendline("EXIT")
        child.close(force=True)
        print(f"Befehl ausgeführt: {cmd}")
    except Exception as e:
        print(f"Fehler bei DIO6_set({value}): {e}")

print("Starte DIO6-Test...")
for i in range(3):
    print(f"Schalte DIO6 EIN (Versuch {i+1})")
    dio6_set(0)  # Aktiv (LOW)
    time.sleep(2)
    print(f"Schalte DIO6 AUS (Versuch {i+1})")
    dio6_set(1)  # Inaktiv (HIGH)
    time.sleep(2)

print("✅ Test abgeschlossen.")

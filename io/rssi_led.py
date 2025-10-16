#!/usr/bin/env python3
# test_dio6.py – Funktionstest für DIO6 (angepasst an ARIES Test Program)

import os
import time

def dio6_on():
    # Setze Port 6 auf 0 (aktiv)
    os.system('echo -e "IOwrite_port 6 0 0xFF\nEXIT\n" | Test_owa4x')

def dio6_off():
    # Setze Port 6 auf 1 (inaktiv)
    os.system('echo -e "IOwrite_port 6 1 0xFF\nEXIT\n" | Test_owa4x')

print("Starte DIO6-Test...")
for i in range(3):
    print(f"Schalte DIO6 EIN (Versuch {i+1})")
    dio6_on()
    time.sleep(2)

    print(f"Schalte DIO6 AUS (Versuch {i+1})")
    dio6_off()
    time.sleep(2)

print("✅ Test abgeschlossen.")

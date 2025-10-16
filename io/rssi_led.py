#!/usr/bin/env python3
# test_dio6.py – Schneller Funktionstest für DIO6 über Test_owa4x

import os
import time

def dio6_on():
    os.system('echo -e "IOSet DIGOUT 6 0\nEXIT\n" | Test_owa4x')

def dio6_off():
    os.system('echo -e "IOSet DIGOUT 6 1\nEXIT\n" | Test_owa4x')

print("Starte DIO6-Test...")
for i in range(3):
    print(f"Schalte DIO6 EIN (Versuch {i+1})")
    dio6_on()
    time.sleep(2)

    print(f"Schalte DIO6 AUS (Versuch {i+1})")
    dio6_off()
    time.sleep(2)

print("✅ Test abgeschlossen.")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
io/output_control.py – Steuerung der DIO6-LED (rot/grün) über Test_owa4x
"""

import pexpect

def dio6_set(value: int):
    """Setzt den Digital Output 6 auf 0 (aktiv/grün) oder 1 (inaktiv/rot)."""
    try:
        child = pexpect.spawn("Test_owa4x", encoding="utf-8", timeout=5)
        child.expect(">>")
        cmd = f"IOSet DIGOUT 6 {value}"
        child.sendline(cmd)
        child.expect(">>")
        child.sendline("EXIT")
        child.close(force=True)
        print(f"DIO6 gesetzt auf {value}")
    except Exception as e:
        print(f"Fehler bei DIO6_set({value}): {e}")

#!/usr/bin/env python3
import os
import sys

# Enable ANSI escape sequences on Windows (Windows 10+)
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE = -11
    mode = ctypes.c_uint()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    kernel32.SetConsoleMode(handle, mode)

PREFIX = "\033["
SUFFIX = "\033[0m"

def green(text: str) -> str:
    return colorText(text, "32m")

def red(text: str) -> str:
    return colorText(text, "31m")

def yellow(text: str) -> str:
    return colorText(text, "33m")

def cyan(text: str) -> str:
    return colorText(text, "36m")

def colorText(text: str, colorCode: str) -> str:
    return PREFIX+colorCode+text+SUFFIX
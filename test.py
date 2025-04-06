#!/usr/bin/env python3
import os
import sys

# Dynamically set LOCAL_MODS_PATH based on script location
if getattr(sys, 'frozen', False):
    # If running from a PyInstaller executable, use the location of the .exe
    base_path = os.path.dirname(sys.executable)
else:
    # If running as a script, use the location of the script
    base_path = os.path.dirname(os.path.realpath(__file__))

LOCAL_MODS_PATH = os.path.join(base_path, "mods")  # Construct path to "mods" folder

def locate_file_path():
    print(LOCAL_MODS_PATH)

if __name__ == "__main__":
    locate_file_path()
import os

# Dynamically set LOCAL_MODS_PATH based on script location
script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory where the script is located
LOCAL_MODS_PATH = os.path.join(script_dir, "mods")  # Construct path to "mods" folder

def locate_file_path():
    print(LOCAL_MODS_PATH)

if __name__ == "__main__":
    locate_file_path()
#!/usr/bin/env python3
import os
import sys
import mod_updater_core as core
import colored_prints as colored
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated*")

# Dynamically set LOCAL_MODS_PATH based on script location
if getattr(sys, 'frozen', False):
    # If running from a PyInstaller executable, use the location of the .exe
    base_path = os.path.dirname(sys.executable)
else:
    # If running as a script, use the location of the script
    base_path = os.path.dirname(os.path.realpath(__file__))
    
LOCAL_MODS_PATH = os.path.join(base_path, "mods")
FORCE_UPDATE_LOG_PATH = os.path.join(base_path, "cloud_forced_update_log.json")

DEFAULT_CONFIG = {
    "url": "",
    "updateAll": False,
    "optionalMods": True,
    "useVersionChecking": True,
}
CONFIG_FILE_PATH = os.path.join(base_path, "modupdaterconfig.json")

def update_mods():
    """Update mods while keeping client-side mods intact."""
    config = core.load_config(CONFIG_FILE_PATH, DEFAULT_CONFIG)
    print(f"Current config: {config}")

    if os.path.exists(LOCAL_MODS_PATH):
        print(f"Using mods folder: {LOCAL_MODS_PATH}")
    else:
        print(f"Mods folder not found at: {LOCAL_MODS_PATH}.")
        user_input = input("Do you want to create the mods folder? (y/n): ").strip().lower()
        if user_input == 'y':
            try:
                # Create the mods folder
                os.makedirs(LOCAL_MODS_PATH)
                print(colored.cyan(f"Mods folder created at: {LOCAL_MODS_PATH}"))
            except Exception as e:
                print(colored.red(f"Failed to create mods folder: {e}"))
        else:
            print(colored.red("Mods folder not created. The program will cancel its execution."))
            core.safe_exit()

    installed_mods = core.get_installed_mods(LOCAL_MODS_PATH)

    force_update_log = {}

    cloud_common_mods = core.get_cloud_modlist("common")
    cloud_mods = cloud_common_mods

    cloud_client_mods = core.get_cloud_modlist("client")
    cloud_mods.update(cloud_client_mods)

    if config.get("optionalMods", True):
        optional_mods = core.get_cloud_modlist("clientadditional")
        cloud_mods.update(optional_mods)

    if not installed_mods:
        print("No mods installed | Starting the downloading process")
        print("Downloading mods.zip (common)")
        core.download_and_extract_zips("mods.zip", "common", LOCAL_MODS_PATH)
        print("Downloading mods.zip (client)")
        core.download_and_extract_zips("mods.zip", "client", LOCAL_MODS_PATH)
        if config.get("optionalMods", True) :
            print("Downloading mods.zip (clientadditional)")
            core.download_and_extract_zips("mods.zip", "clientadditional", LOCAL_MODS_PATH)
        core.writeForceUpdateLog(FORCE_UPDATE_LOG_PATH, force_update_log)
        print(colored.green("Mod downloading complete!"))
        core.safe_exit()
    
    for mod_id, mod_data in cloud_mods.items():
        cloud_filename = mod_data['filename']
        cloud_version = mod_data['version']
        environment = mod_data['environment']

        if mod_id in installed_mods:
            local_filenames = installed_mods[mod_id][0]  # List of installed filenames for this mod ID
            local_versions = installed_mods[mod_id][1]  # List of installed versions of this mod ID
            
            if config.get("useVersionChecking", True) and not config.get("updateAll", False):
                outdated_files = [
                    local_filenames[i] for i, version in enumerate(local_versions) if version != cloud_version
                ]
                versionmatching_files = [
                    local_filenames[i] for i, version in enumerate(local_versions) if version == cloud_version
                ]
                
                kept_file_index = 0
                duplicated_files = []
                if len(versionmatching_files) > 1:
                    # Prefer keeping the one with the cloud filename, otherwise keep the newest
                    versionmatching_files.sort(key=lambda f: (f != cloud_filename, -os.path.getmtime(os.path.join(LOCAL_MODS_PATH, f))))
                    kept_file_index = local_filenames.index(versionmatching_files[0])
                    files_to_remove = versionmatching_files[1:]  # Keep only the first one
                    duplicated_files.extend(files_to_remove)

                for duplicated_file in duplicated_files:
                    core.removeWithCheck(os.path.join(LOCAL_MODS_PATH, duplicated_file), f"Removed mod file duplicate: {duplicated_file}", f"File {duplicated_file} not found, skipping deletion.")

                for outdated_file in outdated_files:
                    core.removeWithCheck(os.path.join(LOCAL_MODS_PATH, outdated_file), f"Removed outdated mod file: {outdated_file}", f"File {outdated_file} not found, skipping deletion.")

                local_version = local_versions[kept_file_index]
                if local_version == cloud_version and not config.get("updateAll", False):
                    newRandomSeqeunce = core.updateWhenForceUpdate(mod_id, FORCE_UPDATE_LOG_PATH)
                    if newRandomSeqeunce == "":
                        print(f"{mod_id} ({local_filenames[kept_file_index]}) is already up-to-date.")
                        continue
                    elif newRandomSeqeunce == core.get_recent_force_update(mod_id, FORCE_UPDATE_LOG_PATH):
                        force_update_log[mod_id] = newRandomSeqeunce
                        print(f"{mod_id} ({local_filenames[kept_file_index]}) is already up-to-date.")
                        continue
                    else:
                        print(f"Updating {mod_id} caused by cloud force update")
                        core.removeWithCheck(os.path.join(LOCAL_MODS_PATH, local_filenames[kept_file_index]), "", "")
                        print(colored.cyan(f"Downloading updated version of {mod_id}: {cloud_filename}"))
                        core.download_mod(cloud_filename, environment, LOCAL_MODS_PATH)
                        force_update_log[mod_id] = newRandomSeqeunce
                else:
                    core.removeWithCheck(os.path.join(LOCAL_MODS_PATH, local_filenames[kept_file_index]), f"Removed outdated mod file: {local_filenames[kept_file_index]}", "")
                    # Download the correct version (if not already present)
                    print(colored.cyan(f"Downloading updated version of {mod_id}: {cloud_filename}"))
                    core.download_mod(cloud_filename, environment, LOCAL_MODS_PATH)
            else:    
                # If not using version checking, check filename mismatch
                outdated_files = [f for f in local_filenames if f != cloud_filename]
                for outdated_file in outdated_files:
                    core.removeWithCheck(os.path.join(LOCAL_MODS_PATH, outdated_file), f"Removed outdated mod file: {outdated_file}", f"File {outdated_file} not found, skipping deletion.")
            
                # If the correct file is already there, don't re-download
                if cloud_filename in local_filenames and not config.get("updateAll", False):
                    newRandomSeqeunce = core.updateWhenForceUpdate(mod_id, FORCE_UPDATE_LOG_PATH)
                    if newRandomSeqeunce == "":
                        print(f"{mod_id} ({local_filenames[kept_file_index]}) is already up-to-date.")
                        continue
                    elif newRandomSeqeunce == core.get_recent_force_update(mod_id, FORCE_UPDATE_LOG_PATH):
                        force_update_log[mod_id] = newRandomSeqeunce
                        print(f"{mod_id} ({local_filenames[kept_file_index]}) is already up-to-date.")
                        continue
                    else:
                        print(f"Updating {mod_id} caused by cloud force update")
                        core.removeWithCheck(os.path.join(LOCAL_MODS_PATH, local_filenames[kept_file_index]), "", "")
                        print(colored.cyan(f"Downloading updated version of {mod_id}: {cloud_filename}"))
                        core.download_mod(cloud_filename, environment, LOCAL_MODS_PATH)
                        force_update_log[mod_id] = newRandomSeqeunce
                
                # Download the correct version (if not already present)
                print(colored.cyan(f"Downloading updated version of {mod_id}: {cloud_filename}"))
                core.download_mod(cloud_filename, environment, LOCAL_MODS_PATH)
        else:
            # If mod is not installed at all, download it
            print(colored.cyan(f"New mod found: {mod_id} | Downloading {cloud_filename}."))
            core.download_mod(cloud_filename, environment, LOCAL_MODS_PATH)

    core.writeForceUpdateLog(FORCE_UPDATE_LOG_PATH, force_update_log)

    print(colored.green("Mod update complete!"))
    core.safe_exit()

if __name__ == "__main__":
    update_mods()
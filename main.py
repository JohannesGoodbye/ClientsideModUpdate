import os
import shutil
import zipfile
import toml
import requests
import json

LOCAL_MODS_PATH = "C:/Users/Johannes/Desktop/Minecraft/ScriptTesting/InstanceModsFolder"  # Update this

NETLIFY_BASE_URL = "https://6981e65b-f3f9-48cd-ac5f-573f755b02bd.netlify.app"

NETLIFY_COMMON_MODS_URL = NETLIFY_BASE_URL + "/modfiles/common"
COMMON_MODLIST_URL = NETLIFY_COMMON_MODS_URL + "/modlist.txt"

NETLIFY_CLIENT_MODS_URL = NETLIFY_BASE_URL + "/modfiles/client"
CLIENT_MODLIST_URL = NETLIFY_CLIENT_MODS_URL + "/modlist.txt"

NETLIFY_OPTIONAL_MODS_URL = NETLIFY_BASE_URL + "/modfiles/clientadditional"
OPTIONAL_MODLIST_URL = NETLIFY_OPTIONAL_MODS_URL + "/modlist.txt"

DEFAULT_CONFIG = {
    "forceUpdate": False,
    "optionalMods": True,
    "useVersionChecking": True,
}
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "modupdaterconfig.json")

def load_config():
    """Load configuration from a JSON file, or use default values if not found."""
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r") as config_file:
                config = json.load(config_file)
                print("Config loaded successfully.")
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config file: {e}. Using default config.")
    else:
        print("Config file not found. Using default config.")
    
    return DEFAULT_CONFIG

def get_mod_id_from_toml(mod_path):
    """Extract the primary mod ID from the mods.toml file inside a JAR."""
    try:
        with zipfile.ZipFile(mod_path, 'r') as jar:
            # Look for META-INF/mods.toml in the JAR
            mods_toml_path = "META-INF/mods.toml"
            if mods_toml_path in jar.namelist():
                with jar.open(mods_toml_path) as toml_file:
                    # Read the content of the mods.toml file as a string
                    toml_content = toml_file.read().decode('utf-8')

                    # Now load the TOML content
                    mod_info = toml.loads(toml_content)

                    # Extract only the first [[mods]] modId (ignore dependencies)
                    mods_section = mod_info.get("mods", [])
                    if mods_section and isinstance(mods_section, list):
                        mod_id = mods_section[0].get("modId")
                        if mod_id:
                            return mod_id

    except Exception as e:
        print(f"Failed to extract mod ID from {mod_path}: {e}")

    return None


def get_mod_id_from_loader_properties(mod_path):
    """Extract mod ID from loader.properties in the jar structure."""
    try:
        with zipfile.ZipFile(mod_path, 'r') as jar:
            # Look for any file ending with loader.properties
            for file_name in jar.namelist():
                if file_name.lower().endswith('loader.properties'):
                    with jar.open(file_name) as properties_file:
                        # Read the properties file content
                        properties_content = properties_file.read().decode('utf-8')

                        # Search for pinnedFile (the actual mod file)
                        for line in properties_content.splitlines():
                            if line.startswith('pinnedFile='):
                                pinned_file = line.split('=')[1].strip()  # Remove any leading/trailing whitespace
                                print(f"Found pinnedFile: {pinned_file} in {mod_path}")

                                # If pinnedFile starts with '/', remove the leading slash
                                if pinned_file.startswith('/'):
                                    pinned_file = pinned_file[1:]

                                # Now we need to look inside the current jar file (mod_path) for pinned_file
                                # Since it's a jar inside another jar, we open the nested jar
                                with zipfile.ZipFile(mod_path, 'r') as parent_jar:
                                    if pinned_file in parent_jar.namelist():
                                        print(f"Looking for mod ID in pinned jar: {pinned_file}")
                                        mod_id = get_mod_id_from_toml(parent_jar.open(pinned_file))
                                        if mod_id:
                                            print(f"Found mod ID ({mod_id}) in pinned jar: {pinned_file}")
                                            return mod_id
                                        else:
                                            print(f"Couldn't find mod ID in pinned jar: {pinned_file}")
                                            return "unknown"
                                    else:
                                        print(f"Pinned file {pinned_file} not found in {mod_path}.")
    except Exception as e:
        print(f"Failed to extract mod ID from {mod_path}: {e}")

    return None

def get_mod_version_from_toml(mod_path):
    """Extract the primary mod version from the mods.toml file inside a JAR."""
    try:
        with zipfile.ZipFile(mod_path, 'r') as jar:
            # Look for META-INF/mods.toml in the JAR
            mods_toml_path = "META-INF/mods.toml"
            if mods_toml_path in jar.namelist():
                with jar.open(mods_toml_path) as toml_file:
                    # Read the content of the mods.toml file as a string
                    toml_content = toml_file.read().decode('utf-8')

                    # Now load the TOML content
                    mod_info = toml.loads(toml_content)

                    # Extract only the first [[mods]] modId (ignore dependencies)
                    mods_section = mod_info.get("mods", [])
                    if mods_section and isinstance(mods_section, list):
                        mod_version = mods_section[0].get("version")
                        if mod_version:
                            return mod_version

    except Exception as e:
        print(f"Failed to extract mod version from {mod_path}: {e}")

    return None


def get_mod_version_from_loader_properties(mod_path):
    """Extract mod version from loader.properties in the jar structure."""
    try:
        with zipfile.ZipFile(mod_path, 'r') as jar:
            # Look for any file ending with loader.properties
            for file_name in jar.namelist():
                if file_name.lower().endswith('loader.properties'):
                    with jar.open(file_name) as properties_file:
                        # Read the properties file content
                        properties_content = properties_file.read().decode('utf-8')

                        # Search for pinnedFile (the actual mod file)
                        for line in properties_content.splitlines():
                            if line.startswith('pinnedFile='):
                                pinned_file = line.split('=')[1].strip()  # Remove any leading/trailing whitespace
                                print(f"Found pinnedFile: {pinned_file} in {mod_path}")

                                # If pinnedFile starts with '/', remove the leading slash
                                if pinned_file.startswith('/'):
                                    pinned_file = pinned_file[1:]

                                # Now we need to look inside the current jar file (mod_path) for pinned_file
                                # Since it's a jar inside another jar, we open the nested jar
                                with zipfile.ZipFile(mod_path, 'r') as parent_jar:
                                    if pinned_file in parent_jar.namelist():
                                        print(f"Looking for mod version in pinned jar: {pinned_file}")
                                        mod_id = get_mod_version_from_toml(parent_jar.open(pinned_file))
                                        if mod_id:
                                            print(f"Found mod version ({mod_id}) in pinned jar: {pinned_file}")
                                            return mod_id
                                        else:
                                            print(f"Couldn't find mod version in pinned jar: {pinned_file}")
                                    else:
                                        print(f"Pinned file {pinned_file} not found in {mod_path}.")
    except Exception as e:
        print(f"Failed to extract mod version from {mod_path}: {e}")

    return None

def get_installed_mods(mods_path):
    """Retrieve a dictionary of installed mod IDs mapped to a list of their filenames."""
    installed_mods = {}
    for filename in os.listdir(mods_path):
        if filename.endswith(".jar"):
            mod_path = os.path.join(mods_path, filename)
            mod_id = get_mod_id_from_toml(mod_path)
            mod_version = get_mod_version_from_toml(mod_path)

            if not mod_id:
                print(f"Mod ID not found in {filename}, checking loader.properties...")
                mod_id = get_mod_id_from_loader_properties(mod_path)
            
            if not mod_version:
                print(f"Mod version not found in {filename}, checking loader.properties...")
                mod_version = get_mod_version_from_loader_properties(mod_path)

            if mod_id:
                if mod_id not in installed_mods:
                    installed_mods[mod_id] = [[], []]  # Store a list of filenames
                installed_mods[mod_id][0].append(filename)  # Add filename to the list
                installed_mods[mod_id][1].append(mod_version)  # Add filename to the list

    return installed_mods

def get_cloud_modlist(environment):
    """Fetch the modlist.txt from Netlify and return a dictionary with mod IDs, filenames, and a flag for the environment."""
    if environment == "common":
        mod_url = COMMON_MODLIST_URL
    elif environment == "client":
        mod_url = CLIENT_MODLIST_URL
    elif environment == "clientadditional":
        mod_url = OPTIONAL_MODLIST_URL
    
    response = requests.get(mod_url)

    if response.status_code == 200:
        print(f"Fetching {environment} modlist.txt from {mod_url}")
        modlist_lines = response.text.splitlines()
        modlist_dict = {}

        for line in modlist_lines:
            parts = line.split(maxsplit=2)
            if len(parts) == 3:
                mod_id, mod_version, filename = parts
                modlist_dict[mod_id] = {'filename': filename, 'version': f"{mod_version}", 'environment': f"{environment}"}

        return modlist_dict
    else:
        print(f"Failed to fetch {environment} modlist.txt from {mod_url}")
        return {}
    
def download_and_extract_zip(zip_filename, environment):
    """Download a mod zip file and extract its contents."""
    if environment == "common":
        mod_url = f"{NETLIFY_COMMON_MODS_URL}/{zip_filename}"
    elif environment == "client":
        mod_url = f"{NETLIFY_CLIENT_MODS_URL}/{zip_filename}"
    elif environment == "clientadditional":
        mod_url = f"{NETLIFY_OPTIONAL_MODS_URL}/{zip_filename}"

    response = requests.get(mod_url, stream=True)
    
    if response.status_code == 200:
        zip_path = os.path.join(LOCAL_MODS_PATH, zip_filename)
        with open(zip_path, 'wb') as zip_file:
            zip_file.write(response.content)

        # Now extract the contents of the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(LOCAL_MODS_PATH)
        print(f"Extracted mods from {zip_filename} ({environment}) into {LOCAL_MODS_PATH}")
        os.remove(zip_path)  # Remove the zip file after extraction
    else:
        print(f"Failed to download {zip_filename} ({environment}) from {mod_url}")

def download_mod(mod_filename, environment):
    """Download a mod file from the Netlify server."""
    if environment == "common":
        mod_url = f"{NETLIFY_COMMON_MODS_URL}/{mod_filename}"
    elif environment == "client":
        mod_url = f"{NETLIFY_CLIENT_MODS_URL}/{mod_filename}"
    elif environment == "clientadditional":
        mod_url = f"{NETLIFY_OPTIONAL_MODS_URL}/{mod_filename}"

    response = requests.get(mod_url, stream=True)
    
    if response.status_code == 200:
        mod_path = os.path.join(LOCAL_MODS_PATH, mod_filename)
        with open(mod_path, 'wb') as mod_file:
            mod_file.write(response.content)
            # shutil.copyfileobj(response.content, mod_file)
        # print(f"Downloaded new mod: {response.url}")
    else:
        print(f"Failed to download {mod_filename} from {mod_url}")

def update_mods():
    """Update mods while keeping client-side mods intact."""
    config = load_config()
    print(f"Current config: {config}")
    installed_mods = get_installed_mods(LOCAL_MODS_PATH)

    cloud_common_mods = get_cloud_modlist("common")
    cloud_mods = cloud_common_mods

    cloud_client_mods = get_cloud_modlist("client")
    cloud_mods.update(cloud_client_mods)

    if config.get("optionalMods", True):
        optional_mods = get_cloud_modlist("clientadditional")
        cloud_mods.update(optional_mods)

    if not installed_mods:
        print("No mods installed | Starting the downloading process")
        print("Downloading mods.zip (common)")
        download_and_extract_zip("mods.zip", "common")
        print("Downloading mods.zip (client)")
        download_and_extract_zip("mods.zip", "client")
        if config.get("optionalMods", True) :
            print("Downloading mods.zip (clientadditional)")
            download_and_extract_zip("mods.zip", "clientadditional")
        print("Mod downloading complete!")
        return
    
    for mod_id, mod_data in cloud_mods.items():
        cloud_filename = mod_data['filename']
        cloud_version = mod_data['version']
        environment = mod_data['environment']

        if mod_id in installed_mods:
            local_filenames = installed_mods[mod_id][0]  # List of installed filenames for this mod ID
            local_versions = installed_mods[mod_id][1]  # List of installed versions of this mod ID
            
            if config.get("useVersionChecking", True) and not config.get("forceUpdate", False):
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
                    try:
                        os.remove(os.path.join(LOCAL_MODS_PATH, duplicated_file))
                        local_filenames.remove(duplicated_file)
                        print(f"Removed mod file duplicate: {duplicated_file}")
                    except FileNotFoundError:
                        print(f"File {duplicated_file} not found, skipping deletion.")

                for outdated_file in outdated_files:
                    try:
                        os.remove(os.path.join(LOCAL_MODS_PATH, outdated_file))
                        local_filenames.remove(outdated_file)
                        print(f"Removed outdated mod file: {outdated_file}")
                    except FileNotFoundError:
                        print(f"File {outdated_file} not found, skipping deletion.")

                local_version = local_versions[kept_file_index]
                if local_version == cloud_version and not config.get("forceUpdate", False):
                    print(f"{mod_id} ({local_filenames[kept_file_index]}) is already up-to-date. 23")
                    continue
                else:
                    os.remove(os.path.join(LOCAL_MODS_PATH, local_filenames[kept_file_index]))
                    print(f"Removed outdated mod file: {local_filenames[kept_file_index]}")
                    # Download the correct version (if not already present)
                    print(f"Downloading updated version of {mod_id}: {cloud_filename} 23")
                    download_mod(cloud_filename, environment)
            else:    
                # If not using version checking, check filename mismatch
                outdated_files = [f for f in local_filenames if f != cloud_filename]
                for outdated_file in outdated_files:
                    try:
                        os.remove(os.path.join(LOCAL_MODS_PATH, outdated_file))
                        local_filenames.remove(outdated_file)
                        print(f"Removed outdated mod file: {outdated_file}")
                    except FileNotFoundError:
                        print(f"File {outdated_file} not found, skipping deletion.")
            
                # If the correct file is already there, don't re-download
                if cloud_filename in local_filenames and not config.get("forceUpdate", False):
                    print(f"{mod_id} ({cloud_filename}) is already up-to-date.")
                    continue
                
                # Download the correct version (if not already present)
                print(f"Downloading updated version of {mod_id}: {cloud_filename}")
                download_mod(cloud_filename, environment)
        else:
            # If mod is not installed at all, download it
            print(f"New mod found: {mod_id} | Downloading {cloud_filename}.")
            download_mod(cloud_filename, environment)

    print("Mod update complete!")

if __name__ == "__main__":
    update_mods()
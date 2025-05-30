#!/usr/bin/env python3
import os
import sys
import zipfile
import toml
import requests
import json
import colored_prints as colored

url_config = {}
urls_initialized = False

cached_cloud_force_update_list = None
cached_force_update_log = None

def load_config(config_file_path, default_config):
    """Load configuration from a JSON file, or use default values if not found."""
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, "r") as config_file:
                config = json.load(config_file)
                print("Config loaded successfully.")
                if config.get("url") == "":
                    print(colored.red("Value \"url\" is empty. The program will cancel it's execution."))
                    safe_exit()
                initialize_urls((config["url"]))
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(colored.red(f"Error loading config file: {e}. Using default config."))
            if default_config.get("url") == "":
                print(colored.red("Value \"url\" is empty. The program will cancel it's execution."))
                safe_exit()
    else:
        print("Config file not found.")

        create_file_input = input("Do you want to create a new config file? (y/n): ").strip().lower()
        if create_file_input == 'y':
            # Create the config file with default values
            try:
                with open(config_file_path, "w") as config_file:
                    json.dump(default_config, config_file, indent=4)
                    print(colored.cyan(f"Config file created at: {config_file_path}"))
                    print(f"current config: {default_config}")
                    exit_programm_input = input("Exit the program so you can modify the config file? (y/n): ")
                    if exit_programm_input == 'y':
                        sys.exit(0) # Exit the program so the user can modify the config file
                    else:
                        print(f"Config file not modified. Continuing with default values: {default_config}")
                        if default_config.get("url") == "":
                            print(colored.red("Value \"url\" is empty. The program will cancel it's execution."))
                            safe_exit()
            except Exception as e:
                print(colored.red(f"Failed to create config file: {e}"))
                safe_exit()
        else:
            print(colored.red("Config file not created. The program will cancel it's execution."))
            safe_exit()
    
    #seems to be useless (next 2 lines)
    initialize_urls((config["url"]))
    return default_config

def initialize_urls(config_url):
    global url_config, urls_initialized
    base = config_url.rstrip("/")
    url_config = {
        "base": base,
        "server_mods": f"{base}/modfiles/server",
        "common_mods": f"{base}/modfiles/common",
        "client_mods": f"{base}/modfiles/client",
        "optional_mods": f"{base}/modfiles/clientadditional",
        "force_update": f"{base}/modfiles/forceupdate.txt",
    }
    url_config.update({
        "server_modlist": f"{url_config['server_mods']}/modlist.txt",
        "common_modlist": f"{url_config['common_mods']}/modlist.txt",
        "client_modlist": f"{url_config['client_mods']}/modlist.txt",
        "optional_modlist": f"{url_config['optional_mods']}/modlist.txt",
    })
    urls_initialized = True


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
        print(colored.red(f"Failed to extract mod ID from {mod_path}: {e}"))

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
                                            print(colored.yellow(f"Couldn't find mod ID in pinned jar: {pinned_file}"))
                                            return "unknown"
                                    else:
                                        print(colored.yellow(f"Pinned file {pinned_file} not found in {mod_path}."))
    except Exception as e:
        print(colored.red(f"Failed to extract mod ID from {mod_path}: {e}"))

    return None

def get_mod_id_kotlin_case(mod_path):
    """Extract mod ID from loader.properties in the jar structure."""
    try:
        with zipfile.ZipFile(mod_path, 'r') as jar:
            # Look for any file ending with loader.properties
            metadata_path = "META-INF/jarjar/metadata.json"
            if metadata_path in jar.namelist():
                with jar.open(metadata_path) as json_file:
                    # Now load the JSON content
                    metadata = json.load(json_file)
                    mod_file_path = None
                    for jars in metadata['jars']:
                        if jars['identifier']['artifact'] == 'kffmod':
                            mod_file_path = jars['path']
                            break

                    if mod_file_path:
                        print(f"Found mod path: {mod_file_path} in metadata.json from {mod_path}")
                        with zipfile.ZipFile(mod_path, 'r') as parent_jar:
                            if mod_file_path in parent_jar.namelist():
                                print(f"Looking for mod ID in real mod jar: {mod_file_path}")
                                mod_id = get_mod_id_from_toml(parent_jar.open(mod_file_path))
                                if mod_id:
                                    return mod_id
                            else:
                                print(f"Real mod file {mod_file_path} not found in {mod_path}.")

            else:
                print(f"metadata.json file not found in {mod_path}.")
    except Exception as e:
        print(colored.red(f"Failed to extract mod ID from {mod_path}: {e}"))

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
                        if mod_version == "${file.jarVersion}":
                            print(f"Found '${{file.jarVersion}}' in mods.toml ({mod_path}). Attempting to read from MANIFEST.MF...")
                            # Try to read MANIFEST.MF instead
                            manifest_path = "META-INF/MANIFEST.MF"
                            if manifest_path in jar.namelist():
                                with jar.open(manifest_path) as manifest_file:
                                    for line in manifest_file.read().decode("utf-8").splitlines():
                                        if line.startswith("Implementation-Version:"):
                                            real_version = line.split(":", 1)[1].strip()
                                            print(f"Resolved version from MANIFEST.MF ({mod_path}): {real_version}")
                                            return real_version
                                    print(f"No 'Implementation-Version' found in MANIFEST.MF for {mod_path}")
                            else:
                                print(f"MANIFEST.MF not found in {mod_path}")
                        elif mod_version:
                            return mod_version

    except Exception as e:
        print(colored.red(f"Failed to extract mod version from {mod_path}: {e}"))

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
                                        mod_version = get_mod_version_from_toml(parent_jar.open(pinned_file))
                                        if mod_version:
                                            print(f"Found mod version ({mod_version}) in pinned jar: {pinned_file}")
                                            return mod_version
                                        else:
                                            print(f"Couldn't find mod version in pinned jar: {pinned_file}")
                                    else:
                                        print(f"Pinned file {pinned_file} not found in {mod_path}.")
    except Exception as e:
        print(colored.red(f"Failed to extract mod version from {mod_path}: {e}"))

    return None

def get_mod_version_kotlin_case(mod_path):
    """Extract mod ID from loader.properties in the jar structure."""
    try:
        with zipfile.ZipFile(mod_path, 'r') as jar:
            # Look for any file ending with loader.properties
            metadata_path = "META-INF/jarjar/metadata.json"
            if metadata_path in jar.namelist():
                with jar.open(metadata_path) as json_file:
                    # Now load the JSON content
                    metadata = json.load(json_file)
                    mod_file_path = None
                    for jars in metadata['jars']:
                        if jars['identifier']['artifact'] == 'kffmod':
                            mod_file_path = jars['path']
                            break

                    if mod_file_path:
                        print(f"Found mod path: {mod_file_path} in metadata.json from {mod_path}")
                        with zipfile.ZipFile(mod_path, 'r') as parent_jar:
                            if mod_file_path in parent_jar.namelist():
                                print(f"Looking for mod version in real mod jar: {mod_file_path}")
                                mod_version = get_mod_version_from_toml(parent_jar.open(mod_file_path))
                                if mod_version:
                                    return mod_version
                            else:
                                print(f"Real mod file {mod_file_path} not found in {mod_path}.")

            else:
                print(f"metadata.json file not found in {mod_path}.")
    except Exception as e:
        print(colored.red(f"Failed to extract mod version from {mod_path}: {e}"))

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
            if not mod_id:
                print(f"Mod ID not found in {filename}, checking metadata.json...")
                mod_id = get_mod_id_kotlin_case(mod_path)
            
            if not mod_version:
                print(f"Mod version not found in {filename}, checking loader.properties...")
                mod_version = get_mod_version_from_loader_properties(mod_path)
            if not mod_version:
                print(f"Mod version not found in {filename}, checking metadata.json...")
                mod_version = get_mod_version_kotlin_case(mod_path)

            if mod_id:
                if mod_id not in installed_mods:
                    installed_mods[mod_id] = [[], []]  # Store a list of filenames
                installed_mods[mod_id][0].append(filename)  # Add filename to the list
                installed_mods[mod_id][1].append(mod_version)  # Add filename to the list

    return installed_mods


def get_cloud_modlist(environment):
    """Fetch the modlist.txt from Netlify and return a dictionary with mod IDs, filenames, and a flag for the environment."""
    if environment == "server":
        mod_url = url_config["server_modlist"]
    elif environment == "common":
        mod_url = url_config["common_modlist"]
    elif environment == "client":
        mod_url = url_config["client_modlist"]
    elif environment == "clientadditional":
        mod_url = url_config["optional_modlist"]
    
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
        print(colored.red(f"Failed to fetch {environment} modlist.txt from {mod_url}"))
        return {}
    

def download_and_extract_zips(base_zip_name, environment, local_mods_path):
    """Download a mod zip file and extract its contents."""
    if not urls_initialized:
        raise RuntimeError("URL configuration not initialized. Ensure load_config() is called first.")
    if environment == "server":
        base_url = url_config["server_mods"]
    elif environment == "common":
        base_url = url_config["common_mods"]
    elif environment == "client":
        base_url = url_config["client_mods"]
    elif environment == "clientadditional":
        base_url = url_config["optional_mods"]
    else:
        print(colored.red(f"Unknown environment for downloading mods.zip: {environment}"))
        return

    index = 0
    while True:
        zip_filename = (
            f"{base_zip_name}" if index == 0
            else f"{os.path.splitext(base_zip_name)[0]}{index}.zip"
        )
        zip_url = f"{base_url}/{zip_filename}"
        print(f"Trying to download: {zip_url}")

        response = requests.get(zip_url, stream=True)
    
        if response.status_code != 200:
            if index == 0:
                print(f"No zip file found at {zip_url}")
                index += 1
                continue
            elif index > 0:
                print(f"No zip file found at {zip_url}")
                break

        zip_path = os.path.join(local_mods_path, zip_filename)
        with open(zip_path, 'wb') as zip_file:
            zip_file.write(response.content)

        # Now extract the contents of the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(local_mods_path)
        print(colored.cyan(f"Extracted mods from {zip_filename} ({environment}) into {local_mods_path}"))

        os.remove(zip_path)  # Remove the zip file after extraction
        index += 1


def download_mod(mod_filename, environment, local_mods_path):
    """Download a mod file from the Netlify server."""
    if not urls_initialized:
        raise RuntimeError("URL configuration not initialized. Ensure load_config() is called first.")
    if environment == "server":
        mod_url = f"{url_config["server_mods"]}/{mod_filename}"
    elif environment == "common":
        mod_url = f"{url_config["common_mods"]}/{mod_filename}"
    elif environment == "client":
        mod_url = f"{url_config["client_mods"]}/{mod_filename}"
    elif environment == "clientadditional":
        mod_url = f"{url_config["optional_mods"]}/{mod_filename}"

    response = requests.get(mod_url, stream=True)
    
    if response.status_code == 200:
        mod_path = os.path.join(local_mods_path, mod_filename)
        with open(mod_path, 'wb') as mod_file:
            mod_file.write(response.content)
            # shutil.copyfileobj(response.content, mod_file)
        # print(f"Downloaded new mod: {response.url}")
    else:
        print(colored.red(f"Failed to download {mod_filename} from {mod_url}"))

def updateWhenForceUpdate(mod_id: str, log_file_path: str) -> str:
    global cached_cloud_force_update_list

    if cached_cloud_force_update_list is None:
        cached_cloud_force_update_list = getForceUpdateCharSequences()
    if not cached_cloud_force_update_list: return ""
    for cloud_mod_id, randomSeqeunce in cached_cloud_force_update_list.items():
        if cloud_mod_id != mod_id: continue
        if get_recent_force_update(mod_id , log_file_path) != randomSeqeunce:
            return randomSeqeunce
        if get_recent_force_update(mod_id, log_file_path) == randomSeqeunce:
            return randomSeqeunce
    return ""

def getForceUpdateCharSequences():
    response = requests.get(url_config["force_update"])

    if response.status_code == 200:
        print(f"Fetching forceupdate.txt from {url_config["force_update"]}")
        modlist_lines = response.text.splitlines()
        modlist_dict = {}

        for line in modlist_lines:
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                mod_id, randomSequence = parts
                modlist_dict[mod_id] = randomSequence
        return modlist_dict
    else:
        print(colored.red(f"Failed to fetch forceupdate.txt from {url_config["force_update"]}"))
    return {}
# def getForceUpdateCharSequences(mod_id: str, valid_environments: list[str]):
    valid_environment_keys = {}
    for valid_environment in valid_environments:
        current_key = ""
        if valid_environment == "server":
            current_key = "s"
        if valid_environment == "common":
            current_key = "c"
        if valid_environment == "client":
            current_key = "r"
        if valid_environment == "clientadditional":
            current_key = "a"
        if not valid_environment_keys.__contains__(current_key):
            valid_environment_keys.update(current_key)
            
    response = requests.get(NETLIFY_FORCE_UPDATE_LIST_URL)

    if response.status_code == 200:
        print(f"Fetching forceupdate.txt from {NETLIFY_FORCE_UPDATE_LIST_URL}")
        modlist_lines = response.text.splitlines()
        modlist_dict = {}

        for line in modlist_lines:
            parts = line.split(maxsplit=2)
            if len(parts) == 3:
                environments, mod_id2, randomSequence = parts
                chars = list(environments)
                for key in valid_environment_keys:
                    if chars.__contains__(key):
                        modlist_dict[mod_id] = {"randomSequence": f"{randomSequence}"}
        return modlist_dict
    else:
        print(f"Failed to fetch forceupdate.txt from {NETLIFY_FORCE_UPDATE_LIST_URL}")
    return {}

def get_recent_force_update(mod_id: str, log_file_path: str) -> str:
    global cached_force_update_log
    if cached_force_update_log is None:
        cached_force_update_log = get_force_update_log(log_file_path)
    if cached_force_update_log:
        log = cached_force_update_log
        return log.get(mod_id, "")
    return ""

def get_force_update_log(log_file_path: str):
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "r") as log_file:
                log = json.load(log_file)
                print("Cloud forced update log loaded successfully.")
                return log
        except (json.JSONDecodeError, IOError) as e:
            print(colored.red(f"Error loading cloud forced update log file: {e}. Removing invalid log file."))
            os.remove(log_file_path)
    else:
        print("No cloud forced update log found")
    return {}

def writeForceUpdateLog(log_file_path: str, force_update_log: dict):
    if force_update_log == {}:
        global cached_cloud_force_update_list

        if cached_cloud_force_update_list is None:
            cached_cloud_force_update_list = getForceUpdateCharSequences()
            force_update_log = cached_cloud_force_update_list
    if os.path.exists(log_file_path):
        print("Rewriting cloud forced update log")
    else:
        print("Creating cloud forced upate log")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    with open(log_file_path, "w") as log_file:
        json.dump(force_update_log, log_file, indent=4)

def removeWithCheck(path, message: str, error: str):
    try:
        if os.path.exists(path):
            os.remove(path)
            if message != "": print(message)
        else:
            if error != "": print(colored.yellow(error))
    except FileNotFoundError:
        if error != "": print(colored.yellow(error))

def safe_exit():
    input("\nPress Enter to exit...")
    sys.exit()
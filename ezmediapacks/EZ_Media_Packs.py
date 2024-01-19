import os
import subprocess
import getpass
import time
import hashlib
import shutil
import requests
from urllib.parse import urlencode

# VARS
auth_url = "https://forum.readycade.com/auth.php"
install_dir_7zip = "C:\\Program Files\\7-Zip"
version_7zip = "2301"
download_url_7zip = f"https://www.7-zip.org/a/7z{version_7zip}-x64.exe"
base_url_media_packs = "https://forum.readycade.com/readycade_media/"
target_directory_media_packs = os.path.join(os.getenv('APPDATA'), 'readycade', 'mediapacks')
max_attempts = 4

def check_network_share():
    print("Checking if the network share is available...")
    try:
        response = subprocess.run(["ping", "-n", "1", "RECALBOX"], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: Could not connect to the network share \\RECALBOX.")
        print("Please make sure you are connected to the network and try again.")
        input("Press Enter to exit...")
        exit(1)
    print()

def prompt_for_credentials():
    db_username = input("Enter your username: ")
    db_password = getpass.getpass("Enter your password: ")

    # TODO: Use the credentials for authentication

def authenticate(username, password):
    payload = {"dbUsername": username, "dbPassword": password}
    response = requests.post(auth_url, data=payload)

    if response.text != "Authenticated":
        print("Authentication failed. Exiting script...")
        exit(1)
    else:
        print("Authentication successful. Proceeding with installation...")

def countdown_message(seconds):
    for i in range(seconds, 0, -1):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("IMPORTANT NOTICE: You are about to install...")
        print(f"Starting installation automatically in {i} seconds...")
        time.sleep(1)

def install_7zip():
    if os.path.exists(os.path.join(install_dir_7zip, "7z.exe")):
        print("7-Zip is already installed.")
    else:
        print("Downloading and installing 7-Zip...")
        local_temp_dir = "C:\\Temp\\readycade"
        os.makedirs(local_temp_dir, exist_ok=True)

        # Download 7-Zip installer
        subprocess.run(["curl", "-L", "--insecure", "-o", os.path.join(local_temp_dir, "7z_installer.exe"), download_url_7zip])

        # Run 7-Zip installer
        subprocess.run(["start", "/wait", "", os.path.join(local_temp_dir, "7z_installer.exe")])

        if os.path.exists(os.path.join(install_dir_7zip, "7z.exe")):
            print("7-Zip is now installed.")
        else:
            print("Installation failed.")
            exit(1)

def download_media_pack(selected_media_pack):
    download_url = base_url_media_packs + selected_media_pack
    target_path = os.path.join(target_directory_media_packs, selected_media_pack)

    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        print(f"Attempt {attempt} to download {selected_media_pack}...")

        # Download the selected media pack with curl
        response = subprocess.run(["curl", "-k", "-C", "-", "-o", target_path, download_url], capture_output=True, text=True)

        if response.returncode == 0:
            print(f"Download of {selected_media_pack} was successful.")
            return True
        else:
            print(f"Download of {selected_media_pack} failed on attempt {attempt}.")
            if attempt < max_attempts:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print("Maximum download attempts reached. Download failed.")
                return False

def main():
    # CHECK NETWORK SHARE
    check_network_share()

    # PROMPT FOR USERNAME AND PASSWORD
    prompt_for_credentials()

    # TODO: Use the credentials for authentication
    # authenticate(db_username, db_password)

    # 10 SECOND COUNTDOWN MESSAGE
    countdown_message(10)

    # INSTALL 7-ZIP
    install_7zip()

    # MEDIA PACK VARS
    # ... (remaining code for media packs)

    # DOWNLOAD MEDIA PACK
    # ... (remaining code for downloading and extracting media packs)

    # CHECK MD5 CHECKSUM
    # ... (remaining code for checksum verification)

    # EXTRACTION AND XCOPY TO NETWORK SHARE
    # ... (remaining code for extraction and copying to network share)

    # CLEAN UP TEMP FILES
    # ... (remaining code for cleaning up temporary files)

    # END MESSAGE WITH COUNTDOWN
    countdown_message(10)

if __name__ == "__main__":
    main()

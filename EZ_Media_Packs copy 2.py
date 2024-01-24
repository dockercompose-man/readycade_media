"""
*************************************************************************
 * 
 * READYCADE CONFIDENTIAL
 * __________________
 * 
 *  [2024] Readycade Incorporated 
 *  All Rights Reserved.
 * 
 * NOTICE:  All information contained herein is, and remains
 * the property of Readycade Incorporated and its suppliers,
 * if any.  The intellectual and technical concepts contained
 * herein are proprietary to Readycade Incorporated
 * and its suppliers and may be covered by U.S. and Foreign Patents,
 * patents in process, and are protected by trade secret or copyright law.
 * Dissemination of this information or reproduction of this material
 * is strictly forbidden unless prior written permission is obtained
 * from Readycade Incorporated.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import requests
from requests.exceptions import RequestException
import hashlib
from http.client import IncompleteRead
import subprocess
import shutil
import sys
import threading
import time
from tqdm import tqdm

# VARS
base_url = "https://forum.readycade.com/readycade_media/"
auth_url = "https://forum.readycade.com/auth.php"

# Global variable to track whether the download should be canceled
download_canceled = False

global_password = "uXR9mtjKxtHHGuQ7qUL6"

def download_file(url, target_directory, status_var, progress_var, max_retries=3):
    local_filename = os.path.join(target_directory, os.path.basename(url))
    display_filename = os.path.basename(local_filename)
    block_size = 8192  # 8 Kibibytes

    for attempt in range(1, max_retries + 1):
        try:
            # Get the size of the existing file
            downloaded_size = os.path.getsize(local_filename) if os.path.exists(local_filename) else 0

            headers = {}
            if downloaded_size > 0:
                headers['Range'] = f"bytes={downloaded_size}-"

            with requests.get(url, stream=True, headers=headers, timeout=10) as response:
                response.raise_for_status()

                # Check for a 206 status code, which indicates a partial content response
                if response.status_code == 206:
                    range_info = response.headers.get('content-range')
                    if range_info:
                        range_parts = range_info.split(' ')[-1].split('-')
                        start = int(range_parts[0])
                        total_parts = range_parts[1].split('/')
                        total = int(total_parts[0])
                        total_size_in_bytes = total - start + 1
                    else:
                        total_size_in_bytes = int(response.headers.get('content-length', 0))
                else:
                    total_size_in_bytes = int(response.headers.get('content-length', 0))

                with open(local_filename, 'ab') as f, tqdm(total=total_size_in_bytes, unit='B', unit_scale=True) as bar:
                    for chunk in response.iter_content(chunk_size=block_size):
                        if download_canceled:
                            status_var.set(f"Download canceled for {display_filename}.")
                            root.after(2000, cleanup_temp_files, target_directory, local_filename)
                            return None

                        f.write(chunk)
                        downloaded_size += len(chunk)
                        bar.update(len(chunk))
                        progress_var.set((downloaded_size / max(1, total_size_in_bytes)) * 100)
                        status_var.set(f"Download in Progress for {display_filename} Please Wait...")
                        root.update_idletasks()

                return local_filename

        except requests.exceptions.RequestException as e:
            print(f"Error during download attempt {attempt}: {e}")
            root.after(2000, clear_status)
            root.after(2000, reset_download_button_delayed)  # Reset the Download button text

        # Implement exponential backoff outside the loop
        wait_time = 2 ** attempt
        print(f"Retrying in {wait_time} seconds...")
        status_var.set(f"Resuming Download for {display_filename}...")
        time.sleep(wait_time)

    status_var.set(f"Max retries reached. Download failed for {display_filename}.")
    root.after(2000, clear_status)
    root.after(2000, reset_download_button_delayed)  # Reset the Download button text
    return None


def calculate_md5_from_file_url(file_url):
    """Calculate the MD5 hash of a file from its URL."""
    md5 = hashlib.md5()
    with requests.get(file_url, stream=True) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            md5.update(chunk)
    return md5.hexdigest()

def calculate_file_md5(file_path):
    """Calculate the MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as file:
        while chunk := file.read(8192):
            md5.update(chunk)
    return md5.hexdigest()

def download_config_pack(base_url, target_directory, selected_config_pack, md5_checksums, status_var, progress_var):
    try:
        config_file_name = config_pack_names[selected_config_pack]

        print(f"Selected media pack: {selected_config_pack}")
        print(f"Media file name: {config_file_name}")

        # Compare the MD5 value from the server with the expected MD5
        expected_md5 = md5_checksums.get(config_file_name, "")
        print(f"Expected MD5: {expected_md5}")

        if expected_md5 != server_md5:
            print("MD5 values from the server do not match the expected MD5. Exiting...")
            status_var.set(f"MD5 values from the server do not match the expected MD5 for {config_file_name}. Exiting...")
            root.after(2000, clear_status)
            root.after(2000, reset_download_button_text)  # Reset the Download button text
            return None

        # Proceed with the rest of the download process
        console_folder = download_file(config_pack_file_url, target_directory, status_var, progress_var)

            # Check if the downloaded file is None (indicating an error)
        if console_folder is None:
            return None

        if console_folder:
            browse_text.set("Download")
            messagebox.showinfo("Media Pack Installed!", "Media Pack Installed! Please Reboot Your Readycade Now.")
            root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)
        else:
            browse_text.set("Download")
            root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)
            root.after(2000, reset_download_button_text)  # Reset the Download button text
    except KeyError:
        print(f"Error: Key not found for '{selected_config_pack}' in config_pack_names. Available keys: {list(config_pack_names.keys())}")
        return None

def extract_config_packs(selected_config_pack, target_directory, status_var):
    config_file_name = config_pack_names[selected_config_pack]

    # Calculate the MD5 hash of the downloaded file
    actual_md5 = calculate_file_md5(os.path.join(target_directory, config_file_name))
    print(f"Actual MD5 from the downloaded file: {actual_md5}")

    # Compare the MD5 values
    expected_md5 = md5_checksums.get(config_file_name, "")
    print(f"Expected MD5: {expected_md5}")

    if expected_md5 != actual_md5:
        status_var.set(f"MD5 values do not match for {config_file_name}. Extraction aborted.")
        root.after(2000, clear_status)
        root.after(2000, reset_download_button_text)  # Reset the Download button text
        return None

    # Specify the target folder for extraction
    extraction_folder = target_directory

    # Proceed with the extraction directly to the target directory
    #extraction_command = [r'C:\Program Files\7-Zip\7z.exe', 'x', '-aoa', '-o{}'.format(extraction_folder), '-p{}'.format(global_password), os.path.join(target_directory, config_file_name)]
    #extraction_command = [r'C:\Program Files\7-Zip\7z.exe', 'x', '-aoa', '-o{}'.format(extraction_folder), '-p{}'.format(global_password), os.path.join(target_directory, config_file_name)]
    #extraction_command = [r'C:\Program Files\7-Zip\7z.exe', 'x', '-aoa', '-o{}'.format(extraction_folder), '-p{}'.format(global_password), os.path.join(target_directory, config_file_name), '-r']
    #extraction_command = [r'C:\Program Files\7-Zip\7z.exe', 'x', '-aoa', '-o{}'.format(os.path.join(extraction_folder, config_file_name.split('.')[0])), '-p{}'.format(global_password), os.path.join(target_directory, config_file_name), '-r']
    extraction_command = [r'C:\Program Files\7-Zip\7z.exe', 'x', '-aoa', '-o{}'.format(os.path.join(extraction_folder, config_file_name.split('.')[0].replace('-media', ''))), '-p{}'.format(global_password), os.path.join(target_directory, config_file_name), '-r']


    # Check if the extraction is successful
    if subprocess.run(extraction_command).returncode == 0:
        # Define the source and target paths for the share folder
        
        target_directory_network = r"F:\Readycade\TEMP\share\roms\{}".format(selected_config_pack)
        #target_directory_network = r"\\RECALBOX\share\roms\{}".format(console_name)

        source_share_path = os.path.join(extraction_folder, config_file_name)
        #target_directory_network = r"\\RECALBOX\share\roms\{}".format(console_name)

        source_directory = os.path.join(extraction_folder, config_file_name.split('.')[0])
        source_directory = source_directory.replace("-media", "")  # Remove "-media" from the directory name
        source_directory = source_directory.replace(".7z", "")  # Remove ".7z" from the directory name

        # Check if the source directory exists before attempting to copy
        if os.path.exists(source_directory):
            shutil.copytree(source_directory, target_directory_network, dirs_exist_ok=True)
        else:
            print(f"Source directory '{source_directory}' does not exist.")



        # Copy only the "share" folder to the network share
        status_var.set(f"Copying Files to Readycade... Please Wait...")
        print("Copying Files to Readycade... Please Wait...")
        #source_directory = os.path.join(extraction_folder, config_file_name.replace(".7z", ""))
        #source_directory = os.path.join(extraction_folder, config_file_name.replace("-media", "").replace(".7z", ""))
        
        #source_directory = os.path.join(extraction_folder, config_file_name.replace(".7z", ""))
        #shutil.copytree(source_directory, target_directory_network, dirs_exist_ok=True)

        #shutil.copytree(source_share_path, target_directory_network, dirs_exist_ok=True)
        
        status_message = f"{selected_config_pack} {config_file_name} folder copied to {target_directory_network}"
        status_var.set(status_message)
        time.sleep(2)  # Sleep for 2 seconds

        status_message = "Files Copied Successfully!"
        status_var.set(status_message)
        time.sleep(2)  # Sleep for 2 seconds

        print("Files Copied Successfully!")
        
        # Display a message box for successful installation
        root.after(1000, clear_and_reset_status, "Media Pack Installed! Please Select Another or Exit the application.")
        print("Media Pack Installed! Please Select Another or Exit the application.")

        # Call cleanup_temp_files only after the successful copy
        root.after(2000, cleanup_temp_files, target_directory, os.path.join(target_directory, config_file_name))
        print("Cleaning Up Temporary Files and Exiting...")



def cleanup_temp_files(target_directory, file_path):
    # Wait for a short time to ensure the file is not in use
    time.sleep(1)

    # Check if the file exists and is not in use
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except PermissionError:
            # File is still in use, wait and try again
            time.sleep(1)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

    # Delete the entire target directory
    try:
        shutil.rmtree(target_directory)
        status_var.set("Temporary files deleted.")
    except Exception as e:
        print(f"Error deleting temporary files: {e}")
        status_var.set("Error deleting temporary files.")

    root.after(2000, clear_status)




def clear_status():
    status_var.set("")  # Clear the status after 2000 milliseconds (2 seconds)
    progress_var.set(0)  # Reset the progress bar

def open_file():
    global download_canceled
    browse_text.set("Downloading...")
    download_canceled = False

    # Create and start a new thread for the download
    download_thread_instance = threading.Thread(target=download_thread)
    download_thread_instance.start()

    # Re-enable the download button
    browse_btn['state'] = 'normal'

    # Disable the cancel button
    cancel_btn['state'] = 'normal'

def download_thread():
    global download_canceled
    selected_config_pack = config_pack_combobox.get()

    if selected_config_pack:
        target_directory = os.path.expandvars(r"%APPDATA%\readycade\mediapacks")
        config_file_name = config_pack_names[selected_config_pack]

        # Ensure the target directory exists
        os.makedirs(target_directory, exist_ok=True)

        # URL for the config pack file on the website
        config_pack_file_url = base_url + config_file_name

        try:
            # Fetch the content of the .md5 file from the server
            md5_file_url = config_pack_file_url + '.md5'
            md5_response = requests.get(md5_file_url)
            md5_response.raise_for_status()
            actual_md5_line = md5_response.text.strip().split('\n')[0]  # Get the first line
            actual_md5 = actual_md5_line.split()[0]  # Extract only the hash
            print(f"Actual MD5 from .md5 file on the website: {actual_md5}")

            # Compare the MD5 values
            expected_md5 = md5_checksums.get(config_file_name, "")
            print(f"Expected MD5: {expected_md5}")

            if expected_md5 != actual_md5:
                print("MD5 values do not match. Exiting...")
                status_var.set(f"MD5 values do not match for {config_file_name}. Exiting...")
                root.after(2000, clear_and_reset_status)
                return None

            # Download the config pack file
            downloaded_file = download_file(config_pack_file_url, target_directory, status_var, progress_var)

            # Check if the downloaded file is None (indicating an error)
            if downloaded_file is None:
                return None

            # Compare the MD5 values
            if expected_md5 != actual_md5:
                print("MD5 values do not match. Exiting...")
                status_var.set(f"MD5 values do not match for {config_file_name}. Exiting...")
                root.after(2000, clear_and_reset_status)
            else:
                # Call the extract_config_packs function after download
                extraction_result = extract_config_packs(selected_config_pack, target_directory, status_var)


                if extraction_result:
                    message = "Media Pack Installed! Please Select Another or Exit the application."
                    browse_text.set("Download")
                    root.after(1000, clear_and_reset_status, message)  # Schedule clearing status after 1000 milliseconds (1 second)
                else:
                    browse_text.set("Download")
                root.after(1000, clear_and_reset_status)  # Schedule clearing status after 1000 milliseconds (1 second)

        except requests.exceptions.RequestException as e:
            print(f"Error during download: {e}")
            status_var.set(f"Error during download. Exiting...")
            root.after(2000, clear_and_reset_status)

def clear_and_reset_status(message=None):
    if message:
        messagebox.showinfo("Config Pack Installed", message)

    clear_status()
    reset_download_button_text()




def reset_download_button_text():
    browse_btn['state'] = 'normal'
    browse_text.set("Download")
    cancel_btn['state'] = 'disabled'

def cancel_download():
    global download_canceled
    download_canceled = True

    # Clean up downloaded files and folders
    selected_config_pack = config_pack_combobox.get()
    target_directory = os.path.expandvars(r"%APPDATA%\readycade\mediapacks")
    file_path = os.path.join(target_directory, config_pack_names[selected_config_pack])

    # Attempt to delete the downloaded file
    try:
        if os.path.exists(file_path):
            os.remove(file_path)

        status_var.set("Download canceled. Temporary file deleted.")
        root.after(2000, clear_status)
        root.after(2000, reset_download_button_delayed)  # Display "Download failed" for 2 seconds
    except Exception as e:
        status_var.set(f"Error: {str(e)}")
        root.after(2000, clear_status)
        root.after(2000, reset_download_button_delayed)  # Display "Download failed" for 2 seconds


def reset_download_button_delayed():
    browse_btn['state'] = 'normal'
    browse_text.set("Download")
    cancel_btn['state'] = 'disabled'


root = tk.Tk()
root.title("Readycade™")

# Remove the TK icon
root.iconbitmap(default="icon.ico")

# Set the window icon
icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')  # Replace 'icon.ico' with your actual icon file
root.iconbitmap(icon_path)

# Logo
logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
logo = Image.open(logo_path)
logo = ImageTk.PhotoImage(logo)
logo_label = tk.Label(image=logo)
logo_label.image = logo
logo_label.grid(column=1, row=0)

# Instructions
instructions = tk.Label(root, text="Select a media pack to download:", font="open-sans")
instructions.grid(columnspan=3, column=0, row=1)

# Dictionary to map user-friendly names to actual file names
config_pack_names = {
    "64dd": "64dd-media.7z",
    "amiga600": "amiga600-media.7z",
    "amiga1200": "amiga1200-media.7z",
    "amstradcpc": "amstradcpc-media.7z",
    "apple2": "apple2-media.7z",
    "apple2gs": "apple2gs-media.7z",
    "arduboy": "arduboy-media.7z",
    "atari800": "atari800-media.7z",
    "atari2600": "atari2600-media.7z",
    "atari5200": "atari5200-media.7z",
    "atari7800": "atari7800-media.7z",
    "atarist": "atarist-media.7z",
    "atomiswave": "atomiswave-media.7z",
    "bbcmicro": "bbcmicro-media.7z",
    "bk": "bk-media.7z",
    "c64": "c64-media.7z",
    "channelf": "channelf-media.7z",
    "colecovision": "colecovision-media.7z",
    "daphne": "daphne-media.7z",
    "dos": "dos-media.7z",
    "fds": "fds-media.7z",
    "gamegear": "gamegear-media.7z",
    "gba": "gba-media.7z",
    "gbc": "gbc-media.7z",
    "gb": "gb-media.7z",
    "gw": "gw-media.7z",
    "gx4000": "gx4000-media.7z",
    "intellivision": "intellivision-media.7z",
    "jaguar": "jaguar-media.7z",
    "lowresnx": "lowresnx-media.7z",
    "lutro": "lutro-media.7z",
    "mastersystem": "mastersystem-media.7z",
    "megadrive": "megadrive-media.7z",
    "model3": "model3-media.7z",
    "msx1": "msx1-media.7z",
    "msx2": "msx2-media.7z",
    "msxturbor": "msxturbor-media.7z",
    "multivision": "multivision-media.7z",
    "n64": "n64-media.7z",
    "naomigd": "naomigd-media.7z",
    "naomi": "naomi-media.7z",
    "neogeocd": "neogeocd-media.7z",
    "neogeo": "neogeo-media.7z",
    "nes": "nes-media.7z",
    "ngpc": "ngpc-media.7z",
    "ngp": "ngp-media.7z",
    "o2em": "o2em-media.7z",
    "oricatmos": "oricatmos-media.7z",
    "pcenginecd": "pcenginecd-media.7z",
    "pcengine": "pcengine-media.7z",
    "pcfx": "pcfx-media.7z",
    "pcv2": "pcv2-media.7z",
    "pokemini": "pokemini-media.7z",
    "ports": "ports-media.7z",
    "samcoupe": "samcoupe-media.7z",
    "satellaview": "satellaview-media.7z",
    "scv": "scv-media.7z",
    "sega32x": "sega32x-media.7z",
    "sg1000": "sg1000-media.7z",
    "snes": "snes-media.7z",
    "solarus": "solarus-media.7z",
    "spectravideo": "spectravideo-media.7z",
    "sufami": "sufami-media.7z",
    "supergrafx": "supergrafx-media.7z",
    "supervision": "supervision-media.7z",
    "thomson": "thomson-media.7z",
    "tic80": "tic80-media.7z",
    "trs80coco": "trs80coco-media.7z",
    "uzebox": "uzebox-media.7z",
    "vectrex": "vectrex-media.7z",
    "vic20": "vic20-media.7z",
    "videopacplus": "videopacplus-media.7z",
    "virtualboy": "virtualboy-media.7z",
    "wasm4": "wasm4-media.7z",
    "wswanc": "wswanc-media.7z",
    "wswan": "wswan-media.7z",
    "x1": "x1-media.7z",
    "x68000": "x68000-media.7z",
    "zx81": "zx81-media.7z",
    "zxspectrum": "zxspectrum-media.7z"
}

md5_checksums = {
    "64dd-media.7z": "02633527841f5effa49552d15a75f06",
    "amiga600-media.7z": "ec0ee2c4462d58dcef0270d59fb879e4",
    "amiga1200-media.7z": "0b21b5401db62c1e32cd61a230fd8555",
    "amstradcpc-media.7z": "17d98adf4e1ae1c2e95c0e3b19643d77",
    "apple2gs-media.7z": "757572a2375245e817ecf85a779019fa",
    "apple2-media.7z": "0a71febe67a76855a2378c81281d6084",
    "arduboy-media.7z": "58a59930f4860f7952c6c310bd09d6dd",
    "atari800-media.7z": "3fd31a6256461668441472796bb914d9",
    "atari2600-media.7z": "ca724daa56c8dc151e571ce1e3cf3959",
    "atari5200-media.7z": "5467ef8b8a0aea67a7663bd474c52fde",
    "atari7800-media.7z": "5df36295bd58beb9a23a22d40d16f1cf",
    "atarist-media.7z": "4e742a6c155c5b908d9d4822ea416cc9",
    "atomiswave-media.7z": "b32f2eec52f95ecc2f85efaada389359",
    "bbcmicro-media.7z": "80b904b30ff635c91d7564a2b3664c0b",
    "bk-media.7z": "b11e1af036054656280c2186d4e35a9d",
    "c64-media.7z": "c7cf804b432d4e470fb72dca636304b3",
    "channelf-media.7z": "325afdf3032901cb4e30ab937846ae9e",
    "colecovision-media.7z": "8b25f3685e740fef2c5bfb8fd3777cd2",
    "daphne-media.7z": "7378952dcdb792b34960cd72f40d215e",
    "dos-media.7z": "6cec65e1ac1f7883b2a0f943fa66d4e9",
    "fds-media.7z": "90f1953813de746a54fce3b6113f7759",
    "gamegear-media.7z": "4cba984ef1232c56e4b12952832c67bf",
    "gba-media.7z": "f4e061ca4528b07f70957894715dc96c",
    "gbc-media.7z": "f8260726e716dfc31369b715bdd3981f",
    "gb-media.7z": "b2332a8998377c90e9e005c7341499ee",
    "gw-media.7z": "4eed0afafccb0671bdb2425bb79aefb3",
    "gx4000-media.7z": "2c6b8f7196bc072d0735e0e0a1616350",
    "intellivision-media.7z": "302eb899b63feff4998b55108ce7a81d",
    "jaguar-media.7z": "3cbda529a084ec721e05dc2591d874b8",
    "lowresnx-media.7z": "5d228cd2ed75e81047184fbea710c45f",
    "lutro-media.7z": "0d7ba0eab7731495ccf39817ffc439fa",
    "mastersystem-media.7z": "1573be2766d9294357c05cf027096d17",
    "megadrive-media.7z": "c0002f7e22ce95db52ae4ca50a250646",
    "model3-media.7z": "460a9adf34ea11ae3b62e99d5bfbb089",
    "msx1-media.7z": "e859f8743b2f0bfab560236f4e12fa85",
    "msx2-media.7z": "e02668a546b9b5e421eb4c3e5c4627aa",
    "msxturbor-media.7z": "f2ced6eca446f041ba841672a1994edc",
    "multivision-media.7z": "d1de52b69a00c31e6aa88fa64666f7de",
    "n64-media.7z": "5b6e5f82471e9c529da8e20a70d86106",
    "naomigd-media.7z": "f422fbff8458411a781eb7cd34c67955",
    "naomi-media.7z": "1bc1a4b51b126494f83e53ba2b3eae10",
    "neogeocd-media.7z": "5463b80f5b0e7a59ec5d28c229b19d77",
    "neogeo-media.7z": "97561127ff4cd3e628d1d46d89d6d657",
    "nes-media.7z": "09f09fdb81ea3b08fb3e5d9269593cd7",
    "ngpc-media.7z": "897e37aa78ff02d7e6b30cb8ae7a2fd3",
    "ngp-media.7z": "d5612cad58852ef49a8ef777556b21c7",
    "o2em-media.7z": "aaed517b57a46eca0a49bddacb70f8f5",
    "oricatmos-media.7z": "a8ad4bec5708855be2dd3f909932b6c1",
    "pcenginecd-media.7z": "af53fc5f72ec32ff38494b2263780588",
    "pcengine-media.7z": "c7806830ff89bebc4a1c6805fb41ab4d",
    "pcfx-media.7z": "abf249f735af3ef1347c21e4fe3ea587",
    "pcv2-media.7z": "df6715d1f58f3f1d68cc54489a5c9ea7",
    "pokemini-media.7z": "5a29562e0811fc92618490e8c493a0b9",
    "ports-media.7z": "5c4d299225960db86f96c4c8f256d27b",
    "samcoupe-media.7z": "c8596a6a8b34bbf575a9a860fb0424ee",
    "satellaview-media.7z": "155de8b31cf282830147eaf2da318cdb",
    "scv-media.7z": "3e5416a9362a916afbec5aace20ba85c",
    "sega32x-media.7z": "6d4d28a77dc7d17558bd84a551fda858",
    "sg1000-media.7z": "03a35433225a98cc207e85ab0218c67c",
    "snes-media.7z": "21e15c70346077f76e485ae7bc3c926d",
    "solarus-media.7z": "5ccd34f981f6292b2a71167f5ab8c58f",
    "spectravideo-media.7z": "99e2478efc2abb2e1b99b4850d42d81e",
    "sufami-media.7z": "730a2f1e59d1be16f2cb6e985f17d791",
    "supergrafx-media.7z": "d688ef83a6c76c70208823d2186facf6",
    "supervision-media.7z": "46d135a43f92b520e8eed59456728f0b",
    "thomson-media.7z": "44de11e083f8b83dd716b49f28916198",
    "tic80-media.7z": "544b395f8ce647680f7d72373fd312da",
    "trs80coco-media.7z": "7680994e4741e3effdcca3006f9695c1",
    "uzebox-media.7z": "56de7b7a7b44d37470fe3d4de390bf54",
    "vectrex-media.7z": "1b8af8efa329b371e46f3667aa1abf57",
    "vic20-media.7z": "58f17c5ee7b43e46d313d1f31a4673ba",
    "videopacplus-media.7z": "8125a02392ecf0af3b8d79e89b631820",
    "virtualboy-media.7z": "05664fa10069a91cf6fa5e87408265ba",
    "wasm4-media.7z": "d23db9df70f336c8a9102c427804f27d",
    "wswanc-media.7z": "2be2634641f1e580bd90a7e4af78a5c5",
    "wswan-media.7z": "5f9114181147467e8c0be035c66e3ca1",
    "x1-media.7z": "9975f3b17dba0c642b84d0ef18b3515d",
    "x68000-media.7z": "6905d8cc5109cc4d131e30a0b746accf",
    "zx81-media.7z": "a79d7847f0bac3a5a8eab17791ed6610",
    "zxspectrum-media.7z": "913a3ac9a8ee085709ebeaa7ebf02942" 
}

# Config pack selection dropdown
config_packs = list(config_pack_names.keys())

config_pack_combobox = ttk.Combobox(root, values=config_packs)
config_pack_combobox.grid(column=1, row=2)
config_pack_combobox.set("Select a media pack")

canvas = tk.Canvas(root, width=600, height=100)
canvas.grid(columnspan=3)

# Browse Button
browse_text = tk.StringVar()
browse_btn = tk.Button(root, textvariable=browse_text, command=open_file, font="open-sans", bg="#ff6600", fg="white", height=2, width=15)
browse_text.set("Download")
browse_btn.grid(column=1, row=3)

# Progress bar
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, length=175, mode='determinate')
progress_bar.grid(column=1, row=4)

# Status Label
status_var = tk.StringVar()
status_label = tk.Label(root, textvariable=status_var, font="open-sans")
status_label.grid(columnspan=3, column=0, row=5)

# Cancel Button
cancel_btn = tk.Button(root, text="Cancel", command=cancel_download, font="open-sans", bg="#ff0000", fg="white", height=2, width=15, state='disabled')
cancel_btn.grid(column=1, row=6)

root.mainloop()


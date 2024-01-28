"""
************************************************************************** 
* READYCADE CONFIDENTIAL
* __________________
* 
*  [2024] Readycade Incorporated 
*  All Rights Reserved.
* 
* NOTICE:  All information contained herein is, and remains* the property of Readycade Incorporated and its suppliers,
* if any.  The intellectual and technical concepts contained* herein are proprietary to Readycade Incorporated
* and its suppliers and may be covered by U.S. and Foreign Patents,
* patents in process, and are protected by trade secret or copyright law.
* Dissemination of this information or reproduction of this material
* is strictly forbidden unless prior written permission is obtained
* from Readycade Incorporated.
**************************************************************************
* Author Michael Cabral 2024
* Title: EZ_Install
* Proprietary License
* Description: Downloads and Installs Readycade Configuration Packs to your Readycade
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Scrollbar, Text
from PIL import Image, ImageTk
import os
import requests
from requests.exceptions import RequestException
import hashlib
from http.client import IncompleteRead
import platform
import subprocess
import shutil
import sys
import threading
import time
from tqdm import tqdm

# VARS
base_url = "https://forum.readycade.com/readycade_configs/"
auth_url = "https://forum.readycade.com/auth.php"

# Global variable to track whether the download should be canceled
download_canceled = False

global_password = "o2M8K2zjs67ysJR8jWy7"

def show_eula():
    # Load EULA from EULA.txt
    with open("EULA.txt", "r") as file:
        eula_text = file.read()

    # Create a new window for displaying the EULA
    eula_window = tk.Toplevel()
    eula_window.title("End User License Agreement")

    # Add a Text widget for displaying the EULA text with a scroll bar
    text_box = Text(eula_window, wrap=tk.WORD, height=24, width=70, padx=15, pady=15)
    text_box.insert(tk.END, eula_text)
    text_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # Add a scrollbar
    scrollbar = Scrollbar(eula_window, command=text_box.yview)
    scrollbar.grid(row=0, column=1, sticky="nsew")
    text_box['yscrollcommand'] = scrollbar.set

    # Add "Agree" and "Disagree" buttons
    def agree():
        eula_window.destroy()
        root.deiconify()

    agree_button = tk.Button(eula_window, text="Agree", command=agree)
    agree_button.grid(row=1, column=0, padx=5, pady=5)

    # Adjust the size of the EULA window
    eula_window.geometry("640x480")

    # Force the focus on the EULA window
    eula_window.focus_force()

    # Handle window closure
    eula_window.protocol("WM_DELETE_WINDOW", agree)


def check_windows():
    if platform.system() != 'Windows':
        messagebox.showerror("Error", "This script is intended to run on Windows only. Exiting.")
        sys.exit(1)

# Call the function to check the platform
check_windows()

# If the platform check passed, continue with the rest of your code
print("Script is running on Windows. Continue execution.")

# CHECK NETWORK SHARE
print("Checking if the network share is available...")

try:
    subprocess.run(["ping", "-n", "1", "RECALBOX"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Network share found.")
except subprocess.CalledProcessError:
    print("Error: Could not connect to the network share \\RECALBOX.")
    print("Please make sure you are connected to the network and try again.")
    
    # Show a message box
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showerror("Error", "Network Share not found. Please make sure you are connected to the network and try again.")
    sys.exit()

print()

def get_credentials():
    db_username = simpledialog.askstring("Authentication", "Enter your username:")
    db_password = simpledialog.askstring("Authentication", "Enter your password:", show='*')

    if db_username and db_password:
        print(f"Username: {db_username}, Password: {db_password}")
    else:
        print("Authentication canceled.")
        sys.exit()

# Get username and password from user input
db_username = simpledialog.askstring("Authentication", "Enter your username:")
db_password = simpledialog.askstring("Authentication", "Enter your password:", show='*')

# AUTHENTICATION
# Perform authentication by sending a POST request to auth.php using the captured credentials
data = {"dbUsername": db_username, "dbPassword": db_password}
response = requests.post(auth_url, data=data)

# Check the authentication result
auth_result = response.text.strip()

if auth_result != "Authenticated":
    print("Authentication failed. Exiting script...")
    sys.exit()

print("Authentication successful. Proceeding with installation...")

# Define the installation directory for 7-Zip
installDir = "C:\\Program Files\\7-Zip"

# Define the 7-Zip version you want to download
version = "2301"

# Define the download URL for the specified version
downloadURL = f"https://www.7-zip.org/a/7z{version}-x64.exe"

# Check if 7-Zip is already installed by looking for 7z.exe in the installation directory
seven_zip_installed = os.path.exists(os.path.join(installDir, "7z.exe"))

if seven_zip_installed:
    print("7-Zip is already installed.")
else:
    # Echo a message to inform the user about the script's purpose
    print("Authentication successful. Proceeding with installation...")

    # Define the local directory to save the downloaded installer
    localTempDir = os.path.expandvars(r"%APPDATA%\readycade\temp")

    # Download the 7-Zip installer using curl and retain the original name
    os.makedirs(localTempDir, exist_ok=True)
    downloadPath = os.path.join(localTempDir, "7z_installer.exe")
    with requests.get(downloadURL, stream=True) as response, open(downloadPath, 'wb') as outFile:
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        with tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading 7-Zip') as pbar:
            for data in response.iter_content(block_size):
                pbar.update(len(data))
                outFile.write(data)

    # Run the 7-Zip installer and wait for it to complete
    subprocess.run(["start", "/wait", "", downloadPath], shell=True)

    # Check if the installation was successful
    if not os.path.exists(os.path.join(installDir, "7z.exe")):
        print("Installation failed.")
        sys.exit()

    # Additional code to run after the installation is complete
    print("7-Zip is now installed.")

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

        print(f"Selected config pack: {selected_config_pack}")
        print(f"Config file name: {config_file_name}")

        # Calculate the MD5 hash of the file on the server
        server_md5 = calculate_md5_from_url(base_url + config_file_name)
        print(f"MD5 from the server: {server_md5}")

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
            messagebox.showinfo("Config Pack Installed", "Config Pack Installed! Please Reboot Your Readycade Now.")
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
    extraction_command = [r'C:\Program Files\7-Zip\7z.exe', 'x', '-aoa', '-o{}'.format(extraction_folder), '-p{}'.format(global_password), os.path.join(target_directory, config_file_name)]

    # Check if the extraction is successful
    if subprocess.run(extraction_command).returncode == 0:
        # Define the source and target paths for the share folder
        source_share_path = os.path.join(extraction_folder, "share")
        target_directory_network = r"F:\Readycade\TEMP"
        #target_directory_network = r"\\RECALBOX\share"

        # Copy only the "share" folder to the network share
        status_var.set(f"Copying Files to Readycade... Please Wait...")
        print("Copying Files to Readycade... Please Wait...")
        shutil.copytree(source_share_path, target_directory_network, dirs_exist_ok=True)

        status_message = f"{selected_config_pack} config pack 'share' folder copied to {target_directory_network}"
        status_var.set(status_message)

        print("Files Copied Successfully!")
        
        # Display a message box for successful installation
        root.after(1000, clear_and_reset_status, "Config Pack Installed! Please Select Another or Exit the application.")
        print("Config Pack Installed! Please Select Another or Exit the application.")

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
        target_directory = os.path.expandvars(r"%APPDATA%\readycade\configpacks")
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
                    message = "Config Pack Installed! Please Select Another or Exit the application."
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
    target_directory = os.path.expandvars(r"%APPDATA%\readycade\configpacks")
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

# Hide the main window initially
root.withdraw()

# Show EULA before creating the main window
show_eula()

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
instructions = tk.Label(root, text="Select a config pack to download:", font="open-sans")
instructions.grid(columnspan=3, column=0, row=1)

# Dictionary to map user-friendly names to actual file names
config_pack_names = {
    "Normal": "readycade_configs.7z",
    "Interger Scaled": "readycade_configs-interger.7z"
}

md5_checksums = {
    "readycade_configs.7z": "4d3f90351e3321ee45a36d8c87e4cb7f",
    "readycade_configs-interger.7z": "c444b3d6ad3ab8706e507e02a71cb43b"
}

# Config pack selection dropdown
config_packs = list(config_pack_names.keys())

config_pack_combobox = ttk.Combobox(root, values=config_packs)
config_pack_combobox.grid(column=1, row=2)
config_pack_combobox.set("Select a config pack")

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


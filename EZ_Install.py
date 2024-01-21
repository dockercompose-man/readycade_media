# /*************************************************************************
# * 
# * READYCADE CONFIDENTIAL
# * __________________
# * 
# *  [2024] Readycade Incorporated 
# *  All Rights Reserved.
# * 
# * NOTICE:  All information contained herein is, and remains
# * the property of Readycade Incorporated and its suppliers,
# * if any.  The intellectual and technical concepts contained
# * herein are proprietary to Readycade Incorporated
# * and its suppliers and may be covered by U.S. and Foreign Patents,
# * patents in process, and are protected by trade secret or copyright law.
# * Dissemination of this information or reproduction of this material
# * is strictly forbidden unless prior written permission is obtained
# * from Readycade Incorporated.
# */

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import requests
from requests.exceptions import ChunkedEncodingError
import hashlib
import subprocess
import shutil
import sys
import threading
import time
from tqdm import tqdm
import urllib.request

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

# VARS
base_url = "https://forum.readycade.com/readycade_configs/"
auth_url = "https://forum.readycade.com/auth.php"

# Global variable to track whether the download should be canceled
download_canceled = False

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

global_password = "o2M8K2zjs67ysJR8jWy7"

def download_config_pack(base_url, target_directory, selected_config_pack, md5_checksums, status_var, progress_var):
    try:
        config_file_name = config_pack_names[selected_config_pack]
        file_path = os.path.join(target_directory, config_file_name)

        print(f"Selected config pack: {selected_config_pack}")
        print(f"Config file name: {config_file_name}")

        download_url = base_url + config_file_name
        file_size = 0

        # Get the file size without downloading the content
        response = requests.head(download_url, stream=True)
        if response.status_code == 200:
            file_size = int(response.headers.get('content-length', 0))

        block_size = 1024
        max_attempts = 4
        attempt = 0

        def update_gui():
            progress = (current_size / file_size) * 100
            progress_var.set(progress)
            status_var.set(f"Download in Progress for {config_file_name} config pack... {progress:.2f}%")
            root.update_idletasks()  # Force GUI update

        while True:
            attempt += 1

            # Construct the curl command
            curl_command = ['curl', '-k', '-C', '-', '-o', file_path, download_url]

            try:
                subprocess.run(curl_command, check=True)

                current_size = 0
                while True:
                    data = process.stdout.read(block_size)
                    if not data:
                        break
                    with open(file_path, 'ab') as file:
                        file.write(data)
                        current_size += len(data)
                        root.after(50, update_gui)  # Schedule the GUI update every 50 milliseconds

                process.stdout.close()
                process.stderr.close()
                process.wait()

                # If download is successful, break out of the retry loop
                break

            except subprocess.CalledProcessError as e:
                print(f"Attempt {attempt}/{max_attempts} failed: {e}")
                if attempt == max_attempts:
                    status_var.set(f"Download failed after {max_attempts} attempts. Exiting...")
                    root.after(2000, clear_status)
                    return None

                status_var.set(f"Retrying download ({attempt}/{max_attempts})...")

    except KeyError:
        print(f"Error: Key not found for '{selected_config_pack}' in config_pack_names. Available keys: {list(config_pack_names.keys())}")
        return None


            # Check MD5 hash
    if not check_md5(download_path, md5_checksums.get(config_file_name, "")):
        status_var.set(f"MD5 verification failed for {config_file_name}. Exiting...")
        root.after(2000, clear_status)
        return None

    for attempt in range(1, max_retries + 1):
            with open(os.path.join(target_directory, config_file_name), 'ab') as file:
                headers = {'Range': 'bytes=%d-' % file.tell()} if attempt > 1 else {}
                response = requests.get(download_url, stream=True, headers=headers, timeout=10)
                file_size = int(response.headers.get('content-length', 0))
                block_size = 1024  # 1 KB
                current_size = 0

                try:
                    response.raise_for_status()
                    file_size = int(response.headers.get('content-length', 0))

                    for data in tqdm(response.iter_content(block_size), total=max(1, file_size // block_size), unit='KB', unit_scale=True):
                        if download_canceled:
                            status_var.set(f"Download of {config_file_name} config pack canceled.")
                            root.after(2000, cleanup_temp_files, target_directory, os.path.join(target_directory, config_file_name))
                            return None
                    file.write(data)
                    progress_var.set((file.tell() / max(1, file_size)) * 100)
                    status_var.set(f"Download in Progress for {config_file_name} config pack... {progress_var.get():.2f}%")
                    root.update_idletasks()

                    # If download is successful, break out of the retry loop
                    break

                except requests.exceptions.RequestException as e:
                    print(f"Attempt {attempt}/{max_attempts} failed: {e}")
                    if attempt == max_attempts:
                        status_var.set(f"Download failed after {max_attempts} attempts. Exiting...")
                        root.after(2000, clear_status)
                        return None
                    status_var.set(f"Retrying download ({attempt}/{max_attempts})...")



    # Check if the selected config pack requires a password
    if selected_config_pack in md5_checksums:
        # Use the global password for all password-protected config packs
        password = global_password
        if not password:
            # Prompt the user for the password if global_password is not set
            password = simpledialog.askstring("Password", f"Enter the password for {selected_config_pack}:", show='*')
        if not password:
            # If the user cancels the password prompt, cancel the download
            status_var.set("Download canceled. Password not provided.")
            root.after(2000, clear_status)
            return None

        # Fetch the content of the .md5 file from the server
        md5_response = requests.get(md5_file_url)
        if md5_response.status_code == 200:
            

            actual_md5_line = md5_response.text.strip().split('\n')[0]  # Get the first line
            actual_md5 = actual_md5_line.split()[0]  # Extract only the hash
            print(f"Actual MD5 from .md5 file: {actual_md5}")

            expected_md5 = md5_checksums.get(md5_file_name, "")
            print(f"Expected MD5: {expected_md5}")

        # Check if the MD5 values match
        if expected_md5 == actual_md5:
            print("MD5 values match. Proceeding with the download.")
            status_var.set(f"MD5 values match for {md5_file_name}. Download starting...")
        else:
            print("MD5 values do not match. Exiting...")
            status_var.set(f"MD5 values do not match for {md5_file_name}. Exiting...")
            root.after(2000, clear_status)
            return None
    else:
        print(f"Error: Failed to fetch .md5 file from {md5_file_url}. Exiting...")
        status_var.set(f"Error: Failed to fetch .md5 file from {md5_file_url}. Exiting...")
        root.after(2000, clear_status)
        return None


    status_var.set("Extraction in progress...")

    # Modify the extraction command based on the tool you are using
    extraction_command = [r'C:\Program Files\7-Zip\7z.exe', 'x', '-aoa', '-o{}'.format(target_directory), '-p{}'.format(global_password), os.path.join(target_directory, config_file_name)]

    # Check if the extraction is successful
    if subprocess.run(extraction_command).returncode == 0:
        target_directory_network = r"\\RECALBOX\share"
        shutil.copytree(target_directory, target_directory_network, dirs_exist_ok=True)
        status_var.set(f"{selected_config_pack} config pack copied to {target_directory_network}")
        status_var.set("Download and copy completed.")
        status_var.set("Deleting temporary files and folders...")
        root.after(2000, cleanup_temp_files, target_directory, os.path.join(target_directory, config_file_name))
    else:
        status_var.set("Extraction failed. Temporary files are not deleted.")
        root.after(2000, cleanup_temp_files, target_directory, os.path.join(target_directory, config_file_name))

    return target_directory

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

    status_var.set("Temporary file deleted.")
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

# ... (previous code)

def download_thread():
    global download_canceled
    selected_config_pack = config_pack_combobox.get()

    if selected_config_pack:
        target_directory = os.path.expandvars(r"%APPDATA%\readycade\configpacks")
        config_file_name = config_pack_names[selected_config_pack]

        # Path to the downloaded config pack file
        downloaded_config_path = os.path.join(target_directory, config_file_name)

        # URL for the MD5 file on the website
        md5_file_url = base_url + config_file_name + '.md5'

        try:
            # Fetch the content of the .md5 file from the server
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
                root.after(2000, clear_status)
                root.after(2000, reset_download_button_text)  # Reset the Download button text
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching .md5 file from {md5_file_url}: {e}")
            status_var.set(f"Error fetching .md5 file from {md5_file_url}. Exiting...")
            root.after(2000, clear_status)
            root.after(2000, reset_download_button_text)  # Reset the Download button text
            return None

        # Continue with the rest of the download process
        console_folder = download_config_pack(base_url, target_directory, selected_config_pack, md5_checksums, status_var, progress_var)

        if console_folder:
            browse_text.set("Download")
            messagebox.showinfo("Config Pack Installed", "Config Pack Installed! Please Select Another or Exit the application.")
            root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)
        else:
            browse_text.set("Download failed.")
            root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)
            root.after(2000, reset_download_button_text)  # Reset the Download button text
    else:
        browse_text.set("Download failed.")
        root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)
        root.after(2000, reset_download_button_text)  # Reset the Download button text

def reset_download_button_text():
    browse_text.set("Download")


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
root.title("Readycade")

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
    "readycade_configs.7z": "d3f90351e3321ee45a36d8c87e4cb7f",
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

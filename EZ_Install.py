import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import requests
import hashlib
import subprocess
import shutil
import sys
import threading
import time
from tqdm import tqdm  # Import tqdm for the progress bar

# VARS
base_url = "https://forum.readycade.com/readycade_configs/"
auth_url = "https://forum.readycade.com/auth.php"

# Global variable to track whether the download should be canceled
download_canceled = False

global_password = "o2M8K2zjs67ysJR8jWy7"

def download_config_pack(base_url, target_directory, selected_config_pack, md5_checksums, status_var, progress_var):
    try:
        config_file_name = config_pack_names[selected_config_pack]
    except KeyError:
        print(f"Error: Key not found for '{selected_config_pack}' in config_pack_names. Available keys: {list(config_pack_names.keys())}")
        return None

    print(f"Selected config pack: {selected_config_pack}")
    print(f"Config file name: {config_file_name}")

    md5_file_url = base_url + config_file_name + '.md5'

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
        actual_md5 = md5_response.text.strip().split()[0]  # Extract only the hash
        print(f"Actual MD5 from .md5 file: {actual_md5}")

        expected_md5 = md5_checksums.get(config_file_name, "")
        print(f"Expected MD5: {expected_md5}")

        # Check if the MD5 values match
        if expected_md5 == actual_md5:
            print("MD5 values match. Proceeding with the download.")
            status_var.set(f"MD5 values match for {config_file_name}. Download starting...")
        else:
            print("MD5 values do not match. Exiting...")
            status_var.set(f"MD5 values do not match for {config_file_name}. Exiting...")
            root.after(2000, clear_status)
            return None
    else:
        print(f"Error: Failed to fetch .md5 file from {md5_file_url}. Exiting...")
        status_var.set(f"Error: Failed to fetch .md5 file from {md5_file_url}. Exiting...")
        root.after(2000, clear_status)
        return None

    # Define download_url before using it
    download_url = base_url + config_file_name

    response = requests.get(download_url, stream=True)
    file_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 KB
    current_size = 0

    file_path = os.path.join(target_directory, config_file_name)
    partially_downloaded_file = os.path.join(target_directory, f"{config_file_name}-configs.7z")

    with open(file_path, 'wb') as file:
        for data in tqdm(response.iter_content(block_size), total=max(1, file_size // block_size), unit='KB', unit_scale=True):
            if download_canceled:
                # User canceled the download, break out of the loop
                status_var.set(f"Download of {config_file_name} config pack canceled.")
                root.after(2000, cleanup_temp_files, target_directory, file_path, partially_downloaded_file)
                return None

            file.write(data)
            current_size += len(data)
            progress = (current_size / max(1, file_size)) * 100  # Ensure file_size is at least 1 to avoid division by zero
            progress_var.set(progress)
            status_var.set(f"Download in Progress for {config_file_name} config pack... {progress:.2f}%")
            root.update_idletasks()  # Force GUI update

    status_var.set("Extraction in progress...")

    # Modify the extraction command based on the tool you are using
    extraction_command = [r'C:\Program Files\7-Zip\7z.exe', 'x', '-aoa', '-o{}'.format(target_directory), '-p{}'.format(global_password), file_path]

    # Check if the extraction is successful
    if subprocess.run(extraction_command).returncode == 0:
        target_directory_network = r"\\RECALBOX\share"
        shutil.copytree(target_directory, target_directory_network, dirs_exist_ok=True)
        status_var.set(f"{selected_config_pack} config pack copied to {target_directory_network}")
        status_var.set("Download and copy completed.")
        status_var.set("Deleting temporary files and folders...")
        root.after(2000, cleanup_temp_files, target_directory, file_path, partially_downloaded_file)
    else:
        status_var.set("Extraction failed. Temporary files are not deleted.")
        root.after(2000, cleanup_temp_files, target_directory, file_path, partially_downloaded_file)

    return target_directory

def cleanup_temp_files(target_directory, file_path, partially_downloaded_file):
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

    # Check if the partially downloaded file exists and is not in use
    if os.path.exists(partially_downloaded_file):
        try:
            os.remove(partially_downloaded_file)
        except PermissionError:
            # File is still in use, wait and try again
            time.sleep(1)
            try:
                os.remove(partially_downloaded_file)
            except Exception as e:
                print(f"Error deleting file: {e}")

    status_var.set("Temporary files deleted.")
    root.after(2000, clear_status)

def clear_status():
    status_var.set("")  # Clear the status after 2000 milliseconds (2 seconds)
    progress_var.set(0)  # Reset the progress bar

def calculate_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5.update(chunk)
    return md5.hexdigest()

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
        console_folder = download_config_pack(base_url, target_directory, selected_config_pack, md5_checksums, status_var, progress_var)

        if console_folder:
            browse_text.set("Download")
            messagebox.showinfo("Config Pack Installed", "Config Pack Installed! Please Select Another or Exit the application.")
            root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)
        else:
            browse_text.set("Download failed.")
            root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)
    else:
        browse_text.set("Download failed.")
        root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)

def cancel_download():
    global download_canceled
    download_canceled = True

    # Clean up downloaded files and folders
    selected_config_pack = config_pack_combobox.get()
    target_directory = os.path.expandvars(r"%APPDATA%\readycade\configpacks")
    file_path = os.path.join(target_directory, config_pack_names[selected_config_pack])
    partially_downloaded_file = os.path.join(target_directory, f"{config_pack_names[selected_config_pack]}.7z")

    # Attempt to delete the downloaded file, the partially downloaded file
    try:
        if os.path.exists(file_path):
            os.remove(file_path)

        if os.path.exists(partially_downloaded_file):
            os.remove(partially_downloaded_file)

        status_var.set("Download canceled. Temporary files deleted.")
        root.after(2000, clear_status)
    except Exception as e:
        status_var.set(f"Error: {str(e)}")
        root.after(2000, clear_status)

    # Re-enable the download button
    browse_btn['state'] = 'normal'

    # Disable the cancel button
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

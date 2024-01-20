import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import requests
import hashlib
import subprocess
import shutil
import threading
from tqdm import tqdm  # Import tqdm for progress bar

def download_media_pack(base_url, target_directory, selected_media_pack, md5_checksums, status_var, progress_var):
    console_name = os.path.splitext(selected_media_pack)[0].replace('-media', '')
    console_folder = os.path.join(target_directory, console_name)
    os.makedirs(console_folder, exist_ok=True)

    download_url = base_url + selected_media_pack
    file_path = os.path.join(target_directory, selected_media_pack)

    response = requests.get(download_url, stream=True)
    file_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 KB
    current_size = 0

    with open(file_path, 'wb') as file:
        for data in tqdm(response.iter_content(block_size), total=file_size // block_size, unit='KB', unit_scale=True):
            file.write(data)
            current_size += len(data)
            progress = (current_size / file_size) * 100
            progress_var.set(progress)
            status_var.set(f"Installation in Progress... {progress:.2f}%")
            root.update_idletasks()  # Force GUI update

    actual_md5 = calculate_md5(file_path)

    expected_md5 = md5_checksums.get(selected_media_pack, "")
    if expected_md5 == actual_md5:
        status_var.set("Checksum verification successful.")
    else:
        status_var.set("Checksum verification failed. Exiting...")
        return None

    status_var.set("Extraction in progress...")

    if subprocess.run([r'C:\Program Files\7-Zip\7z.exe', 'x', f'-o{console_folder}', file_path]).returncode == 0:
        target_directory_network = r"\\RECALBOX\share\roms\{}".format(console_name)
        shutil.copytree(os.path.join(target_directory, console_folder), target_directory_network, dirs_exist_ok=True)
        status_var.set(f"{selected_media_pack} media pack copied to {target_directory_network}")
        status_var.set("Download and copy completed.")
        status_var.set("Deleting temporary files and folders...")
        root.after(2000, cleanup_temp_files, target_directory, console_folder, file_path)
    else:
        status_var.set("Extraction failed. Temporary files are not deleted.")

    return console_folder

def cleanup_temp_files(target_directory, console_folder, file_path):
    shutil.rmtree(os.path.join(target_directory, console_folder), ignore_errors=True)
    os.remove(file_path)
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
    browse_text.set("Downloading...")
    download_thread_instance = threading.Thread(target=download_thread)
    download_thread_instance.start()

def download_thread():
    selected_media_pack = media_pack_combobox.get()

    if selected_media_pack:
        base_url = "https://forum.readycade.com/readycade_media/"
        target_directory = os.path.expandvars(r"%APPDATA%\readycade\mediapacks")
        console_folder = download_media_pack(base_url, target_directory, selected_media_pack, md5_checksums, status_var, progress_var)
        if console_folder:
            browse_text.set("Download")
            messagebox.showinfo("Media Pack Installed", "Media Pack Installed! Please Select Another or Exit the application.")
        else:
            browse_text.set("Download failed.")

root = tk.Tk()
root.title("Readycade")

# Logo
logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
logo = Image.open(logo_path)
logo = ImageTk.PhotoImage(logo)
logo_label = tk.Label(image=logo)
logo_label.image = logo
logo_label.grid(column=1, row=0)

# Instructions
Instructions = tk.Label(root, text="Select a media pack to download:", font="open-sans")
Instructions.grid(columnspan=3, column=0, row=1)

# Media pack selection dropdown
media_packs = ["64dd-media.7z", "amiga600-media.7z", "amiga1200-media.7z", "amstradcpc-media.7z"]
md5_checksums = {
    "64dd-media.7z": "a2e36d62227447a9217b4a2b2c6bdef2",
    "amiga600-media.7z": "864c64b15e80ee992bf011894b5e5980",
    "amiga1200-media.7z": "35444479df16c4bad8476ce5e5fd2e76",
    "amstradcpc-media.7z": "211e304e1396e99c487f566ff5acd4ee"
}

media_pack_combobox = ttk.Combobox(root, values=media_packs)
media_pack_combobox.grid(column=1, row=2)
media_pack_combobox.set("Select a media pack")

# Browse Button
browse_text = tk.StringVar()
browse_btn = tk.Button(root, textvariable=browse_text, command=open_file, font="open-sans", bg="#ff6600", fg="white", height=2, width=15)
browse_text.set("Download")
browse_btn.grid(column=1, row=3)

# Progress bar
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, length=200, mode='determinate')
progress_bar.grid(column=1, row=4)

# Status Label
status_var = tk.StringVar()
status_label = tk.Label(root, textvariable=status_var, font="open-sans")
status_label.grid(columnspan=3, column=0, row=5)

root.mainloop()

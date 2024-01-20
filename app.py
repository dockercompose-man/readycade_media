import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import requests
import hashlib
import subprocess
import shutil
import time
import threading

def download_media_pack(base_url, target_directory, selected_media_pack, md5_checksums):
    console_name = os.path.splitext(selected_media_pack)[0].replace('-media', '')
    console_folder = os.path.join(target_directory, console_name)
    os.makedirs(console_folder, exist_ok=True)

    download_url = base_url + selected_media_pack
    file_path = os.path.join(target_directory, selected_media_pack)

    max_attempts = 4
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        print(f"Attempt {attempt} to download {selected_media_pack}...")

        response = requests.get(download_url, stream=True)
        with open(file_path, 'wb') as file:
            file.write(response.content)

        if response.status_code == 200:
            print(f"Download of {selected_media_pack} was successful.")
            break
        else:
            print(f"Download of {selected_media_pack} failed on attempt {attempt}.")
            if attempt < max_attempts:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print("Maximum download attempts reached. Download failed.")
                return None

    # Calculate the MD5 of the downloaded file
    actual_md5 = calculate_md5(file_path)

    # Check if MD5 matches the expected value
    expected_md5 = md5_checksums.get(selected_media_pack, "")
    if expected_md5 == actual_md5:
        print("Checksum verification successful.")
    else:
        print("Checksum verification failed. Exiting...")
        return None

    # Extract the media pack using 7z
    print(f"Extracting archive: {file_path}")
    if subprocess.run([r'C:\Program Files\7-Zip\7z.exe', 'x', f'-o{console_folder}', file_path]).returncode == 0:
        # Determine the target directory on the network share
        target_directory_network = r"\\RECALBOX\share\roms\{}".format(console_name)

        # Copy the extracted folder and its contents to the network share
        shutil.copytree(os.path.join(target_directory, console_folder), target_directory_network, dirs_exist_ok=True)

        print(f"{selected_media_pack} media pack copied to {target_directory_network}")
        print("Download and copy completed.")

        # CLEAN UP TEMP FILES
        print("Deleting temporary files and folders...")
        shutil.rmtree(os.path.join(target_directory, console_folder), ignore_errors=True)
        os.remove(file_path)
    else:
        print("Extraction failed. Temporary files are not deleted.")

    return console_folder

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
        console_folder = download_media_pack(base_url, target_directory, selected_media_pack, md5_checksums)
        if console_folder:
            browse_text.set("Download")
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

root.mainloop()

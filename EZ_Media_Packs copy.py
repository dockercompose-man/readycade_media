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
from tqdm import tqdm  # Import tqdm for progress bar

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

global_password = "EvCoaxxbEZpZ6CBMBvxj"

def download_media_pack(base_url, target_directory, selected_media_pack, md5_checksums, status_var, progress_var):
    console_name = os.path.splitext(selected_media_pack)[0].replace('-media', '')
    console_folder = os.path.join(target_directory, console_name)
    os.makedirs(console_folder, exist_ok=True)

    download_url = base_url + selected_media_pack
    file_path = os.path.join(target_directory, selected_media_pack)
    partially_downloaded_file = os.path.join(target_directory, f"{console_name}-media.7z")

    # Check if the selected media pack requires a password
    if selected_media_pack in md5_checksums:
        # Use the global password for all password-protected media packs
        password = global_password
        if not password:
            # Prompt the user for the password if global_password is not set
            password = simpledialog.askstring("Password", f"Enter the password for {selected_media_pack}:", show='*')
        if not password:
            # If the user cancels the password prompt, cancel the download
            status_var.set("Download canceled. Password not provided.")
            root.after(2000, clear_status)
            cleanup_temp_files(target_directory, console_folder, file_path, partially_downloaded_file)
            return None

    response = requests.get(download_url, stream=True)
    file_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 KB
    current_size = 0

    with open(file_path, 'wb') as file:
        for data in tqdm(response.iter_content(block_size), total=file_size // block_size, unit='KB', unit_scale=True):
            if download_canceled:
                # User canceled the download, break out of the loop
                status_var.set(f"Download of {console_name} media pack canceled.")
                root.after(2000, cleanup_temp_files, target_directory, console_folder, file_path, partially_downloaded_file)
                return None

            file.write(data)
            current_size += len(data)
            progress = (current_size / file_size) * 100
            progress_var.set(progress)
            status_var.set(f"Installation in Progress for {console_name} media pack... {progress:.2f}%")
            root.update_idletasks()  # Force GUI update

    actual_md5 = calculate_md5(file_path)
    print(f"Actual MD5: {actual_md5}")

    expected_md5 = md5_checksums.get(selected_media_pack, "")
    print(f"Expected MD5: {expected_md5}")

    if expected_md5 == actual_md5:
        status_var.set("Checksum verification successful.")
    else:
        status_var.set(f"Checksum verification failed. Expected: {expected_md5}, Actual: {actual_md5}. Exiting...")
        root.after(2000, cleanup_temp_files, target_directory, console_folder, file_path, partially_downloaded_file)
        return None

    status_var.set("Extraction in progress...")

    # Modify the extraction command based on the tool you are using
    extraction_command = [r'C:\Program Files\7-Zip\7z.exe', 'x', '-aoa', f'-o{console_folder}', '-p{}'.format(global_password), file_path]

    # Check if the extraction is successful
    if subprocess.run(extraction_command).returncode == 0:
        target_directory_network = r"\\RECALBOX\share\roms\{}".format(console_name)
        shutil.copytree(console_folder, target_directory_network, dirs_exist_ok=True)
        status_var.set(f"{selected_media_pack} media pack copied to {target_directory_network}")
        status_var.set("Download and copy completed.")
        status_var.set("Deleting temporary files and folders...")
        root.after(2000, cleanup_temp_files, target_directory, console_folder, file_path, partially_downloaded_file)
    else:
        status_var.set("Extraction failed. Temporary files are not deleted.")
        root.after(2000, cleanup_temp_files, target_directory, console_folder, file_path, partially_downloaded_file)

    return console_folder


def cleanup_temp_files(target_directory, console_folder, file_path, partially_downloaded_file):
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

    # Check if the folder exists and is not in use
    if os.path.exists(os.path.join(target_directory, console_folder)):
        try:
            shutil.rmtree(os.path.join(target_directory, console_folder), ignore_errors=True)
        except Exception as e:
            print(f"Error deleting folder: {e}")

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
    global download_canceled
    selected_media_pack = media_pack_combobox.get()

    if selected_media_pack:
        base_url = "https://forum.readycade.com/readycade_media/"
        target_directory = os.path.expandvars(r"%APPDATA%\readycade\mediapacks")
        console_folder = download_media_pack(base_url, target_directory, selected_media_pack, md5_checksums, status_var, progress_var)

        if console_folder:
            browse_text.set("Download")
            messagebox.showinfo("Media Pack Installed", "Media Pack Installed! Please Select Another or Exit the application.")
            root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)
        else:
            browse_text.set("Download failed.")
            root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)
    else:
        browse_text.set("Download failed.")
        root.after(1000, clear_status)  # Schedule clearing status after 1000 milliseconds (1 second)


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

def cancel_download():
    global download_canceled
    download_canceled = True

    # Clean up downloaded files and folders
    selected_media_pack = media_pack_combobox.get()
    console_name = os.path.splitext(selected_media_pack)[0].replace('-media', '')
    target_directory = os.path.expandvars(r"%APPDATA%\readycade\mediapacks")
    file_path = os.path.join(target_directory, selected_media_pack)
    console_folder = os.path.join(target_directory, console_name)
    partially_downloaded_file = os.path.join(target_directory, f"{console_name}-media.7z")

    # Attempt to delete the downloaded file, the extracted folder, and the partially downloaded file
    try:
        if os.path.exists(file_path):
            os.remove(file_path)

        if os.path.exists(console_folder):
            shutil.rmtree(console_folder, ignore_errors=True)

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



def clear_status():
    status_var.set("")  # Clear the status after 1000 milliseconds (1 second)
    progress_var.set(0)  # Reset the progress bar


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
Instructions = tk.Label(root, text="Select a media pack to download:", font="open-sans")
Instructions.grid(columnspan=3, column=0, row=1)

# Media pack selection dropdown
media_packs = [
    "64dd-media.7z",
    "amiga600-media.7z",
    "amiga1200-media.7z",
    "amstradcpc-media.7z",
    "apple2-media.7z",
    "apple2gs-media.7z",
    "arduboy-media.7z",
    "atari800-media.7z",
    "atari2600-media.7z",
    "atari5200-media.7z",
    "atari7800-media.7z",
    "atarist-media.7z",
    "atomiswave-media.7z",
    "bbcmicro-media.7z",
    "bk-media.7z",
    "c64-media.7z",
    "channelf-media.7z",
    "colecovision-media.7z",
    "daphne-media.7z",
    "dos-media.7z",
    "fds-media.7z",
    "gamegear-media.7z",
    "gba-media.7z",
    "gbc-media.7z",
    "gb-media.7z",
    "gbw-media.7z",
    "gx4000-media.7z",
    "intellivision-media.7z",
    "jaguar-media.7z",
    "lowresnx-media.7z",
    "lutro-media.7z",
    "mastersystem-media.7z",
    "megadrive-media.7z",
    "model3-media.7z",
    "msx1-media.7z",
    "msx2-media.7z",
    "msxturbor-media.7z",
    "multivision-media.7z",
    "n64-media.7z",
    "naomigd-media.7z",
    "naomi-media.7z",
    "neogeocd-media.7z",
    "neogeo-media.7z",
    "nes-media.7z",
    "ngpc-media.7z",
    "ngp-media.7z",
    "o2em-media.7z",
    "oricatmos-media.7z",
    "pcengine-media.7z",
    "pcenginecd-media.7z",
    "pcfx-media.7z",
    "pcv2-media.7z",
    "pokemini-media.7z",
    "ports-media.7z",
    "samcoupe-media.7z",
    "satellaview-media.7z",
    "scv-media.7z",
    "sega32x-media.7z",
    "sg1000-media.7z",
    "snes-media.7z",
    "solarus-media.7z",
    "spectravideo-media.7z",
    "sufami-media.7z",
    "supergrafx-media.7z",
    "supervision-media.7z",
    "thomson-media.7z",
    "tic80-media.7z",
    "trs80coco-media.7z",
    "uzebox-media.7z",
    "vectrex-media.7z",
    "vic20-media.7z",
    "videopacplus-media.7z",
    "virtualboy-media.7z",
    "wasm4-media.7z",
    "wswanc-media.7z",
    "wswan-media.7z",
    "x1-media.7z",
    "x68000-media.7z",
    "zx81-media.7z",
    "zxspectrum-media.7z"
]

md5_checksums = {
    "64dd-media.7z": "6d5573472237d323aeaf3e4fa609883e",
    "amiga600-media.7z": "864c64b15e80ee992bf011894b5e5980",
    "amiga1200-media.7z": "35444479df16c4bad8476ce5e5fd2e76",
    "amstradcpc-media.7z": "211e304e1396e99c487f566ff5acd4ee",
    "apple2gs-media.7z": "74e8e5669f2923e4bcbdac2753cd3434",
    "apple2-media.7z": "eb831f572b4e10c99357eb5a089fb09e",
    "arduboy-media.7z": "2ca7fe373cadf5fa8dc6311ffe2d0bf2",
    "atari800-media.7z": "50aa147f426464580bd9fb003f408ade",
    "atari2600-media.7z": "fa453d942a8b94e88e520443ed67b08b",
    "atari5200-media.7z": "b80a40f28375415977fa0a0fe1e79d3a",
    "atari7800-media.7z": "166ae4335e4d8a4c26660b32c8b8235e",
    "atarist-media.7z": "be3e23d1417aac6198f7f1b9b90f318e",
    "atomiswave-media.7z": "5cdfe5e3efb05accc30c9d36726ca454",
    "bbcmicro-media.7z": "294dc037877a08d5bb781f6ab3822070",
    "bk-media.7z": "7302244a58842e2548eff3a3d9e53fab",
    "c64-media.7z": "ad8ac05290a3b94df8f047d9904ff16e",
    "channelf-media.7z": "ef1613ee3fe43b40ea481d40b0c06e68",
    "colecovision-media.7z": "5409c95725191751c1c8912f0765816d",
    "daphne-media.7z": "a515e01e9f1b756bb813f9be023786a7",
    "dos-media.7z": "1b9c50565666b71277e325675a95d99e",
    "fds-media.7z": "cca31f6c53186afe9940640252b58820",
    "gamegear-media.7z": "f8507f38545df1dca632ee9edf680ce1",
    "gba-media.7z": "02d9c5cedb63a44e8ba5a68d45292961",
    "gbc-media.7z": "4591390a77ba3203bad17da641809eea",
    "gb-media.7z": "8f12081ee4b74e7973b3d461086c32b8",
    "gw-media.7z": "50e7395253d9276c94d39df57b8ab249",
    "gx4000-media.7z": "db97c08c5670ebe0b6915bc357954dd7",
    "intellivision-media.7z": "b29a85e56917bf24ddc167182d3f5bc3",
    "jaguar-media.7z": "0788dc617baa475fb57323aa4a1d44d8",
    "lowresnx-media.7z": "41d147eb86660756145ea6ee87a27c3d",
    "lutro-media.7z": "69cb7245a230ccdbe80421bdb13f09ef",
    "mastersystem-media.7z": "21d6cb6a4225e615dfa0da6785046b75",
    "megadrive-media.7z": "05468e87ec889a28a68a67babc26532a",
    "model3-media.7z": "d30a63408a27b165ab70c70df01c9a1d",
    "msx1-media.7z": "01a11257ad67bdbca73f7ccae1087d0d",
    "msx2-media.7z": "21448c7315a44892e670914644397812",
    "msxturbor-media.7z": "f34fddcf7fa097795482ee2678349d78",
    "multivision-media.7z": "6acd96d673b1efad6e868516c3a053fb",
    "n64-media.7z": "4dc383561d084f99ee8cd27642d7a6ba",
    "naomigd-media.7z": "2768016cedca059c408a360775526d75",
    "naomi-media.7z": "29e5705b7cb55a4335163f319f5f9053",
    "neogeocd-media.7z": "489f65bafcc76720e126b8ddaa79fdc9",
    "neogeo-media.7z": "a3675db62149016f45840481c8b4654e",
    "nes-media.7z": "0983d81b024187b0c3f9cbcf8e0d62ef",
    "ngpc-media.7z": "adcae5943a396093a5386c847c527145",
    "ngp-media.7z": "07e94103b433777cb80b2b26ce2cd32c",
    "o2em-media.7z": "3c794679c66e54088bfa30d016580078",
    "oricatmos-media.7z": "c7609eb24a1ab1ef4061390fbdc7dbaf",
    "pcengine-media.7z": "557e7c8d678db5306049a9f77db7505b",
    "pcenginecd-media.7z": "d48c2cda02f34882214746bd2a520258",
    "pcfx-media.7z": "e68086f8439bf3b19c0ea22c925a535e",
    "pcv2-media.7z": "4748db2648ffc134f2775d3c6a0bbea8",
    "pokemini-media.7z": "8b2eb047b5f9d9bc991c260a7f53aec4",
    "ports-media.7z": "b388c84f0c7d9cb5e529c758bc8d5dcd",
    "samcoupe-media.7z": "b9b873d2178987f139a3284e66de458f",
    "satellaview-media.7z": "75fbba3c1a16f26ee8c22b0d4a5db363",
    "scv-media.7z": "b32ba0f51cba58b1505d10f4e085db63",
    "sega32x-media.7z": "3d06ba89a1fc1301b00b2aae14178975",
    "sg1000-media.7z": "29968ebb163796abf635667a69c606bf",
    "snes-media.7z": "a49c05f6601f6d74901c77afa228bc87",
    "solarus-media.7z": "ef72a08ce0ce14cf47e8a907a1fe6a0f",
    "spectravideo-media.7z": "7daef6d8807811b5f2ae482ec227e1c0",
    "sufami-media.7z": "4df212b924b467b30812348f01a4b71b",
    "supergrafx-media.7z": "466b87c835852d0545905d89f2b7d922",
    "supervision-media.7z": "9961c3dcad91387b39ea6909e4658010",
    "thomson-media.7z": "2054a9d8c102926364056af4de3414d2",
    "tic80-media.7z": "089a5e636561d3683760e606cd22c512",
    "trs80coco-media.7z": "f658209dd1fc8b1976f2033317eabf07",
    "uzebox-media.7z": "24f987cd885297b5591b936e7475bf2a",
    "vectrex-media.7z": "86b466983295c90a69da59eb415b5867",
    "vic20-media.7z": "03dce302b66f04343b9e7819a1ded8b4",
    "videopacplus-media.7z": "9662df65f41d8fac6f246f38dfe49db7",
    "virtualboy-media.7z": "1605f05f73cb142715ee25dbe504773f",
    "wasm4-media.7z": "3543bee3bc2bc692044b29560333ca31",
    "wswanc-media.7z": "5c317009d4cdda494bd67ee68a5a9014",
    "wswan-media.7z": "6f18cc6a4cec027e8a0908e0e25d45a1",
    "x1-media.7z": "0fc04dc8aa141bd4d70b25b4dfc83030",
    "x68000-media.7z": "6ebf2a0fdc1be37f74bfce03067326d5",
    "zx81-media.7z": "c4f23cc445c898de892ed2782d15677c",
    "zxspectrum-media.7z": "e89800571eb212fa297260c691d4651d"     
}

media_pack_combobox = ttk.Combobox(root, values=media_packs)
media_pack_combobox.grid(column=1, row=2)
media_pack_combobox.set("Select a media pack")

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

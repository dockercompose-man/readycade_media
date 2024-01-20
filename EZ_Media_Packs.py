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

global_password = "uXR9mtjKxtHHGuQ7qUL6"

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
    "pcenginecd-media.7z",
    "pcengine-media.7z",
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
    "64dd-media.7z": "702633527841f5effa49552d15a75f06",
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

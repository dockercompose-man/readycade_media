import os
import tkinter as tk
from tkinter import messagebox
import requests
from io import BytesIO
from PIL import Image, ImageTk

class ReadycadeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Readycade")

        # Logo
        logo = Image.open('logo.png')
        logo = ImageTk.PhotoImage(logo)
        logo_label = tk.Label(root, image=logo)
        logo_label.image = logo
        logo_label.grid(column=1, row=0)

        # Instructions
        instructions = tk.Label(root, text="Select a file on your computer or a media pack to download and install", font=("open-sans", 12))
        instructions.grid(columnspan=3, column=0, row=1)

        # Media Pack Selection
        self.selected_media_pack = tk.StringVar()
        self.media_packs = [
            "64dd-media.7z", "amiga600-media.7z", "amiga1200-media.7z",  # Add all media packs
            # ... (add the rest of the media packs)
        ]

        media_pack_label = tk.Label(root, text="Select Media Pack:", font=("open-sans", 10))
        media_pack_label.grid(column=0, row=3)

        media_pack_menu = tk.OptionMenu(root, self.selected_media_pack, *self.media_packs)
        media_pack_menu.config(font=("open-sans", 10), bg="#ff6600", fg="white")
        media_pack_menu.grid(column=1, row=3)

        # Download Button
        download_btn = tk.Button(root, text="Download and Install", command=self.download_media_pack, font=("open-sans", 10),
                                 bg="#ff6600", fg="white", height=2, width=20)
        download_btn.grid(column=1, row=4)

    def open_file(self):
        browse_text = "loading..."
        file = tk.filedialog.askopenfile(parent=self.root, mode='rb', title="Choose a file", filetype=[("All Files", "*.*")])
        if file:
            # Do something with the selected file (you can customize this part)
            file_content = file.read()
            print(file_content)

    def download_media_pack(self):
        selected_media_pack = self.selected_media_pack.get()

        # Perform download and installation here
        # Example: response = requests.get(download_url)
        #          extracted_path = extract_archive(response.content)

        messagebox.showinfo("Download Complete", f"{selected_media_pack} downloaded and installed successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ReadycadeApp(root)
    root.mainloop()

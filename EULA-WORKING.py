import tkinter as tk
from tkinter import Scrollbar, Text, messagebox
from tkinter.filedialog import askopenfile
from PIL import Image, ImageTk
import pypdf

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


# Initialize Tkinter
root = tk.Tk()

# Hide the main window initially
root.withdraw()

# Show EULA before creating the main window
show_eula()

# Set the window title
root.title("Readycade")

# Remove the TK icon
root.iconbitmap(default="icon.ico")

# Logo
logo = Image.open('logo.png')
logo = ImageTk.PhotoImage(logo)
logo_label = tk.Label(image=logo)
logo_label.image = logo
logo_label.grid(column=1, row=0)

# Instructions
Instructions = tk.Label(root, text="Select a PDF file on your computer to extract all its text", font="open-sans")
Instructions.grid(columnspan=3, column=0, row=1)

# Browse Button
browse_text = tk.StringVar()
browse_btn = tk.Button(root, textvariable=browse_text, command=lambda: open_file(), font="open-sans", bg="#ff6600", fg="white", height=2, width=15)
browse_text.set("Browse")
browse_btn.grid(column=1, row=2)

canvas = tk.Canvas(root, width=600, height=250)
canvas.grid(columnspan=3)

# Remove the TK icon
root.iconbitmap(default="")

root.mainloop()

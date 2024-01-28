import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfile
from PIL import Image, ImageTk
import pypdf

def show_eula():
    eula_text = """
    End User License Agreement (EULA)

    This is a sample EULA text. Please replace it with your own EULA.

    1. You agree to use this software responsibly.
    2. You may not distribute or sell this software without permission.
    3. This software is provided "as is" without any warranty.

    Thank you for using Readycade!
    """
    return messagebox.askyesno("End User License Agreement", eula_text)

def open_file():
    browse_text.set("loading...")
    file = askopenfile(parent=root, mode='rb', title="Choose a file", filetype=[("PDF files", "*.pdf")])
    if file:
        read_pdf = pypdf.PdfReader(file)
        page = read_pdf._get_page(0)
        page_content = page.extract_text()
        print(page_content)

        # Text Box
        text_box = tk.Text(root, height=10, width=50, padx=15, pady=15)
        text_box.insert(1.0, page_content)
        text_box.tag_configure("center", justify="center")
        text_box.tag_add("center", 1.0, "end")
        text_box.grid(column=1, row=3)

        browse_text.set("Browse")

# Initialize Tkinter
root = tk.Tk()

# Hide the main window initially
root.withdraw()

# Show EULA before creating the main window
if show_eula():
    # Continue with the main window creation
    root.deiconify()

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
else:
    # Exit the application if the user didn't accept the EULA
    root.destroy()

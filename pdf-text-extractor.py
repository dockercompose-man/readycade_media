import tkinter as tk
import pypdf
from PIL import Image, ImageTk
from tkinter.filedialog import askopenfile

root = tk.Tk()

# set the window title
root.title("Readycade")

# Remove the TK icon
#root.iconbitmap(default="icon.ico")

# Logo
logo = Image.open('logo.png')
logo = ImageTk.PhotoImage(logo)
logo_label = tk.Label(image=logo)
logo_label.image = logo
logo_label.grid(column=1, row=0)

#Instructions
Instructions = tk.Label(root, text="Select a PDF file on your computer to extract all its text", font="open-sans")
Instructions.grid(columnspan=3, column=0, row=1)

#Functions

def open_file():
    browse_text.set("loading...")
    file = askopenfile(parent=root, mode='rb', title="Choose a file", filetype=[("PDF files", "*.pdf")])
    if file:
        read_pdf = pypdf.PdfReader(file)
        page = read_pdf._get_page(0)
        page_content = page.extract_text()
        print(page_content)

        #Text Box
        text_box = tk.Text(root,  height=10, width=50, padx=15, pady=15)
        text_box.insert(1.0, page_content)
        text_box.tag_configure("center", justify="center")
        text_box.tag_add("center", 1.0, "end")
        text_box.grid(column=1, row=3)

        browse_text.set("Browse")

# Browse Button
browse_text = tk.StringVar()
browse_btn = tk.Button(root, textvariable=browse_text, command=lambda:open_file(), font="open-sans", bg="#ff6600", fg="white", height=2, width=15)
browse_text.set("Browse")
browse_btn.grid(column=1, row=2)

canvas = tk.Canvas(root, width=600, height=250)
canvas.grid(columnspan=3)

# Remove the TK icon
root.iconbitmap(default="")

root.mainloop()

import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image, ImageTk

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

bg_image_path = resource_path("cinnamon_background.jpg")
icon_path = resource_path("cinnamon.ico")

# Appearance settings
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class PDFSplitterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Divisor de PDF Sanrio 💖")
        self.geometry("600x420")
        self.resizable(False, False)
        self.configure(bg="#ffffff")

        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
            self.wm_iconbitmap(icon_path)

        if not os.path.exists(bg_image_path):
            messagebox.showwarning("Advertencia", f"No se encontró la imagen de fondo: {bg_image_path}")
            self.bg_photo = None
        else:
            self.bg_image = Image.open(bg_image_path).resize((600, 400))
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)

            self.bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.container = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=15, bg_color="#ffffff", width=480,
                                      height=300)
        self.container.place(relx=0.5, rely=0.5, anchor="center")

        self.label = ctk.CTkLabel(self.container, text="Divide tu PDF por rango de páginas 📄", font=("Comic Sans MS", 18, "bold"), text_color="#a58ce3")
        self.label.pack(pady=(20, 10))

        self.select_button = ctk.CTkButton(self.container, text="Elegir PDF", command=self.select_pdf)
        self.select_button.pack(pady=5)

        self.selected_file_label = ctk.CTkLabel(self.container, text="", text_color="#8a8a8a", font=("Arial", 12))
        self.selected_file_label.pack(pady=(0, 5))

        self.page_from = ctk.CTkEntry(self.container, placeholder_text="Página de inicio (e.g., 1938)")
        self.page_from.pack(pady=5)

        self.page_to = ctk.CTkEntry(self.container, placeholder_text="Página final (e.g., 1946)")
        self.page_to.pack(pady=5)

        self.export_button = ctk.CTkButton(self.container, text="Exportar PDF ✨", command=self.export_pdf)
        self.export_button.pack(pady=10)

        self.open_button = ctk.CTkButton(self.container, text="Abrir PDF resultante 📂", command=self.open_pdf, state="disabled")
        self.open_button.pack(pady=5)

        self.history_button = ctk.CTkButton(self.container, text="Ver historial 🕘", command=self.show_history)
        self.history_button.pack(pady=5)

        self.pdf_path = None
        self.generated_pdf_path = None
        self.history = []  # Exported paths history

    def select_pdf(self):
        self.pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if self.pdf_path:
            filename = os.path.basename(self.pdf_path)
            self.selected_file_label.configure(text=f"📎 {filename}")
            messagebox.showinfo("PDF seleccionado", f"Loaded:\n{filename}")

    def export_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("No hay PDF", "Por favor, selecciona un PDF primero.")
            return

        try:
            start = int(self.page_from.get()) - 1
            end = int(self.page_to.get())
        except ValueError:
            messagebox.showerror("Entrada inválida", "Los números de página deben ser enteros.")
            return

        try:
            reader = PdfReader(self.pdf_path)
            writer = PdfWriter()

            if start < 0 or end > len(reader.pages) or start >= end:
                messagebox.showerror("Rango inválido", f"El rango debe ser entre 1 y {len(reader.pages)}.")
                return

            for i in range(start, end):
                writer.add_page(reader.pages[i])

            output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
            if output_path:
                with open(output_path, "wb") as f:
                    writer.write(f)
                self.generated_pdf_path = output_path
                self.open_button.configure(state="normal")
                self.history.append(output_path)
                messagebox.showinfo("Éxito", f"PDF guardado en:\n{output_path}")

                self.page_from.delete(0, "end")
                self.page_to.delete(0, "end")

                self.pdf_path = None
                self.selected_file_label.configure(text="")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")

    def open_pdf(self):
        if self.generated_pdf_path and os.path.exists(self.generated_pdf_path):
            try:
                os.startfile(self.generated_pdf_path)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{str(e)}")

    def show_history(self):
        if not self.history:
            messagebox.showinfo("Historial", "No hay archivos recientes aún.")
        else:
            history_str = "\n".join(self.history[-5:])
            messagebox.showinfo("Últimos archivos generados 🕘", history_str)

if __name__ == "__main__":
    app = PDFSplitterApp()
    app.mainloop()

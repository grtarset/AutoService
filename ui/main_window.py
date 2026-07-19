import customtkinter as ctk
from ui.invoice_page import InvoicePage

class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("AutoService")
        self.geometry("1300x800")

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.create_layout()
        self.current_page = None
        self.show_invoice_page()

    def clear_content(self):

        for widget in self.content_frame.winfo_children():
            widget.destroy()


    def show_invoice_page(self):

        self.clear_content()

        self.current_page = InvoicePage(self.content_frame)
        self.current_page.pack(fill="both", expand=True)

    def create_layout(self):

        # Ліве меню
        self.menu_frame = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0
        )

        self.menu_frame.pack(
            side="left",
            fill="y"
        )

        # Права частина
        self.content_frame = ctk.CTkFrame(self)

        self.content_frame.pack(
            side="right",
            fill="both",
            expand=True
        )

        title = ctk.CTkLabel(
            self.menu_frame,
            text="AUTOSERVICE",
            font=("Arial", 24, "bold")
        )

        title.pack(pady=30)

        self.create_menu()

    def create_menu(self):

        buttons = [
            "Нова накладна",
            "Клієнти",
            "Автомобілі",
            "Товари",
            "Налаштування"
        ]

        for text in buttons:

            if text == "Нова накладна":
                cmd = self.show_invoice_page
            else:
                cmd = lambda t=text: print(t)

            btn = ctk.CTkButton(
                self.menu_frame,
                text=text,
                height=40,
                command=cmd
            )

            btn.pack(
                fill="x",
                padx=15,
                pady=6
            )
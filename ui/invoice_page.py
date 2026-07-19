import customtkinter as ctk


class InvoicePage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.build()

    def build(self):

        title = ctk.CTkLabel(
            self,
            text="Створення накладної",
            font=("Arial", 24, "bold")
        )
        title.pack(anchor="w", padx=20, pady=(20, 10))

        vehicle_frame = ctk.CTkFrame(self)
        vehicle_frame.pack(fill="x", padx=20, pady=10)

        # ---------- Автомобіль ----------
        ctk.CTkLabel(vehicle_frame, text="Марка").grid(row=0, column=0, padx=10, pady=10)
        self.brand = ctk.CTkEntry(vehicle_frame, width=180)
        self.brand.grid(row=0, column=1)

        ctk.CTkLabel(vehicle_frame, text="Модель").grid(row=0, column=2, padx=10)
        self.model = ctk.CTkEntry(vehicle_frame, width=180)
        self.model.grid(row=0, column=3)

        ctk.CTkLabel(vehicle_frame, text="VIN").grid(row=1, column=0, padx=10)
        self.vin = ctk.CTkEntry(vehicle_frame, width=180)
        self.vin.grid(row=1, column=1)

        ctk.CTkLabel(vehicle_frame, text="Держ. номер").grid(row=1, column=2, padx=10)
        self.number = ctk.CTkEntry(vehicle_frame, width=180)
        self.number.grid(row=1, column=3)

        ctk.CTkLabel(vehicle_frame, text="Пробіг").grid(row=2, column=0, padx=10)
        self.mileage = ctk.CTkEntry(vehicle_frame, width=180)
        self.mileage.grid(row=2, column=1)

        # ---------- Таблиця ----------
        table = ctk.CTkFrame(self)
        table.pack(fill="both", expand=True, padx=20, pady=20)

        headers = [
            "Назва",
            "Тип",
            "Кількість",
            "Ціна",
            "Сума"
        ]

        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(
                table,
                text=h,
                font=("Arial", 14, "bold")
            )
            lbl.grid(row=0, column=i, padx=15, pady=10)

        self.rows = []

        add = ctk.CTkButton(
            self,
            text="+ Додати позицію",
            command=self.add_row
        )

        add.pack(anchor="w", padx=20)

        self.total_label = ctk.CTkLabel(
            self,
            text="Загальна сума: 0 грн",
            font=("Arial", 18, "bold")
        )

        self.total_label.pack(anchor="e", padx=20, pady=20)

    def add_row(self):

        row = len(self.rows) + 1

        frame = self.winfo_children()[2]

        name = ctk.CTkEntry(frame, width=250)
        name.grid(row=row, column=0, padx=5, pady=5)

        type_box = ctk.CTkComboBox(
            frame,
            values=["Товар", "Робота"],
            width=120
        )
        type_box.grid(row=row, column=1)

        qty = ctk.CTkEntry(frame, width=80)
        qty.insert(0, "1")
        qty.grid(row=row, column=2)

        price = ctk.CTkEntry(frame, width=120)
        price.insert(0, "0")
        price.grid(row=row, column=3)

        total = ctk.CTkLabel(frame, text="0")
        total.grid(row=row, column=4)

        self.rows.append({
            "qty": qty,
            "price": price,
            "total": total
        })

        qty.bind("<KeyRelease>", lambda e: self.calculate())
        price.bind("<KeyRelease>", lambda e: self.calculate())

    def calculate(self):

        grand = 0

        for row in self.rows:

            try:
                qty = float(row["qty"].get())
                price = float(row["price"].get())

                s = qty * price

            except:
                s = 0

            row["total"].configure(text=f"{s:.2f}")

            grand += s

        self.total_label.configure(
            text=f"Загальна сума: {grand:.2f} грн"
        )
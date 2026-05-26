import tkinter as tk
from tkinter import ttk


def build_ui(self):
    form = ttk.Frame(self.root)
    form.pack(fill="x", padx=10, pady=10)
    form.columnconfigure(1, weight=1)
    build_input_entries(self, form)

    buttons_frame = tk.Frame(self.root)
    buttons_frame.pack(anchor="center", pady=20)
    build_buttons(self, buttons_frame)

    log_frame = ttk.Frame(self.root)
    log_frame.pack(fill="both", expand=True, padx=10, pady=10)
    build_log(self, log_frame)


def build_buttons(self, buttons_frame):
    ttk.Checkbutton(buttons_frame,
                    text="Показывать полный лог ошибок",
                    variable=self.show_full_error).pack(side="left", padx=5)

    self.run_button = ttk.Button(buttons_frame, text="Запустить", command=self.run)
    self.run_button.pack(side="left", padx=5)

    ttk.Button(buttons_frame, text="Очистить лог", command=self.clear_log).pack(side="left", padx=5)

    ttk.Button(buttons_frame, text="Дополнительные настройки", command=self.open_settings).pack(side="left", padx=5)


def build_log(self, log_frame):
    self.log = tk.Text(log_frame)
    self.log.pack(side="left", fill="both", expand=True)

    scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
    scroll.pack(side="right", fill="y")

    self.log.config(yscrollcommand=scroll.set)


def build_input_entries(self, form):
    ttk.Label(form, text="PDF файл:").grid(row=0, column=0, sticky="w", pady=5)
    ttk.Entry(form, textvariable=self.pdf_path).grid(row=0, column=1, sticky="ew", pady=5, padx=10)
    ttk.Button(form, text="Выбрать файл", command=self.choose_pdf).grid(row=0, column=2, padx=5)

    ttk.Label(form, text="Этажи:").grid(row=1, column=0, sticky="w", pady=5)

    ttk.Entry(form, textvariable=self.floors).grid(row=1, column=1, sticky="ew", pady=5, padx=10)

    ttk.Button(form, text="Инструкция по вводу", command=self.show_floors_help).grid(row=1, column=2, padx=5)

    ttk.Label(form, text="Excel файл:").grid(row=2, column=0, sticky="w", pady=5)
    ttk.Entry(form, textvariable=self.output_path).grid(row=2, column=1, sticky="ew", pady=5, padx=10)
    ttk.Button(form, text="Сохранить как", command=self.choose_output_excel_file).grid(row=2, column=2, padx=5)

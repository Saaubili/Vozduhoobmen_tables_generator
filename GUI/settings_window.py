import tkinter as tk
from tkinter import ttk, messagebox
import ast

import Core.consts as consts
from Core.Utilities.settings_manager import (
    get_current_settings,
    apply_settings,
    save_settings
)

FIELDS = {
    "raw_headers": "Заголовки, по которым определяется таблица",
    "break_words": "Слова разделители, которые прерывают таблицу",
    "max_index_to_search_header_words_by": "До какого слова проверять заголовок",
    "max_distance_to_snap_words_together": "Расстояние между словами, меньше которого\nони считаются в одном ряду",
    "max_distance_to_stop_forming_table": "Расстояние между словами, больше которого\nтаблица считается завершенной",
    "min_explication_font_size": "Размер шрифта, ниже которого слово \"Экспликация\"\nне рассматривается как указывающее на таблицу",
    "should_warn": "Предупреждать, если количество таблиц\nне сходится с количеством найденных слов \"Экспликация\"",
}


class SettingsWindow(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Настройки")
        self.geometry("1200x500")
        self.transient(parent)
        self.grab_set()

        self.entries = {}

        self.build_ui()

    def build_list(self, key, values, parent, row):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=1, sticky="nsew", padx=10, pady=5)

        max_len = max((len(str(v)) for v in values), default=30)
        width = min(max(max_len + 2, 30), 120)

        listbox = tk.Listbox(frame, height=max(min(len(values), 10), 5), width=width)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)

        for value in values:
            listbox.insert("end", ", ".join(value) if isinstance(value, (list, tuple)) else str(value))

        listbox.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="left", fill="y")

        btns = ttk.Frame(frame)
        btns.pack(side="left", fill="y", padx=5)

        ttk.Button(btns, text="Добавить", command=lambda: self.add_list_item(listbox)).pack(pady=5)

        ttk.Button(btns, text="Удалить", command=lambda: self.remove_list_item(listbox)).pack(pady=5)

        self.entries[key] = listbox

    def add_list_item(self, listbox):

        popup = tk.Toplevel(self)
        popup.title("Добавить элемент")
        popup.geometry("500x180")
        popup.transient(self)
        popup.grab_set()

        instruction_text = (
            "Вводите элементы только через пробел\n"
            "с маленькой буквы, строго как они есть в файле")

        ttk.Label(popup, text=instruction_text, justify="left").pack(padx=10, pady=(10, 5), anchor="w")

        entry = ttk.Entry(popup, width=50)
        entry.pack(padx=10, pady=(0, 10), fill="x")

        def confirm():

            value = entry.get().strip()
            if not value:
                popup.destroy()
                return

            items = value.split()

            listbox.insert("end", ", ".join(items))

            popup.destroy()

        ttk.Button(popup, text="Добавить", command=confirm).pack(pady=(0, 10))

    def remove_list_item(self, listbox):
        sel = listbox.curselection()
        if not sel:
            return

        listbox.delete(sel[0])

    def build_ui(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(main)
        scrollbar = ttk.Scrollbar(main, orient="vertical", command=canvas.yview)

        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        settings = get_current_settings()

        row = 0

        for key, value in settings.items():

            ttk.Label(scroll_frame,text=FIELDS.get(key, key),font=("Arial", 10, "bold")).grid(row=row,
                                                                                              column=0,
                                                                                              sticky="w",
                                                                                              pady=8)

            if isinstance(value, (list, tuple)):
                self.build_list(key, value, scroll_frame, row)

            elif isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                ttk.Checkbutton(scroll_frame, variable=var).grid(row=row, column=1, sticky="w", padx=10)
                self.entries[key] = var

            else:
                widget = ttk.Entry(scroll_frame, width=60)
                widget.insert(0, repr(value))
                widget.grid(row=row, column=1, sticky="w", padx=10)

                self.entries[key] = widget

            row += 1

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=10)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=10)

        ttk.Button(buttons, text="Применить на 1 запуск", command=self.apply_once).pack(side="left", padx=5)

        ttk.Button(buttons, text="Сохранить навсегда", command=self.save_forever).pack(side="left", padx=5)

        ttk.Button(buttons, text="Сбросить по умолчанию", command=self.reset_defaults).pack(side="left", padx=5)

        ttk.Button(buttons, text="Закрыть", command=self.destroy).pack(side="right", padx=5)

    def read_settings(self):
        settings = {}
        for key, widget in self.entries.items():

            if isinstance(widget, tk.BooleanVar):
                settings[key] = widget.get()
                continue

            if isinstance(widget, tk.Listbox):

                values = widget.get(0, "end")

                parsed = [v.split(", ") for v in values]

                settings[key] = parsed

                continue

            raw = widget.get().strip()

            try:
                settings[key] = ast.literal_eval(raw)
            except Exception:
                settings[key] = raw

        return settings

    def apply_once(self):
        try:
            apply_settings(self.read_settings())
            messagebox.showinfo("OK", "Применено")

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def save_forever(self):
        try:
            settings = self.read_settings()
            apply_settings(settings)
            save_settings(settings)
            messagebox.showinfo("OK", "Сохранено")

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def reset_defaults(self):
        for key, widget in self.entries.items():
            default = consts.DEFAULT_SETTINGS[key]
            if isinstance(widget, tk.BooleanVar):
                widget.set(default)

            elif isinstance(widget, tk.Listbox):
                widget.delete(0, "end")
                for v in default:
                    widget.insert("end", ", ".join(v))

            else:
                widget.delete(0, "end")
                widget.insert(0, repr(default))
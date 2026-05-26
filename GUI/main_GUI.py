import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from GUI.main_UI_building import build_ui
import threading
import traceback
from GUI.settings_window import SettingsWindow
from Core.data_collector import collect_data_from_pdf
from Core.excel_writer import create_excel


class App:
    def __init__(self, root):
        self.log = None
        self.run_button = None
        self.root = root
        self.root.title("PDF в Excel")
        self.root.geometry("650x450")

        self.pdf_path = tk.StringVar()
        self.floors = tk.StringVar()
        self.output_path = tk.StringVar(value="Результат")

        self.show_full_error = tk.BooleanVar(value=False)

        build_ui(self)

    def show_error_window(self, title, text):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("700x400")

        txt = tk.Text(win, wrap="word")
        txt.pack(fill="both", expand=True)

        txt.insert("1.0", text)
        txt.config(state="normal")

    def write_log(self, msg):
        self.log.insert("end", str(msg) + "\n")
        self.log.see("end")

    def open_settings(self):
        SettingsWindow(self.root)

    def choose_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.pdf_path.set(path)

    def choose_output_excel_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Сохранить Excel файл")
        if path:
            self.output_path.set(path)

    def run(self):
        if not self.pdf_path.get():
            messagebox.showerror("Ошибка", "Выберите PDF файл")
            return

        self.run_button.config(state="disabled")
        self.write_log("Запуск обработки...")

        threading.Thread(target=self.process, daemon=True).start()

    def clear_log(self):
        self.log.delete("1.0", "end")

    def show_floors_help(self):
        win = tk.Toplevel(self.root)
        win.title("Как вводить этажи")
        win.geometry("700x250")
        win.transient(self.root)
        win.grab_set()

        text = tk.Text(win, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        instruction = (
            "Введите нужные вам этаже через пробел. Не используйте другие символы."
            "\nЕсли вы хотите получить экспликации, этаж которых не определён, введите \"без\""
            "\nЕсли вы хотите получить все этажи, оставьте поле пустым"
        )

        text.insert("1.0", instruction)
        text.config(state="disabled")

        ttk.Button(win, text="Закрыть", command=win.destroy).pack(pady=5)

    def process(self):
        def logger(msg):
            self.root.after(0, lambda: self.write_log(msg))

        try:
            pdf_path = self.pdf_path.get().strip()

            if not pdf_path:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "PDF не выбран"))
                return

            logger("Старт обработки PDF...")

            data = collect_data_from_pdf(pdf_path, self.floors.get(), logger=logger)

            if not data:
                logger("Результат: данных нет")
                self.root.after(0, lambda: messagebox.showwarning("Результат", "Ничего не найдено в PDF"))
                return

            output_path = self.output_path.get().strip()
            if not output_path:
                output_path = "Результат.xlsx"

            logger("Создание Excel...")
            create_excel(data, output_path=output_path)
            logger("Готово")
            self.root.after(0, lambda: messagebox.showinfo("Готово", "Excel создан"))


        except FileNotFoundError:
            msg = "PDF файл не найден. Проверьте путь к файлу."
            logger(msg)
            self.root.after(0, lambda: messagebox.showerror("Ошибка", msg))


        except PermissionError:
            msg = "Запрещен доступ к файлу. Возможно, он открыт в другой программе."
            logger(msg)
            self.root.after(0, lambda: messagebox.showerror("Ошибка", msg))


        except Exception as e:
            err = traceback.format_exc()
            msg = f"Произошла ошибка: {str(e)}"
            if self.show_full_error.get():
                logger(err)
                self.root.after(0, lambda: self.show_error_window("Полная ошибка (можно копировать)", err))
            else:
                logger(msg)
                self.root.after(0, lambda: messagebox.showerror("Ошибка", msg))

        finally:
            self.root.after(0, lambda: self.run_button.config(state="normal"))
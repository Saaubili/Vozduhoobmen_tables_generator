import pdfplumber
from Utilities.utility_for_text import normalize_headers
from Tables_extraction.table_finder import find_suitable_tables, form_correct_tables
import consts


def main():
    pdf_path = input("Пожалуйста, введите полный путь к PDF: ").strip().strip('"')
    #Расстояние, на которое будет расширена область поиска слов, чтобы точно захватить все слова в таблице
    padding_x = 35
    valid_headers = normalize_headers(consts.raw_headers)

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[60:]:
            print(f"\nСтраница {page.page_number}:")

            found_explications = page.search("Э?ксп?ликация", regex=True)

            if not found_explications:
                print(f"Не нашёл экспликаций на странице {page.page_number}")
                continue

            all_found_tables_bboxes = set()
            seen_tables = []

            successful_tables = find_suitable_tables(all_found_tables_bboxes, found_explications, page, valid_headers)
            correct_tables = form_correct_tables(successful_tables, page, padding_x, seen_tables, valid_headers)

            filtered_expl = []
            for expl in found_explications:
                if expl["chars"][0]["size"] < consts.max_font_size_to_not_consider_explication:
                    filtered_expl.append(expl)

            if len(correct_tables) < len(filtered_expl):
                print("Внимание! Количество найденных таблиц не соответствует количеству найденных слов Экспликация")

            for correct_table in correct_tables:
                print(f"\n---------- НОВАЯ ТАБЛИЦА на странице: {page.page_number} -----------\n"
                      f"Название: {correct_table.name}. bbox: {correct_table.bbox} | Ряды: {correct_table.rows}")


if __name__ == "__main__":
    main()
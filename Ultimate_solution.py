import pdfplumber
from utility_for_text import normalize_cell, normalize_headers, clean_row, is_word_in_headers
from utility_for_coordinates_work import  are_any_explications_under, is_within_bbox, get_nearest_explication
from  utility_for_word_with_tables import find_successful_tables

raw_headers = [
    ["Номер помещения", "Наименование", "Площадь, м2", "Кат. Пом."],
    ["Номер", "Число", "Площадь, м2"],
    ["№пом", "Наименование", "Площадь м2", "Кат. Пом."],
]

valid_headers = []

forbidden_chars = ".,:;\\|/[]?!'*%#-"


class Table:
    def __init__(self, header, bbox):
        self.header = header
        self.bbox = bbox
        self.name = ""
        self.rows = []

    def set_table_name(self, name):
        self.name = name

    def set_rows(self, created_rows):
        self.rows = created_rows


def main():
    pdf_path = input("Пожалуйста, введите полный путь к PDF: ").strip().strip('"')
    padding_x = 35

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[40:]:
            print(f"\nСтраница {page.page_number}:")

            found_explications = page.search("Э?ксп?ликация", regex=True)

            if not found_explications:
                print(f"Не нашёл экспликаций на странице {page.page_number}")
                continue

            last_table_x1 = 0
            previous_expl_top = 0

            found_explications = sorted(found_explications, key=lambda expl: expl["x0"])

            successful_tables = []
            all_found_tables_bboxes = set()
            seen_tables = []

            for index, explication in enumerate(found_explications):
                if explication["chars"][0]["size"] < 10:
                    continue

                are_any_expl_under, bottom = are_any_explications_under(explication, found_explications[index:], page)

                if not are_any_expl_under and abs(previous_expl_top - explication["top"]) >= 50:
                    last_table_x1 = 0
                    previous_expl_top = explication["top"]
                cropped = page.crop((last_table_x1, explication["top"], page.width, bottom))

                tables = cropped.find_tables()


                if not tables:
                    print(f"Не нашёл таблиц на странице {page.page_number}")
                    continue

                for table in tables:
                    if is_within_bbox(table.bbox, all_found_tables_bboxes):
                        continue

                    table_header_and_bbox = find_successful_tables(table, page, all_found_tables_bboxes, valid_headers)
                    if not table_header_and_bbox:
                        continue
                    header, bbox = table_header_and_bbox
                    all_found_tables_bboxes.add(bbox)

                    successful_table = Table(header, bbox)
                    successful_tables.append(successful_table)

                    if bbox[0] > explication["x1"] or are_any_expl_under:
                        continue

                    last_table_x1 = bbox[0] + (bbox[2] - bbox[0]) / 2


            for index, correct_table in enumerate (successful_tables):
                correct_table_bbox = correct_table.bbox
                name = get_nearest_explication(correct_table_bbox, found_explications, page)
                correct_table.set_table_name(name)

                x0 = max(0, correct_table_bbox[0] - padding_x)
                x1 = min(page.width, correct_table_bbox[2] + padding_x)
                top = correct_table_bbox[1] - 20
                bottom = page.height

                cropped = page.within_bbox((x0, top, x1, bottom))

                words = cropped.extract_words(keep_blank_chars=True)

                x0, y0, x1, y1 = correct_table_bbox

                words = [word for word in words if x0 - 10 <= word["x0"] <= x1 + 10]

                sorted_words = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))

                table = []
                row = []

                current_height = sorted_words[0]["top"]
                for index, word in enumerate(sorted_words):
                    word_text = word["text"]
                    word_top = word["top"]
                    clean_word = normalize_cell(word_text)

                    if word_text[0] in forbidden_chars or len(clean_word) <= 1 and not word_text.isdigit():
                        continue

                    if index <= 30 and is_word_in_headers(clean_word, valid_headers):
                        current_height = word_top
                        continue

                    if abs(current_height - word_top) <= 3:
                        row.append(word_text)
                    elif abs(current_height - word_top) <= 45:
                        current_height = word_top
                        table.append(row)
                        row = []
                        row.append(word_text)
                    else:
                        break
                if row:
                    table.append(row)


                tables_rows = []
                for row_index, row in enumerate (table):
                    if row_index > 1 and any(
                            "экспликация" in word.lower() or "схема" in word.lower() or "условные" in word.lower()
                            for word in row
                    ):
                        break

                    cleaned_row = clean_row(row, correct_table.header)
                    if not cleaned_row:
                        continue
                    joined = "|".join(cleaned_row)

                    tables_rows.append(joined)

                header_string = ""
                for word in correct_table.header:
                    header_string += word.capitalize() + "|"

                tables_rows.insert(0, header_string)

                is_duplicate = False

                current_rows = tables_rows[1:]

                for existing_rows in seen_tables:
                    if current_rows[0] == existing_rows[0] or current_rows[-1] == existing_rows[-1]:
                        is_duplicate = True
                        break

                if is_duplicate:
                    continue

                seen_tables.append(current_rows)
                correct_table.set_rows(tables_rows)

                print(f"\n---------- НОВАЯ ТАБЛИЦА на странице: {page.page_number} -----------\n"
                      f"Название: {correct_table.name}. bbox: {correct_table.bbox} | Ряды: {correct_table.rows}")


if __name__ == "__main__":
    valid_headers = normalize_headers(raw_headers)
    main()
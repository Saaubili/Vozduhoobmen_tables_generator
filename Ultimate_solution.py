import pdfplumber
from utility import normalize_cell, is_good_header, normalize_headers

raw_headers = [
    ["Номер помещения", "Наименование", "Площадь, м2", "Кат. Пом."],
    ["Номер", "Число", "Площадь, м2"],
    ["№пом", "Наименование", "Площадь м2", "Кат. Пом."],
]

valid_headers = []

biggest_header_len = 10


def is_word_in_headers(text):
    text_parts = normalize_cell(text).split()

    for header_template in valid_headers:
        for header_word in header_template:
            header_parts = normalize_cell(header_word).split()

            if all(part in header_parts for part in text_parts):
                return True

    return False


class Table:
    def __init__(self, header, bbox):
        self.header = header
        self.bbox = bbox

def main():
    pdf_path = input("Пожалуйста, введите полный путь к PDF: ").strip().strip('"')
    padding_x = 35

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[35:37]:

            found_explications = page.search("Э?ксп?ликация", regex=True)

            if not found_explications:
                print(f"Не нашёл экспликаций на странице {page.page_number}")
                continue

            for explication in found_explications[:1]:

                cropped = page.crop((0, explication["top"], page.width, page.height))

                tables = cropped.find_tables()

                if not tables:
                    print(f"Не нашёл таблиц на странице {page.page_number}")
                    continue

                print(f"\nСтраница {page.page_number}:")

                successful_tables = []
                all_found_tables_bboxes = set()

                for table in tables:
                    if table.bbox in all_found_tables_bboxes:
                        continue

                    all_found_tables_bboxes.add(table.bbox)
                    data = table.extract()
                    header, is_header_good = is_good_header(data[0], valid_headers)
                    if data and is_header_good:
                        table = Table(header, table.bbox)
                        successful_tables.append(table)

                    else:
                        # print(f"Заголовок не подошёл для {data[0]}")
                        continue

                for correct_table in successful_tables:
                    correct_table_bbox = correct_table.bbox

                    print(f"\n---------- НОВАЯ ТАБЛИЦА на странице: {page.page_number} -----------\n")
                    x0 = max(0, correct_table_bbox[0] - padding_x)
                    x1 = min(page.width, correct_table_bbox[2] + padding_x)
                    top = correct_table_bbox[1] - 20
                    bottom = page.height


                    cropped = page.within_bbox((x0, top, x1, bottom))

                    words = cropped.extract_words(keep_blank_chars=True, use_text_flow=True)

                    sorted_words = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))

                    table = []
                    row = []

                    current_height = sorted_words[0]["top"]
                    for index, word in enumerate(sorted_words):
                        word_text: str = word["text"]
                        word_top = word["top"]
                        clean_word = normalize_cell(word_text)

                        if (len(clean_word) <= 1 and not word_text.isdigit()):
                            continue

                        if index <= biggest_header_len and is_word_in_headers(clean_word):
                            current_height = word_top
                            continue

                        if abs(current_height - word_top) <= 3:
                            row.append(word_text)
                        elif abs(current_height - word_top) <= 30:
                            current_height = word_top
                            table.append(row)
                            row = []
                            row.append(word_text)
                        else:
                            break
                    if row:
                        table.append(row)

                    tables_rows = []
                    for row in table:
                        tables_rows.append("|".join(row))

                    header_string = ""
                    for word in correct_table.header:
                        header_string += word.capitalize() + "|"
                    tables_rows[0] = header_string
                    print(tables_rows)


if __name__ == "__main__":
    valid_headers = normalize_headers(raw_headers)
    main()
import pdfplumber
import re

valid_headers = [
    ["номер помещения", "наименование", "площадь м2", "кат пом"],
    ["номер", "число", "площадь м2"],
    ["№пом", "наименование", "площадь м2", "кат пом"],
]

def cell_matches(cell, template):
    return all(word in cell for word in template.split())


def is_good_header(first_row):
    normalized_row = normalize_row(first_row)

    for header_template in valid_headers:
        matched_columns = 0

        for column_name in header_template:
            if any(cell_matches(cell, column_name) for cell in normalized_row):
                matched_columns += 1

        if matched_columns >= len(header_template) - 1:
            return True

    return False


def normalize_cell(text):
    if not text:
        return ""
    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r"[.,:;]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


normalize_row = lambda row: [normalize_cell(cell) for cell in row]

def main():
    pdf_path = input("Пожалуйста, введите полный путь к PDF: ").strip().strip('"')
    padding_x = 35

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[94:96]:

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

                successful_tables_bboxes = set()
                all_found_tables_bboxes = set()

                for table in tables:
                    if table.bbox in all_found_tables_bboxes:
                        continue

                    all_found_tables_bboxes.add(table.bbox)
                    data = table.extract()
                    if data and is_good_header(data[0]):
                        successful_tables_bboxes.add(table.bbox)

                    else:
                        # print(f"Заголовок не подошёл для {data[0]}")
                        continue

                for correct_table in successful_tables_bboxes:
                    print(f"\n---------- НОВАЯ ТАБЛИЦА на странице: {page.page_number} -----------\n")
                    x0 = max(0, correct_table[0] - padding_x)
                    x1 = min(page.width, correct_table[2] + padding_x)
                    top = correct_table[1] - 20
                    bottom = page.height


                    cropped = page.within_bbox((x0, top, x1, bottom))

                    words = cropped.extract_words(keep_blank_chars=True, use_text_flow=True)

                    sorted_words = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))

                    table = []
                    row = []

                    current_height = sorted_words[0]["top"]
                    for word in sorted_words:
                        word_text: str = word["text"]
                        word_top = word["top"]

                        if len(word_text.strip(",.:;\\/?!'\" ")) <= 1 and not word_text.isdigit():
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
                        tables_rows.append(" ".join(row))
                    print(tables_rows)


if __name__ == "__main__":
    main()
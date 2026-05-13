import pdfplumber
from utility import normalize_cell, is_good_header, normalize_headers, are_any_explications_under, is_within_bbox

raw_headers = [
    ["Номер помещения", "Наименование", "Площадь, м2", "Кат. Пом."],
    ["Номер", "Число", "Площадь, м2"],
    ["№пом", "Наименование", "Площадь м2", "Кат. Пом."],
]

valid_headers = []



def get_table_name(found_explication, page):
    old_text = "Экспликация"
    new_text = ""
    next_chunk_length = 20
    while new_text != old_text:
        old_text = new_text
        bbox_to_find_next_word = (found_explication["x0"],
                                  found_explication["top"] - 5,
                                  found_explication["x1"] + next_chunk_length,
                                  found_explication["bottom"] + 5)
        text_page = page.crop(bbox_to_find_next_word)
        new_text = text_page.extract_text().strip()
        next_chunk_length += 20
    return new_text


def get_nearest_explication(table_bbox, explication_bboxes, page):
    table_x0, table_y0, table_x1, table_y1 = table_bbox
    table_center_x = (table_x0 + table_x1) / 2
    table_center_y = (table_y0 + table_y1) / 2

    nearest_explication = None
    best_distance = float("inf")

    for exp in explication_bboxes:
        exp_x0, exp_y0, exp_x1, exp_y1 = exp["x0"], exp["top"], exp["x1"], exp["bottom"]
        exp_center_x = (exp_x0 + exp_x1) / 2
        exp_center_y = (exp_y0 + exp_y1) / 2

        delta_x = abs(exp_center_x - table_center_x)
        delta_y = abs(exp_center_y - table_center_y)

        distance = delta_x + delta_y

        if distance < best_distance:
            best_distance = distance
            nearest_explication = exp

    return get_table_name(nearest_explication, page)

def clean_row(row, header):
    if len(row) > len(header):
        if not row[0].isdigit():
            return [cell for cell in row[1:]]

    elif len(row) == 1:
        row_split_by_dot = row[0].split(".")
        if len(row_split_by_dot) >= 2 and not any(word.isdigit() for word in row_split_by_dot):
            return []
        return row
    return row


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
        self.name = ""

    def set_table_name(self, name):
        self.name = name


forbidden_chars = ".,:;\\|/[]?!'*%#-"

def main():
    pdf_path = input("Пожалуйста, введите полный путь к PDF: ").strip().strip('"')
    padding_x = 35

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[35:]:
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

            for index, explication in enumerate(found_explications):
                if explication["chars"][0]["size"] < 10:
                    continue

                are_any_expl_under, bottom = are_any_explications_under(explication, found_explications[index:], page)

                if not are_any_expl_under and abs(previous_expl_top - explication["top"]) >= 50:
                    last_table_x1 = 0
                    previous_expl_top = explication["top"]

                table_name = get_table_name(explication, page)
                cropped = page.crop((last_table_x1, explication["top"], page.width, bottom))

                tables = cropped.find_tables()


                if not tables:
                    print(f"Не нашёл таблиц на странице {page.page_number}")
                    continue

                for table in tables:
                    if is_within_bbox(table.bbox, all_found_tables_bboxes):
                        continue

                    data = table.extract()
                    header, header_ok = is_good_header(data[0], valid_headers) if data else (None, False)

                    bbox = table.bbox
                    current_crop = cropped

                    if not (data and header_ok):
                        left, top, right, bottom = bbox

                        expanded_crop = page.crop((
                            max(0, left - 200),
                            max(0, top - 100),
                            min(page.width, right + 100),
                            min(page.height, bottom + 200),
                        ))

                        found_tables = expanded_crop.find_tables()

                        match = None

                        for found_table in found_tables:
                            if is_within_bbox(found_table.bbox, all_found_tables_bboxes):
                                continue

                            found_data = found_table.extract()
                            found_header, found_ok = is_good_header(found_data[0], valid_headers) if found_data else (
                                None, False)

                            if found_data and found_ok:
                                match = (found_table, found_data, found_header, expanded_crop)
                                break

                        if not match:
                            continue

                        table, data, header, current_crop = match
                        bbox = table.bbox
                        header_ok = True

                    if not (data and header_ok):
                        continue

                    all_found_tables_bboxes.add(bbox)

                    # image = current_crop.to_image()
                    # image.draw_rect(bbox)
                    # image.show()

                    successful_table = Table(header, bbox)
                    successful_tables.append(successful_table)

                    if bbox[0] > explication["x1"] or are_any_expl_under:
                        continue

                    last_table_x1 = bbox[0] + (bbox[2] - bbox[0]) / 2


            for index, correct_table in enumerate (successful_tables):
                correct_table_bbox = correct_table.bbox
                name = get_nearest_explication(correct_table_bbox, found_explications, page)
                correct_table.set_table_name(name)

                print(f"\n---------- НОВАЯ ТАБЛИЦА на странице: {page.page_number} -----------\n")
                x0 = max(0, correct_table_bbox[0] - padding_x)
                x1 = min(page.width, correct_table_bbox[2] + padding_x)
                top = correct_table_bbox[1] - 20
                bottom = page.height

                cropped = page.within_bbox((x0, top, x1, bottom))

                words = cropped.extract_words(keep_blank_chars=True)

                x0, y0, x1, y1 = correct_table_bbox

                words = [w for w in words
                    if x0 - 10 <= w["x0"] <= x1 + 10
                ]

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

                    if index <= 30 and is_word_in_headers(clean_word):
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
                print(f"Название: {correct_table.name}. Ряды: {tables_rows}")


if __name__ == "__main__":
    valid_headers = normalize_headers(raw_headers)
    main()
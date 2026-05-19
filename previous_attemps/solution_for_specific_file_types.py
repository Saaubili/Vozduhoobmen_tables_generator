# РАБОТАЕТ ТОЛЬКО С ФАЙЛАМИ, ГДЕ НА КАЖДУЮ ТАБЛИЧКУ СВОЁ НАЗВАНИЕ СО СЛОВОМ ЭКСПЛИКАЦИЯ


import pdfplumber
import re
import time

valid_headers = [
    ["номер помещения", "наименование", "площадь м2", "кат пом"],
    ["номер", "число", "площадь м2"],
    ["№пом", "наименование", "площадь м2", "кат пом"],
]

left_bound_words = ["№пом", "номер", "номер помещения"]
right_bound_words = ["кат", "кат пом"]
reserved_right_bound = ["площадь", "площадь м2"]

def main():
    full_path_to_pdf = input("Пожалуйста, введите полный путь файла: ")
    with pdfplumber.open(full_path_to_pdf) as pdf:
        for page in pdf.pages[35:]:
            all_found_words_explication = page.search(r"Э?ксп?ликация", regex=True)
            if all_found_words_explication:
                all_processed_explications_bbox = set()
                for i, found_explication in enumerate(all_found_words_explication):
                    explication_bbox = create_bbox(found_explication)

                    if explication_bbox in all_processed_explications_bbox or found_explication["chars"][0][
                        "size"] < 10:
                        continue

                    all_processed_explications_bbox.add(explication_bbox)

                    table_x_boundaries = get_table_boundaries_by_words(found_explication,
                                                                       page,
                                                                       "№пом",
                                                                       "Кат",
                                                                       "Площадь")
                    if isinstance(table_x_boundaries, list):
                        table_x0 = table_x_boundaries[0]
                        table_x1 = table_x_boundaries[1]
                    else:
                        print(table_x_boundaries)
                        continue

                    found_table = get_correct_table(table_x0, table_x1, found_explication, page,
                                                    all_processed_explications_bbox)
                    explication_text_bbox = (found_table.bbox[0], found_explication["top"] - 5, found_table.bbox[2],
                                             found_explication["bottom"] + 5)

                    explication_text_page_crop = page.crop(explication_text_bbox)
                    table_name = explication_text_page_crop.extract_text()

                    if found_table:

                        if table_name:
                            print(
                                f"На странице: {page.page_number} найдена следующая таблица c названием {table_name}:{found_table.extract()}")
                        else:
                            print(
                                f"На странице: {page.page_number} найдена следующая таблица без названия:{found_table.extract()}")
                    else:
                        print(f"Невозможно вычленить таблицу на странице {page.page_number}")
            else:
                print(f"На странице {page.page_number} слово \"Экспликация\" не найдено")


def get_table_boundaries_by_words(found_explication, page, left_boundary_word, right_boundary_word,
                                  reserved_right_boundary_word):
    left_boundary_word = left_boundary_word.lower().strip()
    right_boundary_word = right_boundary_word.lower().strip()
    reserved_right_boundary_word = reserved_right_boundary_word.lower().strip()

    chunk_to_move_by_bottom = 30
    chunk_to_move_by_x1 = 200
    chunk_to_move_by_x0 = 100

    table_x0 = 0
    global table_x1
    table_x1 = 0
    reserved_x1 = 0
    max_attempts = 20
    attempt = 0
    while (table_x0 == 0 or table_x1 == 0) and attempt < max_attempts:
        attempt += 1
        x0 = max(0, found_explication["x0"] - chunk_to_move_by_x0)
        x1 = min(page.width, found_explication["x1"] + chunk_to_move_by_x1)
        top = max(0, found_explication["top"])
        bottom = min(page.height, found_explication["bottom"] + chunk_to_move_by_bottom)

        table_header_bbox = (x0, top, x1, bottom)

        cropped_page_with_table_header = page.crop(table_header_bbox)
        header_text = cropped_page_with_table_header.extract_words()
        for word in header_text:
            word_text = word["text"].lower().strip(".,:;")
            if left_boundary_word in word_text:
                table_x0 = word["x0"]
            elif right_boundary_word in word_text:
                if table_x0 != 0 and word["x1"] > table_x0:
                    table_x1 = word["x1"]
            elif reserved_right_boundary_word in word_text:
                if table_x0 != 0 and word["x1"] > table_x0:
                    reserved_x1 = word["x1"]
        chunk_to_move_by_bottom += 5
        if table_x1 == 0:
            chunk_to_move_by_x1 += 40
        if table_x0 == 0:
            chunk_to_move_by_x0 += 40

    if table_x0 == 0:
        return f"Не удалось найти левую границу таблицы на странице {page.page_number}"

    if table_x1 == 0:
        if reserved_x1 != 0:
            table_x1 = reserved_x1
            print("Правая граница по слову 'кат' не найдена, используем 'площадь'")
        else:
            return f"Не удалось найти правую границу таблицы на странице {page.page_number}"
    return [table_x0, table_x1]


def get_correct_table(table_x0, table_x1, found_explication, page, all_processed_explications_bbox):
    shorter_coef = 1
    found_table = get_table_on_cropped_page(table_x0, table_x1, found_explication, page, shorter_coef,
                                            all_processed_explications_bbox)
    while len(found_table.extract()) <= 1:
        if shorter_coef > 4:
            return None
        shorter_coef *= 2
        found_table = get_table_on_cropped_page(table_x0, table_x1, found_explication, page, shorter_coef,
                                                all_processed_explications_bbox)
    return found_table


def get_table_on_cropped_page(table_x0, table_x1, found_explication, page, shorter_coef,
                              all_processed_explications_bbox):
    padding = 70
    x0 = max(0, table_x0 - padding)
    x1 = min(page.width, table_x1 + padding)

    top = min(found_explication["top"], page.height / shorter_coef)
    bottom = max(found_explication["top"], page.height / shorter_coef)

    table_bbox = (x0, top, x1, bottom)

    page_with_table = page.crop(table_bbox)

    is_under_any_other_explication = False
    for explication in all_processed_explications_bbox:
        found_x0 = found_explication['x0']
        found_bottom = found_explication['bottom']

        explication_x0 = explication[0]
        explication_bottom = explication[3]

        same_column = abs(found_x0 - explication_x0) <= 150
        is_below = found_bottom > explication_bottom

        if same_column and is_below:
            is_under_any_other_explication = True
            break

    if is_under_any_other_explication:
        join_tolerance_y = 0
    else:
        join_tolerance_y = 70
    all_found_table = page_with_table.find_tables(table_settings={
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "edge_min_length": 30,
        "join_y_tolerance": join_tolerance_y
    })

    found_table = None
    for table in all_found_table:
        # cropped_page_with_found_table = page.crop(table.bbox)
        # im = cropped_page_with_found_table.to_image(resolution=150)
        # im.draw_rect(table.bbox, stroke="red", stroke_width=2)
        # im.show()
        first_row_text = table.extract()[0]
        if is_good_header(first_row_text):
            found_table = table
            break
        else:
            found_table = all_found_table[0]

    return found_table


def is_within_bbox(current_bbox, found_tables_bboxes):
    for bbox_to_compare_to in found_tables_bboxes:
        if (bbox_to_compare_to[0] <= current_bbox[0]
                and bbox_to_compare_to[2] >= current_bbox[2]
                and bbox_to_compare_to[1] <= current_bbox[1]
                and bbox_to_compare_to[3] >= current_bbox[3]):
            return True
    return False


def is_good_header(first_row):
    row = normalize_row(first_row)

    for template in valid_headers:
        matches = 0

        for cell in row:
            for t in template:
                if t in cell:
                    matches += 1
                    break

        if matches >= len(template):
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


create_bbox = lambda item: (item["x0"], item["top"], item["x1"], item["bottom"])
normalize_row = lambda row: [normalize_cell(cell) for cell in row]

if __name__ == '__main__':
    main()

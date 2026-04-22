import pdfplumber
import re


def main():
    full_path_to_pdf = input("Пожалуйста, введите полный путь файла: ")
    with pdfplumber.open(full_path_to_pdf) as pdf:
         for page in pdf.pages[:]:
            all_found_words_explication = page.search(r"Э?кспликация", regex=True)
            if all_found_words_explication:
                all_processed_explications_bbox = set()

                for found_explication in all_found_words_explication:
                    explication_bbox = create_bbox(found_explication)

                    if explication_bbox in all_processed_explications_bbox or found_explication["chars"][0]["size"] < 10:
                        continue

                    all_processed_explications_bbox.add(explication_bbox)

                    table_x_boundaries = get_table_boundaries_by_words(found_explication,
                                                                       page,
                                                                       "Номер",
                                                                       "Кат",
                                                                       "Площадь")
                    if type(table_x_boundaries) is not str:
                        table_x0 = table_x_boundaries[0]
                        table_x1 = table_x_boundaries[1]
                    else:
                        print(table_x_boundaries)
                        continue

                    found_table = get_correct_table(table_x0, table_x1, found_explication, page)
                    explication_text_bbox = (found_table.bbox[0], found_explication["top"] - 5, found_table.bbox[2], found_explication["bottom"] + 5)

                    explication_text_page_crop = page.crop(explication_text_bbox)
                    table_name = explication_text_page_crop.extract_text()

                    if found_table:
                        if table_name:
                            print(f"На странице: {page} найдена следующая таблица c названием {table_name}:{found_table.extract()}")
                        else:
                            print(f"На странице: {page} найдена следующая таблица без названия:{found_table.extract()}")
                    else:
                        print(f"Невозможно вычленить таблицу на странице {page}")
            else:
                print(f"На странице {page} слово \"Экспликация\" не найдено")


def get_table_boundaries_by_words(found_explication, page, left_boundary_word, right_boundary_word, reserved_right_boundary_word):
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
        return ("Не удалось найти левую границу таблицы")

    if table_x1 == 0:
        if reserved_x1 != 0:
            table_x1 = reserved_x1
            return "Правая граница по слову 'кат' не найдена, используем 'площадь'"
        else:
            return "Не удалось найти правую границу таблицы"
    return [table_x0, table_x1]

def get_correct_table(table_x0, table_x1, found_explication, page):
    shorter_coef = 1
    found_table = get_table_on_cropped_page(table_x0, table_x1, found_explication, page, shorter_coef)
    while len(found_table.extract()) <= 1:
        if shorter_coef > 4:
            return None
        shorter_coef *= 2
        found_table = get_table_on_cropped_page(table_x0, table_x1, found_explication, page, shorter_coef)
    return found_table


def get_table_on_cropped_page(table_x0, table_x1, found_explication, page, shorter_coef):
    x0 = max(0, table_x0 - 30)
    x1 = min(page.width, table_x1 + 30)

    table_bbox = (x0, found_explication["bottom"], x1, page.height / shorter_coef)
    page_with_table = page.within_bbox(table_bbox)
    found_table = page_with_table.find_tables()[0]
    return found_table


def is_within_bbox(current_bbox, found_tables_bboxes):
    for bbox_to_compare_to in found_tables_bboxes:
        if (bbox_to_compare_to[0] <= current_bbox[0]
                and bbox_to_compare_to[2] >= current_bbox[2]
                and bbox_to_compare_to[1] <= current_bbox[1]
                and bbox_to_compare_to[3] >= current_bbox[3]):
            return True
    return False


create_bbox = lambda item: (item["x0"], item["top"], item["x1"], item["bottom"])


if __name__ == '__main__':
    main()
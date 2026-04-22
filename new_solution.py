import pdfplumber
import re


def main():
    full_path_to_pdf = input("Пожалуйста, введите полный путь файла: ")
    with pdfplumber.open(full_path_to_pdf) as pdf:
         for page in pdf.pages[50:]:
            all_found_words_explication = page.search(r"Э?кспликация", regex=True)
            if all_found_words_explication:
                all_found_tables_bboxes = set()
                all_processed_explications_bbox = set()

                for found_explication in all_found_words_explication:
                    explication_bbox = (found_explication["x0"],
                                        found_explication["top"],
                                        found_explication["x1"],
                                        found_explication["bottom"])

                    if explication_bbox in all_processed_explications_bbox or found_explication["chars"][0]["size"] < 10:
                        continue

                    all_processed_explications_bbox.add(explication_bbox)

                    chunk_to_move_by_bottom = 30
                    chunk_to_move_by_x1 = 200
                    chunk_to_move_by_x0 = 100

                    table_x0 = 0
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
                            if "номер" in word_text:
                                table_x0 = word["x0"]
                            elif "кат" in word_text:
                                if table_x0 != 0 and word["x1"] > table_x0:
                                    table_x1 = word["x1"]
                            elif "площадь" in word_text:
                                if table_x0 != 0 and word["x1"] > table_x0:
                                    reserved_x1 = word["x1"]
                        chunk_to_move_by_bottom += 5
                        if table_x1 == 0:
                            chunk_to_move_by_x1 += 40
                        if table_x0 == 0:
                            chunk_to_move_by_x0 += 40

                    if table_x0 == 0:
                        print("Не удалось найти левую границу таблицы")
                        continue

                    if table_x1 == 0:
                        if reserved_x1 != 0:
                            table_x1 = reserved_x1
                            print("Правая граница по слову 'кат.' не найдена, используем 'площадь'")
                        else:
                            print("Не удалось найти правую границу таблицы")
                            continue

                    x0 = max(0, table_x0 - 30)
                    x1 = min(page.width, table_x1 + 30)

                    table_bbox = (x0, found_explication["bottom"], x1, page.height)

                    page_with_table = page.within_bbox(table_bbox)

                    # im = page_with_table.to_image()
                    # im.draw_rect(table_bbox)
                    # im.show()

                    found_table = page_with_table.find_tables()[0]
                    all_found_tables_bboxes.add(table_bbox)

                    extracted_table = found_table.extract()

                    if len(extracted_table) <= 1:
                        table_bbox = (table_x0 - 30, found_explication["bottom"], table_x1 + 30, page.height / 2)

                        page_with_table = page.within_bbox(table_bbox)

                        # im = page_with_table.to_image()
                        # im.draw_rect(table_bbox)
                        # im.show()

                        found_table = page_with_table.find_tables()[0]
                        all_found_tables_bboxes.add(table_bbox)

                    print(f"На странице: {page} найдена следующая таблица:{found_table.extract()}")
            else:
                print(f"На странице {page} слово \"Экспликация\" не найдено")


def is_within_bbox(current_bbox, found_tables_bboxes):
    for bbox_to_compare_to in found_tables_bboxes:
        if (bbox_to_compare_to[0] <= current_bbox[0]
                and bbox_to_compare_to[2] >= current_bbox[2]
                and bbox_to_compare_to[1] <= current_bbox[1]
                and bbox_to_compare_to[3] >= current_bbox[3]):
            return True
    return False


def create_bbox(item):
    return (item["x0"], item["top"], item["x1"], item["bottom"])


if __name__ == '__main__':
    main()

import pdfplumber
import re


def main():
    full_path_to_pdf = input("Пожалуйста, введите полный путь файла: ")
    with pdfplumber.open(full_path_to_pdf) as pdf:
        for page in pdf.pages[100:]:
            all_found_words_explication = page.search(r"Э?кспликация", regex=True)
            if all_found_words_explication:
                tables_on_page = []
                same_headers_bboxes = set()

                for i, found_explication in enumerate(all_found_words_explication):
                    if found_explication["chars"][0]["size"] < 10:
                        continue
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

                    found_same_headers = page.search(new_text, regex=False)

                    for header in found_same_headers:
                        header_id = (header["x0"], header["top"], header["x1"], header["bottom"])
                        if is_within_bbox(header_id, same_headers_bboxes):
                            continue

                        same_headers_bboxes.add(header_id)
                        tables_on_page.append(get_table_by_header(header, page))

                for table in tables_on_page:
                    #print(table.extract())
                    print(f"Нашёл таблицу на странице {page}")
            else:
                print(f"На странице: {page} нет таблиц")


def get_table_by_header(table_header, page):
    x0_offset = 100 if table_header["x0"] - 200 >= 0 else table_header["x0"]
    x1_offset = 200 if table_header["x1"] + 200 <= page.width else page.width - table_header["x1"]

    bbox_to_crop_to_find_table = (table_header["x0"] - x0_offset,
                                  table_header["top"],
                                  table_header["x1"] + x1_offset,
                                  page.height)
    cropped_page = page.within_bbox(bbox_to_crop_to_find_table)
    return cropped_page.find_tables()[0]


def is_within_bbox(current_bbox, same_headers_bboxes):
    for bbox_to_compare_to in same_headers_bboxes:
        if (bbox_to_compare_to[0] <= current_bbox[0]
            and bbox_to_compare_to[2] >= current_bbox[2]
            and bbox_to_compare_to[1] <= current_bbox[1]
            and bbox_to_compare_to[3] >= current_bbox[3]):
            return True
    return False


if __name__ == '__main__':
    main()

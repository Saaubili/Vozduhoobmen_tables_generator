from Utilities.utility_for_coordinates_work import  are_any_explications_under, is_within_bbox, get_nearest_explication
from Utilities.utility_for_work_with_tables import find_if_tables_is_suitable, get_words_from_table
from consts import max_font_size_to_not_consider_explication
from .row_builder import clear_table_rows, create_rows_for_table
from Table_class import Table


def find_suitable_tables(all_found_tables_bboxes, found_explications, page, valid_headers):
    last_table_x1 = 0
    previous_expl_top = 0

    found_explications = sorted(found_explications, key=lambda expl: expl["x0"])
    successful_tables = []

    for expl_index, explication in enumerate(found_explications):
        if explication["chars"][0]["size"] < max_font_size_to_not_consider_explication:
            continue

        are_any_expl_under, bottom = are_any_explications_under(explication, found_explications[expl_index:], page)

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

            table_header_and_bbox = find_if_tables_is_suitable(table, page, all_found_tables_bboxes, valid_headers)
            if not table_header_and_bbox:
                continue
            header, bbox = table_header_and_bbox
            all_found_tables_bboxes.add(bbox)

            name = get_nearest_explication(table.bbox, found_explications, page)

            successful_table = Table(header, bbox, name)
            successful_tables.append(successful_table)

            if bbox[0] > explication["x1"] or are_any_expl_under:
                continue

            last_table_x1 = bbox[0] + (bbox[2] - bbox[0]) / 2
    return successful_tables


def form_correct_tables(successful_tables, page, padding_x, seen_tables, valid_headers):
    verified_correct_tables = []

    for table_index, correct_table in enumerate(successful_tables):
        correct_table_bbox = correct_table.bbox

        words = get_words_from_table(correct_table_bbox, page, padding_x)
        sorted_words = sorted(words, key=lambda word: (round(word["top"], 1), word["x0"]))

        table = []
        create_rows_for_table(sorted_words, table, valid_headers)

        tables_rows = []
        clear_table_rows(table, correct_table, tables_rows)

        header_string = ""
        for word in correct_table.header:
            header_string += word.capitalize() + "|"

        tables_rows.insert(0, header_string)

        is_duplicate = False

        current_rows = tables_rows[1:]

        for existing_rows in seen_tables:
            if current_rows[0] == existing_rows[0] and current_rows[-1] == existing_rows[-1]:
                is_duplicate = True
                break

        if is_duplicate:
            continue

        seen_tables.append(current_rows)
        correct_table.set_rows(tables_rows)
        verified_correct_tables.append(correct_table)

    return verified_correct_tables
import pdfplumber
from collections import defaultdict

from Core import consts
from Core.Utilities.utility_for_text import normalize_headers, form_floors_list
from Core.Utilities.room_parser import parse_table_row
from Core.Tables_extraction.table_finder import find_suitable_tables, form_correct_tables

def normalize_room_no(room_no):
    return str(room_no).strip().replace(" ", "").lower()

def collect_data_from_pdf(pdf_path, chosen_floors, logger=print):
    floors_list = form_floors_list(chosen_floors)
    valid_headers = normalize_headers(consts.raw_headers)
    all_data = defaultdict(list)
    seen_room_nos = defaultdict(set)

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            logger(f"\nСтраница {page.page_number}:")

            row_found_explications = page.search("Э?ксп?ликация", regex=True)

            filtered_found_explications = []
            for expl in row_found_explications:
                if expl["chars"][0]["size"] >= consts.min_explication_font_size:
                    filtered_found_explications.append(expl)

            if not filtered_found_explications:
                logger(f"Не нашёл экспликаций на странице {page.page_number}")
                continue

            all_found_tables_bboxes = set()
            seen_tables = []

            successful_tables = find_suitable_tables(
                all_found_tables_bboxes,
                filtered_found_explications,
                page,
                valid_headers,
                floors_list
            )

            correct_tables = form_correct_tables(
                successful_tables,
                page,
                padding_x=35,
                seen_tables=seen_tables,
                valid_headers=valid_headers
            )

            if consts.should_warn:
                if len(correct_tables) < len(filtered_found_explications):
                    logger("Внимание! Количество найденных таблиц меньше количества экспликаций")

            for correct_table in correct_tables:
                floor = correct_table.floor

                logger(
                    f"\n---------- НОВАЯ ТАБЛИЦА на странице: {page.page_number} -----------\n"
                    f"Название: {correct_table.name}"
                )

                for row in correct_table.rows[1:]:
                    parsed = parse_table_row(row)
                    if not parsed:
                        continue

                    room_key = normalize_room_no(parsed["room_no"])

                    # пропускаем дубли по номеру помещения
                    if room_key in seen_room_nos[floor]:
                        continue

                    seen_room_nos[floor].add(room_key)
                    all_data[floor].append(parsed)

    return all_data
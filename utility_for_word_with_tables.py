from utility_for_text import normalize_row
from  utility_for_coordinates_work import is_within_bbox

def cell_matches(cell, template):
    return all(word in cell for word in template.split())

def is_good_header(first_row, valid_headers):
    normalized_row = normalize_row(first_row)

    for header_template in valid_headers:
        matched_columns = 0

        for column_name in header_template:
            if any(cell_matches(cell, column_name) for cell in normalized_row):
                matched_columns += 1

        if matched_columns >= len(header_template) - 1:
            return (header_template, True)

    return ("", False)



def find_successful_tables(table, page, all_found_tables_bboxes, valid_headers):
    data = table.extract()
    header, header_ok = is_good_header(data[0], valid_headers) if data else (None, False)

    bbox = table.bbox

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
            return []

        table, data, header, current_crop = match
        bbox = table.bbox
        header_ok = True

    if not (data and header_ok):
        return []
    return [header, bbox]
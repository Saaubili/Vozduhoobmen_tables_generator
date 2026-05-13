import re

normalize_row = lambda row: [normalize_cell(cell) for cell in row]
create_bbox = lambda item: (item["x0"], item["top"], item["x1"], item["bottom"])


def normalize_cell(text):
    if not text:
        return ""
    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r"[.,:;]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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


def normalize_headers(raw_headers):
    valid_normalized_header = []
    for header in raw_headers:
        normalized_header = []
        for word in header:
            word = normalize_cell(word)
            normalized_header.append(word)
        valid_normalized_header.append(normalized_header)
    return valid_normalized_header


def are_any_explications_under(current_expl, all_found_expl, page):
    current_x0 = current_expl["x0"]
    current_top = current_expl["top"]

    for explication in all_found_expl:
        same_column = abs(explication["x0"] - current_x0) <= 40
        is_below = explication["top"] > current_top + 50

        if same_column and is_below:
            return [True, explication["top"]]

    return [False, page.height]


def is_within_bbox(current_bbox, found_tables_bboxes, padding=30):
    cur_left, cur_top, cur_right, cur_bottom = current_bbox

    for left, top, right, bottom in found_tables_bboxes:

        if (cur_left >= left - padding
                and cur_right <= right + padding
                and cur_top >= top - padding
                and cur_bottom <= bottom + padding):
            return True

    return False

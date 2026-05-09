import re


def normalize_cell(text):
    if not text:
        return ""
    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r"[.,:;]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


normalize_row = lambda row: [normalize_cell(cell) for cell in row]


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
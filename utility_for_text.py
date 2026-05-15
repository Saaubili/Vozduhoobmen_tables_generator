import re

normalize_row = lambda row: [normalize_cell(cell) for cell in row]


def normalize_cell(text):
    if not text:
        return ""
    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r"[.,:;]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_headers(raw_headers):
    valid_normalized_header = []
    for header in raw_headers:
        normalized_header = []
        for word in header:
            word = normalize_cell(word)
            normalized_header.append(word)
        valid_normalized_header.append(normalized_header)
    return valid_normalized_header


def is_word_in_headers(text, valid_headers):
    text_parts = normalize_cell(text).split()

    for header_template in valid_headers:
        for header_word in header_template:
            header_parts = normalize_cell(header_word).split()

            if all(part in header_parts for part in text_parts):
                return True

    return False

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

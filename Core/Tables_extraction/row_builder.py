from Core.consts import (
    forbidden_chars,
    max_index_to_search_header_words_by,
    max_distance_to_snap_words_together,
    max_distance_to_stop_forming_table,
    break_words
)
from Core.Utilities.utility_for_text import normalize_cell, is_word_in_headers, clean_row

def create_rows_for_table(sorted_words, table, valid_headers):
    current_height = sorted_words[0]["top"]
    row = []
    for word_index, word in enumerate(sorted_words):
        word_text = word["text"]
        word_top = word["top"]
        clean_word = normalize_cell(word_text)

        if word_text[0] in forbidden_chars or len(clean_word) <= 1 and not word_text.isdigit():
            continue

        if word_index <= max_index_to_search_header_words_by and is_word_in_headers(clean_word, valid_headers):
            current_height = word_top
            continue

        if abs(current_height - word_top) <= max_distance_to_snap_words_together:
            row.append(word_text)

        elif abs(current_height - word_top) <= max_distance_to_stop_forming_table:
            current_height = word_top
            table.append(row)
            row = []
            row.append(word_text)

        else:
            break

    if row:
        table.append(row)


def clear_table_rows(table, correct_table, tables_rows):
    for row_index, row in enumerate(table):
        should_break = False
        if row_index > 1:
            for cell in row:
                words_in_cell = [word.lower() for word in cell.split(" ")]
                if any(word in break_words for word in words_in_cell):
                    should_break = True
                    break
        if should_break:
            break

        cleaned_row = clean_row(row, correct_table.header)
        if not cleaned_row:
            continue

        tables_rows.append("|".join(cleaned_row))

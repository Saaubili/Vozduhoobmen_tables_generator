def is_within_bbox(current_bbox, found_tables_bboxes, padding=30):
    cur_left, cur_top, cur_right, cur_bottom = current_bbox

    for left, top, right, bottom in found_tables_bboxes:

        if (cur_left >= left - padding
                and cur_right <= right + padding
                and cur_top >= top - padding
                and cur_bottom <= bottom + padding):
            return True

    return False


def are_any_explications_under(current_expl, all_found_expl, page):
    current_x0 = current_expl["x0"]
    current_top = current_expl["top"]

    for explication in all_found_expl:
        same_column = abs(explication["x0"] - current_x0) <= 40
        is_below = explication["top"] > current_top + 50

        if same_column and is_below:
            return [True, explication["top"]]

    return [False, page.height]


def get_table_name(found_explication, page):
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
    return new_text


def get_nearest_explication(table_bbox, explication_bboxes, page):
    table_x0, table_y0, table_x1, table_y1 = table_bbox
    table_center_x = (table_x0 + table_x1) / 2
    table_center_y = (table_y0 + table_y1) / 2

    nearest_explication = None
    best_distance = float("inf")

    for exp in explication_bboxes:
        exp_x0, exp_y0, exp_x1, exp_y1 = exp["x0"], exp["top"], exp["x1"], exp["bottom"]
        exp_center_x = (exp_x0 + exp_x1) / 2
        exp_center_y = (exp_y0 + exp_y1) / 2

        delta_x = abs(exp_center_x - table_center_x)
        delta_y = abs(exp_center_y - table_center_y)

        distance = delta_x + delta_y

        if distance < best_distance:
            best_distance = distance
            nearest_explication = exp

    return get_table_name(nearest_explication, page)

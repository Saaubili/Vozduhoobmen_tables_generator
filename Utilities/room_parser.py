import re
from Utilities.utility_for_text import normalize_cell

def _looks_like_area(text):
    text = str(text).strip().replace(",", ".")
    try:
        float(text)
        return True
    except:
        return False


def split_room(text):
    text = re.sub(r"\s+", " ", str(text)).strip()
    m = re.match(r"^([A-Za-zА-Яа-яЁё]?\d+(?:\.\d+)*(?:-\d+)?)\s+(.+)$", text)
    if m:
        return m.group(1), m.group(2)
    return None, text


def is_room_like(text):
    text = normalize_cell(text)

    if not text:
        return False

    if "номер" in text or "наимен" in text or "площад" in text or "кат" in text:
        return False

    if not any(ch.isdigit() for ch in text):
        return False

    return bool(re.match(r"^[A-Za-zА-Яа-яЁё]?\d[\dA-Za-zА-Яа-яЁё.\-]*$", text))


def compact_cells(row):
    if isinstance(row, str):
        cells = [c.strip() for c in row.split("|")]
    else:
        cells = [str(c).replace("\n", " ").strip() for c in row]

    return [c for c in cells if c]


def parse_table_row(row):
    cells = compact_cells(row)
    if not cells:
        return None

    joined = " ".join(normalize_cell(c) for c in cells)

    if ("номер" in joined and "наимен" in joined and "площад" in joined):
        return None

    for i, cell in enumerate(cells):
        room_no, name = split_room(cell)
        if room_no and name:
            if i + 1 >= len(cells):
                continue

            area_text = cells[i + 1]
            category = cells[i + 2] if i + 2 < len(cells) else ""

            if not _looks_like_area(area_text):
                continue

            try:
                area = float(str(area_text).replace(",", "."))
            except:
                area = None

            return {
                "room_no": room_no,
                "name": name,
                "area": area,
                "category": category
            }

        if is_room_like(cell):
            if i + 1 >= len(cells):
                continue

            name = cells[i + 1]
            if not name or _looks_like_area(name):
                continue

            area_text = cells[i + 2] if i + 2 < len(cells) else ""
            category = cells[i + 3] if i + 3 < len(cells) else ""

            if not _looks_like_area(area_text):
                continue

            try:
                area = float(str(area_text).replace(",", "."))
            except:
                area = None

            return {
                "room_no": cell,
                "name": name,
                "area": area,
                "category": category
            }

    return None


def get_floor(table_name):
    if not table_name:
        return "Без этажа"

    text = str(table_name).lower()

    if "подвал" in text or "цоколь" in text or "−1 этаж" in text:
        return "-1 этаж"

    m = re.search(r"([\-−]?\d+)\s*этаж", text)
    if m:
        return f"{m.group(1)} этаж"

    return "Без этажа"
import xlsxwriter


def sanitize_sheet_name(name):
    import re
    name = re.sub(r'[\\/*?:\[\]]', "_", str(name))
    name = re.sub(r"\s+", " ", name).strip()
    return name[:31] if name else "Лист"


def _qsheet(name: str) -> str:
    return "'" + str(name).replace("'", "''") + "'"


def _stack_ref(sheet_names, col_range):
    return ",".join(f"{_qsheet(s)}!{col_range}" for s in sheet_names)


def create_excel(data, output_path="result.xlsx"):
    workbook = xlsxwriter.Workbook(output_path)
    workbook.set_calc_mode("auto")

    title_fmt = workbook.add_format({
        "bold": True,
        "font_size": 14,
        "align": "center",
        "valign": "vcenter",
    })
    header_blue_fmt = workbook.add_format({
        "bold": True,
        "font_size": 11,
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True,
        "border": 1,
        "bg_color": "#B8CCE4",
    })
    header_white_fmt = workbook.add_format({
        "bold": True,
        "font_size": 11,
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True,
        "border": 1,
        "bg_color": "#FFFFFF",
    })
    cell_center_fmt = workbook.add_format({
        "border": 1,
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True,
    })
    cell_left_fmt = workbook.add_format({
        "border": 1,
        "align": "left",
        "valign": "vcenter",
        "text_wrap": True,
    })
    num_fmt = workbook.add_format({
        "border": 1,
        "align": "center",
        "valign": "vcenter",
        "num_format": "0.0",
    })
    formula_fmt = workbook.add_format({
        "border": 1,
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True,
    })
    formula_num_fmt = workbook.add_format({
        "border": 1,
        "align": "center",
        "valign": "vcenter",
        "num_format": "0.0",
    })

    if not data:
        ws = workbook.add_worksheet("Пусто")
        ws.write("A1", "Данные не найдены")
        workbook.close()
        return

    created_floors = []

    for floor, rooms in data.items():
        sheet_name = sanitize_sheet_name(floor)
        created_floors.append(sheet_name)

        ws = workbook.add_worksheet(sheet_name)
        ws.merge_range("A1:M1", f"Таблица воздухообменов — {floor}", title_fmt)

        headers = [
            "№ п/п", "Наименование помещений", "Категория",
            "Температура", "Площадь", "Объём",
            "Приток кратность", "Вытяжка кратность",
            "Приток", "Вытяжка",
            "Приточная", "Вытяжная", "Примечание"
        ]

        for col, h in enumerate(headers):
            ws.write(1, col, h, header_blue_fmt if col in (0, 1, 4, 5, 8, 9) else header_white_fmt)

        ws.write("N1", "Высота, м", header_white_fmt)
        ws.write("N2", 3)
        ws.set_column("N:N", None, None, {"hidden": True})

        row_i = 3
        for room in rooms:
            ws.write(f"A{row_i}", room["room_no"], cell_center_fmt)
            ws.write(f"B{row_i}", room["name"], cell_left_fmt)
            ws.write(f"C{row_i}", room["category"], cell_center_fmt)
            ws.write_number(f"E{row_i}", room["area"] if room["area"] is not None else 0, num_fmt)

            ws.write_formula(f"F{row_i}", f"=E{row_i}*$N$2", formula_num_fmt)
            ws.write_formula(f"I{row_i}", f"=F{row_i}*G{row_i}", formula_num_fmt)
            ws.write_formula(f"J{row_i}", f"=F{row_i}*H{row_i}", formula_num_fmt)

            for col in range(1, 14):
                if col in (1, 2, 3, 5, 6, 9, 10):
                    continue
                ws.write_blank(row_i - 1, col - 1, None, cell_center_fmt)

            row_i += 1

        widths = {
            "A": 10, "B": 32, "C": 14, "D": 14, "E": 12, "F": 12,
            "G": 14, "H": 14, "I": 12, "J": 12, "K": 12, "L": 12, "M": 14
        }
        for col, width in widths.items():
            ws.set_column(f"{col}:{col}", width)

        ws.freeze_panes(2, 0)

    ws_sys = workbook.add_worksheet("Системы")

    sys_headers = [
        "Система",
        "Зона обслуживания",
        "Расход м3\\ч",
        "Расход с запасом м3\\ч",
        "Нагрузка на калорифер кВт (расчет на расход с запасом)",
        "Размещение оборудования",
        "Выброс/забор",
        "Примечание к подборам",
        "С-ма в модели",
        "Потреи давления в с-ме, Па (аэродинамика)",
        "Потери в выбросе/заборе",
        "Потери общие",
        "Выдано на подбор производителю",
        "Установлено в модели + ХОВС",
        "Примечание"
    ]

    for col_idx, header in enumerate(sys_headers):
        ws_sys.write(0, col_idx, header, header_white_fmt)

    if not created_floors:
        workbook.close()
        return

    stack_b = f"_xlfn.VSTACK({_stack_ref(created_floors, 'B3:B1000')})"
    stack_i = f"_xlfn.VSTACK({_stack_ref(created_floors, 'I3:I1000')})"
    stack_j = f"_xlfn.VSTACK({_stack_ref(created_floors, 'J3:J1000')})"
    stack_k = f"_xlfn.VSTACK({_stack_ref(created_floors, 'K3:K1000')})"
    stack_l = f"_xlfn.VSTACK({_stack_ref(created_floors, 'L3:L1000')})"
    stack_d = f"_xlfn.VSTACK({_stack_ref(created_floors, 'D3:D1000')})"

    max_row = 202

    for r in range(3, max_row + 1):
        excel_row = r

        formula_B = (
            f'=IFERROR(_xlfn.TEXTJOIN(", ",TRUE,'
            f'_xlfn.UNIQUE('
            f'_xlfn.FILTER('
            f'{stack_b},'
            f'({stack_k}=A{excel_row})+({stack_l}=A{excel_row})'
            f')'
            f')'
            f'),"Не найдено")'
        )

        formula_C = (
            f'=IFERROR('
            f'SUM('
            f'_xlfn.FILTER('
            f'{stack_i},'
            f'({stack_k}=A{excel_row})+({stack_l}=A{excel_row})'
            f')'
            f')'
            f'+'
            f'SUM('
            f'_xlfn.FILTER('
            f'{stack_j},'
            f'({stack_k}=A{excel_row})+({stack_l}=A{excel_row})'
            f')'
            f')'
            f',0)'
        )

        formula_D = f"=C{excel_row}*1.1"

        formula_E = (
            f'=IFERROR('
            f'SUM('
            f'_xlfn.FILTER('
            f'({stack_d}*1.005*(({stack_d})-(-32))*1.2/3600),'
            f'({stack_k}=A{excel_row})+({stack_l}=A{excel_row})'
            f')'
            f')'
            f',0)'
        )

        formula_L = f"=J{excel_row}+K{excel_row}"

        ws_sys.write(r - 1, 0, "-", cell_center_fmt)
        ws_sys.write_formula(r - 1, 1, formula_B, formula_fmt)
        ws_sys.write_formula(r - 1, 2, formula_C, formula_num_fmt)
        ws_sys.write_formula(r - 1, 3, formula_D, formula_num_fmt)
        ws_sys.write_formula(r - 1, 4, formula_E, formula_num_fmt)
        ws_sys.write_formula(r - 1, 11, formula_L, formula_num_fmt)

        for c in range(15):
            if c in (0, 1, 2, 3, 4, 11):
                continue
            ws_sys.write_blank(r - 1, c, None, cell_center_fmt)

    ws_sys.set_column("A:A", 12)
    ws_sys.set_column("B:B", 35)
    ws_sys.set_column("C:C", 16)
    ws_sys.set_column("D:D", 20)
    ws_sys.set_column("E:E", 28)
    ws_sys.set_column("F:F", 22)
    ws_sys.set_column("G:G", 18)
    ws_sys.set_column("H:H", 22)
    ws_sys.set_column("I:I", 18)
    ws_sys.set_column("J:J", 18)
    ws_sys.set_column("K:K", 18)
    ws_sys.set_column("L:L", 16)
    ws_sys.set_column("M:M", 18)
    ws_sys.set_column("N:N", 22)
    ws_sys.set_column("O:O", 16)

    ws_sys.freeze_panes(1, 0)

    ws_pick = workbook.add_worksheet("Подборы")

    pick_headers = [
        "Система",
        "Зона обслуживания",
        "Расход с запасом м3\\ч",
        "Потери общие",
        "Тип вентилятора",
        "Климатическое исполнение",
        "Последовательность элементов",
        "Секция нагрева",
        "Кол-во секций нагрева",
        "Температура наружного воздуха ХПГ",
        "Температура приточного воздуха ХПГ",
        "Шумоглушитель",
        "Примечание"
    ]

    for col_idx, header in enumerate(pick_headers):
        ws_pick.write(0, col_idx, header, header_white_fmt)

    for r in range(3, max_row + 1):
        excel_row = r
        out_row = r - 1

        ws_pick.write_formula(out_row, 0, f"='Системы'!A{excel_row}", cell_center_fmt)
        ws_pick.write_blank(out_row, 1, None, cell_left_fmt)
        ws_pick.write_formula(out_row, 2, f"='Системы'!D{excel_row}", formula_num_fmt)
        ws_pick.write_formula(out_row, 3, f"='Системы'!L{excel_row}", formula_num_fmt)
        ws_pick.write_blank(out_row, 4, None, cell_center_fmt)
        ws_pick.write_blank(out_row, 5, None, cell_center_fmt)
        ws_pick.write_blank(out_row, 6, None, cell_center_fmt)
        ws_pick.write_blank(out_row, 7, None, cell_center_fmt)
        ws_pick.write_blank(out_row, 8, None, cell_center_fmt)
        ws_pick.write_blank(out_row, 9, None, cell_center_fmt)
        ws_pick.write_blank(out_row, 10, None, cell_center_fmt)
        ws_pick.write_blank(out_row, 11, None, cell_center_fmt)
        ws_pick.write_blank(out_row, 12, None, cell_center_fmt)

    ws_pick.data_validation(f"E3:E{max_row}", {
        "validate": "list",
        "source": ["Канальный", "Каркасный", "Крышный"]
    })

    ws_pick.data_validation(f"H3:H{max_row}", {
        "validate": "list",
        "source": ["Водяной", "Электрический", "Не требуется"]
    })

    ws_pick.data_validation(f"L3:L{max_row}", {
        "validate": "list",
        "source": [
            "Со стороны улицы",
            "Со стороны помещения",
            "Со стороны улицы и со стороны помещения",
            "Не требуется"
        ]
    })

    ws_pick.set_column("A:A", 12)
    ws_pick.set_column("B:B", 35)
    ws_pick.set_column("C:C", 16)
    ws_pick.set_column("D:D", 16)
    ws_pick.set_column("E:E", 16)
    ws_pick.set_column("F:F", 18)
    ws_pick.set_column("G:G", 22)
    ws_pick.set_column("H:H", 16)
    ws_pick.set_column("I:I", 18)
    ws_pick.set_column("J:J", 24)
    ws_pick.set_column("K:K", 24)
    ws_pick.set_column("L:L", 28)
    ws_pick.set_column("M:M", 18)

    ws_pick.freeze_panes(1, 0)

    workbook.close()
    print(f"Excel-файл сохранён: {output_path}")
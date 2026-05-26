import copy

raw_headers = [
    ["Номер помещения", "Наименование", "Площадь, м2", "Кат. Пом."],
    ["Номер", "Число", "Площадь, м2"],
    ["№пом", "Наименование", "Площадь м2", "Кат. Пом."],
]

break_words = ["экспликация", "условные", "схема"]

forbidden_chars = ".,:;\\|/[]?!'*%#-"


#Первые 30 слов проверяются на то, являются ли они частью заголовка, остальные нет
max_index_to_search_header_words_by = 30

#Расстояние между словами, преодолев которое, слова не считаются входящими в один ряд
max_distance_to_snap_words_together = 3
#Расстояние между словами, преодолев которое, таблица считается законченной
max_distance_to_stop_forming_table = 45
#Размер шрифта, ниже которого слово "Экспликация" не рассматривается как указывающее на таблицу
min_explication_font_size = 10
#Стоит ли проверять, совпадает ли количество найденных слов "Экспликация" с количеством найденных таблиц
should_warn = False

DEFAULT_SETTINGS = copy.deepcopy({
    "raw_headers": raw_headers,
    "break_words": break_words,
    "forbidden_chars": forbidden_chars,

    "max_index_to_search_header_words_by": max_index_to_search_header_words_by,

    "max_distance_to_snap_words_together": max_distance_to_snap_words_together,
    "max_distance_to_stop_forming_table": max_distance_to_stop_forming_table,

    "min_explication_font_size": min_explication_font_size,

    "should_warn": should_warn,
})
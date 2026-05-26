import json
import os
import Core.consts as consts

SETTINGS_FILE = "settings.json"

def get_current_settings():
    return {
        "raw_headers": consts.raw_headers,
        "break_words": consts.break_words,
        "max_index_to_search_header_words_by": consts.max_index_to_search_header_words_by,
        "max_distance_to_snap_words_together": consts.max_distance_to_snap_words_together,
        "max_distance_to_stop_forming_table": consts.max_distance_to_stop_forming_table,
        "min_explication_font_size": consts.min_explication_font_size,
        "should_warn": consts.should_warn,
    }


def apply_settings(settings):
    consts.raw_headers = settings["raw_headers"]
    consts.break_words = settings["break_words"]

    consts.max_index_to_search_header_words_by = (
        settings["max_index_to_search_header_words_by"]
    )

    consts.max_distance_to_snap_words_together = (
        settings["max_distance_to_snap_words_together"]
    )

    consts.max_distance_to_stop_forming_table = (
        settings["max_distance_to_stop_forming_table"]
    )

    consts.min_explication_font_size = (
        settings["min_explication_font_size"]
    )

    consts.should_warn = settings["should_warn"]


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(consts.DEFAULT_SETTINGS)

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)

    apply_settings(settings)
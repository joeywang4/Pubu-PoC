"""Conver page id to/from API input id"""
import math
import random


def from_input(input_id: str) -> int:
    """Translate API page id to page_id"""
    digit_dict = {
        "1": 1,
        "2": 4,
        "3": 0,
        "4": 8,
        "5": 9,
        "6": 2,
        "7": 5,
        "8": 7,
        "9": 3,
        "0": 6,
    }
    str_id = input_id[1::2]
    str_id = str_id[-2:] + str_id[:-2]

    out = 0
    for char in str_id:
        out = (out * 10) + digit_dict[char]
    return math.ceil((out - 21) / 17)


def to_input(page_id: int) -> str:
    """Tanslate page_id for API query"""
    if page_id < 10000:
        return str(page_id)

    digit_dict = {
        "1": "1",
        "4": "2",
        "0": "3",
        "8": "4",
        "9": "5",
        "2": "6",
        "5": "7",
        "7": "8",
        "3": "9",
        "6": "0",
    }
    str_id = str(page_id * 17 + 5)

    out = ""
    for char in str_id:
        out += digit_dict[char]
    out = out[2:] + out[:2]
    out = "".join([str(random.randint(0, 9)) + s for s in out])
    return out

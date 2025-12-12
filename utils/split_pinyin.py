from typing import Tuple


def spilt_pinyin(pinyin: str) -> Tuple[str, str]:
    """将拼音拆分为声母和韵母"""
    initials = [
        "zh",
        "ch",
        "sh",
        "b",
        "p",
        "m",
        "f",
        "d",
        "t",
        "n",
        "l",
        "g",
        "k",
        "h",
        "j",
        "q",
        "x",
        "r",
        "z",
        "c",
        "s",
        "y",
        "w",
    ]
    initial = ""
    # 找到声母
    for init in initials:
        if pinyin.startswith(init):
            initial = init
            break

    final = pinyin[len(initial) :]
    return (initial, final)

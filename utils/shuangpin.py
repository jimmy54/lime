from typing import Dict, List
from utils.split_pinyin import spilt_pinyin


def generate_shuang_pinyin(pinyin_k_l: List[str]) -> Dict[str, str]:
    sm_map = {"zh": "v", "ch": "i", "sh": "u"}
    ym_map = {
        "iu": "q",
        "ia": "w",
        "ua": "w",
        "e": "e",
        "uan": "r",
        "ue": "t",
        "ve": "t",
        "ing": "y",
        "uai": "y",
        "u": "u",
        "i": "i",
        "o": "o",
        "uo": "o",
        "un": "p",
        "a": "a",
        "iong": "s",
        "ong": "s",
        "iang": "d",
        "uang": "d",
        "en": "f",
        "eng": "g",
        "ang": "h",
        "an": "j",
        "ao": "k",
        "ai": "l",
        "ei": "z",
        "ie": "x",
        "iao": "c",
        "ui": "v",
        "v": "v",
        "ou": "b",
        "in": "n",
        "ian": "m",
    }
    raw = {
        "a": "aa",
        "ai": "ai",
        "an": "an",
        "ang": "ah",
        "ao": "ao",
        "e": "ee",
        "ei": "ei",
        "en": "en",
        "eng": "eg",
        "er": "er",
        "o": "oo",
        "ou": "ou",
    }
    dbp2fullp: Dict[str, str] = {}
    for i in pinyin_k_l:
        if i in raw:
            dbp2fullp[raw[i]] = i
            continue
        s, y = spilt_pinyin(i)
        ds = sm_map[s] if s in sm_map else s
        dy = ym_map[y] if y in ym_map else y
        dbp2fullp[ds + dy] = i
    return dbp2fullp

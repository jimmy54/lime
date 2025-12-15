from os import path
from typing import Dict, List, Set

from assets.pinyin.script.dict import get_dict

script_dir = path.dirname(path.abspath(__file__))


def get_dict_py(filepath: str) -> Dict[str, List[str]]:
    d: Dict[str, List[str]] = {}
    pa = path.normpath(path.join(script_dir, filepath))
    ll = get_dict(pa)
    for i in ll:
        x = i.split("\t")
        zi = x[0]
        pinyin = x[1]
        if not zi or not pinyin:
            continue
        l = d[zi] if zi in d else []
        l.append(pinyin)
        d[zi] = l
    return d


def load_pinyin():
    a = get_dict_py("../8105.dict.yaml")
    b = get_dict_py("../41448.dict.yaml")
    d: Dict[str, Set[str]] = {}
    for i in a:
        l: Set[str] = d[i] if i in d else set()
        l = l | set(a[i])
        d[i] = l
    for i in b:
        l: Set[str] = d[i] if i in d else set()
        l = l | set(b[i])
        d[i] = l

    def pinyin(ci: str):
        l: List[List[str]] = []
        for i in ci:
            if i in d:
                l.append(list(d[i]))
            else:
                return []
        return l

    return pinyin

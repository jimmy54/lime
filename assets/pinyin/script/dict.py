from typing import List


def get_dict(filepath: str) -> List[str]:
    l: List[str] = []
    with open(filepath, "r") as file:
        texts = file.readlines()
        is_meta = False
        for i in texts:
            if i.endswith("\n"):
                i = i[0:-1]
            if i.startswith("#"):
                continue
            if i == "---":
                is_meta = True
                continue
            if i == "...":
                is_meta = False
                continue
            if i == "":
                continue
            if is_meta:
                continue
            l.append(i)
    return l

# 放在test文件夹后找不到模块，不知道怎么处理……

from os import path

import jieba
from numpy import str_
from main import Result, commit, clear_commit, single_ci, stop_all
from pypinyin import lazy_pinyin

from utils.keys_to_pinyin import keys_to_pinyin

script_dir = path.dirname(path.abspath(__file__))
file_path = path.normpath(path.join(script_dir, "test", "冰灯.txt"))


if __name__ == "__main__":
    clear_commit()
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    test_text = jieba.cut(content)

    offset = 0

    def match(src_t: str, r: Result):
        for idx, candidate in enumerate(r["candidates"]):
            text = candidate["word"]
            if src_t.startswith(text):
                if src_t == text:
                    commit(text, new=True, update=True)
                else:
                    commit(text, update=True, new=False)
                return text, idx, candidate["remainkeys"]

    count = 0
    for src_t in test_text:
        count = count + 1
        py = "".join(lazy_pinyin(src_t))

        for _i in range(len(src_t)):
            pinyin_input = keys_to_pinyin(py, shuangpin=False)
            candidates = single_ci(pinyin_input)
            m = match(src_t, candidates)
            if m == None:
                print("找不到:", src_t)
                commit(src_t, update=False, new=True)
                continue
            py = "".join(m[2])
            src_t = src_t[len(m[0]) :]
            print(m[0], m[1])
            offset = offset + m[1]
            if src_t == "":
                break

    print("偏移", offset, "分词数", count)


stop_all()

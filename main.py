from flask import Flask, request, jsonify
from pypinyin import lazy_pinyin
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import List, Dict, Tuple, TypedDict

# 初始化 Flask 应用
print("初始化网络服务器")
app = Flask(__name__)

# 加载模型和分词器
model_name = "Qwen/Qwen3-0.6B"  # 或您使用的模型
print("加载模型", model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# 上下文存储
pre_context = "下面的内容主题多样并且没有标点"
user_context = []


# 按键转拼音
def keys_to_pinyin(keys: str) -> str:
    # 示例：将按键直接映射为拼音（实际可根据需求扩展）
    # 比如双拼、模糊
    return keys


class Candidate(TypedDict):
    word: str
    score: float
    pinyin: List[str]


# 使用 Beam Search 生成候选词，拼音拆分基于候选词
def beam_search_generate(
    pinyin_input: str, beam_width: int = 8, top_k: int = 10
) -> List[Candidate]:
    """
    使用 Beam Search 生成候选词，逐步匹配拼音。

    :param pinyin_input: 用户输入的拼音
    :param beam_width: Beam Search 的宽度
    :param top_k: 最终返回的候选词数量
    :return: 候选词列表
    """
    prompt = get_context()
    inputs = tokenizer(prompt, return_tensors="pt")

    # 初始化 Beam Search 队列
    beam: List[Tuple[float, str, str, List[Tuple[str, float]], List[str]]] = [
        (1.0, "", pinyin_input, [], [])
    ]  # (prob, context, remaining_pinyin, token_tails, matched_pinyin)

    final_candidates: List[
        Tuple[float, str, List[str]]
    ] = []

    run_count = 0

    while beam:
        run_count += 1
        print(run_count)
        next_beam = []
        for prob, context, remaining_pinyin, token_tails, matched_pinyin in beam:
            if not remaining_pinyin:  # 如果拼音已经全部匹配完
                final_candidates.append((prob, context, matched_pinyin))
                continue

            if token_tails:  # 如果有未处理的 token_tail
                for (
                    token_tail,
                    token_tail_prob,
                ) in token_tails:  # 遍历所有未处理的 token_tail
                    token = token_tail[0]  # 取出 token_tail 的第一个字
                    new_token_tail = token_tail[1:]  # 更新 token_tail
                    new_prob = token_tail_prob  # 使用 token_tail 的概率
                    new_context = context + token

                    # 检查拼音匹配
                    token_pinyin = lazy_pinyin(token)
                    if remaining_pinyin.startswith(token_pinyin[0]):
                        print(context, token)
                        new_remaining_pinyin = remaining_pinyin[len(token_pinyin[0]) :]
                        add_to_beam(
                            next_beam,
                            new_prob,
                            new_context,
                            new_remaining_pinyin,
                            new_token_tail,
                            token_tail_prob,
                            matched_pinyin + [token_pinyin[0]],
                        )
                continue

            inputs = tokenizer(prompt + context, return_tensors="pt")
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits[:, -1, :]

            probabilities = torch.softmax(logits, dim=-1)
            tk = logits.size(-1)  # 设置为可能的上限
            top_probs, top_indices = torch.topk(probabilities, tk)

            for i in range(tk):
                if len(next_beam) >= 10:  # 如果 next_beam 的容量达到 100，终止遍历
                    break

                token_id = top_indices[0, i].item()
                token = tokenizer.decode([token_id])
                if len(token) < 1:
                    continue
                token_prob = top_probs[0, i].item()
                new_prob = prob * token_prob  # 累乘概率
                new_context = context + token[0]
                new_token_tail = token[1:]  # 提取 token 的剩余部分

                # 检查拼音匹配
                token_pinyin = lazy_pinyin(token)
                if remaining_pinyin.startswith(token_pinyin[0]):
                    new_remaining_pinyin = remaining_pinyin[len(token_pinyin[0]) :]
                    add_to_beam(
                        next_beam,
                        new_prob,
                        new_context,
                        new_remaining_pinyin,
                        new_token_tail,
                        token_prob,
                        matched_pinyin + [token_pinyin[0]],
                    )

        # 按概率排序并截取 Beam Width 个最优结果
        next_beam.sort(key=lambda x: x[0], reverse=True)  # 按概率从高到低排序
        beam = next_beam[:beam_width]

    # 提取最终候选词
    candidates: List[Candidate] = []
    for prob, tokens, matched_pinyin in final_candidates:
        candidates.append({"word": tokens, "score": prob, "pinyin": matched_pinyin})

    # 按得分排序并返回 Top-K
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]


def commit(text: str):
    user_context.append(text)


def get_context():
    return pre_context + "".join(user_context)


def clear_commit():
    user_context.clear()


def add_to_beam(
    next_beam: List[Tuple[float, str, str, List[Tuple[str, float]], List[str]]],
    new_prob: float,
    new_context: str,
    new_remaining_pinyin: str,
    new_token_tail: str,
    token_prob: float,
    new_matched_pinyin: List[str],
):
    """
    将新路径添加到 Beam 中，检查是否存在相同的 context，
    如果存在且新路径的概率更大，则覆盖旧路径。
    如果存在 tail 的选项，合并同样首字的 tail。
    """
    for i, (
        existing_prob,
        existing_context,
        existing_remaining_pinyin,
        existing_token_tails,
        existing_matched_pinyin,
    ) in enumerate(next_beam):
        if existing_context == new_context:
            if new_token_tail:
                # 合并 tail
                if existing_token_tails:
                    existing_token_tails.append((new_token_tail, token_prob))
                else:
                    next_beam[i] = (
                        existing_prob,
                        existing_context,
                        existing_remaining_pinyin,
                        [(new_token_tail, token_prob)],
                        existing_matched_pinyin,
                    )
            elif new_prob > existing_prob:  # 如果新路径的概率更大，替换
                next_beam[i] = (
                    new_prob,
                    new_context,
                    new_remaining_pinyin,
                    [(new_token_tail, token_prob)] if new_token_tail else [],
                    new_matched_pinyin,
                )
            return

    # 如果不存在相同的 context，直接添加
    next_beam.append(
        (
            new_prob,
            new_context,
            new_remaining_pinyin,
            [(new_token_tail, token_prob)] if new_token_tail else [],
            new_matched_pinyin,
        )
    )


# API: 获取候选词
@app.route("/candidates", methods=["POST"])
def get_candidates() -> Dict[str, List[Dict[str, float]]]:
    data = request.json
    keys: str = data.get("keys", "")  # type: ignore

    pinyin_input = keys_to_pinyin(keys)
    candidates = beam_search_generate(pinyin_input)

    return jsonify({"candidates": candidates})  # type: ignore


# API: 提交文字
@app.route("/commit", methods=["POST"])
def commit_text() -> Dict[str, List[str]]:
    data = request.json
    text = data.get("text", "")  # type: ignore

    if not text:
        return jsonify({"error": "No text provided"}), 400  # type: ignore

    commit(text)

    return jsonify({"message": "Text committed successfully", "context": user_context})  # type: ignore


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

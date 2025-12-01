# ai ime

llm 驱动的输入法。目前支持拼音。

记录用户历史输入。让 llm 预测下一个词，再用拼音筛选。

太小的模型预测不强，太大的模型性能不好。但这里还是用了 qwen3-0.6b

目前作为云输入，还没有与具体输入法引擎结合在一起。

## 运行

### 仅测试

```shell
uv run test_engine.py
```

### 开启服务器

```shell
uv run server.py
```

可以发送按键让引擎分析

```shell
curl --request POST \
  --url http://127.0.0.1:5000/candidates \
  --header 'content-type: application/json' \
  --data '{
  "keys": "nihaoshijie",
  "pre_str": ""
}'
```

返回

```json
{
    "candidates": [
        {
            "pinyin": ["ni", "hao", "shi", "jie"],
            "score": 1.1879427571978856e-13,
            "word": "你好世界"
        }
    ]
}
```

在长句中，只选择前面部分的词，就附带在`pre_str`

选好词后，发送，将作为上下文记录

```shell
curl --request POST \
  --url http://127.0.0.1:5000/commit \
  --header 'content-type: application/json' \
  --data '{
  "text": "你好世界"
}'
```

## 现状

使用`transformers`库，不是专门用来推理的，会很慢，一个字一秒左右。但按照这样的模型大小和 token 长度，在 ollama 下，整句半秒应该是可以的，所以之后可能考虑更换推理库。ollama 还不支持给出下一个候选千个以上的候选，可能要用`llama.cpp`。

还没有设计模糊音、双拼等。

如何与真正的输入法结合起来？也许要用 rime 吧。

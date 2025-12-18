# LIME 项目技术分析报告

## 一、项目概述

**LIME** 是一个基于大语言模型 (LLM) 驱动的中文拼音输入法引擎。项目的核心创新在于：**利用用户输入的拼音来引导 LLM 的文本生成采样过程**，而非传统的词频统计方法。

### 核心理念

传统 LLM 文本生成采用自回归方式预测下一个 token，然后通过采样选择。LIME 将这个采样过程与用户拼音输入结合，用拼音来过滤和筛选候选词，实现智能联想输入。

---

## 二、技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        RIME 输入法前端                           │
│                    (llm_pinyin.lua + luasocket)                 │
└─────────────────────────────────────────────────────────────────┘
                                │ HTTP API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Hono HTTP 服务器                            │
│                        (server.ts)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ /candidates │  │   /commit   │  │      /userdata          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       核心引擎 (main.ts)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   LLM 推理      │  │   拼音过滤器    │  │   上下文管理    │  │
│  │ (node-llama-cpp)│  │ (token_pinyin)  │  │  (sequence)     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      拼音处理模块 (key_map/)                     │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │ keys_to_pinyin│  │ fuzzy_pinyin  │  │    shuangpin      │   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **运行时** | Deno.js | 现代 TypeScript/JavaScript 运行时 |
| **Web框架** | Hono | 轻量级高性能 Web 框架 |
| **LLM推理** | node-llama-cpp | llama.cpp 的 Node.js 绑定 |
| **拼音处理** | pinyin-pro | 汉字转拼音库 |
| **模型** | Qwen3-0.6B-IQ4_XS | 通义千问小型量化模型 |
| **前端** | RIME | 开源输入法框架 |

---

## 三、核心模块分析

### 3.1 LLM 推理引擎 (`main.ts`)

#### 3.1.1 模型初始化

```typescript
const llama = await getLlama({
    gpu: false,
});

const modelPath = "../Qwen3-0.6B-GGUF/Qwen3-0.6B-IQ4_XS.gguf";

const model = await llama.loadModel({
    modelPath: path.join(__dirname, modelPath),
});
const context = await model.createContext({
    contextSize: { max: 4096 },
});
const sequence = context.getSequence();
```

- **模型**: 使用 Qwen3-0.6B 的 IQ4_XS 量化版本，约 300MB
- **上下文**: 最大 4096 tokens
- **GPU**: 默认关闭，使用 CPU 推理

#### 3.1.2 Token-拼音映射索引

```typescript
const token_pinyin_map: Map<number, Array<Array<string>>> = new Map();
const first_pinyin_token = new Map<string, Set<number>>();
```

系统在启动时构建两个关键索引：
- **`token_pinyin_map`**: token ID → 该 token 对应的所有可能拼音组合
- **`first_pinyin_token`**: 首字拼音 → 以该拼音开头的所有 token ID 集合

这种索引设计实现了 **O(1)** 的拼音过滤查找。

#### 3.1.3 核心推理函数 `single_ci()`

```typescript
export async function single_ci(
    pinyin_input: PinyinL,
    op?: ThinkOption,
): Promise<Result> {
    if (pinyin_input.length === 0 || pinyin_input[0].length === 0) {
        return { candidates: [] };
    }

    if (!last_result) {
        return { candidates: [] };
    }

    const c: Candidate[] = [];
    await modelEvalLock.acquire();
    // ... 过滤和推理逻辑
}
```

**工作流程**:
1. 获取 LLM 对下一个 token 的概率分布 (`last_result`)
2. 使用 `filterByPinyin()` 过滤出拼音匹配的 token
3. 对高置信度候选 (>0.7) 进行多步推理，生成长词组
4. 按词长排序返回候选列表

#### 3.1.4 多步推理（长词生成）

```typescript
if (rmpy.length > 0) {
    if (token_prob > 0.7) {
        if (thinkCount > 1) break;
        thinkCount++;
        // ... 进行多步推理生成长词组
        for (let _i = 0; _i < Math.min(rmpyx.length, 4); _i++) {
            const next = await sequence.controlledEvaluate([...]);
            // 继续匹配下一个拼音
        }
    }
}
```

当首字置信度 >0.7 时，系统会继续推理后续字符，最多推理 4 步，生成完整词组。

### 3.2 HTTP 服务层 (`server.ts`)

#### 3.2.1 API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/candidates` | GET/POST | 获取候选词列表 |
| `/commit` | GET/POST | 提交选中的文字 |
| `/userdata` | GET | 获取用户数据 |
| `/debug` | GET | 调试页面 |

#### 3.2.2 认证机制

```typescript
app.use(
    "/*",
    bearerAuth({
        verifyToken: (t) => {
            return verifyKey(t);
        },
    }),
);
```

使用 Bearer Token 认证，密钥通过 SHA-256 哈希存储在 `key.txt` 中。

#### 3.2.3 拼音配置

```typescript
const pinyinConfig: PinyinToKeyOptions = {
    shuangpin: false,
    fuzzy: {
        initial: {
            c: "ch", z: "zh", s: "sh",
            ch: "c", zh: "z", sh: "s",
        },
        final: {
            an: "ang", ang: "an",
            en: "eng", eng: "en",
            in: "ing", ing: "in",
            uan: "uang", uang: "uan",
        },
    },
};
```

支持：
- **模糊音**: 平翘舌、前后鼻音
- **双拼**: 自然码方案（可配置开关）

### 3.3 拼音处理模块 (`key_map/pinyin/`)

#### 3.3.1 键盘输入转拼音 (`keys_to_pinyin.ts`)

```typescript
export function keys_to_pinyin(keys: string, op?: PinyinToKeyOptions): PinyinL {
    const l: PinyinL = [];
    let k = keys;
    const split_key = "'";
    // ... 匹配逻辑
}
```

**功能**:
- 将连续按键序列解析为拼音序列
- 支持 `'` 分隔符手动分词
- 支持不完整拼音的模糊匹配

**返回类型** `PinyinL`:
```typescript
type PinyinL = Array<Array<PinyinAndKey>>;
// 每个位置可能有多个候选拼音（模糊音、不完整输入）
```

#### 3.3.2 双拼映射 (`shuangpin.ts`)

```typescript
export function generate_shuang_pinyin(pinyin_k_l: Array<string>) {
    const sm_map = { zh: "v", ch: "i", sh: "u" };
    const ym_map = {
        iu: "q", ia: "w", ua: "w", e: "e", uan: "r",
        // ... 完整映射
    };
    // 生成双拼到全拼的映射表
}
```

实现了**自然码双拼**方案，将两键映射为完整拼音。

#### 3.3.3 模糊音处理 (`fuzzy_pinyin.ts`)

```typescript
export function generate_fuzzy_pinyin(
    pinyin: string,
    config: FuzzyPinyinConfig = fuzzyPinyinConfig,
) {
    const fuzzy_variants = new Set<string>();
    fuzzy_variants.add(pinyin);
    const [initial, final] = spilt_pinyin(pinyin);
    // 生成所有模糊音变体
}
```

根据配置生成拼音的所有模糊变体，扩大匹配范围。

### 3.4 密钥管理 (`key.ts`)

```typescript
async function hashKey(key: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(key);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    // 转换为十六进制字符串
}
```

**安全设计**:
- 密钥使用 SHA-256 哈希后存储
- 原始密钥不保存，只保存哈希值
- 支持多密钥（每行一个哈希）

### 3.5 RIME 集成 (`rime/`)

#### 3.5.1 Schema 配置 (`llm.schema.yaml`)

```yaml
translators:
    - lua_translator@*llm_pinyin*translator
    - punct_translator
```

使用 Lua 翻译器作为核心，通过 HTTP 调用后端服务。

#### 3.5.2 Lua 客户端 (`llm_pinyin.lua`)

```lua
function translator.func(input, seg, env)
  -- 1. 发送已选文字到 /commit 更新上下文
  -- 2. 发送当前输入到 /candidates 获取候选
  -- 3. 构造 Candidate 对象返回给 RIME
end
```

**通信流程**:
1. 用户按键 → RIME 调用 `translator.func()`
2. Lua 通过 luasocket 发送 HTTP 请求
3. 后端返回候选词 JSON
4. Lua 解析并构造 RIME Candidate 对象

---

## 四、数据流分析

### 4.1 候选词生成流程

```
用户输入: "nihaoshijie"
         │
         ▼
┌─────────────────────────────────────┐
│ keys_to_pinyin() 解析              │
│ → [["ni"], ["hao"], ["shi"], ["jie"]]│
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ filterByPinyin() 过滤              │
│ 从 LLM 概率分布中筛选匹配拼音的 token │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 多步推理（高置信度时）              │
│ 生成 "你好世界" 等长词组            │
└─────────────────────────────────────┘
         │
         ▼
返回: { candidates: [{ word: "你好世界", score: 0.xxx, ... }] }
```

### 4.2 上下文管理

```typescript
export function commit(text: string, update = false, newT = true) {
    // 1. 处理增量更新逻辑
    // 2. 添加用户词
    // 3. 更新 LLM 上下文序列
    // 4. 预计算下一个 token 的概率分布
}
```

**特点**:
- 支持增量更新 (`update=true`)
- 支持新句子开始 (`newT=true`)
- 自动学习用户词 (`add_user_word()`)

---

## 五、性能优化策略

### 5.1 预计算机制

```typescript
sequence
    .controlledEvaluate([
        ...pre,
        [last, { generateNext: { probabilities: true } }],
    ])
    .then((res) => {
        last_result = res.at(-1)?.next.probabilities;
        release();
    });
```

在用户确认选词后，**立即预计算**下一个位置的概率分布，减少用户等待时间。

### 5.2 索引优化

```typescript
const ftokenid = new Set<number>();
for (const firstPinyin of pinyin_input[0]) {
    const s = first_pinyin_token.get(firstPinyin.py) ?? new Set();
    for (const tokenid of s) ftokenid.add(tokenid);
}
```

通过首字拼音索引，将候选过滤从 O(n) 降低到 O(k)，其中 k << n。

### 5.3 并发控制

```typescript
class Lock {
    pm: Promise<void> | null = null;
    async acquire() { if (this.pm) await this.pm; }
    lock() {
        const p = Promise.withResolvers<void>();
        this.pm = p.promise;
        return p.resolve;
    }
}
```

使用简单的 Promise 锁确保模型推理的串行执行，避免并发冲突。

---

## 六、项目结构总结

```
lime/
├── main.ts              # 核心引擎：LLM推理、拼音过滤、上下文管理
├── server.ts            # HTTP服务：API端点、认证
├── key.ts               # 密钥管理：生成、验证
├── key_map/
│   ├── pinyin/
│   │   ├── keys_to_pinyin.ts   # 按键→拼音转换
│   │   ├── all_pinyin.ts       # 完整拼音表
│   │   ├── fuzzy_pinyin.ts     # 模糊音处理
│   │   ├── shuangpin.ts        # 双拼映射
│   │   ├── split_pinyin.ts     # 声母韵母分离
│   │   └── gen_zi_pinyin.ts    # 汉字→拼音字典
│   └── rime_dict.ts            # RIME词典解析
├── utils/
│   ├── pinyin_in_pinyin.ts     # 拼音匹配算法
│   └── obj.ts                  # 工具函数
├── rime/
│   ├── llm.schema.yaml         # RIME输入法配置
│   └── lua/
│       ├── llm_pinyin.lua      # RIME-后端通信
│       └── json.lua            # JSON解析库
├── assets/pinyin/              # 拼音词典数据
└── test/                       # 测试文件
```

---

## 七、技术亮点与创新

1. **LLM 驱动的输入法**: 首创性地将 LLM 的 token 概率分布与拼音输入结合
2. **增量上下文**: 支持实时更新上下文，提供连贯的联想
3. **多步推理**: 高置信度时自动生成长词组
4. **用户词学习**: 自动记录用户输入的词组
5. **模块化设计**: 拼音处理、LLM推理、HTTP服务清晰分离

---

## 八、已知限制

1. **不支持长句输入**: 需要中途选择来组句
2. **无持久化**: 服务器重启后丢失用户数据
3. **输入速度**: 输入太快可能漏字母
4. **依赖外部模型**: 需要单独下载 Qwen3 模型文件

---

## 九、总结

LIME 是一个创新性的 LLM 驱动拼音输入法项目，通过将大语言模型的文本生成能力与传统拼音输入结合，实现了智能化的中文输入体验。项目架构清晰，代码质量较高，具有良好的可扩展性。

---

*报告生成时间: 2024年12月*

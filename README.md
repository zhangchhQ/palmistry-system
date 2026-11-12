# 观掌 · Palmistry System

**把「看相」写进代码，把「凭什么」留在答案里。**

观掌是一场 **传统文化 × AI** 的实验：把掌纹形态整理成可查的图谱，把组合条件写成能跑的规则，再让 AI 把解释讲成人话。

从一条线在哪里开始，到两条线是否真的相接，每个判断都能回到具体观察、条件与出处。你可以查图例、跑规则、追问依据，也可以把它作为 Codex 的项目 Skill 使用。

![Version](https://img.shields.io/badge/version-0.3.0-6C5CE7?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square)
![Runtime](https://img.shields.io/badge/runtime-standard_library-2E8B57?style=flat-square)
![Tests](https://img.shields.io/badge/synthetic_tests-71-4C9A2A?style=flat-square)

| 形态索引 | 可执行规则 | 组合条件 | 合成行为测试 |
|---:|---:|---:|---:|
| **514 条** | **24 条** | **6 组** | **71 项通过** |

## 一张掌图，怎样走到一段解释？

```text
手照 + 本人左右手标注
        ↓ 人工或多模态模型观察
位置、起止、走向、连接、可见性
        ↓ Python 核心核验
术语消歧 → 形态资格 → 组合绑定
        ↓
白话解读 + 可追溯依据
```

**当前 CLI 接收结构化观察；照片由人工或多模态模型先看。** Python 核心负责核对定义和连接，项目尚未接入自动细掌纹检测器。

- **形态有定义。** 先核位置、起止与连接，再决定名称；横纹穿过、真正空缺、前后搭接分别处理。
- **组合有条件。** 同图多条候选线分开绑定，太阳线具体接在哪一条，需要说清。组合的各项前提必须一起成立。
- **解释有来路。** 日常读白话，复核时查看规则、证据与来源。同名异义、图文冲突和流派差别都保留记录。
- **运行在本地。** 核心只用 Python 标准库，默认 stdin → stdout，不调用网络、不写个人档案。

## 先跑一次

需要 **Python 3.11+**。在仓库根目录运行，无需安装运行时依赖：

```sh
git clone https://github.com/zhangchhQ/palmistry-system.git
cd palmistry-system
python3 -m palmistry analyze examples/synthetic-cooperation.json
```

示例使用完全合成的观察数据。它展示的组合是：月丘起的玉柱线，与从同一条玉柱线发出的太阳线相接。

同一份输入，也可以展开查看依据：

```sh
python3 -m palmistry analyze examples/synthetic-cooperation.json --audit
```

要接入自己的观察流程，完整字段与连接示例见[观察合同](docs/observation-contract.md)。个人输入可经 stdin 临时传入：

```sh
python3 -m palmistry analyze --format json < observation.json
```

## 给 AI 接上一套手相工作流

从仓库目录使用 Codex 时，可显式调用[观掌 Skill](.agents/skills/palmistry-system/SKILL.md)：

> 使用 $palmistry-system 看这两张手照。第一张左手，第二张右手，惯用右手。先核对形态，再给白话的传统象征解读，原理自然带入，重点加粗。

Skill 把看图、规则核验与表达接起来：本人标注的手别优先；看清的形态进入核验；明确的连接形成组合；解释保留来源与前提。

**一条清楚的形态、一个成立的组合，都值得给出一段讲得明白的理由。**

## 图谱、古名、卦象，都能查

```sh
# 同一个古名，在不同章节可能指不同掌线
python3 -m palmistry lookup 智慧纹
python3 -m palmistry lookup 智慧纹 --context appendix_one

# 按编号定位图形与条件
python3 -m palmistry form A1-27
python3 -m palmistry form E104

# 查看完整作者案例、原课学习卡及传统主题
python3 -m palmistry study H01
python3 -m palmistry study 职业

# 六爻爻值按初爻至上爻排列
python3 -m palmistry cast 9 7 6 7 8 8
```

内置八卦、六十四卦上下卦组合、明确爻值的变爻计算，以及五行相生相克。掌纹与卦象的传统类比另有说明，计算与象征解释分别处理。见[易学基础](docs/foundations.md)。

## 现在已经做到哪一步？

- **516 个编号图组 → 514 条形态记录。** 覆盖正文164例、附录一72式、附录二174图等。这里统计图录，图组可含子图与重绘；不是516个真人样本。
- **24 条规则、6 组组合、71 项合成行为测试。** 检查手别修正、位置定义、多候选绑定、模糊输入、符号边界和易学计算等行为。
- **2 份历史作者案例、2 个原课单元的完整可用字幕。** 用于研究整手配合、反例与表达；事后回忆、字幕阅读与视频观看分别记录。
- **6 个传统主题可查。** 性情、职业、健康、婚育、富贵及流年，保留作者主张、适用条件与冲突。

项目用于传统文化研究、规则实验和象征解读。自动细掌纹识别、真人独立盲测与预测准确性尚未验证，也没有训练模型权重；不将手部外观用于个人诊断、人格测量或具体年份、收入预测。详细范围见[验收记录](VALIDATION.md)。

## 从哪里继续看？

| 想看什么 | 入口 |
|---|---|
| 规则怎样执行、组合怎样绑定 | [判断核心](palmistry/engine.py) |
| 输入怎样定义、哪些条件必须明确 | [观察合同](docs/observation-contract.md) |
| 图录怎样从整书逐项转化 | [图例转化](docs/figure-conversion.md) |
| 完整案例与原课实际读了哪些 | [案例与课程](docs/cases-and-lessons.md) |
| 解释怎样自然带入原理 | [表达规范](docs/reading-language.md) |
| 怎样继续验证与改进 | [学习闭环](docs/learning-loop.md) |

<details>
<summary>更多资料与实现</summary>

- [观察资格门](palmistry/observations.py)
- [规则、术语与冲突](palmistry/data/knowledge.json)
- [形态目录](palmistry/data/figure_forms.json)
- [历史主题对照](docs/traditional-claims.md)
- [来源与版本](palmistry/data/sources.json)
- [逐章覆盖](palmistry/data/coverage.json)
- [表达学习记录](docs/expression-study.md)
- [易学计算](palmistry/iching.py)

</details>

## 一起把它做得更扎实

欢迎带着**可复现的形态、明确的来源和有分量的反例**来提 Issue。输入示例请用合成观察 JSON，受版权保护的原图和个人隐私留在本地。

如果你也想看看，传统知识怎样变成一套可查、可跑、可迭代的 AI 工作流，**欢迎点一颗 ⭐ Star。**

原书扫描、OCR、课程字幕、课件与私人手照不随仓库分发。**当前尚未选择对外开源许可证**；公开可见与复用授权分开说明，详见[分发说明](LICENSE-NOTICE.md)。

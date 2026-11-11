# 观掌 · Palmistry System

把传统手相知识转成能执行、能复核、能改进的方法。当前版本 **0.3.0**，本地运行，无运行时第三方依赖。

## 这套系统实际做什么

先认清看到的形态，再处理术语、分歧和组合，最后写成大白话。内部保留来源和推导链，日常回答不逐段抄书。

```text
照片 + 本人左右手标注
  ↓ 多模态观察 / 人工核对（当前不包含自动掌纹检测器）
形态数据：位置、起止、连接、可见性
  ↓ 定义核验、规则匹配、同图组合、双手比较
传统象征主题 + 反向条件 + 白话解读
```

已实现：

- 本人标注优先。修正手别后重新计算全部观察归属，不沿用旧左右结论。
- 五条主线的位置核验、九辅线及整体形态词表；独立符号与主线围成区域分开。
- **24条可执行规则、6条组合语法、15条术语记录、9个区域映射、5组冲突记录**。这是当前可执行子集。
- 全书169个文件页均已看图，516个编号图组整理成514条形态记录，覆盖正文164例、附录一72式、附录二174图等。同名异义分别保留，局部扫描遮挡单列。
- 形态图录可按编号或关键词查询；少量满足位置条件的古名可自动映射。图录条目不自动等于吉凶规则。
- 八卦、六十四卦上下卦组合、明确爻值的变爻计算、五行相生相克。
- 陈氏掌纹与卦象的五组类比。类比不会产生动爻、月份或应期。
- 同图组合绑定具体观察，多个父线候选须用`origin_ref`指定连接；局部连续不外推全年或未来回报。
- 两份完整历史作者叙述、两个完整原作者短课单元的可用字幕及六个原书形态练习；五个传统主题加流年可独立查询。阅读与验证等级分别记录。
- 白话与审计两种输出；默认不存照片、输入或报告，不调用网络和收费API。

尚未实现：自动从照片中分割细掌纹、全部古图的自动识别、真人盲测及预测准确性验证。**阅读过整本书，不等于全书每一条断语均已程序化或验证。**逐章状态见[覆盖表](palmistry/data/coverage.json)。

## 快速使用

需要Python 3.11及以上。在仓库根目录运行，不必安装依赖：

```sh
python3 -m unittest discover -v
python3 -m palmistry analyze examples/synthetic-cooperation.json
python3 -m palmistry analyze examples/synthetic-cooperation.json --audit
python3 -m palmistry analyze --format json < observation.json
python3 -m palmistry lookup 智慧纹
python3 -m palmistry lookup 智慧纹 --context appendix_one
python3 -m palmistry form A1-27
python3 -m palmistry form E105
python3 -m palmistry form main:201
python3 -m palmistry study H01
python3 -m palmistry study 职业
python3 -m palmistry hexagram --lower 兑 --upper 震
python3 -m palmistry cast 9 7 6 7 8 8
python3 -m palmistry analogy heart --variant 观
python3 -m palmistry elements 木 土
```

示例完全合成，不对应任何真实手照或个人。`cast`输入按初爻至上爻排列；不会猜硬币正反的计值，也不会替用户随机摇卦。纳甲月日继续由另行核验的工具负责。

## 在Codex里使用

从仓库目录启动时，使用[项目技能](.agents/skills/palmistry-system/SKILL.md)：

> 使用 $palmistry-system 看这两张手照。第一张左手，第二张右手，惯用右手。先核对形态，再给白话的传统象征解读。

技能把观察候选转成合同数据，运行核心后再写解读。涉及边缘、闭合、起点的争议，才回查原图或源页。已经确认的规则直接运用，不能用“查到一个类似图”代替判断。

## 资料与代码

| 内容 | 位置 |
|---|---|
| 判断核心 | [engine.py](palmistry/engine.py) |
| 观察合同与定义门 | [observations.py](palmistry/observations.py) |
| 规则、冲突、术语 | [knowledge.json](palmistry/data/knowledge.json) |
| 易学计算 | [iching.py](palmistry/iching.py) |
| 易学基础与流派边界 | [foundations.md](docs/foundations.md) |
| 输入与识图要求 | [observation-contract.md](docs/observation-contract.md) |
| 全书图例转化及计数口径 | [figure-conversion.md](docs/figure-conversion.md) |
| 白话表达学习及原创示范 | [expression-study.md](docs/expression-study.md) |
| 完整案例与原课 | [cases-and-lessons.md](docs/cases-and-lessons.md) |
| 原理自然带入的表达 | [reading-language.md](docs/reading-language.md) |
| 书中六主题对照 | [traditional-claims.md](docs/traditional-claims.md) |
| 怎样提升实际水平 | [learning-loop.md](docs/learning-loop.md) |
| 来源及版本 | [sources.json](palmistry/data/sources.json) |
| 本次验收 | [VALIDATION.md](VALIDATION.md) |

## 资料边界

原书扫描、OCR、图版和个人手照保留在用户自己的本地资料区，不属于仓库发布内容。仓库仅放原创代码、方法摘要、来源定位和合成测试。第三方手部模型尚未安装，亦未训练或微调模型。对外许可证尚未选择，见[分发说明](LICENSE-NOTICE.md)。

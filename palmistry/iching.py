"""Explicit lower-to-upper line arithmetic; never invent a palm-derived cast."""

from itertools import product

TRIGRAMS = {
    "乾": {"bits": (1, 1, 1), "image": "天", "quality": "健", "direction": "西北", "element": "金"},
    "兑": {"bits": (1, 1, 0), "image": "泽", "quality": "悦", "direction": "西", "element": "金"},
    "离": {"bits": (1, 0, 1), "image": "火", "quality": "丽", "direction": "南", "element": "火"},
    "震": {"bits": (1, 0, 0), "image": "雷", "quality": "动", "direction": "东", "element": "木"},
    "巽": {"bits": (0, 1, 1), "image": "风", "quality": "入", "direction": "东南", "element": "木"},
    "坎": {"bits": (0, 1, 0), "image": "水", "quality": "陷", "direction": "北", "element": "水"},
    "艮": {"bits": (0, 0, 1), "image": "山", "quality": "止", "direction": "东北", "element": "土"},
    "坤": {"bits": (0, 0, 0), "image": "地", "quality": "顺", "direction": "西南", "element": "土"},
}
ORDER = tuple(TRIGRAMS)
# Rows = upper trigram; columns = lower trigram. Names/numbers, not quoted commentary.
MATRIX = (
    ((1,"乾"),(10,"履"),(13,"同人"),(25,"无妄"),(44,"姤"),(6,"讼"),(33,"遁"),(12,"否")),
    ((43,"夬"),(58,"兑"),(49,"革"),(17,"随"),(28,"大过"),(47,"困"),(31,"咸"),(45,"萃")),
    ((14,"大有"),(38,"睽"),(30,"离"),(21,"噬嗑"),(50,"鼎"),(64,"未济"),(56,"旅"),(35,"晋")),
    ((34,"大壮"),(54,"归妹"),(55,"丰"),(51,"震"),(32,"恒"),(40,"解"),(62,"小过"),(16,"豫")),
    ((9,"小畜"),(61,"中孚"),(37,"家人"),(42,"益"),(57,"巽"),(59,"涣"),(53,"渐"),(20,"观")),
    ((5,"需"),(60,"节"),(63,"既济"),(3,"屯"),(48,"井"),(29,"坎"),(39,"蹇"),(8,"比")),
    ((26,"大畜"),(41,"损"),(22,"贲"),(27,"颐"),(18,"蛊"),(4,"蒙"),(52,"艮"),(23,"剥")),
    ((11,"泰"),(19,"临"),(36,"明夷"),(24,"复"),(46,"升"),(7,"师"),(15,"谦"),(2,"坤")),
)
GENERATES = dict(zip("木火土金水", "火土金水木"))
CONTROLS = {"木":"土", "土":"水", "水":"火", "火":"金", "金":"木"}


def compose(lower: str, upper: str) -> dict:
    if lower not in TRIGRAMS or upper not in TRIGRAMS:
        raise ValueError("上下卦必须使用乾兑离震巽坎艮坤之一")
    number, name = MATRIX[ORDER.index(upper)][ORDER.index(lower)]
    return {"number": number, "name": name, "lower": lower, "upper": upper,
            "lines_bottom_up": list(TRIGRAMS[lower]["bits"] + TRIGRAMS[upper]["bits"]),
            "source_id": "zhouyi-table"}


def from_bits(bits) -> dict:
    if not isinstance(bits, (list, tuple)) or len(bits) != 6 or any(type(b) is not int or b not in (0, 1) for b in bits):
        raise ValueError("需要六个自下而上的0/1整数；不能用布尔值代替")
    reverse = {v["bits"]: k for k, v in TRIGRAMS.items()}
    return compose(reverse[tuple(bits[:3])], reverse[tuple(bits[3:])])


def change(bits, moving) -> dict:
    original = from_bits(bits)
    if not isinstance(moving, (list, tuple)) or any(type(i) is not int or i not in range(1, 7) for i in moving):
        raise ValueError("动爻必须为1至6的整数，初爻为1")
    if len(set(moving)) != len(moving):
        raise ValueError("动爻不能重复")
    changed = list(bits)
    for i in moving:
        changed[i - 1] ^= 1
    return {"method": "explicit-line-change", "original": original,
            "moving_bottom_up": sorted(moving), "changed": from_bits(changed)}


def cast(values) -> dict:
    if not isinstance(values, (list, tuple)) or len(values) != 6 or any(type(v) is not int or v not in (6, 7, 8, 9) for v in values):
        raise ValueError("需要六个自下而上的爻值6/7/8/9；不自动猜硬币正反计值")
    result = change([v % 2 for v in values], [i + 1 for i, v in enumerate(values) if v in (6, 9)])
    return {**result, "method": "provided-six-line-values", "raw_values_bottom_up": list(values),
            "randomness": "none-generated", "month_day_najia": "not-calculated"}


def element_relation(a, b) -> str:
    if a not in GENERATES or b not in GENERATES:
        raise ValueError("五行须为木火土金水之一")
    if a == b:
        return "同类"
    if GENERATES[a] == b:
        return "我生"
    if GENERATES[b] == a:
        return "生我"
    if CONTROLS[a] == b:
        return "我克"
    return "克我"


def all_hexagrams():
    return [compose(lower, upper) for upper, lower in product(ORDER, repeat=2)]


def palm_analogy(line: str, variant: str | None = None) -> dict:
    # Source-specific analogies, not a universal palm-to-casting algorithm.
    choices = {"life": ("震", "坎"), "fate": ("离", "坎"),
               "head": ("兑", "震"), "sun": ("坤", "坎")}
    if line == "heart":
        if variant not in ("观", "晋"):
            raise ValueError("原书天纹有观/晋两支；必须明确选择，不能默认合并")
        lower, upper = "坤", "巽" if variant == "观" else "离"
    elif line in choices:
        if variant is not None:
            raise ValueError("此类比没有该变体")
        lower, upper = choices[line]
    else:
        raise ValueError("此书未给出该线的已核类比")
    return {"method": "chen-palm-analogy", "hexagram": compose(lower, upper),
            "moving_lines": None, "cast": False, "source_id": "chen-1994",
            "locator": "PDF8—12 前置论文", "timing": "not-derived"}

"""Plain Chinese output from qualified observations; audit detail is opt-in."""

NAMES = {"life":"生命线", "head":"头脑线", "heart":"感情线", "fate":"玉柱线（事业线）", "sun":"太阳线",
         "triangle":"独立三角形", "square":"独立四方形", "island":"线内岛形", "cross":"十字形", "star":"星形"}
HANDS = {"left":"左手", "right":"右手", "unknown":"手别待确认"}
WORDS = {"life_line":"生命线", "moon_region":"小指侧下部（月丘）", "fate_line":"玉柱线", "head_line":"头脑线", "heart_line":"感情线",
         "wrist":"掌根", "palm_center":"掌中", "thumb_index":"拇指与食指之间", "middle_base":"中指根下", "middle_finger":"中指",
         "ring_base":"无名指根下", "little_base":"小指根下", "index_base":"食指根下", "index_middle_gap":"食指与中指之间",
         "descending_outer":"向小指侧下斜", "transverse":"横向展开", "continuous":"当前清楚部分连续", "gap":"有已确认的间断", "chain":"链状"}


def describe(row):
    g = row["geometry"]
    parts = []
    for key, prefix in (("start", "起自"), ("end", "朝向"), ("direction", ""), ("continuity", "")):
        if g.get(key) in WORDS:
            parts.append(prefix + WORDS[g[key]])
    if g.get("path") == "around_thumb_ball":
        parts.append("绕拇指根部成弧")
    if g.get("double") is True:
        parts.append("可见两路并行")
    if g.get("upward_branch") is True:
        parts.append("有上行支线")
    if row["kind"] == "symbol":
        parts.append("短线独立成形" if g.get("independent") else "按位置与连接关系辨认")
    return "，".join(parts) or "形态已记录，细节见观察数据"


def render(result, audit=False):
    lines = []
    labels = "；".join(f"第{i}张为{HANDS[img['hand']]}" for i, img in enumerate(result["images"], 1))
    lines.append(labels + "。")
    selected, used_evidence, seen_themes = [], set(), set()
    for row in result["themes"]:
        if row["theme"] in seen_themes or used_evidence.intersection(row["evidence_ids"]):
            continue
        selected.append(row)
        used_evidence.update(row["evidence_ids"])
        seen_themes.add(row["theme"])
        if len(selected) == 3:
            break
    distinct = [r["theme"] for r in selected]
    visible_images = {r["image_id"] for r in selected}
    synthesis = next((c for c in result["combinations"] if c["image_id"] in visible_images), None)
    if synthesis:
        lines.append("按传统象征读法，" + synthesis["text"])
    elif distinct:
        lines.append("按传统象征读法，先抓住" + "、".join(distinct[:2]) + "这两层。" if len(distinct)>1 else "按传统象征读法，重点在"+distinct[0]+"这一层。")
    else:
        lines.append("目前没有足够清楚、位置相符的纹路，先保留形态观察。")
    displayed = set()
    for r in selected:
        if r["theme"] in displayed:
            continue
        displayed.add(r["theme"])
        if not synthesis or not set(r['evidence_ids']) <= set(synthesis['evidence_ids']):
            lines.append(f"\n**{r['theme']}**：{r['text']}")
        evidence = [o for o in result["observations"] if o["id"] in r["evidence_ids"]]
        lines.append("看到的依据：" + "；".join(f"{HANDS[o['hand']]}{NAMES.get(o['feature'],o['feature'])}{describe(o)}" for o in evidence) + "。")
        if len(displayed) == 3:
            break
    reasons = list(dict.fromkeys(x["reason"] for x in result["unknowns"]))
    if reasons:
        lines.append("\n还没看准的部分：" + "；".join(reasons[:3]) + "。")
    if result["comparisons"]:
        changed = [NAMES.get(c["feature"], c["feature"]) for c in result["comparisons"] if c["differences"]]
        lines.append("\n双手对照：" + ("、".join(changed) + "的已确认形态有差异，先保留差异，不倒推出具体经历。" if changed else "共有描述字段未见差异；缺失字段仍不作比较。"))
    if audit:
        lines.append("\n规则依据（供复核）：")
        for r in result["matches"]:
            lines.append(f"- {r['rule_id']} ← {','.join(r['evidence_ids'])}；{r['source']['id']} {r['source']['locator']}")
        lines.append("\n本结果使用输入的形态观察，未运行掌纹图像识别模型。")
    return "\n".join(lines)

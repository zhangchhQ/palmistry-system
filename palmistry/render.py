"""Plain Chinese output from qualified observations; audit detail is opt-in."""

NAMES = {"life":"生命线", "head":"头脑线", "heart":"感情线", "fate":"玉柱线（事业线）", "sun":"太阳线",
         "health":"健康线（传统名称）", "union":"结合线", "mars":"火星线", "attachment":"痴情线（传统名称）",
         "insurance":"保险线（传统名称）", "intuition":"直感线", "travel":"旅行线", "venus_girdle":"金星带", "mercury":"水星线",
         "triangle":"独立三角形", "square":"独立四方形", "island":"线内岛形", "cross":"十字形", "star":"星形"}
HANDS = {"left":"左手", "right":"右手", "unknown":"手别待确认"}
WORDS = {"life_line":"生命线", "moon_region":"小指侧下部（月丘）", "fate_line":"玉柱线", "head_line":"头脑线", "heart_line":"感情线",
         "wrist":"掌根", "palm_center":"掌中", "thumb_index":"拇指与食指之间", "middle_base":"中指根下", "middle_finger":"中指",
         "ring_base":"无名指根下", "little_base":"小指根下", "index_base":"食指根下", "index_middle_gap":"食指与中指之间",
         "descending_outer":"向小指侧下斜", "transverse":"横向展开", "continuous":"当前清楚部分连续", "gap":"有已确认的间断", "overlapping":"可见前后段搭接", "chain":"链状"}


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


def reading_sections(result):
    """Select grounded sections before wording; never fuse unrelated images or topics."""
    focus = result['focus']
    eligible = [r for r in result['matches'] if focus=='overall' or r['topic'] in {focus,'general'}]
    available = {r['image_id'] for r in eligible}
    dominant = result['dominant_hand']
    primary = next((i['id'] for i in result['images'] if i['id'] in available and i['hand']==dominant and dominant!='unknown'),None)
    if primary is None:
        primary = next((i['id'] for i in result['images'] if i['id'] in available),None)
    allowed = {r['rule_id'] for r in eligible if r['image_id']==primary}
    combinations = [c for c in result['combinations'] if c['image_id']==primary and set(c['requires'])<=allowed]
    sections, used = [], set()
    if combinations:
        c = combinations[0]
        sections.append({'kind':'combination','title':c.get('title','掌线组合'),'text':c['text'],
                         'evidence_ids':c['evidence_ids'],'image_id':primary,'combination_id':c['id']})
        used.update(c['evidence_ids'])
    for r in sorted(eligible,key=lambda x:(-x['priority'],x['rule_id'],x['evidence_ids'])):
        if r['image_id']!=primary or used.intersection(r['evidence_ids']):
            continue
        sections.append({'kind':'single-shape','title':r['theme'],'text':r['text'],
                         'evidence_ids':r['evidence_ids'],'image_id':primary,'rule_id':r['rule_id']})
        used.update(r['evidence_ids'])
        if len(sections)>=3:
            break
    return sections


def render(result, audit=False):
    labels = "；".join(f"第{i}张为{HANDS[img['hand']]}" for i, img in enumerate(result["images"], 1))
    lines = [labels + "。"]
    sections = reading_sections(result)
    if sections:
        lines.append('按传统象征读法：')
    else:
        lines.append('当前未认定足够清楚的掌线；可见部分按形态保留。')
    for section in sections:
        evidence = [o for o in result['observations'] if o['id'] in section['evidence_ids']]
        detail = '；'.join(f"{HANDS[o['hand']]}{NAMES.get(o['feature'],o['feature'])}{describe(o)}" for o in evidence)
        lines.append(f"\n**{section['title']}**。{detail}。{section['text']}")
    observed = {r['id']:r for r in result['observations']}
    reasons = []
    for item in result['unknowns']:
        row = observed.get(item.get('observation_id'))
        subject = f"{HANDS[row['hand']]}{NAMES.get(row['feature'],row['feature'])}" if row else '掌线连接' if item.get('combination_id') else '手别'
        message = subject + '：' + item['reason']
        if message not in reasons:
            reasons.append(message)
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

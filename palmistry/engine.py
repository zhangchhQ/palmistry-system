"""Evidence-first, deterministic symbolic rule composition."""

import json
from itertools import product
from importlib.resources import files

from .observations import qualify, resolve_hand, validate
from . import __version__
from .forms import search_forms, semantic_aliases


def knowledge():
    return json.loads(files("palmistry").joinpath("data/knowledge.json").read_text(encoding="utf-8"))


def lookup(term, context=None):
    data = knowledge()
    candidates = [v for v in data["terms"] if v["term"] == term and (context is None or v["context"] == context)]
    shapes=search_forms(term)
    status=("shape-only" if shapes else "unknown") if not candidates else "ambiguous" if len({v['meaning'] for v in candidates}) > 1 else "resolved"
    return {"term": term, "context": context, "status": status,
            "candidates": candidates, "shape_matches": shapes}


def _match(rule, row):
    if row["status"] != "recognized" or row["kind"] != rule["kind"] or row["feature"] != rule["feature"]:
        return False
    return all(row["geometry"].get(key) == value for key, value in rule["when"].items())


def _combinations(data, matches, observations, images):
    """Bind predicates to individual observations, then verify named connections."""
    result, gaps = [], []
    observed = {r['id']: r for r in observations}
    for img in images:
        same = [r for r in matches if r['image_id'] == img['id']]
        buckets = {}
        for row in same:
            buckets.setdefault(row['rule_id'], []).append(row)
        for definition in data['combinations']:
            required = definition['requires']
            if not all(key in buckets for key in required):
                continue
            found, reasons, seen = False, set(), set()
            for group in product(*(sorted(buckets[key], key=lambda r:r['evidence_ids']) for key in required)):
                bindings, valid = {}, True
                for match in group:
                    row = observed[match['evidence_ids'][0]]
                    if row['feature'] in bindings and bindings[row['feature']] != row['id']:
                        reasons.add('同类掌线的多个条件未落在同一条观察上')
                        valid = False
                        break
                    bindings[row['feature']] = row['id']
                if not valid:
                    continue
                links = []
                for obs_id in sorted(set(bindings.values())):
                    row = observed[obs_id]
                    start = row['geometry'].get('start', '')
                    parent_feature = start[:-5] if start.endswith('_line') else None
                    if parent_feature not in bindings:
                        continue
                    parent_id = bindings[parent_feature]
                    ref = row['geometry'].get('origin_ref')
                    candidates = [r for r in observations if r['image_id']==img['id'] and r['status']=='recognized' and r['kind']=='line' and r['feature']==parent_feature]
                    if (ref is not None and ref != parent_id) or (ref is None and (len(candidates)!=1 or candidates[0]['id']!=parent_id)):
                        reasons.add('连接对象有多个候选；须标明实际相接的掌线')
                        valid = False
                        break
                    links.append({'child':obs_id,'parent':parent_id,'basis':'explicit-origin-ref' if ref else 'unique-recognized-parent'})
                evidence = sorted(set(bindings.values()))
                if not valid or len(evidence) < definition['minimum_observations']:
                    continue
                signature = tuple(evidence)
                if signature in seen:
                    continue
                seen.add(signature)
                found = True
                result.append({**definition,'image_id':img['id'],'evidence_ids':evidence,'bindings':bindings,
                               'connections':links,'claim_type':'system-symbolic-synthesis',
                               'source_type':'original-combination-not-book-quote','scope':'observed-segments'})
            if not found and reasons:
                gaps.append({'image_id':img['id'],'combination_id':definition['id'],'reason':'；'.join(sorted(reasons))})
    result.sort(key=lambda c:(-len(c['requires']),c['image_id'],c['id'],c['evidence_ids']))
    return result, gaps


def analyze(payload):
    validate(payload)
    data = knowledge()
    rows, images, unknowns = [], [], []
    for img in payload["images"]:
        hand = resolve_hand(img)
        images.append({"id": img["id"], **hand, "view": img["view"], "quality": img["quality"], "comparable": img.get("comparable", False)})
        if hand["hand"] == "unknown":
            unknowns.append({"image_id": img["id"], "reason": "左右手尚未由本人标明；模型候选不提升为确认"})
        for obs in img["observations"]:
            status, reason = qualify(img, obs)
            row = {**obs, "image_id": img["id"], "hand": hand["hand"], "status": status, "reason": reason}
            rows.append(row)
            if status in {"unresolved", "enclosure"}:
                unknowns.append({"observation_id": obs["id"], "reason": reason})
    matches = []
    for rule in data["rules"]:
        for row in rows:
            if _match(rule, row):
                matches.append({"rule_id": rule["id"], "image_id": row["image_id"], "hand": row["hand"],
                                "evidence_ids": [row["id"]], "topic": rule["topic"], "theme": rule["theme"],
                                "text": rule["text"], "source": rule["source"], "priority": rule["priority"],
                                "claim_type": "traditional-symbolism"})
    combinations, combination_gaps = _combinations(data, matches, rows, images)
    unknowns.extend(combination_gaps)
    comparisons = []
    image_map = {img["id"]: img for img in images}
    for feature in sorted({r["feature"] for r in rows}):
        eligible = [r for r in rows if r["feature"] == feature and r["status"] == "recognized" and
                    r["hand"] != "unknown" and image_map[r["image_id"]]["comparable"] and
                    image_map[r["image_id"]]["quality"] == "clear" and image_map[r["image_id"]]["view"] == "palm"]
        left, right = [r for r in eligible if r["hand"] == "left"], [r for r in eligible if r["hand"] == "right"]
        if len(left) == len(right) == 1:
            a, b = left[0], right[0]
            shared = sorted(set(a["geometry"]) & set(b["geometry"]))
            differences = {k: {"left": a["geometry"][k], "right": b["geometry"][k]} for k in shared if a["geometry"][k] != b["geometry"][k]}
            comparisons.append({"feature": feature, "left_evidence": a["id"], "right_evidence": b["id"],
                                "differences": differences, "shared_fields": shared,
                                "chronology": "not-inferred"})
    focus = payload.get("focus", "overall")
    chosen = [r for r in matches if focus == "overall" or r["topic"] in {focus, "general"}]
    themes, seen = [], set()
    for row in sorted(chosen, key=lambda v: -v["priority"]):
        key = (row["theme"], row["image_id"])
        if key not in seen:
            themes.append(row)
            seen.add(key)
    present_rules = {r["rule_id"] for r in matches}
    gaps = [{"rule_id": r["id"], "requires": r["when"]} for r in data["rules"] if r["id"] not in present_rules]
    return {"version": __version__, "knowledge_version": data["version"], "method": "observation-led-palm-symbolism",
            "focus": focus, "dominant_hand": payload.get("dominant_hand", "unknown"), "images": images,
            "observations": rows, "matches": matches, "themes": themes, "combinations": combinations,
            "combination_gaps": combination_gaps,
            "shape_aliases": semantic_aliases(rows),
            "comparisons": comparisons, "unknowns": unknowns,
            "coverage": {"matched_rule_count": len(present_rules), "unmatched_rules": gaps,
                         "meaning": "规则命中情况，不是识图或预测准确率"},
            "capabilities": {"automatic_crease_detection": False, "image_labels_verified_by_pixels": False,
                             "medical_or_personality_inference": False, "forecast_accuracy_validated": False,
                             "calendar_timing_from_palm": False, "income_amount_from_palm": False},
            "storage": "none"}

"""Evidence-first, deterministic symbolic rule composition."""

import json
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
    combinations = []
    for img in images:
        same = [r for r in matches if r["image_id"] == img["id"]]
        by_id = {r["rule_id"]: r for r in same}
        for combination in data["combinations"]:
            if set(combination["requires"]) <= set(by_id):
                evidence = sorted({e for key in combination["requires"] for e in by_id[key]["evidence_ids"]})
                # Same observation cannot masquerade as multiple independently confirmed features.
                if len(evidence) < combination["minimum_observations"]:
                    continue
                combinations.append({**combination, "image_id": img["id"], "evidence_ids": evidence,
                                     "claim_type": "system-symbolic-synthesis", "source_type": "original-combination-not-book-quote"})
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
    combinations.sort(key=lambda c:-len(c["requires"]))
    return {"version": __version__, "knowledge_version": data["version"], "method": "observation-led-palm-symbolism",
            "focus": focus, "dominant_hand": payload.get("dominant_hand", "unknown"), "images": images,
            "observations": rows, "matches": matches, "themes": themes, "combinations": combinations,
            "shape_aliases": semantic_aliases(rows),
            "comparisons": comparisons, "unknowns": unknowns,
            "coverage": {"matched_rule_count": len(present_rules), "unmatched_rules": gaps,
                         "meaning": "规则命中情况，不是识图或预测准确率"},
            "capabilities": {"automatic_crease_detection": False, "image_labels_verified_by_pixels": False,
                             "medical_or_personality_inference": False, "forecast_accuracy_validated": False},
            "storage": "none"}

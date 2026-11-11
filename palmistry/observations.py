"""Strict, transient observation contract. User labels always win."""

import re

SIDES = {"left", "right", "unknown"}
FEATURES = {
    "line": {"life", "head", "heart", "fate", "sun", "mars", "health", "union",
             "attachment", "insurance", "intuition", "travel", "venus_girdle", "mercury"},
    "symbol": {"triangle", "square", "star", "cross", "island", "circle", "grid", "trident", "apex", "spot"},
    "morphology": {"palm_outline", "finger_palm_ratio", "finger_tip", "finger_joint", "thumb_shape", "finger_spacing", "finger_joint_marks", "back_tendon_pattern"},
    "mount": {"jupiter", "saturn", "sun", "mercury", "mars_first", "venus", "mars_second", "moon", "plain"},
}
GEOMETRY = {
    "start", "end", "path", "direction", "continuity", "parallel_to", "parent_line",
    "independent", "closed", "edge_count", "stroke_count", "common_intersection",
    "gap_confirmed", "overlap", "shape", "scheme", "relief", "upward_branch", "double", "region", "origin_ref",
}
BOOL_FIELDS = {"independent", "closed", "common_intersection", "gap_confirmed", "overlap", "upward_branch", "double"}
INT_FIELDS = {"edge_count", "stroke_count"}
STR_VALUES = {
    "start": {"wrist", "life_line", "moon_region", "palm_center", "head_line", "heart_line", "fate_line", "thumb_index", "little_side", "unknown"},
    "end": {"middle_base", "middle_finger", "ring_base", "little_base", "index_base", "index_middle_gap", "palm_center", "wrist", "moon_region", "head_line", "heart_line", "life_line", "unknown"},
    "path": {"around_thumb_ball", "across_palm", "under_finger_bases", "toward_middle", "toward_ring", "beside_life", "small_finger_edge", "under_upper_crease", "lower_outer_palm", "finger_joint", "unknown"},
    "direction": {"transverse", "descending_outer", "ascending", "curved", "wavy", "unknown"},
    "continuity": {"continuous", "gap", "overlapping", "chain", "partial", "unknown"},
    "parallel_to": {"life", "head", "heart", "fate", "sun", "unknown"},
    "parent_line": {"life", "head", "heart", "fate", "sun", "none", "unknown"},
    "shape": {"square", "oblong", "oval", "tapered", "mixed", "knotted", "spatulate", "conical", "pointed", "thin", "concave", "straight", "curved", "parallel_bundle", "unknown"},
    "scheme": {"five_elements", "western_seven", "appendix_six", "descriptive", "unknown"},
    "relief": {"raised", "flat", "depressed", "unknown"},
    "region": {"jupiter", "saturn", "sun", "mercury", "mars_first", "venus", "mars_second", "moon", "plain", "finger_joints", "thumb_joint", "unknown"},
}


class ObservationError(ValueError):
    pass


def _fields(value, allowed, required, where):
    if not isinstance(value, dict):
        raise ObservationError(f"{where}必须为对象")
    if set(value) - allowed:
        raise ObservationError(f"{where}包含未定义字段：{', '.join(sorted(set(value)-allowed))}")
    if required - set(value):
        raise ObservationError(f"{where}缺少字段：{', '.join(sorted(required-set(value)))}")


def _identifier(value, where):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise ObservationError(f"{where}需为1至64位字母、数字、下划线或短横线")


def validate(payload):
    _fields(payload, {"schema_version", "dominant_hand", "focus", "images", "record_type"}, {"schema_version", "images"}, "输入")
    if payload["schema_version"] != "1.0":
        raise ObservationError("仅支持schema_version=1.0")
    if payload.get("dominant_hand", "unknown") not in SIDES:
        raise ObservationError("惯用手必须为left/right/unknown")
    if payload.get("focus", "overall") not in {"overall", "career", "relationships"}:
        raise ObservationError("主题仅支持overall/career/relationships")
    if payload.get("record_type", "transient") not in {"transient", "synthetic"}:
        raise ObservationError("仅接收本次临时观察或合成测试，不接收个人档案")
    if not isinstance(payload["images"], list) or not 1 <= len(payload["images"]) <= 12:
        raise ObservationError("需要1至12个图像观察对象")
    image_ids, observation_ids = set(), set()
    for img in payload["images"]:
        _fields(img, {"id", "user_hand", "provider_hand", "mirror", "quality", "view", "comparable", "observations"}, {"id", "quality", "view", "observations"}, "图像")
        _identifier(img["id"], "图像ID")
        if img["id"] in image_ids:
            raise ObservationError("图像ID重复")
        image_ids.add(img["id"])
        if any(img.get(key, "unknown") not in SIDES for key in ("user_hand", "provider_hand")):
            raise ObservationError("手别必须为left/right/unknown")
        if img.get("mirror", "unknown") not in {"mirrored", "not_mirrored", "unknown"}:
            raise ObservationError("镜像状态无效")
        if img["quality"] not in {"clear", "limited", "unusable"}:
            raise ObservationError("图像质量须为clear/limited/unusable")
        if img["view"] not in {"palm", "side", "back", "oblique"}:
            raise ObservationError("视角须为palm/side/back/oblique")
        if type(img.get("comparable", False)) is not bool:
            raise ObservationError("comparable必须为布尔值")
        if not isinstance(img["observations"], list) or len(img["observations"]) > 100:
            raise ObservationError("observations须为最多100项的列表")
        for obs in img["observations"]:
            _fields(obs, {"id", "kind", "feature", "visibility", "basis", "geometry"}, {"id", "kind", "feature", "visibility", "basis", "geometry"}, "观察")
            _identifier(obs["id"], "观察ID")
            if obs["id"] in observation_ids:
                raise ObservationError("观察ID必须全局唯一")
            observation_ids.add(obs["id"])
            if obs["kind"] not in FEATURES or obs["feature"] not in FEATURES[obs["kind"]]:
                raise ObservationError("未知形态类别或特征名")
            if obs["visibility"] not in {"clear", "partial", "unobservable", "not_seen"}:
                raise ObservationError("可见性状态无效")
            if obs["basis"] not in {"observed", "hypothesized"}:
                raise ObservationError("basis须为observed/hypothesized")
            _fields(obs["geometry"], GEOMETRY, set(), "几何描述")
            for key, value in obs["geometry"].items():
                if key == "origin_ref":
                    _identifier(value, "origin_ref")
                if key in BOOL_FIELDS and type(value) is not bool:
                    raise ObservationError(f"{key}必须为布尔值")
                if key in INT_FIELDS and (type(value) is not int or not 0 <= value <= 12):
                    raise ObservationError(f"{key}必须为0至12的整数")
                if key in STR_VALUES and (not isinstance(value, str) or value not in STR_VALUES[key]):
                    raise ObservationError(f"{key}取值无效")
    located = {obs['id']: (img['id'], obs) for img in payload['images'] for obs in img['observations']}
    for img in payload['images']:
        for obs in img['observations']:
            ref = obs['geometry'].get('origin_ref')
            if ref is None:
                continue
            if ref not in located or ref == obs['id']:
                raise ObservationError('origin_ref须指向另一条已提供的观察')
            image_id, parent = located[ref]
            if image_id != img['id'] or obs['kind'] != 'line' or parent['kind'] != 'line':
                raise ObservationError('origin_ref只能连接同一张照片中的掌线')
            if obs['geometry'].get('start') != parent['feature'] + '_line':
                raise ObservationError('origin_ref与起点所指掌线不一致')
    return payload


def resolve_hand(img):
    user, provider = img.get("user_hand", "unknown"), img.get("provider_hand", "unknown")
    return {"hand": user, "source": "user" if user != "unknown" else "unconfirmed",
            "provider_disagrees": user != "unknown" and provider != "unknown" and user != provider,
            "mirror": img.get("mirror", "unknown")}


def qualify(img, obs):
    """Qualify *an observed candidate*, not automatic pixel recognition."""
    g, f, k = obs["geometry"], obs["feature"], obs["kind"]
    if img["quality"] == "unusable" or obs["visibility"] != "clear" or obs["basis"] != "observed":
        return "unresolved", "当前观察不够清楚；不把未看见当作不存在"
    if k == "line":
        if img["view"] not in {"palm", "oblique"} and f != "union":
            return "unresolved", "该视角不支持确认这条掌内线"
        checks = {
            "life": g.get("path") == "around_thumb_ball",
            "head": g.get("path") == "across_palm" and g.get("start") == "thumb_index",
            "heart": g.get("path") == "under_finger_bases",
            "fate": g.get("end") in {"middle_base", "middle_finger"} or (g.get("path")=="toward_middle" and g.get("end") in {"palm_center","head_line","heart_line"}),
            "sun": g.get("end") == "ring_base" or (g.get("path")=="toward_ring" and g.get("end") in {"palm_center","head_line","heart_line"}),
            "union": img["view"] == "side" and g.get("path") == "small_finger_edge",
        }
        if f in checks and not checks[f]:
            return "unresolved", "候选名称与已给起止位置不一致或位置不足"
        if f in {"mars", "insurance", "attachment"}:
            return "descriptive", "仅确认主线附近的平行小纹；不凭平行关系强分辅线名称"
        if f not in checks:
            return "descriptive", "辅线先作位置观察，不据名称套用人生断语"
        if g.get("continuity") == "gap" and not (g.get("gap_confirmed") is True and g.get("overlap") is False):
            return "unresolved", "所谓中断尚未排除阴影、遮挡或搭接"
        if g.get('continuity') == 'overlapping' and g.get('overlap') is not True:
            return 'unresolved', '搭接须确认实际重叠，不把空缺改称搭接'
        return "recognized", "位置与候选线定义相符"
    if k == "symbol":
        if f in {"triangle", "square"}:
            if g.get("independent") is not True:
                return "enclosure", "只见围成的区域，不能确认为独立符号"
            if g.get("closed") is not True or g.get("edge_count") != (3 if f == "triangle" else 4):
                return "unresolved", "图形闭合或边数尚不满足定义"
        elif f in {"star", "cross"}:
            allowed = {3, 4} if f == "star" else {2}
            if g.get("independent") is not True or g.get("stroke_count") not in allowed or g.get("common_intersection") is not True:
                return "unresolved", "短线数量或共同交点不够明确"
        elif f == "island":
            if g.get("closed") is not True or g.get("parent_line") not in {"life", "head", "heart", "fate", "sun"}:
                return "unresolved", "岛形须确认在线内闭合，不以两线偶遇替代"
        else:
            return "descriptive", "此形态保留观察，首版不自动配吉凶"
        return "recognized", "符号形态满足当前明确条件"
    if k == "mount":
        if img["view"] != "oblique" and g.get("relief") not in (None, "unknown"):
            return "unresolved", "正面单照不足以确认掌丘高低"
        return "descriptive", "可定位宫丘；不以隆起程度测量性格或器官"
    if k == "morphology" and f == "back_tendon_pattern" and img["view"] != "back":
        return "unresolved", "掌背筋络须掌背视角；不能在掌心照片中补出"
    return "descriptive", "保留整体形态及分类语境，混合型不强行定纯型"

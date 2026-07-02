# server.py —— 主服务器，整合所有模块
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, session, request, jsonify
import random

from modules.map_gen import generate_map, GRID_SIZE_MAP, PROGRESS_MAX_MAP, generate_holiday_map
from modules.events import (
    CELL_TYPE_CONFIG, NODE_DESCRIPTIONS, get_options_for_type,
    REENTERABLE_TYPES, BLOCKABLE_TYPES, EXAM_PREP_OPTIONS,
)
from modules.stats import (
    init_character, clamp_stat, apply_effects, apply_class_rel_effects,
    get_love_multiplier, handle_confession, check_love_zero, fluctuate,
    STAT_NAMES, STAT_MIN, CLASS_REL_MIN, STAT_MAX,
    apply_hard_spirit_penalty, apply_grade_decay, get_holiday_score_req,
)
from modules.endings import do_exam, do_gaokao, BAD_ENDING_MESSAGES

app = Flask(__name__)
app.secret_key = 'replace-with-random-secret-key'

# 从 names.txt 加载姓名库
def load_names():
    name_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'names.txt')
    with open(name_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

NAME_POOL = load_names()

def pick_random_name():
    return random.choice(NAME_POOL)

TOTAL_MAPS = 6
SEMESTER_NAMES = {
    1: "高一年级 上学期", 2: "高一年级 下学期",
    3: "高二年级 上学期", 4: "高二年级 下学期",
    5: "高三年级 上学期", 6: "高三年级 下学期",
}

# ==================== 游戏状态管理 ====================
def init_game_state():
    map_data, connections, grid_size = generate_map(1, None, None)
    return {
        "player_pos": [grid_size // 2, grid_size // 2],
        "progress": 0, "progress_max": PROGRESS_MAX_MAP[1],
        "map_count": 1, "grid_size": grid_size,
        "map_data": map_data, "connections": connections,
        "character": init_character(),
        "game_over": False,
        "message": "你踏入了重点高中的校门，新的高中生活开始了！",
        "pending_cell": None, "pending_options": None, "pending_type": None,
        "exam_result": None, "ending": None, "bad_ending": None,
        "critical_stats": [], "in_exam_prep": False, "history": [],
    }


def get_game_state():
    if 'game' not in session:
        session['game'] = init_game_state()
    return session['game']


def save_game_state(state):
    session['game'] = state


def get_stat_min(stat_name):
    return CLASS_REL_MIN if stat_name == "班级关系" else STAT_MIN


def build_full_grid(state):
    grid = []
    for y in range(state["grid_size"]):
        row = []
        for x in range(state["grid_size"]):
            key = f"{x},{y}"
            cell = state["map_data"].get(key)
            if cell and cell["revealed"]:
                cfg = CELL_TYPE_CONFIG.get(cell["type"], {})
                row.append({"x": x, "y": y, "type": cell["type"],
                            "icon": cfg.get("icon"), "color": cfg.get("color"),
                            "entered": cell["entered"], "blocked": cell["blocked"]})
            else:
                row.append(None)
        grid.append(row)
    return grid


def build_connection_lines(state):
    lines, seen = [], set()
    for key, neighbors in state["connections"].items():
        x1, y1 = map(int, key.split(","))
        for nk in neighbors:
            pair = tuple(sorted([key, nk]))
            if pair in seen:
                continue
            seen.add(pair)
            x2, y2 = map(int, nk.split(","))
            lines.append([x1, y1, x2, y2])
    return lines


def reveal_connected(state, x, y):
    key = f"{x},{y}"
    for nk in state["connections"].get(key, []):
        if nk in state["map_data"] and not state["map_data"][nk]["revealed"]:
            state["map_data"][nk]["revealed"] = True


def check_bad_ending(state, effects):
    for stat in list(state["critical_stats"]):
        eff_val = effects.get(stat, 0)
        if eff_val <= 0 and state["character"][stat] <= get_stat_min(stat):
            state["game_over"] = True
            state["bad_ending"] = BAD_ENDING_MESSAGES.get(stat, f"{stat}已跌入谷底……")
            state["message"] = f"💀 坏结局触发！{stat}已经降到了最低点……"
            return True
        if eff_val > 0 or state["character"][stat] > get_stat_min(stat):
            state["critical_stats"].remove(stat)
    return False


def update_critical_stats(state):
    for stat in STAT_NAMES:
        if stat == "爱情进展":
            continue
        if state["character"][stat] <= get_stat_min(stat) and stat not in state["critical_stats"]:
            state["critical_stats"].append(stat)


def save_map_snapshot(state):
    cells_entered, type_counts = [], {}
    cells_revealed = 0
    for key, cell in state["map_data"].items():
        if cell["revealed"]:
            cells_revealed += 1
        if cell["entered"]:
            cells_entered.append(cell["type"])
            type_counts[cell["type"]] = type_counts.get(cell["type"], 0) + 1
    state.setdefault("history", []).append({
        "map": state["map_count"],
        "semester": SEMESTER_NAMES.get(state["map_count"], ""),
        "grid_size": state["grid_size"], "progress": state["progress"],
        "cells_revealed": cells_revealed, "cells_entered": len(cells_entered),
        "types": type_counts,
    })


def transition_to_next_map(state):
    next_map = state["map_count"] + 1
    save_map_snapshot(state)
    map_data, connections, grid_size = generate_map(next_map)
    state["map_data"] = map_data
    state["connections"] = connections
    state["grid_size"] = grid_size
    state["player_pos"] = [grid_size // 2, grid_size // 2]
    state["progress"] = 0
    state["progress_max"] = PROGRESS_MAX_MAP[next_map]
    state["map_count"] = next_map
    state["pending_cell"] = state["pending_options"] = state["pending_type"] = None
    state["critical_stats"] = []
    state["in_exam_prep"] = False


def check_progress_full(state):
    if state["progress"] < state["progress_max"]:
        return False
    if state.get("in_exam_prep"):
        msg = do_exam(state["character"])
        state["exam_result"] = msg
        state["in_exam_prep"] = False
        state["message"] = msg + f"\n\n新学期开始了——{SEMESTER_NAMES.get(state['map_count'] + 1, '')}"
        transition_to_next_map(state)
        return False
    if state["map_count"] < TOTAL_MAPS:
        state["in_exam_prep"] = True
        state["pending_cell"] = state["pending_options"] = state["pending_type"] = None
        state["message"] = "📚 期末考试临近！你需要为即将到来的考试做好备考准备。"
        return False
    else:
        save_map_snapshot(state)
        state["ending"] = do_gaokao(state["character"])
        state["game_over"] = True
        state["message"] = "🎓 高考结束！"
        return True


# ==================== API 路由 ====================
@app.route('/api/state')
def api_state():
    state = get_game_state()
    if state.get("in_exam_prep"):
        grid = [[{"x": 0, "y": 0, "type": "期末备考", "icon": "📚", "color": "#E67E22", "entered": False, "blocked": False}]]
        return jsonify({
            "player_pos": [0, 0], "progress": state["progress"], "progress_max": state["progress_max"],
            "map_count": state["map_count"], "total_maps": TOTAL_MAPS, "grid_size": 1,
            "semester_name": SEMESTER_NAMES.get(state["map_count"], ""),
            "grid": grid, "connection_lines": [], "character": state["character"],
            "game_over": state["game_over"], "message": state["message"],
            "pending_cell": state["pending_cell"], "pending_options": state["pending_options"],
            "pending_type": state["pending_type"], "exam_result": state["exam_result"],
            "ending": state["ending"], "bad_ending": state["bad_ending"],
            "critical_stats": state["critical_stats"], "in_exam_prep": True,
            "romance_state": state["character"].get("romance_state"),
            "history": state.get("history", []),
        })
    grid = build_full_grid(state)
    lines = build_connection_lines(state)
    return jsonify({
        "player_pos": state["player_pos"], "progress": state["progress"],
        "progress_max": state["progress_max"], "map_count": state["map_count"],
        "total_maps": TOTAL_MAPS, "grid_size": state["grid_size"],
        "semester_name": SEMESTER_NAMES.get(state["map_count"], ""),
        "grid": grid, "connection_lines": lines, "character": state["character"],
        "game_over": state["game_over"], "message": state["message"],
        "pending_cell": state["pending_cell"], "pending_options": state["pending_options"],
        "pending_type": state["pending_type"], "exam_result": state["exam_result"],
        "ending": state["ending"], "bad_ending": state["bad_ending"],
        "critical_stats": state["critical_stats"], "in_exam_prep": False,
        "romance_state": state["character"].get("romance_state"),
        "history": state.get("history", []),
    })


@app.route('/api/enter', methods=['POST'])
def api_enter():
    state = get_game_state()
    if state["game_over"]:
        return jsonify({"error": "游戏已结束"}), 400
    if state["pending_cell"] is not None:
        return jsonify({"error": "请先完成当前选择"}), 400
    data = request.get_json()
    x, y = data.get('x'), data.get('y')
    if x is None or y is None:
        return jsonify({"error": "缺少坐标"}), 400

    # 期末备考特殊处理
    if state.get("in_exam_prep"):
        state["pending_cell"] = [0, 0]
        state["pending_options"] = EXAM_PREP_OPTIONS
        state["pending_type"] = "期末备考"
        save_game_state(state)
        return jsonify({"status": "ok", "pending": True, "cell_type": "期末备考",
                        "options": [{"index": i, "label": o["label"], "desc": o["desc"]}
                                    for i, o in enumerate(EXAM_PREP_OPTIONS)]})

    key = f"{x},{y}"
    if key not in state["map_data"]:
        return jsonify({"error": "无效坐标"}), 400
    cell = state["map_data"][key]
    if not cell["revealed"]:
        return jsonify({"error": "该区域尚未点亮"}), 400
    if cell["blocked"]:
        return jsonify({"error": "该区域已被封锁"}), 400

    ctype = cell["type"]

    if ctype == "入学":
        if cell["entered"] and [x, y] == state["player_pos"]:
            return jsonify({"error": "你已经在这里了"}), 400
        cell["entered"] = True
        state["player_pos"] = [x, y]
        reveal_connected(state, x, y)
        state["message"] = "你站在校门口，一切从这里开始。"
        save_game_state(state)
        return jsonify({"status": "ok", "pending": False})

    if ctype not in REENTERABLE_TYPES and cell["entered"] and ctype in BLOCKABLE_TYPES:
        return jsonify({"error": "该区域已被封锁"}), 400

    type_label, options = get_options_for_type(ctype, state["character"], state.get("difficulty", "normal"))
    if options is None:
        return jsonify({"error": "未知格子类型"}), 400

    state["pending_cell"] = [x, y]
    state["pending_options"] = options
    state["pending_type"] = type_label
    save_game_state(state)
    return jsonify({"status": "ok", "pending": True, "cell_type": type_label,
                    "options": [{"index": i, "label": o["label"], "desc": o["desc"]}
                                for i, o in enumerate(options)]})


@app.route('/api/choose', methods=['POST'])
def api_choose():
    state = get_game_state()
    if state["game_over"]:
        return jsonify({"error": "游戏已结束"}), 400
    if state["pending_cell"] is None:
        return jsonify({"error": "没有待处理的选择"}), 400

    data = request.get_json()
    choice_idx = data.get('choice')
    if choice_idx is None:
        return jsonify({"error": "缺少选项索引"}), 400
    options = state["pending_options"]
    if choice_idx < 0 or choice_idx >= len(options):
        return jsonify({"error": "无效的选项索引"}), 400

    chosen = options[choice_idx]
    px, py = state["pending_cell"]
    key = f"{px},{py}"
    ctype = state["map_data"].get(key, {}).get("type", state.get("pending_type", ""))

    # 波动效果
    no_fluct = chosen.get("_no_fluctuate", False)
    adjusted_effects = {}
    for s in STAT_NAMES:
        if s in chosen:
            adjusted_effects[s] = fluctuate(chosen[s], no_fluctuate=no_fluct)
    if adjusted_effects.get("爱情进展", 0) > 0:
        adjusted_effects["爱情进展"] = int(adjusted_effects["爱情进展"] * get_love_multiplier(state["character"]))

    if check_bad_ending(state, adjusted_effects):
        save_game_state(state)
        return jsonify({"status": "ok", "game_over": True, "bad_ending": state["bad_ending"],
                        "message": state["message"]})

    apply_effects(state["character"], adjusted_effects)
    class_msg = apply_class_rel_effects(state["character"])

    # 高考特殊结局处理
    if chosen.get("_gaokao_action") == "flee":
        state["ending"] = "🏃【弃考·逃离考场】\n高中三年按部就班的生活终于迎来尽头，可是此刻，你心中却生出一个冲动的念头。或许是压抑太久的叛逆，或许是面对未知的怯懦——你在抵达考场的前一刻，转身跑向了城市另一头的车站。\n\n风吹过空荡荡的校服口袋，你没有回头。"
        state["game_over"] = True
        state["pending_cell"] = state["pending_options"] = state["pending_type"] = None
        save_game_state(state)
        return jsonify({"status": "ok", "game_over": True, "ending": state["ending"], "message": "你逃离了考场……"})
    if chosen.get("_gaokao_action") == "oversleep":
        state["ending"] = "😱【意外·错过高考】\n你预先订好的闹钟并没有响。当阳光透过窗帘缝隙洒在脸上，你终于从一场漫长而舒适的睡眠中醒来——墙上的时钟赫然指向了十二点整。\n\n有那么一瞬间，你以为这是梦。但窗外的蝉鸣和空荡荡的房间告诉你，一切都是真的。"
        state["game_over"] = True
        state["pending_cell"] = state["pending_options"] = state["pending_type"] = None
        save_game_state(state)
        return jsonify({"status": "ok", "game_over": True, "ending": state["ending"], "message": "你错过了高考……"})

    # 期末备考
    if ctype == "期末备考":
        state["message"] = f"你选择了【{chosen['label']}】—— {chosen['desc']}"
        if class_msg:
            state["message"] += "\n" + class_msg
        state["pending_cell"] = state["pending_options"] = state["pending_type"] = None
        check_progress_full(state)
        save_game_state(state)
        return jsonify({"status": "ok", "message": state["message"],
                        "character": state["character"], "progress": state["progress"],
                        "game_over": state["game_over"], "map_count": state["map_count"]})

    # 表白
    if chosen.get("_is_confession"):
        result = handle_confession(state["character"])
        state["message"] = f"你选择了【{chosen['label']}】—— {result['msg']}"
    else:
        state["message"] = f"你选择了【{chosen['label']}】—— {chosen['desc']}"
    if class_msg:
        state["message"] += "\n" + class_msg

    # 爱情归零
    love_zero_msg = check_love_zero(state["character"])
    if love_zero_msg:
        state["message"] += "\n" + love_zero_msg

    # 标记格子
    cell = state["map_data"].get(key)
    if cell:
        cell["entered"] = True
        state["player_pos"] = [px, py]
        if ctype in BLOCKABLE_TYPES:
            cell["blocked"] = True
        reveal_connected(state, px, py)

    state["progress"] += 1
    if chosen.get("_timeReverse"):
        state["progress"] = max(0, state["progress"] - 3)
    state["pending_cell"] = state["pending_options"] = state["pending_type"] = None
    update_critical_stats(state)
    check_progress_full(state)
    save_game_state(state)

    return jsonify({"status": "ok", "message": state["message"],
                    "character": state["character"], "player_pos": state["player_pos"],
                    "progress": state["progress"], "progress_max": state["progress_max"],
                    "game_over": state["game_over"], "map_count": state["map_count"],
                    "ending": state["ending"], "bad_ending": state["bad_ending"],
                    "critical_stats": state["critical_stats"],
                    "romance_state": state["character"].get("romance_state"),
                    "love_zero_popup": love_zero_msg if love_zero_msg and state["character"].get("romance_state") == "single" else None})


# ==================== 前端页面 ====================
@app.route('/')
def index():
    session.pop('game', None)
    session['game'] = init_game_state()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'game.html'), 'r', encoding='utf-8') as f:
        return f.read()


if __name__ == '__main__':
    app.run(debug=True)

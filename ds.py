from flask import Flask, session, request, jsonify, render_template_string
import random
import math

app = Flask(__name__)
app.secret_key = 'replace-with-random-secret-key'

# ==================== 常量配置 ====================
TOTAL_MAPS = 6

# 每张地图的尺寸
GRID_SIZE_MAP = {1: 5, 2: 5, 3: 7, 4: 7, 5: 7, 6: 9}

# 每张地图的进度上限
PROGRESS_MAX_MAP = {1: 15, 2: 15, 3: 20, 4: 20, 5: 20, 6: 25}

# 学期名称
SEMESTER_NAMES = {
    1: "高一年级 上学期",
    2: "高一年级 下学期",
    3: "高二年级 上学期",
    4: "高二年级 下学期",
    5: "高三年级 上学期",
    6: "高三年级 下学期",
}

# 状态上限
STAT_MAX = 100
STAT_MIN = 0
CLASS_REL_MIN = -100

# ---------- 格子类型定义 ----------
CELL_TYPE_CONFIG = {
    "入学": {"desc": "高中生活的起点，你站在校门前，满怀期待。", "icon": "🎓", "category": "special", "color": "#FFD700"},
    "学习": {"desc": "", "icon": "📚", "category": "study", "color": "#4A90E2"},
    "课余": {"desc": "", "icon": "⚽", "category": "extracurricular", "color": "#F5A623"},
    "测验": {"desc": "一场突击测验！检验你近期的学习成果。", "icon": "📝", "category": "test", "color": "#E74C3C"},
    "恋爱": {"desc": "心跳加速，空气中弥漫着青春的气息。", "icon": "💕", "category": "romance", "color": "#FF6B9D"},
    "造梦": {"desc": "你仰望星空，未来的蓝图在脑海中展开。", "icon": "✨", "category": "dream", "color": "#9013FE"},
    "研学": {"desc": "一次珍贵的研学机会！走出课堂，探索更广阔的天地。", "icon": "🔬", "category": "research", "color": "#1ABC9C"},
}

# ---------- 学习选项（3档） ----------
LEARNING_OPTIONS = [
    {"label": "轻松学习", "desc": "按部就班，保持自己的节奏就好。",
     "成绩水平": 3, "学习状态": 1, "体能": 0, "精神状态": 2, "爱情进展": 0, "班级关系": 2},
    {"label": "适度用功", "desc": "多花些时间，把基础打扎实。",
     "成绩水平": 5, "学习状态": 3, "体能": -2, "精神状态": 0, "爱情进展": 0, "班级关系": 0},
    {"label": "拼命苦读", "desc": "挑灯夜战，卷到飞起！",
     "成绩水平": 8, "学习状态": 5, "体能": -5, "精神状态": -4, "爱情进展": 0, "班级关系": -3},
]

# ---------- 课余选项（两种组合） ----------
EXTRACURRICULAR_COMBOS = [
    [  # 组合1
        {"label": "和同学社交", "desc": "你和新朋友聊得很投机，友谊的小船扬帆起航。",
         "爱情进展": 2, "精神状态": 3, "体能": 0, "成绩水平": 0, "学习状态": 0, "班级关系": 4},
        {"label": "和同学打游戏", "desc": "游戏世界里你们并肩作战，酣畅淋漓。",
         "精神状态": 5, "体能": 0, "成绩水平": -2, "学习状态": -2, "爱情进展": 1, "班级关系": 3},
        {"label": "和同学打球", "desc": "汗水挥洒，球场上青春飞扬。",
         "体能": 5, "精神状态": 3, "成绩水平": 0, "学习状态": 0, "爱情进展": 1, "班级关系": 3},
        {"label": "多做几道习题", "desc": "笨鸟先飞，多练多会，稳扎稳打。",
         "成绩水平": 3, "学习状态": 2, "体能": -2, "精神状态": -2, "爱情进展": 0, "班级关系": -1},
    ],
    [  # 组合2
        {"label": "和同学社交", "desc": "你和同学们聊着最近的趣事，气氛轻松。",
         "爱情进展": 2, "精神状态": 3, "体能": 0, "成绩水平": 0, "学习状态": 0, "班级关系": 4},
        {"label": "听听音乐", "desc": "戴上耳机，世界安静了，灵魂得到了抚慰。",
         "精神状态": 5, "体能": 0, "成绩水平": 0, "学习状态": 1, "爱情进展": 0, "班级关系": 0},
        {"label": "多做几道习题", "desc": "趁着空闲，巩固一下薄弱知识点。",
         "成绩水平": 3, "学习状态": 2, "体能": -2, "精神状态": -2, "爱情进展": 0, "班级关系": -1},
        {"label": "自己玩游戏", "desc": "一个人沉浸在游戏世界里，放松也不错。",
         "精神状态": 3, "体能": -2, "成绩水平": -2, "学习状态": -2, "爱情进展": 0, "班级关系": -2},
    ],
]

# ---------- 测验选项 ----------
TEST_OPTIONS = [
    {"label": "认真答题", "desc": "沉着冷静，仔细审题，发挥正常水平。",
     "成绩水平": 2, "学习状态": 3, "体能": 0, "精神状态": -3, "爱情进展": 0, "班级关系": 0},
    {"label": "全力以赴", "desc": "拼尽全力，每一分都要争取！",
     "成绩水平": 4, "学习状态": 5, "体能": -2, "精神状态": -6, "爱情进展": 0, "班级关系": -1},
    {"label": "轻松应对", "desc": "心态放松，尽力就好，不给自己太大压力。",
     "成绩水平": 1, "学习状态": 1, "体能": 0, "精神状态": -1, "爱情进展": 0, "班级关系": 1},
]

# ---------- 研学选项 ----------
RESEARCH_OPTIONS = [
    {"label": "深入探究", "desc": "你沉浸在知识的海洋中，收获颇丰。",
     "成绩水平": 5, "学习状态": 6, "体能": -1, "精神状态": -2, "爱情进展": 0, "班级关系": 1},
    {"label": "开阔视野", "desc": "走出课本，你看到了更广阔的世界。",
     "成绩水平": 3, "学习状态": 3, "体能": 0, "精神状态": 4, "爱情进展": 1, "班级关系": 3},
    {"label": "结交朋友", "desc": "在研学途中你结识了志同道合的伙伴。",
     "成绩水平": 1, "学习状态": 1, "体能": 0, "精神状态": 3, "爱情进展": 2, "班级关系": 6},
]

# ---------- 恋爱选项（单身：表白 / 恋爱中：约会） ----------
CONFESSION_OPTIONS = [
    {"label": "主动表白", "desc": "你鼓起勇气，把藏在心底的话说了出来。",
     "爱情进展": 0, "精神状态": 2, "成绩水平": -3, "学习状态": -3, "体能": 0, "班级关系": 2,
     "_is_confession": True},
    {"label": "默默守护", "desc": "你把这份心意藏在心底，静静地看着 Ta。",
     "爱情进展": 3, "精神状态": 0, "成绩水平": 0, "学习状态": 0, "体能": 0, "班级关系": 1},
    {"label": "专注学习", "desc": "你决定把精力放在学业上，先不想这些。",
     "爱情进展": -3, "精神状态": -2, "成绩水平": 3, "学习状态": 5, "体能": 0, "班级关系": -1},
]

DATING_COMBOS = [
    [  # 组合1：甜蜜约会 (60%)
        {"label": "去海洋馆约会", "desc": "你们一起看着五彩斑斓的鱼群，Ta 笑得很开心。",
         "爱情进展": 6, "精神状态": 3, "成绩水平": 0, "学习状态": -1, "体能": -1, "班级关系": 0},
        {"label": "去手工店约会", "desc": "你们一起做了一对陶艺杯子，独一无二的回忆。",
         "爱情进展": 5, "精神状态": 2, "成绩水平": 0, "学习状态": -1, "体能": 0, "班级关系": 0},
        {"label": "在校园一起看晚霞", "desc": "天边的云彩染成金色，你们并肩坐着，时间仿佛静止了。",
         "爱情进展": 4, "精神状态": 4, "成绩水平": 0, "学习状态": 0, "体能": 0, "班级关系": 1},
        {"label": "在校园散步", "desc": "傍晚的校园很安静，你们慢慢走着，聊着各自的梦想。",
         "爱情进展": 4, "精神状态": 2, "成绩水平": 0, "学习状态": 0, "体能": 2, "班级关系": 1},
    ],
    [  # 组合2：情感起伏 (40%)
        {"label": "尽力安慰", "desc": "Ta 心情不好，你陪在身边，说了很多温暖的话。",
         "爱情进展": 4, "精神状态": 2, "成绩水平": 0, "学习状态": -1, "体能": 0, "班级关系": 0},
        {"label": "沉默倾听", "desc": "你没有说什么，只是静静地听着 Ta 的倾诉。有时候陪伴就是最好的安慰。",
         "爱情进展": 3, "精神状态": 1, "成绩水平": 0, "学习状态": 0, "体能": 0, "班级关系": 0},
        {"label": "大吵一架", "desc": "因为一些小事你们吵了起来，彼此说了伤人的话……",
         "爱情进展": -8, "精神状态": -4, "成绩水平": -1, "学习状态": -2, "体能": 0, "班级关系": -2},
    ],
]

# 期末备考选项
EXAM_PREP_OPTIONS = [
    {"label": "全力冲刺", "desc": "挑灯夜战，把每一个知识点都过一遍！",
     "成绩水平": 5, "学习状态": 5, "体能": -5, "精神状态": -8, "爱情进展": 0, "班级关系": -1},
    {"label": "劳逸结合", "desc": "合理规划时间，学习休息两不误。",
     "成绩水平": 3, "学习状态": 3, "体能": 0, "精神状态": 0, "爱情进展": 0, "班级关系": 0},
    {"label": "佛系随缘", "desc": "该会的自然会，不会的也强求不来，心态最重要。",
     "成绩水平": 1, "学习状态": 1, "体能": 2, "精神状态": 3, "爱情进展": 0, "班级关系": 1},
    {"label": "彻底摆烂", "desc": "反正也复习不完，不如好好休息……",
     "成绩水平": -3, "学习状态": -4, "体能": 3, "精神状态": 5, "爱情进展": 0, "班级关系": -1},
]

# ---------- 造梦选项 ----------
DREAM_OPTIONS = [
    {"label": "追逐梦想", "desc": "你为自己的理想制定了清晰的计划。",
     "精神状态": 5, "学习状态": 3, "成绩水平": 2, "体能": 0, "爱情进展": 0, "班级关系": 1},
    {"label": "放松休息", "desc": "好好休息，养足精神才能走更远的路。",
     "体能": 5, "精神状态": 4, "成绩水平": 0, "学习状态": -2, "爱情进展": 0, "班级关系": 0},
    {"label": "思考人生", "desc": "你静下心来，认真思考未来的方向。",
     "精神状态": 3, "学习状态": 5, "成绩水平": 1, "体能": -2, "爱情进展": 0, "班级关系": 2},
]

# 选项索引到配置的映射
def get_love_options(character):
    """根据恋爱状态返回对应选项。"""
    if character.get("romance_state") == "dating":
        # 60% 甜蜜约会, 40% 情感起伏
        combo = random.choices([0, 1], weights=[0.6, 0.4], k=1)[0]
        return ("恋爱", DATING_COMBOS[combo])
    else:
        return ("恋爱", CONFESSION_OPTIONS)

CELL_OPTIONS_MAP = {
    "学习": lambda: ("学习", LEARNING_OPTIONS),
    "课余": lambda: ("课余", random.choice(EXTRACURRICULAR_COMBOS)),
    "测验": lambda: ("测验", TEST_OPTIONS),
    "恋爱": lambda state: get_love_options(state["character"]),
    "造梦": lambda: ("造梦", DREAM_OPTIONS),
    "研学": lambda: ("研学", RESEARCH_OPTIONS),
}

# 可反复进入的格子类型
REENTERABLE_TYPES = {"恋爱", "造梦"}

# 进入后封锁的格子类型
BLOCKABLE_TYPES = {"学习", "课余", "测验", "研学"}

STAT_NAMES = ["成绩水平", "爱情进展", "体能", "精神状态", "学习状态", "班级关系"]

# 坏结局定义
BAD_ENDING_MESSAGES = {
    "成绩水平": "📉【学业崩溃】\n你的成绩一落千丈，再也跟不上课程进度。最终，你不得不离开了学校……青春的路上，学习不是唯一，但放弃了它，前路变得格外艰难。",
    "体能": "🏥【身体垮掉】\n长期的透支终于让你的身体撑不住了。躺在病床上的你，望着天花板，后悔没有好好爱惜自己。健康才是一切的根本啊。",
    "精神状态": "💔【精神崩溃】\n巨大的压力终于压垮了你。你把自己关在房间里，不愿面对任何人。青春的阳光，似乎再也照不进来了……",
    "学习状态": "😞【厌学弃学】\n你对学习彻底失去了兴趣。课本上的字像蚂蚁一样爬来爬去，你一个字也看不进去。没有知识武装的青春，还能走多远？",
    "班级关系": "😢【众叛亲离】\n你在班级中彻底被孤立了。走廊里同学们的欢声笑语，与你无关。孤独像一把刀子，慢慢地切割着你的心。",
}


# ==================== 地图生成 ====================
def bfs_distance(conn, start_key, target_key, max_depth=10):
    """计算两个格子之间在连通图中的最短距离。"""
    if start_key == target_key:
        return 0
    visited = {start_key}
    queue = [(start_key, 0)]
    for current, dist in queue:
        if dist >= max_depth:
            continue
        for nk in conn.get(current, []):
            if nk == target_key:
                return dist + 1
            if nk not in visited:
                visited.add(nk)
                queue.append((nk, dist + 1))
    return float('inf')


def generate_connections(grid_size):
    """生成 grid_size × grid_size 网格的随机连通图（邻接表），减少四连通格子数量。"""
    # 收集所有边（相邻格子之间）
    edges = []
    for x in range(grid_size):
        for y in range(grid_size):
            if x + 1 < grid_size:
                edges.append(((x, y), (x + 1, y)))
            if y + 1 < grid_size:
                edges.append(((x, y), (x, y + 1)))

    random.shuffle(edges)

    # 并查集
    parent = {}
    def find(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    def union(p1, p2):
        r1, r2 = find(p1), find(p2)
        if r1 != r2:
            parent[r1] = r2
            return True
        return False

    for x in range(grid_size):
        for y in range(grid_size):
            parent[(x, y)] = (x, y)

    conn = {f"{x},{y}": [] for x in range(grid_size) for y in range(grid_size)}

    # Kruskal 生成最小生成树
    for (a, b) in edges:
        if union(a, b):
            conn[f"{a[0]},{a[1]}"].append(f"{b[0]},{b[1]}")
            conn[f"{b[0]},{b[1]}"].append(f"{a[0]},{a[1]}")

    # 减少四连通：对于已有3条边的格子，降低额外加边的概率
    for (a, b) in edges:
        ka, kb = f"{a[0]},{a[1]}", f"{b[0]},{b[1]}"
        if kb in conn[ka]:
            continue
        # 如果任一端已有3条以上边，大幅降低加边概率
        prob = 0.15
        if len(conn[ka]) >= 3 or len(conn[kb]) >= 3:
            prob = 0.03
        if random.random() < prob:
            conn[ka].append(kb)
            conn[kb].append(ka)

    # 确保中心格直接连通 2 或 3 格
    center_key = f"{grid_size // 2},{grid_size // 2}"
    center_neighbors = list(conn[center_key])
    target_count = random.randint(2, 3)
    possible_neighbors = [
        (grid_size // 2 - 1, grid_size // 2),
        (grid_size // 2 + 1, grid_size // 2),
        (grid_size // 2, grid_size // 2 - 1),
        (grid_size // 2, grid_size // 2 + 1),
    ]

    if len(center_neighbors) < target_count:
        random.shuffle(possible_neighbors)
        for cx, cy in possible_neighbors:
            ck = f"{cx},{cy}"
            if 0 <= cx < grid_size and 0 <= cy < grid_size:
                if ck not in conn[center_key] and len(conn[center_key]) < target_count:
                    conn[center_key].append(ck)
                    conn[ck].append(center_key)
    elif len(center_neighbors) > target_count:
        random.shuffle(center_neighbors)
        for nk in center_neighbors[target_count:]:
            conn[center_key].remove(nk)
            conn[nk].remove(center_key)

    return conn


def generate_map(map_count):
    """生成一张完整地图，返回 (map_data, connections, grid_size)。"""
    grid_size = GRID_SIZE_MAP[map_count]
    conn = generate_connections(grid_size)
    map_data = {}
    center = (grid_size // 2, grid_size // 2)
    center_key = f"{center[0]},{center[1]}"

    # 收集所有格子（排除中心）
    all_cells = []
    for x in range(grid_size):
        for y in range(grid_size):
            if (x, y) != center:
                all_cells.append((x, y))
    random.shuffle(all_cells)

    # 中心格 = 入学
    map_data[center_key] = {"type": "入学", "revealed": True, "entered": True, "blocked": False}

    # 恋爱：恰好 1 个，且与中心距离 ≤ 3
    love_cell = None
    for cell in all_cells:
        ck = f"{cell[0]},{cell[1]}"
        if bfs_distance(conn, center_key, ck, max_depth=3) <= 3:
            love_cell = cell
            break
    if love_cell is None:
        # 放宽到所有格子
        love_cell = all_cells[0]
    all_cells.remove(love_cell)
    map_data[f"{love_cell[0]},{love_cell[1]}"] = {"type": "恋爱", "revealed": False, "entered": False, "blocked": False}

    # 研学：恰好 1 个，且与中心距离 ≤ 4
    research_cell = None
    for cell in all_cells:
        ck = f"{cell[0]},{cell[1]}"
        if bfs_distance(conn, center_key, ck, max_depth=4) <= 4:
            research_cell = cell
            break
    if research_cell is None:
        research_cell = all_cells[0]
    all_cells.remove(research_cell)
    map_data[f"{research_cell[0]},{research_cell[1]}"] = {"type": "研学", "revealed": False, "entered": False, "blocked": False}

    # 造梦：3~5 个
    dream_count = random.randint(3, 5)
    for _ in range(dream_count):
        if all_cells:
            dc = all_cells.pop()
            map_data[f"{dc[0]},{dc[1]}"] = {"type": "造梦", "revealed": False, "entered": False, "blocked": False}

    # 剩余格子：学习:课余:测验 = 5:3:2
    remaining = len(all_cells)
    study_count = int(remaining * 0.5)
    extra_count = int(remaining * 0.3)
    test_count = remaining - study_count - extra_count

    for (x, y) in all_cells[:study_count]:
        map_data[f"{x},{y}"] = {"type": "学习", "revealed": False, "entered": False, "blocked": False}
    for (x, y) in all_cells[study_count:study_count + extra_count]:
        map_data[f"{x},{y}"] = {"type": "课余", "revealed": False, "entered": False, "blocked": False}
    for (x, y) in all_cells[study_count + extra_count:]:
        map_data[f"{x},{y}"] = {"type": "测验", "revealed": False, "entered": False, "blocked": False}

    # 初始点亮：中心格的所有直接连通格
    for nk in conn[center_key]:
        if nk in map_data:
            map_data[nk]["revealed"] = True

    return map_data, conn, grid_size


# ==================== 角色状态管理 ====================
def init_character():
    return {
        "成绩水平": 40,
        "爱情进展": 0,
        "体能": 50,
        "精神状态": 50,
        "学习状态": 30,
        "班级关系": 20,
        "romance_state": "single",  # "single" | "dating"
    }


def clamp_stat(value, stat_name):
    """将状态值限制在合法范围内。"""
    if stat_name == "班级关系":
        return max(CLASS_REL_MIN, min(STAT_MAX, value))
    return max(STAT_MIN, min(STAT_MAX, value))


def apply_effects(character, effects):
    """将选项效果应用到角色状态，并限制范围。"""
    for stat in STAT_NAMES:
        if stat in effects:
            character[stat] = clamp_stat(character[stat] + effects[stat], stat)
    return character


def apply_class_rel_effects(character):
    """根据班级关系数值，应用每步被动效果。返回描述文本。"""
    cr = character["班级关系"]
    msg_parts = []

    if cr >= 50:
        if cr >= 75:
            character["精神状态"] = clamp_stat(character["精神状态"] + 2, "精神状态")
            character["学习状态"] = clamp_stat(character["学习状态"] + 2, "学习状态")
            msg_parts.append("良好的人际关系让你的精神状态和学习状态小幅恢复。")
        else:
            character["精神状态"] = clamp_stat(character["精神状态"] + 1, "精神状态")
            character["学习状态"] = clamp_stat(character["学习状态"] + 1, "学习状态")
            msg_parts.append("融洽的班级氛围让你感到轻松。")

    elif 0 <= cr < 10:
        character["爱情进展"] = min(character["爱情进展"], 20)

    elif -20 <= cr < 0:
        character["爱情进展"] = 0
        character["精神状态"] = clamp_stat(character["精神状态"] - 1, "精神状态")
        msg_parts.append("你在班级中有些孤立，精神状态略微下降。")

    elif cr < -20:
        if cr >= -50:
            character["精神状态"] = clamp_stat(character["精神状态"] - 2, "精神状态")
            character["学习状态"] = clamp_stat(character["学习状态"] - 2, "学习状态")
            msg_parts.append("班级中的冷遇让你的状态有所下滑。")
        elif cr >= -80:
            character["精神状态"] = clamp_stat(character["精神状态"] - 3, "精神状态")
            character["学习状态"] = clamp_stat(character["学习状态"] - 3, "学习状态")
            msg_parts.append("被孤立的感受让你心力交瘁……")
        else:
            character["精神状态"] = clamp_stat(character["精神状态"] - 5, "精神状态")
            character["学习状态"] = clamp_stat(character["学习状态"] - 5, "学习状态")
            msg_parts.append("众叛亲离的处境让你的精神状态急剧恶化！")

    return "\n".join(msg_parts)


def get_love_multiplier(character):
    """根据班级关系返回爱情进展的倍率。"""
    cr = character["班级关系"]
    if cr >= 75:
        return 1.3
    elif cr >= 50:
        return 1.15
    return 1.0


def handle_confession(character):
    """处理表白逻辑，返回 (结果描述, 是否成功, 是否有特殊弹窗)。"""
    love = character["爱情进展"]
    if love < 20:
        # 必定失败
        character["爱情进展"] = 0
        character["romance_state"] = "single"
        return "你鼓足勇气表白了……但 Ta 委婉地拒绝了你。💔 这段还未开始的感情就这样结束了。", False, True
    elif love < 50:
        roll = random.random()
        if roll < 0.40:
            character["爱情进展"] = 0
            character["romance_state"] = "single"
            return "你表白了，但 Ta 说「我们还是做朋友吧」。💔 你的心碎了一地。", False, True
        elif roll < 0.70:
            character["爱情进展"] = max(0, character["爱情进展"] // 2)
            character["romance_state"] = "single"
            return "Ta 犹豫了很久，最后还是摇了摇头……💔 也许还需要更多时间吧。", False, True
        elif roll < 0.98:
            character["romance_state"] = "dating"
            character["爱情进展"] = clamp_stat(character["爱情进展"] + 5, "爱情进展")
            return "Ta 红着脸点了点头！💕 你们在一起了！青春的篇章翻开了新的一页。", True, False
        else:
            character["romance_state"] = "dating"
            character["爱情进展"] = STAT_MAX
            return "Ta 说「其实我也喜欢你很久了……」💖 双向奔赴的爱情，美好得不像话！", True, False
    else:
        # love >= 50: 必定成功
        character["romance_state"] = "dating"
        character["爱情进展"] = clamp_stat(character["爱情进展"] + 8, "爱情进展")
        return "Ta 笑着接受了你的表白！💕 你们的故事正式开始了。", True, False


def check_love_zero(character):
    """检查爱情是否归零，若归零则重置恋爱状态并返回提示。"""
    if character["爱情进展"] <= 0 and character.get("romance_state") == "dating":
        character["romance_state"] = "single"
        character["爱情进展"] = 0
        return "💔 你们的感情走到了尽头……Ta 不喜欢你了，这段爱情结束了。"
    if character["爱情进展"] <= 0 and character.get("romance_state") == "single":
        character["爱情进展"] = 0
    return None


# ==================== 期末测验 ====================
def do_exam(character):
    """进行一次期末测验，基于成绩水平和学习状态检定。"""
    check_val = character["成绩水平"] + character["学习状态"]
    if check_val >= 140:
        result = "excellent"
        msg = "📊 期末测验成绩优异！你在年级名列前茅，老师对你赞不绝口。"
        effects = {"成绩水平": 5, "学习状态": 3, "精神状态": 2, "班级关系": 2}
    elif check_val >= 100:
        result = "good"
        msg = "📊 期末测验发挥不错，成绩稳居中上游，付出有了回报。"
        effects = {"成绩水平": 3, "学习状态": 2, "精神状态": 0, "班级关系": 1}
    elif check_val >= 60:
        result = "pass"
        msg = "📊 期末测验勉强过关，有些科目还需要加把劲啊。"
        effects = {"成绩水平": 0, "学习状态": -1, "精神状态": -1, "班级关系": 0}
    else:
        result = "fail"
        msg = "📊 期末测验考砸了……你看着成绩单，心里很不是滋味。"
        effects = {"成绩水平": -3, "学习状态": -3, "精神状态": -3, "班级关系": -2}

    apply_effects(character, effects)
    return result, msg


# ==================== 高考结局 ====================
def do_gaokao(character):
    """高考：综合检定所有状态，输出结局。"""
    c = character
    score = c["成绩水平"] + c["学习状态"]
    love = c["爱情进展"]
    body = c["体能"]
    spirit = c["精神状态"]
    cr = c["班级关系"]

    if score >= 160 and spirit >= 60:
        ending = "🏆【金榜题名】\n你以优异的成绩考入了理想的名校！高中三年的努力在这一刻得到了最好的回报。未来一片光明，愿你在大学继续追逐梦想！"
    elif love >= 60 and score >= 100:
        ending = "💕【青春无悔】\n你不仅收获了不错的成绩，更拥有了一段难忘的青春回忆。那个人，那些事，都将成为你心中最温暖的角落。"
    elif body >= 80:
        ending = "⚽【阳光少年】\n你在体育方面展现了惊人的天赋，凭借特长生的身份进入了心仪的大学。汗水浇灌的青春，同样精彩！"
    elif score >= 100:
        ending = "📚【天道酬勤】\n你凭借扎实的努力考上了一所不错的大学。虽然不是最顶尖的，但你知道，人生的路还很长，继续加油！"
    elif spirit >= 60 and cr >= 60:
        ending = "🌈【多彩青春】\n你的高中生活丰富多彩，虽然成绩不是最理想的，但你收获了友谊、爱情和对生活的热爱。这何尝不是一种成功？"
    elif score >= 40:
        ending = "🚶【平凡之路】\n高考成绩平平，你进入了一所普通院校。但你知道，人生不只有考试，还有无限的可能等待你去探索。"
    else:
        ending = "😢【重新出发】\n高考的结果不尽如人意，你感到了深深的挫败。但青春不只有一条路，收拾心情，重新出发吧！"

    return ending


# ==================== 游戏状态管理 ====================
def init_game_state():
    map_data, connections, grid_size = generate_map(1)
    return {
        "player_pos": [grid_size // 2, grid_size // 2],
        "progress": 0,
        "progress_max": PROGRESS_MAX_MAP[1],
        "map_count": 1,
        "grid_size": grid_size,
        "map_data": map_data,
        "connections": connections,
        "character": init_character(),
        "game_over": False,
        "message": "你踏入了重点高中的校门，新的高中生活开始了！点击已点亮的格子来探索吧。",
        "pending_cell": None,
        "pending_options": None,
        "pending_type": None,
        "exam_result": None,
        "ending": None,
        "bad_ending": None,
        "critical_stats": [],
        "in_exam_prep": False,
        "romance_state": "single",
        "history": [],  # 每张地图的探索记录
    }


def get_game_state():
    if 'game' not in session:
        session['game'] = init_game_state()
    return session['game']


def save_game_state(state):
    session['game'] = state


def build_full_grid(state):
    """构建完整网格数据，供前端渲染。"""
    grid = []
    for y in range(state["grid_size"]):
        row = []
        for x in range(state["grid_size"]):
            key = f"{x},{y}"
            cell = state["map_data"].get(key)
            if cell and cell["revealed"]:
                row.append({
                    "x": x, "y": y,
                    "type": cell["type"],
                    "icon": CELL_TYPE_CONFIG[cell["type"]]["icon"],
                    "color": CELL_TYPE_CONFIG[cell["type"]]["color"],
                    "entered": cell["entered"],
                    "blocked": cell["blocked"],
                })
            else:
                row.append(None)
        grid.append(row)
    return grid


def build_connection_lines(state):
    """构建连线数据：包含所有格子间的连通关系（首次进入即显示）。"""
    lines = []
    seen = set()
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
    """将指定格子的所有直接连通未点亮格变为已点亮。"""
    key = f"{x},{y}"
    for nk in state["connections"].get(key, []):
        if nk in state["map_data"] and not state["map_data"][nk]["revealed"]:
            state["map_data"][nk]["revealed"] = True


def check_bad_ending(state, effects):
    """检查是否触发坏结局：关键状态到达下限且本次未提升。"""
    # 先检查之前已标记的 critical_stats
    for stat in list(state["critical_stats"]):
        eff_val = effects.get(stat, 0)
        if eff_val <= 0 and state["character"][stat] <= get_stat_min(stat):
            state["game_over"] = True
            state["bad_ending"] = BAD_ENDING_MESSAGES.get(stat, f"你的{stat}已经跌入谷底……")
            state["message"] = f"💀 坏结局触发！你的{stat}已经降到了最低点……"
            return True
        elif eff_val > 0:
            state["critical_stats"].remove(stat)
        elif state["character"][stat] > get_stat_min(stat):
            state["critical_stats"].remove(stat)

    return False


def get_stat_min(stat_name):
    """获取状态的下限值。"""
    if stat_name == "班级关系":
        return CLASS_REL_MIN
    return STAT_MIN


def update_critical_stats(state):
    """更新已到达下限的状态列表。"""
    for stat in STAT_NAMES:
        if stat == "爱情进展":
            continue
        if state["character"][stat] <= get_stat_min(stat) and stat not in state["critical_stats"]:
            state["critical_stats"].append(stat)


def save_map_snapshot(state):
    """保存当前地图的探索快照到历史记录。"""
    cells_entered = []
    cells_revealed = 0
    for key, cell in state["map_data"].items():
        if cell["revealed"]:
            cells_revealed += 1
        if cell["entered"]:
            cells_entered.append(cell["type"])
    type_counts = {}
    for t in cells_entered:
        type_counts[t] = type_counts.get(t, 0) + 1
    state.setdefault("history", []).append({
        "map": state["map_count"],
        "semester": SEMESTER_NAMES.get(state["map_count"], ""),
        "grid_size": state["grid_size"],
        "progress": state["progress"],
        "cells_revealed": cells_revealed,
        "cells_entered": len(cells_entered),
        "types": type_counts,
    })


def check_progress_full(state):
    """检查进度是否已满。除高三下学期外，先进入期末备考阶段。"""
    if state["progress"] >= state["progress_max"]:
        if state.get("in_exam_prep"):
            result, msg = do_exam(state["character"])
            state["exam_result"] = msg
            state["in_exam_prep"] = False
            sem_name = SEMESTER_NAMES.get(state["map_count"] + 1, "")
            state["message"] = msg + f"\n\n新学期开始了——{sem_name}"
            save_map_snapshot(state)
            new_map, new_conn, new_size = generate_map(state["map_count"] + 1)
            state["map_data"] = new_map
            state["connections"] = new_conn
            state["grid_size"] = new_size
            state["player_pos"] = [new_size // 2, new_size // 2]
            state["progress"] = 0
            state["progress_max"] = PROGRESS_MAX_MAP[state["map_count"] + 1]
            state["map_count"] += 1
            state["pending_cell"] = None
            state["pending_options"] = None
            state["pending_type"] = None
            state["critical_stats"] = []
            return False

        if state["map_count"] < TOTAL_MAPS:
            # 高三下学期直接进高考，其余进入期末备考
            if state["map_count"] == TOTAL_MAPS - 1:
                # 高三上学期 → 直接期末测验然后进入高三下学期
                result, msg = do_exam(state["character"])
                state["exam_result"] = msg
                sem_name = SEMESTER_NAMES.get(state["map_count"] + 1, "")
                state["message"] = msg + f"\n\n最后一个学期开始了——{sem_name}"
                save_map_snapshot(state)
                new_map, new_conn, new_size = generate_map(state["map_count"] + 1)
                state["map_data"] = new_map
                state["connections"] = new_conn
                state["grid_size"] = new_size
                state["player_pos"] = [new_size // 2, new_size // 2]
                state["progress"] = 0
                state["progress_max"] = PROGRESS_MAX_MAP[state["map_count"] + 1]
                state["map_count"] += 1
                state["pending_cell"] = None
                state["pending_options"] = None
                state["pending_type"] = None
                state["critical_stats"] = []
                return False
            else:
                # 进入期末备考特殊地图
                state["in_exam_prep"] = True
                state["pending_cell"] = None
                state["pending_options"] = None
                state["pending_type"] = None
                state["message"] = "📚 期末考试临近！你需要为即将到来的考试做好备考准备。做出你的选择吧。"
                return False
        else:
            # 高三下学期：高考
            save_map_snapshot(state)
            ending = do_gaokao(state["character"])
            state["game_over"] = True
            state["ending"] = ending
            state["message"] = "🎓 高考结束！"
            return True
    return False


# ==================== API 路由 ====================
@app.route('/api/state')
def api_state():
    state = get_game_state()
    if state.get("in_exam_prep"):
        # 期末备考特殊地图：仅一个格子
        grid = [[{"x": 0, "y": 0, "type": "期末备考", "icon": "📚", "color": "#E67E22", "entered": False, "blocked": False}]]
        lines = []
        return jsonify({
            "player_pos": [0, 0],
            "progress": state["progress"],
            "progress_max": state["progress_max"],
            "map_count": state["map_count"],
            "total_maps": TOTAL_MAPS,
            "grid_size": 1,
            "semester_name": SEMESTER_NAMES.get(state["map_count"], ""),
            "grid": grid,
            "connection_lines": lines,
            "character": state["character"],
            "game_over": state["game_over"],
            "message": state["message"],
            "pending_cell": state["pending_cell"],
            "pending_options": state["pending_options"],
            "pending_type": state["pending_type"],
            "exam_result": state["exam_result"],
            "ending": state["ending"],
            "bad_ending": state["bad_ending"],
            "critical_stats": state["critical_stats"],
            "in_exam_prep": True,
            "romance_state": state["character"].get("romance_state"),
            "history": state.get("history", []),
        })
    grid = build_full_grid(state)
    lines = build_connection_lines(state)
    return jsonify({
        "player_pos": state["player_pos"],
        "progress": state["progress"],
        "progress_max": state["progress_max"],
        "map_count": state["map_count"],
        "total_maps": TOTAL_MAPS,
        "grid_size": state["grid_size"],
        "semester_name": SEMESTER_NAMES.get(state["map_count"], ""),
        "grid": grid,
        "connection_lines": lines,
        "character": state["character"],
        "game_over": state["game_over"],
        "message": state["message"],
        "pending_cell": state["pending_cell"],
        "pending_options": state["pending_options"],
        "pending_type": state["pending_type"],
        "exam_result": state["exam_result"],
        "ending": state["ending"],
        "bad_ending": state["bad_ending"],
        "critical_stats": state["critical_stats"],
        "in_exam_prep": False,
        "romance_state": state["character"].get("romance_state"),
        "history": state.get("history", []),
    })


@app.route('/api/enter', methods=['POST'])
def api_enter():
    """进入一个已点亮的格子。"""
    state = get_game_state()
    if state["game_over"]:
        return jsonify({"error": "游戏已结束"}), 400
    if state["pending_cell"] is not None:
        return jsonify({"error": "请先完成当前选择"}), 400

    data = request.get_json()
    x, y = data.get('x'), data.get('y')
    if x is None or y is None:
        return jsonify({"error": "缺少坐标"}), 400

    key = f"{x},{y}"
    if key not in state["map_data"]:
        return jsonify({"error": "无效坐标"}), 400

    cell = state["map_data"][key]
    if not cell["revealed"]:
        return jsonify({"error": "该区域尚未点亮"}), 400
    if cell["blocked"]:
        return jsonify({"error": "该区域已被封锁，无法再次进入"}), 400

    ctype = cell["type"]

    # 期末备考格子：特殊处理
    if ctype == "期末备考":
        state["pending_cell"] = [x, y]
        state["pending_options"] = EXAM_PREP_OPTIONS
        state["pending_type"] = "期末备考"
        save_game_state(state)
        return jsonify({
            "status": "ok",
            "pending": True,
            "cell_type": "期末备考",
            "options": [{"index": i, "label": o["label"], "desc": o["desc"]} for i, o in enumerate(EXAM_PREP_OPTIONS)],
        })

    # 入学格子：直接进入，无选项，不增加进度
    if ctype == "入学":
        if cell["entered"] and [x, y] == state["player_pos"]:
            return jsonify({"error": "你已经在这里了"}), 400
        cell["entered"] = True
        state["player_pos"] = [x, y]
        reveal_connected(state, x, y)
        state["message"] = "你站在校门口，一切从这里开始。"
        save_game_state(state)
        return jsonify({"status": "ok", "pending": False})

    # 可反复进入的格子：允许连续进入
    if ctype in REENTERABLE_TYPES:
        pass  # 即使已经在当前位置也允许进入
    else:
        # 不可反复进入的格子：检查是否已进入
        if cell["entered"] and ctype in BLOCKABLE_TYPES:
            return jsonify({"error": "该区域已被封锁，无法再次进入"}), 400

    # 获取选项
    if ctype in CELL_OPTIONS_MAP:
        if ctype == "恋爱":
            type_label, options = CELL_OPTIONS_MAP[ctype](state)
        else:
            type_label, options = CELL_OPTIONS_MAP[ctype]()
        state["pending_cell"] = [x, y]
        state["pending_options"] = options
        state["pending_type"] = type_label
        save_game_state(state)
        return jsonify({
            "status": "ok",
            "pending": True,
            "cell_type": type_label,
            "options": [{"index": i, "label": o["label"], "desc": o["desc"]} for i, o in enumerate(options)],
        })

    return jsonify({"error": "未知格子类型"}), 400


@app.route('/api/choose', methods=['POST'])
def api_choose():
    """在已进入的格子中做出选择。"""
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

    # 分离爱情进展效果并应用倍率
    love_effect = chosen.get("爱情进展", 0)
    adjusted_effects = dict(chosen)
    if love_effect > 0:
        mult = get_love_multiplier(state["character"])
        adjusted_effects["爱情进展"] = int(love_effect * mult)

    # 检查坏结局：在应用效果之前检查 critical_stats
    if check_bad_ending(state, adjusted_effects):
        save_game_state(state)
        return jsonify({
            "status": "ok",
            "game_over": True,
            "bad_ending": state["bad_ending"],
            "message": state["message"],
        })

    # 应用选项效果
    apply_effects(state["character"], adjusted_effects)

    # 应用班级关系被动效果
    class_msg = apply_class_rel_effects(state["character"])

    # 期末备考特殊逻辑：不进地图格子，直接触发测验
    if ctype == "期末备考":
        state["message"] = f"你选择了【{chosen['label']}】—— {chosen['desc']}"
        if class_msg:
            state["message"] += "\n" + class_msg
        state["pending_cell"] = None
        state["pending_options"] = None
        state["pending_type"] = None
        check_progress_full(state)
        save_game_state(state)
        return jsonify({
            "status": "ok",
            "message": state["message"],
            "character": state["character"],
            "progress": state["progress"],
            "progress_max": state["progress_max"],
            "game_over": state["game_over"],
            "map_count": state["map_count"],
            "exam_result": state["exam_result"],
            "ending": state["ending"],
            "bad_ending": state["bad_ending"],
            "critical_stats": state["critical_stats"],
            "in_exam_prep": state.get("in_exam_prep", False),
            "romance_state": state["character"].get("romance_state"),
        })

    # 标记已进入
    state["map_data"][key]["entered"] = True
    state["player_pos"] = [px, py]

    # 可封锁类型进入后封锁
    if ctype in BLOCKABLE_TYPES:
        state["map_data"][key]["blocked"] = True

    # 点亮连通格
    reveal_connected(state, px, py)

    # 增加进度
    state["progress"] += 1

    # 处理表白逻辑
    confession_msg = None
    confession_success = None
    if chosen.get("_is_confession"):
        confession_msg, confession_success, love_popup = handle_confession(state["character"])
        state["message"] = f"你选择了【{chosen['label']}】—— {confession_msg}"
    else:
        state["message"] = f"你选择了【{chosen['label']}】—— {chosen['desc']}"

    if class_msg:
        state["message"] += "\n" + class_msg

    # 检查爱情归零
    love_zero_msg = check_love_zero(state["character"])
    if love_zero_msg:
        state["message"] += "\n" + love_zero_msg

    # 清除 pending 状态
    state["pending_cell"] = None
    state["pending_options"] = None
    state["pending_type"] = None

    # 更新 critical_stats
    update_critical_stats(state)

    # 检查进度是否已满
    check_progress_full(state)

    save_game_state(state)
    return jsonify({
        "status": "ok",
        "message": state["message"],
        "character": state["character"],
        "player_pos": state["player_pos"],
        "progress": state["progress"],
        "progress_max": state["progress_max"],
        "game_over": state["game_over"],
        "map_count": state["map_count"],
        "exam_result": state["exam_result"],
        "ending": state["ending"],
        "bad_ending": state["bad_ending"],
        "critical_stats": state["critical_stats"],
        "romance_state": state["character"].get("romance_state"),
        "love_zero_popup": love_zero_msg if love_zero_msg and state["character"].get("romance_state") == "single" else None,
    })


# ==================== 前端页面 ====================
HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>高中生涯 - 无悔青春</title>
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #e0e0e0;
    }
    #app {
        display: flex;
        gap: 25px;
        padding: 20px;
        align-items: flex-start;
    }
    /* ---- 网格容器 ---- */
    #grid-wrapper {
        position: relative;
        background: rgba(255,255,255,0.05);
        padding: 10px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    #grid {
        display: grid;
        gap: 3px;
    }
    #conn-svg {
        position: absolute;
        top: 10px; left: 10px;
        pointer-events: none;
        z-index: 1;
    }
    .cell {
        border-radius: 6px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        border: 2px solid transparent;
        cursor: pointer;
        transition: all 0.2s;
        position: relative;
        user-select: none;
        color: #fff;
        text-shadow: 0 1px 3px rgba(0,0,0,0.4);
        z-index: 2;
    }
    .cell:hover:not(.fog):not(.blocked) {
        transform: scale(1.10);
        border-color: #fff;
        box-shadow: 0 0 14px rgba(255,255,255,0.35);
        z-index: 3;
    }
    .cell.current {
        border: 3px solid #fff !important;
        box-shadow: 0 0 16px rgba(255,215,0,0.55);
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 8px rgba(255,215,0,0.4); }
        50% { box-shadow: 0 0 20px rgba(255,215,0,0.8); }
    }
    .cell.entered:not(.reenterable) { filter: brightness(0.6); }
    .cell.entered.reenterable { filter: brightness(0.8); }
    .cell.blocked {
        filter: brightness(0.3) saturate(0.15);
        cursor: not-allowed;
    }
    .cell.blocked::after {
        content: "🚫";
        position: absolute;
        font-size: 13px;
        pointer-events: none;
    }
    .cell.fog {
        background: rgba(160,170,190,0.18);
        color: #7a7a9a;
        cursor: default;
        font-size: 20px;
        border: 1px dashed rgba(255,255,255,0.12);
    }
    .cell .icon { font-size: 20px; line-height: 1; }
    .cell .label { font-size: 10px; margin-top: 2px; opacity: 0.85; }

    /* ---- 信息面板 ---- */
    #info-panel {
        width: 280px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .panel-box {
        background: rgba(255,255,255,0.06);
        padding: 12px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .panel-box h4 {
        font-size: 12px;
        color: #aaa;
        margin-bottom: 6px;
    }
    .progress-bar {
        width: 100%; height: 14px;
        background: rgba(255,255,255,0.1);
        border-radius: 7px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%; width: 0%;
        background: linear-gradient(90deg, #4A90E2, #7ED321);
        border-radius: 7px;
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .progress-fill.flash {
        animation: progressFlash 0.6s ease-out;
    }
    @keyframes progressFlash {
        0% { filter: brightness(2); box-shadow: 0 0 20px rgba(126,211,33,0.8); }
        100% { filter: brightness(1); box-shadow: 0 0 0px rgba(126,211,33,0); }
    }
    .progress-text-pop {
        display: inline-block;
        animation: popIn 0.4s ease-out;
    }
    @keyframes popIn {
        0% { transform: scale(1.6); color: #FFD700; }
        100% { transform: scale(1); color: #888; }
    }
    #message-box {
        min-height: 50px;
        max-height: 160px;
        font-size: 12px;
        line-height: 1.6;
        color: #ccc;
        white-space: pre-line;
        overflow-y: auto;
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 3px 0;
        font-size: 11px;
    }
    .stat-row .stat-name { width: 32px; color: #aaa; }
    .stat-bar-bg {
        flex: 1; height: 7px;
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
        overflow: hidden;
        margin: 0 6px;
    }
    .stat-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.4s;
    }
    .stat-row .stat-val { width: 22px; text-align: right; font-size: 10px; color: #ccc; }
    .critical-warn { color: #e74c3c !important; font-weight: bold; }

    button {
        padding: 10px;
        background: #4A90E2;
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 13px;
        font-weight: bold;
        transition: background 0.2s;
    }
    button:hover { background: #5AA0F2; }

    /* ---- 选项弹窗 ---- */
    #modal-overlay {
        display: none;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.7);
        z-index: 100;
        justify-content: center;
        align-items: center;
    }
    #modal-overlay.active { display: flex; }
    #modal {
        background: #1e1e3a;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 16px;
        padding: 24px;
        max-width: 380px;
        width: 90%;
        box-shadow: 0 16px 48px rgba(0,0,0,0.5);
    }
    #modal h3 { text-align: center; margin-bottom: 4px; font-size: 17px; }
    #modal .subtitle { text-align: center; color: #888; font-size: 11px; margin-bottom: 14px; }
    #modal .option-btn {
        display: block; width: 100%; text-align: left;
        padding: 10px 14px; margin: 5px 0;
        background: rgba(255,255,255,0.06);
        border: 2px solid rgba(255,255,255,0.1);
        border-radius: 10px; color: #ddd;
        font-size: 13px; cursor: pointer; transition: all 0.2s;
    }
    #modal .option-btn:hover {
        background: rgba(74,144,226,0.25);
        border-color: #4A90E2;
    }
    #modal .option-btn .opt-label { font-weight: bold; }
    #modal .option-btn .opt-desc { font-size: 10px; color: #999; margin-top: 2px; }

    /* ---- 结局弹窗 ---- */
    #ending-overlay {
        display: none;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.85);
        z-index: 200;
        justify-content: center;
        align-items: center;
    }
    #ending-overlay.active { display: flex; }
    #ending-box {
        background: #1a1a2e;
        border: 2px solid #FFD700;
        border-radius: 20px;
        padding: 28px;
        max-width: 440px;
        width: 90%;
        text-align: center;
        box-shadow: 0 0 60px rgba(255,215,0,0.3);
    }
    #ending-box.bad {
        border-color: #e74c3c;
        box-shadow: 0 0 60px rgba(231,76,60,0.4);
    }
    #ending-box h2 { font-size: 22px; margin-bottom: 14px; }
    #ending-box .ending-text { font-size: 14px; line-height: 1.8; white-space: pre-line; color: #ddd; margin-bottom: 18px; }
</style>
</head>
<body>

<div id="app">
    <div id="grid-wrapper">
        <svg id="conn-svg"></svg>
        <div id="grid"></div>
    </div>
    <div id="info-panel">
        <div class="panel-box">
            <h4 id="semester-title">📅 加载中...</h4>
            <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
            <small style="color:#888;"><span id="progress-text">0</span>/<span id="progress-max-text">12</span></small>
        </div>
        <div class="panel-box" id="message-box">加载中...</div>
        <div class="panel-box" id="stats-box">
            <h4>📊 角色状态 <span id="critical-indicator" style="color:#e74c3c;display:none;">⚠️危急</span></h4>
            <div id="stats-container"></div>
        </div>
        <button onclick="resetGame()">🔄 重新开始</button>
    </div>
</div>

<!-- 选项弹窗 -->
<div id="modal-overlay">
    <div id="modal">
        <h3 id="modal-title"></h3>
        <div class="subtitle" id="modal-subtitle"></div>
        <div id="modal-options"></div>
    </div>
</div>

<!-- 爱情归零弹窗 -->
<div id="love-popup-overlay" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:150;justify-content:center;align-items:center;">
    <div style="background:#1e1e3a;border:2px solid #FF6B9D;border-radius:16px;padding:24px;max-width:360px;text-align:center;box-shadow:0 0 40px rgba(255,107,157,0.3);">
        <h3 style="color:#FF6B9D;">💔 爱情终结</h3>
        <p id="love-popup-msg" style="color:#ddd;font-size:14px;line-height:1.6;margin:12px 0;"></p>
        <button onclick="document.getElementById('love-popup-overlay').style.display='none'" style="background:#FF6B9D;">我知道了</button>
    </div>
</div>

<!-- 结局弹窗 -->
<div id="ending-overlay">
    <div id="ending-box">
        <h2 id="ending-title">🎓 高中生涯 · 终章</h2>
        <div class="ending-text" id="ending-text"></div>
        <button onclick="resetGame()">🔄 再来一次</button>
    </div>
</div>

<script>
    const CELL_ICONS = { "入学":"🎓", "学习":"📚", "课余":"⚽", "测验":"📝", "恋爱":"💕", "造梦":"✨", "研学":"🔬", "期末备考":"📚" };
    const CELL_COLORS = { "入学":"#FFD700", "学习":"#4A90E2", "课余":"#F5A623", "测验":"#E74C3C", "恋爱":"#FF6B9D", "造梦":"#9013FE", "研学":"#1ABC9C", "期末备考":"#E67E22" };
    const STAT_COLORS = { "成绩水平":"#4A90E2", "爱情进展":"#FF6B9D", "体能":"#F5A623", "精神状态":"#7ED321", "学习状态":"#9013FE", "班级关系":"#1ABC9C" };
    const STAT_LABELS = { "成绩水平":"成绩", "爱情进展":"爱情", "体能":"体能", "精神状态":"精神", "学习状态":"学习", "班级关系":"班缘" };
    const REENTERABLE = ["恋爱", "造梦"];
    const CELL_SIZE = 54;
    const CELL_GAP = 5;

    let currentState = null;

    async function fetchState() {
        const resp = await fetch('/api/state');
        currentState = await resp.json();
        render();
        if (currentState.ending || currentState.bad_ending) showEnding();
    }

    function render() {
        if (!currentState) return;
        const { grid, player_pos, progress, progress_max, map_count, grid_size, semester_name,
                character, message, game_over, pending_cell, critical_stats, connection_lines } = currentState;
        const gridEl = document.getElementById('grid');
        const total = CELL_SIZE + CELL_GAP;

        gridEl.style.gridTemplateColumns = `repeat(${grid_size}, ${CELL_SIZE}px)`;
        gridEl.style.gridTemplateRows = `repeat(${grid_size}, ${CELL_SIZE}px)`;
        gridEl.innerHTML = '';

        for (let row = 0; row < grid_size; row++) {
            for (let col = 0; col < grid_size; col++) {
                const cellData = grid[row][col];
                const div = document.createElement('div');
                div.className = 'cell';
                div.style.width = CELL_SIZE + 'px';
                div.style.height = CELL_SIZE + 'px';

                if (cellData === null) {
                    div.classList.add('fog');
                    div.innerHTML = '❓';
                } else {
                    div.style.background = CELL_COLORS[cellData.type] || '#555';
                    div.innerHTML = `<span class="icon">${CELL_ICONS[cellData.type]||'❓'}</span><span class="label">${cellData.type}</span>`;
                    div.dataset.x = cellData.x;
                    div.dataset.y = cellData.y;

                    if (cellData.x === player_pos[0] && cellData.y === player_pos[1]) {
                        div.classList.add('current');
                    }
                    if (cellData.entered) {
                        if (REENTERABLE.includes(cellData.type)) {
                            div.classList.add('reenterable');
                        } else {
                            div.classList.add('entered');
                        }
                    }
                    if (cellData.blocked) div.classList.add('blocked');

                    // 点击事件
                    const isCurrent = cellData.x === player_pos[0] && cellData.y === player_pos[1];
                    const canEnter = !cellData.blocked &&
                        (REENTERABLE.includes(cellData.type) || !isCurrent || !cellData.entered);
                    if (canEnter && !game_over) {
                        div.addEventListener('click', () => enterCell(cellData.x, cellData.y));
                    }
                }
                gridEl.appendChild(div);
            }
        }

        // 渲染连线
        renderConnections(connection_lines, grid_size, total);

        document.getElementById('semester-title').textContent = '📅 ' + (semester_name || '');
        // 进度动画
        const progEl = document.getElementById('progress-text');
        const oldProg = parseInt(progEl.textContent) || 0;
        if (progress !== oldProg) {
            progEl.textContent = progress;
            progEl.classList.remove('progress-text-pop');
            void progEl.offsetWidth;
            progEl.classList.add('progress-text-pop');
            const fillEl = document.getElementById('progress-fill');
            fillEl.classList.remove('flash');
            void fillEl.offsetWidth;
            fillEl.classList.add('flash');
        } else {
            progEl.textContent = progress;
        }
        document.getElementById('progress-max-text').textContent = progress_max;
        document.getElementById('progress-fill').style.width = (progress / progress_max * 100) + '%';
        document.getElementById('message-box').textContent = message;

        // 危急指示器
        const critInd = document.getElementById('critical-indicator');
        if (critical_stats && critical_stats.length > 0) {
            critInd.style.display = 'inline';
        } else {
            critInd.style.display = 'none';
        }

        // 渲染角色状态
        const statsEl = document.getElementById('stats-container');
        const statMax = 100;
        statsEl.innerHTML = '';
        for (const [stat, val] of Object.entries(character)) {
            const isClassRel = stat === '班级关系';
            const minVal = isClassRel ? -100 : 0;
            const range = statMax - minVal;
            const pct = ((val - minVal) / range * 100);
            const critical = critical_stats && critical_stats.includes(stat);
            statsEl.innerHTML += `
                <div class="stat-row">
                    <span class="stat-name ${critical ? 'critical-warn' : ''}">${STAT_LABELS[stat]||stat}</span>
                    <div class="stat-bar-bg"><div class="stat-bar-fill" style="width:${pct}%;background:${STAT_COLORS[stat]}"></div></div>
                    <span class="stat-val ${critical ? 'critical-warn' : ''}">${val}</span>
                </div>`;
        }
    }

    function renderConnections(lines, gridSize, total) {
        const svg = document.getElementById('conn-svg');
        const svgW = gridSize * total - CELL_GAP;
        const svgH = svgW;
        svg.setAttribute('width', svgW);
        svg.setAttribute('height', svgH);
        svg.setAttribute('viewBox', `0 0 ${svgW} ${svgH}`);
        svg.innerHTML = '';

        if (!lines) return;
        const half = CELL_SIZE / 2;
        for (const [x1, y1, x2, y2] of lines) {
            const cx1 = x1 * total + half;
            const cy1 = y1 * total + half;
            const cx2 = x2 * total + half;
            const cy2 = y2 * total + half;
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', cx1);
            line.setAttribute('y1', cy1);
            line.setAttribute('x2', cx2);
            line.setAttribute('y2', cy2);
            line.setAttribute('stroke', 'rgba(255,255,255,0.45)');
            line.setAttribute('stroke-width', '3');
            line.setAttribute('stroke-linecap', 'round');
            line.setAttribute('filter', 'drop-shadow(0 0 2px rgba(255,255,255,0.3))');
            svg.appendChild(line);
        }
    }

    async function enterCell(x, y) {
        if (currentState.game_over) return;
        const resp = await fetch('/api/enter', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({x, y})
        });
        const data = await resp.json();
        if (data.error) { alert(data.error); return; }
        if (data.pending) {
            showModal(data.cell_type, data.options);
        } else {
            await fetchState();
        }
    }

    function showModal(cellType, options) {
        document.getElementById('modal-title').textContent = (CELL_ICONS[cellType]||'') + ' ' + cellType;
        document.getElementById('modal-subtitle').textContent = '请做出你的选择：';
        const optsEl = document.getElementById('modal-options');
        optsEl.innerHTML = '';
        options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.innerHTML = `<div class="opt-label">${opt.label}</div><div class="opt-desc">${opt.desc}</div>`;
            btn.addEventListener('click', () => makeChoice(opt.index));
            optsEl.appendChild(btn);
        });
        document.getElementById('modal-overlay').classList.add('active');
    }

    async function makeChoice(index) {
        document.getElementById('modal-overlay').classList.remove('active');
        const resp = await fetch('/api/choose', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({choice: index})
        });
        const data = await resp.json();
        currentState = { ...currentState, ...data };
        // 爱情归零弹窗
        if (data.love_zero_popup) {
            document.getElementById('love-popup-msg').textContent = data.love_zero_popup;
            document.getElementById('love-popup-overlay').style.display = 'flex';
        }
        // 重新获取完整状态以刷新grid
        await fetchState();
    }

    function showEnding() {
        const overlay = document.getElementById('ending-overlay');
        const box = document.getElementById('ending-box');
        const title = document.getElementById('ending-title');
        const text = document.getElementById('ending-text');

        if (currentState.bad_ending) {
            box.classList.add('bad');
            title.textContent = '💀 青春陨落';
            title.style.color = '#e74c3c';
            text.innerHTML = currentState.bad_ending + buildSummaryHTML();
        } else if (currentState.ending) {
            box.classList.remove('bad');
            title.textContent = '🎓 高中生涯 · 终章';
            title.style.color = '#FFD700';
            text.innerHTML = currentState.ending + buildSummaryHTML();
        }
        overlay.classList.add('active');
    }

    function buildSummaryHTML() {
        const char = currentState.character || {};
        const hist = currentState.history || [];
        let html = '<hr style="border-color:rgba(255,255,255,0.15);margin:16px 0;"><h4 style="color:#aaa;margin-bottom:8px;">📊 最终状态</h4>';
        for (const [stat, val] of Object.entries(char)) {
            if (stat === 'romance_state') continue;
            const label = STAT_LABELS[stat] || stat;
            const pct = Math.max(0, Math.min(100, (stat === '班级关系' ? (val + 100) / 2 : val)));
            html += `<div style="display:flex;align-items:center;font-size:11px;margin:2px 0;">
                <span style="width:36px;text-align:right;color:#aaa;">${label}</span>
                <div style="flex:1;height:7px;background:rgba(255,255,255,0.1);border-radius:4px;margin:0 6px;">
                    <div style="height:100%;width:${pct}%;background:${STAT_COLORS[stat]};border-radius:4px;"></div>
                </div><span style="width:24px;">${val}</span></div>`;
        }
        if (hist.length > 0) {
            html += '<h4 style="color:#aaa;margin:12px 0 6px;">📅 学期回顾</h4>';
            hist.forEach(h => {
                const types = Object.entries(h.types||{}).map(([t,c]) => `${t}×${c}`).join(' ');
                html += `<div style="font-size:10px;color:#999;margin:2px 0;">${h.semester} (${h.grid_size}×${h.grid_size}) 探索${h.cells_entered}格 ${types}</div>`;
            });
        }
        html += `<div style="font-size:10px;color:#666;margin-top:8px;">恋爱状态：${char.romance_state === 'dating' ? '💕 恋爱中' : '💔 单身'}</div>`;
        return html;
    }

    function resetGame() {
        location.reload();
    }

    fetchState();
</script>
</body>
</html>
'''


@app.route('/')
def index():
    session.pop('game', None)
    session['game'] = init_game_state()
    return render_template_string(HTML_TEMPLATE)


if __name__ == '__main__':
    app.run(debug=True)
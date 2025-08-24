from enum import Enum

# 游戏参数
INIT_FOOD = 20
INIT_FERTILITY = 100

FARM_MAX_PER_GRID_PER_TURN = 5
PIECE_MOVE_MAX_PER_TURN = 3
PIECE_KING_MOVE_MAX_PER_TURN = 1
SKILL_MAX_PER_TURN = 2

PIECE_BASIC_MOVE_COST = {
    'pawn': 1,
    'knight': 3,
    'bishop': 3,
    'rook': 5,
    'queen': 9,
    'king': 3
}
def PIECE_MOVE_COST(typ, moved_times):
    if typ == 'king' and moved_times >= PIECE_KING_MOVE_MAX_PER_TURN:
        return 9999
    return PIECE_BASIC_MOVE_COST[typ] + 2 * moved_times


# 游戏阶段枚举
class GamePhase(Enum):
    ACTION = "action"  # 行动阶段
    MOVE = "move"  # 走子阶段

# 管理视图枚举
class ManagementView(Enum):
    NONE = "none"  # 正常视图
    TAX = "tax"    # 收税视图
    FARM = "farm"  # 屯田视图

# 游戏事件定义
class GameEvent:
    SKILL_CAST = 1   # 技能释放
    TAX_COLLECT = 2  # 征税
    TURN_END = 3     # 回合结束
    PHASE_CHANGE = 4 # 阶段变化

# 资源系统
class ResourceSystem:
    def __init__(self):
        self.food = {'black': INIT_FOOD, 'white': INIT_FOOD}
        self.fertility = [[INIT_FERTILITY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # 丰饶度
        self.territory = [[None  for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # 领土控制
        self.tax_grid =  [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # 税收标记
        self.farm_grid = [[0     for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # 屯田次数

    def update_fertility(self, board):
        # 行动阶段开始前，任何格子上如果有棋子，则丰饶度-5
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if board[row][col]:
                    self.fertility[row][col] = max(0, self.fertility[row][col] - 5)

    def collect_tax(self, player_color):
        # 征税逻辑：根据标记的税收格子获得粮草
        total_tax = 0
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.tax_grid[row][col] and self.territory[row][col] == player_color:
                    tax_amount = self.fertility[row][col] // 10
                    total_tax += tax_amount
                    self.fertility[row][col] = max(0, self.fertility[row][col] - 10)

        self.food[player_color] += total_tax
        return total_tax

    def implement_farming(self, player_color):
        # 实施屯田计划
        total_farm_cost = 0
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                farm_times = self.farm_grid[row][col]
                if farm_times > 0 and self.territory[row][col] == player_color:
                    farm_cost = farm_times * 10
                    if self.food[player_color] >= farm_cost:
                        self.food[player_color] -= farm_cost
                        self.fertility[row][col] += farm_times * 5
                        total_farm_cost += farm_cost
                    else:
                        # 粮草不足，调整屯田次数
                        max_affordable = self.food[player_color] // 10
                        actual_times = min(farm_times, max_affordable)
                        actual_cost = actual_times * 10
                        self.food[player_color] -= actual_cost
                        self.fertility[row][col] += actual_times * 5
                        total_farm_cost += actual_cost
                        self.farm_grid[row][col] = actual_times

        return total_farm_cost

    def update_territory(self, row, col, color):
        # 更新领土控制
        self.territory[row][col] = color

    def reset_management_grids(self):
        # 重置管理网格
        self.tax_grid = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.farm_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# 技能系统
class SkillSystem:
    SKILL_COSTS = {
        'pawn': 10,  # 兵技能消耗
        # 'knight': 10,  # 马技能消耗
        'rook': 10,  # 车技能消耗
        # 'bishop': 10,  # 象技能消耗
        # 'queen': 50,  # 后召唤消耗
        # 'king': 10,  # 王技能消耗
    }

    def __init__(self, resource_system):
        self.resource_system = resource_system

    def can_cast_skill(self, piece_type, player_color):
        return self.resource_system.food[player_color] >= self.SKILL_COSTS.get(piece_type, 0)

    def cast_skill(self, piece_type, player_color):
        if self.can_cast_skill(piece_type, player_color):
            self.resource_system.food[player_color] -= self.SKILL_COSTS[piece_type]
            return True
        return False


# 显示参数
SCREEN_SCALE = 0.75
scl = lambda x: round(x * SCREEN_SCALE)

SCREEN_WIDTH = scl(1600)
SCREEN_HEIGHT = scl(900)
GAME_FONT = "fonts/Minecraftia-Regular-1.ttf"
GAME_BTN_FONT = "fonts/simsun.ttc"
GRID_SIZE = 8  # 8x8棋盘

# 透明度常量
BEHIND_OBST_TRANS = 0.6  # 棋子在障碍物下的透明度

# 网格中心点坐标
POS_GRID_NW_CENTRE = (scl(543), scl(193))  # 左上第一格的中心点
POS_GRID_SE_CENTRE = (scl(1062), scl(708))  # 右下最后一格的中心点

# 提示栏坐标
POS_INFO_NW = (scl(1200), scl(100))  # 文本起始点
POS_INFO_SE = (scl(1540), scl(810))  # （没用）

# 计算网格间距
GRID_SPACING_X = (POS_GRID_SE_CENTRE[0] - POS_GRID_NW_CENTRE[0]) / (GRID_SIZE - 1)
GRID_SPACING_Y = (POS_GRID_SE_CENTRE[1] - POS_GRID_NW_CENTRE[1]) / (GRID_SIZE - 1)

# 棋子大小
PIECE_SIZE = scl(60)

# 颜色定义
BACKGROUND_COLOUR = (22, 70, 33)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)
HIGHLIGHT_GREEN = (0, 255, 0, 128)
HIGHLIGHT_RED = (255, 0, 0, 128)

# 字符串优化
def to_times(times: int) -> str:
    match times:
        case 1:
            return "once"
        case 2:
            return "twice"
        case _:
            return "%d times" % times


# 杂项
CONSOLE_LOGGING = True
FILE_LOGGING_NAME = "log/game.log"

import pygame
import sys
import os
import math
from collections import defaultdict

# 初始化pygame
pygame.init()

# 游戏常量
SCREEN_SCALE = 0.7
scl = lambda x: int(x * SCREEN_SCALE)

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

POS_INFO_NW = (scl(1200), scl(100))
POS_INFO_SE = (scl(1540), scl(810))

# 计算网格间距
GRID_SPACING_X = (POS_GRID_SE_CENTRE[0] - POS_GRID_NW_CENTRE[0]) / (GRID_SIZE - 1)
GRID_SPACING_Y = (POS_GRID_SE_CENTRE[1] - POS_GRID_NW_CENTRE[1]) / (GRID_SIZE - 1)

# 棋子大小
PIECE_SIZE = scl(60)

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Custom Chess Game")

# 游戏事件定义
class GameEvent:
    SKILL_CAST = 1  # 技能释放
    TAX_COLLECT = 2 # 征税
    TURN_END = 3    # 回合结束

# 事件处理器
class EventHandler:
    def __init__(self):
        self.listeners = defaultdict(list)

    def add_listener(self, event_type, callback):
        self.listeners[event_type].append(callback)

    def dispatch(self, event_type, data=None):
        for callback in self.listeners[event_type]:
            callback(data)

# 资源系统
class ResourceSystem:
    def __init__(self):
        self.food = {'black': 600, 'white': 600}  # 初始粮草值设为600
        self.fertility = [[100 for _ in range(8)] for _ in range(8)]  # 丰饶度初始化为100
        # 添加叛乱值
        self.rebellion = [[0 for _ in range(8)] for _ in range(8)]

    def update_fertility(self, board):
        # 每回合丰饶度衰减/恢复
        for row in range(8):
            for col in range(8):
                if board[row][col]:
                    self.fertility[row][col] = max(0, self.fertility[row][col] - 10)
                else:
                    self.fertility[row][col] = min(100, self.fertility[row][col] + 5)

    def collect_tax(self, player, board):
        # 征税逻辑：根据控制的格子丰饶度获得粮草
        total_tax = 0
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color == player.color:
                    total_tax += self.fertility[row][col] // 10
        self.food[player.color] += total_tax
        return total_tax

# 技能系统
class SkillSystem:
    SKILL_COSTS = {
        'pawn': 10,    # 兵技能消耗
        'knight': 10,  # 马技能消耗
        'rook': 10,    # 车技能消耗
        'bishop': 10,  # 象技能消耗
        'queen': 50,   # 后召唤消耗
        'king': 10     # 王技能消耗
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

# 加载图片
def load_images():
    images = {}
    # 确保有images文件夹
    if not os.path.exists("images"):
        os.makedirs("images")
        print("Please put image resources in the images folder")

    # 尝试加载图片，如果失败则使用彩色方块代替
    try:
        images['board'] = pygame.image.load("images/board.png").convert_alpha()
        images['board'] = pygame.transform.scale(images['board'], (SCREEN_WIDTH, SCREEN_HEIGHT))
    except:
        try:
            images['board'] = pygame.image.load("images/beach.png").convert_alpha()
            images['board'] = pygame.transform.scale(images['board'], (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            print("Cannot load board.png, using default background")
            images['board'] = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            images['board'].fill(LIGHT_BROWN)

    # 加载棋子图片
    piece_colors = ['black', 'white']
    piece_types = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
    for color in piece_colors:
        # 加载通用颜色棋子
        try:
            images[f'piece_{color}'] = pygame.image.load(f"images/piece_{color}.png").convert_alpha()
            images[f'piece_{color}'] = pygame.transform.scale(images[f'piece_{color}'], (PIECE_SIZE, PIECE_SIZE))
        except:
            print(f"Cannot load piece_{color}.png, using default piece")
            images[f'piece_{color}'] = pygame.Surface((PIECE_SIZE, PIECE_SIZE), pygame.SRCALPHA)
            if color == 'black':
                pygame.draw.circle(images[f'piece_{color}'], BLACK, (PIECE_SIZE // 2, PIECE_SIZE // 2), PIECE_SIZE // 2)
            elif color == 'white':
                pygame.draw.circle(images[f'piece_{color}'], WHITE, (PIECE_SIZE // 2, PIECE_SIZE // 2), PIECE_SIZE // 2)

        # 加载特定类型棋子
        for ptype in piece_types:
            try:
                images[f'piece_{color}_{ptype}'] = pygame.image.load(f"images/piece_{color}_{ptype}.png").convert_alpha()
                images[f'piece_{color}_{ptype}'] = pygame.transform.scale(images[f'piece_{color}_{ptype}'], (PIECE_SIZE, PIECE_SIZE))
            except:
                print(f"Cannot load piece_{color}_{ptype}.png, using default piece")
                # 如果没有专用贴图，将使用通用颜色贴图

    # 加载障碍物贴图
    for color in piece_colors:
        try:
            images[f'obstacle_{color}_lujiao'] = pygame.image.load(f"images/obstacle_{color}_lujiao.png").convert_alpha()
            images[f'obstacle_{color}_lujiao'] = pygame.transform.scale(images[f'obstacle_{color}_lujiao'], (PIECE_SIZE, PIECE_SIZE))
        except:
            print(f"Cannot load obstacle_{color}_lujiao.png, using default indicator")
            images[f'obstacle_{color}_lujiao'] = pygame.Surface((PIECE_SIZE, PIECE_SIZE), pygame.SRCALPHA)
            # 使用颜色圆圈作为默认显示
            circle_color = BLACK if color == 'black' else WHITE
            pygame.draw.circle(images[f'obstacle_{color}_lujiao'], circle_color, (PIECE_SIZE // 2, PIECE_SIZE // 2), PIECE_SIZE // 3)

        # 新增：加载堡垒贴图
        try:
            images[f'obstacle_{color}_fortress'] = pygame.image.load(f"images/obstacle_{color}_fortress.png").convert_alpha()
            images[f'obstacle_{color}_fortress'] = pygame.transform.scale(images[f'obstacle_{color}_fortress'], (PIECE_SIZE, PIECE_SIZE))
        except:
            print(f"Cannot load obstacle_{color}_fortress.png, using default indicator")
            images[f'obstacle_{color}_fortress'] = pygame.Surface((PIECE_SIZE, PIECE_SIZE), pygame.SRCALPHA)
            circle_color = BLACK if color == 'black' else WHITE
            pygame.draw.rect(images[f'obstacle_{color}_fortress'], circle_color, (0, 0, PIECE_SIZE, PIECE_SIZE))

    # 加载高亮和有效移动提示
    try:
        images['highlight'] = pygame.image.load("images/highlight.png").convert_alpha()
        images['highlight'] = pygame.transform.scale(images['highlight'], (PIECE_SIZE + 20, PIECE_SIZE + 20))
    except:
        print("Cannot load highlight.png, using default highlight effect")
        images['highlight'] = pygame.Surface((PIECE_SIZE + 20, PIECE_SIZE + 20), pygame.SRCALPHA)
        pygame.draw.circle(images['highlight'], (255, 255, 0, 128), (PIECE_SIZE // 2 + 10, PIECE_SIZE // 2 + 10),
                           PIECE_SIZE // 2 + 5, 5)

    try:
        images['valid_move'] = pygame.image.load("images/valid_move.png").convert_alpha()
        images['valid_move'] = pygame.transform.scale(images['valid_move'], (PIECE_SIZE // 2, PIECE_SIZE // 2))
    except:
        print("Cannot load valid_move.png, using default indicator")
        images['valid_move'] = pygame.Surface((PIECE_SIZE // 2, PIECE_SIZE // 2), pygame.SRCALPHA)
        pygame.draw.circle(images['valid_move'], (0, 255, 0, 128), (PIECE_SIZE // 4, PIECE_SIZE // 4), PIECE_SIZE // 4)

    return images


# 将网格坐标转换为屏幕坐标
def grid_to_screen(row, col):
    x = POS_GRID_NW_CENTRE[0] + col * GRID_SPACING_X
    y = POS_GRID_NW_CENTRE[1] + row * GRID_SPACING_Y
    return (x, y)


# 将屏幕坐标转换为网格坐标
def screen_to_grid(x, y):
    # 计算相对于左上角第一个格子的偏移量
    dx = x - POS_GRID_NW_CENTRE[0]
    dy = y - POS_GRID_NW_CENTRE[1]

    # 计算网格坐标
    col = round(dx / GRID_SPACING_X)
    row = round(dy / GRID_SPACING_Y)

    # 确保坐标在有效范围内
    if row < 0 or row >= GRID_SIZE or col < 0 or col >= GRID_SIZE:
        return None

    return (row, col)


# 棋子类
class Piece:
    def __init__(self, piece_id, piece_type, color, row, col):
        self.id = piece_id  # 棋子唯一标识
        self.type = piece_type  # 棋子类型（由您定义）
        self.color = color  # 棋子颜色
        self.row = row  # 行位置
        self.col = col  # 列位置
        self.selected = False  # 是否被选中

    def draw(self, screen, images, font, transparency=1.0):
        # 计算棋子在屏幕上的位置
        x, y = grid_to_screen(self.row, self.col)

        # 如果被选中，绘制高亮效果（不受透明度影响）
        if self.selected:
            highlight_rect = images['highlight'].get_rect(center=(x, y))
            screen.blit(images['highlight'], highlight_rect)

        # 绘制棋子（优先使用专用贴图）
        piece_img = images.get(f'piece_{self.color}_{self.type}', images[f'piece_{self.color}'])
        
        # 应用透明度
        if transparency < 1.0:
            # 创建带有透明度的surface
            transparent_surface = pygame.Surface(piece_img.get_size(), pygame.SRCALPHA)
            # 将原图像绘制到临时surface上
            transparent_surface.blit(piece_img, (0, 0))
            # 设置整体透明度
            transparent_surface.set_alpha(int(255 * transparency))
            piece_img = transparent_surface

        piece_rect = piece_img.get_rect(center=(x, y))
        screen.blit(piece_img, piece_rect)

        # 绘制棋子ID（也应用透明度）
        text_surface = font.render(str(self.id), True, BLACK if self.color == 'white' else WHITE)
        if transparency < 1.0:
            text_surface.set_alpha(int(255 * transparency))
        text_rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, text_rect)

    def is_clicked(self, pos):
        # 检查点击位置是否在棋子上
        piece_x, piece_y = grid_to_screen(self.row, self.col)
        distance = math.sqrt((pos[0] - piece_x) ** 2 + (pos[1] - piece_y) ** 2)
        return distance < PIECE_SIZE // 2


# 玩家类
class Player:
    def __init__(self, color, piece_count):
        self.color = color
        self.pieces = []  # 玩家的棋子列表
        self.piece_count = piece_count
        self.initialize_pieces()

    def initialize_pieces(self):
        # 根据玩家颜色初始化棋子位置
        # 这里只是一个示例，您需要根据您的游戏规则来设置
        if self.color == 'black':
            # 黑方初始布局（棋盘下方）
            self.pieces = [
                Piece(1, 'rook', 'black', 0, 0),
                Piece(2, 'knight', 'black', 0, 1),
                Piece(3, 'bishop', 'black', 0, 2),
                Piece(4, 'queen', 'black', 0, 3),
                Piece(5, 'king', 'black', 0, 4),
                Piece(6, 'bishop', 'black', 0, 5),
                Piece(7, 'knight', 'black', 0, 6),
                Piece(8, 'rook', 'black', 0, 7),
                *[Piece(9+i, 'pawn', 'black', 1, i) for i in range(8)]
            ]
        elif self.color == 'white':
            # 白方初始布局（棋盘上方）
            self.pieces = [
                Piece(1, 'rook', 'white', 7, 0),
                Piece(2, 'knight', 'white', 7, 1),
                Piece(3, 'bishop', 'white', 7, 2),
                Piece(4, 'queen', 'white', 7, 3),
                Piece(5, 'king', 'white', 7, 4),
                Piece(6, 'bishop', 'white', 7, 5),
                Piece(7, 'knight', 'white', 7, 6),
                Piece(8, 'rook', 'white', 7, 7),
                *[Piece(9+i, 'pawn', 'white', 6, i) for i in range(8)]
            ]


# 游戏类
class Game:
    BUTTONS = {
        'skill': {
            'name': '开大',
            'pos': [scl(50), scl(50)],  # 调整到合适位置
            'size': [scl(80), scl(40)],
            'anchor': 'NW'
        },
        'tax': {
            'name': '征税',
            'pos': [scl(50), scl(100)],
            'size': [scl(80), scl(40)],
            'anchor': 'NW'
        },
        'end_turn': {
            'name': '结束回合',
            'pos': [scl(50), scl(150)],
            'size': [scl(100), scl(40)],
            'anchor': 'NW'
        }
    }

    def __init__(self):
        self.images = load_images()
        self.font = pygame.font.Font(GAME_FONT, scl(24))
        self.title_font = pygame.font.Font(GAME_FONT, scl(38))
        self.button_font = pygame.font.Font(GAME_BTN_FONT, scl(20))
        self.players = [
            Player('black', 8),
            Player('white', 8)
        ]
        self.board = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_piece = None
        self.valid_moves = []
        self.current_player_idx = 0  # 当前玩家索引
        self.game_over = False
        self.winner = None
        self.initialize_board()

        # 添加资源系统、技能系统和事件处理器
        self.resource_system = ResourceSystem()
        self.skill_system = SkillSystem(self.resource_system)
        self.event_handler = EventHandler()
        self.event_handler.add_listener(GameEvent.TURN_END, self.on_turn_end)

        # 添加按钮状态
        self.buttons = self.BUTTONS.copy()
        # 添加技能相关属性
        self.pawn_abilities = {}  # 存储兵的鹿角技能效果
        self.rook_fortresses = {}  # 存储车的堡垒技能效果
        self.king_cores = {}  # 存储王的核心化领土效果
        
        # 添加障碍物系统
        self.antlers = {}  # 鹿角位置 {(row,col): owner_color}
        self.fortresses = {}  # 堡垒位置 {(row,col): owner_color}
        self.core_territories = {}  # 核心领土 {(row,col): owner_color}
        
        # 添加阶段状态：move(走子阶段) 和 action(行动阶段)
        self.phase = "move"
        # 跟踪每个玩家是否完成走子和行动
        self.player_move_completed = [False, False]  # 跟踪每个玩家是否完成走子
        self.player_action_completed = [False, False]  # 跟踪每个玩家是否完成行动

    def initialize_board(self):
        # 初始化棋盘，将玩家的棋子放置到棋盘上
        for player in self.players:
            for piece in player.pieces:
                self.board[piece.row][piece.col] = piece

    def get_current_player(self):
        return self.players[self.current_player_idx]

    def draw(self, screen):
        # 绘制棋盘背景
        screen.blit(self.images['board'], (0, 0))

        # 只在走子阶段绘制有效移动位置
        if self.phase == "move":
            for row, col in self.valid_moves:
                x, y = grid_to_screen(row, col)
                move_rect = self.images['valid_move'].get_rect(center=(x, y))
                screen.blit(self.images['valid_move'], move_rect)

        # 首先绘制所有棋子（可能有透明度）
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.board[row][col]:
                    piece = self.board[row][col]
                    # 检查棋子是否在障碍物下
                    transparency = 1.0  # 默认不透明
                    if (piece.row, piece.col) in self.antlers or (piece.row, piece.col) in self.fortresses:
                        transparency = BEHIND_OBST_TRANS
                    
                    piece.draw(screen, self.images, self.font, transparency)

        # 然后绘制障碍物（在棋子之上绘制）
        # 绘制鹿角障碍物
        for (row, col), color in self.antlers.items():
            x, y = grid_to_screen(row, col)
            antler_img = self.images.get(f'obstacle_{color}_lujiao')
            antler_rect = antler_img.get_rect(center=(x, y))
            screen.blit(antler_img, antler_rect)

        # 绘制堡垒障碍物
        for (row, col), color in self.fortresses.items():
            x, y = grid_to_screen(row, col)
            fortress_img = self.images.get(f'obstacle_{color}_fortress')
            fortress_rect = fortress_img.get_rect(center=(x, y))
            screen.blit(fortress_img, fortress_rect)

        # 绘制按钮
        self.draw_buttons(screen)

        # 绘制游戏信息
        self.draw_game_info(screen)

    def draw_game_info(self, screen):
        # 定义信息栏的位置和尺寸
        info_rect = pygame.Rect(POS_INFO_NW[0], POS_INFO_NW[1],
                                POS_INFO_SE[0] - POS_INFO_NW[0],
                                POS_INFO_SE[1] - POS_INFO_NW[1])

        # 绘制信息栏背景
        # pygame.draw.rect(screen, (240, 240, 240), info_rect)
        # pygame.draw.rect(screen, BLACK, info_rect, 2)  # 边框

        # 设置字体
        font_large = pygame.font.Font(GAME_FONT, scl(36))
        font_small = pygame.font.Font(GAME_FONT, scl(28))

        # 计算文本起始位置
        x = POS_INFO_NW[0] + scl(20)
        y = POS_INFO_NW[1] + scl(20)

        # 绘制当前玩家信息
        current_player = self.get_current_player()
        text = font_large.render(f"Player: {current_player.color}", True, WHITE)
        screen.blit(text, (x, y))
        y += scl(70)

        # 绘制玩家资源信息
        for player in self.players:
            food_text = font_small.render(f"{player.color}: Food: {self.resource_system.food[player.color]}", True, WHITE)
            # food_text = font_small.render(f"{player.color}: {len(player.pieces)} pieces, Food: {self.resource_system.food[player.color]}", True, WHITE)
            screen.blit(food_text, (x, y))
            y += scl(40)

        y += scl(30)  # 增加一些间距

        # 绘制当前阶段信息
        phase_text = font_small.render(f"Phase: {self.phase}", True, WHITE)
        screen.blit(phase_text, (x, y))
        y += scl(60)
        
        # 绘制玩家完成状态
        for i, player in enumerate(self.players):
            move_status = "ok" if self.player_move_completed[i] else "○"
            action_status = "ok" if self.player_action_completed[i] else "○"
            status_text = font_small.render(
                f"{player.color}: Move {move_status} | Action {action_status}", 
                True, WHITE
            )
            screen.blit(status_text, (x, y))
            y += scl(40)
        y += scl(20)

        # 绘制操作说明
        instructions = [
            "Click piece to select",
            "Click target position to move",
            "Press R to restart game"
        ]

        for instruction in instructions:
            text = font_small.render(instruction, True, WHITE)
            screen.blit(text, (x, y))
            y += scl(40)

        # 如果游戏结束，显示获胜者
        if self.game_over:
            y += scl(20)  # 增加一些间距
            winner_text = font_large.render(f"Game Over!", True, WHITE)
            screen.blit(winner_text, (x, y))
            y += scl(70)
            winner_text = font_large.render(f"Winner: {self.winner}", True, WHITE)
            screen.blit(winner_text, (x, y))

    def draw_buttons(self, screen):
        """绘制所有按钮"""
        for button_id, button_info in self.buttons.items():
            x, y = button_info['pos']
            width, height = button_info['size']

            # 根据阶段和条件决定按钮是否可用
            if button_id == 'tax' and self.phase != "action":
                button_color = (100, 100, 100)  # 灰色表示禁用
            elif button_id == 'skill' and (self.phase != "action" or self.selected_piece is None):
                button_color = (100, 100, 100)  # 灰色表示禁用
            elif button_id == 'end_turn':
                button_color = (100, 100, 200)  # 结束回合按钮始终可用
            else:
                button_color = (100, 100, 200)  # 正常颜色

            # 绘制按钮背景
            button_rect = pygame.Rect(x, y, width, height)
            pygame.draw.rect(screen, button_color, button_rect)
            pygame.draw.rect(screen, BLACK, button_rect, 2)

            # 绘制按钮文字
            text = self.button_font.render(button_info['name'], True, WHITE)
            text_rect = text.get_rect(center=(x + width//2, y + height//2))
            screen.blit(text, text_rect)

    def check_button_click(self, pos):
        """检查是否点击了按钮"""
        x, y = pos
        for button_id, button_info in self.buttons.items():
            btn_x, btn_y = button_info['pos']
            btn_width, btn_height = button_info['size']

            # 检查点击位置是否在按钮范围内
            if (btn_x <= x <= btn_x + btn_width and
                btn_y <= y <= btn_y + btn_height):
                print(f"按钮被点击: {button_id}")
                return button_id

        return None

    def handle_button_action(self, button_id):
        current_player = self.get_current_player()
        current_idx = self.current_player_idx
        
        if button_id == 'tax':
            # 征税逻辑（只在行动阶段有效）
            if self.phase == "action":
                # 检查是否有足够的粮草
                if self.resource_system.food[current_player.color] <= 0:
                    print(f"{current_player.color} 粮草不足，无法征税")
                    return
                tax_collected = self.resource_system.collect_tax(current_player, self.board)
                self.resource_system.food[current_player.color] -= 1  # 征税消耗1点粮草
                print(f"{current_player.color} 征税获得 {tax_collected} 粮草，消耗1点粮草")
                
        elif button_id == 'end_turn':
            # 结束当前阶段
            if self.phase == "move":
                # 在走子阶段结束回合，标记当前玩家已完成走子
                self.player_move_completed[current_idx] = True
                
                # 检查是否所有玩家都完成了走子
                if all(self.player_move_completed):
                    # 所有玩家完成走子，切换到行动阶段
                    self.phase = "action"
                    self.player_action_completed = [False, False]
                    self.current_player_idx = 0
                    # 清除任何选中的棋子
                    if self.selected_piece:
                        self.selected_piece.selected = False
                        self.selected_piece = None
                else:
                    # 切换到下一个玩家继续走子
                    self.current_player_idx = (current_idx + 1) % len(self.players)
                    # 清除任何选中的棋子
                    if self.selected_piece:
                        self.selected_piece.selected = False
                        self.selected_piece = None
                    
            elif self.phase == "action":
                # 在行动阶段结束回合，标记当前玩家已完成行动
                self.player_action_completed[current_idx] = True
                
                # 检查是否所有玩家都完成了行动
                if all(self.player_action_completed):
                    # 所有玩家完成行动，切换到下一回合的走子阶段
                    self.phase = "move"
                    self.player_move_completed = [False, False]
                    # 触发回合结束事件
                    self.event_handler.dispatch(GameEvent.TURN_END)
                    # 从第一个玩家开始新回合
                    self.current_player_idx = 0
                else:
                    # 切换到下一个玩家继续行动
                    self.current_player_idx = (current_idx + 1) % len(self.players)
                
                # 清除任何选中的棋子
                if self.selected_piece:
                    self.selected_piece.selected = False
                    self.selected_piece = None
                    
        elif button_id == 'skill':
            # 技能逻辑（只在行动阶段有效）
            if self.phase == "action":
                if self.selected_piece and self.selected_piece.color == current_player.color:
                    # 根据棋子类型使用相应技能
                    if self.selected_piece.type == 'pawn':
                        success, msg = self.pawn_skill(self.selected_piece)
                        if success:
                            self.skill_system.cast_skill(self.selected_piece.type, current_player.color)
                        print(msg)
                    elif self.selected_piece.type == 'rook':
                        success, msg = self.rook_skill(self.selected_piece)
                        if success:
                            self.skill_system.cast_skill(self.selected_piece.type, current_player.color)
                        print(msg)
                    elif self.selected_piece.type == 'knight':
                        success, msg = self.knight_skill(self.selected_piece)
                        if success:
                            self.skill_system.cast_skill(self.selected_piece.type, current_player.color)
                        print(msg)
                    elif self.selected_piece.type == 'king':
                        success, msg = self.king_skill(self.selected_piece)
                        if success:
                            self.skill_system.cast_skill(self.selected_piece.type, current_player.color)
                        print(msg)
                    elif self.selected_piece.type in ['bishop', 'queen']:
                        self.use_ability(self.selected_piece)
                    else:
                        print("该棋子没有特殊技能")
                else:
                    print("请先选择一个自己的棋子再使用技能")

    def is_blocked(self, from_pos, to_pos, attacker_color):
        """检查移动路径是否被障碍物阻挡"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # 如果是马，可以跳过鹿角（但不能跳过堡垒）
        piece = self.board[from_row][from_col]
        if piece and piece.type == 'knight':
            # 马可以跳过鹿角，但不能进入敌方堡垒
            if (to_row, to_col) in self.fortresses and self.fortresses[(to_row, to_col)] != attacker_color:
                return True
            return False
        
        # 直线移动检测
        if from_row == to_row or from_col == to_col:
            if from_row == to_row:  # 水平移动
                step = 1 if to_col > from_col else -1
                for col in range(from_col + step, to_col, step):
                    pos = (from_row, col)
                    # 敌方鹿角阻挡
                    if pos in self.antlers and self.antlers[pos] != attacker_color:
                        return True
                    # 敌方堡垒阻挡
                    if pos in self.fortresses and self.fortresses[pos] != attacker_color:
                        return True
            else:  # 垂直移动
                step = 1 if to_row > from_row else -1
                for row in range(from_row + step, to_row, step):
                    pos = (row, from_col)
                    if pos in self.antlers and self.antlers[pos] != attacker_color:
                        return True
                    if pos in self.fortresses and self.fortresses[pos] != attacker_color:
                        return True
        
        # 斜线移动检测
        else:
            row_step = 1 if to_row > from_row else -1
            col_step = 1 if to_col > from_col else -1
            steps = abs(to_row - from_row)
            for i in range(1, steps):
                r = from_row + i * row_step
                c = from_col + i * col_step
                pos = (r, c)
                if pos in self.antlers and self.antlers[pos] != attacker_color:
                    return True
                if pos in self.fortresses and self.fortresses[pos] != attacker_color:
                    return True
        
        # 目标位置堡垒检测
        if to_pos in self.fortresses and self.fortresses[to_pos] != attacker_color:
            return True
            
        return False

    def move_piece(self, from_row, from_col, to_row, to_col):
        # 移动棋子
        piece = self.board[from_row][from_col]
        
        # 检查目标位置是否有敌方鹿角
        target_pos = (to_row, to_col)
        if target_pos in self.antlers and self.antlers[target_pos] != piece.color:
            # 吃掉鹿角（不移位，只移除鹿角）
            del self.antlers[target_pos]
            print(f"{piece.color} 吃掉了敌方鹿角")
            return  # 不移位，直接返回
            
        # 检查目标位置是否有敌方堡垒
        if target_pos in self.fortresses and self.fortresses[target_pos] != piece.color:
            print(f"{piece.color} 无法移动到敌方堡垒")
            return  # 无法移动到敌方堡垒
        
        # 如果是特殊棋子移动，消耗资源
        if piece.type in ['knight', 'bishop', 'queen']:
            self.skill_system.cast_skill(piece.type, piece.color)

        # 处理目标位置的棋子（吃子）
        target_piece = self.board[to_row][to_col]
        if target_piece:
            # 从玩家的棋子列表中移除被吃的棋子
            for player in self.players:
                if target_piece in player.pieces:
                    player.pieces.remove(target_piece)
                    break

        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.row = to_row
        piece.col = to_col

    def get_valid_moves(self, row, col):
        piece = self.board[row][col]
        moves = []

        if piece.type == 'pawn':
            # 兵的特殊移动规则
            direction = 1 if piece.color == 'black' else -1
            # 基本前进
            if 0 <= row + direction < GRID_SIZE and self.board[row + direction][col] is None:
                moves.append((row + direction, col))
                # 如果是初始位置，可以前进两格
                if (piece.color == 'black' and row == 1) or (piece.color == 'white' and row == 6):
                    if self.board[row + 2*direction][col] is None:
                        moves.append((row + 2*direction, col))
            # 吃子斜进
            for dc in [-1, 1]:
                if 0 <= col + dc < GRID_SIZE and 0 <= row + direction < GRID_SIZE:
                    target = self.board[row + direction][col + dc]
                    if target and target.color != piece.color:
                        moves.append((row + direction, col + dc))

        elif piece.type == 'rook':
            # 车的移动规则（直线无限距离）
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                for i in range(1, GRID_SIZE):
                    r, c = row + dr*i, col + dc*i
                    if not (0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE):
                        break
                    if self.board[r][c] is None:
                        moves.append((r, c))
                    else:
                        if self.board[r][c].color != piece.color:
                            moves.append((r, c))
                        break

        elif piece.type == 'knight':
            # 马的移动规则（L形）
            for dr, dc in [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]:
                r, c = row + dr, col + dc
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    if self.board[r][c] is None or self.board[r][c].color != piece.color:
                        moves.append((r, c))

        elif piece.type == 'bishop':
            # 象的移动规则（斜线无限距离）
            for dr, dc in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                for i in range(1, GRID_SIZE):
                    r, c = row + dr*i, col + dc*i
                    if not (0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE):
                        break
                    if self.board[r][c] is None:
                        moves.append((r, c))
                    else:
                        if self.board[r][c].color != piece.color:
                            moves.append((r, c))
                        break

        elif piece.type == 'queen':
            # 后的移动规则（直线+斜线无限距离）
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]:
                for i in range(1, GRID_SIZE):
                    r, c = row + dr*i, col + dc*i
                    if not (0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE):
                        break
                    if self.board[r][c] is None:
                        moves.append((r, c))
                    else:
                        if self.board[r][c].color != piece.color:
                            moves.append((r, c))
                        break

        elif piece.type == 'king':
            # 王的移动规则（单格任意方向）
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    r, c = row + dr, col + dc
                    if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                        if self.board[r][c] is None or self.board[r][c].color != piece.color:
                            moves.append((r, c))

        # 过滤被阻挡的移动
        valid_moves = []
        for move in moves:
            # 检查目标位置是否有敌方堡垒
            if move in self.fortresses and self.fortresses[move] != piece.color:
                continue  # 跳过敌方堡垒
                
            # 检查移动路径是否被阻挡
            if not self.is_blocked((row, col), move, piece.color):
                valid_moves.append(move)
                
        return valid_moves

    def pawn_skill(self, piece):
        """兵技能：放置鹿角"""
        pos = (piece.row, piece.col)
        if pos not in self.antlers and pos not in self.fortresses:
            self.antlers[pos] = piece.color
            return True, "鹿角放置成功"
        return False, "该位置已有障碍物"

    def rook_skill(self, piece):
        """车技能：建造堡垒"""
        pos = (piece.row, piece.col)
        if pos not in self.fortresses and pos not in self.antlers:
            self.fortresses[pos] = piece.color
            # 堡垒提供防御加成
            self.resource_system.fertility[piece.row][piece.col] += 20
            return True, "堡垒建造成功"
        return False, "该位置已有障碍物"

    def handle_click(self, pos):
        if self.game_over:
            return
            
        # 根据当前阶段决定处理逻辑
        if self.phase == "move":
            self._handle_move_phase(pos)
        elif self.phase == "action":
            self._handle_action_phase(pos)

    def _handle_action_phase(self, pos):
        # 先检查是否点击了按钮
        button_clicked = self.check_button_click(pos)
        if button_clicked:
            # 处理按钮点击
            self.handle_button_action(button_clicked)
            return
            
        # 将屏幕坐标转换为网格坐标
        grid_pos = screen_to_grid(pos[0], pos[1])
        if grid_pos is None:
            return
            
        row, col = grid_pos
        current_player = self.get_current_player()
        
        # 如果没有选中的棋子，尝试选择一个
        if self.selected_piece is None:
            if self.board[row][col] and self.board[row][col].color == current_player.color:
                self.board[row][col].selected = True
                self.selected_piece = self.board[row][col]
                # 在行动阶段不显示移动范围
                self.valid_moves = []
        else:
            # 如果已经选中了棋子，检查是否点击了同一棋子（取消选择）
            if (row, col) == (self.selected_piece.row, self.selected_piece.col):
                self.selected_piece.selected = False
                self.selected_piece = None
                self.valid_moves = []
            # 如果点击了其他棋子，切换选择
            elif self.board[row][col] and self.board[row][col].color == current_player.color:
                self.selected_piece.selected = False
                self.board[row][col].selected = True
                self.selected_piece = self.board[row][col]
                self.valid_moves = []

    def _handle_move_phase(self, pos):
        # 将屏幕坐标转换为网格坐标
        grid_pos = screen_to_grid(pos[0], pos[1])
        if grid_pos is None:
            return

        row, col = grid_pos
        current_player = self.get_current_player()

        # 如果没有选中的棋子，尝试选择一个
        if self.selected_piece is None:
            if self.board[row][col] and self.board[row][col].color == current_player.color:
                self.board[row][col].selected = True
                self.selected_piece = self.board[row][col]
                # 获取有效移动位置（这里需要您实现）
                self.valid_moves = self.get_valid_moves(row, col)
        else:
            # 如果已经选中了棋子，尝试移动它
            if (row, col) in self.valid_moves:
                # 检查是否有足够的资源执行移动（对于特殊技能）
                if self.selected_piece.type in ['knight', 'bishop', 'queen']:
                    if not self.skill_system.can_cast_skill(self.selected_piece.type, current_player.color):
                        # 资源不足，无法执行特殊技能
                        self.selected_piece.selected = False
                        self.selected_piece = None
                        self.valid_moves = []
                        return

                self.move_piece(self.selected_piece.row, self.selected_piece.col, row, col)
                self.selected_piece.selected = False
                self.selected_piece = None
                self.valid_moves = []

                # 标记当前玩家已完成走子
                current_idx = self.current_player_idx
                self.player_move_completed[current_idx] = True
                
                # 检查是否所有玩家都完成了走子
                if all(self.player_move_completed):
                    # 所有玩家完成走子，切换到行动阶段
                    self.phase = "action"
                    # 重置行动完成状态
                    self.player_action_completed = [False, False]
                    # 从第一个玩家开始行动
                    self.current_player_idx = 0
                else:
                    # 切换到下一个玩家继续走子
                    self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

                # 检查游戏是否结束
                self.check_game_over()
            else:
                # 如果点击了其他棋子，取消选择当前棋子
                self.selected_piece.selected = False
                self.selected_piece = None
                self.valid_moves = []

    def switch_player(self):
        # 切换玩家
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        # 触发回合结束事件
        self.event_handler.dispatch(GameEvent.TURN_END)

    def on_turn_end(self, data=None):
        # 回合结束时的处理逻辑
        # 更新丰饶度
        self.resource_system.update_fertility(self.board)

        # 更新叛乱值
        for row in range(8):
            for col in range(8):
                # 丰饶度低于50时可能产生叛乱
                if self.resource_system.fertility[row][col] < 50:
                    import random
                    self.resource_system.rebellion[row][col] += random.randint(0, 50 - self.resource_system.fertility[row][col])
                    # 叛乱值超过100时，该格子变为中立（简化实现）
                    if self.resource_system.rebellion[row][col] > 100:
                        piece = self.board[row][col]
                        if piece:
                            # 从玩家棋子列表中移除
                            for player in self.players:
                                if piece in player.pieces:
                                    player.pieces.remove(piece)
                                    break
                            self.board[row][col] = None
                            self.resource_system.rebellion[row][col] = 0
                            print(f"位置({row},{col})发生叛乱，棋子被移除")

        # 征税
        current_player = self.get_current_player()
        # 回合开始时自动增加1点粮草
        self.resource_system.food[current_player.color] += 1
        print(f"{current_player.color} 回合开始，获得1点粮草")

    def check_game_over(self):
        # 这里需要您实现检查游戏是否结束的逻辑
        # 这只是示例代码，检查是否有一方的棋子全部被吃掉
        for player in self.players:
            if len(player.pieces) == 0:
                self.game_over = True
                # 找到棋子数量最多的玩家作为获胜者
                max_pieces = 0
                for p in self.players:
                    if len(p.pieces) > max_pieces:
                        max_pieces = len(p.pieces)
                        self.winner = p.color
                break

    def reset(self):
        # 重置游戏
        self.players = [
            Player('black', 8),
            Player('white', 8)
        ]
        self.board = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_piece = None
        self.valid_moves = []
        self.current_player_idx = 0
        self.game_over = False
        self.winner = None
        self.initialize_board()

        # 重置资源系统
        self.resource_system = ResourceSystem()
        self.skill_system = SkillSystem(self.resource_system)
        
        # 重置阶段状态
        self.phase = "move"
        self.player_move_completed = [False, False]  # 跟踪每个玩家是否完成走子
        self.player_action_completed = [False, False]  # 跟踪每个玩家是否完成行动


# 主游戏循环
def main():
    clock = pygame.time.Clock()
    game = Game()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    game.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # 按R键重置游戏
                    game.reset()

        # 绘制背景
        screen.fill(GRAY)

        # 绘制游戏
        game.draw(screen)

        # 更新屏幕
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
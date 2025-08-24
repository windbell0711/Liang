import pygame
import sys
import os
import math
import logging
from logging.handlers import RotatingFileHandler
from collections import defaultdict

from consts import *


# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if FILE_LOGGING_NAME:
    if os.path.dirname(FILE_LOGGING_NAME) and not os.path.exists(os.path.dirname(FILE_LOGGING_NAME)):
        os.makedirs(os.path.dirname(FILE_LOGGING_NAME))
    file_handler = RotatingFileHandler(FILE_LOGGING_NAME, encoding='utf-8', maxBytes=256*1024, backupCount=2)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s: %(levelname)s:\t%(filename)s:%(lineno)d\t%(message)s"))
    logger.addHandler(file_handler)
if CONSOLE_LOGGING:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s: %(levelname)s:\t%(filename)s:%(lineno)d\t%(message)s"))
    logger.addHandler(console_handler)

# 事件处理器
class EventHandler:
    def __init__(self):
        self.listeners = defaultdict(list)

    def add_listener(self, event_type, callback):
        self.listeners[event_type].append(callback)

    def dispatch(self, event_type, data=None):
        for callback in self.listeners[event_type]:
            callback(data)

# 加载图片
def load_images():
    images = {}
    # 确保有images文件夹
    if not os.path.exists("images"):
        os.makedirs("images")
        logger.error("Please put image resources in the images folder")

    # 尝试加载图片，如果失败则使用彩色方块代替
    try:
        images['board'] = pygame.image.load("images/board.png").convert_alpha()
        images['board'] = pygame.transform.scale(images['board'], (SCREEN_WIDTH, SCREEN_HEIGHT))
    except:
        try:
            images['board'] = pygame.image.load("images/beach.png").convert_alpha()
            images['board'] = pygame.transform.scale(images['board'], (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            logger.warning("Cannot load board.png, using default background")
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
            logger.warning(f"Cannot load piece_{color}.png, using default piece")
            images[f'piece_{color}'] = pygame.Surface((PIECE_SIZE, PIECE_SIZE), pygame.SRCALPHA)
            if color == 'black':
                pygame.draw.circle(images[f'piece_{color}'], BLACK, (PIECE_SIZE // 2, PIECE_SIZE // 2), PIECE_SIZE // 2)
            elif color == 'white':
                pygame.draw.circle(images[f'piece_{color}'], WHITE, (PIECE_SIZE // 2, PIECE_SIZE // 2), PIECE_SIZE // 2)

        # 加载特定类型棋子
        for ptype in piece_types:
            try:
                images[f'piece_{color}_{ptype}'] = pygame.image.load(
                    f"images/piece_{color}_{ptype}.png").convert_alpha()
                images[f'piece_{color}_{ptype}'] = pygame.transform.scale(images[f'piece_{color}_{ptype}'],
                                                                          (PIECE_SIZE, PIECE_SIZE))
            except:
                logger.warning(f"Cannot load piece_{color}_{ptype}.png, using default piece")
                # 如果没有专用贴图，将使用通用颜色贴图

    # 加载障碍物贴图
    for color in piece_colors:
        try:
            images[f'obstacle_{color}_lujiao'] = pygame.image.load(
                f"images/obstacle_{color}_lujiao.png").convert_alpha()
            images[f'obstacle_{color}_lujiao'] = pygame.transform.scale(images[f'obstacle_{color}_lujiao'],
                                                                        (PIECE_SIZE, PIECE_SIZE))
        except:
            logger.warning(f"Cannot load obstacle_{color}_lujiao.png, using default indicator")
            images[f'obstacle_{color}_lujiao'] = pygame.Surface((PIECE_SIZE, PIECE_SIZE), pygame.SRCALPHA)
            # 使用颜色圆圈作为默认显示
            circle_color = BLACK if color == 'black' else WHITE
            pygame.draw.circle(images[f'obstacle_{color}_lujiao'], circle_color, (PIECE_SIZE // 2, PIECE_SIZE // 2),
                               PIECE_SIZE // 3)

        # 新增：加载堡垒贴图
        try:
            images[f'obstacle_{color}_fortress'] = pygame.image.load(
                f"images/obstacle_{color}_fortress.png").convert_alpha()
            images[f'obstacle_{color}_fortress'] = pygame.transform.scale(images[f'obstacle_{color}_fortress'],
                                                                          (PIECE_SIZE, PIECE_SIZE))
        except:
            logger.warning(f"Cannot load obstacle_{color}_fortress.png, using default indicator")
            images[f'obstacle_{color}_fortress'] = pygame.Surface((PIECE_SIZE, PIECE_SIZE), pygame.SRCALPHA)
            circle_color = BLACK if color == 'black' else WHITE
            pygame.draw.rect(images[f'obstacle_{color}_fortress'], circle_color, (0, 0, PIECE_SIZE, PIECE_SIZE))

    # 加载高亮和有效移动提示
    try:
        images['highlight'] = pygame.image.load("images/highlight.png").convert_alpha()
        images['highlight'] = pygame.transform.scale(images['highlight'], (PIECE_SIZE + 20, PIECE_SIZE + 20))
    except:
        logger.warning("Cannot load highlight.png, using default highlight effect")
        images['highlight'] = pygame.Surface((PIECE_SIZE + 20, PIECE_SIZE + 20), pygame.SRCALPHA)
        pygame.draw.circle(images['highlight'], (255, 255, 0, 128), (PIECE_SIZE // 2 + 10, PIECE_SIZE // 2 + 10),
                           PIECE_SIZE // 2 + 5, 5)

    try:
        images['valid_move'] = pygame.image.load("images/valid_move.png").convert_alpha()
        images['valid_move'] = pygame.transform.scale(images['valid_move'], (PIECE_SIZE // 2, PIECE_SIZE // 2))
    except:
        logger.warning("Cannot load valid_move.png, using default indicator")
        images['valid_move'] = pygame.Surface((PIECE_SIZE // 2, PIECE_SIZE // 2), pygame.SRCALPHA)
        pygame.draw.circle(images['valid_move'], (0, 255, 0, 128), (PIECE_SIZE // 4, PIECE_SIZE // 4), PIECE_SIZE // 4)

    return images

# 将网格坐标转换为屏幕坐标
def grid_to_screen(row, col):
    x = POS_GRID_NW_CENTRE[0] + col * GRID_SPACING_X
    y = POS_GRID_NW_CENTRE[1] + row * GRID_SPACING_Y
    return x, y

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
    return row, col


# 棋子类
class Piece:
    def __init__(self, piece_id, piece_type, color, row, col):
        self.id = piece_id  # 棋子唯一标识
        self.type = piece_type  # 棋子类型
        self.color = color  # 棋子颜色
        self.row = row  # 行位置
        self.col = col  # 列位置
        self.selected = False  # 是否被选中
        self.moved_this_turn = 0  # 本回合移动次数

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
        # text_surface = font.render(str(self.id), True, BLACK if self.color == 'white' else WHITE)
        # if transparency < 1.0:
        #     text_surface.set_alpha(int(255 * transparency))
        # text_rect = text_surface.get_rect(center=(x, y))
        # screen.blit(text_surface, text_rect)

    def is_clicked(self, pos):
        # 检查点击位置是否在棋子上
        piece_x, piece_y = grid_to_screen(self.row, self.col)
        distance = math.sqrt((pos[0] - piece_x) ** 2 + (pos[1] - piece_y) ** 2)
        return distance < PIECE_SIZE // 2

    def reset_turn_state(self):
        # 重置回合状态
        self.moved_this_turn = 0


# 玩家类
class Player:
    def __init__(self, color, piece_count):
        self.color = color
        self.pieces = []  # 玩家的棋子列表
        self.piece_count = piece_count
        self.moves_this_turn = 0  # 本回合移动次数
        self.skills_used_this_turn = 0  # 本回合技能使用次数
        self.initialize_pieces()

    def initialize_pieces(self):
        # 根据玩家颜色初始化棋子位置
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
                *[Piece(9 + i, 'pawn', 'black', 1, i) for i in range(8)]
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
                *[Piece(9 + i, 'pawn', 'white', 6, i) for i in range(8)]
            ]

    def reset_turn_state(self):
        # 重置回合状态
        self.moves_this_turn = 0
        self.skills_used_this_turn = 0  # 重置技能使用次数
        for piece in self.pieces:
            piece.reset_turn_state()


# 游戏类
class Game:
    BUTTONS = {
        # 白方
        'white_tax': {
            'name': '白征税',
            'pos':  [scl(116), scl(252)],
            'size': [scl(72),  scl(88)],
            'anchor': 'NW',
            'invisible': False,
        },
        'white_farm': {
            'name': '白屯田',
            'pos':  [scl(202), scl(252)],
            'size': [scl(72),  scl(88)],
            'anchor': 'NW',
            'invisible': False,
        },
        'white_end': {
            'name': '白结束',
            'pos':  [scl(288), scl(252)],
            'size': [scl(72),  scl(88)],
            'anchor': 'NW',
            'invisible': False,
        },

        # 黑方
        'black_tax': {
            'name': '黑征税',
            'pos':  [scl(116), scl(565)],
            'size': [scl(72),  scl(88)],
            'anchor': 'NW',
            'invisible': False,
        },
        'black_farm': {
            'name': '黑屯田',
            'pos':  [scl(202), scl(565)],
            'size': [scl(72),  scl(88)],
            'anchor': 'NW',
            'invisible': False,
        },
        'black_end': {
            'name': '黑结束',
            'pos':  [scl(288), scl(565)],
            'size': [scl(72),  scl(88)],
            'anchor': 'NW',
            'invisible': False,
        }
    }

    def __init__(self):
        # 初始化pygame字体模块
        pygame.font.init()
        # 尝试加载字体，如果失败则使用系统默认字体
        try:
            self.font = pygame.font.Font(GAME_FONT, scl(24))
        except pygame.error:
            logger.warning(f"无法加载字体文件 {GAME_FONT}，使用系统默认字体")
            self.font = pygame.font.Font(None, scl(24))
        try:
            self.title_font = pygame.font.Font(GAME_FONT, scl(38))
        except pygame.error:
            logger.warning(f"无法加载字体文件 {GAME_FONT}，使用系统默认字体")
            self.title_font = pygame.font.Font(None, scl(38))
        try:
            self.button_font = pygame.font.Font(GAME_BTN_FONT, scl(20))
        except pygame.error:
            logger.warning(f"无法加载字体文件 {GAME_BTN_FONT}，使用系统默认字体")
            self.button_font = pygame.font.Font(None, scl(20))

        self.images = load_images()

        # 添加资源系统、技能系统和事件处理器
        self.resource_system = ResourceSystem()
        self.skill_system = SkillSystem(self.resource_system)
        self.event_handler = EventHandler()
        self.event_handler.add_listener(GameEvent.TURN_END, self.on_turn_end)
        self.event_handler.add_listener(GameEvent.PHASE_CHANGE, self.on_phase_change)

        self.players = [
            Player('white', 8),
            Player('black', 8),
        ]  # 顺序影响走子顺序
        self.board: list[list[Piece|None]] = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_piece:  Piece|None = None
        self.valid_moves = []
        self.current_player_idx = 0  # 当前玩家索引
        self.game_over = False
        self.winner = None
        self.phase = GamePhase.ACTION  # 初始阶段为行动阶段
        self.management_view = ManagementView.NONE  # 管理视图
        self.initialize_board()

        self.buttons = self.BUTTONS.copy()

        # 添加技能相关属性
        self.pawn_abilities = {}  # 存储兵的鹿角技能效果
        self.rook_fortresses = {}  # 存储车的堡垒技能效果
        self.king_cores = {}  # 存储王的核心化领土效果

        # 添加障碍物系统
        self.antlers = {}  # 鹿角位置 {(row,col): owner_color}
        self.fortresses = {}  # 堡垒位置 {(row,col): owner_color}
        self.core_territories = {}  # 核心领土 {(row,col): owner_color}

    def initialize_board(self):
        # 初始化棋盘，将玩家的棋子放置到棋盘上
        for player in self.players:
            for piece in player.pieces:
                self.board[piece.row][piece.col] = piece
                # 初始化领土控制
                self.resource_system.update_territory(piece.row, piece.col, player.color)

    def get_current_player(self):
        return self.players[self.current_player_idx]

    def draw(self, screen):
        # 绘制棋盘背景
        screen.blit(self.images['board'], (0, 0))

        # 绘制每个格子的丰饶度
        self.draw_fertility_values(screen)

        # 绘制管理视图的标记（如果有）
        if self.management_view != ManagementView.NONE:
            self.draw_management_marks(screen)

        # 绘制有效移动位置（只在走子阶段且选中棋子时）
        if self.phase == GamePhase.MOVE and self.selected_piece:
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

        # 绘制管理视图说明（如果有）
        if self.management_view != ManagementView.NONE:
            self.draw_management_instructions(screen)

    def draw_fertility_values(self, screen):
        # 创建小号字体用于显示丰饶度
        fertility_font = pygame.font.Font(GAME_FONT, scl(16))
        
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                fertility = self.resource_system.fertility[row][col]
                x, y = grid_to_screen(row, col)
                
                # 调整文本位置，使其位于格子右下角
                text_x = x + GRID_SPACING_X * 0.3
                text_y = y + GRID_SPACING_Y * 0.3
                
                # 绘制丰饶度文本（蓝色）
                text_surface = fertility_font.render(str(fertility), True, BLUE)
                text_rect = text_surface.get_rect(center=(text_x, text_y))
                screen.blit(text_surface, text_rect)

    def draw_management_marks(self, screen):
        # 统一方框/圆圈的边长（像素）
        mark_size = int(GRID_SPACING_X * 0.8)

        # 创建小号字体用于显示操作后的丰饶度
        small_font = pygame.font.Font(GAME_FONT, scl(14))
        
        current_player = self.get_current_player()
        
        # 计算操作后的资源状态
        final_food, fertility_changes = self.calculate_post_operation_resources(current_player.color)
        
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x, y = grid_to_screen(row, col)

                # ================= 征税模式 =================
                if self.management_view == ManagementView.TAX:
                    # 只给当前玩家自己的领土画绿色框
                    if (self.resource_system.territory[row][col] ==
                            current_player.color):
                        if self.resource_system.tax_grid[row][col]:
                            # 计算矩形框的尺寸和位置
                            rect_size = int(GRID_SPACING_X * 0.8)  # 矩形框大小为格子间距的80%
                            rect_x = x - rect_size // 2
                            rect_y = y - rect_size // 2
                            # 绘制红色矩形框
                            pygame.draw.rect(screen, RED, (rect_x, rect_y, rect_size, rect_size), 2)
                            
                            # 在右上角显示操作后的丰饶度（红色）
                            post_fertility = self.resource_system.fertility[row][col] + fertility_changes[row][col]
                            text_surface = small_font.render(str(post_fertility), True, RED)
                            text_rect = text_surface.get_rect(center=(x + rect_size//3, y - rect_size//3))
                            screen.blit(text_surface, text_rect)
                        else:
                            rect_x = x - mark_size // 2
                            rect_y = y - mark_size // 2
                            # 绿色方框
                            pygame.draw.rect(screen, GREEN, (rect_x, rect_y, mark_size, mark_size), 3)


                # ================= 屯田模式 =================
                elif self.management_view == ManagementView.FARM:
                    farm_times = self.resource_system.farm_grid[row][col]
                    if farm_times > 0:
                        # 放大后的红色圆圈
                        pygame.draw.circle(screen, HIGHLIGHT_RED,
                                           (x, y), mark_size // 2, 3)
                        # 圈中央写数字
                        text_surface = self.font.render(str(farm_times), True, WHITE)
                        text_rect = text_surface.get_rect(center=(x, y))
                        screen.blit(text_surface, text_rect)
                        
                        # 在右上角显示操作后的丰饶度（红色）
                        post_fertility = self.resource_system.fertility[row][col] + fertility_changes[row][col]
                        text_surface = small_font.render(str(post_fertility), True, RED)
                        text_rect = text_surface.get_rect(center=(x + mark_size//3, y - mark_size//3))
                        screen.blit(text_surface, text_rect)

    def draw_management_instructions(self, screen):
        # 绘制管理视图的操作说明
        instructions = []
        if self.management_view == ManagementView.TAX:
            instructions = [
                "Tax Management View",
                "Left Click: Mark as tax square",
                "Right Click: Unmark",
                "Ctrl+A: Mark all taxable squares",
                "Click tax button again to exit"
            ]
        elif self.management_view == ManagementView.FARM:
            instructions = [
                "Farming Management View",
                "Left Click: Increase farming times",
                "Right Click: Decrease farming times",
                "Click farming button again to exit"
            ]

        # 绘制说明背景
        instruction_bg = pygame.Surface((scl(300), scl(180)), pygame.SRCALPHA)
        instruction_bg.fill((0, 0, 0, 200))
        screen.blit(instruction_bg, (scl(50), scl(200)))

        # 绘制说明文字
        font_small = pygame.font.Font(GAME_FONT, scl(20))
        for i, instruction in enumerate(instructions):
            text = font_small.render(instruction, True, WHITE)
            screen.blit(text, (scl(60), scl(210) + i * scl(30)))

    def draw_game_info(self, screen):
        # 定义信息栏的位置和尺寸（没用）
        info_rect = pygame.Rect(POS_INFO_NW[0], POS_INFO_NW[1],
                                POS_INFO_SE[0] - POS_INFO_NW[0],
                                POS_INFO_SE[1] - POS_INFO_NW[1])

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
            food_text = font_small.render(f"{player.color}: Food: {self.resource_system.food[player.color]}", True,
                                          WHITE)
            screen.blit(food_text, (x, y))
            y += scl(40)
            
            # 如果在行动阶段，显示操作后的粮草
            if self.phase == GamePhase.ACTION and player.color == current_player.color:
                final_food, _ = self.calculate_post_operation_resources(player.color)
                if final_food != self.resource_system.food[player.color]:
                    post_food_text = font_small.render(f"After: Food: {final_food}", True,
                                                       GREEN if final_food >= 0 else RED)  # 颜色提示
                    screen.blit(post_food_text, (x, y))
                    y += scl(40)

        y += scl(30)  # 增加一些间距

        # 绘制当前阶段信息
        phase_text = font_small.render(f"Phase: {self.phase.value}", True, WHITE)
        screen.blit(phase_text, (x, y))
        y += scl(40)

        # 绘制管理视图信息
        if self.management_view != ManagementView.NONE:
            view_text = font_small.render(f"View: {self.management_view.value}", True, WHITE)
            screen.blit(view_text, (x, y))
            y += scl(40)

        # 绘制移动次数信息
        if self.phase == GamePhase.MOVE:
            moves_text = font_small.render(
                f"Moves: {current_player.moves_this_turn}/{PIECE_MOVE_MAX_PER_TURN}",
                True, WHITE
            )
            screen.blit(moves_text, (x, y))
            y += scl(40)

            # 添加技能使用次数显示
            skills_text = font_small.render(
                f"Skills: {current_player.skills_used_this_turn}/{SKILL_MAX_PER_TURN}",
                True, WHITE
            )
            screen.blit(skills_text, (x, y))
            y += scl(40)
            
            # 添加移动消耗信息（如果选中了棋子）
            if self.selected_piece:
                move_cost = PIECE_MOVE_COST(self.selected_piece.type, self.selected_piece.moved_this_turn)
                cost_text = font_small.render(
                    f"Move cost: {move_cost} food",
                    True, WHITE
                )
                screen.blit(cost_text, (x, y))
                y += scl(40)

        y += scl(20)

        # 绘制操作说明
        instructions = []
        if self.phase == GamePhase.ACTION:
            instructions = [
                "Click Tax/Farming buttons for planning",
                "Click End Turn to implement plan"
            ]
        elif self.phase == GamePhase.MOVE:
            instructions = [
                "Click piece to select",
                "Click target position to move",
                "Right-click piece to use skill",
                "Maximum 1 move per turn"
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
        current = self.get_current_player()
        for btn_id, info in self.buttons.items():
            # 跳过不可见的按钮
            if 'invisible' in info.keys() and info['invisible']:
                continue

            x, y = info['pos']
            w, h = info['size']
            rect = pygame.Rect(x, y, w, h)

            # 可用性：对应回合 + 对应阶段
            is_usable = True
            if btn_id.startswith('white') and current.color != 'white':
                is_usable = False
            if btn_id.startswith('black') and current.color != 'black':
                is_usable = False
            if any(k in btn_id for k in ['tax', 'farm']) and self.phase != GamePhase.ACTION:
                is_usable = False

            color = (100, 100, 200) if is_usable else (100, 100, 100)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 2)
            text = self.button_font.render(info['name'], True, WHITE)
            text_rect = text.get_rect(center=rect.center)
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
                logger.debug(f"按钮被点击: {button_id}")
                return button_id

        return None

    def handle_button_action(self, button_id):
        current = self.get_current_player()  # 当前回合玩家
        # 白方按钮只能白方回合用，黑方按钮只能黑方回合用
        usable = {
            'white_tax': current.color == 'white' and self.phase == GamePhase.ACTION,
            'white_farm': current.color == 'white' and self.phase == GamePhase.ACTION,
            'white_end': current.color == 'white',
            'black_tax': current.color == 'black' and self.phase == GamePhase.ACTION,
            'black_farm': current.color == 'black' and self.phase == GamePhase.ACTION,
            'black_end': current.color == 'black'
        }
        if not usable.get(button_id, False):
            return  # 不是对应回合，直接忽略

        # --------- 征税 ---------
        if button_id.endswith('_tax'):
            if self.management_view == ManagementView.TAX:
                self.management_view = ManagementView.NONE  # 再次点击退出
            else:
                self.management_view = ManagementView.TAX

        # --------- 屯田 ---------
        elif button_id.endswith('_farm'):
            if self.management_view == ManagementView.FARM:
                self.management_view = ManagementView.NONE
            else:
                self.management_view = ManagementView.FARM

        # --------- 结束回合 ---------
        elif button_id.endswith('_end'):
            if self.phase == GamePhase.ACTION:
                # 检查操作是否会导致负资源
                final_food, fertility_changes = self.calculate_post_operation_resources(current.color)
                
                # 检查粮草是否为负
                if final_food < 0:
                    logger.info("Cannot end turn: Not enough food for farming operations")
                    return
                    
                # 检查是否有格子的丰饶度为负
                for row in range(GRID_SIZE):
                    for col in range(GRID_SIZE):
                        if self.resource_system.territory[row][col] == current.color:
                            post_fertility = self.resource_system.fertility[row][col] + fertility_changes[row][col]
                            if post_fertility < 0:
                                logger.info(f"Cannot end turn: Fertility at ({row}, {col}) would become negative")
                                return
                
                # 执行税收 + 屯田
                tax = self.resource_system.collect_tax(current.color)
                farm_cost = self.resource_system.implement_farming(current.color)
                logger.debug(f"{current.color} 征税 {tax}，屯田花费 {farm_cost}")
                self.phase = GamePhase.MOVE
                self.management_view = ManagementView.NONE
                self.event_handler.dispatch(GameEvent.PHASE_CHANGE)

            elif self.phase == GamePhase.MOVE:
                # 轮到下一位玩家
                self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
                self.phase = GamePhase.ACTION
                self.event_handler.dispatch(GameEvent.PHASE_CHANGE)
                self.event_handler.dispatch(GameEvent.TURN_END)

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
        current_player = self.get_current_player()

        # 检查是否已超过移动次数限制
        if current_player.moves_this_turn >= PIECE_MOVE_MAX_PER_TURN:
            logger.info("Maximum moves per turn reached")
            return False

        # 检查王是否已超过移动次数限制
        if piece.type == 'king' and piece.moved_this_turn >= PIECE_KING_MOVE_MAX_PER_TURN:
            logger.info("King can only move %s per turn" % to_times(PIECE_KING_MOVE_MAX_PER_TURN))
            return False

        # 检查移动消耗
        move_cost = PIECE_MOVE_COST(piece.type, piece.moved_this_turn)
        if self.resource_system.food[current_player.color] < move_cost:
            logger.info(f"Not enough food to move {piece.type} (cost: {move_cost})")
            return False

        # 检查目标位置是否有敌方鹿角
        target_pos = (to_row, to_col)
        if target_pos in self.antlers and self.antlers[target_pos] != piece.color:
            # 吃掉鹿角（不移位，只移除鹿角）
            del self.antlers[target_pos]
            logger.debug(f"{piece.color} ate enemy antlers")
            
            # 扣除移动消耗
            self.resource_system.food[current_player.color] -= move_cost
            current_player.moves_this_turn += 1
            return True  # 不移位，但消耗移动次数和粮草

        # 检查目标位置是否有敌方堡垒
        if target_pos in self.fortresses and self.fortresses[target_pos] != piece.color:
            logger.info(f"{piece.color} cannot move to enemy fortress")
            return False  # 无法移动到敌方堡垒

        # 处理目标位置的棋子（吃子）
        target_piece = self.board[to_row][to_col]
        if target_piece:
            # 从玩家的棋子列表中移除被吃的棋子
            for player in self.players:
                if target_piece in player.pieces:
                    player.pieces.remove(target_piece)
                    break

        # 更新领土控制
        self.resource_system.update_territory(to_row, to_col, piece.color)

        # 扣除移动消耗
        self.resource_system.food[current_player.color] -= move_cost

        # 执行移动
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.row = to_row
        piece.col = to_col
        piece.moved_this_turn = True
        current_player.moves_this_turn += 1

        return True

    def get_valid_moves(self, row, col):
        piece = self.board[row][col]
        moves = []
        current_player = self.get_current_player()
        move_cost = PIECE_MOVE_COST(piece.type, piece.moved_this_turn)

        # 检查是否有足够的粮草移动这个棋子
        has_enough_food = self.resource_system.food[current_player.color] >= move_cost

        if not has_enough_food:
            return []  # 粮草不足，无法移动

        if piece.type == 'pawn':
            # 兵的特殊移动规则
            direction = 1 if piece.color == 'black' else -1
            # 基本前进
            if 0 <= row + direction < GRID_SIZE and self.board[row + direction][col] is None:
                moves.append((row + direction, col))
                # 如果是初始位置，可以前进两格
                if (piece.color == 'black' and row == 1) or (piece.color == 'white' and row == 6):
                    if self.board[row + 2 * direction][col] is None:
                        moves.append((row + 2 * direction, col))
            # 吃子斜进
            for dc in [-1, 1]:
                if 0 <= col + dc < GRID_SIZE and 0 <= row + direction < GRID_SIZE:
                    target = self.board[row + direction][col + dc]
                    if target and target.color != piece.color:
                        moves.append((row + direction, col + dc))

        elif piece.type == 'rook':
            # 车的移动规则（直线无限距离）
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                for i in range(1, GRID_SIZE):
                    r, c = row + dr * i, col + dc * i
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
            for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
                r, c = row + dr, col + dc
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    if self.board[r][c] is None or self.board[r][c].color != piece.color:
                        moves.append((r, c))

        elif piece.type == 'bishop':
            # 象的移动规则（斜线无限距离）
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, GRID_SIZE):
                    r, c = row + dr * i, col + dc * i
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
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, GRID_SIZE):
                    r, c = row + dr * i, col + dc * i
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

    def handle_management_view_click(self, pos, button):
        # 处理管理视图的点击
        grid_pos = screen_to_grid(pos[0], pos[1])
        if grid_pos is None:
            return

        row, col = grid_pos
        current_player = self.get_current_player()

        # 只有自己的领土才能操作
        if self.resource_system.territory[row][col] != current_player.color:
            return

        if self.management_view == ManagementView.TAX:
            # 税收视图
            if button == 1:  # 左键
                self.resource_system.tax_grid[row][col] = True
            elif button == 3:  # 右键
                self.resource_system.tax_grid[row][col] = False

        elif self.management_view == ManagementView.FARM:
            # 屯田视图
            if button == 1:  # 左键
                if self.resource_system.farm_grid[row][col] < FARM_MAX_PER_GRID_PER_TURN:
                    self.resource_system.farm_grid[row][col] += 1
            elif button == 3:  # 右键
                if self.resource_system.farm_grid[row][col] > 0:
                    self.resource_system.farm_grid[row][col] -= 1

    def handle_click(self, pos, button=1):
        if self.game_over:
            return

        # 先检查是否点击了按钮
        button_clicked = self.check_button_click(pos)
        if button_clicked:
            self.handle_button_action(button_clicked)
            return

        # 如果在管理视图中，处理管理视图的点击
        if self.management_view != ManagementView.NONE:
            self.handle_management_view_click(pos, button)
            return

        # 根据当前阶段决定处理逻辑
        if self.phase == GamePhase.ACTION:
            self._handle_action_phase(pos)
        elif self.phase == GamePhase.MOVE:
            self._handle_move_phase(pos, button)  # 添加button参数

    def _handle_action_phase(self, pos):
        # 行动阶段只能操作按钮，不能选择棋子
        pass

    def _handle_move_phase(self, pos, button):
        # 将屏幕坐标转换为网格坐标
        grid_pos = screen_to_grid(pos[0], pos[1])
        if grid_pos is None:
            return

        row, col = grid_pos
        current_player = self.get_current_player()

        # 右键点击 - 尝试使用技能
        if button == 3:  # 右键
            if self.board[row][col] and self.board[row][col].color == current_player.color:
                # 检查技能使用次数限制
                if current_player.skills_used_this_turn >= SKILL_MAX_PER_TURN:
                    logger.info("Maximum skills per turn reached")
                    return

                piece = self.board[row][col]
                # 尝试使用技能
                if self.cast_skill(piece):
                    current_player.skills_used_this_turn += 1
            return

        # 左键点击 - 原有的移动逻辑
        # 如果没有选中的棋子，尝试选择一个
        if self.selected_piece is None:
            if self.board[row][col] and self.board[row][col].color == current_player.color:
                self.board[row][col].selected = True
                self.selected_piece = self.board[row][col]
                # 获取有效移动位置
                self.valid_moves = self.get_valid_moves(row, col)
        else:
            # 如果已经选中了棋子，尝试移动它
            if (row, col) in self.valid_moves:
                success = self.move_piece(self.selected_piece.row, self.selected_piece.col, row, col)
                if success:
                    self.selected_piece.selected = False
                    self.selected_piece = None
                    self.valid_moves = []

                    # 检查游戏是否结束
                    self.check_game_over()
            else:
                # 如果点击了其他棋子，取消选择当前棋子
                self.selected_piece.selected = False
                self.selected_piece = None
                self.valid_moves = []

    def cast_skill(self, piece):
        current_player = self.get_current_player()

        # 检查粮草是否足够
        if not self.skill_system.can_cast_skill(piece.type, current_player.color):
            logger.info(f"Not enough food to cast {piece.type} skill")
            return False

        # 兵技能 - 放置鹿角
        if piece.type == 'pawn':
            pos = (piece.row, piece.col)
            # 检查位置是否已经有障碍物
            if pos in self.antlers or pos in self.fortresses:
                logger.info("Cannot place antlers on existing obstacle")
                return False

            # 扣除粮草并放置鹿角
            if self.skill_system.cast_skill(piece.type, current_player.color):
                self.antlers[pos] = current_player.color
                logger.debug(f"{current_player.color} placed antlers at {pos}")
                return True

        # 车技能 - 放置堡垒
        elif piece.type == 'rook':
            pos = (piece.row, piece.col)
            # 检查位置是否已经有障碍物
            if pos in self.antlers or pos in self.fortresses:
                logger.info("Cannot place fortress on existing obstacle")
                return False

            # 扣除粮草并放置堡垒
            if self.skill_system.cast_skill(piece.type, current_player.color):
                self.fortresses[pos] = current_player.color
                logger.debug(f"{current_player.color} placed fortress at {pos}")
                return True

        # 其他棋子无技能
        else:
            logger.info(f"{piece.type} has no skill")
            return False

    def on_turn_end(self, data=None):
        # 回合结束时的处理逻辑
        # 更新丰饶度
        self.resource_system.update_fertility(self.board)

        # 重置玩家和棋子的回合状态
        for player in self.players:
            player.reset_turn_state()

        # 重置管理网格
        self.resource_system.reset_management_grids()

    def on_phase_change(self, data=None):
        # 阶段变化时的处理逻辑
        if self.phase == GamePhase.ACTION:
            logger.info("进入行动阶段")
        elif self.phase == GamePhase.MOVE:
            logger.info("进入走子阶段")

    def check_game_over(self):
        # 检查游戏是否结束
        # 如果一方没有棋子，游戏结束
        for player in self.players:
            if len(player.pieces) == 0:
                self.game_over = True
                # 找到另一方作为获胜者
                for p in self.players:
                    if p != player:
                        self.winner = p.color
                break

    def reset(self):
        # 重置游戏
        self.players = [
            Player('white', 8),
            Player('black', 8),
        ]
        self.board = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_piece = None
        self.valid_moves = []
        self.current_player_idx = 0
        self.game_over = False
        self.winner = None
        self.phase = GamePhase.ACTION
        self.management_view = ManagementView.NONE
        self.initialize_board()

        # 重置资源系统
        self.resource_system = ResourceSystem()
        self.skill_system = SkillSystem(self.resource_system)

        # 重置障碍物
        self.antlers = {}
        self.fortresses = {}
        self.core_territories = {}

    def calculate_post_operation_resources(self, player_color):
        """计算操作后的粮草和丰饶度状态"""
        food = self.resource_system.food[player_color]
        fertility_changes = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # 计算税收收入
        tax_income = 0
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if (self.resource_system.tax_grid[row][col] and 
                    self.resource_system.territory[row][col] == player_color):
                    tax_amount = self.resource_system.fertility[row][col] // 10
                    tax_income += tax_amount
                    fertility_changes[row][col] -= 10  # 税收减少丰饶度
        
        # 计算屯田花费和收益
        farm_cost = 0
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                farm_times = self.resource_system.farm_grid[row][col]
                if farm_times > 0 and self.resource_system.territory[row][col] == player_color:
                    farm_cost += farm_times * 10
                    fertility_changes[row][col] += farm_times * 5  # 屯田增加丰饶度
        
        # 计算最终粮草
        final_food = food + tax_income - farm_cost
        
        return final_food, fertility_changes


# 主游戏循环
def main():
    # 创建游戏窗口
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Custom Chess Game")

    clock = pygame.time.Clock()
    game = Game()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in [1, 3]:  # 左键或右键点击
                    game.handle_click(event.pos, event.button)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # 按R键重置游戏
                    game.reset()
                elif event.key == pygame.K_a and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # Ctrl+A 标记所有可收税格子
                    if game.management_view == ManagementView.TAX:
                        current_player = game.get_current_player()
                        for row in range(GRID_SIZE):
                            for col in range(GRID_SIZE):
                                if game.resource_system.territory[row][col] == current_player.color:
                                    game.resource_system.tax_grid[row][col] = True

        # 绘制背景
        screen.fill(BACKGROUND_COLOUR)

        # 绘制游戏
        game.draw(screen)

        # 更新屏幕
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    logger.info("Game ended")
    sys.exit()


if __name__ == "__main__":
    main()

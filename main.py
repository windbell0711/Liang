import pygame
import sys
import os
import math

# 初始化pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
GRID_SIZE = 8  # 8x8棋盘

# 网格中心点坐标
GRID_NW_CENTRE = (543, 193)  # 左上第一格的中心点
GRID_SE_CENTRE = (1062, 708)  # 右下最后一格的中心点

# 计算网格间距
GRID_SPACING_X = (GRID_SE_CENTRE[0] - GRID_NW_CENTRE[0]) / (GRID_SIZE - 1)
GRID_SPACING_Y = (GRID_SE_CENTRE[1] - GRID_NW_CENTRE[1]) / (GRID_SIZE - 1)

# 棋子大小
PIECE_SIZE = 60

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
        print("Cannot load board.png, using default background")
        images['board'] = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        images['board'].fill(LIGHT_BROWN)

    # 加载棋子图片
    piece_colors = ['red', 'blue', 'green', 'yellow']
    for color in piece_colors:
        try:
            images[f'piece_{color}'] = pygame.image.load(f"images/piece_{color}.png").convert_alpha()
            images[f'piece_{color}'] = pygame.transform.scale(images[f'piece_{color}'], (PIECE_SIZE, PIECE_SIZE))
        except:
            print(f"Cannot load piece_{color}.png, using default piece")
            images[f'piece_{color}'] = pygame.Surface((PIECE_SIZE, PIECE_SIZE), pygame.SRCALPHA)
            if color == 'red':
                pygame.draw.circle(images[f'piece_{color}'], RED, (PIECE_SIZE // 2, PIECE_SIZE // 2), PIECE_SIZE // 2)
            elif color == 'blue':
                pygame.draw.circle(images[f'piece_{color}'], BLUE, (PIECE_SIZE // 2, PIECE_SIZE // 2), PIECE_SIZE // 2)
            elif color == 'green':
                pygame.draw.circle(images[f'piece_{color}'], GREEN, (PIECE_SIZE // 2, PIECE_SIZE // 2), PIECE_SIZE // 2)
            elif color == 'yellow':
                pygame.draw.circle(images[f'piece_{color}'], YELLOW, (PIECE_SIZE // 2, PIECE_SIZE // 2),
                                   PIECE_SIZE // 2)

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
    x = GRID_NW_CENTRE[0] + col * GRID_SPACING_X
    y = GRID_NW_CENTRE[1] + row * GRID_SPACING_Y
    return (x, y)


# 将屏幕坐标转换为网格坐标
def screen_to_grid(x, y):
    # 计算相对于左上角第一个格子的偏移量
    dx = x - GRID_NW_CENTRE[0]
    dy = y - GRID_NW_CENTRE[1]

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

    def draw(self, screen, images, font):
        # 计算棋子在屏幕上的位置
        x, y = grid_to_screen(self.row, self.col)

        # 如果被选中，绘制高亮效果
        if self.selected:
            highlight_rect = images['highlight'].get_rect(center=(x, y))
            screen.blit(images['highlight'], highlight_rect)

        # 绘制棋子
        piece_img = images[f'piece_{self.color}']
        piece_rect = piece_img.get_rect(center=(x, y))
        screen.blit(piece_img, piece_rect)

        # 绘制棋子ID
        text = font.render(str(self.id), True, WHITE)
        text_rect = text.get_rect(center=(x, y))
        screen.blit(text, text_rect)

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
        if self.color == 'red':
            for i in range(self.piece_count):
                row = 1
                col = i % GRID_SIZE
                self.pieces.append(Piece(i + 1, 'pawn', self.color, row, col))
        elif self.color == 'blue':
            for i in range(self.piece_count):
                row = 6
                col = i % GRID_SIZE
                self.pieces.append(Piece(i + 1, 'pawn', self.color, row, col))
        elif self.color == 'green':
            for i in range(self.piece_count):
                row = i % GRID_SIZE
                col = 1
                self.pieces.append(Piece(i + 1, 'pawn', self.color, row, col))
        elif self.color == 'yellow':
            for i in range(self.piece_count):
                row = i % GRID_SIZE
                col = 6
                self.pieces.append(Piece(i + 1, 'pawn', self.color, row, col))


# 游戏类
class Game:
    def __init__(self):
        self.images = load_images()
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 36)
        self.players = [
            Player('red', 8),
            Player('blue', 8),
            Player('green', 8),
            Player('yellow', 8)
        ]
        self.board = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_piece = None
        self.valid_moves = []
        self.current_player_idx = 0  # 当前玩家索引
        self.game_over = False
        self.winner = None
        self.initialize_board()

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

        # 绘制有效移动位置
        for row, col in self.valid_moves:
            x, y = grid_to_screen(row, col)
            move_rect = self.images['valid_move'].get_rect(center=(x, y))
            screen.blit(self.images['valid_move'], move_rect)

        # 绘制棋子
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.board[row][col]:
                    self.board[row][col].draw(screen, self.images, self.font)

        # 绘制游戏信息
        self.draw_game_info(screen)

    def draw_game_info(self, screen):
        # 绘制当前玩家信息
        current_player = self.get_current_player()
        text = self.title_font.render(f"Current Player: {current_player.color}", True, BLACK)
        screen.blit(text, (1200, 50))

        # 绘制玩家棋子信息
        y_offset = 100
        for player in self.players:
            text = self.title_font.render(f"{player.color}: {len(player.pieces)} pieces", True, BLACK)
            screen.blit(text, (1200, y_offset))
            y_offset += 50

        # 绘制操作说明
        instructions = [
            "Click on a piece to select",
            "Click on target position to move",
            "Press R to restart the game"
        ]

        for i, instruction in enumerate(instructions):
            text = self.title_font.render(instruction, True, BLACK)
            screen.blit(text, (1200, y_offset + i * 50))

        # 如果游戏结束，显示获胜者
        if self.game_over:
            winner_text = self.title_font.render(f"Game Over! Winner: {self.winner}", True, RED)
            screen.blit(winner_text, (1200, y_offset + len(instructions) * 50 + 30))

    def handle_click(self, pos):
        if self.game_over:
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
                # 获取有效移动位置（这里需要您实现）
                self.valid_moves = self.get_valid_moves(row, col)
        else:
            # 如果已经选中了棋子，尝试移动它
            if (row, col) in self.valid_moves:
                self.move_piece(self.selected_piece.row, self.selected_piece.col, row, col)
                self.selected_piece.selected = False
                self.selected_piece = None
                self.valid_moves = []

                # 切换玩家
                self.switch_player()

                # 检查游戏是否结束
                self.check_game_over()
            else:
                # 如果点击了其他棋子，取消选择当前棋子
                self.selected_piece.selected = False
                self.selected_piece = None
                self.valid_moves = []

    def get_valid_moves(self, row, col):
        # 这里需要您实现获取有效移动位置的逻辑
        # 这只是示例代码，返回相邻的位置
        moves = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            r, c = row + dr, col + dc
            if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                if self.board[r][c] is None:
                    moves.append((r, c))
        return moves

    def move_piece(self, from_row, from_col, to_row, to_col):
        # 移动棋子
        piece = self.board[from_row][from_col]
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.row = to_row
        piece.col = to_col

    def switch_player(self):
        # 切换玩家
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

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
            Player('red', 8),
            Player('blue', 8),
            Player('green', 8),
            Player('yellow', 8)
        ]
        self.board = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected_piece = None
        self.valid_moves = []
        self.current_player_idx = 0
        self.game_over = False
        self.winner = None
        self.initialize_board()


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

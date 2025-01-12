import pygame
import sys
import random

# Инициализация Pygame
pygame.init()

# Настройки экрана
WIDTH, HEIGHT = 498, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Clash Royale Emulator")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 102, 204)
RED = (204, 0, 0)

# Шрифт
font = pygame.font.Font(None, 36)

# Загрузка изображений
arena_img = pygame.image.load("img/arena.png")
arena_img = pygame.transform.scale(arena_img, (WIDTH, HEIGHT))

tower1_img = pygame.image.load("img/tower1.png")
tower1_img = pygame.transform.scale(tower1_img, (80, 120))

tower2_img = pygame.image.load("img/tower2.png")
tower2_img = pygame.transform.scale(tower2_img, (80, 120))

PLAYER_TOWERS = [(WIDTH // 2 // 4.4, HEIGHT - 400), (WIDTH // 2 // 0.695, HEIGHT - 400)]
ENEMY_TOWERS = [(WIDTH // 2 // 4.4, 255), (WIDTH // 2 // 0.695, 255)]

CARD_TYPES = {
    "giant": {"health": 2000, "damage": 150, "speed": 1, "range": 1},
    "golem": {"health": 3000, "damage": 200, "speed": 0.8, "range": 1},
    "musketeer": {"health": 600, "damage": 150, "speed": 1.2, "range": 4},
    "mega_knight": {"health": 2800, "damage": 250, "speed": 1.5, "range": 1},
    "valkyrie": {"health": 1200, "damage": 100, "speed": 1.3, "range": 1.5},
    "pekka": {"health": 1500, "damage": 300, "speed": 0.9, "range": 1},
    "goblin": {"health": 200, "damage": 50, "speed": 1.5, "range": 1},
    "skeleton": {"health": 50, "damage": 20, "speed": 1.8, "range": 1},
    "fireball": {"damage": 400, "range": 2},
    "arrows": {"damage": 100, "range": 3}
}

def snap_to_grid(x, y):
    """Привязывает координаты к ближайшей клетке."""
    cell_size = 28  # Примерный размер клетки на изображении
    snapped_x = ((x // cell_size) * cell_size + cell_size // 2) + 2
    snapped_y = ((y // cell_size) * cell_size + cell_size // 2) + 2
    return snapped_x, snapped_y

class Unit:
    def __init__(self, x, y, card_type, is_enemy):
        self.x = x
        self.y = y
        self.card_type = card_type
        self.health = CARD_TYPES[card_type]["health"]
        self.damage = CARD_TYPES[card_type]["damage"]
        self.speed = CARD_TYPES[card_type]["speed"]
        self.range = CARD_TYPES[card_type]["range"]
        self.is_enemy = is_enemy

        # Загрузка кадров анимации
        self.walk_frames = [pygame.image.load(f"img/{card_type}{int(is_enemy)}_walk_{i}.png") for i in range(2)]
        self.current_frame = 0
        self.animation_speed = 0.1  # Скорость смены кадров
        self.frame_timer = 0

        self.image = self.walk_frames[0]
        self.state = "walking"  # Возможные состояния: walking, attacking
        self.target = None

    def update_animation(self):
        self.frame_timer += self.animation_speed
        if self.frame_timer >= 1:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.walk_frames)

        if self.state == "walking":
            self.image = self.walk_frames[self.current_frame]

    def move(self):
        if self.is_enemy:
            self.y += self.speed
        else:
            self.y -= self.speed

    def attack(self, target):
        self.target = target
        self.state = "attacking"
        if self.target and self.target.health > 0:
            self.target.health -= self.damage
        else:
            self.state = "walking"  # Вернуться к хождению, если цели нет

    def draw(self):
        # Обновление анимации
        self.update_animation()
        # Отрисовка спрайта
        screen.blit(self.image, (int(self.x) - 25, int(self.y) - 25))  # Центрирование изображения
        # Отображение индикатора здоровья над персонажем
        pygame.draw.rect(screen, RED, (self.x - 25, self.y - 50, 50, 5))
        pygame.draw.rect(screen, BLUE,
                         (self.x - 25, self.y - 50, int(50 * self.health / CARD_TYPES[self.card_type]["health"]), 5))

class Tower:
    def __init__(self, x, y, is_enemy):
        self.x = x
        self.y = y
        self.health = 3000
        self.is_enemy = is_enemy

class Tower1(Tower):

    def draw(self):
        screen.blit(tower1_img, (self.x, self.y))
        pygame.draw.rect(screen, RED, (self.x, self.y - 10, 80, 5))
        pygame.draw.rect(screen, BLUE, (self.x, self.y - 10, int(80 * self.health / 3000), 5))

class Tower2(Tower):

    def draw(self):
        screen.blit(tower2_img, (self.x, self.y))
        pygame.draw.rect(screen, RED, (self.x, self.y - 10, 80, 5))
        pygame.draw.rect(screen, BLUE, (self.x, self.y - 10, int(80 * self.health / 3000), 5))

# Главное меню
def main_menu():
    while True:
        screen.fill(WHITE)
        draw_text("Clash Royale Emulator", font, BLACK, screen, WIDTH // 2, 100)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        button_1 = pygame.Rect(WIDTH // 2 - 100, 200, 200, 50)
        button_2 = pygame.Rect(WIDTH // 2 - 100, 300, 200, 50)

        pygame.draw.rect(screen, BLUE if button_1.collidepoint((mouse_x, mouse_y)) else BLACK, button_1)
        pygame.draw.rect(screen, BLUE if button_2.collidepoint((mouse_x, mouse_y)) else BLACK, button_2)

        draw_text("Play with Bot", font, WHITE, screen, WIDTH // 2, 225)
        draw_text("2 Players", font, WHITE, screen, WIDTH // 2, 325)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_1.collidepoint((mouse_x, mouse_y)):
                    game_loop(bot_mode=True)
                if button_2.collidepoint((mouse_x, mouse_y)):
                    game_loop(bot_mode=False)

        pygame.display.flip()

# Основной игровой цикл
def game_loop(bot_mode):
    player_towers = [Tower1(*pos, is_enemy=False) for pos in PLAYER_TOWERS]
    enemy_towers = [Tower2(*pos, is_enemy=True) for pos in ENEMY_TOWERS]
    player_units = []
    enemy_units = []

    running = True
    while running:
        screen.fill(WHITE)
        screen.blit(arena_img, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONUP:
                x, y = event.pos
                if 0 < x < WIDTH // 2 and 213 <= y <= 880:
                    print(x, y)
                    x, y = snap_to_grid(x, y)
                    player_units.append(Unit(x, y, 'giant', False))

        # Отрисовка башен
        for tower in player_towers + enemy_towers:
            tower.draw()

        # Движение и атака юнитов
        for unit in player_units + enemy_units:
            unit.move()
            unit.draw()

        pygame.display.flip()

# Отображение текста на экране
def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    text_rect.center = (x, y)
    surface.blit(text_obj, text_rect)

# Запуск главного меню
main_menu()

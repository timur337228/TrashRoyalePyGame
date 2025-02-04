import random
import sys
import pygame
import heapq

# Координаты мостов
BRIDGES = [(100, 550), (400, 550)]

pygame.init()

pers = ''
enemy = False


def snap_to_grid(x, y):
    cell_size = 28
    snapped_x = (x // cell_size) * cell_size + cell_size // 2
    snapped_y = (y // cell_size) * cell_size + cell_size // 2
    return snapped_x, snapped_y


# Настройки экрана
WIDTH, HEIGHT = 498, 1080
PLAYER_TOWERS = [(WIDTH // 2 // 2.6, HEIGHT - 340), (WIDTH // 2 // 0.625, HEIGHT - 340)]
ENEMY_TOWERS = [(WIDTH // 2 // 2.6, 310), (WIDTH // 2 // 0.625, 310)]
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Clash Royale Emulator")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 102, 204)
RED = (204, 0, 0)
GREEN = (0, 255, 0)
CARD_TYPES = {
    "giant": {"health": 2000, "damage": 150, "speed": 0.7, "range": 1, "time_to_attack": 3, "only_towers": True},
    "golem": {"health": 3000, "damage": 200, "speed": 0.5, "range": 1, "time_to_attack": 4, "only_towers": True},
    # "musketeer": {"health": 600, "damage": 150, "speed": 0.8, "range": 4, "time_to_attack": 2.6, "only_towers": False},
    "mega_knight": {"health": 2800, "damage": 250, "speed": 1.0, "range": 1, "time_to_attack": 3, "only_towers": False},
    "valkyrie": {"health": 1200, "damage": 100, "speed": 0.8, "range": 1.5, "time_to_attack": 2.4,
                 "only_towers": False},
    "pekka": {"health": 1500, "damage": 300, "speed": 0.9, "range": 1, "time_to_attack": 3.4, "only_towers": False},
    "goblin": {"health": 200, "damage": 50, "speed": 1.5, "range": 1, "time_to_attack": 2, "only_towers": False},
    "skeleton": {"health": 50, "damage": 20, "speed": 1.8, "range": 1, "time_to_attack": 1.6, "only_towers": False}
}

# Шрифт
font = pygame.font.Font(None, 36)
# Загрузка изображений
arena_img = pygame.image.load("img/arena.png")
arena_img = pygame.transform.scale(arena_img, (WIDTH, HEIGHT))

tower1_img = pygame.image.load("img/tower1.png")
tower1_img = pygame.transform.scale(tower1_img, (80, 120))

tower2_img = pygame.image.load("img/tower2.png")
tower2_img = pygame.transform.scale(tower2_img, (80, 120))

arrow_img = pygame.image.load("img/arrow.png")
arrow_img = pygame.transform.scale(arrow_img, (20, 50))


class Elixir:
    def __init__(self):
        self.amount = 0
        self.last_update = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update >= 2000:  # Каждые 2 секунды
            self.amount += 1
            self.last_update = current_time


elixir = Elixir()


class Unit(pygame.sprite.Sprite):
    def __init__(self, x, y, card_type, is_enemy):
        super().__init__()
        self.card_type = card_type
        self.health = CARD_TYPES[card_type]["health"]
        self.damage = CARD_TYPES[card_type]["damage"]
        self.speed = CARD_TYPES[card_type]["speed"]
        self.range = CARD_TYPES[card_type]["range"] * 50
        self.time_to_attack = CARD_TYPES[card_type]["time_to_attack"]
        self.only_towers = CARD_TYPES[card_type].get("only_towers", False)
        self.is_enemy = is_enemy

        # Загрузка кадров анимации движения и атаки
        self.walk_frames = [pygame.image.load(f"img/{card_type}{int(is_enemy)}_walk_{i}.png") for i in range(2)]
        # self.sleep_image = pygame.image.load(f"img/{card_type}{int(is_enemy)}.png")
        self.attack_frames = [pygame.image.load(f"img/{card_type}{int(is_enemy)}_attack_{i}.png") for i in range(2)]

        self.current_frame = 0
        self.animation_speed = 0.1
        self.frame_timer = 0

        self.image = self.walk_frames[0]
        self.rect = self.image.get_rect(center=(x, y))

        self.state = "walking"
        self.target = None
        self.attack_timer = 0

    def update(self, units, towers):
        if self.health == 0:
            self.kill()
        if self.state == "walking":
            self.move(units, towers)
            if self.find_target(units, towers):
                self.state = "attack"
        elif self.state == "attack":
            self.update_animation('attack')
            self.attack()

    def update_animation(self, f: str):
        if f == 'walk':
            frame_tamer = 1
        elif f == 'attack':
            frame_tamer = self.time_to_attack * 2

        self.frame_timer += self.animation_speed
        if self.frame_timer >= frame_tamer:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % (
                len(self.attack_frames) if self.state == "attack" else len(self.walk_frames))
        self.image = self.attack_frames[self.current_frame] if self.state == "attack" else self.walk_frames[
            self.current_frame]

    def move(self, units, towers):
        self.update_animation('walk')
        if units is None:
            return
        target = min(towers, key=lambda t: self.distance_to(t) if t.is_enemy != self.is_enemy else float('inf'))
        if not self.only_towers:
            target = min(units + towers, key=lambda t: self.distance_to(t) if t.is_enemy != self.is_enemy else float('inf'))


        if target and target.health > 0:
            dx, dy = target.rect.centerx - self.rect.centerx, target.rect.centery - self.rect.centery
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if int(distance) == 0:
                self.state = 'attack'
                return
            dx, dy = dx / distance, dy / distance
            self.rect.x += dx * self.speed * 2
            self.rect.y += dy * self.speed * 2
            return
        else:
            self.kill()

    def find_target(self, units, towers):
        if units is None:
            return []
        targets = [u for u in units if u.is_enemy != self.is_enemy and self.distance_to(u) <= self.range]
        if self.only_towers:
            targets = [t for t in towers if t.is_enemy != self.is_enemy and self.distance_to(t) <= self.range]
        if targets:
            self.target = min(targets, key=self.distance_to)
            return True

    def attack(self):
        if self.target and self.target.health > 0 and True:
            self.state = 'attack'
            self.speed = 0
            self.attack_timer += 1 / 60
            if self.attack_timer >= self.time_to_attack:
                self.attack_timer = 0
                print(1)
                self.target.health -= self.damage
                if self.target.health <= 0:
                    self.target.kill()
                    self.target = None
        else:
            self.state = "walking"
            self.speed = CARD_TYPES[self.card_type]["speed"]

    def draw_health_bar(self, surface):
        bar_width = self.rect.width
        bar_height = 5
        health_ratio = max(self.health, 0) / CARD_TYPES[self.card_type]["health"]
        green_width = int(bar_width * health_ratio)
        red_width = bar_width - green_width

        pygame.draw.rect(surface, GREEN, (self.rect.left, self.rect.top - 10, green_width, bar_height))
        pygame.draw.rect(surface, RED, (self.rect.left + green_width, self.rect.top - 10, red_width, bar_height))

    def distance_to(self, other):
        return ((self.rect.centerx - other.rect.centerx) ** 2 + (self.rect.centery - other.rect.centery) ** 2) ** 0.56


class Tower(pygame.sprite.Sprite):
    def __init__(self, x, y, is_enemy):
        super().__init__()
        self.image = tower1_img if not is_enemy else tower2_img
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 3000
        self.attack_timer = 0
        self.is_enemy = is_enemy

    def update(self, units, towers):
        # Проверка здоровья башни
        if self.health <= 0:
            self.kill()

    def attack(self, units):
        self.attack_timer += 1 / 60
        if self.attack_timer >= 0.5:
            self.attack_timer = 0
            for unit in units:
                if self.distance_to(unit) <= 500 and self.is_enemy != unit.is_enemy:
                    arrow = Arrow(self.rect.centerx, self.rect.centery, unit)
                    all_sprites.add(arrow)
                    return

    def distance_to(self, other):
        return ((self.rect.centerx - other.rect.centerx) ** 2 + (self.rect.centery - other.rect.centery) ** 2) ** 0.56

    def draw_health_bar(self, surface):
        bar_width = self.rect.width
        bar_height = 5
        health_ratio = max(self.health, 0) / 3000
        green_width = int(bar_width * health_ratio)
        red_width = bar_width - green_width

        pygame.draw.rect(surface, GREEN, (self.rect.left, self.rect.top - 10, green_width, bar_height))
        pygame.draw.rect(surface, RED, (self.rect.left + green_width, self.rect.top - 10, red_width, bar_height))


class Card:
    def __init__(self, card_type, is_enemy):
        self.card_type = card_type
        self.is_enemy = is_enemy
        self.selected = False
        self.image = pygame.image.load(f"img/{self.card_type}_card.png")
        self.rect = self.image.get_rect()

    def draw(self, surface, position):
        self.rect.topleft = position  # Обновляем позицию
        pygame.draw.rect(surface, RED, self.rect, 3)  # Рисуем красную рамку
        surface.blit(self.image, self.rect)

    def is_clicked(self, event):
        # Проверяем, была ли нажата кнопка
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class Arrow(pygame.sprite.Sprite):
    def __init__(self, x, y, target):
        super().__init__()
        self.image = arrow_img
        self.rect = self.image.get_rect(center=(x, y))
        self.target = target
        self.speed = 10

    def update(self, *args, **kwargs):
        if self.target and self.target.health > 0:
            dx, dy = self.target.rect.centerx - self.rect.centerx, self.target.rect.centery - self.rect.centery
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if int(distance) == 0:
                self.target.health -= 100
                self.kill()
            dx, dy = dx / distance, dy / distance

            self.rect.x += dx * self.speed
            self.rect.y += dy * self.speed

            if self.distance_to(self.target) <= 10:
                self.target.health -= 100
                self.kill()
        else:
            self.kill()

    def distance_to(self, other):
        return ((self.rect.centerx - other.rect.centerx) ** 2 + (self.rect.centery - other.rect.centery) ** 2) ** 0.5


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
                    game_loop()
                if button_2.collidepoint((mouse_x, mouse_y)):
                    game_loop()

        pygame.display.flip()


def game_loop():
    global all_sprites, pers, enemy
    all_sprites = pygame.sprite.Group()
    player_units = pygame.sprite.Group()
    enemy_units = pygame.sprite.Group()
    player_towers = pygame.sprite.Group()
    enemy_towers = pygame.sprite.Group()

    for x, y in PLAYER_TOWERS:
        tower = Tower(x, y, is_enemy=False)
        player_towers.add(tower)
        all_sprites.add(tower)

    for x, y in ENEMY_TOWERS:
        tower = Tower(x, y, is_enemy=True)
        enemy_towers.add(tower)
        all_sprites.add(tower)
    cards_player = []
    for card in sorted(list(CARD_TYPES.keys()), key=lambda *args: random.random()):
        cards_player.append(Card(card, is_enemy=False))
    cards_enemy = []
    for card in sorted(list(CARD_TYPES.keys()), key=lambda *args: random.random()):
        cards_enemy.append(Card(card, is_enemy=True))

    running = True
    while running:
        screen.blit(arena_img, (0, 0))
        for event in pygame.event.get():
            y = True
            for card in cards_player + cards_enemy:
                if card.is_clicked(event):
                    pers = card.card_type
                    enemy = card.is_enemy
                    y = False
                    break
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and y:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                mouse_x, mouse_y = snap_to_grid(mouse_x, mouse_y)
                # Выбираем тип персонажа (например, "giant")
                unit = Unit(mouse_x, mouse_y, pers, is_enemy=enemy)
                player_units.add(unit)
                all_sprites.add(unit)
        for unit in player_units:
            if unit.find_target(player_units, enemy_towers) or unit.find_target(player_units, player_towers):
                unit.attack()
        for tower in enemy_towers:
            tower.attack(player_units)
        for tower in player_towers:
            tower.attack(player_units)
        all_towers = player_towers.sprites() + enemy_towers.sprites()
        all_units = player_units.sprites() + enemy_units.sprites()
        all_sprites.update(all_units, all_towers)
        # Рисование всех спрайтов
        all_sprites.draw(screen)

        # Рисование полосок здоровья
        for sprite in all_sprites:
            if isinstance(sprite, (Unit, Tower)):
                sprite.draw_health_bar(screen)
        pygame.display.flip()

        screen.fill((150, 2, 2))
        for type_card in [cards_player, cards_enemy]:
            for i, card in enumerate(type_card):
                if i < 4:
                    card.draw(screen, (136 * i, 0 if type_card != cards_player else 1080 - 164))
                else:
                    continue

        # enemy_towers[ind].attack(player_units)


# Функция для отображения текста

def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect(center=(x, y))
    surface.blit(text_obj, text_rect)


main_menu()

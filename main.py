import random
import sys
import pygame
import math
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
pygame.display.set_caption("Tresh Royale Emulator")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 102, 204)
RED = (204, 0, 0)
GREEN = (0, 255, 0)

DOP_TYPES = ['golemit']

CARD_TYPES = {
    "giant": {"health": 2000, "damage": 150, "speed": 0.7, "range": 1, "time_to_attack": 3, "only_towers": True,
              "elixir_cost": 4, 'close_attack': True, 'splash': False, 'amount': 1},
    "golem": {"health": 3000, "damage": 200, "speed": 0.5, "range": 1, "time_to_attack": 4, "only_towers": True,
              "elixir_cost": 7, 'close_attack': True, 'splash': False, 'amount': 1, 'decay': 2},
    'golemit': {"health": 1000, "damage": 75, "speed": 0.4, "range": 1, "time_to_attack": 3, "only_towers": True,
                "elixir_cost": 5, 'close_attack': True, 'splash': False, 'amount': 2},
    "mega_knight": {"health": 2800, "damage": 150, "speed": 1.0, "range": 3, "time_to_attack": 3, "only_towers": False,
                    "elixir_cost": 7, 'close_attack': True, 'splash': 360, 'amount': 1},
    # "musketeer": {"health": 600, "damage": 150, "speed": 0.8, "range": 8, "time_to_attack": 2.6, "only_towers": False,
    #               "elixir_cost": 4, 'close_attack': True, 'splash': False, 'amount': 1},
    "valkyrie": {"health": 1200, "damage": 100, "speed": 0.8, "range": 1.5, "time_to_attack": 2.4, "only_towers": False,
                 "elixir_cost": 4, 'close_attack': True, 'splash': 360, 'amount': 1},
    "pekka": {"health": 2300, "damage": 800, "speed": 0.9, "range": 1, "time_to_attack": 3.4, "only_towers": False,
              "elixir_cost": 7, 'close_attack': True, 'splash': False, 'amount': 1},
    "goblin": {"health": 200, "damage": 50, "speed": 1.5, "range": 1, "time_to_attack": 2, "only_towers": False,
               "elixir_cost": 2, 'close_attack': True, 'splash': False, 'amount': 3},
    "skeleton": {"health": 50, "damage": 20, "speed": 1.8, "range": 1, "time_to_attack": 1.6, "only_towers": False,
                 "elixir_cost": 1, 'close_attack': True, 'splash': False, 'amount': 3}
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


def update_deck(deck, used_card):
    """
    Обновляет колоду: удаляет использованную карту и добавляет новую.
    :param deck: Текущая колода (список карт).
    :param used_card: Использованная карта.
    :return: Обновленная колода.
    """
    # Удаляем использованную карту из колоды
    deck.remove(used_card)

    # Добавляем новую карту из оставшихся доступных карт
    available_cards = list(CARD_TYPES.keys())  # Все доступные карты
    current_cards_in_deck = [card.card_type for card in deck]  # Карты, уже находящиеся в колоде

    # Находим карты, которые еще не в колоде
    new_cards = [card for card in available_cards if card not in current_cards_in_deck]

    if new_cards:
        # Добавляем случайную новую карту
        new_card_type = random.choice(new_cards)
        new_card = Card(new_card_type, is_enemy=used_card.is_enemy)
        deck.append(new_card)

    return deck


class Elixir:
    def __init__(self):
        self.amount = 7
        self.last_update = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update >= 2000:  # Каждые 2 секунды
            self.amount = min(self.amount + 1, 10)
            self.last_update = current_time

    def can_afford(self, cost):
        return self.amount >= cost

    def spend(self, cost):
        if self.can_afford(cost):
            self.amount -= cost
            return True
        return False


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
        self.splash_radius = CARD_TYPES[self.card_type]["splash"]

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

    def is_position_occupied(x, y, units):
        for unit in units:
            if unit.rect.collidepoint(x, y):
                return True
        return False

    def get_nearby_units(self, radius_degrees, facing_direction):
        nearby_units = []
        radius_radians = math.radians(radius_degrees)
        for unit in all_sprites:
            # Проверяем, что юнит вражеский и не является самим собой
            if (isinstance(unit, (Unit, Tower))
                    and unit != self
                    and unit.is_enemy != self.is_enemy):
                # Вычисляем угол к юниту
                dx = unit.rect.centerx - self.rect.centerx
                dy = unit.rect.centery - self.rect.centery
                angle_to_unit = math.atan2(dy, dx)

                # Вычисляем разницу углов
                angle_diff = abs(angle_to_unit - facing_direction)
                angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi  # Нормализация

                # Проверяем попадание в сектор и расстояние
                if (abs(angle_diff) <= radius_radians / 2
                        and self.distance_to(unit) <= self.range):
                    nearby_units.append(unit)
        return nearby_units

    def update(self, units, towers):
        if self.health <= 0:
            self.handle_death(units, towers)
            return
        if self.state == "walking":
            self.move(units, towers)
            if self.find_target(units, towers):
                self.state = "attack"
        if self.state == "attack":
            self.update_animation('attack')
            self.attack()

    def handle_death(self, units, towers):
        if self.card_type == "golem":
            # Создаем два големита
            for i, offset in enumerate([-20, 20]):  # Один слева, другой справа
                golimit = Unit(self.rect.centerx + offset, self.rect.centery, "golemit", self.is_enemy)
                if self.is_enemy:
                    enemy_units.add(golimit)  # Добавляем в группу вражеских юнитов
                else:
                    player_units.add(golimit)  # Добавляем в группу союзных юнитов
                all_sprites.add(golimit)
            # Взрыв голема
            self.create_explosion('golem', self.is_enemy, 50, 150)
        elif self.card_type == "golemit":
            self.create_explosion('golemit', self.is_enemy, 25, 75)
        self.kill()

    def create_explosion(self, name, is_enemy, damage, radius):
        explosion = Explosion(name, is_enemy, self.rect.centerx, self.rect.centery, damage, radius)
        all_sprites.add(explosion)

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
            target = min(units + towers,
                         key=lambda t: self.distance_to(t) if t.is_enemy != self.is_enemy else float('inf'))

        if target and target.health > 0:
            dx, dy = target.rect.centerx - self.rect.centerx, target.rect.centery - self.rect.centery
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if int(distance) == 0:
                self.state = 'attack'
                return

            # Проверка на необходимость движения через мост
            if (self.rect.centery < 550 and target.rect.centery > 550) or (
                    self.rect.centery > 550 and target.rect.centery < 550):
                # Находим ближайший мост
                bridge = min(BRIDGES, key=lambda b: self.distance_to_bridge(b))
                dx_bridge, dy_bridge = bridge[0] - self.rect.centerx, bridge[1] - self.rect.centery
                distance_bridge = (dx_bridge ** 2 + dy_bridge ** 2) ** 0.5
                if distance_bridge > 0:
                    dx_bridge, dy_bridge = dx_bridge / distance_bridge, dy_bridge / distance_bridge
                    self.rect.x += dx_bridge * self.speed * 2
                    self.rect.y += dy_bridge * self.speed * 2
                    return

            dx, dy = dx / distance, dy / distance
            self.rect.x += dx * self.speed * 2
            self.rect.y += dy * self.speed * 2
            return

    def distance_to_bridge(self, bridge):
        return ((self.rect.centerx - bridge[0]) ** 2 + (self.rect.centery - bridge[1]) ** 2) ** 0.5

    def find_target(self, units, towers):
        if units is None:
            return []
        targets = [t for t in towers if t.is_enemy != self.is_enemy and self.distance_to(t) <= self.range]
        if not self.only_towers:
            targets += [u for u in units if u.is_enemy != self.is_enemy and self.distance_to(u) <= self.range]
        if targets:
            self.target = min(targets, key=self.distance_to)
            return True
        self.target = None

    def attack(self):
        if self.target and self.target.health > 0:
            self.state = 'attack'
            self.speed = 0
            self.attack_timer += 1 / 60
            if self.attack_timer >= self.time_to_attack:
                self.attack_timer = 0
                if CARD_TYPES[self.card_type]["splash"]:
                    # Если атака по области, наносим урон всем целям в радиусе
                    facing_direction = math.radians(self.splash_radius)
                    for unit in self.get_nearby_units(self.splash_radius, facing_direction):
                        unit.health -= self.damage
                        if unit.health <= 0:
                            unit.kill()
                else:
                    # Если атака одиночная, наносим урон только одной цели
                    self.target.health -= self.damage
                    if self.target.health <= 0:
                        self.target = None
        else:
            self.state = "walking"
            self.speed = CARD_TYPES[self.card_type]["speed"]

    # def get_nearby_units(self, radius_degrees, facing_direction):
    #     nearby_units = []
    #     radius_radians = math.radians(radius_degrees)
    #     for unit in all_sprites:
    #         if isinstance(unit, (Unit, Tower)) and unit != self:
    #             angle_to_unit = math.atan2(unit.rect.y - self.rect.y, unit.rect.x - self.rect.x)
    #             angle_difference = (angle_to_unit - facing_direction) % (2 * math.pi)
    #             if angle_difference <= radius_radians / 2 and self.distance_to(unit) <= self.range:
    #                 nearby_units.append(unit)
    #     return nearby_units

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


class Explosion(pygame.sprite.Sprite):
    def __init__(self, card_type, is_enemy, x, y, damage, radius):
        super().__init__()
        self.frames = [pygame.image.load(f"img/boom_{card_type}_{i}.png") for i in range(3)]
        self.current_frame = 0
        self.is_enemy = is_enemy
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=(x, y))
        self.damage = damage
        self.radius = radius
        self.frame_timer = 0
        self.animation_speed = 0.1

    def update(self, *args, **kwargs):
        for mg in range(6):
            self.frame_timer += self.animation_speed
            if self.frame_timer >= 1:
                self.frame_timer = 0
                self.current_frame += 1
                if self.current_frame >= len(self.frames):
                    self.kill()
                    return
                self.image = self.frames[self.current_frame]

        # Наносим урон всем юнитам в радиусе
        if self.is_enemy:
            for unit in player_units:
                if isinstance(unit, Unit) and self.distance_to(unit) <= self.radius:
                    unit.health -= self.damage
                    if unit.health <= 0:
                        unit.kill()
        else:
            for unit in enemy_units:
                if isinstance(unit, Unit) and self.distance_to(unit) <= self.radius:
                    unit.health -= self.damage
                    if unit.health <= 0:
                        unit.kill()

    def distance_to(self, other):
        return ((self.rect.centerx - other.rect.centerx) ** 2 + (self.rect.centery - other.rect.centery) ** 2) ** 0.5


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
        if self.attack_timer >= 0.6:
            self.attack_timer = 0
            for unit in units:
                if self.distance_to(unit) <= 450 and self.is_enemy != unit.is_enemy:
                    arrow = Arrow(self.rect.centerx, self.rect.centery, unit)
                    all_sprites.add(arrow)
                    return

    def distance_to(self, other):
        return ((self.rect.centerx - other.rect.centerx) ** 2 + (self.rect.centery - other.rect.centery) ** 2) ** 0.57

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
        self.damage = 50

    def update(self, *args, **kwargs):
        if self.target and self.target.health > 0:
            dx, dy = self.target.rect.centerx - self.rect.centerx, self.target.rect.centery - self.rect.centery
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if int(distance) == 0:
                self.target.health -= self.damage
                self.kill()
                return

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


def show_result(result_text):
    while True:
        screen.fill(WHITE)
        draw_text(result_text, font, BLACK, screen, WIDTH // 2, HEIGHT // 2 - 50)

        # Кнопка "Играть снова"
        mouse_x, mouse_y = pygame.mouse.get_pos()
        button_play_again = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
        pygame.draw.rect(screen, BLUE if button_play_again.collidepoint((mouse_x, mouse_y)) else BLACK,
                         button_play_again)
        draw_text("Играть снова", font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 25)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_play_again.collidepoint((mouse_x, mouse_y)):
                    main_menu()
                    return

        pygame.display.flip()


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


class MainTower(Tower):
    def __init__(self, x, y, is_enemy):
        super().__init__(x, y, is_enemy)
        self.image = pygame.image.load(f"img/main_tower_{int(is_enemy)}.png")
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 3500  # Увеличим здоровье главной башни
        self.attack_range = 150  # Радиус атаки

    def attack(self, units):
        self.attack_timer += 1 / 60
        if self.attack_timer >= 0.5:
            self.attack_timer = 0
            for unit in units:
                if self.distance_to(unit) <= self.attack_range and self.is_enemy != unit.is_enemy:
                    arrow = Arrow(self.rect.centerx, self.rect.centery, unit)
                    all_sprites.add(arrow)
                    return


def game_loop():
    global all_sprites, pers, enemy, player_units, enemy_units, card_cell
    card_cell = None
    p = 0
    elixir1 = Elixir()
    elixir2 = Elixir()
    all_sprites = pygame.sprite.Group()
    player_units = pygame.sprite.Group()
    enemy_units = pygame.sprite.Group()
    player_towers = pygame.sprite.Group()
    enemy_towers = pygame.sprite.Group()
    cards_player = [Card(card, is_enemy=False) for card in
                    sorted(list(CARD_TYPES.keys()), key=lambda *args: random.random())]
    cards_enemy = [Card(card, is_enemy=True) for card in
                   sorted(list(CARD_TYPES.keys()), key=lambda *args: random.random())]

    for x, y in PLAYER_TOWERS:
        tower = Tower(x, y, is_enemy=False)
        player_towers.add(tower)
        all_sprites.add(tower)

    for x, y in ENEMY_TOWERS:
        tower = Tower(x, y, is_enemy=True)
        enemy_towers.add(tower)
        all_sprites.add(tower)
    main_tower_player = MainTower(250, 257, is_enemy=True)
    main_tower_enemy = MainTower(250, 834, is_enemy=False)
    player_towers.add(main_tower_player)
    enemy_towers.add(main_tower_enemy)
    all_sprites.add(main_tower_player)
    all_sprites.add(main_tower_enemy)
    # cards_player = []
    # for card in sorted(list(CARD_TYPES.keys() - DOP_TYPES), key=lambda *args: random.random()):
    #     cards_player.append(Card(card, is_enemy=False))
    # cards_enemy = []
    # for card in sorted(list(CARD_TYPES.keys() - DOP_TYPES), key=lambda *args: random.random()):
    #     cards_enemy.append(Card(card, is_enemy=True))
    cards_player = []
    for card in sorted(list(CARD_TYPES.keys()), key=lambda *args: random.random()):
        cards_player.append(Card(card, is_enemy=False))
    cards_enemy = []
    for card in sorted(list(CARD_TYPES.keys()), key=lambda *args: random.random()):
        cards_enemy.append(Card(card, is_enemy=True))

    running = True
    while running:
        if main_tower_player.health <= 0 or len(player_towers) == 0:
            show_result("Игрок 1 победил!")
            return
        if main_tower_enemy.health <= 0 or len(enemy_towers) == 0:
            show_result("Игрок 2 победил!")
            return
        if len(enemy_towers.sprites()) == 0 or len(player_towers.sprites()) == 0:
            main_menu()
            return
        screen.blit(arena_img, (0, 0))
        for event in pygame.event.get():
            y = True
            for card in cards_player:
                if card.is_clicked(event):
                    pers_player = card.card_type
                    card_cell = card
                    p = 1
                    y = False
                    break
            for card in cards_enemy:
                if card.is_clicked(event):
                    pers_enemy = card.card_type
                    card_cell = card
                    p = 2
                    y = False
                    break
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and y:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                mouse_x, mouse_y = snap_to_grid(mouse_x, mouse_y)

                if card_cell is not None:
                    if p == 1 and mouse_y >= 540:  # Игрок может ставить только на своей половине
                        if elixir1.can_afford(CARD_TYPES[pers_player]["elixir_cost"]):
                            elixir1.amount -= CARD_TYPES[pers_player]["elixir_cost"]
                            for i in range(CARD_TYPES[pers_player]['amount']):
                                unit = Unit(mouse_x + 10 * i, mouse_y, pers_player, is_enemy=False)
                                player_units.add(unit)
                                all_sprites.add(unit)
                            cards_player = update_deck(cards_player, card_cell)
                            card_cell = None
                if card_cell is not None:
                    if p == 2 and mouse_y < 540:  # Враг может ставить только на своей половине
                        if elixir2.can_afford(CARD_TYPES[pers_enemy]["elixir_cost"]):
                            elixir2.amount -= CARD_TYPES[pers_enemy]["elixir_cost"]
                            for i in range(CARD_TYPES[pers_enemy]['amount']):
                                unit = Unit(mouse_x + 10 * i, mouse_y, pers_enemy, is_enemy=True)
                                enemy_units.add(unit)
                                all_sprites.add(unit)
                            cards_enemy = update_deck(cards_enemy, card_cell)
                            card_cell = None

        all_towers = player_towers.sprites() + enemy_towers.sprites()
        all_units = player_units.sprites() + enemy_units.sprites()
        for unit in player_units:
            if (unit.find_target(player_units, enemy_towers) or unit.find_target(player_units,
                                                                                 player_towers) or
                    unit.find_target(all_units, all_towers)):
                unit.attack()
        for unit in enemy_units:
            if (unit.find_target(enemy_units, player_towers) or unit.find_target(enemy_units,
                                                                                 enemy_towers) or
                    unit.find_target(all_units, all_towers)):
                unit.attack()
        for tower in enemy_towers:
            tower.attack(player_units)
        for tower in player_towers:
            tower.attack(enemy_units)
        all_towers = player_towers.sprites() + enemy_towers.sprites()
        all_units = player_units.sprites() + enemy_units.sprites()
        all_sprites.update(all_units, all_towers)
        # Рисование всех спрайтов
        all_sprites.draw(screen)

        # Рисование полосок здоровья
        for sprite in all_sprites:
            if isinstance(sprite, (Unit, Tower)):
                sprite.draw_health_bar(screen)
        elixir1.update()
        draw_text(f"Эликсир: {elixir1.amount}", font, BLACK, screen, 422, 900)
        elixir2.update()
        draw_text(f"Эликсир: {elixir2.amount}", font, BLACK, screen, 422, 190)
        pygame.display.flip()

        screen.fill((150, 2, 2))
        for type_card in [cards_player, cards_enemy]:
            for i, card in enumerate(type_card):
                if i <= 4:
                    card.draw(screen, (136 * i, 0 if type_card == cards_enemy else 1080 - 164))

        # enemy_towers[ind].attack(player_units)


# Функция для отображения текста

def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect(center=(x, y))
    surface.blit(text_obj, text_rect)


main_menu()

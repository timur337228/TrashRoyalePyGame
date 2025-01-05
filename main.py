import pygame
import sys
from math import pi

# Инициализация Pygame
pygame.init()

# Настройки экрана
WIDTH, HEIGHT = 498, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple Clash Royale")

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


# Функция отображения текста на экране
def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    text_rect.center = (x, y)
    surface.blit(text_obj, text_rect)


# Главное меню
def main_menu():
    while True:
        screen.fill(WHITE)

        # Заголовок
        draw_text("Simple Clash Royale", font, BLACK, screen, WIDTH // 2, 100)

        # Кнопки меню
        mouse_x, mouse_y = pygame.mouse.get_pos()
        button_1 = pygame.Rect(WIDTH // 2 - 100, 200, 200, 50)
        button_2 = pygame.Rect(WIDTH // 2 - 100, 300, 200, 50)

        pygame.draw.rect(screen, BLUE if button_1.collidepoint((mouse_x, mouse_y)) else BLACK, button_1)
        pygame.draw.rect(screen, BLUE if button_2.collidepoint((mouse_x, mouse_y)) else BLACK, button_2)

        draw_text("Play with Bot", font, WHITE, screen, WIDTH // 2, 225)
        draw_text("2 Players", font, WHITE, screen, WIDTH // 2, 325)

        # Обработка событий
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
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Отображение поля боя
        screen.blit(arena_img, (0, 0))

        # Отображение башен
        screen.blit(tower1_img, (WIDTH // 2 // 4.4, HEIGHT - 400))
        screen.blit(tower1_img, (WIDTH // 2 // 0.695, HEIGHT - 400))
        screen.blit(tower2_img, (WIDTH // 2 // 4.4, 255))
        screen.blit(tower2_img, (WIDTH // 2 // 0.695, 255))

        pygame.display.flip()


# Запуск главного меню
main_menu()

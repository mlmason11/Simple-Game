import colorama
import math
import os
import pygame
import random
import time

from colorama import Fore
from os import listdir
from os.path import isfile, join

from lib.user import User


FPS = 60
PLAYER_VELOCITY = 5
WIDTH, HEIGHT = 1000, 800


pygame.init()
pygame.display.set_caption("PYLATFORMER")
window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def get_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [fil for fil in listdir(path) if isfile(join(path, fil))]

    all_sprites = {}
    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(block_size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((block_size, block_size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, block_size, block_size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

def get_coin(coin_size):
    path = join("assets", "Coins", "Coin.png")
    image = pygame.image.load(path).convert_alpha()

    scaled_image = pygame.transform.scale(image, (coin_size, coin_size))  # Scale the image to the desired coin size
    return scaled_image

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win,offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Coin(Object):
    def __init__(self, x, y, size, coin_image):
        super().__init__(x, y, size, size)
        self.image.blit(coin_image, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)
        self._collected = False  # Initialize collected state to False

    # def is_collected(self):
    #     return self.collected

    @property
    def collected(self):
        return self._collected
    
    @collected.setter
    def collected(self, collected):
        self._collected = collected

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = get_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"
        
    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = self.animation_count // self.ANIMATION_DELAY % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

class Player(Object):
    
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = get_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    num_coins = 0
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.wall_slide = False

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def make_wall_slide(self):
        if self.y_vel != 0:
            self.wall_slide = True
            self.y_vel = self.GRAVITY / 2
            self.animation_count = 0
            self.jump_count = 0

    def wall_jump(self):
        if self.wall_slide:
            self.jump()
            self.wall_slide = False

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def hit_head(self):
        self.fall_count = 0
        self.y_vel *= -1

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 1.5:
            if self.wall_slide:
                sprite_sheet = "wall_jump"
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = self.animation_count // self.ANIMATION_DELAY % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None # try to find a way to return all collided objects
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VELOCITY * 2)
    collide_right = collide(player, objects, PLAYER_VELOCITY * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VELOCITY)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VELOCITY)

    collide_vertical = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *collide_vertical]

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()
        elif obj and player.wall_slide:
            player.make_wall_slide()

def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

def generate_random_blocks(width, height, block_size, num_blocks, existing_blocks):
    random_blocks = []
    min_distance = block_size * 2  # Minimum distance between blocks

    for _ in range(num_blocks):
        while True:
            x = random.randint(0, width - block_size)
            y = random.randint(100, height - block_size - 100)
            
            new_block = Block(x, y, block_size)
            
            # Check for collisions with existing blocks
            overlap = False
            for block in existing_blocks:
                if new_block.rect.colliderect(block.rect):
                    overlap = True
                    break
            
            if not overlap:
                random_blocks.append(new_block)
                existing_blocks.append(new_block)
                break
        
    return random_blocks

def generate_random_coins(width, height, coin_size, num_coins, objects, coin_image):
    random_coins = []
    min_distance = coin_size * 2  # Minimum distance between coins

    for _ in range(num_coins):
        while True:
            x = random.randint(0, width - coin_size)
            y = random.randint(100, height - coin_size - 100)

            new_coin = Coin(x, y, coin_size, get_coin(coin_size))

            # Check for collisions with existing objects (blocks and coins)
            overlap = False
            for obj in objects:
                if new_coin.rect.colliderect(obj.rect):
                    overlap = True
                    break

            if not overlap:
                random_coins.append(new_coin)
                objects.append(new_coin)
                break

    return random_coins

def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()


def tutorial(window, user):
    clock = pygame.time.Clock()
    start = time.time()
    background, bg_image = get_background("Blue.png")
    block_size = 96
    coin_size = 32
    num_random_blocks = 10  # Adjust this number as needed
    num_random_coins = 5  # Adjust this number as needed
    offset_x = 0
    scroll_area_width = 200
    coin_image = pygame.image.load(join("assets", "Coins", "Coin.png")).convert_alpha()

    objects = []
    player = Player(100, 100, 50, 50)
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(-WIDTH // block_size, (WIDTH * 3) // block_size)]
    random_blocks = generate_random_blocks(WIDTH, HEIGHT, 96, num_random_blocks, objects)
    random_coins = generate_random_coins(WIDTH, HEIGHT, coin_size, num_random_coins, objects, coin_image)
    fire = Fire(700, HEIGHT - block_size - 64, 16, 32)
    fire.on()
    objects = [
        *objects,
        *floor,
        Block(0, HEIGHT - block_size * 2, block_size),
        Block(block_size * 3, HEIGHT - block_size * 4, block_size),
        *random_blocks,
        *random_coins,
        fire
    ]

    run = True
    while run == True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_SPACE or event.key == pygame.K_UP) and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if (player.rect.right - offset_x >= WIDTH - scroll_area_width and player.x_vel > 0) or (player.rect.left - offset_x <= scroll_area_width and player.x_vel < 0):
            offset_x += player.x_vel
    
    user.post_run_update(time.time() - start)
    pygame.quit()
    quit()

def print_pause(string):
        print(string)
        time.sleep(1)

def main(window):

    User.create_table()

    MENU_PROMPTS = """
        1. RETURNING USER
        2. NEW USER
        3. VIEW ALL USERS
        4. EXIT GAME
    """
    user_input = ""

    while user_input != "4":
        print_pause("Welcome to Simple Game. Follow the menu prompts to play.")
        print_pause(MENU_PROMPTS)
        user_input = input(">>> ")

        if user_input == "1":
            print_pause("Hello returning user, please enter your username")
            user_input = input(">>> ")
            user = User.query_by_username(user_input)
            if user:
                tutorial(window, user)
            print_pause("The username you entered does not exist. Please try again...")

        elif user_input == "2":
            print_pause("Hello new user, please enter your new username")
            user_input = input(">>> ")
            user = User(user_input)
            if user not in User.all_usernames:
                tutorial(window, user)
            print_pause("The username you entered already exists. Please try again...")

        elif user_input == "3":
            User.query_all()

        elif user_input == "4":
            break

        else:
            print_pause("Invalid choice. Please select a valid option.")


if __name__ == '__main__':
    main(window)

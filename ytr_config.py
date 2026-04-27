import pygame
import math
import random
import time

# Set Game and Window
pygame.init()
immune = False
WIN_W, WIN_H = 1560 * 1, 1000 * 1

# load audios
bulletspawn = pygame.mixer.Sound("audio/bulletspawn.mp3")
bulletspawn.set_volume(0.2)
bloom = pygame.mixer.Sound("audio/bloom.wav")
bloom.set_volume(0.2)
javsound = pygame.mixer.Sound("audio/javelin.wav")
javsound.set_volume(0.5)
wave = pygame.mixer.Sound("audio/wave.wav")
wave.set_volume(0.2)
burst = pygame.mixer.Sound("audio/burst.mp3")
burst.set_volume(0.2)
beam = pygame.mixer.Sound("audio/beam.ogg")
beam.set_volume(1)
star = pygame.mixer.Sound("audio/star.wav")
star.set_volume(0.2)
win = pygame.mixer.Sound("audio/win.mp3")
laugh = pygame.mixer.Sound("audio/evil_laugh.mp3")
lose = pygame.mixer.Sound("audio/lose.mp3")
starfall_laugh = pygame.mixer.Sound("audio/dark_laugh.mp3")
player_damage = pygame.mixer.Sound("audio/playerdamage.mp3")

# load image sprites
win_text_img = pygame.image.load("sprites/You Win.png")
win_text_img = pygame.transform.scale(win_text_img, (1000,200))
lose_text_img = pygame.image.load("sprites/You Lose.png")
lose_text_img = pygame.transform.scale(lose_text_img, (1000,200))
restart_img = pygame.image.load("sprites/restart_button.png")
quit_img = pygame.image.load("sprites/quit_button.png")
bullet_img = pygame.image.load("sprites/BOSS/BOSS - attacks/BOSS small attack.png")
bullet_img = pygame.transform.scale(bullet_img, (10, 10))  # resize if needed
ball_img = pygame.image.load("sprites/BOSS/BOSS - attacks/BOSS strong 1 attack.png")
beam_img = pygame.image.load("sprites/BOSS/BOSS - attacks/beam.png")
attack_img = pygame.image.load("sprites/HERO/HERO attack.png")
attack_img = pygame.transform.scale(attack_img, (16, 10))  # resize if needed
spear_img = pygame.image.load("sprites/BOSS/BOSS - attacks/BOSS spear.png")
boss_img = pygame.image.load("sprites/BOSS/BOSS - frames/BOSS1.png")
boss_img = pygame.transform.smoothscale(boss_img, (400, 400))  # resize if needed
hero_img = pygame.image.load("sprites/HERO/HERO - frames/HERO1.png")
boss_hit_img = pygame.image.load("sprites/BOSS/BOSS damaged.png")
boss_hit_img = pygame.transform.smoothscale(boss_hit_img, (400, 400))  # resize if needed
warning_img = pygame.image.load("sprites/BOSS/BOSS - attacks/warning.png")
warning_img = pygame.transform.smoothscale(warning_img, (20*1.2, 100*1.2))  # resize if needed
arena = pygame.image.load("sprites/Arena.png").convert()
arena = pygame.transform.scale(arena,(WIN_W,WIN_H))
arena2 = pygame.image.load("sprites/Arena Stage 2.png").convert()
arena2 = pygame.transform.scale(arena2,(WIN_W,WIN_H))

# Set display, fonts, and texts
screen = pygame.display.set_mode((WIN_W, WIN_H))
font = pygame.font.SysFont("times new roman", 40)
small_font = pygame.font.SysFont("times new roman", 28)
pygame.display.set_caption("Hell")
IMMUNE_DURATION = 400
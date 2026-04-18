import pygame
import math
import random
import time
pygame.init()
immune = False
WIN_W, WIN_H = 960, 720
bulletspawn = pygame.mixer.Sound("audio/bulletspawn.mp3")
bullet_img = pygame.image.load("sprites/BOSS/BOSS - attacks/BOSS small attack.png")
bullet_img = pygame.transform.scale(bullet_img, (16, 16))  # resize if needed
boss_img = pygame.image.load("sprites/BOSS/BOSS - frames/BOSS1.png")
boss_img = pygame.transform.smoothscale(boss_img, (400, 400))  # resize if needed
screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Hell")
IMMUNE_DURATION = 500

#functions: 

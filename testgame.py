#!/usr/bin/env python3
import pygame
import math
import random
import time


pygame.init()
WIN_W, WIN_H    = 960, 720
screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Knockback Arena")
run = True
count = 0
while run:
    count += 1
    if count >= 500:
        pygame.quit()
        run = False
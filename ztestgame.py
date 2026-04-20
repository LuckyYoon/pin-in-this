#!/usr/bin/env python3
#Imports
import pygame
import math
import random
import time
from zconfig import *

#Initialize pygame and screen
run = True
pygame.init()
clock = pygame.time.Clock()
# Load music
pygame.mixer.init()
pygame.mixer.music.load("audio/pygameboss_.mp3")
bulletspawn.set_volume(0.1)
pygame.mixer.music.set_volume(2)
# Play music (loop forever with -1)
pygame.mixer.music.play(-1)

#Dynamic variables

usage = 0
attack1on = False
attack2on = False
attack3on = False
num = 0
timers = {}
bullets = [] 
attacks = [] 


from zclasses import *
boss = Boss(800,WIN_H/2)
player = Player(50,20)
controller = Controller()
view = View()


while run:
    clock.tick(60)
    boss.hit = False
    #Register user inputs
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
         run = False
    #Allow player to move
    controller.move(player)
    controller.attack(player,attacks,timers)
    fire_attack(attacks, boss)

    #Create player and boss, will likely be moved to view class
    screen.fill((0, 0, 0))  # clear screen
    #pygame.draw.circle(screen, (50, 200, 50), (player.x,player.y), player.size)

    if delay(timers,"newframe",200):
        boss_img = pygame.image.load(f"sprites/BOSS/BOSS - frames/BOSS{num}.png").convert_alpha()
        boss_img = pygame.transform.scale(boss_img, (boss.size * 6, boss.size * 10))
        hero_img = pygame.image.load(f"sprites/HERO/HERO - frames/HERO{num}.png").convert_alpha()
        hero_img = pygame.transform.scale(hero_img, (player.size * 16, player.size * 16))
        num += 1
        if num >= 4:
            num = 0
    

    if delay(timers,"newattack",2000*random.random() + 1000) and not controller.phase:
        usage = 0
        attack3on = True
        boss.attack3(player,bullets)

    if delay(timers,"newattack",2000*random.random() + 1000) and controller.phase:
        usage = 0
        if 2 * random.random() <= 1:
            attack1on = True
            attack2on = False
        else:
            attack2on = True
            attack1on = False

    if delay(timers,"attack1",200) and usage <= 5 and attack1on and not attack2on:
        boss.attack1(bullets,5*random.random())
        usage += 1
        if usage >= 5 and len(bullets)<=0:
            attack1on = False
    

    if delay(timers,"attack2",400) and usage <= 5 and attack2on and not attack1on:
            boss.attack2(bullets,5*random.random())
            usage += 1
            if usage >= 5 and len(bullets)<=0:
                attack2on = False

    if delay(timers,"attack3",400) and usage <= 2 and attack3on:
            boss.attack3(player,bullets)
            usage += 1
            if usage >= 2 and len(bullets)<=0:
                attack3on = False
                
    # Do the boss attack once for now
    
    player.x = max(0, min(WIN_W - 20, player.x))
    player.y = max(0, min(WIN_H - 20, player.y))    

    #if delay("attack2",2000):
    #    boss.attack2(5*random.random())

    # Move bullets and such. Will be moved to diff class later.
    if attack1on or attack2on or attack3on:
        fire_bullet(bullets,player)
    #boss.move_boss()  

    view.draw_player(player,hero_img)

    
    view.draw_boss(boss,boss_img)
    view.draw_boss_healthbar(boss)
    view.draw_player_healthbar(player)

    bullets = [b for b in bullets if 0 <= b.p_x <= WIN_W and 0 <= b.p_y <= WIN_H]
    for b in bullets:
        view.draw_bullet(b,bullet_img)
    
    attacks = [a for a in attacks if 0 <= a.p_x <= WIN_W and 0 <= a.p_y <= WIN_H]
    
    for a in attacks:
        view.draw_bullet(a,attack_img)
        
    if boss.hit == True:
        boss_img = pygame.image.load("sprites/BOSS/BOSS damaged.png")

        
        
        
        #rect = bullet_img.get_rect(center=(b.p_x, b.p_y))
        #screen.blit(bullet_img, rect)
    # Immunity code
    if player.immune:
        if pygame.time.get_ticks() - player.immune_start_time >= IMMUNE_DURATION:
            player.immune = False

    if boss.hp <= 500:
        controller.phase = True
    

    pygame.display.flip()
    if pygame.time.get_ticks() >= 60000 or player.hp<=0 or boss.hp <=0 :
        pygame.quit()
        run = False
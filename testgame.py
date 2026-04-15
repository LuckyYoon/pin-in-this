#!/usr/bin/env python3
import pygame
import math
import random
import time

#Initialize pygame and screen
pygame.init()
WIN_W, WIN_H = 960, 720
screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Hell")
clock = pygame.time.Clock()
run = True

#Global variables
count = 0
hit = False
immune = False
IMMUNE_DURATION = 500
last_time = 0
usage = 0
attack1on = False
attack2on = False
attack3on = False
phase2 = False

timers = {}

def fire_bullet(bullets):
     for bullet in bullets:
         bullet.create_projectile()
         bullet.launch_projectile()
         bullet.spin_projectile()
         bullet.player_collision()


def delay(key, ms):
    now = pygame.time.get_ticks()

    if key not in timers:
        timers[key] = now
        return False

    if now - timers[key] >= ms:
        timers[key] = now
        return True

    return False


class Player:

    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.hp = 100
        self.size = 8
        self.movespeed = 4
        self.alive = True

class Controller:

    def move(self, player):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            player.x -= player.movespeed
        if keys[pygame.K_d]:
            player.x += player.movespeed
        if keys[pygame.K_w]:
            player.y -= player.movespeed
        if keys[pygame.K_s]:
            player.y += player.movespeed
        self.phase()

    def phase(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_9]:
            print("Enter Phase 2")
            global phase2
            phase2 = True

            

class Boss:
    
    def __init__(self,X,Y):
        self.X = X
        self.Y = Y
        self.HP = 1000
        self.SIZE = 20
        self.new_x = X
        self.new_y = Y
        self.movespeed = 0
        self.dx = 0
        self.dy = 0

    def random_move(self):
        self.new_x = WIN_W * random.random() 
        self.new_y = WIN_H * random.random()
        self.dx = self.new_x-self.X
        self.dy = self.new_y-self.Y
        distance = math.hypot(self.dx,self.dy)
        if distance != 0:
            self.dx /= distance
            self.dy /= distance

    def move_boss(self):
        self.X += 5*self.dx
        self.Y += 5*self.dy
        if self.X == self.new_x and self.Y == self.new_y:
            self.random_move()
        elif self.X < 20 or self.Y < 20 or self.X > WIN_W - 100 or self.Y > WIN_H - 100:
            self.random_move()
        

    def attack1(self,displace):
        #Code for the boss's first attack
        self.displace = displace
        for i in range(30):
        # Math to do radial attack
            # Create the angle for bullet direction
            angle = (2 * math.pi / 30) * i + self.displace
            # Create the velocity in x of bullet
            dx = math.cos(angle)
            # Create the velocity in y of bullet
            dy = math.sin(angle)
            #Each bullet is created as a boss projectile and added to a list
            bullet = BossProjectile(5,5,30,self.X,self.Y)
            # The bullet directions
            bullet.dx = dx
            bullet.dy = dy
            bullet.launch = True
            bullets.append(bullet)
                  

    def attack2(self,displace):
        self.displace = displace
        for i in range(20):
        #Math to do radial attack
            angle = (2 * math.pi / 20) * i + self.displace
            dx = math.cos(angle)
            dy = math.sin(angle)
               
            #Each bullet is creates as a boss projectile and added to a list
                
            bullet = BossProjectile(2,5,30,self.X ,self.Y)
            bullet.dx = dx
            bullet.dy = dy
            bullet.spin = True 
            bullet.origin_x = self.X
            bullet.origin_y = self.Y
            bullet.angle = angle
            
            bullets.append(bullet)
    
    def attack3(self):
        for i in range(15):
        # Math to do radial attack
            # Create the angle for bullet direction
            angle = (2 * math.pi / 15) * i
            # Create the velocity in x of bullet
            dx = math.cos(angle)
            # Create the velocity in y of bullet
            dy = math.sin(angle)
            #Each bullet is created as a boss projectile and added to a list
            bullet = BossProjectile(10,4,30,player.x,player.y)

        # DO NOT launch immediately
            bullet.launch = False

        # SET DELAY (1 second = 1000 ms)
            bullet.delay = 1500
            bullet.spawn_time = pygame.time.get_ticks()
            # The bullet directions
            bullet.dx = dx
            bullet.dy = dy
            bullet.launch = True
            bullets.append(bullet)
            
            
            

class Projectile:

    def __init__(self,p_speed,p_size,p_damage,p_x,p_y):
        self.p_speed = p_speed  
        self.p_size = p_size
        self.p_damage = p_damage
        self.p_x = p_x
        self.p_y = p_y
        self.origin_x = p_x
        self.origin_y = p_y
        self.dx = 0
        self.dy = 0
    

    def create_projectile(self):
        if self.delay > 0:
            color = (255, 50, 50)  # red warning
        else:
            color = (50, 200, 50)
        #Draw the projectile on the screen. Will likely be moved to view class
        pygame.draw.circle(screen, color, (int(self.p_x),int(self.p_y)), self.p_size)
    

class BossProjectile(Projectile):
    
    def __init__(self,p_speed,p_size,p_damage,p_x,p_y):
        super().__init__(p_speed,p_size,p_damage,p_x,p_y)
        self.orbit_speed = 0.01
        self.radius = 1.5
        self.angle = 0
        self.spin = False
        self.launch = False

        self.delay = 0
        self.spawn_time = 0
    def launch_projectile(self):
                # wait before launching
        if self.delay > 0:
            if pygame.time.get_ticks() - self.spawn_time >= self.delay:
                self.launch = True
                self.delay = 0  # prevent repeating
            else:
                return  # still waiting
        if self.launch:
            #Move the projectile
            self.p_x += self.dx * self.p_speed
            self.p_y += self.dy * self.p_speed

    def spin_projectile(self):
        if self.spin:
            # increase angle = spinning
            self.angle += self.orbit_speed

            # slowly expand outward
            self.radius += 1.5   # <- controls spiral outward speed

            # convert polar → cartesian
            self.p_x = self.origin_x + math.cos(self.angle) * self.radius
            self.p_y = self.origin_y + math.sin(self.angle) * self.radius

    #Boss projectiles will collide with player to do damage         
    #After a hit, player is immune for a little.
    def player_collision(self):
        
        global hit
        global immune
        global immune_start_time
        #Math for calculating a collision
         # 🚫 DO NOT DAMAGE during warning phase
        if self.delay > 0:
            return
        dist = math.hypot(player.x - self.p_x, player.y - self.p_y)
        #Check for collision and not immune
        if dist < (0.9*self.p_size + player.size) and not immune:
            player.hp -= self.p_damage
            print("Hit!")
            print(player.hp)
            #slight pause after being hit
            pygame.time.delay(200)
            #player is immune
            immune = True
            immune_start_time = pygame.time.get_ticks()
            #turn immune off after 0.5 sec
            
    

        

    

bullets = []  
boss = Boss(480,360)
player = Player(50,20)
controller = Controller()

while run:
    clock.tick(60)

    #Register user inputs
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
         run = False
    #Allow player to move
    controller.move(player)

    #Create player and boss, will likely be moved to view class
    screen.fill((0, 0, 0))  # clear screen
    pygame.draw.circle(screen, (50, 200, 50), (player.x,player.y), player.size)
    pygame.draw.circle(screen,(50, 200, 50), (boss.X,boss.Y), boss.SIZE)

    if delay("newattack",2000*random.random() + 1000) and not phase2:
        usage = 0
        attack3on = True
        boss.attack3()

    if delay("newattack",2000*random.random() + 1000) and phase2:
        usage = 0
        if 2 * random.random() <= 1:
            attack1on = True
            attack2on = False
        else:
            attack2on = True
            attack1on = False

    if delay("attack1",200) and usage <= 5 and attack1on and not attack2on:
        boss.attack1(5*random.random())
        usage += 1
        if usage >= 5 and len(bullets)<=0:
            attack1on = False
    

    if delay("attack2",400) and usage <= 5 and attack2on and not attack1on:
            boss.attack2(5*random.random())
            usage += 1
            if usage >= 5 and len(bullets)<=0:
                attack2on = False

    if delay("attack3",400) and usage <= 2 and attack3on:
            boss.attack3()
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
        fire_bullet(bullets)
    boss.move_boss()    
    bullets = [b for b in bullets if 0 <= b.p_x <= WIN_W and 0 <= b.p_y <= WIN_H]

    # Immunity code
    if immune:
        if pygame.time.get_ticks() - immune_start_time >= IMMUNE_DURATION:
            immune = False

    
    pygame.display.flip()
    if pygame.time.get_ticks() >= 30000 or player.hp<=0:
        pygame.quit()
        run = False
       
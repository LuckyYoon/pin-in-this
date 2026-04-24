import pygame
import math
import random
import time
from zconfig import *


# Model Classes

class Player:
    """
    Class for storing information about the user of the game. It stores the player's
    position, health, size, speed, living status, and immunity status.

    Attributes:
        x: Float representing the player's position in x
        y: Float representing the player's position in y
        hp: Int representing the amount of health the player has. The player dies if health is 0.
        size: Int representing the visual and hitbox size of player
        movespeed: Int representing he speed of the player.
        alive: Boolean representing if the player is alive or not
        immune: Boolean representing if the player is immune or not.
        immune_start_time: Float representing the time a player becomes immune.
    """
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.hp = 100
        self.size = 10
        self.movespeed = 4
        self.alive = True
        self.immune = False
        self.immune_start_time = 0

class Boss:
    """
    Creates a Boss character that the user will fight and attempt to defeat.

    Attributes:
        x: floats that represent the Boss' x position
        y: floats that represent the Boss' y position
        hp: an int that's the number of Boss' hit points
        size: an int that's the Boss' size/hit box
        new_x: float that indicates where the Boss will move next, x-direction wise
        new_y: float that indicates where the Boss will move next, y-direction wise
        movespeed: an int that's the Boss' movespeed
        dx: x-direction velocity
        dy: y-direction velocity
    """
    def __init__(self,X,Y):
        """
        Initializes a Boss instace

        ARGS:
            X: float that's the starting x location of the Boss
            y: float that's the starting y location of the Boss
        """
        self.x = X
        self.y = Y
        self.hp = 1000
        self.size = 60
        self.hitbox = (self.x-WIN_W//20, self.y-int(WIN_H*1/5), WIN_W//5, int(WIN_H*2/5))
        self.new_x = X
        self.new_y = Y
        self.movespeed = 0
        self.dx = 0
        self.dy = 0
        self.hit = False

    def random_move(self):
        """
        Function to set the boss's velocity to move to a random location on the screen.

        Returns:
            None
        """
        self.new_x = WIN_W * random.random() 
        self.new_y = WIN_H * random.random()
        self.dx = self.new_x-self.x
        self.dy = self.new_y-self.y
        distance = math.hypot(self.dx,self.dy)
        if distance != 0:
            self.dx /= distance
            self.dy /= distance

    def move_boss(self):
        """
        Function to move the boss. The boss will move to a random location on the screen, then pick a new location once it gets there.

        Returns:
            None
        """
        self.x += 5*self.dx
        self.y += 5*self.dy
        if self.x == self.new_x and self.y == self.new_y:
            self.random_move()
        elif self.x < 20 or self.y < 20 or self.x > WIN_W - 100 or self.y > WIN_H - 100:
            self.random_move()
        
    
    def attack1(self,bullets,displace):
        """
        Creates a radial attack spawning on the boss.
        Args:
            bullets: The global list of boss projectiles
            displace: A float representing a random number to shift the angle
            projectiles launch a little.
        """
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
            bullet = BossProjectile(5,5,20,self.x,self.y)
            # The bullet directions
            bullet.dx = dx
            bullet.dy = dy
            bullet.launch = True
            bullet.image = pygame.transform.scale(bullet_img, (10, 10))  # resize if needed
            bullets.append(bullet)
                  

    def attack2(self,bullets,displace):
        """
        Creates a radial attack spawning on the boss with a spinning effect.

        Args:
            bullets: The global list of boss projectiles
            displace: A float representing a random number to shift the angle
        
        Returns:
            None
        """
        self.displace = displace
        for i in range(30):
        #Math to do radial attack
            angle = (2 * math.pi / 30) * i + self.displace
            dx = math.cos(angle)
            dy = math.sin(angle)
               
            #Each bullet is creates as a boss projectile and added to a list
                
            bullet = BossProjectile(2,5,20,self.x ,self.y)
            bullet.dx = dx
            bullet.dy = dy
            bullet.spin = True 
            bullet.origin_x = self.x
            bullet.origin_y = self.y
            bullet.angle = angle
            bullet.radius = 2
            bullet.stable_radius = 2
            bullet.image = pygame.transform.scale(bullet_img, (10, 10))  # resize if needed
            bullets.append(bullet)
    
    def attack3(self,player,bullets):
        """
        Creates a radial attack spawning on the player with a delay before the projectiles launch.

        Args:
            player: An instance of the player class to target
            bullets: The global list of boss projectiles

        Returns:
            None
        """
        bulletspawn.play()
        for i in range(8):
        # Math to do radial attackS
            # Create the angle for bullet direction
            angle = (2 * math.pi / 8) * i
            # Create the velocity in x of bullet
            dx = math.cos(angle)
            # Create the velocity in y of bullet
            dy = math.sin(angle)
            #Each bullet is created as a boss projectile and added to a list
            bullet = BossProjectile(10,4,20,player.x,player.y)

        # DO NOT launch immediately
            bullet.launch = False

        # SET DELAY (1 second = 1000 ms)
            bullet.delay = 1500
            bullet.spawn_time = pygame.time.get_ticks()
            # The bullet directions
            bullet.dx = dx
            bullet.dy = dy
            bullet.launch = True
            bullet.image = pygame.transform.scale(bullet_img, (10, 10))  # resize if needed
            bullets.append(bullet)

    def attack4(self,bullets):
        """
        Creates a wave attack spawning on the right side of the screen.

        Args:
            bullets: The global list of boss projectiles

        Returns:
            None
        """
        #wave attack
        for i in range(10):
            bullet = BossProjectile(10,6,10,WIN_W-20,random.random()*WIN_H)
            bullet.dx = -1
            bullet.dy = 0
            bullet.launch = True
            bullet.image = pygame.transform.scale(ball_img, (25, 25))  # resize if needed
            bullets.append(bullet)
    
    def attack5(self,bullets,spawn_pos):
        """
        Creates a single bullet attack spawning at a specific position.

        Args:
            bullets: The global list of boss projectiles
            spawn_pos: The position where the bullet will spawn

        Returns:
            None
        """
        #single bullet
        bullet = BossProjectile(20,24*1.2,20,WIN_W-50,spawn_pos)
        bullet.dx = -1
        bullet.dy = 0
        bullet.launch = True
        bullet.image = pygame.transform.scale(ball_img, (120*1.2, 60*1.2))  # resize if needed
        bullets.append(bullet)
    
    def attack6(self, bullets, player):
        """
        Creates a javelin attack that spawns on the boss and aims at the player with a delay before the projectiles launch. 
        The attack also reduces the size of the arena.

        Args:
            bullets: The global list of boss projectiles
            player: An instance of the player class to target
        
        Returns:
            None
        """
        #javelin
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        dx /= dist
        dy /= dist

        prime = BossProjectile(10, 10, 10, WIN_W * (0.6 + random.random() * 0.3), WIN_H*(0.2+ random.random() * 0.5))
        prime.dx = dx
        prime.dy = dy
        prime.delay = 500
        prime.spawn_time = pygame.time.get_ticks()
        prime.launch = True
        prime.image = pygame.transform.scale(bullet_img, (20, 20))   
        bullets.append(prime)

        # === CREATE LASER SEGMENTS ===
        spacing = 15

        for i in range(1, 15):  # beam length
            seg = BossProjectile(0, 8, 10, self.x, self.y)

            seg.follow_prime_bullet = prime   # KEY LINE
            seg.offset = spacing * i   # distance behind

            seg.image = pygame.transform.scale(bullet_img, (14, 14))

            bullets.append(seg)

    def attack7(self, bullets, player):
        """
        Creates a sweeping attack that spawns on the boss and sweeps across the arena with a delay before the projectiles launch.

        Args:
            bullets: The global list of boss projectiles
            player: An instance of the player class to target
        
        Returns:
            None
        """
        # Aim at player initially
        dx = -1
        dy = -3
        angle = math.atan2(dy, dx)

        prime = BossProjectile(0, 12, 15, self.x, self.y)
        
        prime.angle = angle
        
        prime.orbit_speed = 0.01   # sweep speed (tune this)
        prime.radius = 0           # stays at boss
        prime.stable_radius = 0
        prime.origin_x = self.x
        prime.origin_y = self.y
        prime.is_laser = True
        prime.delay = 1500
        prime.spawn_time = pygame.time.get_ticks()
        prime.orbit_speed = 0.05
        prime.spin = True
        prime.base_image = pygame.transform.scale(bullet_img, (20, 20))
        prime.image = pygame.transform.scale(bullet_img, (20, 20))
        

        bullets.append(prime)

        # === CREATE LASER SEGMENTS === 
        spacing = 10
        length = 100

        for i in range(1, length):
            seg = BossProjectile(0, 10, 15, self.x, self.y)
            seg.follow_prime_laser = prime
            seg.offset = spacing * i
            seg.delay = 1500
            seg.is_laser = True
            seg.spawn_time = pygame.time.get_ticks()
            seg.base_image = pygame.transform.scale(beam_img, (14, 14))
            seg.image = seg.base_image
            
            
            bullets.append(seg)
            
        

        
                
                
                

class Projectile:
    """
    Class for projectile stats. This stores projectile speed, size,
    damage, position, and velocity.

    Attributes:
        p_speed: int, Speed of the projectile
        p_size: int, Size of the projectile
        p_damage: int, Damage the projectile will deal
        p_x: float, Spawn position of the projectile in x
        p_y: float, Spawn position of the projectile in y
        origin_x: float, x-position of where Projectile instance will spawn
        origin_y: float, y-position of where Projectile instacne will spawn
        dx: int, x velocity of Projectile
        dy: int, y velocity of Projectile
    """
    def __init__(self,p_speed,p_size,p_damage,p_x,p_y):
        """
        Initializes a Projectile

        Args:
            p_speed: int, Speed of the projectile
            p_size: int, Size of the projectile
            p_damage: int, damage of the projectile
            p_x: float, Spawn position of the projectile in x
            p_y: float, Spawn position of the projectile in y
        """
        self.p_speed = p_speed  
        self.p_size = p_size
        self.p_damage = p_damage
        self.p_x = p_x
        self.p_y = p_y
        self.origin_x = p_x
        self.origin_y = p_y
        self.dx = 0
        self.dy = 0
    

    

class BossProjectile(Projectile):
    """
    Class for projectiles the Boss fires. This inherits base stats from
    the Projectile class and adds its own functions.

    Attributes:
        orbit_speed: float, rotating speed of Boss Projectile
        radius: float, distance from position where Proejctile orbit abouts
        angle: float, direction the projectile will travel in
    """

    def __init__(self,p_speed,p_size,p_damage,p_x,p_y):
        super().__init__(p_speed,p_size,p_damage,p_x,p_y)
        self.orbit_speed = 0.01
        self.radius = 1.5
        self.stable_radius = self.radius
        self.angle = 0
        self.is_laser = False
        self.spin = False
        self.launch = False
        self.image = None
        self.base_image = None
        self.follow_prime_bullet = None   # reference to prime bullet
        self.follow_prime_laser = None   # reference to prime bullet
        self.offset = 0           # distance behind prime

        self.delay = 0
        self.spawn_time = 0
    def launch_projectile(self):
        """
        Function that moves projectiles. First checks for a delay before the launch, then changes
        projectile position based on speed and direction.

        Returns:
            None
        """

        # Follow a projectile
        if self.follow_prime_bullet:
            p = self.follow_prime_bullet

            # stay behind the projectile along its direction
            self.p_x = p.p_x - p.dx * self.offset
            self.p_y = p.p_y - p.dy * self.offset
            return
                
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
        """
        Function to apply a rotation to projectiles for specific attacks.

        Returns:
            None
        """
        # FOLLOW PRIME (laser behavior)
        if self.delay > 0:
            if pygame.time.get_ticks() - self.spawn_time >= self.delay:
                self.spin = True
                self.delay = 0  # prevent repeating
            else:
                return  # still waiting
        if self.follow_prime_laser:
                p = self.follow_prime_laser

                # recompute direction from prime angle
                dx = math.cos(p.angle)
                dy = math.sin(p.angle)

                # stay behind prime along its direction
                self.p_x = p.p_x - dx * self.offset
                self.p_y = p.p_y - dy * self.offset
                return
        
        if self.spin:
            
            # increase angle = spinning
            self.angle += self.orbit_speed

            # slowly expand outward
            self.radius += self.stable_radius   # <- controls spiral outward speed

            # convert polar → cartesian
            self.p_x = self.origin_x + math.cos(self.angle) * self.radius
            self.p_y = self.origin_y + math.sin(self.angle) * self.radius

        
    #Boss projectiles will collide with player to do damage         
    #After a hit, player is immune for a little.
    def player_collision(self,player):
        """
        Function to hit the player if a boss projectile comes too close.
        The player will lose health and become immune for a short period. 
        The game will freeze very quickly to indicate hit.

        Args:
            player: An instance of the player class
        """

        #Math for calculating a collision
        if self.delay > 0:
            return
        dist = math.hypot(player.x - self.p_x, player.y - self.p_y)
        #Check for collision and not immune
        if dist < (0.9*self.p_size + player.size) and not player.immune:
            player.hp -= self.p_damage
            print("Hit!")
            print(player.hp) 
            #slight pause after being hit
            pygame.time.delay(200)
            #player is immune
            player.immune = True
            player.immune_start_time = pygame.time.get_ticks()
            #turn immune off after 0.5 sec

class PlayerProjectile(Projectile):
    """
    Class for projectiles the Player fires. This inherits base stats from
    the Projectile class and adds its own functions.

    Attributes:
    """
    


    def __init__(self,p_speed,p_size,p_damage,p_x,p_y):
        super().__init__(p_speed,p_size,p_damage,p_x,p_y)
        self.delay = 0
        self.hit = False
        self.image = attack_img
        self.player_p_hitbox = (self.p_x,self.p_y,2,5)


    def launch_projectile(self):
        """
        Function that launches projectiles. Changes projectile position based on speed and direction.

        Returns:
            None
        """
        self.p_x += self.dx * self.p_speed
        self.p_y += self.dy * self.p_speed
        self.player_p_hitbox = (self.p_x,self.p_y,2,5)

    def boss_collision(self,boss):
        """
        Function to hit the boss if a player projectile comes too close.
        The boss will lose health.

        Args:
            boss: An instance of the boss class
        """
        if self.hit:
            return
        #Math for calculating a collision
        player_rect = pygame.Rect(self.player_p_hitbox)
        boss_rect = pygame.Rect(boss.hitbox)

        #Check for collision and not immune
        if player_rect.colliderect(boss_rect):
            boss.hp -= self.p_damage
            print("Boss Hit!")
            print(boss.hp)
            
            self.hit = True
            boss.hit = True
            
            
            
    





#View Class

class View:
    """
    Class Containing functions to draw all sprites.
    """



    def draw_player(self, player, player_img):
        """
        Draws the sprite for the player.

        Args:
            player: instance of the Player class
        """
        rect = player_img.get_rect(center= (player.x,player.y))
        screen.blit(player_img, rect)
        

    def draw_boss(self, boss, boss_img):
        """
        Draws the sprite for the boss.

        Args:
            boss: instance of the Player class
        """
        rect = boss_img.get_rect(center= (boss.x,boss.y))
        screen.blit(boss_img, rect)
            
                           
    def draw_bullet(self, bullet, live):
        """
        Draws the sprite for the projectiles.

        Args:
            bullet: instance of the Projectile class
        """    
        #color = (255, 50, 50) if bullet.delay > 0 else (50, 200, 50)
        #pygame.draw.circle(screen, color,
            #(int(bullet.p_x), int(bullet.p_y)), bullet.p_size)
        if not live:
            return
        
        img = bullet.image
        
        if hasattr(bullet, "is_laser") and bullet.is_laser:
            angle_deg = -math.degrees(
                bullet.angle if not bullet.follow_prime_laser else bullet.follow_prime_laser.angle
        )
            img = pygame.transform.rotate(bullet.base_image, angle_deg)

        rect = img.get_rect(center=(bullet.p_x, bullet.p_y))
        screen.blit(img, rect)

    def draw_boss_healthbar(self, boss):
        """
        Displays the boss healthbar at the top of the screen displaying the boss's
        current hp
        Args:
            boss: instance of the Boss Class   
        """
        # position + size of bar
        bar_width = 400
        bar_height = 20
        x = WIN_W // 2 - bar_width // 2
        y = 20

        # health ratio (0 → 1)
        ratio = boss.hp / 1000

        # background (empty bar)
        pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))

        # current health
        pygame.draw.rect(screen, (200, 50, 50),
            (x, y, int(bar_width * ratio), bar_height))

        # border
        pygame.draw.rect(screen, (255, 255, 255),
            (x, y, bar_width, bar_height), 2)
        
         # Boss name
        name_text = font.render("The Rhavenger of Yoontown", True, (255, 255, 255))
        text_rect = name_text.get_rect(center=(WIN_W // 2, y + bar_height + 15))
        screen.blit(name_text, text_rect)

    def draw_player_healthbar(self, player):
        """
        Displays the player healthbar at the top left of the screen displaying the player's
        current hp
        Args:
            player: instance of the Player Class   
        """
        bar_width = 200
        bar_height = 15
        x = 20
        y = 20

        # health ratio
        ratio = player.hp / 100  # since player max is 100

        # background
        pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))

        # color based on health
        if ratio > 0.5:
            color = (50, 200, 50)
        elif ratio > 0.25:
            color = (255, 200, 50)
        else:
            color = (255, 50, 50)

        # fill
        pygame.draw.rect(screen, color,
            (x, y, int(bar_width * ratio), bar_height))

        # border
        pygame.draw.rect(screen, (255, 255, 255),
            (x, y, bar_width, bar_height), 2)   

        name_text = font.render("Gilbert", True, (255, 255, 255))
        text_rect = name_text.get_rect(center=(x + bar_width/2, y + bar_height + 15))
        screen.blit(name_text, text_rect)


# Controller Class

class Controller:
    """
    Allows the user to control Player to move using WASD inputs and fire attacks.
    """

    def __init__(self):
        self.phase = False

    def move(self, player):
        """
        Function for moving the player with WASD keys.
        Args:
            player: Instance of the player class
        """
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            player.x -= player.movespeed
        if keys[pygame.K_d]:
            player.x += player.movespeed
        if keys[pygame.K_w]:
            player.y -= player.movespeed
        if keys[pygame.K_s]:
            player.y += player.movespeed
        self.phase2()


    def attack(self,player,attacks,timers):
        """
        Function for the player launching projectiles.
        Args:
            player: Instance of the player class
        """
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        if (keys[pygame.K_SPACE] or mouse[0])  and delay(timers, "player_shot", 200):
            # create projectile from player position
            proj = PlayerProjectile(8, 4, 20, player.x, player.y)

            # shoot upward (you can change later)
            proj.dx = 1
            proj.dy = 0
            attacks.append(proj)


    def phase2(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_9]:
            print("Enter Phase 2")
            self.phase = True


def fire_bullet(bullets,player):
     """
     Function to fire boss projectiles.
     Args:
        bullets: The list of bullets (instances of boss projectiles)
        player: Instance of the Player class
     """
     for bullet in bullets:
         bullet.launch_projectile()
         bullet.spin_projectile()
         bullet.player_collision(player)

def fire_attack(attacks,boss):
    """
    Function to fire player projectiles.
    Args:
        attacks: The list of player attacks (instances of player projectiles)
        boss: Instance of the Boss class
    """
    for attack in attacks:
         attack.launch_projectile()
         attack.boss_collision(boss)

def delay(timers, key, ms):
    """
     Function to create delays for specific actions.
     Args:
        timers: A dictionary of different objects to time. Keys are names and values are
        delay integers in ms
        key: The name of the timer
        ms: The amount of time in ms to delay by
    Returns:
        False- if the time in ms has not passed
        True- if the time in ms has passed
     """
    now = pygame.time.get_ticks()

    if key not in timers:
        timers[key] = now
        return False

    if now - timers[key] >= ms:
        timers[key] = now
        return True

    return False

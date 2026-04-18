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
        self.size = 8
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
        

    def attack1(self,bullets,displace):
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
                  

    def attack2(self,bullets,displace):
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
    
    def attack3(self,player,bullets):
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
        self.angle = 0
        self.spin = False
        self.launch = False

        self.delay = 0
        self.spawn_time = 0
    def launch_projectile(self):
        """
        Function that moves projectiles. First checks for a delay before the launch, then changes
        projectile position based on speed and direction.

        Returns:
            None ?
        """
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
        """
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

#View Class

class View:
    """
    Class Containing functions to draw all sprites.
    """
    def draw_player(self, player):
        """
        Draws the sprite for the player.

        Args:
            player: instance of the Player class
        """
        pygame.draw.circle(screen, (50, 150, 255),
            (int(player.x), int(player.y)), player.size)

    def draw_boss(self, boss):
        """
        Draws the sprite for the boss.

        Args:
            boss: instance of the Player class
        """
        pygame.draw.circle(screen, (255, 50, 50),
            (int(boss.X), int(boss.Y)), boss.SIZE)
                           
    def draw_bullet(self, bullet):
        """
        Draws the sprite for the projectiles.

        Args:
            bullet: instance of the Projectile class
        """    
        color = (255, 50, 50) if bullet.delay > 0 else (50, 200, 50)
        pygame.draw.circle(screen, color,
            (int(bullet.p_x), int(bullet.p_y)), bullet.p_size)


# Controller Class

class Controller:
    """
    Allows the user to control Player to move using WASD inputs
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


def delay(timers, key, ms):
    """
     Function to create delays for specific actions.
     Args:
        timers: A dictionary of different objects to time.
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

"""
Game classes for the Yoontown Runner game.
Defines model classes (Player, Boss, Projectiles), view classes, and controller classes.
"""

import math
import random

import pygame  # pylint: disable=no-member

from ytr_config import *  # pylint: disable=wildcard-import,unused-wildcard-import

# Model Classes


class Player:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
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

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 325
        self.size = 10
        self.movespeed = 4
        self.alive = True
        self.immune = False
        self.immune_start_time = 0


class Boss:
    """
    Creates a Boss character that the user will fight and attempt to defeat.
    Stores the Boss's position, health, size, and methods for the different boss attacks.


    Attributes:
        x: floats that represent the Boss' x position
        y: floats that represent the Boss' y position
        hp: an int that's the number of Boss' hit points
        size: an int that's the Boss' size for sprites
        hitbox:
        hit: Boolean representing if the boss was hit or not
    """

    def __init__(self, x, y):
        """
        Initializes a Boss instance.

        Args:
            x: float that's the starting x location of the Boss
            y: float that's the starting y location of the Boss
        """
        self.x = x
        self.y = y
        self.hp = 1000
        self.size = 60
        self.hitbox = (
            self.x - WIN_W // 70,
            self.y - int(WIN_H * 1 / 5),
            WIN_W // 15,
            int(WIN_H * 2 / 5),
        )
        self.hit = False

    def radial(self, bullets, displace):
        """
        Creates a radial attack spawning on the boss.
        Args:
            bullets: The global list of boss projectiles
            displace: A float representing a random number to shift the angle
            projectiles launch a little.
        """
        # 22 bullets
        for i in range(30):
            # Math to do radial attack
            # Create the angle for bullet direction
            angle = (2 * math.pi / 30) * i + displace
            # Create the velocity in x and y of bullet
            dx = math.cos(angle)
            dy = math.sin(angle)
            # Each bullet is created as a boss projectile and added to a list
            bullet = BossProjectile(6, 8, 15, self.x - 90, self.y - 20)
            # The bullet directions
            bullet.dx = dx
            bullet.dy = dy
            # Set the bullet to launch using launchprojectile
            bullet.launch = True
            # Set the bullet image
            bullet.image = pygame.transform.scale(ball_img, (60, 25))
            bullet.image = pygame.transform.rotate(
                bullet.image, 180
            )  # resize if needed
            # Make the image rotate depending on its angle
            angle = -math.degrees(angle)
            bullet.image = pygame.transform.rotate(bullet.image, angle)
            # Play the sound effect
            burst.stop()
            burst.play()
            # Add bullet to list
            bullets.append(bullet)

    def spinning_radial(self, bullets, displace):
        """
        Creates a radial attack spawning on the boss with a spinning effect.


        Args:
            bullets: The global list of boss projectiles
            displace: A float representing a random number to shift the angle
        """
        # 12 bullets
        for i in range(16):
            # Math to do radial attack
            # Create angle for bullet direction
            angle = (2 * math.pi / 25) * i + displace
            # Create velocity in x and y of bullet
            dx = math.cos(angle)
            dy = math.sin(angle)
            # Each bullet is creates as a boss projectile
            bullet = BossProjectile(2, 5, 12, self.x - 90, self.y - 20)
            # Set the bullets direction
            bullet.dx = dx
            bullet.dy = dy
            # Set the bullet to rotate using spin_projectile
            bullet.spin = True
            # The bullet's spawn origin to rotate around in spin_projectile
            bullet.origin_x = self.x
            bullet.origin_y = self.y
            # The bullet's initial angle
            bullet.angle = angle
            # The radius the bullet is rotating
            bullet.radius = 6  # this is a variable
            bullet.stable_radius = 6  # this is a constant
            # The speed of rotation for the bullet
            bullet.orbit_speed = 0.015
            # Update the bullet image
            bullet.image = pygame.transform.scale(
                bullet_img, (20, 10)
            )  # resize if needed
            bullet.image = pygame.transform.rotate(
                bullet.image, 180
            )  # resize if needed
            # Rotate the image to match the angle
            angle = -math.degrees(angle)
            bullet.image = pygame.transform.rotate(bullet.image, angle)
            # Add the bullet to the list
            bullets.append(bullet)
            # Play the sound effect
            wave.stop()
            wave.play()

    def blooming_radial(self, bullets, player):
        """
        Creates a radial attack spawning on the player with a delay before the projectiles launch.

        Args:
            player: An instance of the player class to target
            bullets: The global list of boss projectiles

        Returns:
            None
        """
        # Play the warning sound effect
        bulletspawn.play()
        # 8 bullets
        for i in range(8):
            # Math to do radial attackS
            # Create the angle for bullet direction
            angle = (2 * math.pi / 8) * i
            # Create the velocity in x of bullet
            dx = math.cos(angle)
            # Create the velocity in y of bullet
            dy = math.sin(angle)
            # Each bullet is created as a boss projectile and added to a list
            bullet = BossProjectile(10, 5, 12, player.x, player.y)

            # Makes the bullet not launch immediately
            bullet.launch = False

            # Set a delay before the bullets launch using launch_projectile
            bullet.delay = 1500  # this variable is used in launch_projectile
            bullet.spawn_time = (
                pygame.time.get_ticks()
            )  # also used in launch_projectile to see when the first bullet spawned
            # The bullet directions
            bullet.dx = dx
            bullet.dy = dy
            # The image of the bullet
            bullet.image = pygame.transform.scale(
                bullet_img, (12, 12)
            )  # resize if needed
            # Add bullet to list
            bullets.append(bullet)

    def starfall(self, bullets, displace):
        """
        Creates a star wave attack spawning on the right side of the screen.

        Args:
            bullets: The global list of boss projectiles
            displace: Random float to slightly shift bullet positions
        """
        # wave attack
        # 6 bullets

        for i in range(8):
            # initialize the bullet as a boss projectile
            # Each bullet will spawn in a line based on i
            bullet = BossProjectile(
                10, 6 * 1.4, 10, WIN_W - 20, 0.125 * WIN_H * i * displace + 60
            )
            # Set bullet x and y direction
            bullet.dx = -1
            bullet.dy = 0
            # Launch the bullet using launch_projectile
            bullet.launch = True
            # Set bullet image
            bullet.image = pygame.transform.scale(ball_img, (25 * 1.2, 10 * 1.2))
            # Add bullet to list
            bullets.append(bullet)

    def meteor(self, bullets, spawn_pos, dull):
        """
        Creates a single large meteor spawning on the right side of the screen.


        Args:
            bullets: The global list of boss projectiles
            spawn_pos: The position where the bullet will spawn
            dull: Determines if the bullet is the warning projectile or meteor
        Returns:
            None
        """
        # Warning projectile, dictates the position of the meteor(s)
        if dull:
            # Initialize warning as boss projectile
            bullet = BossProjectile(10, 0, 0, WIN_W - 100, spawn_pos)
            # Set the bullet image
            bullet.image = warning_img
            # Set the velocity in x and y
            bullet.dx = -1
            bullet.dy = 0
            # Launch the bullet using launch_projectile
            bullet.launch = True
            # Add bullet to list
            bullets.append(bullet)

        # Actual meteor projectile
        else:
            # Initialize meteor as boss projectile
            bullet = BossProjectile(40, 24 * 1.4, 20, WIN_W - 50, spawn_pos)
            # Set the velocity in x and y
            bullet.dx = -1
            bullet.dy = 0
            # Launch the bullet using launch_projectile
            bullet.launch = True
            # Set the image of the meteor
            bullet.image = pygame.transform.scale(ball_img, (120 * 1.4, 60 * 1.4))
            # Add bullet to list
            bullets.append(bullet)
            # Play the sound effect
            star.play()

    def javelin(self, bullets, player):
        """
        Creates a javelin attack that spawns on the boss, aims at the player,
        and lodges in the corners of the screen temporarily.

        Args:
            bullets: The global list of boss projectiles
            player: An instance of the player class to target
        """

        # javelin
        # Dictate velocity in x and y based on player position
        dx = player.x - self.x
        dy = player.y - self.y
        # Calculate boss distance frim player
        dist = math.hypot(dx, dy)

        # if the player is on the boss, direction is undefined
        if dist == 0:
            return

        # Make the velocity vector into a unit vector
        dx /= dist
        dy /= dist

        # Code for the head of the javelin, the 'prime' projectile. Segments will follow it.
        prime = BossProjectile(
            22,
            10,
            15,
            WIN_W * (0.6 + random.random() * 0.3),
            WIN_H * (0.2 + random.random() * 0.5),
        )
        # Dictate velocity in x and y
        prime.dx = dx
        prime.dy = dy
        # Set the delay before projectile launch using launch_projectile delay logic
        prime.delay = 1000  # used in launch_projectile
        prime.spawn_time = pygame.time.get_ticks()  # used in launch_projectile
        # Set image of the projectile
        prime.image = pygame.transform.scale(bullet_img, (20, 20))
        # Add the prime projectile to list
        bullets.append(prime)
        # Play sound effect
        javsound.play()
        # Create javelin segments
        # Spacing between each segment
        spacing = 10
        # 30 segments
        for i in range(1, 45):  # beam length
            # Initialize segment as boss projectile with arbitrary spawn point
            seg = BossProjectile(0, 8, 10, self.x, self.y)
            # Initialize the segment to follow the prime bullet
            # This logic is used in launch_projectile
            seg.follow_prime_bullet = prime
            # Set the distance for each segment behind the prime projectile
            seg.offset = spacing * i  # distance behind
            # Allow the segment to become "lodged" in the wall, making it not go off the screen
            seg.lodged = True
            # Set segment image
            seg.image = pygame.transform.scale(bullet_img, (14, 14))
            # Add segment to list
            bullets.append(seg)

    def laser(self, bullets, player):
        """
        Creates a sweeping laser that spawns near the player, waits a moment,
        then sweeps across the arena.

        Args:
            bullets: The global list of boss projectiles
            player: An instance of the player class to target
        """

        # Aim away from player initially
        dx = -50
        dy = -50
        angle = math.atan2(dy, dx)

        # Initialize the prime projectile, where the laser will rotate around
        prime = BossProjectile(0, 12, 15, player.x + 100, player.y + 50)
        # Create the angle for spin_projectile logic
        prime.angle = angle
        # Create the sweep speed of the laser
        # Make it so the laser stays in one position
        prime.radius = 0
        prime.stable_radius = 0
        # Give the projectile the laser attribute so it isn't deleted off-screen.
        prime.is_laser = True
        # Set the delay before the laser launches for spin_projectile logic
        prime.delay = 1000  # used in spin_projectile
        prime.spawn_time = pygame.time.get_ticks()  # used in spin_projectile
        # Sweep speed of the laser
        prime.orbit_speed = 0.05
        # Allow laser to spin
        prime.spin = True
        # Set image of the prime projectile
        prime.base_image = pygame.transform.scale(bullet_img, (20, 20))
        prime.image = pygame.transform.scale(bullet_img, (20, 20))
        # Play the sound effect
        beam.play()
        # Add projectile to list
        bullets.append(prime)

        # create the segments of the laser
        spacing = 10
        length = 100

        # Print 100 segments
        for i in range(1, length):
            # each laser segment is a boss projectile
            seg = BossProjectile(0, 10, 15, player.x + 100, player.y + 50)
            # set the follow prime logic for spin_projectile
            seg.follow_prime_laser = prime
            # set the offset of each segment from the prime projectile
            seg.offset = spacing * i
            # Set delay before projectile starts spinning
            seg.delay = 500  # used in spin_projectile
            seg.spawn_time = pygame.time.get_ticks()  # also used in spin_projectile
            # Set laser attribute so the segment isn't deleted when it runs off-screen.
            seg.is_laser = True
            # Set segment image
            seg.base_image = pygame.transform.scale(beam_img, (14, 14))
            seg.image = seg.base_image

            # add segment to list
            bullets.append(seg)


class Projectile:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
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
        dx: float, x velocity of Projectile
        dy: float, y velocity of Projectile
    """

    def __init__(
        self, p_speed, p_size, p_damage, p_x, p_y
    ):  # pylint: disable=too-many-arguments,too-many-positional-arguments
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


class BossProjectile(Projectile):  # pylint: disable=too-many-instance-attributes
    """
    Class for projectiles the Boss fires. This inherits base stats from
    the Projectile class and adds its own functions.


    Attributes:
        orbit_speed: float, rotating speed of Boss Projectile
        radius: variable float, distance from position where Projectile orbit abouts
        stable_radius = constant int representing the distance where the Projectile orbits about
        angle: float, direction the projectile will travel in
        is_laser: Boolean determing if the projectile is a laser or not
        spin: Boolean determing whether to spin the projectile or not
        launch: Boolean determing whether to launch the projectile or not
        image: String representing image of the projectile
        base_image: string representing image of the projectile if the image changes
        follow_prime_bullet: instance of boss projectile other projectiles may follow
        follow_prime_laser: instance of a laser boss projectile other projectiles may follow
        offset: The distance of each projectile behind the prime projectile
        lodged: Boolean determining if the projectile should run off the screen or not
        delay: int representing the delay before a bullet launches or spins
        spawn_time: float representing the time the bullet was initially called,
            used for delay calculations.
    """

    def __init__(
        self, p_speed, p_size, p_damage, p_x, p_y
    ):  # pylint: disable=too-many-arguments,too-many-positional-arguments
        super().__init__(p_speed, p_size, p_damage, p_x, p_y)
        self.orbit_speed = 0.01
        self.radius = 1.5
        self.stable_radius = self.radius
        self.angle = 0
        self.is_laser = False
        self.spin = False
        self.launch = False
        self.image = None
        self.base_image = None
        self.follow_prime_bullet = None  # reference to prime bullet
        self.follow_prime_laser = None  # reference to prime bullet
        self.offset = 0  # distance behind prime
        self.lodged = False
        self.delay = 0
        self.spawn_time = 0

    def launch_projectile(self):
        """
        Moves projectiles. First checks for a delay, then updates position
        based on speed, direction, or if the projectile is following another one.
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
                # play sound effect
                bloom.stop()
                bloom.play()
            else:
                return  # still waiting
        if self.launch:
            # Move the projectile based on speed and direction
            self.p_x += self.dx * self.p_speed
            self.p_y += self.dy * self.p_speed

    # Rotate the projectile
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

            # Increase angle by orbit speed
            self.angle += self.orbit_speed

            # slowly expand outward
            self.radius += self.stable_radius

            # translate rotations into position
            self.p_x = self.origin_x + math.cos(self.angle) * self.radius
            self.p_y = self.origin_y + math.sin(self.angle) * self.radius

    # Boss projectiles will collide with player to do damage
    # After a hit, player is immune for a little.
    def player_collision(self, player):
        """
        Function to hit the player if a boss projectile comes too close.
        The player will lose health and become immune for a short period.
        The game will freeze very quickly to indicate hit.


        Args:
            player: An instance of the player class
        """

        # If the projectile has a delay, do not damage the player
        if self.delay > 0:
            return
        # Calculate distance between player and projectile
        dist = math.hypot(player.x - self.p_x, player.y - self.p_y)
        # Check for player and projectile collision wile player isnt immune
        if dist < (0.9 * self.p_size + player.size) and not player.immune:
            # lower player hp
            player.hp -= self.p_damage
            print("Hit!")
            print(player.hp)
            # slight pause after being hit
            pygame.time.delay(100)
            # player is immune temporarily
            player.immune = True
            player.immune_start_time = pygame.time.get_ticks()
            player_damage.play()


class PlayerProjectile(Projectile):
    """
    Class for projectiles the Player fires. This inherits base stats from
    the Projectile class and adds its own functions.


    Attributes:
    hit: Boolean determining if the projectile hit the boss or not
    image: string determining the image of the projectile
    player_p_hitbox: list of attributes to construct hitbox rectangle
    """

    def __init__(
        self, p_speed, p_size, p_damage, p_x, p_y
    ):  # pylint: disable=too-many-arguments,too-many-positional-arguments
        super().__init__(p_speed, p_size, p_damage, p_x, p_y)
        self.hit = False
        self.image = attack_img
        self.player_p_hitbox = (self.p_x, self.p_y, 2, 5)

    def launch_projectile(self):
        """
        Launches the projectile by updating its position based on speed and direction.
        """
        # Move the projectile
        self.p_x += self.dx * self.p_speed
        self.p_y += self.dy * self.p_speed
        # Create hitbox
        self.player_p_hitbox = (self.p_x, self.p_y, 2, 5)

    def boss_collision(self, boss):
        """
        Function to hit the boss if a player projectile comes too close.
        The boss will lose health.


        Args:
            boss: An instance of the boss class
        """
        # If boss is hit, do not check for collisions for the same projectile
        if self.hit:
            return
        # Create rectangles
        player_rect = pygame.Rect(self.player_p_hitbox)
        boss_rect = pygame.Rect(boss.hitbox)

        # Check for player projectile and boss rectangle collision
        if player_rect.colliderect(boss_rect):
            # Lower boss hp
            boss.hp -= self.p_damage
            print("Boss Hit!")
            print(boss.hp)
            # Set the player projectile and boss hit attributes to true
            self.hit = True
            boss.hit = True


# Do later
# View Class


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
        rect = player_img.get_rect(center=(player.x, player.y))
        screen.blit(player_img, rect)

    def draw_boss(self, boss, image):
        """
        Draws the sprite for the boss.


        Args:
            boss: instance of the Boss class
            image: the boss sprite image
        """
        rect = image.get_rect(center=(boss.x, boss.y))
        screen.blit(image, rect)

    def draw_bullet(self, bullet, live):
        """
        Draws the sprite for the projectiles.


        Args:
            bullet: instance of the Projectile class
        """
        # color = (255, 50, 50) if bullet.delay > 0 else (50, 200, 50)
        # pygame.draw.circle(screen, color,
        # (int(bullet.p_x), int(bullet.p_y)), bullet.p_size)
        if not live:
            return

        img = bullet.image

        if hasattr(bullet, "is_laser") and bullet.is_laser:
            angle_deg = -math.degrees(
                bullet.angle
                if not bullet.follow_prime_laser
                else bullet.follow_prime_laser.angle
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
        bar_width = 800
        bar_height = 30
        x = WIN_W // 2 - bar_width // 2
        y = WIN_H * 0.05

        # health ratio (0 → 1)
        ratio = boss.hp / 1000

        # background (empty bar)
        pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))

        # draw bar showing current health
        pygame.draw.rect(
            screen, (200, 50, 50), (x, y, int(bar_width * ratio), bar_height)
        )

        # border
        pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 2)

        # Boss name
        name_text = font.render("The Rhavenger of Yoontown", True, (255, 255, 255))
        text_rect = name_text.get_rect(center=(WIN_W // 2, y + bar_height + 25))
        screen.blit(name_text, text_rect)

    def draw_player_healthbar(self, player):
        """
        Displays the player healthbar at the top left of the screen displaying the player's
        current hp
        Args:
            player: instance of the Player Class
        """
        # Width and height of healthbar
        bar_width = 200
        bar_height = 30
        # Position of healthbar
        x = WIN_W * 0.03
        y = WIN_H * 0.03

        # health ratio
        ratio = player.hp / 325  # since player max is 325

        # background
        pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height))

        # color based on health
        if ratio > 0.5:
            color = (50, 200, 50)
        elif ratio > 0.25:
            color = (255, 200, 50)
        else:
            color = (255, 50, 50)

        # fill bar
        pygame.draw.rect(screen, color, (x, y, int(bar_width * ratio), bar_height))

        # make border
        pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 2)

        # Add text for the player, gilbert
        name_text = small_font.render("Gilbert", True, (255, 255, 255))
        text_rect = name_text.get_rect(center=(x + bar_width / 2, y + bar_height + 15))
        screen.blit(name_text, text_rect)


# Controller Classes


class Controller:
    """
    Allows the user to control Player to move using WASD inputs and fire attacks.
    """

    def move(self, player):
        """
        Function for moving the player with WASD keys.
        Args:
            player: Instance of the player class
        """
        # Do player movement with WASD keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:  # pylint: disable=no-member
            player.x -= player.movespeed
        if keys[pygame.K_d]:  # pylint: disable=no-member
            player.x += player.movespeed
        if keys[pygame.K_w]:  # pylint: disable=no-member
            player.y -= player.movespeed
        if keys[pygame.K_s]:  # pylint: disable=no-member
            player.y += player.movespeed

    def attack(self, player, attacks, timers):
        """
        Function for the player launching projectiles.
        Args:
            player: Instance of the player class
            attacks: The list of player attacks
            timers: Dictionary of timers used by delay function
        """
        # Read player input
        keys = pygame.key.get_pressed()
        # If space bar is hit, fire attack. Delay is cooldown between attacks
        if (keys[pygame.K_SPACE]) and delay(  # pylint: disable=no-member
            timers, "player_shot", 200
        ):
            # create projectile from player position
            proj = PlayerProjectile(8, 4, 100, player.x, player.y)
            # shoot to the side
            proj.dx = 1
            proj.dy = 0
            # add to player attacks list
            attacks.append(proj)


def fire_bullet(bullets, player):
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


def fire_attack(attacks, boss):
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


class Button:  # pylint: disable=too-few-public-methods
    """A clickable UI button that renders an image and detects mouse clicks."""

    def __init__(self, x, y, image, scale):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(
            image, (int(width * scale), int(height * scale))
        )
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self):
        """Draw the button and return True if it was clicked this frame."""
        action = False
        # get mouse position
        pos = pygame.mouse.get_pos()

        # check if mouse is hovering over the button and clicks
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                action = True
        # draw button on screen
        screen.blit(self.image, (self.rect.x, self.rect.y))
        return action

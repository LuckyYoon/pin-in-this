"""
Main game loop for Yoontown Rhavenge.
Initialises pygame, manages game state, runs the boss fight, and handles win/lose conditions.
"""

import random
import pygame
from ytr_config import *  # pylint: disable=wildcard-import,unused-wildcard-import
from ytr_classes import *  # pylint: disable=wildcard-import,unused-wildcard-import

# Initialize pygame
pygame.init()  # pylint: disable=no-member
pygame.mixer.init()
clock = pygame.time.Clock()

# Start Music
pygame.mixer.music.load("audio/pygameboss.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# Create class instances
boss = Boss(WIN_W * 0.8, WIN_H / 2)
player = Player(WIN_W * 0.05, WIN_H / 2)
controller = Controller()
view = View()
restart_button = Button(WIN_W * 0.4, WIN_H * 0.4, restart_img, 2)
quit_button = Button(WIN_W * 0.4, WIN_W * 0.5, quit_img, 2)


# ================= INITIAL GAME STATE =================

# Create game data variables
bullets = []
attacks = []
timers = {}

# Set arena image
arena_img = arena

# Start animation logic
num = 0
num2 = 0
num3 = 0
num4 = 0
transition_num = 0

# Set attack logic
inf = 0
radialusage = 0
spinning_radialusage = 0
blooming_radialusage = 0
starfallusage = 0
meteoractive = False
meteorusage = 0
choose_pos = True
lodge = False
javelinusage = 0
laseractive = False
pattern1usage = 0
pattern2usage = 0
pattern3usage = 0
current_attack = None
javelintimer = 300
transition = True
win_sound_delay = 0
lose_sound_delay = 0
attack_time = 0

# Set game state logic
run = True
game_over = False
phase2 = False


# //////////////////// RUN THE GAME ////////////////////

while run:

    clock.tick(60)
    boss.hit = False

    # ================= BOSS ATTACKS =================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # pylint: disable=no-member
            run = False

    # Radial attack
    if current_attack == 1:
        if delay(timers, "radial", 150):
            boss.radial(bullets, random.random() * 0.5)
            radialusage += 1
        if radialusage > 12:
            radialusage = 0
            current_attack = None

    # Spinning Radial attack
    if current_attack == 2:
        if delay(timers, "spinning_radial", 200):
            boss.spinning_radial(bullets, random.random() * 5)
            spinning_radialusage += 1
        if spinning_radialusage > 10:
            spinning_radialusage = 0
            current_attack = None

    # Blooming Radial attack
    if current_attack == 3:
        if delay(timers, "blooming_radial", 300):
            boss.blooming_radial(bullets, player)
            blooming_radialusage += 1
        if blooming_radialusage > 10:
            blooming_radialactive = False
            blooming_radialusage = 0
            current_attack = None

    # Javelin attack
    if current_attack == 4:
        if delay(timers, "javelin", javelintimer):
            boss.javelin(bullets, player)
            javelinusage += 1

        if javelinusage > 20:
            lodge = True
            javelinusage = 0
            print("start delay")
            current_attack = None

    # Attack pattern 1 Radial, Javelin
    if current_attack == 5:
        if delay(timers, "pattern1-1", 400):
            boss.radial(bullets, random.random() * 5)
            pattern1usage += 1
        if delay(timers, "pattern1-2", 1500):
            boss.javelin(bullets, player)
            pattern1usage += 1
        if pattern1usage > 20:
            pattern1active = False
            pattern1usage = 0
            current_attack = None

    # Attack pattern 2: Spinning Radial, Javelin
    if current_attack == 6:
        if delay(timers, "pattern2-1", 1500):
            boss.spinning_radial(bullets, random.random() * 5)
            pattern2usage += 1
        if delay(timers, "pattern2-2", 500):
            boss.javelin(bullets, player)
            pattern2usage += 1

    # Starfall attack (Phase 2)
    if current_attack == 7:
        if delay(timers, "starfall", 200):
            boss.starfall(bullets, 0.8 + random.random() * 0.2)
            starfallusage += 1
            if starfallusage == 2:
                starfall_laugh.play()
        if starfallusage > 30:
            starfallusage = 0
            current_attack = None

    # Attack pattern 3: Blooming Radial, Laser
    if current_attack == 8:
        if delay(timers, "pattern3-1", 1000):
            boss.blooming_radial(bullets, player)
            pattern3usage += 1
        if delay(timers, "pattern3-2", 500 + inf):
            boss.laser(bullets, player)
            inf = 9999
            laseractive = True
        if pattern3usage > 5:
            pattern3usage = 0
            laseractive = False
            inf = 0
            current_attack = None

    # Meteor attack (Phase 2)
    if meteoractive:
        if choose_pos:
            pos = WIN_H * (0.2 + random.random() * 0.6)
            choose_pos = False
            inf = 1500
            boss.meteor(bullets, pos * (0.9 + random.random() * 0.3), True)
        if delay(timers, "meteor", 200 + inf):
            inf = 0
            boss.meteor(bullets, pos * (0.9 + random.random() * 0.3), False)
            meteorusage += 1

        if meteorusage > 12:
            meteoractive = False
            meteorusage = 0
            inf = 0
            timers.pop("meteor")

    # When Boss enters Phase 2, Meteor becomes active
    if phase2 and delay(timers, "meteortimer", 15000 + attack_time):
        choose_pos = True
        meteoractive = True

    # Checks if Javelin is lodged into the wall and determines when it disappears
    if (
        lodge
        and not current_attack == 4
        and not current_attack == 5
        and not current_attack == 6
    ):
        if delay(timers, "linger", 3500):
            bullets = [b for b in bullets if not b.lodged]
            print("end delay")
            lodge = False
            timers.pop("linger")
        if pattern2usage > 20:
            pattern2usage = 0
            current_attack = None
            if phase2:
                current_attack = 4
            else:
                lodge = True

    # Boss picks attack
    if (
        delay(timers, "newattack", 2700 + attack_time)
        and current_attack is None
        and not phase2
    ):
        current_attack = random.randint(1, 4)
        print(f"Chosen attack: {current_attack}")

    if (
        delay(timers, "newattack2", 1800 + attack_time)
        and current_attack is None
        and phase2
    ):
        current_attack = random.randint(1, 8)
        print(f"Chosen attack: {current_attack}")

    # ================= PLAYER INPUT =================

    # Controller input
    controller.move(player)
    controller.attack(player, attacks, timers)
    fire_attack(attacks, boss)

    # Prevent Player from leaving the screen
    player.x = max(0, min(WIN_W - 20, player.x))
    player.y = max(0, min(WIN_H - 20, player.y))

    # ================= DRAW GAME ELEMENTS =================

    # Changes to transition to Phase 2
    if boss.hp <= 0 and not phase2:
        attacks = []
        bullets = []

        while transition:
            if delay(timers, "transitiontime", 3500):
                transition = False
            if delay(timers, "transitionframe", 50):
                transition_num += 1
                arena_img = pygame.image.load(
                    f"sprites/arenatransition/pixil-frame-{transition_num}.png"
                )
                arena_img = pygame.transform.smoothscale(arena_img, (WIN_W, WIN_H))
                if transition_num == 69:
                    transition_num = 69
                if transition_num == 1:
                    pygame.mixer.music.load("audio/pygameboss2.mp3")
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)
            screen.fill((0, 0, 0))
            screen.blit(arena_img, (0, 0))
            pygame.display.flip()
        if delay(timers, "aftertransition", 1):
            laugh.play()
            transition = False
            phase2 = True
            boss_img = pygame.image.load(
                "sprites/BOSS/BOSS - Stage 2 Frames/BOSS-S2-0.png"
            ).convert_alpha()
            javelintimer = 150
            arena_img = arena2
            boss_hit_img = pygame.image.load("sprites/BOSS/BOSS Stage 2 damaged.png")
            boss_hit_img = pygame.transform.smoothscale(
                boss_hit_img, (400, 400)
            )  # resize if needed
            print("New Arena")
            player.x = WIN_W * 0.2
            player.y = WIN_H * 0.5
            timers.pop("aftertransition")
            boss.hp = 1000

    # Update Boss HP
    if boss.hit:
        boss_img = boss_hit_img
    screen.fill((0, 0, 0))
    screen.blit(arena_img, (0, 0))

    # Update bullets
    fire_bullet(bullets, player)

    # Immunity
    if player.immune:
        if pygame.time.get_ticks() - player.immune_start_time >= IMMUNE_DURATION:
            player.immune = False

    # ================= ANIMATIONS =================

    # Arena animation (Phase 2 only)
    if delay(timers, "newframearena", 50) and phase2:
        arena_img = pygame.image.load(
            f"sprites/ARENA Frames/pixil-frame-{num3}.png"
        ).convert_alpha()
        arena_img = pygame.transform.scale(arena_img, (WIN_W, WIN_H))
        num3 = (num3 + 1) % 12

    # Hero animation
    if delay(timers, "newframehero", 200):
        hero_img = pygame.image.load(
            f"sprites/HERO/HERO - frames/HERO{num2}.png"
        ).convert_alpha()
        hero_img = pygame.transform.scale(
            hero_img, (player.size * 16, player.size * 16)
        )

        num2 = (num2 + 1) % 4

    # Boss animation (Phase 1)
    if delay(timers, "newframeboss", 200) and not phase2:
        boss_img = pygame.image.load(
            f"sprites/BOSS/BOSS - frames/BOSS{num}.png"
        ).convert_alpha()
        boss_img = pygame.transform.scale(boss_img, (boss.size * 3, boss.size * 5))

        num = (num + 1) % 4

    # Boss animation (Phase 2)
    if delay(timers, "newframeboss2", 150) and phase2:
        boss_img = pygame.image.load(
            f"sprites/BOSS/BOSS - Stage 2 Frames/BOSS-S2-{num4}.png"
        ).convert_alpha()
        boss_img = pygame.transform.scale(
            boss_img, (boss.size * 5 * 1.5, boss.size * 5 * 1.5)
        )
        num4 = (num4 + 1) % 4

    # ================= UPDATE GAME STATE =================

    if not game_over:
        # Boss attack cleanup
        bullets = [
            b
            for b in bullets
            if 0 <= b.p_x <= WIN_W and 0 <= b.p_y <= WIN_H or b.is_laser
        ]
        for b in bullets:
            if not laseractive and b.is_laser:
                bullets.remove(b)
            view.draw_bullet(b, True)

        # Turns off laser when game is over
        if laseractive:
            if delay(timers, "laser", 5000):
                laseractive = False
                beam.stop()
                print("Stops")
                print(laseractive)
                timers.pop("laser")
                beam.stop()

        # Player attack cleanup
        attacks = [a for a in attacks if 0 <= a.p_x <= WIN_W and 0 <= a.p_y <= WIN_H]
        for a in attacks:
            view.draw_bullet(a, not a.hit)
        view.draw_player(player, hero_img)
        view.draw_boss(boss, boss_img)
        view.draw_boss_healthbar(boss)
        view.draw_player_healthbar(player)

    # ================= GAME END OPTIONS =================

    # Check if either Boss or Player health is 0 or less
    if boss.hp <= -7 or player.hp <= 0:
        beam.stop()
        bullets = []
        game_over = True
        current_attack = None
        attack_time = 999999999
        pygame.mixer.music.stop()

        # Display win screen
        if boss.hp < 0 and player.hp > 0:  # pylint: disable=chained-comparison
            screen.blit(win_text_img, (310, 70))
            if delay(timers, "winsound", win_sound_delay):
                win.play()
                win_sound_delay += 10000

        # Display lose screen
        else:
            screen.blit(lose_text_img, (310, 70))
            if delay(timers, "losesound", lose_sound_delay):
                lose.play()
                lose_sound_delay += 999999

        # Quit game
        view.draw_button(quit_button)
        if controller.handle_button(quit_button):
            break

        # Restart Button resets the game to initial state
        view.draw_button(restart_button)
        if controller.handle_button(restart_button):
            # reset game

            # Music
            pygame.mixer.music.load("audio/pygameboss.mp3")
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
            boss_hit_img = pygame.image.load("sprites/BOSS/BOSS damaged.png")
            boss_hit_img = pygame.transform.smoothscale(
                boss_hit_img, (400, 400)
            )  # resize if needed
            # Game objects
            boss = Boss(WIN_W * 0.8, WIN_H / 2)
            player = Player(WIN_W * 0.05, WIN_H / 2)
            controller = Controller()
            view = View()
            restart_button = Button(WIN_W * 0.4, WIN_H * 0.4, restart_img, 2)
            quit_button = Button(WIN_W * 0.4, WIN_W * 0.45, quit_img, 2)

            # Data
            bullets = []
            attacks = []
            game_over = False
            timers = {}
            arena_img = arena

            # Animation
            num = 0
            num2 = 0
            num3 = 0
            num4 = 0
            inf = 0
            phase2 = False
            radialactive = False
            radialusage = 0
            spinning_radialactive = False
            spinning_radialusage = 0
            blooming_radialactive = False
            blooming_radialusage = 0
            starfallactive = False
            transition_num = 0
            starfallusage = 0
            meteoractive = False
            meteorusage = 0
            choose_pos = True
            javelinactive = False
            lodge = False
            transition = True
            javelinusage = 0
            laseractive = False
            pattern1active = False
            pattern1usage = 0
            pattern2active = False
            pattern2usage = 0
            pattern3active = False
            pattern3usage = 0
            current_attack = None
            javelintimer = 300
            attack_time = 0
            win_sound_delay = 0
            lose_sound_delay = 0

    # Updates the entire visual surface
    pygame.display.flip()

# Quit pygame
pygame.quit()  # pylint: disable=no-member

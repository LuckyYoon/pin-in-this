import pygame
import math
import random

# Initialize
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Basic Bullet Hell Bossfight")
clock = pygame.time.Clock()

bullet_img = pygame.image.load("pixil-frame-0.png").convert_alpha()
bullet_img = pygame.transform.scale(bullet_img, (16, 16))  # resize if needed
boss_img = pygame.image.load("pixil-frame-0 (1).png").convert_alpha()
boss_img = pygame.transform.smoothscale(boss_img, (200, 200))  # resize if needed


# Player
player_pos = [WIDTH // 2, HEIGHT - 60]
player_speed = 5
player_radius = 8

# Boss
boss_pos = [WIDTH // 2, 100]
boss_radius = 20

# Bullets
bullets = []
bullet_speed = 2

# Shoot timer
shoot_timer = 0
shoot_delay = 60
displace = 0
running = True
count = 0
movement1 = 10
movement2 = 10
while running:
    displace += 5 * random.random()
    clock.tick(60)
    screen.fill((10, 10, 20))

    boss_pos[0] +=   (random.random()) + movement1/2 
    boss_pos[1] +=   (random.random()) + movement2/2 
    
    if boss_pos[0] > 700 or boss_pos[1] > 500:
        movement1 = -1 * 8*random.random() - 2
        movement2 = -1 * 10*random.random() - 2

    if boss_pos[0] < 100 or boss_pos[1] < 100:
       movement1 = 1 * 8*random.random() + 2
       movement2 = 1 * 10*random.random() + 2
    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_pos[0] -= player_speed
    if keys[pygame.K_RIGHT]:
        player_pos[0] += player_speed
    if keys[pygame.K_UP]:
        player_pos[1] -= player_speed
    if keys[pygame.K_DOWN]:
        player_pos[1] += player_speed

    # Clamp player
    player_pos[0] = max(0, min(WIDTH, player_pos[0]))
    player_pos[1] = max(0, min(HEIGHT, player_pos[1]))

    
    # Boss shooting pattern (radial burst)
    shoot_timer += 5
    if shoot_timer >= shoot_delay:
        shoot_timer = 0
        count += 1
        
        if count >= 50:
            shoot_delay = 2000
        for i in range(30):
            angle = (2 * math.pi / 30) * i + displace
            dx = math.cos(angle)
            dy = math.sin(angle)
            bullets.append([boss_pos[0], boss_pos[1], dx, dy])

    # Update bullets
    for b in bullets:
        b[0] += b[2] * bullet_speed
        b[1] += b[3] * bullet_speed

    # Remove off-screen bullets
    bullets = [b for b in bullets if 0 <= b[0] <= WIDTH and 0 <= b[1] <= HEIGHT]

    # Collision detection
    for b in bullets:
        dist = math.hypot(b[0] - player_pos[0], b[1] - player_pos[1])
        if dist < player_radius:
            print("Hit!")
            running = False

    # Draw boss
    rect = boss_img.get_rect(center= boss_pos)
    screen.blit(boss_img, rect)
    # Draw player
    pygame.draw.circle(screen, (50, 200, 50), player_pos, player_radius)

    # Draw bullets
    for b in bullets:
        rect = bullet_img.get_rect(center=(int(b[0]), int(b[1])))
        screen.blit(bullet_img, rect)

    pygame.display.flip()

pygame.quit()
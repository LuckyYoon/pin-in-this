#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║           K N O C K B A C K   A R E N A             ║
║                                                      ║
║  Host a game :  python knockback.py --server   ║
║  Join a game :  python knockback.py --join IP  ║
╚══════════════════════════════════════════════════════╝

Controls:
  WASD  — move
  SPACE — knockback attack (pushes all nearby players away)
"""

import pygame
import socket
import threading
import json
import sys
import math
import random
import time
import argparse

# ── Constants ──────────────────────────────────────────────────────────────────
WIN_W, WIN_H    = 960, 720
MAP_SIZE        = 600
MAP_X           = (WIN_W - MAP_SIZE) // 2
MAP_Y           = (WIN_H - MAP_SIZE) // 2
P_RADIUS        = 18
SPEED           = 5.0
FRICTION        = 0.78
KB_FORCE        = 30
KB_RADIUS       = 140
ATK_COOLDOWN    = 1.2   # seconds between attacks
ATK_FLASH_DUR   = 0.18  # seconds the ring flash shows
PORT            = 55555
TICK_RATE       = 60
MAX_PLAYERS     = 6

PLAYER_COLORS = [
    (220,  70,  70),   # red
    ( 65, 135, 225),   # blue
    ( 70, 200,  90),   # green
    (235, 185,  40),   # yellow
    (180,  70, 225),   # purple
    ( 50, 205, 205),   # cyan
]

BG_COLOR        = (22, 22, 28)
MAP_COLOR       = (42, 44, 52)
MAP_BORDER      = (180, 185, 200)
TEXT_COLOR      = (200, 205, 220)
HINT_COLOR      = (120, 125, 140)


# ── Tiny networking helpers ────────────────────────────────────────────────────

def send_msg(sock: socket.socket, data: dict) -> None:
    sock.sendall((json.dumps(data) + "\n").encode())


class LineBuffer:
    """Reassembles newline-delimited JSON messages from a TCP stream."""
    def __init__(self):
        self._buf = b""

    def feed(self, chunk: bytes):
        self._buf += chunk
        while b"\n" in self._buf:
            line, self._buf = self._buf.split(b"\n", 1)
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                pass


# ── Server-side player state ───────────────────────────────────────────────────

class Player:
    def __init__(self, pid: int, x: float, y: float, color: tuple):
        self.pid        = pid
        self.x          = x
        self.y          = y
        self.vx         = 0.0
        self.vy         = 0.0
        self.color      = list(color)
        self.atk_cd     = 0.0
        self.atk_flash  = 0.0

    def to_dict(self) -> dict:
        return {
            "pid":   self.pid,
            "x":     self.x,
            "y":     self.y,
            "color": self.color,
            "flash": self.atk_flash > 0,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  SERVER
# ══════════════════════════════════════════════════════════════════════════════

class GameServer:
    def __init__(self):
        self.players:  dict[int, Player]        = {}
        self.inputs:   dict[int, dict]          = {}
        self.clients:  dict[int, socket.socket] = {}
        self.lock      = threading.Lock()
        self.next_pid  = 0
        self.running   = True

    # ── Network ────────────────────────────────────────────────────────────────

    def start(self):
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("", PORT))
        self.srv.listen(MAX_PLAYERS)

        # Try to get the LAN IP
        try:
            tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            tmp.connect(("8.8.8.8", 80))
            lan_ip = tmp.getsockname()[0]
            tmp.close()
        except OSError:
            lan_ip = "127.0.0.1"

        print("=" * 52)
        print("  KNOCKBACK ARENA  —  Server running")
        print(f"  LAN address : {lan_ip}:{PORT}")
        print(f"  Others join : python knockback.py --join {lan_ip}")
        print("=" * 52)

        threading.Thread(target=self._accept_loop, daemon=True).start()
        self._game_loop()

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.srv.accept()
            except OSError:
                break

            with self.lock:
                pid   = self.next_pid
                self.next_pid += 1
                color = PLAYER_COLORS[pid % len(PLAYER_COLORS)]
                # Spawn in the center area
                cx = MAP_X + MAP_SIZE / 2 + random.uniform(-60, 60)
                cy = MAP_Y + MAP_SIZE / 2 + random.uniform(-60, 60)
                self.players[pid]  = Player(pid, cx, cy, color)
                self.inputs[pid]   = {"dx": 0, "dy": 0, "attack": False}
                self.clients[pid]  = conn

            print(f"[+] Player {pid} connected from {addr[0]}")
            send_msg(conn, {"type": "init", "pid": pid, "color": list(color)})
            threading.Thread(target=self._recv_loop,
                             args=(pid, conn), daemon=True).start()

    def _recv_loop(self, pid: int, conn: socket.socket):
        lb = LineBuffer()
        while self.running:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                for msg in lb.feed(data):
                    if msg.get("type") == "input":
                        with self.lock:
                            if pid in self.inputs:
                                self.inputs[pid] = msg
            except OSError:
                break

        print(f"[-] Player {pid} disconnected")
        with self.lock:
            for d in (self.players, self.inputs, self.clients):
                d.pop(pid, None)
        try:
            conn.close()
        except OSError:
            pass

    def _broadcast(self, data: dict):
        raw  = (json.dumps(data) + "\n").encode()
        dead = []
        with self.lock:
            for pid, conn in self.clients.items():
                try:
                    conn.sendall(raw)
                except OSError:
                    dead.append(pid)
            for pid in dead:
                for d in (self.players, self.inputs, self.clients):
                    d.pop(pid, None)

    # ── Physics / game loop ────────────────────────────────────────────────────

    def _game_loop(self):
        dt   = 1.0 / TICK_RATE
        last = time.perf_counter()

        while self.running:
            # Rate-limit the loop
            now = time.perf_counter()
            if now - last < dt:
                time.sleep(dt - (now - last))
                now = time.perf_counter()
            elapsed = min(now - last, 0.1)   # cap at 100 ms to avoid spirals
            last    = now

            with self.lock:
                pids = list(self.players.keys())

                for pid in pids:
                    p   = self.players[pid]
                    inp = self.inputs.get(pid, {})
                    dx, dy = inp.get("dx", 0), inp.get("dy", 0)

                    # Movement
                    mag = math.hypot(dx, dy)
                    if mag:
                        p.vx += (dx / mag) * SPEED
                        p.vy += (dy / mag) * SPEED

                    # Cooldowns
                    p.atk_cd    = max(0.0, p.atk_cd    - elapsed)
                    p.atk_flash = max(0.0, p.atk_flash - elapsed)

                    # Attack
                    if inp.get("attack") and p.atk_cd == 0.0:
                        p.atk_cd    = ATK_COOLDOWN
                        p.atk_flash = ATK_FLASH_DUR
                        self.inputs[pid]["attack"] = False   # consume

                        for other_pid in pids:
                            if other_pid == pid:
                                continue
                            o    = self.players[other_pid]
                            ddx  = o.x - p.x
                            ddy  = o.y - p.y
                            dist = math.hypot(ddx, ddy)
                            if 0 < dist <= KB_RADIUS:
                                force = KB_FORCE * (1.0 - dist / KB_RADIUS)
                                o.vx += (ddx / dist) * force
                                o.vy += (ddy / dist) * force

                # Integrate velocities & apply friction
                for pid in pids:
                    p     = self.players[pid]
                    p.vx *= FRICTION
                    p.vy *= FRICTION
                    p.x  += p.vx
                    p.y  += p.vy

                    # Wall bounce
                    l = MAP_X + P_RADIUS;   r = MAP_X + MAP_SIZE - P_RADIUS
                    t = MAP_Y + P_RADIUS;   b = MAP_Y + MAP_SIZE - P_RADIUS
                    if p.x < l: p.x =  l; p.vx =  abs(p.vx) * 0.4
                    if p.x > r: p.x =  r; p.vx = -abs(p.vx) * 0.4
                    if p.y < t: p.y =  t; p.vy =  abs(p.vy) * 0.4
                    if p.y > b: p.y =  b; p.vy = -abs(p.vy) * 0.4

                # Simple player-player separation
                for i, pid in enumerate(pids):
                    for other_pid in pids[i+1:]:
                        p, o  = self.players[pid], self.players[other_pid]
                        ddx   = o.x - p.x
                        ddy   = o.y - p.y
                        dist  = math.hypot(ddx, ddy)
                        min_d = P_RADIUS * 2
                        if 0 < dist < min_d:
                            push  = (min_d - dist) / 2
                            nx, ny = ddx / dist, ddy / dist
                            p.x  -= nx * push;  p.y  -= ny * push
                            o.x  += nx * push;  o.y  += ny * push

                state = {
                    "type":    "state",
                    "players": [self.players[pid].to_dict() for pid in pids],
                }

            self._broadcast(state)


# ══════════════════════════════════════════════════════════════════════════════
#  CLIENT
# ══════════════════════════════════════════════════════════════════════════════

class GameClient:
    def __init__(self, host: str):
        self.host         = host
        self.my_pid       = None
        self.players:  dict = {}
        self.lock         = threading.Lock()
        self.running      = True
        self._atk_pending = False   # True for one frame after SPACE pressed

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, PORT))
        except ConnectionRefusedError:
            print(f"Could not connect to {self.host}:{PORT}  —  is the server running?")
            sys.exit(1)

        print(f"Connected to {self.host}:{PORT}")
        threading.Thread(target=self._recv_loop, daemon=True).start()
        self._render_loop()

    # ── Network receive ────────────────────────────────────────────────────────

    def _recv_loop(self):
        lb = LineBuffer()
        while self.running:
            try:
                data = self.sock.recv(16384)
                if not data:
                    break
                for msg in lb.feed(data):
                    t = msg.get("type")
                    if t == "init":
                        self.my_pid = msg["pid"]
                        print(f"You are Player {self.my_pid}")
                    elif t == "state":
                        with self.lock:
                            self.players = {p["pid"]: p for p in msg["players"]}
            except OSError:
                break
        self.running = False

    def _send_input(self, dx: int, dy: int, attack: bool):
        try:
            send_msg(self.sock, {"type": "input", "dx": dx, "dy": dy, "attack": attack})
        except OSError:
            self.running = False

    # ── Rendering ──────────────────────────────────────────────────────────────

    def _render_loop(self):
        pygame.init()
        screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Knockback Arena")

        font_sm = pygame.font.SysFont("Arial", 16)
        font_md = pygame.font.SysFont("Arial", 20)
        font_lg = pygame.font.SysFont("Arial", 32, bold=True)
        clock   = pygame.time.Clock()

        atk_surface = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)

        while self.running:
            # ── Events ────────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_SPACE:
                        self._atk_pending = True

            keys = pygame.key.get_pressed()
            dx   = (keys[pygame.K_d] - keys[pygame.K_a])
            dy   = (keys[pygame.K_s] - keys[pygame.K_w])
            self._send_input(dx, dy, self._atk_pending)
            self._atk_pending = False

            # ── Draw background ────────────────────────────────────────────────
            screen.fill(BG_COLOR)

            # Arena floor
            pygame.draw.rect(screen, MAP_COLOR, (MAP_X, MAP_Y, MAP_SIZE, MAP_SIZE))

            # Grid lines (subtle)
            grid_step = MAP_SIZE // 6
            for i in range(1, 6):
                gx = MAP_X + i * grid_step
                gy = MAP_Y + i * grid_step
                pygame.draw.line(screen, (50, 52, 62),
                                 (gx, MAP_Y), (gx, MAP_Y + MAP_SIZE))
                pygame.draw.line(screen, (50, 52, 62),
                                 (MAP_X, gy), (MAP_X + MAP_SIZE, gy))

            # Arena border
            pygame.draw.rect(screen, MAP_BORDER,
                             (MAP_X, MAP_Y, MAP_SIZE, MAP_SIZE), 3)
            # Corner accents
            acc = 16
            for cx2, cy2, sx, sy in [
                (MAP_X,            MAP_Y,            1,  1),
                (MAP_X+MAP_SIZE,   MAP_Y,           -1,  1),
                (MAP_X,            MAP_Y+MAP_SIZE,   1, -1),
                (MAP_X+MAP_SIZE,   MAP_Y+MAP_SIZE,  -1, -1),
            ]:
                pygame.draw.line(screen, (230,235,255),
                                 (cx2, cy2), (cx2 + sx*acc, cy2), 3)
                pygame.draw.line(screen, (230,235,255),
                                 (cx2, cy2), (cx2, cy2 + sy*acc), 3)

            # ── Players ────────────────────────────────────────────────────────
            with self.lock:
                snap = dict(self.players)

            for pid, p in snap.items():
                px, py = int(p["x"]), int(p["y"])
                col    = tuple(p["color"])
                is_me  = (pid == self.my_pid)

                # Attack flash ring
                if p.get("flash"):
                    atk_surface.fill((0, 0, 0, 0))
                    pygame.draw.circle(atk_surface, (*col, 45),
                                       (px, py), KB_RADIUS)
                    screen.blit(atk_surface, (0, 0))
                    pygame.draw.circle(screen, col, (px, py), KB_RADIUS, 2)

                # Drop shadow
                pygame.draw.circle(screen, (10, 10, 15), (px+4, py+4), P_RADIUS)

                # Body
                pygame.draw.circle(screen, col, (px, py), P_RADIUS)

                # Shading (darker lower half)
                shade = pygame.Surface((P_RADIUS*2, P_RADIUS*2), pygame.SRCALPHA)
                pygame.draw.circle(shade, (0, 0, 0, 60),
                                   (P_RADIUS, P_RADIUS + 4), P_RADIUS)
                screen.blit(shade, (px - P_RADIUS, py - P_RADIUS))

                # Specular highlight
                pygame.draw.circle(screen, (255, 255, 255),
                                   (px - P_RADIUS//3, py - P_RADIUS//3),
                                   max(3, P_RADIUS // 4))

                # Outline — white & thicker for local player
                outline_col = (255, 255, 255) if is_me else (0, 0, 0)
                outline_w   = 3 if is_me else 1
                pygame.draw.circle(screen, outline_col, (px, py), P_RADIUS, outline_w)

                # Label
                label_str = f"P{pid}" + ("  ← you" if is_me else "")
                label     = font_sm.render(label_str, True,
                                           (255, 255, 255) if is_me else TEXT_COLOR)
                screen.blit(label, (px - label.get_width()//2, py - P_RADIUS - 22))

            # ── HUD ────────────────────────────────────────────────────────────
            title = font_lg.render("Knockback Arena", True, (210, 215, 255))
            screen.blit(title, (WIN_W//2 - title.get_width()//2, 14))

            player_count = font_md.render(
                f"{len(snap)} player{'s' if len(snap) != 1 else ''} online",
                True, HINT_COLOR)
            screen.blit(player_count, (WIN_W//2 - player_count.get_width()//2, 52))

            hint = font_sm.render(
                "WASD: move     SPACE: knockback     ESC: quit",
                True, HINT_COLOR)
            screen.blit(hint, (WIN_W//2 - hint.get_width()//2, WIN_H - 26))

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        self.running = False
        try:
            self.sock.close()
        except OSError:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Knockback Arena — top-down LAN multiplayer")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--server", action="store_true",
                       help="Host a game (no display needed)")
    group.add_argument("--join", metavar="HOST",
                       help="Join a game at HOST (e.g. 192.168.1.5)")
    args = parser.parse_args()

    if args.server:
        try:
            GameServer().start()
        except KeyboardInterrupt:
            print("\nServer stopped.")
    else:
        GameClient(args.join).start()


if __name__ == "__main__":
    main()
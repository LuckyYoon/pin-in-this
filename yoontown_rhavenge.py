#!/usr/bin/env python3
"""
LAN top-down obstacle survival game
- Server-authoritative
- UDP networking
- Players are circles, move with WASD
- No player-player collision
- Obstacles spawn from the top and move down
- Last alive wins
- Starts after 3 players join and a 5 second countdown
- Host is the first player to join; if host leaves, the next join order player becomes host
- Host can force the countdown with SPACE once at least 3 players are connected
- Dead players stay connected and keep spectating
- Server prints its LAN IP on startup
"""

from __future__ import annotations

import json
import math
import random
import socket
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pygame


HOST = "0.0.0.0"
PORT = 50007

W, H = 960, 640
FPS = 60

PLAYER_RADIUS = 12
PLAYER_SPEED = 300.0

SNAPSHOT_HZ = 30.0
INPUT_HZ = 30.0

MIN_PLAYERS = 1
COUNTDOWN_SECONDS = 3.0
INTERMISSION_SECONDS = 4.0
PLAYER_TIMEOUT = 20.0

# Client connection timeout (seconds before giving up)
JOIN_TIMEOUT = 15.0

# ── Interpolation ─────────────────────────────────────────────────────────────
# How far behind real-time the client renders.  100 ms works well on a LAN;
# raise to ~150 ms if you see occasional jumps on a worse network.
INTERP_DELAY: float = 0.033

# How long to keep snapshot history (seconds).  Must be > INTERP_DELAY.
SNAPSHOT_BUFFER_DURATION: float = 0.1
# ─────────────────────────────────────────────────────────────────────────────

BG = (16, 18, 24)
GRID = (28, 32, 42)
WHITE = (235, 240, 245)
MUTED = (160, 170, 185)
RED = (220, 80, 80)
GREEN = (90, 220, 120)
GOLD = (235, 205, 80)
BROWN = (145, 92, 40)
DARK = (34, 36, 42)


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def circle_rect_collision(cx: float, cy: float, r: float, rx: float, ry: float, rw: float, rh: float) -> bool:
    nx = clamp(cx, rx, rx + rw)
    ny = clamp(cy, ry, ry + rh)
    dx = cx - nx
    dy = cy - ny
    return dx * dx + dy * dy <= r * r


def build_segments_from_gaps(width: int, gaps: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Convert gap intervals into filled obstacle segments."""
    if not gaps:
        return [(0, width)]

    merged = []
    for x, w in sorted(gaps):
        x2 = x + w
        if not merged:
            merged.append([x, x2])
        else:
            if x <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], x2)
            else:
                merged.append([x, x2])

    segments = []
    cur = 0
    for x1, x2 in merged:
        if x1 > cur:
            segments.append((cur, x1 - cur))
        cur = max(cur, x2)
    if cur < width:
        segments.append((cur, width - cur))
    return [(x, w) for x, w in segments if w > 0]


@dataclass
class Player:
    pid: int
    name: str
    addr: Tuple[str, int]
    x: float = 0.0
    y: float = 0.0
    alive: bool = True
    input_mask: int = 0
    last_seen: float = field(default_factory=time.perf_counter)


@dataclass
class Obstacle:
    y: float
    h: int
    speed: float
    segments: List[Tuple[int, int]]


class GameServer:
    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.setblocking(False)

        self.players: Dict[int, Player] = {}
        self.addr_to_pid: Dict[Tuple[str, int], int] = {}
        self.join_order: List[int] = []
        self.next_pid = 1

        self.host_pid: Optional[int] = None

        self.phase = "lobby"
        self.countdown = 0.0
        self.intermission = 0.0
        self.requested_start = False

        self.round = 1
        self.round_time = 0.0
        self.spawn_timer = 0.0
        self.obstacles: List[Obstacle] = []
        self.winner_pid: Optional[int] = None

        self.last_snapshot = 0.0
        self.rng = random.Random()

    def run(self):
        local_ip = get_local_ip()
        print(f"Server listening on UDP port {self.port}")
        print(f"LAN IP: {local_ip}:{self.port}")
        print("Players should connect to that IP on the same network.")
        print("Waiting for players...")

        # Pure Python game loop — no pygame display needed on the server.
        target_dt = 1.0 / 120.0
        last_time = time.perf_counter()

        while True:
            loop_start = time.perf_counter()
            dt = loop_start - last_time
            last_time = loop_start

            self._receive_packets()
            self._drop_timed_out_players(loop_start)
            self._update_game(dt)
            self._send_snapshots(loop_start)

            elapsed = time.perf_counter() - loop_start
            sleep_time = target_dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _receive_packets(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(8192)
            except BlockingIOError:
                break
            except OSError:
                break

            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue

            mtype = msg.get("t")
            if mtype == "j":
                self._handle_join(addr, str(msg.get("n", "")).strip())
            elif mtype == "i":
                pid = self.addr_to_pid.get(addr)
                if pid and pid in self.players:
                    p = self.players[pid]
                    p.input_mask = int(msg.get("m", 0))
                    p.last_seen = time.perf_counter()
            elif mtype == "hs":
                pid = self.addr_to_pid.get(addr)
                print(f"hs received from pid={pid}, host_pid={self.host_pid}, phase={self.phase}, players={len(self.players)}")
                if pid == self.host_pid and len(self.players) >= MIN_PLAYERS:
                    self.requested_start = True
                    if self.phase == "countdown":
                        self.countdown = min(self.countdown, 1.0)
            elif mtype == "p":
                pid = self.addr_to_pid.get(addr)
                if pid and pid in self.players:
                    self.players[pid].last_seen = time.perf_counter()

    def _handle_join(self, addr, name: str):
        if not name:
            return

        existing = self.addr_to_pid.get(addr)
        if existing and existing in self.players:
            p = self.players[existing]
            p.name = name[:16]
            p.last_seen = time.perf_counter()
            self._send_welcome(addr, existing)
            return

        pid = self.next_pid
        self.next_pid += 1

        p = Player(pid=pid, name=name[:16], addr=addr, last_seen=time.perf_counter())

        # Players joining while a match is already running become spectators
        # so they don't spawn at (0, 0) and immediately die / end the round.
        if self.phase in ("playing", "countdown", "finished"):
            p.alive = False

        self.players[pid] = p
        self.addr_to_pid[addr] = pid
        self.join_order.append(pid)

        if self.host_pid is None:
            self.host_pid = pid

        self._send_welcome(addr, pid)
        print(f"Joined: {name} [{addr[0]}:{addr[1]}] pid={pid}")

    def _send_welcome(self, addr, pid: int):
        payload = {"t": "w", "id": pid, "h": self.host_pid}
        self._safe_send(addr, payload)

    def _drop_timed_out_players(self, now: float):
        to_remove = [pid for pid, p in self.players.items() if now - p.last_seen > PLAYER_TIMEOUT]
        for pid in to_remove:
            self._remove_player(pid, reason="timeout")

    def _remove_player(self, pid: int, reason: str = "left"):
        p = self.players.pop(pid, None)
        if not p:
            return
        self.addr_to_pid.pop(p.addr, None)
        if pid in self.join_order:
            self.join_order.remove(pid)

        print(f"Removed pid={pid} ({p.name}) reason={reason}")

        if self.host_pid == pid:
            self.host_pid = self._choose_new_host()

        if self.phase == "countdown" and len(self.players) < MIN_PLAYERS:
            self.phase = "lobby"
            self.countdown = 0.0
            self.requested_start = False

        if not self.players:
            self._reset_match_state()

    def _choose_new_host(self) -> Optional[int]:
        for pid in self.join_order:
            if pid in self.players:
                return pid
        return None

    def _reset_match_state(self):
        self.phase = "lobby"
        self.countdown = 0.0
        self.intermission = 0.0
        self.requested_start = False
        self.round = 1
        self.round_time = 0.0
        self.spawn_timer = 0.0
        self.obstacles.clear()
        self.winner_pid = None
        for p in self.players.values():
            p.alive = True
            p.input_mask = 0

    def _spawn_positions(self) -> List[Tuple[float, float]]:
        n = max(1, len(self.players))
        xs = [W * (i + 1) / (n + 1) for i in range(n)]
        ys = [H - 80.0 for _ in range(n)]
        return list(zip(xs, ys))

    def _start_match(self):
        self.phase = "playing"
        self.countdown = 0.0
        self.intermission = 0.0
        self.round = 1
        self.round_time = 0.0
        self.spawn_timer = 0.7
        self.obstacles.clear()
        self.winner_pid = None

        spawn_points = self._spawn_positions()
        for (pid, p), (x, y) in zip(self.players.items(), spawn_points):
            p.alive = True
            p.x = x
            p.y = y

    def _round_duration(self) -> float:
        return clamp(14.0 - (self.round - 1) * 0.55, 8.0, 14.0)

    def _spawn_interval(self) -> float:
        base = clamp(1.5 - (self.round - 1) * 0.2, 0.8, 1.5)
        return base + self.rng.uniform(0.05, 0.15)

    def _obstacle_speed(self) -> float:
        return 150.0 + (self.round - 1) * 5.0

    def _obstacle_height(self) -> int:
        return int(clamp(72 - (self.round - 1) * 2.0, 30, 72))

    def _make_obstacle(self) -> Obstacle:
        h = self._obstacle_height()
        speed = self._obstacle_speed()

        pattern = self.rng.choices(
            ["single", "double", "offset", "triple"],
            weights=[
                max(1, 7 - self.round // 3),
                max(1, 3 + self.round // 4),
                max(1, 3 + self.round // 5),
                max(1, self.round // 6),
            ],
            k=1,
        )[0]

        min_gap = int(clamp(220 - (self.round - 1) * 10, 70, 220))
        if pattern == "single":
            gap_w = min_gap
            x = self.rng.randint(30, W - 30 - gap_w)
            gaps = [(x, gap_w)]
        elif pattern == "double":
            gap_w = max(55, min_gap // 2)
            left = self.rng.randint(20, W // 2 - gap_w - 20)
            right = self.rng.randint(W // 2 + 20, W - 20 - gap_w)
            gaps = [(left, gap_w), (right, gap_w)]
        elif pattern == "offset":
            gap_w = int(min_gap * 1.15)
            bias = self.rng.random() ** 1.8
            x = int((W - 60 - gap_w) * bias) + 30
            gaps = [(clamp(x, 30, W - 30 - gap_w), gap_w)]
        else:
            gap_w = max(48, min_gap // 3)
            xs = sorted([
                self.rng.randint(20, W // 3 - gap_w - 10),
                self.rng.randint(W // 3, 2 * W // 3 - gap_w),
                self.rng.randint(2 * W // 3, W - 20 - gap_w),
            ])
            gaps = [(x, gap_w) for x in xs]

        segments = build_segments_from_gaps(W, gaps)
        return Obstacle(y=-h, h=h, speed=speed, segments=segments)

    def _update_player_movement(self, dt: float):
        for p in self.players.values():
            if not p.alive:
                continue

            dx = dy = 0.0
            m = p.input_mask

            if m & 1:
                dy -= 1.0
            if m & 4:
                dy += 1.0
            if m & 2:
                dx -= 1.0
            if m & 8:
                dx += 1.0

            if dx != 0.0 or dy != 0.0:
                length = math.hypot(dx, dy)
                dx /= length
                dy /= length
                p.x += dx * PLAYER_SPEED * dt
                p.y += dy * PLAYER_SPEED * dt

            p.x = clamp(p.x, PLAYER_RADIUS, W - PLAYER_RADIUS)
            p.y = clamp(p.y, PLAYER_RADIUS, H - PLAYER_RADIUS)

    def _update_game(self, dt: float):
        self._update_player_movement(dt)

        if self.phase == "lobby":
            if self.requested_start and len(self.players) >= MIN_PLAYERS:
                self.phase = "countdown"
                self.countdown = COUNTDOWN_SECONDS

        elif self.phase == "countdown":
            self.countdown -= dt
            if self.countdown <= 0:
                if len(self.players) >= MIN_PLAYERS:
                    self._start_match()
                else:
                    self.phase = "lobby"
                    self.countdown = 0.0
                    self.requested_start = False

        elif self.phase == "playing":
            self.round_time += dt
            if self.round_time >= self._round_duration():
                self.round += 1
                self.round_time = 0.0

            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer += self._spawn_interval()
                self.obstacles.append(self._make_obstacle())

            for obs in self.obstacles:
                obs.y += obs.speed * dt
            self.obstacles = [o for o in self.obstacles if o.y < H + o.h + 20]

            for p in self.players.values():
                if not p.alive:
                    continue
                hit = False
                for obs in self.obstacles:
                    oy = obs.y
                    oh = obs.h
                    if p.y + PLAYER_RADIUS < oy or p.y - PLAYER_RADIUS > oy + oh:
                        continue
                    for sx, sw in obs.segments:
                        if circle_rect_collision(p.x, p.y, PLAYER_RADIUS, sx, oy, sw, oh):
                            hit = True
                            break
                    if hit:
                        break
                if hit:
                    p.alive = False

            alive_ids = [pid for pid, p in self.players.items() if p.alive]
            if len(alive_ids) <= 1 and len(self.players) > 0:
                self.phase = "finished"
                self.intermission = INTERMISSION_SECONDS
                self.winner_pid = alive_ids[0] if alive_ids else None

        elif self.phase == "finished":
            self.intermission -= dt
            if self.intermission <= 0:
                self._reset_match_state()
                if len(self.players) >= MIN_PLAYERS:
                    self.phase = "countdown"
                    self.countdown = COUNTDOWN_SECONDS

    def _state_payload(self):
        players = []
        for pid, p in self.players.items():
            players.append([pid, p.name, round(p.x, 2), round(p.y, 2), 1 if p.alive else 0])

        obstacles = []
        for o in self.obstacles:
            obstacles.append([round(o.y, 2), o.h, round(o.speed, 2), o.segments])

        return {
            "t": "s",
            "ph": self.phase,
            "c": round(self.countdown, 2),
            "i": round(self.intermission, 2),
            "r": self.round,
            "h": self.host_pid,
            "w": self.winner_pid,
            "n": len(self.players),
            "p": players,
            "o": obstacles,
        }

    def _send_snapshots(self, now: float):
        if now - self.last_snapshot < 1.0 / SNAPSHOT_HZ:
            return
        self.last_snapshot = now

        # Build the shared base payload once, then personalise it per player
        # by injecting "my_id". This lets the client learn its PID from a
        # snapshot even if the dedicated welcome packet was dropped (UDP).
        base = self._state_payload()
        base_json = json.dumps(base, separators=(",", ":"))

        for pid, p in self.players.items():
            # Insert my_id just before the closing brace — cheaper than
            # rebuilding the whole dict for every player.
            personalised = base_json[:-1] + f',"my_id":{pid}}}'
            try:
                self.sock.sendto(personalised.encode("utf-8"), p.addr)
            except OSError:
                pass

    def _safe_send(self, addr, payload):
        try:
            self.sock.sendto(json.dumps(payload, separators=(",", ":")).encode("utf-8"), addr)
        except OSError:
            pass


# ── Snapshot buffer entry ─────────────────────────────────────────────────────
# Each entry is (local_recv_time: float, state: dict).
# We keep SNAPSHOT_BUFFER_DURATION seconds of history so the interpolator
# always has at least two bracketing frames to work with.
# ─────────────────────────────────────────────────────────────────────────────


class GameClient:
    def __init__(self, server_ip: str, port: int, name: str):
        self.server_addr = (server_ip, port)
        self.name = name[:16]

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)

        self.my_pid: Optional[int] = None
        self.host_pid: Optional[int] = None
        self.state = None

        self.last_join = 0.0
        self.last_input = 0.0
        self.last_ping = 0.0
        self.current_mask = 0
        self.key_mask = 0

        self.colors = {}

        # ── Interpolation buffer ──────────────────────────────────────────────
        # List of (recv_time, state_dict) tuples, oldest first.
        self.snapshot_buffer: List[Tuple[float, dict]] = []
        # ─────────────────────────────────────────────────────────────────────

        pygame.init()
        pygame.display.set_caption("Hole LAN")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(None, 24)
        self.small = pygame.font.SysFont(None, 18)
        self.big = pygame.font.SysFont(None, 40)

    # ── Interpolation helpers ─────────────────────────────────────────────────

    def _interpolated_players(self, render_time: float) -> List:
        """
        Return a player list with x/y lerped to render_time.

        We scan the snapshot buffer for the two consecutive entries that
        bracket render_time, then linearly interpolate each player's position.
        If render_time is outside the buffer we fall back to the nearest edge.
        """
        buf = self.snapshot_buffer
        if not buf:
            return []

        # Not enough history yet — use the oldest snapshot as-is.
        if render_time <= buf[0][0]:
            return buf[0][1].get("p", [])

        # render_time is ahead of all snapshots (very unlikely on a LAN, but
        # possible at startup).  Return the latest snapshot without extrapolation
        # to avoid wild position predictions.
        if render_time >= buf[-1][0]:
            return buf[-1][1].get("p", [])

        # Find the bracketing pair (t0 <= render_time < t1).
        for i in range(len(buf) - 1):
            t0, s0 = buf[i]
            t1, s1 = buf[i + 1]
            if t0 <= render_time <= t1:
                span = t1 - t0
                alpha = (render_time - t0) / span if span > 0.0 else 1.0

                # Index the older snapshot by player-id for O(1) lookup.
                prev: Dict[int, list] = {e[0]: e for e in s0.get("p", [])}

                result = []
                for entry in s1.get("p", []):
                    pid, pname, x1, y1, alive = entry
                    if pid in prev:
                        _, _, x0, y0, _ = prev[pid]
                        # Lerp position; keep the latest alive flag so deaths
                        # are reflected immediately rather than being delayed.
                        x = x0 + (x1 - x0) * alpha
                        y = y0 + (y1 - y0) * alpha
                        result.append([pid, pname, x, y, alive])
                    else:
                        # Player just joined — no previous sample; use as-is.
                        result.append(entry)
                return result

        # Should be unreachable, but be safe.
        return buf[-1][1].get("p", [])

    def _dead_reckoned_obstacles(self, now: float) -> List:
        """
        Return an obstacle list with y positions extrapolated forward from the
        latest snapshot by (now - recv_time) * speed.

        Obstacles move at a perfectly constant speed set by the server, so
        extrapolation is exact — there is no error accumulation.  This avoids
        the pop-in / pop-out artefact you would get if you tried to interpolate
        obstacles that might appear or disappear between snapshots.
        """
        if not self.snapshot_buffer:
            return []

        recv_time, latest = self.snapshot_buffer[-1]
        dt = max(0.0, now - recv_time)   # never go backwards

        result = []
        for oy, oh, speed, segments in latest.get("o", []):
            result.append([oy + speed * dt, oh, speed, segments])
        return result

    # ─────────────────────────────────────────────────────────────────────────

    def run(self):
        join_deadline = time.perf_counter() + JOIN_TIMEOUT
        running = True

        while running and self.my_pid is None:
            now = time.perf_counter()

            # Bail out with an informative screen if the server never replies.
            if now > join_deadline:
                self._draw_error(
                    f"No response from {self.server_addr[0]}:{self.server_addr[1]}",
                    "Check that the server is running and the IP is correct.",
                )
                pygame.time.wait(4000)
                pygame.quit()
                return

            self._pump_network(join_phase=True)
            self._send_join()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self._draw_connecting(time_left=int(join_deadline - now))
            self.clock.tick(FPS)

        if self.my_pid is None:
            pygame.quit()
            return

        running = True
        while running:
            self.clock.tick(FPS)
            self._pump_network(join_phase=False)
            self._handle_events()
            self._send_input()
            self._draw()
        pygame.quit()

    def _send_join(self):
        now = time.perf_counter()
        if now - self.last_join >= 0.35:
            self.last_join = now
            msg = {"t": "j", "n": self.name}
            self._safe_send(msg)

    def _send_input(self, force: bool = False):
        now = time.perf_counter()

        # Send immediately when the key state changes, otherwise keep
        # refreshing at INPUT_HZ so the server knows you are still alive.
        if not force and now - self.last_input < 1.0 / INPUT_HZ:
            return

        self.last_input = now
        self.current_mask = self.key_mask
        self._safe_send({"t": "i", "m": self.current_mask})

    def _safe_send(self, payload):
        try:
            self.sock.sendto(json.dumps(payload, separators=(",", ":")).encode("utf-8"), self.server_addr)
        except OSError:
            pass

    def _pump_network(self, join_phase: bool):
        while True:
            try:
                data, _ = self.sock.recvfrom(8192)
            except BlockingIOError:
                break
            except OSError:
                break

            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue

            t = msg.get("t")
            if t == "w":
                # Dedicated welcome packet — always trust it.
                self.my_pid = int(msg["id"])
                self.host_pid = msg.get("h")
            elif t == "s":
                self.state = msg
                self.host_pid = msg.get("h")
                # Snapshots carry "my_id" so the client learns its PID even
                # when the welcome packet was lost in transit.
                if self.my_pid is None:
                    my_id = msg.get("my_id")
                    if my_id is not None:
                        self.my_pid = int(my_id)

                # ── Push into interpolation buffer ────────────────────────
                recv_time = time.perf_counter()
                self.snapshot_buffer.append((recv_time, msg))

                # Prune entries older than SNAPSHOT_BUFFER_DURATION seconds.
                cutoff = recv_time - SNAPSHOT_BUFFER_DURATION
                # Keep at least one entry so _interpolated_players always has
                # something to fall back to.
                while len(self.snapshot_buffer) > 1 and self.snapshot_buffer[0][0] < cutoff:
                    self.snapshot_buffer.pop(0)
                # ─────────────────────────────────────────────────────────

    def _handle_events(self):
        changed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                elif event.key == pygame.K_w:
                    self.key_mask |= 1
                    changed = True
                elif event.key == pygame.K_a:
                    self.key_mask |= 2
                    changed = True
                elif event.key == pygame.K_s:
                    self.key_mask |= 4
                    changed = True
                elif event.key == pygame.K_d:
                    self.key_mask |= 8
                    changed = True
                elif event.key == pygame.K_SPACE:
                    self._safe_send({"t": "hs"})

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_w:
                    self.key_mask &= ~1
                    changed = True
                elif event.key == pygame.K_a:
                    self.key_mask &= ~2
                    changed = True
                elif event.key == pygame.K_s:
                    self.key_mask &= ~4
                    changed = True
                elif event.key == pygame.K_d:
                    self.key_mask &= ~8
                    changed = True

        if changed:
            self._send_input(force=True)

    def _player_color(self, pid: int):
        if pid not in self.colors:
            rng = random.Random(pid * 1337)
            self.colors[pid] = (
                80 + rng.randint(0, 150),
                80 + rng.randint(0, 150),
                80 + rng.randint(0, 150),
            )
        return self.colors[pid]

    def _draw_connecting(self, time_left: int = JOIN_TIMEOUT):
        self.screen.fill(BG)
        title = self.big.render("Connecting to server...", True, WHITE)
        name_surf = self.font.render(f"Name: {self.name}   Server: {self.server_addr[0]}:{self.server_addr[1]}", True, MUTED)
        sub = self.small.render(f"Waiting for welcome packet...  (timeout in {time_left}s)", True, MUTED)
        self.screen.blit(title, title.get_rect(center=(W // 2, H // 2 - 25)))
        self.screen.blit(name_surf, name_surf.get_rect(center=(W // 2, H // 2 + 18)))
        self.screen.blit(sub, sub.get_rect(center=(W // 2, H // 2 + 48)))
        pygame.display.flip()

    def _draw_error(self, line1: str, line2: str = ""):
        self.screen.fill(BG)
        t1 = self.big.render("Connection failed", True, RED)
        t2 = self.font.render(line1, True, WHITE)
        t3 = self.small.render(line2, True, MUTED) if line2 else None
        self.screen.blit(t1, t1.get_rect(center=(W // 2, H // 2 - 40)))
        self.screen.blit(t2, t2.get_rect(center=(W // 2, H // 2 + 4)))
        if t3:
            self.screen.blit(t3, t3.get_rect(center=(W // 2, H // 2 + 36)))
        pygame.display.flip()

    def _draw_grid(self):
        for x in range(0, W, 40):
            pygame.draw.line(self.screen, GRID, (x, 0), (x, H))
        for y in range(0, H, 40):
            pygame.draw.line(self.screen, GRID, (0, y), (W, y))

    def _draw(self):
        self.screen.fill(BG)
        self._draw_grid()

        if not self.state:
            msg = self.font.render("Waiting for game state...", True, WHITE)
            self.screen.blit(msg, (20, 20))
            pygame.display.flip()
            return

        now = time.perf_counter()

        # ── Interpolated / dead-reckoned scene data ───────────────────────────
        render_time = now - INTERP_DELAY
        players = self._interpolated_players(render_time)
        obstacles = self._dead_reckoned_obstacles(now)
        # ─────────────────────────────────────────────────────────────────────

        for oy, oh, _speed, segments in obstacles:
            for sx, sw in segments:
                pygame.draw.rect(self.screen, BROWN, pygame.Rect(int(sx), int(oy), int(sw), int(oh)))

        for pid, name, x, y, alive in players:
            color = self._player_color(pid) if alive else (110, 110, 120)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), PLAYER_RADIUS)
            pygame.draw.circle(self.screen, DARK, (int(x), int(y)), PLAYER_RADIUS, 2)

            label = name + (" [HOST]" if pid == self.host_pid else "") + (" [DEAD]" if not alive else "")
            text = self.small.render(label, True, WHITE if alive else MUTED)
            rect = text.get_rect(midbottom=(int(x), int(y) - PLAYER_RADIUS - 4))
            self.screen.blit(text, rect)

        ph = self.state.get("ph")
        round_n = self.state.get("r", 1)
        count = len(players)
        alive_count = sum(1 for _, _, _, _, a in players if a)

        hud1 = self.font.render(f"Round {round_n}   Players: {count}   Alive: {alive_count}", True, WHITE)
        self.screen.blit(hud1, (16, 14))

        if self.my_pid == self.host_pid:
            hud2 = self.small.render("You are host. Press SPACE to force the countdown.", True, GOLD)
            self.screen.blit(hud2, (16, 40))
        else:
            host_name = ""
            for pid, name, *_ in players:
                if pid == self.host_pid:
                    host_name = name
                    break
            hud2 = self.small.render(f"Host: {host_name}", True, MUTED)
            self.screen.blit(hud2, (16, 40))

        if ph == "lobby":
            text = self.big.render("Waiting for 3 players", True, WHITE)
            self.screen.blit(text, text.get_rect(center=(W // 2, 70)))
        elif ph == "countdown":
            c = self.state.get("c", COUNTDOWN_SECONDS)
            text = self.big.render(f"Starting in {max(0, math.ceil(c))}", True, GOLD)
            self.screen.blit(text, text.get_rect(center=(W // 2, 70)))
        elif ph == "finished":
            winner = self.state.get("w")
            winner_name = "Nobody survived"
            for pid, name, *_ in players:
                if pid == winner:
                    winner_name = f"{name} wins!"
                    break
            text = self.big.render(winner_name, True, GREEN if winner is not None else RED)
            self.screen.blit(text, text.get_rect(center=(W // 2, 70)))
            sub = self.small.render("New round soon...", True, MUTED)
            self.screen.blit(sub, sub.get_rect(center=(W // 2, 108)))

        pygame.display.flip()


def ask_for_name() -> str:
    while True:
        name = input("Enter your name: ").strip()
        if name:
            return name[:16]


def ask_for_server() -> str:
    ip = input("Server IP [127.0.0.1]: ").strip()
    return ip or "127.0.0.1"


def run_server():
    # Server runs as a plain Python loop — no pygame display required.
    # This means it works fine over SSH or in any headless environment.
    GameServer().run()


def run_client(server_ip: str):
    name = ask_for_name()
    client = GameClient(server_ip, PORT, name)
    client.run()


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python yoontown_rhavenge.py server")
        print("  python yoontown_rhavenge.py client [server_ip]")
        return

    mode = sys.argv[1].lower()
    if mode == "server":
        run_server()
    elif mode == "client":
        server_ip = sys.argv[2] if len(sys.argv) >= 3 else ask_for_server()
        run_client(server_ip)
    else:
        print("Unknown mode. Use 'server' or 'client'.")


if __name__ == "__main__":
    main()
import pytest
from collections import defaultdict
from unittest.mock import patch
import pygame

from zclasses import delay, Controller, Player


# ── Helpers ───────────────────────────────────────────────────────────────────

# Map friendly names → real pygame integer constants so we never patch the
# constants themselves (they must stay as ints for subscript access to work).
_KEY_MAP = {
    "K_a": pygame.K_a,
    "K_d": pygame.K_d,
    "K_w": pygame.K_w,
    "K_s": pygame.K_s,
}

def make_key_state(pressed_key_names):
    """
    Return a defaultdict(bool) that mimics pygame.key.get_pressed().
    Keys listed in *pressed_key_names* (e.g. {"K_a", "K_w"}) map to True;
    everything else defaults to False.  Supports integer subscript access.
    """
    state = defaultdict(bool)
    for name in pressed_key_names:
        state[_KEY_MAP[name]] = True
    return state


# ═════════════════════════════════════════════════════════════════════════════
# Tests for delay()
# ═════════════════════════════════════════════════════════════════════════════

class TestDelay:
    """Tests for the delay(timers, key, ms) function."""

    @patch("pygame.time.get_ticks", return_value=1000)
    def test_new_key_registers_and_returns_false(self, mock_ticks):
        """First call with an unseen key must store it and return False."""
        timers = {}
        result = delay(timers, "shoot", 500)

        assert result is False
        assert "shoot" in timers
        assert timers["shoot"] == 1000

    @patch("pygame.time.get_ticks", return_value=1000)
    def test_new_key_does_not_fire_immediately(self, mock_ticks):
        """Even if ms=0, a brand-new key should not fire on the first call."""
        timers = {}
        result = delay(timers, "shoot", 0)

        assert result is False

    @patch("pygame.time.get_ticks", return_value=1600)
    def test_returns_true_when_interval_elapsed(self, mock_ticks):
        """Should return True when enough time has passed since the last tick."""
        timers = {"shoot": 1000}
        result = delay(timers, "shoot", 500)

        assert result is True

    @patch("pygame.time.get_ticks", return_value=1499)
    def test_returns_false_when_interval_not_elapsed(self, mock_ticks):
        """Should return False when the interval has not yet elapsed."""
        timers = {"shoot": 1000}
        result = delay(timers, "shoot", 500)

        assert result is False

    @patch("pygame.time.get_ticks", return_value=1500)
    def test_returns_true_exactly_at_boundary(self, mock_ticks):
        """Should fire exactly when elapsed time equals ms (boundary condition)."""
        timers = {"shoot": 1000}
        result = delay(timers, "shoot", 500)

        assert result is True

    @patch("pygame.time.get_ticks", return_value=1600)
    def test_resets_timer_after_firing(self, mock_ticks):
        """After returning True the stored timestamp must be updated."""
        timers = {"shoot": 1000}
        delay(timers, "shoot", 500)

        assert timers["shoot"] == 1600

    @patch("pygame.time.get_ticks", return_value=1499)
    def test_does_not_reset_timer_when_not_fired(self, mock_ticks):
        """Timer value must stay unchanged when the interval has not elapsed."""
        timers = {"shoot": 1000}
        delay(timers, "shoot", 500)

        assert timers["shoot"] == 1000

    @patch("pygame.time.get_ticks", return_value=2000)
    def test_multiple_keys_are_independent(self, mock_ticks):
        """Each key in the timers dict is tracked independently."""
        timers = {"shoot": 1000, "dash": 1800}

        assert delay(timers, "shoot", 500) is True   # 2000-1000 >= 500
        assert delay(timers, "dash",  500) is False  # 2000-1800 < 500

    @patch("pygame.time.get_ticks", return_value=1000)
    def test_empty_string_key(self, mock_ticks):
        """An empty string is a valid dict key and should behave correctly."""
        timers = {}
        result = delay(timers, "", 200)

        assert result is False
        assert "" in timers

    @patch("pygame.time.get_ticks", return_value=1000)
    def test_zero_ms_fires_on_second_call(self, mock_ticks):
        """With ms=0 any non-negative elapsed time should trigger on the next call."""
        timers = {"shoot": 999}   # elapsed = 1000-999 = 1 >= 0
        result = delay(timers, "shoot", 0)

        assert result is True


# ═════════════════════════════════════════════════════════════════════════════
# Tests for Controller.move()
# ═════════════════════════════════════════════════════════════════════════════

class TestControllerMove:
    """Tests for Controller.move(player) using the real Player class."""

    def _patched_move(self, controller, player, pressed_key_names):
        """
        Run controller.move() with only the keys in *pressed_key_names* held.
        get_pressed() is patched with a subscriptable defaultdict(bool) keyed
        by the real pygame integer constants, so keys[pygame.K_a] works correctly.
        """
        key_state = make_key_state(pressed_key_names)
        with patch("pygame.key.get_pressed", return_value=key_state):
            controller.phase2 = lambda: None   # stub undefined method
            controller.move(player)

    # ── Player default values ─────────────────────────────────────────────────

    def test_player_default_attributes(self):
        """Player.__init__ sets the expected defaults."""
        player = Player(10, 20)

        assert player.x                == 10
        assert player.y                == 20
        assert player.hp               == 100
        assert player.size             == 8
        assert player.movespeed        == 4
        assert player.alive            is True
        assert player.immune           is False
        assert player.immune_start_time == 0

    # ── directional keys ─────────────────────────────────────────────────────

    def test_move_left_decreases_x(self):
        player = Player(100, 50)
        self._patched_move(Controller(), player, {"K_a"})

        assert player.x == 100 - player.movespeed  # 96

    def test_move_right_increases_x(self):
        player = Player(100, 50)
        self._patched_move(Controller(), player, {"K_d"})

        assert player.x == 100 + player.movespeed  # 104

    def test_move_up_decreases_y(self):
        player = Player(50, 100)
        self._patched_move(Controller(), player, {"K_w"})

        assert player.y == 100 - player.movespeed  # 96

    def test_move_down_increases_y(self):
        player = Player(50, 100)
        self._patched_move(Controller(), player, {"K_s"})

        assert player.y == 100 + player.movespeed  # 104

    # ── no keys pressed ───────────────────────────────────────────────────────

    def test_no_keys_pressed_does_not_change_position(self):
        player = Player(50, 50)
        self._patched_move(Controller(), player, set())

        assert player.x == 50
        assert player.y == 50

    # ── diagonal movement (two keys at once) ──────────────────────────────────

    def test_diagonal_up_right(self):
        player = Player(100, 100)
        self._patched_move(Controller(), player, {"K_w", "K_d"})

        assert player.x == 100 + player.movespeed
        assert player.y == 100 - player.movespeed

    def test_diagonal_down_left(self):
        player = Player(100, 100)
        self._patched_move(Controller(), player, {"K_s", "K_a"})

        assert player.x == 100 - player.movespeed
        assert player.y == 100 + player.movespeed

    # ── movespeed is respected ────────────────────────────────────────────────

    def test_movespeed_value_applied_correctly(self):
        """Player.movespeed (default 4) drives the step size."""
        player = Player(0, 0)
        assert player.movespeed == 4

        self._patched_move(Controller(), player, {"K_d"})
        assert player.x == 4

    # ── controller initial state ──────────────────────────────────────────────

    def test_controller_initial_phase_is_false(self):
        assert Controller().phase is False
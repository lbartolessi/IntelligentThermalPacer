"""
tests/test_thermal_pacer.py

Unit and integration test suite for the IntelligentThermalPacer package.
Implements the MockTelemetryProvider and verifies transitions of
SCALE_DOWN, SCALE_UP, and HOLD according to Section 8 of the spec.

Uses Python's standard unittest library to ensure zero external dependency
requirements for running the test suite.
"""

import json
import os
import shutil
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from thermal_pacer.client import ThermalGuard
from thermal_pacer.daemon import (
    DaemonConfig,
    DaemonState,
    TelemetryPoint,
    TelemetryProvider,
    ThermalDaemonEngine,
    compute_guidance,
)

# Guard the original system sleep function to avoid recursion when patching time.sleep
original_sleep = time.sleep

# Prevent the daemon's graceful shutdown from ever terminating the test runner process.
# Since the daemon runs in a background thread and shuts down asynchronously, patching
# os._exit at the module level ensures it remains disabled for the entire process lifetime.
import thermal_pacer.daemon
thermal_pacer.daemon.os._exit = lambda status: None


# ---------------------------------------------------------------------------
# MockTelemetryProvider (§8-2)
# ---------------------------------------------------------------------------

class MockTelemetryProvider(TelemetryProvider):
    """
    Mock telemetry provider implementing the TelemetryProvider protocol.
    Provides temperature values dynamically based on the virtual time elapsed.
    This makes testing multithreaded daemon updates 100% deterministic and
    immune to the exact execution speed of the thread loop.
    """

    def __init__(self, start_time: float, get_virtual_time_func, max_target_temp: float = 62.0) -> None:
        self.start_time = start_time
        self.max_target_temp = max_target_temp
        self.get_virtual_time = get_virtual_time_func

    def get_critical_temperature(self) -> float:
        now = self.get_virtual_time()
        elapsed = now - self.start_time

        # 1. Warm-up (0 to 180s): stable 50.0 °C
        if elapsed <= 180.0:
            return 50.0
        # 2. Rising phase (180 to 330s): climbs from 50.0 to 59.0 °C
        elif elapsed <= 330.0:
            # Rise of 9 °C over 150 seconds = 3.6 °C/minute (> 0.5 °C/min)
            pct = (elapsed - 180.0) / 150.0
            return 50.0 + pct * 9.0
        # 3. Cooling phase (330s onwards): falls from 59.0 down to 48.0 °C over 220s
        else:
            pct = min(1.0, (elapsed - 330.0) / 220.0)
            return 59.0 - pct * 11.0


# ---------------------------------------------------------------------------
# Unit and Integration Test Suite
# ---------------------------------------------------------------------------

class TestThermalPacer(unittest.TestCase):

    def test_warmup_guard(self):
        """If elapsed time < trend_analysis_window_seconds, get_guidance must return HOLD."""
        config = DaemonConfig(
            trend_analysis_window_seconds=180,
            safety_margin_celsius=5.0,
            max_target_temp=62.0,
        )
        state = DaemonState(config=config)
        state.start_time = time.monotonic() - 100.0  # Only 100s elapsed (< 180s)

        # Populate queue with some points
        now = time.monotonic()
        for i in range(180):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=50.0)
            )

        # Even with warm/stable temps, warmup guard should force HOLD
        self.assertEqual(compute_guidance(state), "HOLD")

    def test_scale_down_rising_trend(self):
        """
        SCALE_DOWN triggers if T_avg(Current) > T_avg(Previous) > T_avg(Prior)
        with upward trend delta > 0.5 °C/min.
        """
        config = DaemonConfig(
            trend_analysis_window_seconds=180,
            safety_margin_celsius=5.0,
            max_target_temp=62.0,
            emit_warnings=False,
        )
        state = DaemonState(config=config)
        state.start_time = time.monotonic() - 300.0  # Warmed up

        now = time.monotonic()
        # Prior segment
        for i in range(120, 180):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=50.0)
            )
        # Previous segment
        for i in range(60, 120):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=51.0)
            )
        # Current segment
        for i in range(0, 60):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=52.5)
            )

        self.assertEqual(compute_guidance(state), "SCALE_DOWN")

    def test_scale_down_high_throttling_ratio(self):
        """SCALE_DOWN triggers if Re(Current) > 0.40."""
        config = DaemonConfig(
            trend_analysis_window_seconds=180,
            safety_margin_celsius=5.0,
            max_target_temp=62.0,
            emit_warnings=False,
        )
        state = DaemonState(config=config)
        state.start_time = time.monotonic() - 300.0  # Warmed up

        now = time.monotonic()
        # Prior & Previous segments: stable temps
        for i in range(60, 180):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=50.0)
            )

        # Current segment: Re > 0.40
        for i in range(0, 60):
            state.telemetry_queue.append(
                TelemetryPoint(
                    timestamp=now - i,
                    temperature=50.0,
                    pace_calls=5,
                    pace_waits=3,  # Re = 0.60
                )
            )

        self.assertEqual(compute_guidance(state), "SCALE_DOWN")

    def test_scale_up_nominal_conditions(self):
        """
        SCALE_UP triggers only if:
          - All temps in the window are < max_target_temp - safety_margin_celsius
          - Flat or decreasing slope (T_cur <= T_pri)
          - Throttling ratio Re == 0.0 across the entire window
        """
        config = DaemonConfig(
            trend_analysis_window_seconds=180,
            safety_margin_celsius=5.0,
            max_target_temp=62.0,  # Threshold = 57.0 °C
        )
        state = DaemonState(config=config)
        state.start_time = time.monotonic() - 300.0  # Warmed up

        now = time.monotonic()
        for i in range(120, 180):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=55.0)
            )
        for i in range(60, 120):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=54.0)
            )
        for i in range(0, 60):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=53.0)
            )

        self.assertEqual(compute_guidance(state), "SCALE_UP")

    def test_hold_default(self):
        """HOLD should be returned when temperatures are stable but not meeting SCALE_UP."""
        config = DaemonConfig(
            trend_analysis_window_seconds=180,
            safety_margin_celsius=5.0,
            max_target_temp=62.0,
        )
        state = DaemonState(config=config)
        state.start_time = time.monotonic() - 300.0

        now = time.monotonic()
        for i in range(120, 180):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=58.0)
            )
        for i in range(60, 120):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=59.0)
            )
        for i in range(0, 60):
            state.telemetry_queue.append(
                TelemetryPoint(timestamp=now - i, temperature=58.0)
            )

        self.assertEqual(compute_guidance(state), "HOLD")

    def test_deterministic_ramp_profile(self):
        """
        Test using a fast virtual clock and MockTelemetryProvider (§8-3).
        Simulates a ramp profile and validates scale decisions over socket.
        """
        # Create temp directory for socket to avoid /var/run permissions
        temp_dir = tempfile.mkdtemp()
        test_socket_path = os.path.join(temp_dir, "test_thermal_pacer.sock")

        try:
            config = DaemonConfig(
                max_target_temp=62.0,
                safety_margin_celsius=5.0,
                trend_analysis_window_seconds=180,
                polling_interval_seconds=1.0,  # Match 1s step size
                enable_nvidia_gpu=False,
                restore_on_exit=False,
            )

            virtual_time = 1000.0
            last_polled_time = virtual_time

            mock_provider = MockTelemetryProvider(
                start_time=virtual_time,
                max_target_temp=62.0,
                get_virtual_time_func=lambda: virtual_time
            )

            def mock_monotonic():
                return virtual_time

            def mock_sleep(seconds):
                nonlocal last_polled_time
                # Synchronize daemon telemetry loop in lock-step with virtual_time.
                # Background thread will block here until advance_virtual_time()
                # pushes the clock forward, registering exactly one sample per second.
                while virtual_time <= last_polled_time:
                    original_sleep(0.0001)
                last_polled_time = virtual_time

            def advance_virtual_time(seconds: float):
                nonlocal virtual_time
                for _ in range(int(seconds)):
                    virtual_time += 1.0
                    # Wait for telemetry loop thread to process the new tick
                    while last_polled_time < virtual_time:
                        original_sleep(0.0001)

            with patch("thermal_pacer.daemon.time.monotonic", new=mock_monotonic), \
                 patch("thermal_pacer.daemon.time.sleep", new=mock_sleep), \
                 patch("thermal_pacer.daemon.detect_cpu_arch", return_value="unknown"), \
                 patch("thermal_pacer.daemon.read_governors", return_value={}), \
                 patch("thermal_pacer.daemon.backup_hardware_state", return_value=None), \
                 patch("thermal_pacer.daemon.set_all_governors", return_value=None), \
                 patch("thermal_pacer.daemon.write_boost_state", return_value=None):

                engine = ThermalDaemonEngine(config=config, telemetry_provider=mock_provider)
                engine.state.start_time = virtual_time

                server_thread = threading.Thread(
                    target=engine.run,
                    daemon=True,
                )

                with patch("thermal_pacer.daemon.SOCKET_PATH", test_socket_path):
                    server_thread.start()

                    # Wait for socket creation
                    retries = 50
                    while not os.path.exists(test_socket_path) and retries > 0:
                        original_sleep(0.01)
                        retries -= 1

                    self.assertTrue(os.path.exists(test_socket_path))

                    # Connect client
                    with ThermalGuard(socket_path=test_socket_path) as guard:
                        # Helper to block until the telemetry queue catches up with the virtual time clock.
                        # This prevents race conditions where the client thread queries the daemon before
                        # the telemetry thread has fully processed and committed the latest data point.
                        def wait_for_queue_sync():
                            while not engine.state.telemetry_queue or engine.state.telemetry_queue[-1].timestamp < virtual_time:
                                original_sleep(0.0001)

                        # 1. Warm-up phase check
                        # Advance time by 50 seconds (warmup is 180s, so elapsed < window)
                        advance_virtual_time(50.0)
                        wait_for_queue_sync()
                        self.assertEqual(guard.get_concurrency_guidance(), "HOLD")

                        # 2. Stable/Clear warmup phase
                        # Advance past the remaining warmup duration (total 180s elapsed).
                        # At exactly 180s elapsed, the warm-up guard passes, and temperatures
                        # in the queue are all stable at 50.0 °C, yielding SCALE_UP.
                        advance_virtual_time(130.0)
                        wait_for_queue_sync()
                        self.assertEqual(guard.get_concurrency_guidance(), "SCALE_UP")

                        # 3. Rising phase
                        # Advance by another 150 seconds (total 330s elapsed)
                        # The temperature will climb from 50.0 °C to 59.0 °C
                        advance_virtual_time(150.0)
                        wait_for_queue_sync()
                        self.assertEqual(guard.get_concurrency_guidance(), "SCALE_DOWN")

                        # 4. Cooling phase
                        # Advance by another 240 seconds (total 570s elapsed)
                        # The temperature cools down and stabilizes under 57.0 °C, and
                        # once the high 59.0 °C temperatures roll completely out of the
                        # 180-second telemetry window, guidance shifts back to SCALE_UP.
                        advance_virtual_time(240.0)
                        wait_for_queue_sync()
                        self.assertEqual(guard.get_concurrency_guidance(), "SCALE_UP")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

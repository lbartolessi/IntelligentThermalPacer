"""
thermal_pacer/daemon.py

The IntelligentThermalPacer daemon (thermal_pacerd).

Run as a socket-activated systemd service:
    python3 -m thermal_pacer.daemon

Out-of-band governor restoration (called by ExecStopPost on SIGKILL):
    python3 -m thermal_pacer.daemon --restore-governors

Architecture (§6):
  - socketserver.ThreadingUnixStreamServer handles concurrent clients.
  - One background thread polls hardware telemetry every 1 second.
  - A threading.Lock protects all writes/reads to the telemetry deque.
  - client_count is an atomic-safe integer (protected by the same lock).
  - When client_count drops to 0 the daemon restores governors and exits.
"""

from __future__ import annotations

import collections
import datetime
import glob
import json
import logging
import logging.handlers
import os
import signal
import socket
import socketserver
import sys
import syslog
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOCKET_PATH: str = "/var/run/thermal_pacer.sock"
CONFIG_PATH: str = "/etc/thermal_pacer/thermal_config.json"
BAK_FILE: str = "/var/run/thermal_pacer.governors.bak"

AMD_BOOST_PATHS: list[str] = [
    "/sys/devices/system/cpu/amd_pstate/cpb_boost",
    "/sys/devices/system/cpu/cpufreq/boost",
]
INTEL_BOOST_PATH: str = "/sys/devices/system/cpu/intel_pstate/no_turbo"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class DaemonConfig:
    max_target_temp: float = 62.0
    strategy: str = "eco"
    safety_margin_celsius: float = 5.0
    force_powersave_on_start: bool = True
    disable_cpu_boost: bool = True
    restore_on_exit: bool = True
    polling_interval_seconds: float = 1.0
    enable_nvidia_gpu: bool = True
    trend_analysis_window_seconds: int = 180
    emit_warnings: bool = True


def load_config(path: str = CONFIG_PATH) -> DaemonConfig:
    """Load configuration from JSON file; fall back to safe defaults."""
    cfg = DaemonConfig()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

        ts = raw.get("thermal_settings", {})
        cfg.max_target_temp = float(ts.get("max_target_temp", cfg.max_target_temp))
        cfg.strategy = ts.get("strategy", cfg.strategy)
        cfg.safety_margin_celsius = float(ts.get("safety_margin_celsius", cfg.safety_margin_celsius))

        lg = raw.get("linux_governor", {})
        cfg.force_powersave_on_start = bool(lg.get("force_powersave_on_start", cfg.force_powersave_on_start))
        cfg.disable_cpu_boost = bool(lg.get("disable_cpu_boost", cfg.disable_cpu_boost))
        cfg.restore_on_exit = bool(lg.get("restore_on_exit", cfg.restore_on_exit))

        tel = raw.get("telemetry", {})
        cfg.polling_interval_seconds = float(tel.get("polling_interval_seconds", cfg.polling_interval_seconds))
        cfg.enable_nvidia_gpu = bool(tel.get("enable_nvidia_gpu", cfg.enable_nvidia_gpu))

        sm = raw.get("statistical_memory", {})
        cfg.trend_analysis_window_seconds = int(sm.get("trend_analysis_window_seconds", cfg.trend_analysis_window_seconds))
        cfg.emit_warnings = bool(sm.get("emit_warnings", cfg.emit_warnings))

    except (OSError, ValueError) as exc:
        print(f"[ThermalPacer] Config load warning ({exc}); using defaults.", file=sys.stderr)

    return cfg


# ---------------------------------------------------------------------------
# Telemetry Provider Protocol (§8 – Dependency Injection contract)
# ---------------------------------------------------------------------------

@runtime_checkable
class TelemetryProvider(Protocol):
    """Single-method interface for hardware temperature acquisition."""

    def get_critical_temperature(self) -> float:
        """Return the highest observed hardware temperature (°C)."""
        ...


class LiveTelemetryProvider:
    """
    Production telemetry provider.

    CPU temperatures via psutil.sensors_temperatures() (§6-A).
    GPU temperature via pynvml if enable_nvidia_gpu is True (§6-A).
    """

    def __init__(self, enable_nvidia: bool = True) -> None:
        self._nvml: object = None
        self._nvml_handle: object = None

        if enable_nvidia:
            try:
                import pynvml  # type: ignore[import]
                pynvml.nvmlInit()
                self._nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                self._nvml = pynvml
            except Exception:
                pass  # GPU unavailable – degrade gracefully

    def _get_cpu_temps(self) -> list[float]:
        temps: list[float] = []
        try:
            import psutil  # type: ignore[import]
            sensor_data = psutil.sensors_temperatures()
            cpu_keys = ("coretemp", "cpu_thermal", "k10temp", "acpitz", "zenpower")
            for key, entries in sensor_data.items():
                if key in cpu_keys:
                    for entry in entries:
                        temps.append(entry.current)
            if not temps:
                for entries in sensor_data.values():
                    for entry in entries:
                        temps.append(entry.current)
        except Exception:
            pass
        return temps

    def _get_gpu_temp(self) -> Optional[float]:
        if self._nvml is not None and self._nvml_handle is not None:
            try:
                gpu_temp = self._nvml.nvmlDeviceGetTemperature(  # type: ignore[attr-defined]
                    self._nvml_handle, self._nvml.NVML_TEMPERATURE_GPU  # type: ignore[attr-defined]
                )
                return float(gpu_temp)
            except Exception:
                pass
        return None

    def get_critical_temperature(self) -> float:
        temps = self._get_cpu_temps()
        gpu_temp = self._get_gpu_temp()
        if gpu_temp is not None:
            temps.append(gpu_temp)
        return max(temps) if temps else 0.0


# ---------------------------------------------------------------------------
# Telemetry Data Point
# ---------------------------------------------------------------------------

@dataclass
class TelemetryPoint:
    timestamp: float      # time.monotonic()
    temperature: float
    pace_calls: int = 0   # pace_check calls received this 1-second interval
    pace_waits: int = 0   # "wait" responses sent this 1-second interval


# ---------------------------------------------------------------------------
# Shared Daemon State
# ---------------------------------------------------------------------------

@dataclass
class DaemonState:
    config: DaemonConfig
    lock: threading.Lock = field(default_factory=threading.Lock)
    telemetry_queue: collections.deque = field(init=False)
    client_count: int = 0
    start_time: float = field(default_factory=time.monotonic)
    # Interval pace counters (reset each telemetry tick)
    _interval_calls: int = 0
    _interval_waits: int = 0

    def __post_init__(self) -> None:
        maxlen = max(self.config.trend_analysis_window_seconds, 1)
        self.telemetry_queue = collections.deque(maxlen=maxlen)

    # --- thread-safe counter helpers ---
    def record_pace_call(self, was_wait: bool) -> None:
        with self.lock:
            self._interval_calls += 1
            if was_wait:
                self._interval_waits += 1

    def flush_interval_counters(self) -> tuple[int, int]:
        """Atomically swap interval counters to zero; return (calls, waits)."""
        with self.lock:
            calls, waits = self._interval_calls, self._interval_waits
            self._interval_calls = 0
            self._interval_waits = 0
        return calls, waits

    def latest_temperature(self) -> float:
        with self.lock:
            if self.telemetry_queue:
                return self.telemetry_queue[-1].temperature
        return 0.0


# ---------------------------------------------------------------------------
# CPU Topology and Boost Management (§6-B)
# ---------------------------------------------------------------------------

def detect_cpu_arch() -> str:
    """Return 'intel', 'amd', or 'unknown' by inspecting /proc/cpuinfo."""
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as fh:
            content = fh.read().lower()
        if "intel" in content:
            return "intel"
        if "amd" in content:
            return "amd"
    except OSError:
        pass
    return "unknown"


def _find_amd_boost_path() -> str:
    for p in AMD_BOOST_PATHS:
        if os.path.exists(p):
            return p
    return ""


def read_boost_state(arch: str) -> tuple[str, str]:
    """Return (path, raw_value) for the boost control sysfs node."""
    if arch == "amd":
        path = _find_amd_boost_path()
    elif arch == "intel":
        path = INTEL_BOOST_PATH if os.path.exists(INTEL_BOOST_PATH) else ""
    else:
        return "", ""

    if not path:
        return "", ""
    try:
        with open(path, "r") as fh:
            return path, fh.read().strip()
    except OSError:
        return path, ""


def write_boost_state(arch: str, enabled: bool) -> None:
    """
    Enable or disable CPU boost respecting architecture polarity (§6-B):
      AMD  – path value: 1=enabled, 0=disabled
      Intel – no_turbo:  0=enabled (turbo allowed), 1=disabled (no turbo)
    """
    if arch == "amd":
        value = "1" if enabled else "0"
        path = _find_amd_boost_path()
        if not path:
            return
    elif arch == "intel":
        value = "0" if enabled else "1"
        path = INTEL_BOOST_PATH
    else:
        return

    try:
        with open(path, "w") as fh:
            fh.write(value)
    except OSError as exc:
        print(f"[ThermalPacer] boost write failed ({path}): {exc}", file=sys.stderr)


def read_governors() -> dict[str, str]:
    governors: dict[str, str] = {}
    for path in sorted(glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")):
        cpu = path.split("/")[5]
        try:
            with open(path, "r") as fh:
                governors[cpu] = fh.read().strip()
        except OSError:
            pass
    return governors


def write_governors(governors: dict[str, str]) -> None:
    for cpu, gov in governors.items():
        path = f"/sys/devices/system/cpu/{cpu}/cpufreq/scaling_governor"
        try:
            with open(path, "w") as fh:
                fh.write(gov)
        except OSError as exc:
            print(f"[ThermalPacer] governor write failed ({cpu}): {exc}", file=sys.stderr)


def set_all_governors(governor: str) -> None:
    for path in glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"):
        try:
            with open(path, "w") as fh:
                fh.write(governor)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Hardware Recovery Cache (§6-B)
# ---------------------------------------------------------------------------

def backup_hardware_state(arch: str, governors: dict[str, str],
                           boost_path: str, boost_value: str) -> None:
    """Persist current hardware state to the emergency recovery file."""
    payload = {
        "arch": arch,
        "governors": governors,
        "boost_path": boost_path,
        "boost_value": boost_value,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    try:
        with open(BAK_FILE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
    except OSError as exc:
        print(f"[ThermalPacer] Could not write backup file: {exc}", file=sys.stderr)


def restore_from_backup() -> None:
    """
    --restore-governors OOB path (§6-B).

    Reads BAK_FILE, restores governors and boost, unlinks the file, exits.
    Called by systemd ExecStopPost to recover after an uncatchable SIGKILL.
    """
    try:
        with open(BAK_FILE, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[ThermalPacer] --restore-governors: cannot read {BAK_FILE}: {exc}",
              file=sys.stderr)
        sys.exit(1)

    write_governors(state.get("governors", {}))

    boost_path: str = state.get("boost_path", "")
    boost_value: str = state.get("boost_value", "")
    if boost_path and boost_value:
        try:
            with open(boost_path, "w") as fh:
                fh.write(boost_value)
        except OSError as exc:
            print(f"[ThermalPacer] --restore-governors: boost restore failed: {exc}",
                  file=sys.stderr)

    try:
        os.unlink(BAK_FILE)
    except OSError:
        pass

    print("[ThermalPacer] Governors restored successfully.")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Trend Analysis (§6-C)
# ---------------------------------------------------------------------------

def _segment_mean(points: list[TelemetryPoint]) -> float:
    if not points:
        return 0.0
    return sum(p.temperature for p in points) / len(points)


def _segment_re(points: list[TelemetryPoint]) -> float:
    total = sum(p.pace_calls for p in points)
    waits = sum(p.pace_waits for p in points)
    return waits / total if total > 0 else 0.0


def compute_guidance(state: DaemonState) -> str:
    """
    Evaluate rolling window segments and return a concurrency directive (§6-C).

    Returns 'SCALE_DOWN', 'SCALE_UP', or 'HOLD'.
    """
    cfg = state.config
    now = time.monotonic()
    elapsed = now - state.start_time
    window = cfg.trend_analysis_window_seconds

    # Warm-up guard
    if elapsed < window:
        return "HOLD"

    s_size = window // 3  # seconds per segment

    with state.lock:
        points = list(state.telemetry_queue)

    if not points:
        return "HOLD"

    def slice_segment(start_ago: int, end_ago: int) -> list[TelemetryPoint]:
        return [p for p in points if start_ago <= (now - p.timestamp) < end_ago]

    seg_current  = slice_segment(0,          s_size)
    seg_previous = slice_segment(s_size,     2 * s_size)
    seg_prior    = slice_segment(2 * s_size, 3 * s_size)

    if not seg_current or not seg_previous or not seg_prior:
        return "HOLD"

    t_cur  = _segment_mean(seg_current)
    t_prev = _segment_mean(seg_previous)
    t_pri  = _segment_mean(seg_prior)
    re_cur = _segment_re(seg_current)

    # SCALE_DOWN (§6-C)
    upward_trend = t_cur > t_prev > t_pri
    # Δ rate over the full window span (current centre vs prior centre)
    span_minutes = (2 * s_size) / 60.0
    delta_per_min = (t_cur - t_pri) / span_minutes if span_minutes > 0 else 0.0

    if (upward_trend and delta_per_min > 0.5) or re_cur > 0.40:
        if cfg.emit_warnings:
            try:
                syslog.openlog("thermal_pacer", syslog.LOG_PID, syslog.LOG_DAEMON)
                syslog.syslog(
                    syslog.LOG_WARNING,
                    f"SCALE_DOWN triggered: T_cur={t_cur:.1f}°C "
                    f"Δ={delta_per_min:.2f}°C/min Re={re_cur:.2f}",
                )
            except Exception:
                pass
        return "SCALE_DOWN"

    # SCALE_UP (§6-C)
    threshold = cfg.max_target_temp - cfg.safety_margin_celsius
    re_all = _segment_re(points)
    all_below = all(p.temperature < threshold for p in points)
    flat_or_down = t_cur <= t_pri

    if all_below and flat_or_down and re_all < 1e-9:
        return "SCALE_UP"

    return "HOLD"


# ---------------------------------------------------------------------------
# Pace-check throttle decision
# ---------------------------------------------------------------------------

def _throttle_duration_ms(current_temp: float, max_target: float) -> int:
    """
    Compute a proportional sleep duration when temperature exceeds the ceiling.
    Clamps between 50 ms and 2 000 ms.
    """
    overshoot = max(0.0, current_temp - max_target)
    return int(min(max(50, overshoot * 200), 2000))


# ---------------------------------------------------------------------------
# Request Handler
# ---------------------------------------------------------------------------

class ThermalRequestHandler(socketserver.StreamRequestHandler):
    """
    Per-connection handler spun up by ThreadingUnixStreamServer.

    Increments client_count on entry, decrements on exit.
    When client_count reaches 0 the daemon restores governors and exits.
    """

    # Injected by ThermalDaemonEngine
    daemon_state: DaemonState

    def setup(self) -> None:
        super().setup()
        with self.daemon_state.lock:
            self.daemon_state.client_count += 1

    def handle(self) -> None:
        state = self.daemon_state
        cfg = state.config

        try:
            for raw_line in self.rfile:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    cmd = json.loads(line)
                except json.JSONDecodeError:
                    self._send({"action": "error", "code": "UNKNOWN_COMMAND"})
                    continue

                command = cmd.get("command", "")

                if command == "pace_check":
                    current_temp = state.latest_temperature()
                    if current_temp >= cfg.max_target_temp:
                        duration_ms = _throttle_duration_ms(current_temp, cfg.max_target_temp)
                        self._send({"action": "wait", "duration_ms": duration_ms})
                        state.record_pace_call(was_wait=True)
                    else:
                        self._send({"action": "continue"})
                        state.record_pace_call(was_wait=False)

                elif command == "get_guidance":
                    decision = compute_guidance(state)
                    self._send({"action": "guidance_reply", "decision": decision})

                else:
                    self._send({"action": "error", "code": "UNKNOWN_COMMAND"})

        except OSError:
            pass  # Client disconnected abruptly

    def finish(self) -> None:
        super().finish()
        with self.daemon_state.lock:
            self.daemon_state.client_count -= 1
            count = self.daemon_state.client_count

        if count == 0:
            _graceful_shutdown(self.daemon_state)

    def _send(self, payload: dict) -> None:
        try:
            self.wfile.write((json.dumps(payload) + "\n").encode("utf-8"))
            self.wfile.flush()
        except OSError:
            pass


def _graceful_shutdown(state: DaemonState) -> None:
    """
    Called when the last client disconnects (§1 – Absolute State Restoration).
    Restores all hardware parameters and exits.
    """
    if state.config.restore_on_exit:
        try:
            with open(BAK_FILE, "r", encoding="utf-8") as fh:
                bak = json.load(fh)
            write_governors(bak.get("governors", {}))
            boost_path = bak.get("boost_path", "")
            boost_value = bak.get("boost_value", "")
            if boost_path and boost_value:
                with open(boost_path, "w") as fh:
                    fh.write(boost_value)
            os.unlink(BAK_FILE)
        except Exception as exc:
            print(f"[ThermalPacer] Shutdown restore failed: {exc}", file=sys.stderr)

    print("[ThermalPacer] All clients disconnected. Exiting.", file=sys.stderr)
    # Use os._exit to forcefully exit from a daemon thread context
    os._exit(0)


# ---------------------------------------------------------------------------
# Telemetry Background Thread
# ---------------------------------------------------------------------------

def _telemetry_loop(state: DaemonState, provider: TelemetryProvider) -> None:
    """
    Runs every polling_interval_seconds (§6-A).
    Appends a TelemetryPoint to the deque and resets interval counters.
    """
    interval = state.config.polling_interval_seconds
    while True:
        time.sleep(interval)
        temp = provider.get_critical_temperature()
        calls, waits = state.flush_interval_counters()
        point = TelemetryPoint(
            timestamp=time.monotonic(),
            temperature=temp,
            pace_calls=calls,
            pace_waits=waits,
        )
        with state.lock:
            state.telemetry_queue.append(point)


# ---------------------------------------------------------------------------
# Custom Server (systemd socket activation support)
# ---------------------------------------------------------------------------

class ThermalServer(socketserver.ThreadingUnixStreamServer):
    """
    ThreadingUnixStreamServer that can accept an already-bound socket
    passed in by systemd socket activation (LISTEN_FDS mechanism).
    """

    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        server_address_or_socket,
        request_handler_class,
        bind_and_activate: bool = True,
    ) -> None:
        if isinstance(server_address_or_socket, socket.socket):
            # Inherited socket from systemd: skip bind/activate
            socketserver.BaseServer.__init__(self, "", request_handler_class)
            self.socket = server_address_or_socket
        else:
            super().__init__(server_address_or_socket, request_handler_class, bind_and_activate)


def _get_systemd_socket() -> Optional[socket.socket]:
    """
    Detect and return the socket passed by systemd socket activation.
    Returns None if not running under systemd.
    """
    try:
        listen_fds = int(os.environ.get("LISTEN_FDS", "0"))
        listen_pid = int(os.environ.get("LISTEN_PID", "0"))
    except ValueError:
        return None

    if listen_fds == 1 and listen_pid == os.getpid():
        SD_LISTEN_FDS_START = 3
        sock = socket.socket(fileno=SD_LISTEN_FDS_START)
        sock.setblocking(True)
        return sock
    return None


# ---------------------------------------------------------------------------
# Engine – wires everything together
# ---------------------------------------------------------------------------

class ThermalDaemonEngine:
    """
    Orchestrates config loading, hardware initialisation, telemetry thread,
    and the socket server. Exposed as a class to support dependency injection
    in the test suite (§8).
    """

    def __init__(
        self,
        config: Optional[DaemonConfig] = None,
        telemetry_provider: Optional[TelemetryProvider] = None,
    ) -> None:
        self.config = config or load_config()
        self.state = DaemonState(config=self.config)
        self.provider: TelemetryProvider = (
            telemetry_provider or LiveTelemetryProvider(self.config.enable_nvidia_gpu)
        )
        self._arch: str = detect_cpu_arch()

    def _apply_startup_governors(self) -> None:
        """
        Enforce Rule of Precedence (§3):
          - 'eco' strategy always forces powersave + disables boost.
          - Other strategies respect individual flags.
        """
        cfg = self.config

        force_powersave = cfg.strategy == "eco" or cfg.force_powersave_on_start
        disable_boost   = cfg.strategy == "eco" or cfg.disable_cpu_boost

        if force_powersave:
            set_all_governors("powersave")
        if disable_boost:
            write_boost_state(self._arch, enabled=False)

    def run(self) -> None:
        """Start the daemon: backup hardware, configure governors, serve."""
        cfg = self.config

        # --- Snapshot and backup current hardware state (§6-B) ---
        governors = read_governors()
        boost_path, boost_value = read_boost_state(self._arch)
        backup_hardware_state(self._arch, governors, boost_path, boost_value)

        # --- Apply startup governor policy (§3 precedence rule) ---
        self._apply_startup_governors()

        # --- Start background telemetry thread (§6-A) ---
        tel_thread = threading.Thread(
            target=_telemetry_loop,
            args=(self.state, self.provider),
            daemon=True,
            name="telemetry-poller",
        )
        tel_thread.start()

        # --- Build and configure the server ---
        systemd_sock = _get_systemd_socket()

        if systemd_sock is not None:
            server = ThermalServer(systemd_sock, ThermalRequestHandler)
        else:
            # Stand-alone mode (testing / manual startup)
            if os.path.exists(SOCKET_PATH):
                os.unlink(SOCKET_PATH)
            server = ThermalServer(SOCKET_PATH, ThermalRequestHandler)

        # Inject shared state into the handler class
        ThermalRequestHandler.daemon_state = self.state  # type: ignore[attr-defined]

        print(f"[ThermalPacer] Daemon ready. arch={self._arch} strategy={cfg.strategy}",
              file=sys.stderr)

        try:
            server.serve_forever()
        finally:
            server.server_close()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    if "--restore-governors" in argv:
        restore_from_backup()  # exits inside

    engine = ThermalDaemonEngine()
    engine.run()


if __name__ == "__main__":
    main()

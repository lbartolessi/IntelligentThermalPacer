"""
thermal_pacer/calibration.py

Automated Intelligent Calibration Protocol for IntelligentThermalPacer (§7).

Invoked via:  sudo python3 -m thermal_pacer --calibrate

Phases:
  1. Chronological validity check (skip if < 30 days since last calibration).
  2. Phase 1 – Idle baseline: 30 s at rest → T_idle.
  3. Phase 2 – Eco profile:  powersave + boost off, 60 s synthetic load → T_eco.
  4. Phase 3 – Peak profile: restore governors + boost on, 60 s load → T_peak,
               tracking ramp velocity.
  5. Evaluate and conditionally update thermal_config.json.

Safety: an exclusive, non-blocking fcntl.flock on /var/run/thermal_pacer.lock
prevents concurrent calibration runs and aborts if the daemon has live clients.
"""

from __future__ import annotations

import concurrent.futures
import datetime
import fcntl
import json
import math
import multiprocessing
import os
import sys
import time
from typing import Optional

from thermal_pacer.daemon import (
    CONFIG_PATH,
    LiveTelemetryProvider,
    TelemetryProvider,
    detect_cpu_arch,
    read_governors,
    set_all_governors,
    write_boost_state,
    write_governors,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOCK_FILE: str = "/var/run/thermal_pacer.lock"
CALIBRATION_EXPIRY_DAYS: int = 30

IDLE_PHASE_SECONDS: int = 30
STRESS_PHASE_SECONDS: int = 60

THERMAL_RAMP_CRITICAL_CELSIUS_PER_SEC: float = 1.5
CALCULATED_OFFSET_CELSIUS: float = 4.0  # T_calculated = T_eco + 4°C  (§7-5)


# ---------------------------------------------------------------------------
# CPU-intensive workload (pure Python – no numpy required)
# ---------------------------------------------------------------------------

def _stress_worker(duration_seconds: float) -> None:
    """
    Synthetic matrix-multiplication workload designed to maximise CPU heat.
    Each process runs its own tight loop until the deadline.
    Uses 40×40 matrices (pure Python) to keep overhead per iteration low.
    """
    size = 40
    end = time.monotonic() + duration_seconds
    while time.monotonic() < end:
        a = [[float(i * size + j) for j in range(size)] for i in range(size)]
        b = [[float((i + j) % size) for j in range(size)] for i in range(size)]
        # Matrix multiply: c[i][j] = sum_k a[i][k] * b[k][j]
        _ = [
            [sum(a[i][k] * b[k][j] for k in range(size)) for j in range(size)]
            for i in range(size)
        ]


def _run_stress_load(duration_seconds: float) -> None:
    """
    Spin the stress workload on all available CPU cores using
    multiprocessing.Pool so the GIL does not constrain thermal load.
    """
    n_workers = multiprocessing.cpu_count()
    with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = [pool.submit(_stress_worker, duration_seconds) for _ in range(n_workers)]
        concurrent.futures.wait(futures)


# ---------------------------------------------------------------------------
# Temperature sampling helpers
# ---------------------------------------------------------------------------

def _sample_mean_temp(
    provider: TelemetryProvider,
    duration_seconds: float,
    sample_interval: float = 1.0,
) -> float:
    """
    Sample the telemetry provider repeatedly over *duration_seconds* and
    return the arithmetic mean of all readings.
    """
    samples: list[float] = []
    end = time.monotonic() + duration_seconds
    while time.monotonic() < end:
        samples.append(provider.get_critical_temperature())
        time.sleep(sample_interval)
    return sum(samples) / len(samples) if samples else 0.0


def _sample_ramp_velocity(
    provider: TelemetryProvider,
    duration_seconds: float,
    sample_interval: float = 1.0,
) -> tuple[float, float]:
    """
    Record temperatures at 1-second intervals during a stress phase.
    Returns (max_temperature, max_ramp_velocity_celsius_per_second).

    Ramp velocity is the maximum Δtemp/Δtime observed between consecutive
    readings.
    """
    readings: list[tuple[float, float]] = []  # (monotonic_time, temp)
    end = time.monotonic() + duration_seconds
    while time.monotonic() < end:
        t_now = time.monotonic()
        temp = provider.get_critical_temperature()
        readings.append((t_now, temp))
        time.sleep(sample_interval)

    if not readings:
        return 0.0, 0.0

    max_temp = max(t for _, t in readings)
    max_ramp = 0.0
    for i in range(1, len(readings)):
        delta_t = readings[i][0] - readings[i - 1][0]
        delta_temp = readings[i][1] - readings[i - 1][1]
        if delta_t > 0:
            ramp = delta_temp / delta_t
            if ramp > max_ramp:
                max_ramp = ramp

    return max_temp, max_ramp


# ---------------------------------------------------------------------------
# Config read/write
# ---------------------------------------------------------------------------

def _load_raw_config(path: str = CONFIG_PATH) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[Calibration] ERROR: Cannot load config ({path}): {exc}", file=sys.stderr)
        sys.exit(1)


def _save_raw_config(cfg: dict, path: str = CONFIG_PATH) -> None:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2)
            fh.write("\n")
    except OSError as exc:
        print(f"[Calibration] ERROR: Cannot write config ({path}): {exc}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Lock helpers
# ---------------------------------------------------------------------------

def _acquire_exclusive_lock(lock_path: str) -> int:
    """
    Obtain a non-blocking exclusive POSIX file lock (§7).
    Returns the open file descriptor on success.
    Calls sys.exit(1) if the lock is already held.
    """
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BlockingIOError:
        print(
            "[Calibration] ABORT: Another calibration (or daemon with active clients) "
            "is holding the exclusive lock. Cannot proceed.",
            file=sys.stderr,
        )
        sys.exit(1)
    except OSError as exc:
        print(f"[Calibration] ABORT: Cannot acquire lock ({lock_path}): {exc}", file=sys.stderr)
        sys.exit(1)


def _release_lock(fd: int, lock_path: str) -> None:
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        os.unlink(lock_path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Main calibration routine
# ---------------------------------------------------------------------------

def run_calibration(
    config_path: str = CONFIG_PATH,
    telemetry_provider: Optional[TelemetryProvider] = None,
) -> None:
    """
    Execute the full calibration protocol (§7).

    Parameters
    ----------
    config_path:
        Path to the JSON configuration file (overridable in tests).
    telemetry_provider:
        Optional provider for DI in unit tests; defaults to LiveTelemetryProvider.
    """

    # --- Exclusive lock (§7) ---
    lock_fd = _acquire_exclusive_lock(LOCK_FILE)

    try:
        _run_calibration_locked(config_path, telemetry_provider)
    finally:
        _release_lock(lock_fd, LOCK_FILE)


def _check_chronological_validity(raw_cfg: dict) -> bool:
    """Check if the calibration has expired (§7-1)."""
    cal_diag = raw_cfg.get("calibration_diagnostics", {})
    last_cal_str: str = cal_diag.get("last_calibration_utc", "")
    if last_cal_str:
        try:
            last_cal = datetime.datetime.fromisoformat(last_cal_str.replace("Z", "+00:00"))
            now_utc = datetime.datetime.now(tz=datetime.timezone.utc)
            elapsed_days = (now_utc - last_cal).days
            if elapsed_days < CALIBRATION_EXPIRY_DAYS:
                remaining = CALIBRATION_EXPIRY_DAYS - elapsed_days
                print(
                    f"[Calibration] NOTICE: Last calibration was {elapsed_days} day(s) ago "
                    f"(< {CALIBRATION_EXPIRY_DAYS} days). "
                    f"Next calibration available in {remaining} day(s). Aborting.",
                    file=sys.stderr,
                )
                return False
        except ValueError:
            pass  # Unparseable timestamp – proceed with calibration
    return True


def _run_phase2_eco(provider: TelemetryProvider, arch: str, t_idle: float) -> float:
    """Phase 2 – Eco profile: powersave + boost off, 60s load (§7-3)."""
    print(f"[Calibration] Phase 2 – Eco profile ({STRESS_PHASE_SECONDS}s)…")
    set_all_governors("powersave")
    write_boost_state(arch, enabled=False)

    import threading

    t_eco_readings: list[float] = []
    phase2_done = threading.Event()

    def _phase2_sampler() -> None:
        while not phase2_done.is_set():
            t_eco_readings.append(provider.get_critical_temperature())
            time.sleep(1.0)

    sampler_thread = threading.Thread(target=_phase2_sampler, daemon=True)
    sampler_thread.start()

    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as pool:
        futs = [pool.submit(_stress_worker, float(STRESS_PHASE_SECONDS))
                for _ in range(multiprocessing.cpu_count())]
        concurrent.futures.wait(futs)

    phase2_done.set()
    sampler_thread.join(timeout=2.0)

    t_eco = sum(t_eco_readings) / len(t_eco_readings) if t_eco_readings else t_idle
    print(f"[Calibration] Phase 2 done. T_eco = {t_eco:.1f}°C")
    return t_eco


def _run_phase3_peak(
    provider: TelemetryProvider,
    arch: str,
    baseline_governors: dict[str, str],
    t_eco: float,
) -> tuple[float, float]:
    """Phase 3 – Peak profile: restore default governors + boost on, 60s load (§7-4)."""
    print(f"[Calibration] Phase 3 – Peak profile ({STRESS_PHASE_SECONDS}s)…")
    write_governors(baseline_governors)
    write_boost_state(arch, enabled=True)

    import threading

    t_peak_readings: list[tuple[float, float]] = []  # (timestamp, temp)
    phase3_done = threading.Event()

    def _phase3_sampler() -> None:
        while not phase3_done.is_set():
            t_peak_readings.append((time.monotonic(), provider.get_critical_temperature()))
            time.sleep(1.0)

    sampler3 = threading.Thread(target=_phase3_sampler, daemon=True)
    sampler3.start()

    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as pool:
        futs = [pool.submit(_stress_worker, float(STRESS_PHASE_SECONDS))
                for _ in range(multiprocessing.cpu_count())]
        concurrent.futures.wait(futs)

    phase3_done.set()
    sampler3.join(timeout=2.0)

    t_peak = max((t for _, t in t_peak_readings), default=t_eco)

    max_ramp_vel = 0.0
    for i in range(1, len(t_peak_readings)):
        dt = t_peak_readings[i][0] - t_peak_readings[i - 1][0]
        dtemp = t_peak_readings[i][1] - t_peak_readings[i - 1][1]
        if dt > 0:
            vel = dtemp / dt
            if vel > max_ramp_vel:
                max_ramp_vel = vel

    print(f"[Calibration] Phase 3 done. T_peak = {t_peak:.1f}°C  "
          f"Ramp = {max_ramp_vel:.2f}°C/s")
    return t_peak, max_ramp_vel


def _evaluate_calibration_results(
    raw_cfg: dict,
    t_idle: float,
    t_eco: float,
    t_peak: float,
    max_ramp_vel: float,
    config_path: str,
) -> None:
    """Evaluate and conditionally update configuration based on results (§7-5)."""
    t_calculated = t_eco + CALCULATED_OFFSET_CELSIUS
    print(f"[Calibration] T_calculated = {t_eco:.1f} + {CALCULATED_OFFSET_CELSIUS} "
          f"= {t_calculated:.1f}°C")

    current_max_target = float(
        raw_cfg.get("thermal_settings", {}).get("max_target_temp", math.inf)
    )

    if t_calculated < current_max_target:
        raw_cfg.setdefault("thermal_settings", {})["max_target_temp"] = round(t_calculated, 1)
        print(f"[Calibration] max_target_temp updated: "
              f"{current_max_target:.1f}°C → {t_calculated:.1f}°C (more restrictive).")
    else:
        print(f"[Calibration] max_target_temp kept at {current_max_target:.1f}°C "
              f"(T_calculated={t_calculated:.1f}°C is not more restrictive).")

    if max_ramp_vel > THERMAL_RAMP_CRITICAL_CELSIUS_PER_SEC:
        raw_cfg.setdefault("calibration_diagnostics", {})
        raw_cfg["calibration_diagnostics"]["thermal_efficiency_rating"] = "CRITICAL_COMPACT_CHASSIS"
        existing_rec: str = raw_cfg["calibration_diagnostics"].get(
            "hardware_safety_recommendation", ""
        )
        warning_suffix = (
            f" WARNING: Critical thermal ramp velocity detected "
            f"({max_ramp_vel:.2f}°C/s > {THERMAL_RAMP_CRITICAL_CELSIUS_PER_SEC}°C/s). "
            "Severely reduce concurrent worker count."
        )
        raw_cfg["calibration_diagnostics"]["hardware_safety_recommendation"] = (
            existing_rec + warning_suffix
        )
        print(f"[Calibration] CRITICAL_COMPACT_CHASSIS rating set "
              f"(ramp={max_ramp_vel:.2f}°C/s).")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    raw_cfg.setdefault("calibration_diagnostics", {})["last_calibration_utc"] = now_iso

    _save_raw_config(raw_cfg, config_path)
    print(f"[Calibration] Configuration saved to {config_path}.")

    print("[Calibration] Protocol complete.")
    print(f"  T_idle   = {t_idle:.1f}°C")
    print(f"  T_eco    = {t_eco:.1f}°C")
    print(f"  T_peak   = {t_peak:.1f}°C")
    print(f"  T_calc   = {t_calculated:.1f}°C")
    print(f"  Ramp vel = {max_ramp_vel:.2f}°C/s")


def _run_calibration_locked(
    config_path: str,
    telemetry_provider: Optional[TelemetryProvider],
) -> None:
    arch = detect_cpu_arch()
    provider: TelemetryProvider = telemetry_provider or LiveTelemetryProvider(
        enable_nvidia=True
    )
    raw_cfg = _load_raw_config(config_path)

    if not _check_chronological_validity(raw_cfg):
        return

    print("[Calibration] Chronological check passed. Starting calibration protocol.")

    baseline_governors = read_governors()

    print(f"[Calibration] Phase 1 – Idle baseline ({IDLE_PHASE_SECONDS}s)…")
    t_idle = _sample_mean_temp(provider, IDLE_PHASE_SECONDS)
    print(f"[Calibration] Phase 1 done. T_idle = {t_idle:.1f}°C")

    t_eco = _run_phase2_eco(provider, arch, t_idle)

    t_peak, max_ramp_vel = _run_phase3_peak(provider, arch, baseline_governors, t_eco)

    _evaluate_calibration_results(raw_cfg, t_idle, t_eco, t_peak, max_ramp_vel, config_path)

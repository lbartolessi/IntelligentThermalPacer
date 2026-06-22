"""
thermal_pacer/client.py

Lightweight, zero-dependency* client library for the IntelligentThermalPacer daemon.

Implements the ThermalGuard context manager described in §5 of the spec (Rev. 4.0).
Communicates exclusively via the Unix Domain Socket defined in §4, using
makefile('r') for safe line-based reading to avoid stream fragmentation bugs.

(*) Only stdlib modules are used here; psutil/pynvml live in the daemon.
"""

import json
import socket
import time
from types import TracebackType
from typing import Any, Literal, Optional, Type


class ThermalGuard:
    """
    Context manager that connects a host application to the ThermalPacer daemon,
    enabling cooperative in-thread thermal throttling and concurrency guidance.

    Usage
    -----
    ::

        from thermal_pacer import ThermalGuard

        with ThermalGuard() as guard:
            for item in workload:
                guard.pace()                        # cooperative throttle point
                guidance = guard.get_concurrency_guidance()
                if guidance == "SCALE_DOWN":
                    reduce_workers()
                elif guidance == "SCALE_UP":
                    increase_workers()
                process(item)

    The context manager guarantees socket teardown under every execution path:
    clean exit, host-application exceptions, and uncaught signals that do
    unwind the Python stack (anything except SIGKILL, which the *daemon* handles
    via systemd's ExecStopPost and the ``--restore-governors`` flag).
    """

    def __init__(self, socket_path: str = "/var/run/thermal_pacer.sock") -> None:
        """
        Initialises the client library, pointing it at the shared systemd socket.

        The connection is **not** established here; it is deferred to
        :meth:`__enter__` so that instantiation itself is always safe.

        Parameters
        ----------
        socket_path:
            Absolute path of the Unix Domain Socket created by
            ``thermal_pacer.socket`` (systemd socket activation).
            Override only in tests or non-standard installations.
        """
        self.socket_path: str = socket_path
        self._socket_conn: Optional[socket.socket] = None
        self._socket_file: Optional[Any] = None  # IO[str] returned by makefile()

    # ------------------------------------------------------------------
    # Context-manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> "ThermalGuard":
        """
        Context manager entry point.

        Establishes a connection to the Unix domain socket and registers
        this client with the daemon (incrementing its internal
        ``client_count``).  Enforces a **5-second socket timeout** to
        prevent the host application from hanging indefinitely if the
        daemon is unresponsive.

        Returns
        -------
        ThermalGuard
            Self, so that the ``as`` clause in ``with ThermalGuard() as g``
            receives the connected instance.

        Raises
        ------
        RuntimeError
            If the connection to the daemon socket cannot be established.
        """
        self._connect_to_daemon()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        """
        Context manager exit point.

        Closes the socket unconditionally, which triggers an EOF on the
        daemon's read stream.  The daemon interprets EOF as client
        disconnection, decrements ``client_count``, and — when it reaches
        zero — restores all hardware governors and exits cleanly.

        Returns
        -------
        False
            Always.  Returning ``False`` (or ``None``) from ``__exit__``
            propagates any host-application exception naturally, preserving
            normal error-handling semantics.
        """
        self._disconnect_from_daemon()
        return False  # Do not suppress host-application exceptions

    # ------------------------------------------------------------------
    # Public API (§5)
    # ------------------------------------------------------------------

    def pace(self) -> None:
        """
        Cooperative throttle point — inject inside host execution loops.

        Sends a ``pace_check`` command to the daemon (§4, Command 1).
        If the daemon replies with ``{"action": "wait", "duration_ms": N}``,
        the call blocks via :func:`time.sleep` for the instructed duration
        before returning, slowing the host loop proportionally to thermal
        pressure.

        If the daemon is unreachable or returns malformed JSON the call
        silently returns without blocking, preserving host-application
        liveness (*fail-safe* design).

        Protocol
        --------
        * Send:    ``{"command": "pace_check"}\\n``
        * Receive: ``{"action": "continue"}``  →  no-op
        * Receive: ``{"action": "wait", "duration_ms": 45}``  →  sleep 45 ms
        """
        if not self._socket_conn or not self._socket_file:
            return

        try:
            self._socket_conn.sendall(b'{"command": "pace_check"}\n')
            response_raw: str = self._socket_file.readline().strip()
            if not response_raw:
                return

            response: dict[str, Any] = json.loads(response_raw)
            if response.get("action") == "wait":
                duration_ms: int = response.get("duration_ms", 0)
                if duration_ms > 0:
                    time.sleep(duration_ms / 1000.0)
        except (socket.error, json.JSONDecodeError):
            # Fail-safe: if daemon is unresponsive, continue processing
            # to avoid breaking the host application.
            pass

    def get_concurrency_guidance(self) -> Literal["SCALE_DOWN", "HOLD", "SCALE_UP"]:
        """
        Queries daemon trend metrics for worker-orchestration guidance.

        Sends a ``get_guidance`` command to the daemon (§4, Command 2) and
        returns one of three symbolic directives based on the rolling-window
        temperature analysis described in §6-C:

        * ``"SCALE_DOWN"`` — thermal pressure is rising; reduce parallelism.
        * ``"SCALE_UP"``   — system has headroom; more workers are safe.
        * ``"HOLD"``       — steady state; keep current concurrency level.

        ``"HOLD"`` is also returned as a safe default when:

        * The connection to the daemon is not active.
        * The daemon is in its warm-up period (< ``trend_analysis_window_seconds``
          of data collected).
        * Any socket or JSON error occurs (*fail-safe*).

        Protocol
        --------
        * Send:    ``{"command": "get_guidance"}\\n``
        * Receive: ``{"action": "guidance_reply", "decision": "HOLD"}``

        Returns
        -------
        Literal["SCALE_DOWN", "HOLD", "SCALE_UP"]
            The concurrency directive issued by the daemon.
        """
        if not self._socket_conn or not self._socket_file:
            return "HOLD"

        try:
            self._socket_conn.sendall(b'{"command": "get_guidance"}\n')
            response_raw: str = self._socket_file.readline().strip()
            if not response_raw:
                return "HOLD"

            response: dict[str, Any] = json.loads(response_raw)
            if response.get("action") == "guidance_reply":
                decision = response.get("decision", "HOLD")
                # Validate that the daemon returned a recognised directive.
                if decision in ("SCALE_DOWN", "HOLD", "SCALE_UP"):
                    return decision  # type: ignore[return-value]
        except (socket.error, json.JSONDecodeError):
            pass

        return "HOLD"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect_to_daemon(self) -> None:
        """
        Opens a ``AF_UNIX / SOCK_STREAM`` connection to the daemon socket.

        Sets a **5-second timeout** on the socket to prevent the host
        application from hanging if the daemon becomes unresponsive mid-
        session.  The raw socket is then wrapped with
        :meth:`socket.socket.makefile` using ``'r'`` mode and UTF-8
        encoding, which provides buffered, line-oriented reading and avoids
        the stream-fragmentation bugs associated with raw ``recv()`` calls.

        Raises
        ------
        RuntimeError
            Wraps any :exc:`socket.error` with a descriptive message so
            callers do not need to import the ``socket`` module to handle
            connection failures.
        """
        try:
            self._socket_conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket_conn.settimeout(5.0)
            self._socket_conn.connect(self.socket_path)
            # makefile() provides safe, line-based reading (§5 rationale).
            self._socket_file = self._socket_conn.makefile("r", encoding="utf-8")
        except socket.error as exc:
            # Null out partially initialised state before raising.
            self._socket_conn = None
            self._socket_file = None
            raise RuntimeError(
                f"Failed to connect to ThermalPacer daemon at "
                f"'{self.socket_path}': {exc}"
            ) from exc

    def _disconnect_from_daemon(self) -> None:
        """
        Closes the buffered file wrapper and the underlying socket.

        Both resources are closed independently so that a failure on one
        does not prevent cleanup of the other.  After this method returns,
        both ``_socket_file`` and ``_socket_conn`` are ``None``, making
        subsequent guard calls no-ops (safe idempotent teardown).
        """
        if self._socket_file is not None:
            try:
                self._socket_file.close()
            except Exception:
                pass
            self._socket_file = None

        if self._socket_conn is not None:
            try:
                self._socket_conn.close()
            except socket.error:
                pass
            self._socket_conn = None

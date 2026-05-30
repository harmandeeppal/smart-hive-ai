"""
Railway inference cost controller.

Pauses/resumes the simulator and audio containers on Railway based on
dashboard session activity.  Completely no-ops when RAILWAY_API_TOKEN is
not set, so local demo and hardware deployments are unaffected.
"""
from __future__ import annotations

import os
import logging
import threading
import requests

logger = logging.getLogger(__name__)

RAILWAY_API_URL = "https://backboard.railway.app/graphql/v2"
WATCHDOG_TIMEOUT = 15 * 60  # 15 minutes

_token = os.getenv("RAILWAY_API_TOKEN", "")
_environment_id = os.getenv("RAILWAY_ENVIRONMENT_ID", "")
_simulator_service_id = os.getenv("RAILWAY_SIMULATOR_SERVICE_ID", "")
_audio_service_id = os.getenv("RAILWAY_AUDIO_SERVICE_ID", "")

_watchdog_timer: threading.Timer | None = None
_watchdog_lock = threading.Lock()
_timeout_callback = None


def _railway_enabled() -> bool:
    return bool(_token and _environment_id)


def _graphql(query: str, variables: dict | None = None) -> dict | None:
    if not _railway_enabled():
        return None
    try:
        resp = requests.post(
            RAILWAY_API_URL,
            json={"query": query, "variables": variables or {}},
            headers={"Authorization": f"Bearer {_token}", "Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.error("Railway API error: %s", exc)
        return None


_SLEEP_MUTATION = """
mutation SetSleep($environmentId: String!, $serviceId: String!, $sleep: Boolean!) {
    serviceInstanceUpdate(
        environmentId: $environmentId,
        serviceId: $serviceId,
        input: { sleepApplication: $sleep }
    )
}
"""


def _set_service_sleep(service_id: str, sleep: bool) -> None:
    if not service_id:
        return
    action = "pause" if sleep else "resume"
    result = _graphql(_SLEEP_MUTATION, {
        "environmentId": _environment_id,
        "serviceId": service_id,
        "sleep": sleep,
    })
    if result and not result.get("errors"):
        logger.info("Railway: %sd service %s", action, service_id)
    else:
        logger.warning("Railway: failed to %s service %s: %s", action, service_id, result)


def pause_demo_services() -> None:
    """Put simulator + audio containers to sleep on Railway."""
    if not _railway_enabled():
        logger.debug("Railway not configured — pause is a no-op")
        return
    logger.info("Pausing Railway demo services (session idle / ended)")
    _set_service_sleep(_simulator_service_id, True)
    _set_service_sleep(_audio_service_id, True)


def resume_demo_services() -> None:
    """Wake simulator + audio containers on Railway."""
    if not _railway_enabled():
        logger.debug("Railway not configured — resume is a no-op")
        return
    logger.info("Resuming Railway demo services (new session)")
    _set_service_sleep(_simulator_service_id, False)
    _set_service_sleep(_audio_service_id, False)


def _watchdog_fire() -> None:
    logger.info("Watchdog: no heartbeat for 15 min — pausing demo services")
    pause_demo_services()
    if _timeout_callback:
        _timeout_callback()


def reset_watchdog(on_timeout=None) -> None:
    """Start or reset the 15-minute idle watchdog."""
    global _watchdog_timer, _timeout_callback
    with _watchdog_lock:
        if _watchdog_timer is not None:
            _watchdog_timer.cancel()
        if on_timeout is not None:
            _timeout_callback = on_timeout
        _watchdog_timer = threading.Timer(WATCHDOG_TIMEOUT, _watchdog_fire)
        _watchdog_timer.daemon = True
        _watchdog_timer.start()
        logger.debug("Watchdog reset (%ds)", WATCHDOG_TIMEOUT)


def stop_watchdog() -> None:
    """Cancel the watchdog (call on clean session end)."""
    global _watchdog_timer
    with _watchdog_lock:
        if _watchdog_timer is not None:
            _watchdog_timer.cancel()
            _watchdog_timer = None
            logger.debug("Watchdog stopped")

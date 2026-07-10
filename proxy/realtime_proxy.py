#!/usr/bin/env python3
"""
MiniMax Realtime API WebSocket Proxy
====================================

Background
----------
Browsers cannot send custom headers on the native `WebSocket` constructor.
MiniMax Realtime API (`wss://api.minimax.io/ws/v1/realtime`) requires an
`Authorization: Bearer <key>` header for auth, so a browser-only client
silently fails the handshake (header is dropped, server returns 401-equivalent).

This proxy bridges the gap:
    Browser  --(ws://localhost:8765?key=...)-->  Proxy  --(wss://api.minimax.io + header)-->  MiniMax

The API key is passed via the URL query string on the client side and the
proxy attaches it as an `Authorization` header on the upstream WebSocket
handshake. Text and binary frames are relayed bidirectionally without
inspection.

Usage
-----
    cd proxy/
    ./venv/bin/python realtime_proxy.py            # foreground
    # or
    ./venv/bin/python realtime_proxy.py --port 9000  # custom port

Then in voice-buddy.html the client connects to `ws://localhost:<port>`.

Security
--------
- Binds to 127.0.0.1 only (not 0.0.0.0) — no external exposure.
- API key is redacted in logs (`Bearer ***...last4`).
- No message payload is logged (audio chunks may be large / sensitive).
- The upstream connection is closed when the client disconnects.

Author: MacD (relay for Voice Buddy V1)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
from typing import Optional
from urllib.parse import parse_qs, urlparse

import websockets
from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosed

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

UPSTREAM_URL = "wss://api.minimax.io/ws/v1/realtime?model=abab6.5s-chat"
DEFAULT_HOST = "127.0.0.1"  # loopback only — never expose to LAN
DEFAULT_PORT = 8765
ALLOWED_KEY_PREFIX = "sk-"  # reject obvious garbage early

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("minimax-proxy")


def _redact_key(key: str) -> str:
    """Return a safe-to-log representation of the API key."""
    if len(key) <= 8:
        return "***"
    return f"{key[:6]}...{key[-4:]}"


# ---------------------------------------------------------------------------
# Connection plumbing
# ---------------------------------------------------------------------------


async def _relay(client_ws: ServerConnection, upstream_ws) -> None:
    """Bidirectional frame relay between client and upstream.

    Two tasks: client→upstream and upstream→client. Whichever finishes
    first triggers cancellation of the other so a single disconnect
    tears down both sides.
    """
    async def client_to_upstream() -> None:
        try:
            async for message in client_ws:
                if isinstance(message, (bytes, bytearray)):
                    await upstream_ws.send(message)
                else:
                    await upstream_ws.send(message)
        except ConnectionClosed:
            pass
        except Exception as e:
            log.warning("client→upstream relay error: %s", e)

    async def upstream_to_client() -> None:
        try:
            async for message in upstream_ws:
                if isinstance(message, (bytes, bytearray)):
                    await client_ws.send(message)
                else:
                    await client_ws.send(message)
        except ConnectionClosed:
            pass
        except Exception as e:
            log.warning("upstream→client relay error: %s", e)

    await asyncio.gather(client_to_upstream(), upstream_to_client())


def _extract_key(client_ws: ServerConnection) -> Optional[str]:
    """Pull API key from the client request path's `?key=` query param."""
    try:
        path = client_ws.request.path if client_ws.request else ""
    except Exception:
        path = ""
    if not path:
        return None
    qs = parse_qs(urlparse(path).query)
    key = qs.get("key", [None])[0]
    return key.strip() if key else None


async def handle_client(client_ws: ServerConnection) -> None:
    """Handle one browser client: open upstream, relay, close both."""
    remote = getattr(client_ws, "remote_address", ("?", "?"))
    key = _extract_key(client_ws)

    if not key:
        log.warning("reject %s: no ?key= query param", remote)
        await client_ws.close(code=1008, reason="Missing API key (use ?key=...)")
        return

    if not key.startswith(ALLOWED_KEY_PREFIX):
        log.warning("reject %s: key %s does not start with %s",
                    remote, _redact_key(key), ALLOWED_KEY_PREFIX)
        await client_ws.close(code=1008, reason="API key must start with 'sk-'")
        return

    log.info("client %s connecting upstream with key %s", remote, _redact_key(key))

    try:
        async with websockets.connect(
            UPSTREAM_URL,
            additional_headers={"Authorization": f"Bearer {key}"},
            open_timeout=15,
            ping_interval=20,
            ping_timeout=20,
            max_size=20 * 1024 * 1024,  # 20 MiB — audio chunks can be chunky
        ) as upstream_ws:
            log.info("client %s upstream opened", remote)
            await _relay(client_ws, upstream_ws)
    except websockets.exceptions.InvalidStatus as e:
        # Most common: 401 from MiniMax because key invalid
        log.error("client %s upstream auth failed: %s", remote, e)
        await client_ws.close(code=4001, reason=f"Upstream auth failed: {e}")
    except websockets.exceptions.InvalidStatusCode as e:
        log.error("client %s upstream rejected: %s", remote, e)
        await client_ws.close(code=4002, reason=f"Upstream rejected: {e}")
    except OSError as e:
        log.error("client %s network error: %s", remote, e)
        await client_ws.close(code=4003, reason=f"Network error: {e}")
    except Exception as e:
        log.exception("client %s unexpected error: %s", remote, e)
        try:
            await client_ws.close(code=1011, reason=f"Proxy error: {type(e).__name__}")
        except Exception:
            pass
    finally:
        log.info("client %s closed", remote)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main(host: str, port: int) -> None:
    log.info("MiniMax Realtime proxy starting on ws://%s:%d", host, port)
    log.info("Upstream: %s", UPSTREAM_URL)
    log.info("Bind: 127.0.0.1 only (loopback). Ctrl-C to stop.")

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            # Windows / restricted envs — fall back to default handling
            pass

    async with serve(handle_client, host, port, max_size=20 * 1024 * 1024):
        await stop.wait()
    log.info("Proxy stopped cleanly")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="MiniMax Realtime WebSocket proxy (browser → MiniMax wss)"
    )
    p.add_argument("--host", default=DEFAULT_HOST,
                   help=f"Bind host (default {DEFAULT_HOST}; do NOT use 0.0.0.0)")
    p.add_argument("--port", type=int, default=DEFAULT_PORT,
                   help=f"Bind port (default {DEFAULT_PORT})")
    return p.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    if args.host == "0.0.0.0":
        log.warning("Refusing to bind to 0.0.0.0 — security risk. Use 127.0.0.1.")
        sys.exit(1)
    try:
        asyncio.run(main(args.host, args.port))
    except KeyboardInterrupt:
        log.info("Interrupted")
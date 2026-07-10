# MiniMax Realtime Proxy

A tiny Python WebSocket relay that lets a browser talk to MiniMax's Realtime
API (`wss://api.minimax.io/ws/v1/realtime`).

## Why this exists

The browser's native `WebSocket` constructor **does not support custom headers**.
MiniMax's Realtime API requires an `Authorization: Bearer <key>` header, so a
pure-browser client silently fails the handshake — the header is dropped and
the server returns 401-equivalent.

This proxy is the bridge:

```
Browser  ─── ws://localhost:8765?key=sk-... ──▶  Proxy
                                                   │
                                                   ▼
                                       wss://api.minimax.io/ws/v1/realtime
                                       (Authorization header attached)
```

## Setup (one-time)

```bash
cd proxy/
python3 -m venv venv
./venv/bin/pip install websockets
```

Tested with Python 3.14 + `websockets` 16.x.

## Run

```bash
./venv/bin/python realtime_proxy.py
```

Default: `ws://127.0.0.1:8765` (loopback only — never LAN-exposed).

Then open `voice-buddy.html` and click **連接**. The client connects to the
proxy, the proxy attaches the `Authorization` header upstream.

## Usage tips

- **First**: start the proxy in a terminal you'll see (logs go to stderr).
- **API key safety**: the key is passed via `?key=` query param. Logs redact it
  to `sk-cp-...last4`. Don't share your proxy terminal screen.
- **Restart**: Ctrl-C stops cleanly; restart with the same command.
- **Custom port**: `./venv/bin/python realtime_proxy.py --port 9000`.

## Security notes

- Binds to `127.0.0.1` only — refuses `--host 0.0.0.0` by design.
- No payload logging (audio chunks can be large / private).
- API key rejection is explicit: must start with `sk-` else close 1008.
- Upstream auth failure closes the client with code `4001` (visible in
  browser dev tools as a clean error toast).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Browser toast: `code 4001` | Upstream rejected the key | Check API key validity in MiniMax dashboard |
| Browser toast: `code 4003` | Network/DNS failure | Check `api.minimax.io` reachable from this Mac |
| Proxy logs `no ?key=` | Voice Buddy client didn't include key | Hard-reload `voice-buddy.html` to pick up new client code |
| `Address already in use` | Another process on port 8765 | `lsof -iTCP:8765 -sTCP:LISTEN` then kill, or use `--port` |

## File layout

```
proxy/
├── realtime_proxy.py     # The relay (≈180 lines, single file)
├── README.md             # This file
└── venv/                 # Python virtualenv (gitignored)
```
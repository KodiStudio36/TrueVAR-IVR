import asyncio
import json
import logging
import threading
from typing import Optional, Set

try:
    import websockets
    _WS_AVAILABLE = True
except ImportError:
    _WS_AVAILABLE = False

from PyQt5.QtCore import QObject, pyqtSignal
from app.injector import singleton

log = logging.getLogger(__name__)


@singleton
class WebSocketManager(QObject):
    """Asyncio WebSocket server on a background daemon thread.

    Incoming data is forwarded to the Qt thread via signals.
    Outgoing data is scheduled on the asyncio loop via run_coroutine_threadsafe.
    """

    # Emitted on the Qt thread when the core sends a message
    settings_received = pyqtSignal(dict)       # full settings dict
    event_received    = pyqtSignal(str, dict)  # (event_name, extra_data)

    HOST = 'localhost'
    PORT = 8765

    def __init__(self, host: str = HOST, port: int = PORT):
        super().__init__()
        self._host = host
        self._port = port
        self._clients: Set = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------ startup

    def start(self):
        """Spawn the background thread and start listening."""
        if not _WS_AVAILABLE:
            log.error("'websockets' is not installed — WebSocket disabled.")
            return
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="ws-server"
        )
        self._thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except Exception:
            log.exception("WebSocket server crashed")

    async def _serve(self):
        async with websockets.serve(self._handler, self._host, self._port):
            log.info(f"WebSocket listening on ws://{self._host}:{self._port}")
            await asyncio.Future()  # run forever

    # ------------------------------------------------------------------ handler

    async def _handler(self, websocket, path=""):
        self._clients.add(websocket)
        addr = getattr(websocket, 'remote_address', '?')
        log.debug(f"Client connected: {addr}")
        try:
            async for raw in websocket:
                self._dispatch(raw)
        except Exception:
            pass
        finally:
            self._clients.discard(websocket)
            log.debug(f"Client disconnected: {addr}")

    def _dispatch(self, raw: str):
        """Parse JSON and emit the right Qt signal (runs on asyncio thread)."""
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            log.warning(f"Non-JSON message ignored: {raw!r}")
            return

        msg_type = msg.get('type')
        if msg_type == 'settings':
            self.settings_received.emit(msg.get('data', {}))
        elif msg_type == 'event':
            self.event_received.emit(msg.get('event', ''), msg.get('data', {}))
        else:
            log.warning(f"Unknown message type: {msg_type!r}")

    # ------------------------------------------------------------------ outbound

    def send_event(self, event: str, data: Optional[dict] = None):
        """Broadcast an event to all connected clients (Qt-thread-safe)."""
        if not self._loop or not self._clients:
            return
        payload = json.dumps({'type': 'event', 'event': event, 'data': data or {}})
        asyncio.run_coroutine_threadsafe(self._broadcast(payload), self._loop)

    async def _broadcast(self, message: str):
        targets = list(self._clients)
        results = await asyncio.gather(
            *[c.send(message) for c in targets],
            return_exceptions=True,
        )
        for exc in results:
            if isinstance(exc, Exception):
                log.debug(f"Send failed: {exc}")
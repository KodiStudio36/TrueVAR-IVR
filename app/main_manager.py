from PyQt5.QtCore import QObject, pyqtSignal
from app.injector import singleton, Injector


@singleton
class MainManager(QObject):
    """Routes WebSocket messages ↔ Qt UI signals.

    Inbound WS events  →  Qt signals  →  MainWindow slots
    CameraManager state  →  outbound WS events  →  core app
    """

    # UI navigation
    show_settings_signal = pyqtSignal()
    hide_settings_signal = pyqtSignal()
    show_replay_signal   = pyqtSignal()
    hide_replay_signal   = pyqtSignal()

    # Recording control
    toggle_recording_signal = pyqtSignal()
    start_recording_signal  = pyqtSignal()
    stop_recording_signal   = pyqtSignal()

    _INBOUND_EVENT_MAP = {
        'start_recording':  'start_recording_signal',
        'stop_recording':   'stop_recording_signal',
        'toggle_recording': 'toggle_recording_signal',
        'show_replay':      'show_replay_signal',
        'hide_replay':      'hide_replay_signal',
        'show_settings':    'show_settings_signal',
        'hide_settings':    'hide_settings_signal',
    }

    def __init__(self):
        super().__init__()
        # Lazy imports prevent circular dependencies at module load time
        from app.websocket_manager import WebSocketManager
        from app.camera_manager    import CameraManager

        self._ws: WebSocketManager = Injector.find(WebSocketManager)
        self._ws.event_received.connect(self._on_ws_event)
        self._ws.settings_received.connect(self._on_ws_settings)

        # Mirror recording state to the core automatically
        cam: CameraManager = Injector.find(CameraManager)
        cam.is_recording_stream.connect(self._on_recording_changed)

    # ------------------------------------------------------------------ inbound

    def _on_ws_event(self, event_name: str, data: dict):
        signal_attr = self._INBOUND_EVENT_MAP.get(event_name)
        if signal_attr:
            getattr(self, signal_attr).emit()
        else:
            log.warning(f"Unhandled inbound event: {event_name!r}")

    def _on_ws_settings(self, settings: dict):
        from app.camera_manager   import CameraManager
        from app.key_bind_manager import KeyBindManager

        Injector.find(CameraManager).apply_settings(settings)

        key_bind_data = settings.get('key_binds')
        if key_bind_data:
            Injector.find(KeyBindManager).apply_settings(key_bind_data)

    # ------------------------------------------------------------------ outbound

    def _on_recording_changed(self, is_recording: bool):
        if is_recording:
            from app.camera_manager import CameraManager
            fight_num = Injector.find(CameraManager).fight_num
            self._ws.send_event('recording_started', {'fight_num': fight_num})
        else:
            self._ws.send_event('recording_stopped')

    def notify_replay_opened(self):
        self._ws.send_event('replay_opened')

    def notify_replay_closed(self):
        self._ws.send_event('replay_closed')

    def notify_error(self, message: str):
        self._ws.send_event('error', {'message': message})


import logging
log = logging.getLogger(__name__)
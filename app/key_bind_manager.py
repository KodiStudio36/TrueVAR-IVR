from app.injector import singleton
from app.settings_manager import SettingsManager, Setting


@singleton
class KeyBindManager(SettingsManager):
    """Key bindings — defaults used until core sends 'key_binds' in a settings message."""

    settings_key               = Setting("S")
    replay_key                 = Setting("R")
    record_key                 = Setting("N")
    next_camera_key            = Setting("E")
    play_pause_key             = Setting(" ")
    frame_forward_key          = Setting("Right")
    frame_backward_key         = Setting("Left")
    second_forward_key         = Setting("Shift+Right")
    second_backward_key        = Setting("Shift+Left")
    reset_zoom_key             = Setting("Escape")
    toggle_external_screen_key = Setting("W")

    def __init__(self):
        super().__init__()
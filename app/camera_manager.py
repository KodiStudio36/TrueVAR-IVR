# app/camera_manager.py
from PyQt5.QtCore import pyqtSignal, QObject
import os
import glob
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, GstVideo

from config import records_path
from app.injector import singleton
from app.settings_manager import SettingsManager, Setting


@singleton
class CameraManager(SettingsManager, QObject):
    is_recording_stream = pyqtSignal(bool)

    # Scoreboard recording size. The replay panel shows it at a fixed
    # 250 px width -> 250 x 141 logical px at 16:9. x2 for HiDPI / zoomed
    # displays gives ~500 x 281; 480 x 270 is the nearest standard 16:9 size.
    SCOREBOARD_WIDTH  = 480
    SCOREBOARD_HEIGHT = 270

    # Defaults — overridden when core sends a 'settings' message
    fps            = Setting(30)
    res_height     = Setting(720)
    camera_count   = Setting(1)
    delete_records = Setting(True)
    auto_record    = Setting(False)
    is_scoreboard  = Setting(False)   # pushed from core's CameraSettings.is_scoreboard

    def __init__(self):
        SettingsManager.__init__(self)
        QObject.__init__(self)

        self.is_recording = False
        self.fight_num    = "0"
        self.segments     = 0
        self.pipeline     = None

        if not Gst.is_initialized():
            Gst.init(None)

    @property
    def res_width(self):
        return self.res_height // 9 * 16

    def add_camera(self):
        self.camera_count += 1

    def remove_camera(self):
        if self.camera_count > 1:
            self.camera_count -= 1

    def handle_message(self, bus, message):
        if message.type == Gst.MessageType.ERROR:
            err, _ = message.parse_error()
            print(f"GStreamer error: {err.message}")
        elif message.type == Gst.MessageType.EOS:
            print("GStreamer EOS")

    def start_cameras(self):
        # All branches (cameras + scoreboard) live in ONE pipeline, so they
        # share one clock and start at the same running time. `videorate`
        # on every branch turns that into a constant frame rate: AVI has no
        # per-frame timestamps, so without it any frame dropped by the leaky
        # queue would shorten that file and shift it against the others.
        # With it, position X ms means the same moment in every file.
        pipe: str = ""

        if self._scoreboard_available():
            pipe += (
                f"{self._shmsrc(0)} ! "
                f"video/x-raw,width=1280,height=720,framerate=30/1,"
                f"format=NV12,interlace-mode=progressive ! "
                # Plain CPU scaling: at 480x270 it costs next to nothing and
                # avoids VA-memory caps negotiation with the software encoder.
                f"queue leaky=downstream ! videorate ! videoscale ! videoconvert ! "
                f"video/x-raw,width={self.SCOREBOARD_WIDTH},height={self.SCOREBOARD_HEIGHT},"
                f"framerate={self.fps}/1,format=I420 ! "
                # MJPEG: every frame is a keyframe, so replay seeks (frame
                # steps included) land exactly where the camera player is.
                f"jpegenc quality=85 ! avimux ! "
                f"filesink location={self.get_scoreboard_filepath(self.segments)} "
            )

        for idx in range(1, self.camera_count + 1):
            pipe += (
                f"{self._shmsrc(idx)} ! "
                f"video/x-raw,width={self.res_width},height={self.res_height},"
                f"framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! "
                f"queue leaky=downstream ! videorate ! vapostproc ! "
                f"vah264enc bitrate=4000 ! avimux ! "
                f"filesink location={self.get_filepath(idx, self.segments)} "
            )

        print(pipe)
        self.pipeline = Gst.parse_launch(pipe)
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.handle_message)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.is_recording = True
        self.is_recording_stream.emit(True)

    def stop_cameras(self):
        if self.pipeline:
            self.pipeline.send_event(Gst.Event.new_eos())
            self.pipeline.get_bus().timed_pop_filtered(Gst.SECOND, Gst.MessageType.EOS)
            self.pipeline.set_state(Gst.State.NULL)
            self.is_recording = False
            self.is_recording_stream.emit(False)

    def stop(self):
        if self.is_recording:
            self.stop_cameras()

    def get_filepath(self, idx, segment):
        return f"{records_path}/id{self.fight_num}_camera{idx}_segment{segment}.avi"

    def get_scoreboard_filepath(self, segment):
        return f"{records_path}/id{self.fight_num}_scoreboard_segment{segment}.avi"

    def has_scoreboard_recording(self, segment):
        return os.path.exists(self.get_scoreboard_filepath(segment))

    def _shm_socket(self, idx):
        return f"/tmp/camera{idx}_shm_socket"

    def _shmsrc(self, idx):
        return f"shmsrc socket-path={self._shm_socket(idx)} do-timestamp=true is-live=true"

    def _scoreboard_available(self):
        # Core only creates camera0's socket when is_scoreboard is on. Both
        # checks matter: a shmsrc pointing at a missing socket errors out the
        # whole pipeline and would stop the camera recordings with it.
        if not self.is_scoreboard:
            return False
        if not os.path.exists(self._shm_socket(0)):
            print("Scoreboard enabled but no scoreboard socket found — recording cameras only.")
            return False
        return True

    def new_segment(self):
        self.segments += 1

    def reset_segments(self):
        self.segments = 0

    def release_records(self):
        if self.delete_records:
            for path in glob.glob(os.path.join(records_path, '*')):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Failed to remove {path}: {e}")
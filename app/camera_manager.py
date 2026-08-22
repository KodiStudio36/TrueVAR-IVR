# app/camera_manager.py
from PyQt5.QtCore import pyqtSignal, QObject
import os
import glob
import time
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

    # Defaults — overridden when core sends a 'settings' message
    fps            = Setting(30)
    res_height     = Setting(720)
    camera_count   = Setting(1)
    delete_records = Setting(True)
    auto_record    = Setting(False)
    is_scoreboard  = Setting(False)

    def __init__(self):
        SettingsManager.__init__(self)
        QObject.__init__(self)

        self.is_recording = False
        self.fight_num    = "0"
        self.segments     = 0
        self.pipeline     = None

        # Wall-clock (epoch) time the current fight started, as told to us
        # by core in the 'start_recording' event's fight_start_epoch field.
        # Core and this app run as processes on the same machine, so their
        # time.time() epochs are directly comparable — no clock sync needed.
        self.fight_start_epoch = None
        # segment index -> epoch time.time() when that segment began recording
        self.segment_start_times = {}

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
        # Record when THIS segment actually started, so replay can later work
        # out "elapsed seconds since fight start" for any position in it.
        self.segment_start_times[self.segments] = time.time()

        pipe: str = ""

        if self.is_scoreboard:
            pipe = (
                f"{self._shmsrc(0)} ! "
                f"video/x-raw,width=1280,height=720,framerate={self.fps}/1,"
                f"format=NV12,interlace-mode=progressive ! "
                f"queue leaky=downstream ! vapostproc ! "
                f"video/x-raw,width={self.res_width // 4},height={self.res_height // 4} ! "
                f"tee name=overlay_tee "
            )

        for idx in range(1, self.camera_count + 1):
            if self.is_scoreboard:
                pipe += (
                    f"{self._shmsrc(idx)} ! "
                    f"video/x-raw,width={self.res_width},height={self.res_height},"
                    f"framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! "
                    f"queue leaky=downstream ! vapostproc ! "
                    f"compositor name=comp{idx} "
                    f"  sink_0::xpos=0 sink_0::ypos=0 "
                    f"  sink_1::xpos=10 sink_1::ypos=10 ! "
                    f"video/x-raw,width={self.res_width},height={self.res_height} ! "
                    f"vah264enc bitrate=4000 ! avimux ! "
                    f"filesink location={self.get_filepath(idx, self.segments)} "
                    f"overlay_tee. ! queue ! comp{idx}. "
                )
            else:
                pipe += (
                    f"{self._shmsrc(idx)} ! "
                    f"video/x-raw,width={self.res_width},height={self.res_height},"
                    f"framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! "
                    f"queue leaky=downstream ! vapostproc ! "
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

    def _shmsrc(self, idx):
        return f"shmsrc socket-path=/tmp/camera{idx}_shm_socket do-timestamp=true is-live=true"

    def new_segment(self):
        self.segments += 1

    def reset_segments(self):
        self.segments = 0
        self.segment_start_times = {}

    def set_fight_start_epoch(self, epoch):
        """Called by MainManager when core's 'start_recording' event arrives
        with a fight_start_epoch — this is t=0 for the scoreboard timeline.
        """
        self.fight_start_epoch = epoch

    def get_segment_start_offset(self, segment):
        """Seconds elapsed since fight start when `segment` began recording,
        or None if we don't have both timestamps yet (e.g. fight_start_epoch
        never arrived, or this segment was never actually recorded).
        """
        if self.fight_start_epoch is None:
            return None
        started_at = self.segment_start_times.get(segment)
        if started_at is None:
            return None
        return started_at - self.fight_start_epoch

    def release_records(self):
        if self.delete_records:
            for path in glob.glob(os.path.join(records_path, '*')):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Failed to remove {path}: {e}")
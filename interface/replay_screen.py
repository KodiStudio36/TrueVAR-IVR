import os
import logging
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem, QVideoWidget
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QVBoxLayout, QWidget, QPushButton, QShortcut,
    QSlider, QStyle, QHBoxLayout, QLabel, QStackedLayout, QStackedWidget, QGridLayout,
    QFrame, QSizePolicy
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtCore import QUrl, Qt, QSizeF, QEvent
from PyQt5.QtGui import QWheelEvent, QMouseEvent, QKeySequence, QFont

from app.injector import Injector
from app.camera_manager import CameraManager
from app.scoreboard_history import ScoreboardHistory
from interface.scoreboard_widget import TaekwondoScoreboard
from interface.styles import COLORS

log = logging.getLogger(__name__)

class ZoomableVideoWidget(QGraphicsView):
    def __init__(self, segments):
        super().__init__()

        self.camera_manager: CameraManager = Injector.find(CameraManager)
        self.segments = segments

        # Create a scene and a video item
        self.scene = QGraphicsScene(self)
        self.videoItem = QGraphicsVideoItem()
        self.scene.addItem(self.videoItem)

        # Set the scene on the view
        self.setScene(self.scene)

        # Set up the media player
        self.mediaPlayer = QMediaPlayer(self, QMediaPlayer.VideoSurface)
        self.mediaPlayer.setVideoOutput(self.videoItem)
        self.mediaPlayer.mediaStatusChanged.connect(self.statusChanged)

        # Set some initial zoom factor
        self.zoom_factor = 1.0

        # Dragging variables
        self.dragging = False
        self.last_mouse_pos = None

        self.filename = None

        self.setStyleSheet(f"""
            QGraphicsView {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        self.setFrameShape(QFrame.NoFrame)

        self.show()

    def resizeEvent(self, event):
        """ Resize the video item to maintain the aspect ratio 4:3 """
        view_width = self.size().width() - 2
        view_height = self.size().height() - 2

        if view_height > view_width:
            # Calculate the height for 4:3 aspect ratio
            view_height = view_width * 3 / 4

        else:
            view_width = view_height * 4 / 3

        # Set the size of the video item
        self.videoItem.setSize(QSizeF(view_width, view_height))

        # Center the video item in the scene
        self.videoItem.setPos(0, 0)

        super().resizeEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        """ Handle mouse wheel event to zoom in and out """
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        self.zoom_factor += 0.1
        self.setTransformAA()

    def zoom_out(self):
        if self.zoom_factor > 1.0:
            self.zoom_factor -= 0.1
            self.setTransformAA()

    def zoom_reset(self):
        self.zoom_factor = 1
        self.setTransformAA()

    def setTransformAA(self):
        transform = self.transform()
        transform.reset()  # Reset any previous transformations
        transform.scale(self.zoom_factor, self.zoom_factor)
        self.setTransform(transform)

    def mousePressEvent(self, event: QMouseEvent):
        """ Handle mouse press event for dragging """
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_mouse_pos = event.pos()
        elif event.button() == Qt.RightButton:
            self.zoom_reset()

    def mouseMoveEvent(self, event: QMouseEvent):
        """ Handle mouse move event for dragging """
        if self.dragging:
            # Calculate how much the mouse moved
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()

            # Scroll the scene by the delta
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

    def mouseReleaseEvent(self, event: QMouseEvent):
        """ Handle mouse release event to stop dragging """
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def statusChanged(self, status):
        if status == QMediaPlayer.EndOfMedia:
            #load back media
            self.load_video(self.filename, self.mediaPlayer.duration())
            self.mediaPlayer.play()
            self.mediaPlayer.pause()

    def play_video(self):
        if self.mediaPlayer.position() == self.mediaPlayer.duration():
            self.mediaPlayer.setPosition(0)
        self.mediaPlayer.play()

    def pause_video(self):
        self.mediaPlayer.pause()

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

    def frame_forward(self):
        current_position = self.mediaPlayer.position()
        new_position = int(current_position + 1000 / self.camera_manager.fps)
        self.mediaPlayer.setPosition(new_position)

    def frame_backward(self):
        current_position = self.mediaPlayer.position()
        new_position = int(current_position - 1000 / self.camera_manager.fps)
        self.mediaPlayer.setPosition(new_position)

    def sec_forward(self):
        current_position = self.mediaPlayer.position()
        new_position = int(current_position + 1000)
        self.mediaPlayer.setPosition(new_position)

    def sec_backward(self):
        current_position = self.mediaPlayer.position()
        new_position = int(current_position - 1000)
        self.mediaPlayer.setPosition(new_position)

    def load_video(self, filename, position=None):
        self.filename = filename
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.camera_manager.get_filepath(filename, self.segments))))

        self.mediaPlayer.play()
        self.mediaPlayer.pause()

    def keyPressEvent(self, event):
        # Ignore all key events
        event.ignore()

    def set_segments(self, segments):
        self.segments = segments


class ReplayScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.camera_manager: CameraManager = Injector.find(CameraManager)
        self.score_history = self._resolve_score_history()

        self.current_page = 1

        self.segmentBack = QPushButton()
        self.segmentBack.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.segmentBack.clicked.connect(self.seg_back)

        self.label = QLabel()
        self.label.setText("Ahoj")
        self.label.setStyleSheet("font-weight: 700;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(self.label.sizePolicy().horizontalPolicy(), self.label.sizePolicy().verticalPolicy())

        self.segmentNext = QPushButton()
        self.segmentNext.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        self.segmentNext.clicked.connect(self.seg_next)

        # Create a QhboxLayout1 for the control buttons
        hboxLayout2 = QHBoxLayout()
        hboxLayout2.setContentsMargins(0, 0, 0, 0)
        hboxLayout2.addWidget(self.segmentBack)
        hboxLayout2.addWidget(self.label, stretch=1)
        hboxLayout2.addWidget(self.segmentNext)

        # Create and add the video widget (fills whatever space isn't used by the fixed-width scoreboard)
        self.videoWidget = ZoomableVideoWidget(0)
        self.videoWidget.mediaPlayer.setPlaylist = QMediaPlaylist()
        self.videoWidget.setMinimumHeight(320)

        # Create control buttons
        self.playBtn = QPushButton()
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)

        self.frameBackward = QPushButton()
        self.frameBackward.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.frameBackward.clicked.connect(self.frame_backward)

        self.frameForward = QPushButton()
        self.frameForward.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.frameForward.clicked.connect(self.frame_forward)

        self.secondBackward = QPushButton()
        self.secondBackward.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.secondBackward.clicked.connect(self.sec_backward)

        self.secondForward = QPushButton()
        self.secondForward.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        self.secondForward.clicked.connect(self.sec_forward)

        # Create a QSlider for seeking within the video
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.sliderPressed.connect(self.sliderPressed)
        self.slider.sliderReleased.connect(self.sliderReleased)

        # Create a QhboxLayout1 for the control buttons
        hboxLayout1 = QHBoxLayout()
        hboxLayout1.setContentsMargins(0, 0, 0, 0)
        hboxLayout1.addWidget(self.playBtn)
        hboxLayout1.addWidget(self.frameBackward)
        hboxLayout1.addWidget(self.frameForward)
        hboxLayout1.addWidget(self.slider)
        hboxLayout1.addWidget(self.secondBackward)
        hboxLayout1.addWidget(self.secondForward)

        # Create a QVBoxLayout for the video widget and controls (this is the LEFT column)
        vboxLayout = QVBoxLayout()
        vboxLayout.setSpacing(10)
        vboxLayout.addLayout(hboxLayout2)
        vboxLayout.addWidget(self.videoWidget, stretch=1)
        vboxLayout.addLayout(hboxLayout1)

        left_container = QWidget()
        left_container.setLayout(vboxLayout)
        # The video column is dynamic — it grows/shrinks to fill whatever
        # space is left over once the scoreboard's fixed width is taken out.
        left_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- RIGHT column: read-only Taekwondo scoreboard on top ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.setAlignment(Qt.AlignTop)

        self.scoreboard = TaekwondoScoreboard()
        right_layout.addWidget(self.scoreboard)
        right_layout.addStretch(1)

        # Fixed width so it stays compact and never fights the video for space
        right_container.setFixedWidth(TaekwondoScoreboard.WIDTH)
        right_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Main layout: dynamic video/controls on the left, static scoreboard on the right
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        main_layout.addWidget(left_container, stretch=1)
        main_layout.addWidget(right_container, stretch=0)

        self.setLayout(main_layout)

        self.videoWidget.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.videoWidget.mediaPlayer.positionChanged.connect(self.position_changed)
        self.videoWidget.mediaPlayer.durationChanged.connect(self.duration_changed)
        self.videoWidget.mediaPlayer.seekableChanged.connect(self.seekable_changed)

        self.isPlaying = False
        self.duration = 0
        self.position = None

    # Method to play or pause the video
    def play_video(self):
        if self.videoWidget.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.videoWidget.pause_video()
            self.isPlaying = False
        else:
            self.videoWidget.play_video()
            self.isPlaying = True

    # Method to handle changes in media player state (playing or paused)
    def mediastate_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    # Method to handle changes in video position
    def position_changed(self, position):
        self.slider.setValue(position)
        self._sync_scoreboard(position)

    # Method to set the video position
    def set_position(self, position):
        self.videoWidget.set_position(position)
        self._sync_scoreboard(position)

    def seekable_changed(self):
        if self.position:
            self.set_position(self.position)

        else:
            self.set_position(self.duration-10000)


    # Method to handle changes in video duration
    def duration_changed(self, duration):
        self.slider.setRange(0, duration)
        self.duration = duration

    def sliderPressed(self):
        self.isPlayingOnSlide = False
        if self.videoWidget.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.isPlayingOnSlide = True
        
        self.videoWidget.pause_video()

    def sliderReleased(self):
        if self.isPlayingOnSlide:
            self.videoWidget.play_video()

        self.slider.setFocusPolicy(Qt.NoFocus)
        self._sync_scoreboard(self.videoWidget.mediaPlayer.position())

    def frame_forward(self):
        self.videoWidget.frame_forward()

    def frame_backward(self):
        self.videoWidget.frame_backward()

    def sec_forward(self):
        self.videoWidget.sec_forward()

    def sec_backward(self):
        self.videoWidget.sec_backward()

    # Change camera angle
    def next_page(self):
        self.current_page += 1 
        if self.current_page == self.camera_manager.camera_count +1: self.current_page = 1
        self.position = self.videoWidget.mediaPlayer.position()
        self.videoWidget.load_video(self.current_page, self.videoWidget.mediaPlayer.position())
        if self.isPlaying:
            self.videoWidget.play_video()
        self.update_label()
        self._sync_scoreboard(self.videoWidget.mediaPlayer.position())

    def seg_back(self):
        self.update_seg(self.videoWidget.segments - 1)

    def seg_next(self):
        self.update_seg(self.videoWidget.segments + 1)

    def update_seg(self, segments, position=None):
        self.segmentNext.setDisabled(self.camera_manager.segments <= segments)
        self.segmentBack.setDisabled(segments <= 0)
        self.videoWidget.set_segments(segments)
        self.position = None
        self.videoWidget.load_video(1, position)
        self.current_page = 1
        self.update_label()
        self._sync_scoreboard(self.videoWidget.mediaPlayer.position())

    def update_label(self):
        self.label.setText(f"Camera {self.current_page}, Segment {self.videoWidget.segments}")

    def start(self):
        self.position = None
        self.update_seg(self.camera_manager.segments)

    def stop_video(self):
        pass

    # ------------------------------------------------------------------ scoreboard sync

    def _resolve_score_history(self) -> ScoreboardHistory:
        """Injector.find() auto-creates and caches singletons on first use,
        so this returns the SAME ScoreboardHistory instance that
        MainManager._on_ws_event() feeds when 'score_history'/'score_event'
        arrive over the websocket — no manual registration needed.
        """
        return Injector.find(ScoreboardHistory)

    def _sync_scoreboard(self, position_ms):
        """Look up the score/penalty state for the current video position
        and push it into the read-only scoreboard widget.
        """
        if self.score_history.is_empty():
            log.debug("Scoreboard sync skipped: no history data loaded yet.")
            return

        offset = self._segment_start_offset(self.videoWidget.segments)
        if offset is None:
            log.debug(
                "Scoreboard sync skipped: no start offset for segment %s "
                "(fight_start_epoch=%s) — video position can't be mapped "
                "to fight-elapsed time yet.",
                self.videoWidget.segments,
                getattr(self.camera_manager, "fight_start_epoch", "?"),
            )
            return

        elapsed = offset + (position_ms / 1000.0)
        state = self.score_history.state_at(elapsed)
        if state is None:
            log.debug(
                "Scoreboard sync: no event at or before elapsed=%.2fs "
                "(offset=%.2fs, position=%sms, %d events loaded)",
                elapsed, offset, position_ms, len(self.score_history._events),
            )
            return

        log.debug("Scoreboard sync: elapsed=%.2fs -> %s", elapsed, state)
        self.scoreboard.sync_from_state(state)

    def _segment_start_offset(self, segment):
        """Seconds elapsed since fight start when `segment` began recording.

        Backed by CameraManager.get_segment_start_offset(), which compares
        the segment's recorded start timestamp against fight_start_epoch
        (received from core alongside the 'start_recording' event).
        """
        getter = getattr(self.camera_manager, "get_segment_start_offset", None)
        if getter is None:
            return None
        return getter(segment)
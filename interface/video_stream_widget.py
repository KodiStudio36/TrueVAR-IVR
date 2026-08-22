from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
import gi
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QMetaObject, Q_ARG
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

from PyQt5.QtWidgets import QVBoxLayout, QLabel

class VideoStreamWidget(QWidget):
    def __init__(self, pipeline_description, w, h):
        super().__init__(None)
        print(pipeline_description)
        self.pipeline_description = pipeline_description
        self.w = w
        self.h = h

        self.label = QLabel("Initializing video...")
        self.label.setFixedSize(self.w, self.h)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                background-color: #1B1F24;
                color: #9AA3AE;
                border: 1px solid #2A2F37;
                border-radius: 8px;
                font-size: 12px;
            }
        """)
        self.pipeline = None
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def start(self):
        # Create the GStreamer pipeline with specified color format
        self.pipeline = Gst.parse_launch(self.pipeline_description)
        self.appsink = self.pipeline.get_by_name("sink")
        self.appsink.set_property("emit-signals", True)
        self.appsink.set_property("sync", False)
        self.appsink.connect("new-sample", self.on_new_sample)

        # Start the pipeline
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_new_sample(self, sink):
        # Callback for new samples from GStreamer pipeline
        sample = sink.emit("pull-sample")
        if sample:
            buffer = sample.get_buffer()

            # Extract frame data from the buffer
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if success:
                # Ensure we are using the RGB format for PyQt compatibility
                frame_data = map_info.data
                image = QImage(frame_data, self.w, self.h, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                
                # Update the QLabel pixmap in a thread-safe way
                QMetaObject.invokeMethod(self.label, "setPixmap", Qt.QueuedConnection, Q_ARG(QPixmap, pixmap))
                
                buffer.unmap(map_info)
        return Gst.FlowReturn.OK

    def stop(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)
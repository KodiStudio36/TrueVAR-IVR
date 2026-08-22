import sys
import logging
import signal
from pathlib import Path
from PyQt5.QtWidgets import QApplication

# log_dir = Path.cwd() / "logs"
# log_dir.mkdir(parents=True, exist_ok=True)
# log_file = log_dir / "ivr.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    # handlers=[
    #     logging.StreamHandler(sys.stdout),        # keep printing to console
    #     logging.FileHandler(log_file, mode="a"),  # + append to file
    # ],
)
# logging.getLogger(__name__).info(f"Logging to {log_file}")


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("truevar_ivr")
    app.setDesktopFileName("truevar_ivr")

    def shutdown(*args):
        print("Received SIGTERM")
        app.quit()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # @singleton decorators fire on import and self-register in Injector.
    # Import dependency-free managers first so MainManager finds them already registered.
    from app.camera_manager    import CameraManager    # noqa: F401
    from app.key_bind_manager  import KeyBindManager   # noqa: F401
    from app.websocket_manager import WebSocketManager
    from app.main_manager      import MainManager      # noqa: F401
    from app.injector          import Injector
    from interface.main_window import MainWindow

    Injector.find(WebSocketManager).start()

    window = MainWindow()
    window.setWindowTitle("Instant Video Replay")
    window.show()

    timer = signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
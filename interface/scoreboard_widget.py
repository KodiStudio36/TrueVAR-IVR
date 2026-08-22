from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from PyQt5.QtCore import Qt


class ScoreColumn(QFrame):
    """A single competitor's read-only column (Blue or Red): points + gamjeoms.

    This is a passive display only — it shows whatever score state the
    replay is currently synced to, it does not capture or edit scores.
    Use set_score()/set_gamjeom() to update it (e.g. when the replay
    position changes to a moment with a different score).
    """

    def __init__(self, name, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.points = 0
        self.gamjeoms = 0

        self.setObjectName("scoreColumn")
        self.setStyleSheet(f"""
            QFrame#scoreColumn {{
                background-color: {color};
                border-radius: 12px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignTop)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(
            "color: white; font-weight: 800; font-size: 12px; letter-spacing: 1px; background: transparent;"
        )
        layout.addWidget(name_label)

        self.points_label = QLabel("0")
        self.points_label.setAlignment(Qt.AlignCenter)
        self.points_label.setStyleSheet(
            "color: white; font-weight: 900; font-size: 44px; background: transparent;"
        )
        layout.addWidget(self.points_label)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: rgba(255,255,255,0.25); border: none;")
        layout.addWidget(divider)

        gam_label = QLabel("GAMJEOM")
        gam_label.setAlignment(Qt.AlignCenter)
        gam_label.setStyleSheet(
            "color: rgba(255,255,255,0.85); font-weight: 700; font-size: 10px; "
            "letter-spacing: 1px; background: transparent;"
        )
        layout.addWidget(gam_label)

        self.gamjeom_label = QLabel("0")
        self.gamjeom_label.setAlignment(Qt.AlignCenter)
        self.gamjeom_label.setStyleSheet(
            "color: white; font-weight: 800; font-size: 20px; background: transparent;"
        )
        layout.addWidget(self.gamjeom_label)

    def set_score(self, points):
        self.points = points
        self.points_label.setText(str(points))

    def set_gamjeom(self, gamjeoms):
        self.gamjeoms = gamjeoms
        self.gamjeom_label.setText(str(gamjeoms))

    def reset(self):
        self.set_score(0)
        self.set_gamjeom(0)


class TaekwondoScoreboard(QFrame):
    """Compact, read-only Blue vs Red Taekwondo scoreboard.

    Reflects the score/gamjeom/round/clock state associated with the video
    currently being replayed. Fixed width by design so the video player
    next to it can take up the rest of the available space.
    """

    WIDTH = 250

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedWidth(self.WIDTH)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        title = QLabel("SCOREBOARD")
        title.setObjectName("sectionTitle")
        title.setAlignment(Qt.AlignCenter)
        outer.addWidget(title)

        # Round + clock header — sits above the point columns, styled like
        # a small stopwatch readout so it reads clearly at a glance.
        header = QHBoxLayout()
        header.setSpacing(8)

        self.round_label = QLabel("ROUND 1")
        self.round_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.round_label.setStyleSheet(
            "color: #9AA3AE; font-weight: 700; font-size: 12px; letter-spacing: 0.5px;"
        )
        header.addWidget(self.round_label)

        header.addStretch(1)

        self.clock_label = QLabel("--:--")
        self.clock_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.clock_label.setStyleSheet(
            "color: #F5F6F7; font-weight: 800; font-size: 16px; "
            "font-family: 'Consolas', 'Menlo', monospace;"
        )
        header.addWidget(self.clock_label)

        outer.addLayout(header)

        columns = QHBoxLayout()
        columns.setSpacing(10)
        self.blue = ScoreColumn("CHUNG", "#2F6FE4")
        self.red = ScoreColumn("HONG", "#E5484D")
        columns.addWidget(self.blue)
        columns.addWidget(self.red)
        outer.addLayout(columns)

    def set_round(self, round_num):
        self.round_label.setText(f"ROUND {round_num}")

    def set_clock(self, clk):
        self.clock_label.setText(clk or "--:--")

    def set_scores(self, blue_points, blue_gamjeom, red_points, red_gamjeom):
        """Sync just the point/gamjeom columns to a specific point in the match/replay."""
        self.blue.set_score(blue_points)
        self.blue.set_gamjeom(blue_gamjeom)
        self.red.set_score(red_points)
        self.red.set_gamjeom(red_gamjeom)

    def sync_from_state(self, state: dict):
        """Sync everything (round, clock, points, gamjeoms) from one
        ScoreEvent-shaped dict, e.g. straight out of ScoreboardHistory.state_at().
        """
        self.set_round(state.get("round", 1))
        self.set_clock(state.get("clk", ""))
        self.set_scores(
            state.get("blue_points", 0), state.get("blue_penalties", 0),
            state.get("red_points", 0), state.get("red_penalties", 0),
        )

    def reset(self):
        self.set_round(1)
        self.set_clock("")
        self.blue.reset()
        self.red.reset()
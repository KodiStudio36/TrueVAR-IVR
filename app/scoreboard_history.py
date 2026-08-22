"""Client-side (IVR app) holder for the scoreboard timeline sent by core.

Wire this into whatever receives inbound websocket messages in this app
(the counterpart to IVRPlugin's `send_event` on the core side — not among
the uploaded files, so hook the two calls below into it):

  - on a "show_replay" event: call
        scoreboard_history.set_history(data.get("score_history", []))
    so the full timeline for the fight about to be replayed is loaded.

  - on a "score_event" event (live, while recording): call
        scoreboard_history.append_event(data)
    to keep a rolling live buffer even before replay is opened.

`state_at(t)` then answers "what was the score at elapsed second t of the
fight" with O(log n) lookup — this is what replay_screen.py calls as the
video position changes.
"""
from bisect import bisect_right
from typing import Optional


class ScoreboardHistory:
    def __init__(self):
        self.match_id = None
        self._events: list[dict] = []          # sorted ascending by "t"
        self._times: list[float] = []           # parallel list, kept in sync for bisect

    def set_history(self, events: list[dict], match_id=None) -> None:
        self.match_id = match_id
        self._events = sorted(events, key=lambda e: e["t"])
        self._times = [e["t"] for e in self._events]

    def append_event(self, event: dict) -> None:
        # Events stream in chronological order already; append is O(1).
        self._events.append(event)
        self._times.append(event["t"])

    def clear(self) -> None:
        self.match_id = None
        self._events = []
        self._times = []

    def is_empty(self) -> bool:
        return not self._events

    def state_at(self, t: float) -> Optional[dict]:
        """Score/penalty state at or just before elapsed time t (seconds
        since fight start). Returns None if there's no data yet for that t.
        """
        if not self._events:
            return None
        idx = bisect_right(self._times, t) - 1
        if idx < 0:
            return None
        return self._events[idx]
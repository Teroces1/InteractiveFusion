from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Literal

from leapc_cffi import libleapc as LeapC, ffi


HandType = Literal["left", "right"]
FingerName = Literal["thumb", "index", "middle", "ring", "pinky"]


@dataclass
class Vec3:
    x: float
    y: float
    z: float


@dataclass
class HandData:
    hand_type: HandType
    palm: Vec3
    fingers: Dict[FingerName, Vec3]


@dataclass
class FrameData:
    hands: Dict[HandType, HandData]


class LeapController:
    """
    Thin wrapper around LeapC that:
      - Manages connection lifecycle
      - Polls tracking events
      - Exposes palm + 5 fingertip positions for both hands
    """

    def __init__(self) -> None:
        # Allocate connection pointer and create/open connection
        self._conn_ptr = ffi.new("LEAP_CONNECTION*")
        result = LeapC.LeapCreateConnection(ffi.NULL, self._conn_ptr)
        if result != LeapC.eLeapRS_Success:
            raise RuntimeError(f"LeapCreateConnection failed with code {int(result)}")

        result = LeapC.LeapOpenConnection(self._conn_ptr[0])
        if result != LeapC.eLeapRS_Success:
            raise RuntimeError(f"LeapOpenConnection failed with code {int(result)}")

        # Allocate a single message struct and set its size before polling
        self._msg = ffi.new("LEAP_CONNECTION_MESSAGE *")
        self._msg[0].size = ffi.sizeof("LEAP_CONNECTION_MESSAGE")

    # --- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        if self._conn_ptr is not None:
            LeapC.LeapCloseConnection(self._conn_ptr[0])
            self._conn_ptr = None

    def __enter__(self) -> "LeapController":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # --- public API --------------------------------------------------------

    def poll_frame(self, timeout_ms: int = 1000) -> Optional[FrameData]:
        """
        Polls the Leap service once.

        Returns:
            FrameData if a tracking event is received within timeout,
            otherwise None (on timeout or non-tracking events).
        """
        result = LeapC.LeapPollConnection(self._conn_ptr[0], timeout_ms, self._msg)

        if result == LeapC.eLeapRS_Timeout:
            return None
        if result != LeapC.eLeapRS_Success:
            # You can choose to raise instead if you want strict behavior
            return None

        evt_type = self._msg[0].type

        if evt_type == LeapC.eLeapEventType_Tracking:
            tracking_evt = self._msg[0].tracking_event[0]
            return self._parse_tracking_event(tracking_evt)

        # Ignore non-tracking events for this wrapper
        return None

    # --- helpers -----------------------------------------------------------

    def _parse_tracking_event(self, evt) -> FrameData:
        hands: Dict[HandType, HandData] = {}

        for i in range(evt.nHands):
            hand = evt.pHands[i]
            hand_type: HandType = (
                "left" if hand.type == LeapC.eLeapHandType_Left else "right"
            )

            palm_pos = hand.palm.position
            palm = Vec3(float(palm_pos.x), float(palm_pos.y), float(palm_pos.z))

            # Fingertips: distal.next_joint for each finger
            # Field names follow LeapC hand struct: thumb, index, middle, ring, pinky
            fingers: Dict[FingerName, Vec3] = {}

            def fingertip(joint) -> Vec3:
                return Vec3(float(joint.x), float(joint.y), float(joint.z))

            fingers["thumb"] = fingertip(hand.thumb.distal.next_joint)
            fingers["index"] = fingertip(hand.index.distal.next_joint)
            fingers["middle"] = fingertip(hand.middle.distal.next_joint)
            fingers["ring"] = fingertip(hand.ring.distal.next_joint)
            fingers["pinky"] = fingertip(hand.pinky.distal.next_joint)

            hands[hand_type] = HandData(
                hand_type=hand_type,
                palm=palm,
                fingers=fingers,
            )

        return FrameData(hands=hands)

    # --- convenience accessors --------------------------------------------

    def get_hand(self, hand_type: HandType, timeout_ms: int = 1000) -> Optional[HandData]:
        """
        Polls once and returns the requested hand if present.
        """
        frame = self.poll_frame(timeout_ms=timeout_ms)
        if frame is None:
            return None
        return frame.hands.get(hand_type)

    def get_palm_position(
        self, hand_type: HandType, timeout_ms: int = 1000
    ) -> Optional[Vec3]:
        """
        Returns palm position for the requested hand, or None if not available.
        """
        hand = self.get_hand(hand_type, timeout_ms=timeout_ms)
        return hand.palm if hand else None

    def get_finger_position(
        self,
        hand_type: HandType,
        finger: FingerName,
        timeout_ms: int = 1000,
    ) -> Optional[Vec3]:
        """
        Returns fingertip position for a given hand and finger, or None if not available.
        """
        hand = self.get_hand(hand_type, timeout_ms=timeout_ms)
        if not hand:
            return None
        return hand.fingers.get(finger)


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    with LeapController() as lc:
        print("Connection opened. Move your hands over the device...")

        while True:
            frame = lc.poll_frame(timeout_ms=1000)
            if frame is None:
                continue

            for hand_type, hand in frame.hands.items():
                print(f"{hand_type.upper()} palm: ({hand.palm.x:.1f}, {hand.palm.y:.1f}, {hand.palm.z:.1f})")
                for fname, fpos in hand.fingers.items():
                    print(
                        f"  {hand_type.upper()} {fname:6s}: "
                        f"({fpos.x:.1f}, {fpos.y:.1f}, {fpos.z:.1f})"
                    )

            time.sleep(0.05)

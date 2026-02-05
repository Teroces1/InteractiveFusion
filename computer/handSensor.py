"""
LeapHandTracker
- Requires Leap/Ultraleap Python bindings available as `Leap` (common in Leap SDK installs).
- Keeps a live copy of the latest frame and provides get_hands() to fetch structured hand data.

Position units: millimeters (Leap native).
"""

import time
import threading

# try common module names used in examples
try:
    import Leap                    # legacy Leap Python bindings
except Exception as e:
    raise ImportError(
        "Could not import Leap module. Install the Ultraleap/Leap Python SDK or "
        "ensure your Python interpreter can import the Leap library. See Ultraleap docs."
    ) from e


class _FrameListener(Leap.Listener):
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self.latest_frame = None
        self.connected = False

    def on_connect(self, controller):
        self.connected = True
        # enable gestures if you want them:
        # controller.enable_gesture(Leap.Gesture.TYPE_SWIPE)
        print("[Leap] Connected")

    def on_disconnect(self, controller):
        self.connected = False
        print("[Leap] Disconnected")

    def on_frame(self, controller):
        frame = controller.frame()
        with self._lock:
            # copy the frame reference (Leap frames are lightweight objects)
            self.latest_frame = frame

    def get_frame(self):
        with self._lock:
            return self.latest_frame


def _vec_to_tuple(v):
    """Convert Leap.Vector to (x,y,z) tuple. Accepts plain Python sequences too."""
    try:
        return (float(v.x), float(v.y), float(v.z))
    except Exception:
        # if v is already tuple/list
        return tuple(map(float, v))


class LeapHandTracker:
    """
    High-level tracker class.

    Usage:
        tracker = LeapHandTracker()
        tracker.start()
        time.sleep(0.5)  # give it a moment to gather frames
        hands = tracker.get_hands()
        tracker.stop()
    """

    BONE_NAMES = {
        Leap.Bone.TYPE_METACARPAL: "metacarpal",
        Leap.Bone.TYPE_PROXIMAL: "proximal",
        Leap.Bone.TYPE_INTERMEDIATE: "intermediate",
        Leap.Bone.TYPE_DISTAL: "distal",
    }

    def __init__(self, auto_start=False):
        self._controller = Leap.Controller()
        self._listener = _FrameListener()
        self._started = False
        if auto_start:
            self.start()

    def start(self):
        if not self._started:
            self._controller.add_listener(self._listener)
            self._started = True
            # wait a short while for initial frames
            t0 = time.time()
            while time.time() - t0 < 1.0:
                if self._listener.get_frame() is not None:
                    break
                time.sleep(0.01)

    def stop(self):
        if self._started:
            self._controller.remove_listener(self._listener)
            self._started = False

    def get_hands(self):
        """
        Returns a dict keyed by hand.id. Each value is:
        {
            'id': hand.id,
            'type': 'left'/'right',
            'palm_pos': (x,y,z),
            'palm_normal': (x,y,z),
            'palm_direction': (x,y,z),
            'grab_strength': float,
            'pinch_strength': float,
            'fingers': [
                {
                    'id': finger.id,
                    'type': finger.type,  # 0..4 (thumb..pinky) per API
                    'tip': (x,y,z),
                    'bones': {
                        'metacarpal': {'prev_joint':(), 'next_joint':(), 'center':()},
                        'proximal': {...},
                        ...
                    }
                }, ...
            ]
        }
        """
        frame = self._listener.get_frame()
        if frame is None:
            return {}

        hands_out = {}
        for hand in frame.hands:
            hand_dict = {
                "id": hand.id,
                "type": "left" if hand.is_left else "right",
                "palm_pos": _vec_to_tuple(hand.palm_position),
                "palm_normal": _vec_to_tuple(hand.palm_normal),
                "palm_direction": _vec_to_tuple(hand.direction),
                "grab_strength": float(hand.grab_strength),
                "pinch_strength": float(getattr(hand, "pinch_strength", 0.0)),
                "fingers": []
            }

            # iterate fingers
            for finger in hand.fingers:
                finger_dict = {
                    "id": finger.id,
                    "type": int(finger.type),  # 0 thumb ... 4 pinky
                    "tip": _vec_to_tuple(finger.tip_position),
                    "bones": {}
                }

                # Leap finger.bone(bone_type) for TYPE_METACARPAL .. TYPE_DISTAL
                for bone_type in (Leap.Bone.TYPE_METACARPAL,
                                  Leap.Bone.TYPE_PROXIMAL,
                                  Leap.Bone.TYPE_INTERMEDIATE,
                                  Leap.Bone.TYPE_DISTAL):
                    bone = finger.bone(bone_type)
                    name = self.BONE_NAMES.get(bone_type, str(bone_type))
                    prev_j = _vec_to_tuple(bone.prev_joint)
                    next_j = _vec_to_tuple(bone.next_joint)
                    # bone center as midpoint
                    center = tuple((a + b) / 2.0 for a, b in zip(prev_j, next_j))
                    finger_dict["bones"][name] = {
                        "prev_joint": prev_j,
                        "next_joint": next_j,
                        "center": center,
                        "length": float(bone.length) if hasattr(bone, "length") else None
                    }

                hand_dict["fingers"].append(finger_dict)

            hands_out[hand.id] = hand_dict

        return hands_out


# Example usage
if __name__ == "__main__":
    tracker = LeapHandTracker()
    try:
        tracker.start()
        print("Listening... (press Ctrl+C to exit)")
        while True:
            hands = tracker.get_hands()
            if hands:
                for hid, h in hands.items():
                    print(f"Hand {hid} ({h['type']}) palm at {h['palm_pos']}")
                    for finger in h["fingers"]:
                        print(f"  Finger {finger['type']} tip {finger['tip']}")
                        # print joint centers
                        for bname, bdata in finger["bones"].items():
                            print(f"    {bname} center {bdata['center']}")
            else:
                print("No hands detected.")
            time.sleep(0.08)  # ~12 Hz polling; frames arrive at ~100Hz, so we sample
    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        tracker.stop()

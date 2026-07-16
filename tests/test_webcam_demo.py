from scripts import webcam_demo


class FakeCapture:
    def __init__(self, frames, opened=True):
        self.frames = iter(frames)
        self.opened = opened
        self.released = False

    def isOpened(self):
        return self.opened

    def read(self):
        return True, next(self.frames)

    def release(self):
        self.released = True


class FakeCV:
    COLOR_BGR2RGB = 4

    def __init__(self, capture, keys):
        self.capture = capture
        self.keys = iter(keys)
        self.converted = []
        self.shown = []
        self.destroyed = False

    def VideoCapture(self, camera):
        self.camera = camera
        return self.capture

    def cvtColor(self, frame, conversion):
        self.converted.append((frame, conversion))
        return f"rgb:{frame}"

    def imshow(self, title, frame):
        self.shown.append((title, frame))

    def waitKey(self, delay):
        assert delay == 1
        return next(self.keys)

    def destroyAllWindows(self):
        self.destroyed = True


class FakeReader:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def decode_array(self, frame, **kwargs):
        self.calls.append((frame, kwargs))
        return self.results


def test_parse_possible_formats():
    assert webcam_demo.parse_possible_formats(None) is None
    assert webcam_demo.parse_possible_formats(" QR_CODE, DATA_MATRIX ") == [
        "QR_CODE",
        "DATA_MATRIX",
    ]


def test_run_demo_decodes_sampled_frame_and_releases_camera():
    capture = FakeCapture(["frame-1"])
    cv = FakeCV(capture, [ord("q")])
    reader = FakeReader([{"parsed_text": "demo payload"}])
    output = []

    webcam_demo.run_demo(
        camera=2,
        interval=0.75,
        multi=False,
        try_harder=False,
        possible_formats=["QR_CODE"],
        cv_module=cv,
        reader=reader,
        monotonic=lambda: 10.0,
        output=output.append,
    )

    assert cv.camera == 2
    assert reader.calls == [
        (
            "rgb:frame-1",
            {
                "multi": False,
                "try_harder": False,
                "possible_formats": ["QR_CODE"],
            },
        )
    ]
    assert output == ["demo payload"]
    assert capture.released
    assert cv.destroyed


def test_run_demo_respects_interval_between_decode_attempts():
    capture = FakeCapture(["frame-1", "frame-2"])
    cv = FakeCV(capture, [-1, 27])
    reader = FakeReader([])
    times = iter([1.0, 1.1])

    webcam_demo.run_demo(
        interval=0.5,
        cv_module=cv,
        reader=reader,
        monotonic=lambda: next(times),
    )

    assert [frame for frame, _kwargs in reader.calls] == ["rgb:frame-1"]
    assert [frame for _title, frame in cv.shown] == ["frame-1", "frame-2"]
    assert capture.released
    assert cv.destroyed


def test_run_demo_reports_unavailable_camera():
    capture = FakeCapture([], opened=False)
    cv = FakeCV(capture, [])

    try:
        webcam_demo.run_demo(cv_module=cv, reader=FakeReader([]))
    except RuntimeError as exc:
        assert str(exc) == "Could not open camera 0"
    else:
        raise AssertionError("run_demo should reject an unavailable camera")

    assert capture.released

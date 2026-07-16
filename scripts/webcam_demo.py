"""Small OpenCV webcam demonstration using pyzxing's existing one-shot API."""

import argparse
import time

from pyzxing import BarCodeReader


def _load_cv2():
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is required for the webcam demo; install opencv-python"
        ) from exc
    return cv2


def parse_possible_formats(value):
    if not value:
        return None
    formats = [item.strip() for item in value.split(",") if item.strip()]
    return formats or None


def _payloads(results):
    payloads = []
    for result in results:
        payload = result.get("parsed_text") or result.get("text")
        if payload is None:
            payload = result.get("parsed") or result.get("raw")
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8", errors="replace")
        if payload is not None and payload not in payloads:
            payloads.append(payload)
    return payloads


def run_demo(
    *,
    camera=0,
    interval=0.5,
    multi=True,
    try_harder=True,
    possible_formats=None,
    cv_module=None,
    reader=None,
    monotonic=time.monotonic,
    output=print,
):
    """Preview a camera and periodically decode the current frame.

    This deliberately composes ``cv2.VideoCapture`` with ``decode_array()``.
    It does not add a persistent JVM or a streaming API to pyzxing.
    """
    if interval < 0:
        raise ValueError("interval must be non-negative")

    cv = cv_module or _load_cv2()
    barcode_reader = reader or BarCodeReader()
    capture = cv.VideoCapture(camera)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"Could not open camera {camera}")

    next_scan_at = 0.0
    visible_payloads = set()
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"Could not read a frame from camera {camera}")

            now = monotonic()
            if now >= next_scan_at:
                rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                results = barcode_reader.decode_array(
                    rgb_frame,
                    multi=multi,
                    try_harder=try_harder,
                    possible_formats=possible_formats,
                )
                payloads = _payloads(results)
                for payload in payloads:
                    if payload not in visible_payloads:
                        output(payload)
                visible_payloads = set(payloads)
                next_scan_at = now + interval

            cv.imshow("pyzxing webcam demo (q or Esc to quit)", frame)
            key = cv.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                return
    finally:
        capture.release()
        cv.destroyAllWindows()


def build_parser():
    parser = argparse.ArgumentParser(
        description="Decode periodically sampled webcam frames with pyzxing"
    )
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index")
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Minimum seconds between decode attempts",
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Return at most one barcode per sampled frame",
    )
    parser.add_argument(
        "--no-try-harder",
        action="store_true",
        help="Disable ZXing's TRY_HARDER hint",
    )
    parser.add_argument(
        "--possible-formats",
        help="Comma-separated ZXing formats, for example QR_CODE,DATA_MATRIX",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run_demo(
            camera=args.camera,
            interval=args.interval,
            multi=not args.single,
            try_harder=not args.no_try_harder,
            possible_formats=parse_possible_formats(args.possible_formats),
        )
    except (RuntimeError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    main()

import base64
import hashlib
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from pyzxing import BarCodeReader, DecodeError, DecodeTimeoutError, FileTooLargeError
from pyzxing.config import Config
from pyzxing.utils import get_file


def make_reader(tmp_path, **kwargs):
    jar = tmp_path / "zxing.jar"
    jar.write_bytes(b"jar")
    return BarCodeReader(jar_path=jar, java_command="java", **kwargs)


def result_record(input_uri, **overrides):
    record = {
        "schema_version": 1,
        "status": "ok",
        "input": input_uri,
        "format": "QR_CODE",
        "type": "TEXT",
        "text": "hello",
        "parsed_text": "hello",
        "raw_bytes_base64": base64.b64encode(b"raw codewords").decode("ascii"),
        "num_bits": 104,
        "byte_segments_base64": [],
        "points": [[1.5, 2.0], [3, 4]],
        "orientation": 0,
        "orientation_source": "derived",
        "metadata": {},
        "error": None,
    }
    record.update(overrides)
    return record


def not_found_record(input_uri):
    return result_record(
        input_uri,
        status="not_found",
        format=None,
        type=None,
        text=None,
        parsed_text=None,
        raw_bytes_base64=None,
        num_bits=None,
        byte_segments_base64=[],
        points=[],
        orientation=None,
        orientation_source="unavailable",
        metadata={},
    )


def error_record(input_uri, code="INVALID_IMAGE", message="Could not load image"):
    return result_record(
        input_uri,
        status="error",
        format=None,
        type=None,
        text=None,
        parsed_text=None,
        raw_bytes_base64=None,
        num_bits=None,
        byte_segments_base64=[],
        points=[],
        orientation=None,
        orientation_source="unavailable",
        metadata={},
        error={"code": code, "message": message},
    )


def jsonl(*records):
    return b"\n".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        for record in records
    ) + b"\n"


def test_decode_uses_argv_without_a_shell(monkeypatch, tmp_path):
    image = tmp_path / "image; touch SHOULD_NOT_RUN.png"
    image.write_bytes(b"image")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            returncode=0,
            stdout=jsonl(not_found_record(command[3])),
            stderr=b"",
        )

    monkeypatch.setattr("pyzxing.reader.subprocess.run", fake_run)
    results = make_reader(tmp_path).decode(str(image))
    assert results == [{"filename": Path(image).resolve().as_uri().encode("utf-8")}]
    assert isinstance(captured["command"], list)
    assert captured["command"][3] == Path(image).resolve().as_uri()
    assert "shell" not in captured["kwargs"]


def test_decode_timeout_is_reported(monkeypatch, tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")

    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr("pyzxing.reader.subprocess.run", fake_run)
    with pytest.raises(DecodeTimeoutError, match="1s timeout"):
        make_reader(tmp_path, timeout=1).decode(str(image))


def test_nonzero_without_error_record_is_a_protocol_error(monkeypatch, tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")
    failed = SimpleNamespace(returncode=2, stdout=b"", stderr=b"bad input")
    monkeypatch.setattr("pyzxing.reader.subprocess.run", lambda *a, **k: failed)

    with pytest.raises(DecodeError, match="protocol violation.*bad input"):
        make_reader(tmp_path).decode(str(image))


def test_structured_java_error_preserves_stable_code(monkeypatch, tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")

    def fake_run(command, **kwargs):
        return SimpleNamespace(
            returncode=3,
            stdout=jsonl(error_record(command[3], "INVALID_IMAGE", "broken image")),
            stderr=b"diagnostic only",
        )

    monkeypatch.setattr("pyzxing.reader.subprocess.run", fake_run)
    with pytest.raises(DecodeError, match="INVALID_IMAGE: broken image") as raised:
        make_reader(tmp_path).decode(str(image))
    assert raised.value.code == "INVALID_IMAGE"


def test_jsonl_maps_legacy_and_additive_fields(monkeypatch, tmp_path):
    image = tmp_path / "issue-34.png"
    image.write_bytes(b"image")
    payload = "测试：生产许可证"
    gb18030_bytes = payload.encode("gb18030")

    def fake_run(command, **kwargs):
        record = result_record(
            command[3],
            text=payload,
            parsed_text=payload,
            raw_bytes_base64=base64.b64encode(b"\x01\x02").decode("ascii"),
            byte_segments_base64=[base64.b64encode(gb18030_bytes).decode("ascii")],
            num_bits=16,
            orientation=270,
            orientation_source="derived",
            metadata={
                "character_set": "GB18030",
                "symbology_identifier": "]Q1",
                "errors_corrected": 2,
                "erasures_corrected": 1,
                "future_metadata": "ignored",
            },
            future_protocol_field="ignored",
        )
        return SimpleNamespace(returncode=0, stdout=jsonl(record), stderr=b"")

    monkeypatch.setattr("pyzxing.reader.subprocess.run", fake_run)
    result = make_reader(tmp_path).decode(
        str(image), character_set="GB18030", possible_formats=["QR_CODE"]
    )[0]

    assert result["filename"] == Path(image).resolve().as_uri().encode("utf-8")
    assert result["format"] == b"QR_CODE"
    assert result["type"] == b"TEXT"
    assert result["raw"] == payload.encode("utf-8")
    assert result["parsed"] == payload.encode("utf-8")
    assert result["text"] == payload
    assert result["parsed_text"] == payload
    assert result["raw_bytes"] == b"\x01\x02"
    assert result["byte_segments"] == [gb18030_bytes]
    assert result["points"] == [(1.5, 2.0), (3, 4)]
    assert result["num_bits"] == 16
    assert result["orientation"] == 270
    assert result["orientation_source"] == "derived"
    assert result["metadata"] == {
        "character_set": "GB18030",
        "errors_corrected": 2,
        "erasures_corrected": 1,
        "symbology_identifier": "]Q1",
    }


def test_decode_passes_exact_hint_argv(monkeypatch, tmp_path):
    image = tmp_path / "issue #38 100%.png"
    image.write_bytes(b"image")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        return SimpleNamespace(
            returncode=0,
            stdout=jsonl(result_record(command[3], text="1982", parsed_text="1982")),
            stderr=b"",
        )

    monkeypatch.setattr("pyzxing.reader.subprocess.run", fake_run)
    result = make_reader(tmp_path).decode(
        str(image),
        multi=False,
        try_harder=False,
        pure_barcode=True,
        character_set="UTF-8",
        possible_formats=("QR_CODE", "DATA_MATRIX"),
    )

    assert result[0]["parsed"] == b"1982"
    assert captured["command"] == [
        "java",
        "-jar",
        str(tmp_path / "zxing.jar"),
        Path(image).resolve().as_uri(),
        "--pure-barcode",
        "--character-set",
        "UTF-8",
        "--possible-formats",
        "QR_CODE,DATA_MATRIX",
    ]


def test_decode_defaults_enable_multi_and_try_harder(monkeypatch, tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        return SimpleNamespace(
            returncode=0,
            stdout=jsonl(not_found_record(command[3])),
            stderr=b"",
        )

    monkeypatch.setattr("pyzxing.reader.subprocess.run", fake_run)
    make_reader(tmp_path).decode(str(image))
    assert captured["command"][-2:] == ["--multi", "--try-harder"]


@pytest.mark.parametrize(
    "stdout, message",
    [
        (b"", "zero records"),
        (b"not json\n", "not valid JSON"),
        (b"\xff\n", "not valid UTF-8"),
    ],
)
def test_protocol_rejects_invalid_jsonl(monkeypatch, tmp_path, stdout, message):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")
    failed = SimpleNamespace(returncode=0, stdout=stdout, stderr=b"")
    monkeypatch.setattr("pyzxing.reader.subprocess.run", lambda *a, **k: failed)

    with pytest.raises(DecodeError, match=message):
        make_reader(tmp_path).decode(str(image))


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"schema_version": 2}, "unsupported schema_version"),
        ({"raw_bytes_base64": "%%%"}, "invalid Base64"),
        ({"points": [[1, True]]}, "finite"),
        ({"points": [[1, 10 ** 1000]]}, "finite"),
        ({"orientation": 45}, "orientation"),
        ({"orientation": None, "orientation_source": "derived"}, "non-null"),
        ({"metadata": {"issue_number": True}}, "wrong type"),
    ],
)
def test_protocol_validates_result_fields(monkeypatch, tmp_path, overrides, message):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")

    def fake_run(command, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=jsonl(result_record(command[3], **overrides)),
            stderr=b"",
        )

    monkeypatch.setattr("pyzxing.reader.subprocess.run", fake_run)
    with pytest.raises(DecodeError, match=message):
        make_reader(tmp_path).decode(str(image))


def test_protocol_rejects_mismatched_input(monkeypatch, tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")
    process = SimpleNamespace(
        returncode=0,
        stdout=jsonl(result_record("file:///different.png")),
        stderr=b"",
    )
    monkeypatch.setattr("pyzxing.reader.subprocess.run", lambda *a, **k: process)

    with pytest.raises(DecodeError, match="input does not match"):
        make_reader(tmp_path).decode(str(image))


def test_protocol_rejects_unknown_error_code(monkeypatch, tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")

    def fake_run(command, **kwargs):
        return SimpleNamespace(
            returncode=4,
            stdout=jsonl(error_record(command[3], "FUTURE_ERROR", "unsupported")),
            stderr=b"",
        )

    monkeypatch.setattr("pyzxing.reader.subprocess.run", fake_run)
    with pytest.raises(DecodeError, match="unsupported error code"):
        make_reader(tmp_path).decode(str(image))


def test_protocol_rejects_mixed_statuses(monkeypatch, tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")

    def fake_run(command, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=jsonl(result_record(command[3]), not_found_record(command[3])),
            stderr=b"",
        )

    monkeypatch.setattr("pyzxing.reader.subprocess.run", fake_run)
    with pytest.raises(DecodeError, match="may not be mixed"):
        make_reader(tmp_path).decode(str(image))


def test_protocol_preserves_multi_result_order(monkeypatch, tmp_path):
    image = tmp_path / "multi.png"
    image.write_bytes(b"image")

    def fake_run(command, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=jsonl(
                result_record(command[3], text="first", parsed_text="first"),
                result_record(command[3], text="second", parsed_text="second"),
            ),
            stderr=b"",
        )

    monkeypatch.setattr("pyzxing.reader.subprocess.run", fake_run)
    results = make_reader(tmp_path).decode(str(image))
    assert [result["text"] for result in results] == ["first", "second"]


@pytest.mark.parametrize(
    "kwargs, exception",
    [
        ({"multi": 1}, TypeError),
        ({"try_harder": "yes"}, TypeError),
        ({"pure_barcode": None}, TypeError),
        ({"character_set": ""}, ValueError),
        ({"possible_formats": []}, ValueError),
        ({"possible_formats": ["QR_CODE\x00"]}, ValueError),
        ({"possible_formats": ["二维码"]}, ValueError),
    ],
)
def test_decode_validates_hints_before_java(tmp_path, kwargs, exception):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")
    with pytest.raises(exception):
        make_reader(tmp_path).decode(str(image), **kwargs)


def test_explicit_jar_path_is_used(tmp_path):
    explicit = tmp_path / "explicit.jar"
    explicit.write_bytes(b"explicit")
    reader = BarCodeReader(jar_path=explicit, java_command="java")
    assert reader._ensure_jar() == str(explicit)


def test_production_reader_ignores_ci_test_environment(monkeypatch, tmp_path):
    test_jar = tmp_path / "ci.jar"
    built_jar = tmp_path / Config.JAR_FILENAME
    test_jar.write_bytes(b"ci")
    built_jar.write_bytes(b"built")
    monkeypatch.setenv("PYZXING_TEST_JAR", str(test_jar))
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    reader = BarCodeReader(build_dir=tmp_path, java_command="java")
    assert reader._ensure_jar() == str(built_jar)


def test_decode_array_forwards_keyword_hints(monkeypatch, tmp_path):
    class Array:
        shape = (1, 1)

    def imwrite(filename, image):
        Path(filename).write_bytes(b"temporary image")
        return True

    monkeypatch.setitem(sys.modules, "cv2", SimpleNamespace(imwrite=imwrite))
    monkeypatch.setattr(Config, "TEMP_DIR", str(tmp_path))
    reader = make_reader(tmp_path)
    captured = {}

    def fake_decode(filename, **kwargs):
        captured["filename"] = filename
        captured["kwargs"] = kwargs
        return ["decoded"]

    monkeypatch.setattr(reader, "decode", fake_decode)
    result = reader.decode_array(
        Array(),
        multi=False,
        try_harder=False,
        pure_barcode=True,
        character_set="GB18030",
        possible_formats=["QR_CODE"],
    )

    assert result == ["decoded"]
    assert captured["kwargs"] == {
        "multi": False,
        "try_harder": False,
        "pure_barcode": True,
        "character_set": "GB18030",
        "possible_formats": ["QR_CODE"],
    }
    assert not Path(captured["filename"]).exists()


def test_file_size_limit_is_enforced(monkeypatch, tmp_path):
    image = tmp_path / "large.png"
    image.write_bytes(b"1234")
    monkeypatch.setattr(Config, "MAX_FILE_SIZE", 3)

    with pytest.raises(FileTooLargeError):
        make_reader(tmp_path).decode(str(image))


def test_concurrent_download_uses_one_cache_writer(monkeypatch, tmp_path):
    payload = b"verified jar"
    expected_hash = hashlib.sha256(payload).hexdigest()
    calls = 0
    calls_lock = threading.Lock()

    class FakeResponse:
        headers = {'Content-Length': str(len(payload))}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self, size):
            value, self.payload = getattr(self, 'payload', payload), b''
            time.sleep(0.02)
            return value

    def fake_urlopen(origin, timeout):
        nonlocal calls
        with calls_lock:
            calls += 1
        return FakeResponse()

    monkeypatch.setattr("pyzxing.utils.urlopen", fake_urlopen)

    def download():
        return get_file(
            "zxing.jar",
            "https://example.invalid/zxing.jar",
            tmp_path,
            expected_sha256=expected_hash,
            timeout=1,
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(lambda _: download(), range(4)))

    assert calls == 1
    assert len(set(paths)) == 1
    assert Path(paths[0]).read_bytes() == payload

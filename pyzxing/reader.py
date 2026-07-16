import base64
import binascii
import glob
import json
import logging
import math
import os
import os.path as osp
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from joblib import Parallel, delayed

from .config import Config
from .platform_utils import PlatformUtils
from .utils import get_file, sha256


_SCHEMA_VERSION = 1
_REQUIRED_RECORD_FIELDS = {
    "schema_version",
    "status",
    "input",
    "format",
    "type",
    "text",
    "parsed_text",
    "raw_bytes_base64",
    "num_bits",
    "byte_segments_base64",
    "points",
    "orientation",
    "orientation_source",
    "metadata",
    "error",
}
_ORIENTATIONS = {0, 90, 180, 270}
_ORIENTATION_SOURCES = {"metadata", "derived", "unavailable"}
_ERROR_CODES = {
    "INVALID_ARGUMENT",
    "MISSING_INPUT",
    "MULTIPLE_INPUTS",
    "MISSING_OPTION_VALUE",
    "INVALID_CHARACTER_SET",
    "INVALID_FORMAT",
    "INVALID_INPUT_URI",
    "UNSUPPORTED_URI_SCHEME",
    "INPUT_NOT_FOUND",
    "INPUT_READ_FAILED",
    "INVALID_IMAGE",
    "DECODE_FAILED",
    "INTERNAL_ERROR",
}
_METADATA_TYPES = {
    "orientation": int,
    "character_set": str,
    "error_correction_level": str,
    "errors_corrected": int,
    "erasures_corrected": int,
    "issue_number": int,
    "suggested_price": str,
    "possible_country": str,
    "upc_ean_extension": str,
    "structured_append_sequence": int,
    "structured_append_parity": int,
    "symbology_identifier": str,
}

preset_jar_url = Config.get_jar_url()
preset_jar_filename = Config.JAR_FILENAME
build_jar_dir = osp.join(osp.dirname(osp.dirname(osp.abspath(__file__))), Config.BUILD_DIR)


class PyZXingError(RuntimeError):
    """Base exception for pyzxing runtime failures."""


class JavaNotFoundError(PyZXingError):
    """Raised when no Java executable can be found."""


class DecodeError(PyZXingError):
    """Raised when the ZXing process cannot decode an input."""

    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


class DecodeTimeoutError(DecodeError):
    """Raised when ZXing exceeds the configured timeout."""


class FileTooLargeError(DecodeError):
    """Raised when an input exceeds the configured size limit."""


class BarCodeReader:
    def __init__(self, jar_path=None, cache_dir=None, timeout=None,
                 max_workers=None, build_dir=None, java_command=None):
        """Create a reader without performing network or subprocess work."""
        self.lib_path = osp.abspath(osp.expanduser(jar_path)) if jar_path else None
        self.cache_dir = cache_dir or Config.get_cache_dir()
        self.timeout = timeout if timeout is not None else Config.TIMEOUT_SECONDS
        self.max_workers = max_workers or Config.MAX_WORKERS
        self.build_dir = build_dir or build_jar_dir
        self.java_command = java_command or shutil.which(PlatformUtils.get_java_command())
        if not self.java_command:
            raise JavaNotFoundError(
                "Java was not found. Install JDK 17 and ensure 'java' is on PATH."
            )

    def _ensure_jar(self):
        if self.lib_path:
            if not osp.isfile(self.lib_path):
                raise FileNotFoundError(f"ZXing JAR not found: {self.lib_path}")
            return self.lib_path

        os.makedirs(self.cache_dir, exist_ok=True)
        built_jar = osp.join(self.build_dir, preset_jar_filename)
        if osp.isfile(built_jar):
            self.lib_path = built_jar
            return self.lib_path

        installed_jar = osp.join(
            osp.abspath(osp.expanduser(sys.prefix)),
            "share",
            "pyzxing",
            "runner",
            preset_jar_filename,
        )
        if osp.isfile(installed_jar):
            actual_sha256 = sha256(installed_jar)
            if actual_sha256 != Config.JAR_SHA256:
                raise DecodeError(
                    "Installed Runner SHA-256 mismatch: expected "
                    f"{Config.JAR_SHA256}, got {actual_sha256}: {installed_jar}"
                )
            self.lib_path = installed_jar
            return self.lib_path

        self.lib_path = get_file(
            preset_jar_filename,
            preset_jar_url,
            self.cache_dir,
            expected_sha256=Config.JAR_SHA256,
            timeout=self.timeout,
        )
        return self.lib_path

    def decode(self, filename_pattern, *, multi=True, try_harder=True,
               pure_barcode=False, character_set=None, possible_formats=None):
        if not filename_pattern:
            raise ValueError("filename_pattern must be a non-empty path or glob")

        hints = _validate_hints(
            multi=multi,
            try_harder=try_harder,
            pure_barcode=pure_barcode,
            character_set=character_set,
            possible_formats=possible_formats,
        )
        filenames = sorted(glob.glob(osp.abspath(osp.expanduser(filename_pattern))))
        if not filenames:
            raise FileNotFoundError(f"No files found: {filename_pattern}")

        for filename in filenames:
            size = osp.getsize(filename)
            if size > Config.MAX_FILE_SIZE:
                raise FileTooLargeError(
                    f"Input exceeds {Config.MAX_FILE_SIZE} bytes: {filename} ({size} bytes)"
                )

        if len(filenames) <= Config.PARALLEL_THRESHOLD:
            decoded = [self._decode(filename, **hints) for filename in filenames]
        else:
            jobs = min(self.max_workers, len(filenames))
            decoded = Parallel(n_jobs=jobs)(
                delayed(self._decode)(filename, **hints) for filename in filenames
            )

        return [barcode for file_results in decoded for barcode in file_results]

    def decode_array(self, array, *, multi=True, try_harder=True,
                     pure_barcode=False, character_set=None, possible_formats=None):
        try:
            import cv2 as cv
        except ImportError:
            logging.error("OpenCV not installed. Install opencv-python to use decode_array().")
            raise

        temp_dir = Config.get_temp_dir()
        os.makedirs(temp_dir, exist_ok=True)
        filename = osp.join(temp_dir, f'{uuid.uuid4().hex}.png')
        try:
            image = array[:, :, ::-1] if len(array.shape) == 3 else array
            if not cv.imwrite(filename, image):
                raise DecodeError("OpenCV failed to write the temporary image")
            return self.decode(
                filename,
                multi=multi,
                try_harder=try_harder,
                pure_barcode=pure_barcode,
                character_set=character_set,
                possible_formats=possible_formats,
            )
        finally:
            if osp.exists(filename):
                os.remove(filename)

    def _decode(self, filename, *, multi, try_harder, pure_barcode,
                character_set, possible_formats):
        jar_path = self._ensure_jar()
        file_uri = Path(filename).resolve().as_uri()
        command = [self.java_command, '-jar', jar_path, file_uri]
        if multi:
            command.append('--multi')
        if try_harder:
            command.append('--try-harder')
        if pure_barcode:
            command.append('--pure-barcode')
        if character_set is not None:
            command.extend(['--character-set', character_set])
        if possible_formats is not None:
            command.extend(['--possible-formats', possible_formats])

        try:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                check=False,
                env=PlatformUtils.get_process_environment(),
            )
        except subprocess.TimeoutExpired as exc:
            raise DecodeTimeoutError(
                f"ZXing exceeded the {self.timeout}s timeout for {filename}"
            ) from exc
        except OSError as exc:
            raise DecodeError(f"Failed to start Java for {filename}: {exc}") from exc

        return _parse_jsonl_process(process, file_uri)


def _validate_hints(*, multi, try_harder, pure_barcode, character_set,
                    possible_formats):
    for name, value in (
        ("multi", multi),
        ("try_harder", try_harder),
        ("pure_barcode", pure_barcode),
    ):
        if not isinstance(value, bool):
            raise TypeError(f"{name} must be a bool")

    if character_set is not None:
        if not isinstance(character_set, str):
            raise TypeError("character_set must be a string or None")
        if not character_set or "\x00" in character_set:
            raise ValueError("character_set must be a non-empty charset name")

    if possible_formats is not None:
        if isinstance(possible_formats, str):
            formats = [item.strip() for item in possible_formats.split(',')]
        else:
            try:
                formats = list(possible_formats)
            except TypeError as exc:
                raise TypeError(
                    "possible_formats must be a string, iterable of strings, or None"
                ) from exc
        if not formats or any(
                not isinstance(item, str) or not item or "\x00" in item
                for item in formats):
            raise ValueError("possible_formats must contain non-empty format names")
        try:
            possible_formats = ','.join(formats)
            possible_formats.encode('ascii', errors='strict')
        except UnicodeEncodeError as exc:
            raise ValueError("possible_formats must contain ASCII format names") from exc

    return {
        "multi": multi,
        "try_harder": try_harder,
        "pure_barcode": pure_barcode,
        "character_set": character_set,
        "possible_formats": possible_formats,
    }


def _parse_jsonl_process(process, expected_input):
    records = _load_jsonl(process.stdout, process.returncode, process.stderr)
    validated = [_validate_record(record, expected_input) for record in records]
    statuses = {record["status"] for record in validated}

    if process.returncode != 0:
        if len(validated) == 1 and statuses == {"error"}:
            error = validated[0]["error"]
            raise DecodeError(
                f'{error["code"]}: {error["message"]}', code=error["code"]
            )
        raise _protocol_error(
            "nonzero exit must contain exactly one valid error record",
            process.returncode,
            process.stderr,
        )

    if "error" in statuses:
        raise _protocol_error(
            "status=error requires a nonzero exit code",
            process.returncode,
            process.stderr,
        )
    if statuses == {"not_found"}:
        if len(validated) != 1:
            raise _protocol_error(
                "not_found must be the only record",
                process.returncode,
                process.stderr,
            )
        return [{"filename": expected_input.encode("utf-8", errors="strict")}]
    if statuses != {"ok"}:
        raise _protocol_error(
            "ok and not_found records may not be mixed",
            process.returncode,
            process.stderr,
        )
    return [_map_ok_record(record) for record in validated]


def _load_jsonl(stdout, returncode, stderr):
    try:
        output = stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise _protocol_error(
            "stdout is not valid UTF-8", returncode, stderr
        ) from exc
    lines = output.splitlines()
    if not lines:
        raise _protocol_error("stdout contained zero records", returncode, stderr)

    records = []
    for line_number, line in enumerate(lines, start=1):
        if not line:
            raise _protocol_error(
                f"line {line_number} is empty", returncode, stderr
            )
        try:
            record = json.loads(
                line,
                object_pairs_hook=_unique_object,
                parse_constant=_reject_json_constant,
            )
        except (TypeError, ValueError) as exc:
            raise _protocol_error(
                f"line {line_number} is not valid JSON: {exc}", returncode, stderr
            ) from exc
        if not isinstance(record, dict):
            raise _protocol_error(
                f"line {line_number} is not a JSON object", returncode, stderr
            )
        records.append(record)
    return records


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value):
    raise ValueError(f"non-finite JSON number {value}")


def _validate_record(record, expected_input):
    missing = sorted(_REQUIRED_RECORD_FIELDS.difference(record))
    if missing:
        raise DecodeError(
            "Runner protocol violation: missing fields " + ", ".join(missing)
        )
    schema_version = record["schema_version"]
    if isinstance(schema_version, bool) or schema_version != _SCHEMA_VERSION:
        raise DecodeError(
            f"Runner protocol violation: unsupported schema_version {schema_version!r}"
        )

    status = record["status"]
    if status not in {"ok", "not_found", "error"}:
        raise DecodeError(f"Runner protocol violation: invalid status {status!r}")

    input_value = record["input"]
    if status == "error" and input_value is None:
        pass
    elif not isinstance(input_value, str) or input_value != expected_input:
        raise DecodeError(
            "Runner protocol violation: input does not match the requested URI"
        )

    if status == "ok":
        _validate_ok_record(record)
    else:
        _validate_empty_result_record(record)
        if status == "not_found" and record["error"] is not None:
            raise DecodeError("Runner protocol violation: not_found error must be null")
        if status == "error":
            _validate_error(record["error"])
    return record


def _validate_ok_record(record):
    for field in ("input", "format", "type", "text", "parsed_text"):
        if not isinstance(record[field], str):
            raise DecodeError(f"Runner protocol violation: {field} must be a string")
    for field in ("format", "type"):
        try:
            record[field].encode("ascii", errors="strict")
        except UnicodeEncodeError as exc:
            raise DecodeError(
                f"Runner protocol violation: {field} must contain ASCII"
            ) from exc

    _decode_optional_base64(record["raw_bytes_base64"], "raw_bytes_base64")
    _decode_byte_segments(record["byte_segments_base64"])
    _validate_num_bits(record["num_bits"])
    _validate_points(record["points"])
    _validate_orientation(record["orientation"], record["orientation_source"])
    _validate_metadata(record["metadata"])
    if record["error"] is not None:
        raise DecodeError("Runner protocol violation: ok error must be null")


def _validate_empty_result_record(record):
    for field in ("format", "type", "text", "parsed_text", "raw_bytes_base64",
                  "num_bits", "orientation"):
        if record[field] is not None:
            raise DecodeError(
                f"Runner protocol violation: {field} must be null for {record['status']}"
            )
    for field in ("byte_segments_base64", "points"):
        if record[field] != []:
            raise DecodeError(
                f"Runner protocol violation: {field} must be empty for {record['status']}"
            )
    if record["orientation_source"] != "unavailable":
        raise DecodeError(
            f"Runner protocol violation: orientation_source must be unavailable for "
            f"{record['status']}"
        )
    if record["metadata"] != {}:
        raise DecodeError(
            f"Runner protocol violation: metadata must be empty for {record['status']}"
        )


def _validate_error(error):
    if not isinstance(error, dict) or set(error) != {"code", "message"}:
        raise DecodeError(
            "Runner protocol violation: error must contain only code and message"
        )
    if error["code"] not in _ERROR_CODES:
        raise DecodeError(
            f"Runner protocol violation: unsupported error code {error['code']!r}"
        )
    if not isinstance(error["message"], str) or not error["message"]:
        raise DecodeError("Runner protocol violation: error message must be non-empty")


def _decode_optional_base64(value, field):
    if value is None:
        return None
    if not isinstance(value, str):
        raise DecodeError(f"Runner protocol violation: {field} must be a string or null")
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise DecodeError(f"Runner protocol violation: invalid Base64 in {field}") from exc


def _decode_byte_segments(values):
    if not isinstance(values, list):
        raise DecodeError(
            "Runner protocol violation: byte_segments_base64 must be an array"
        )
    decoded = []
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise DecodeError(
                f"Runner protocol violation: byte_segments_base64[{index}] "
                "must be a string"
            )
        decoded.append(
            _decode_optional_base64(value, f"byte_segments_base64[{index}]")
        )
    return decoded


def _validate_num_bits(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DecodeError("Runner protocol violation: num_bits must be a nonnegative integer")


def _validate_points(points):
    if not isinstance(points, list):
        raise DecodeError("Runner protocol violation: points must be an array")
    for index, point in enumerate(points):
        if not isinstance(point, list) or len(point) != 2:
            raise DecodeError(
                f"Runner protocol violation: points[{index}] must be an [x, y] pair"
            )
        for coordinate in point:
            try:
                finite = math.isfinite(coordinate)
            except (OverflowError, TypeError):
                finite = False
            if (isinstance(coordinate, bool)
                    or not isinstance(coordinate, (int, float))
                    or not finite):
                raise DecodeError(
                    f"Runner protocol violation: points[{index}] must be finite numbers"
                )


def _validate_orientation(orientation, source):
    if orientation is not None and (
            isinstance(orientation, bool) or orientation not in _ORIENTATIONS):
        raise DecodeError(
            "Runner protocol violation: orientation must be 0/90/180/270 or null"
        )
    if source not in _ORIENTATION_SOURCES:
        raise DecodeError(
            f"Runner protocol violation: invalid orientation_source {source!r}"
        )
    if source == "unavailable" and orientation is not None:
        raise DecodeError(
            "Runner protocol violation: unavailable orientation must be null"
        )
    if source != "unavailable" and orientation is None:
        raise DecodeError(
            "Runner protocol violation: available orientation must be non-null"
        )


def _validate_metadata(metadata):
    if not isinstance(metadata, dict):
        raise DecodeError("Runner protocol violation: metadata must be an object")
    result = {}
    for key, expected_type in _METADATA_TYPES.items():
        if key not in metadata:
            continue
        value = metadata[key]
        if (expected_type is int and isinstance(value, bool)) or not isinstance(
                value, expected_type):
            raise DecodeError(
                f"Runner protocol violation: metadata.{key} has the wrong type"
            )
        if key == "orientation" and value not in _ORIENTATIONS:
            raise DecodeError(
                "Runner protocol violation: metadata.orientation is invalid"
            )
        result[key] = value
    return result


def _map_ok_record(record):
    text = record["text"]
    parsed_text = record["parsed_text"]
    return {
        "filename": record["input"].encode("utf-8", errors="strict"),
        "format": record["format"].encode("ascii", errors="strict"),
        "type": record["type"].encode("ascii", errors="strict"),
        "raw": text.encode("utf-8", errors="strict"),
        "parsed": parsed_text.encode("utf-8", errors="strict"),
        "points": [tuple(point) for point in record["points"]],
        "text": text,
        "parsed_text": parsed_text,
        "raw_bytes": _decode_optional_base64(
            record["raw_bytes_base64"], "raw_bytes_base64"
        ),
        "byte_segments": _decode_byte_segments(record["byte_segments_base64"]),
        "num_bits": record["num_bits"],
        "orientation": record["orientation"],
        "orientation_source": record["orientation_source"],
        "metadata": _validate_metadata(record["metadata"]),
    }


def _protocol_error(message, returncode, stderr):
    diagnostic = PlatformUtils.decode_output(stderr).strip()
    suffix = f" (exit code {returncode})"
    if diagnostic:
        suffix += f": {diagnostic}"
    return DecodeError(f"Runner protocol violation: {message}{suffix}")

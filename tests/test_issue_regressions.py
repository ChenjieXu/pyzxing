import hashlib
import json
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ISSUE_34_FIXTURE = (
    REPOSITORY_ROOT
    / "java-runner/src/test/resources/fixtures/gb18030/gb18030-byte-no-eci.png"
)
ISSUE_34_REPORT = json.loads(
    (REPOSITORY_ROOT / "reports/issue-34-gb18030.json").read_text(
        encoding="utf-8"
    )
)
ISSUE_35_REPORT_PATH = REPOSITORY_ROOT / "reports/issue-35-assessment.json"
ISSUE_35_REPORT = json.loads(ISSUE_35_REPORT_PATH.read_text(encoding="utf-8"))
ISSUE_38_REPORT = json.loads(
    (REPOSITORY_ROOT / "reports/issue-38-zxing-comparison.json").read_text(
        encoding="utf-8"
    )
)
ISSUE_38_FIXTURES = ISSUE_38_REPORT["representative_fixtures"]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_issue_34_gb18030_without_eci(barcode_reader, test_runner_jar):
    payload = "生产许可证号：测试-123"
    payload_bytes = bytes.fromhex(
        "c9fab2fad0edbfc9d6a4bac5a3bab2e2cad42d313233"
    )

    default = barcode_reader.decode(
        str(ISSUE_34_FIXTURE), multi=False, possible_formats=["QR_CODE"]
    )[0]
    explicit = barcode_reader.decode(
        str(ISSUE_34_FIXTURE),
        multi=False,
        character_set="GB18030",
        possible_formats=["QR_CODE"],
    )[0]

    assert default["text"] == "Éú²úÐí¿ÉÖ¤ºÅ£º²âÊÔ-123"
    assert default["text"] != payload
    assert default["byte_segments"] == [payload_bytes]
    assert "character_set" not in default["metadata"]
    assert explicit["text"] == payload
    assert explicit["parsed_text"] == payload
    assert explicit["byte_segments"] == [payload_bytes]
    assert explicit["metadata"]["character_set"] == "GB18030"
    assert sha256(ISSUE_34_FIXTURE) == ISSUE_34_REPORT["fixture"]["sha256"]
    assert sha256(test_runner_jar) == ISSUE_34_REPORT["decoder"]["artifact_sha256"]


def test_known_good_data_matrix(barcode_reader):
    result = barcode_reader.decode(
        str(REPOSITORY_ROOT / "tests/resources/data-matrix/basic.png"),
        multi=False,
        possible_formats=["DATA_MATRIX"],
    )[0]

    assert result["format"] == b"DATA_MATRIX"
    assert result["text"] == "PYZXING-DATAMATRIX-1.2.0"
    assert result["parsed"] == b"PYZXING-DATAMATRIX-1.2.0"
    assert result["points"]
    assert all(isinstance(point, tuple) for point in result["points"])


def test_issue_35_assessment_is_internally_consistent(test_runner_jar):
    report = ISSUE_35_REPORT
    expected_attachments = {
        "A": {
            "attachment_id": 165688220,
            "source_url": (
                "https://user-images.githubusercontent.com/12841788/"
                "165688220-5b84da45-b752-415a-b144-a53f39e21497.jpg"
            ),
            "downloaded_sha256": (
                "59657944f84517840199113e833f7d4dbe098fe4232a8f793d2e316990873bf0"
            ),
        },
        "B": {
            "attachment_id": 165692086,
            "source_url": (
                "https://user-images.githubusercontent.com/12841788/"
                "165692086-7d0f830d-b8b7-4e3f-b99d-483ec75a88b0.jpg"
            ),
            "downloaded_sha256": (
                "bf76fab9c60c56e444b74e1a3e9b2b86beeafdd64e4706c647987c078032fcd1"
            ),
        },
    }

    assert ISSUE_35_REPORT_PATH.is_file()
    assert report["schema_version"] == 1
    assert report["issue"]["number"] == 35
    assert report["status"] == "needs_reproducer"
    assert report["conclusion"]["classification"] == "needs_reproducer"
    assert {attachment["case"] for attachment in report["attachments"]} == {
        "A",
        "B",
    }
    for attachment in report["attachments"]:
        expected = expected_attachments[attachment["case"]]
        assert attachment["attachment_id"] == expected["attachment_id"]
        assert attachment["source_url"] == expected["source_url"]
        assert attachment["downloaded_sha256"] == expected["downloaded_sha256"]
        assert attachment["dimensions"] == {"width": 3780, "height": 3288}
        assert attachment["reporter_ground_truth"] == {
            "format": None,
            "text": None,
        }

    modes = set(report["hint_matrix"])
    assert set(report["results"]["A"]["cases"]) == modes
    assert set(report["results"]["B"]["cases"]) == modes
    assert report["results"]["A"]["cases"]["try_harder"] == {
        "exit_code": 0,
        "status": "ok",
        "format": "CODE_39",
        "text": "XA6MG   2KF     ",
    }
    assert all(
        result == {
            "exit_code": 0,
            "status": "not_found",
            "format": None,
            "text": None,
        }
        for result in report["results"]["B"]["cases"].values()
    )
    assert sha256(test_runner_jar) == report["decoder"]["artifact_sha256"]


@pytest.mark.parametrize("kind,barcode_format", [
    ("qrcode", "QR_CODE"),
    ("code128", "CODE_128"),
])
@pytest.mark.parametrize("degrees", [0, 90, 180, 270])
def test_issue_50_right_angle_orientation(
        barcode_reader, kind, barcode_format, degrees):
    result = barcode_reader.decode(
        str(
            REPOSITORY_ROOT
            / f"tests/resources/orientation/{kind}-{degrees}.png"
        ),
        multi=False,
        try_harder=True,
        possible_formats=[barcode_format],
    )[0]

    assert result["orientation"] == degrees
    if kind == "qrcode":
        assert result["orientation_source"] == "derived"
        assert "orientation" not in result["metadata"]
    elif degrees == 0:
        assert result["orientation_source"] == "derived"
        assert "orientation" not in result["metadata"]
    else:
        assert result["orientation_source"] == "metadata"
        assert result["metadata"]["orientation"] == {
            90: 270,
            180: 180,
            270: 90,
        }[degrees]


@pytest.mark.parametrize(
    "fixture",
    ISSUE_38_FIXTURES,
    ids=lambda fixture: str(fixture["value"]),
)
def test_issue_38_representatives_decode_as_pure_qr(barcode_reader, fixture):
    path = REPOSITORY_ROOT / fixture["path"]
    result = barcode_reader.decode(
        str(path),
        multi=False,
        pure_barcode=True,
        possible_formats=["QR_CODE"],
    )[0]

    assert sha256(path) == fixture["sha256"]
    assert result["format"] == b"QR_CODE"
    assert result["text"] == str(fixture["value"])


def test_issue_38_report_is_internally_consistent(test_runner_jar):
    report = ISSUE_38_REPORT
    corpus = report["corpus"]["values"]

    assert report["schema_version"] == 1
    assert report["corpus"]["count"] == len(corpus) == 192
    assert len(set(corpus)) == 192
    assert 10 <= len(ISSUE_38_FIXTURES) <= 20
    expected_modes = {
        "default",
        "try_harder",
        "pure_barcode",
        "qr_only",
        "wrapper_defaults",
    }

    for decoder in report["decoders"].values():
        assert set(decoder["modes"]) == expected_modes
        for mode in decoder["modes"].values():
            total = (
                mode["success_count"]
                + mode["failure_count"]
                + mode["mismatch_count"]
                + mode["error_count"]
            )
            assert total == len(corpus)
            assert set(mode["remaining_failures"]).issubset(corpus)

    assert report["decoders"]["zxing_3_4_1"]["modes"]["pure_barcode"][
        "success_count"
    ] == 192
    assert report["decoders"]["zxing_3_5_4"]["modes"]["pure_barcode"][
        "success_count"
    ] == 192
    assert sha256(test_runner_jar) == report["decoders"]["zxing_3_5_4"][
        "artifact_sha256"
    ]

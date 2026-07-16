#!/usr/bin/env python3
"""Validate the committed issue #34, #35, and #38 release evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict

from verify_version_sync import ROOT, read_python_constants


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ISSUE_38_CORPUS_SHA256 = "0386726dcde447b076ba9666578f09fe118843d70d562ab2da61d594538d53c1"
ISSUE_38_MODES = {"default", "try_harder", "pure_barcode", "qr_only", "wrapper_defaults"}
ISSUE_35_MODES = {
    "default",
    "try_harder",
    "code_39_only",
    "try_harder_code_39",
    "pure_barcode",
    "wrapper_defaults",
    "wrapper_defaults_code_39",
}
ISSUE_35_ATTACHMENTS = {
    "A": {
        "label": "new1",
        "attachment_id": 165688220,
        "attachment_uuid": "5b84da45-b752-415a-b144-a53f39e21497",
        "source_url": (
            "https://user-images.githubusercontent.com/12841788/"
            "165688220-5b84da45-b752-415a-b144-a53f39e21497.jpg"
        ),
        "downloaded_filename": "new1.jpg",
        "downloaded_sha256": (
            "59657944f84517840199113e833f7d4dbe098fe4232a8f793d2e316990873bf0"
        ),
        "downloaded_bytes": 1882585,
    },
    "B": {
        "label": "P3111 00KHRTRND__20220313_14_4945_1",
        "attachment_id": 165692086,
        "attachment_uuid": "7d0f830d-b8b7-4e3f-b99d-483ec75a88b0",
        "source_url": (
            "https://user-images.githubusercontent.com/12841788/"
            "165692086-7d0f830d-b8b7-4e3f-b99d-483ec75a88b0.jpg"
        ),
        "downloaded_filename": "P3111_00KHRTRND__20220313_14_4945_1.jpg",
        "downloaded_sha256": (
            "bf76fab9c60c56e444b74e1a3e9b2b86beeafdd64e4706c647987c078032fcd1"
        ),
        "downloaded_bytes": 1806680,
    },
}
ISSUE_35_HINTS = {
    "default": {
        "arguments": [],
        "hints": {
            "multi": False,
            "try_harder": False,
            "pure_barcode": False,
            "possible_formats": None,
        },
    },
    "try_harder": {
        "arguments": ["--try-harder"],
        "hints": {
            "multi": False,
            "try_harder": True,
            "pure_barcode": False,
            "possible_formats": None,
        },
    },
    "code_39_only": {
        "arguments": ["--possible-formats", "CODE_39"],
        "hints": {
            "multi": False,
            "try_harder": False,
            "pure_barcode": False,
            "possible_formats": ["CODE_39"],
        },
    },
    "try_harder_code_39": {
        "arguments": ["--try-harder", "--possible-formats", "CODE_39"],
        "hints": {
            "multi": False,
            "try_harder": True,
            "pure_barcode": False,
            "possible_formats": ["CODE_39"],
        },
    },
    "pure_barcode": {
        "arguments": ["--pure-barcode"],
        "hints": {
            "multi": False,
            "try_harder": False,
            "pure_barcode": True,
            "possible_formats": None,
        },
    },
    "wrapper_defaults": {
        "arguments": ["--multi", "--try-harder"],
        "hints": {
            "multi": True,
            "try_harder": True,
            "pure_barcode": False,
            "possible_formats": None,
        },
    },
    "wrapper_defaults_code_39": {
        "arguments": [
            "--multi",
            "--try-harder",
            "--possible-formats",
            "CODE_39",
        ],
        "hints": {
            "multi": True,
            "try_harder": True,
            "pure_barcode": False,
            "possible_formats": ["CODE_39"],
        },
    },
}
ISSUE_35_A_SUCCESS_MODES = {
    "try_harder",
    "try_harder_code_39",
    "wrapper_defaults",
    "wrapper_defaults_code_39",
}
ISSUE_35_A_TEXT = "XA6MG   2KF     "


def load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_path(value: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"invalid repository-relative evidence path: {value!r}")
    path = (ROOT / value).resolve(strict=True)
    try:
        path.relative_to(ROOT)
    except ValueError as error:
        raise ValueError(f"evidence path escapes the repository: {value!r}") from error
    return path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_issue_34(report: Dict[str, Any], config: Dict[str, str]) -> str:
    require(report.get("schema_version") == 1, "issue #34 report schema_version must be 1")
    require(report.get("issue", {}).get("number") == 34, "issue #34 report has wrong issue")
    require(report.get("status") == "pass", "issue #34 report is not passing")

    fixture = report.get("fixture", {})
    fixture_path = repository_path(fixture.get("path"))
    provenance_path = repository_path(fixture.get("provenance_path"))
    fixture_sha = fixture.get("sha256")
    require(SHA256_RE.fullmatch(fixture_sha or "") is not None, "invalid #34 fixture SHA-256")
    require(sha256(fixture_path) == fixture_sha, "issue #34 fixture SHA-256 changed")

    provenance = load_json(provenance_path)
    require(provenance.get("fixture") == fixture_path.name, "#34 provenance fixture name differs")
    require(provenance.get("sha256") == fixture_sha, "#34 provenance SHA-256 differs")
    for key in ("payload_text", "payload_encoding", "payload_hex", "generator"):
        require(provenance.get(key) == fixture.get(key), f"#34 fixture/provenance {key} differs")
    for key, value in fixture.get("qr", {}).items():
        require(provenance.get("qr", {}).get(key) == value, f"#34 QR provenance {key} differs")
    require(fixture.get("payload_encoding") == "GB18030", "#34 payload encoding is not GB18030")
    payload_bytes = bytes.fromhex(fixture.get("payload_hex", ""))
    require(
        payload_bytes.decode("gb18030") == fixture.get("payload_text"),
        "#34 payload hex does not decode to the recorded text",
    )
    require(fixture.get("generator", {}).get("uses_zxing") is False, "#34 fixture is not independent")
    require(fixture.get("qr", {}).get("eci") is False, "#34 fixture must exercise no-ECI data")

    decoder = report.get("decoder", {})
    require(decoder.get("runner_version") == config["RUNNER_VERSION"], "#34 Runner version differs")
    require(
        decoder.get("zxing_version") == config["DEFAULT_ZXING_VERSION"],
        "#34 ZXing version differs",
    )
    require(decoder.get("artifact") == config["JAR_FILENAME"], "#34 Runner filename differs")
    artifact_sha = decoder.get("artifact_sha256")
    require(SHA256_RE.fullmatch(artifact_sha or "") is not None, "invalid #34 Runner SHA-256")

    cases = report.get("cases", {})
    require(
        set(cases) == {"default_without_character_set", "explicit_gb18030"},
        "#34 report must preserve default and explicit GB18030 cases",
    )
    for case_name, case in cases.items():
        require(case.get("status") == "pass", f"#34 {case_name} is not passing")
        require(isinstance(case.get("command"), list) and case["command"], f"#34 {case_name} lacks command")
        require(case.get("expected_text") == case.get("actual_text"), f"#34 {case_name} text differs")
        require(
            case.get("expected_byte_segment_hex") == fixture.get("payload_hex")
            and case.get("actual_byte_segment_hex") == fixture.get("payload_hex"),
            f"#34 {case_name} BYTE segment differs",
        )
    default_case = cases["default_without_character_set"]
    require(
        default_case.get("documents_no_eci_default_limitation") is True,
        "#34 default case must record the no-ECI limitation",
    )
    explicit_case = cases["explicit_gb18030"]
    require(explicit_case.get("actual_text") == fixture.get("payload_text"), "#34 explicit text differs")
    require(explicit_case.get("metadata_character_set") == "GB18030", "#34 hint metadata differs")

    references = report.get("test_references")
    require(isinstance(references, list) and references, "#34 report lacks test references")
    for reference in references:
        repository_path(reference.split("::", 1)[0])
    return artifact_sha


def verify_issue_35(report: Dict[str, Any], config: Dict[str, str]) -> str:
    require(
        set(report)
        == {
            "schema_version",
            "issue",
            "status",
            "attachments",
            "attachment_retention",
            "decoder",
            "hint_matrix",
            "results",
            "conclusion",
        },
        "issue #35 report top-level fields changed",
    )
    require(report.get("schema_version") == 1, "issue #35 report schema_version must be 1")
    issue = report.get("issue", {})
    require(
        issue
        == {
            "number": 35,
            "title": "not scanning codes properly",
            "url": "https://github.com/ChenjieXu/pyzxing/issues/35",
            "state_at_audit": "OPEN",
            "created_at": "2022-04-28T06:08:24Z",
            "updated_at": "2025-09-11T03:34:47Z",
        },
        "issue #35 public issue provenance changed",
    )
    require(report.get("status") == "needs_reproducer", "issue #35 status changed")
    require(
        report.get("attachment_retention")
        == "source_url_and_sha256_only_not_committed",
        "issue #35 attachment retention policy changed",
    )

    attachments = report.get("attachments")
    require(isinstance(attachments, list) and len(attachments) == 2, "issue #35 needs two attachments")
    require(
        {attachment.get("case") for attachment in attachments} == {"A", "B"},
        "issue #35 attachment cases changed",
    )
    for attachment in attachments:
        case = attachment["case"]
        expected = ISSUE_35_ATTACHMENTS[case]
        require(
            set(attachment)
            == {
                "case",
                "label",
                "attachment_id",
                "attachment_uuid",
                "source_url",
                "downloaded_filename",
                "download_command",
                "downloaded_sha256",
                "downloaded_bytes",
                "dimensions",
                "reporter_ground_truth",
            },
            f"issue #35 attachment {case} fields changed",
        )
        for key, value in expected.items():
            require(attachment.get(key) == value, f"issue #35 attachment {case} {key} changed")
        require(
            SHA256_RE.fullmatch(attachment["downloaded_sha256"]) is not None,
            f"issue #35 attachment {case} SHA-256 is invalid",
        )
        require(
            attachment.get("dimensions") == {"width": 3780, "height": 3288},
            f"issue #35 attachment {case} dimensions changed",
        )
        require(
            attachment.get("reporter_ground_truth") == {"format": None, "text": None},
            f"issue #35 attachment {case} invents reporter ground truth",
        )
        require(
            attachment.get("download_command")
            == [
                "curl",
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                attachment["source_url"],
                "--output",
                attachment["downloaded_filename"],
            ],
            f"issue #35 attachment {case} download command changed",
        )

    decoder = report.get("decoder", {})
    require(
        decoder.get("runner_version") == config["RUNNER_VERSION"],
        "issue #35 Runner version differs",
    )
    require(
        decoder.get("zxing_version") == config["DEFAULT_ZXING_VERSION"],
        "issue #35 ZXing version differs",
    )
    require(decoder.get("artifact") == config["JAR_FILENAME"], "issue #35 Runner filename differs")
    artifact_sha = decoder.get("artifact_sha256")
    require(SHA256_RE.fullmatch(artifact_sha or "") is not None, "invalid #35 Runner SHA-256")
    require(
        decoder.get("protocol") == "UTF-8 JSONL schema_version 1",
        "issue #35 Runner protocol differs",
    )

    hint_matrix = report.get("hint_matrix", {})
    require(set(hint_matrix) == ISSUE_35_MODES, "issue #35 hint matrix changed")
    for mode, expected in ISSUE_35_HINTS.items():
        observed = hint_matrix[mode]
        require(set(observed) == {"command", "hints"}, f"issue #35 {mode} fields changed")
        require(observed.get("hints") == expected["hints"], f"issue #35 {mode} hints changed")
        require(
            observed.get("command")
            == ["java", "-jar", config["JAR_FILENAME"], "{attachment_file_uri}"]
            + expected["arguments"],
            f"issue #35 {mode} command changed",
        )

    results = report.get("results", {})
    require(set(results) == {"A", "B"}, "issue #35 result cases changed")
    attachment_ids = {
        case: expected["attachment_id"]
        for case, expected in ISSUE_35_ATTACHMENTS.items()
    }
    for case, result in results.items():
        require(
            set(result) == {"attachment_id", "cases"},
            f"issue #35 result {case} fields changed",
        )
        require(
            result.get("attachment_id") == attachment_ids[case],
            f"issue #35 result {case} attachment changed",
        )
        cases = result.get("cases", {})
        require(set(cases) == ISSUE_35_MODES, f"issue #35 result {case} modes changed")
        for mode, observed in cases.items():
            require(
                set(observed) == {"exit_code", "status", "format", "text"},
                f"issue #35 result {case}.{mode} fields changed",
            )
            require(observed.get("exit_code") == 0, f"issue #35 result {case}.{mode} failed")
            expected_success = case == "A" and mode in ISSUE_35_A_SUCCESS_MODES
            if expected_success:
                require(
                    observed.get("status") == "ok"
                    and observed.get("format") == "CODE_39"
                    and observed.get("text") == ISSUE_35_A_TEXT,
                    f"issue #35 result {case}.{mode} decode changed",
                )
            else:
                require(
                    observed.get("status") == "not_found"
                    and observed.get("format") is None
                    and observed.get("text") is None,
                    f"issue #35 result {case}.{mode} must remain not_found",
                )

    conclusion = report.get("conclusion", {})
    require(
        set(conclusion) == {"classification", "summary", "required_follow_up"},
        "issue #35 conclusion fields changed",
    )
    require(
        conclusion.get("classification") == "needs_reproducer",
        "issue #35 conclusion must remain needs_reproducer",
    )
    require(
        "Attachment A decodes as CODE_39" in conclusion.get("summary", "")
        and "Attachment B does not decode" in conclusion.get("summary", "")
        and "cannot yet be classified" in conclusion.get("summary", ""),
        "issue #35 conclusion overstates the available evidence",
    )
    follow_up = conclusion.get("required_follow_up")
    require(
        isinstance(follow_up, list)
        and len(follow_up) == 3
        and all(isinstance(item, str) and item for item in follow_up),
        "issue #35 required reproducer details changed",
    )
    return artifact_sha


def verify_mode(mode_name: str, mode: Dict[str, Any], corpus: set) -> None:
    counts = []
    for key in ("success_count", "failure_count", "mismatch_count", "error_count"):
        value = mode.get(key)
        require(isinstance(value, int) and value >= 0, f"{mode_name}.{key} is invalid")
        counts.append(value)
    require(sum(counts) == len(corpus), f"{mode_name} counts do not cover the corpus")

    remaining = mode.get("remaining_failures")
    mismatches = mode.get("mismatches")
    errors = mode.get("errors")
    require(isinstance(remaining, list), f"{mode_name}.remaining_failures is not a list")
    require(len(remaining) == mode["failure_count"], f"{mode_name} failure count differs")
    require(len(set(remaining)) == len(remaining), f"{mode_name} repeats failures")
    require(set(remaining).issubset(corpus), f"{mode_name} contains an unknown failure")
    require(isinstance(mismatches, list) and len(mismatches) == mode["mismatch_count"], f"{mode_name} mismatch count differs")
    require(isinstance(errors, list) and len(errors) == mode["error_count"], f"{mode_name} error count differs")


def verify_issue_38(report: Dict[str, Any], config: Dict[str, str]) -> str:
    require(report.get("schema_version") == 1, "issue #38 report schema_version must be 1")
    issue = report.get("issue", {})
    require(issue.get("number") == 38, "issue #38 report has wrong issue")
    require(issue.get("reported_failure_count") == 192, "issue #38 failure count changed")

    corpus = report.get("corpus", {})
    values = corpus.get("values")
    require(isinstance(values, list), "issue #38 corpus values must be a list")
    require(corpus.get("count") == 192 and len(values) == 192, "issue #38 corpus must contain 192 values")
    require(values == sorted(set(values)), "issue #38 corpus must be sorted and unique")
    corpus_digest = hashlib.sha256(
        json.dumps(values, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    require(corpus_digest == ISSUE_38_CORPUS_SHA256, "issue #38 exact reported corpus changed")
    require("Issue #38" in corpus.get("source", ""), "issue #38 corpus source is missing")
    generator = corpus.get("generator", {})
    require(generator.get("segno") and generator.get("opencv"), "issue #38 generator versions missing")
    require(generator.get("segno_call") and generator.get("opencv_pipeline"), "issue #38 generator pipeline missing")
    require(
        generator.get("segno_parameters")
        == {"version": 1, "error": "H", "mode": "numeric", "mask": "automatic per value"},
        "issue #38 Segno parameters changed",
    )

    decoders = report.get("decoders", {})
    require(set(decoders) == {"zxing_3_4_1", "zxing_3_5_4"}, "issue #38 decoder set changed")
    versions = {"zxing_3_4_1": "3.4.1", "zxing_3_5_4": config["DEFAULT_ZXING_VERSION"]}
    baseline = decoders["zxing_3_4_1"]
    require(
        baseline.get("artifact_url")
        == "https://github.com/ChenjieXu/pyzxing/releases/download/"
        "v1.1.0/javase-3.4.1-SNAPSHOT-jar-with-dependencies.jar",
        "issue #38 baseline artifact URL changed",
    )
    baseline_source = baseline.get("source", {})
    require(
        baseline_source.get("repository") == "https://github.com/zxing/zxing.git"
        and re.fullmatch(r"[0-9a-f]{40}", baseline_source.get("commit", "")) is not None,
        "issue #38 baseline source provenance is incomplete",
    )
    require(
        isinstance(baseline_source.get("build_commands"), list)
        and baseline_source["build_commands"]
        and baseline_source.get("build_command_source"),
        "issue #38 baseline build provenance is incomplete",
    )
    current_decoder = decoders["zxing_3_5_4"]
    require(
        current_decoder.get("runner_version") == config["RUNNER_VERSION"]
        and current_decoder.get("protocol") == "UTF-8 JSONL schema_version 1",
        "issue #38 current Runner provenance differs",
    )
    corpus_set = set(values)
    for decoder_name, expected_version in versions.items():
        decoder = decoders[decoder_name]
        require(decoder.get("zxing_version") == expected_version, f"{decoder_name} version differs")
        require(SHA256_RE.fullmatch(decoder.get("artifact_sha256", "")) is not None, f"{decoder_name} SHA-256 is invalid")
        require(set(decoder.get("commands", {})) == ISSUE_38_MODES, f"{decoder_name} commands differ")
        require(set(decoder.get("modes", {})) == ISSUE_38_MODES, f"{decoder_name} modes differ")
        for mode_name in sorted(ISSUE_38_MODES):
            command = decoder["commands"][mode_name]
            require(isinstance(command, list) and command, f"{decoder_name}.{mode_name} command missing")
            verify_mode(f"{decoder_name}.{mode_name}", decoder["modes"][mode_name], corpus_set)
        pure = decoder["modes"]["pure_barcode"]
        require(
            pure["success_count"] == 192
            and pure["failure_count"] == 0
            and pure["mismatch_count"] == 0
            and pure["error_count"] == 0,
            f"{decoder_name} pure-barcode result is not 192/192",
        )

    current = decoders["zxing_3_5_4"]
    require(current.get("artifact") == config["JAR_FILENAME"], "#38 current Runner filename differs")
    current_sha = current["artifact_sha256"]

    fixtures = report.get("representative_fixtures")
    require(isinstance(fixtures, list) and len(fixtures) == 16, "#38 must keep 16 representative fixtures")
    for fixture in fixtures:
        value = fixture.get("value")
        require(value in corpus_set, f"#38 representative value {value!r} is outside corpus")
        path = repository_path(fixture.get("path"))
        require(sha256(path) == fixture.get("sha256"), f"#38 fixture {path.name} SHA-256 changed")
        results = fixture.get("results", {})
        require(set(results) == set(decoders), f"#38 fixture {value} decoder results differ")
        for decoder_name, decoder in decoders.items():
            require(set(results[decoder_name]) == ISSUE_38_MODES, f"#38 fixture {value} modes differ")
            for mode_name, observed in results[decoder_name].items():
                mode = decoder["modes"][mode_name]
                expected = "not_found" if value in mode["remaining_failures"] else "success"
                require(observed == expected, f"#38 fixture {value} {decoder_name}.{mode_name} differs")

    summary = report.get("summary", {})
    require(summary.get("all_reported_values_decode_with_pure_barcode_3_5_4") is True, "#38 summary lost pure-barcode result")
    require(
        summary.get("default_3_4_1_success_count")
        == decoders["zxing_3_4_1"]["modes"]["default"]["success_count"],
        "#38 baseline summary differs",
    )
    require(
        summary.get("default_3_5_4_success_count") == current["modes"]["default"]["success_count"],
        "#38 current summary differs",
    )
    require(
        summary.get("wrapper_defaults_3_4_1_success_count")
        == decoders["zxing_3_4_1"]["modes"]["wrapper_defaults"]["success_count"],
        "#38 baseline wrapper summary differs",
    )
    require(
        summary.get("wrapper_defaults_3_5_4_success_count")
        == current["modes"]["wrapper_defaults"]["success_count"],
        "#38 current wrapper summary differs",
    )
    return current_sha


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-unfinalized-runner",
        action="store_true",
        help="validate evidence before Config receives the canonical checksum",
    )
    args = parser.parse_args()

    config = read_python_constants(ROOT / "pyzxing" / "config.py", "Config")
    issue_34_sha = verify_issue_34(load_json(ROOT / "reports" / "issue-34-gb18030.json"), config)
    issue_35_sha = verify_issue_35(
        load_json(ROOT / "reports" / "issue-35-assessment.json"), config
    )
    issue_38_sha = verify_issue_38(
        load_json(ROOT / "reports" / "issue-38-zxing-comparison.json"), config
    )
    require(
        issue_34_sha == issue_35_sha == issue_38_sha,
        "#34, #35, and #38 used different canonical Runner bytes",
    )
    if config["JAR_SHA256"] == "0" * 64:
        require(args.allow_unfinalized_runner, "Config.JAR_SHA256 is still a pre-release placeholder")
    else:
        require(issue_34_sha == config["JAR_SHA256"], "evidence Runner SHA differs from Config")

    print(
        "release evidence verified: issue-34 issue-35 issue-38 "
        f"runner_sha256={issue_34_sha}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

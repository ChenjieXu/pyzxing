#!/usr/bin/env python3
"""Verify package, Runner, release asset, and conda version synchronization."""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import Dict


ROOT = Path(__file__).resolve().parents[1]
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
JINJA_SET_RE = re.compile(r'^\{% set ([a-z0-9_]+) = "([^"]*)" %\}(?:\s*\{#.*#\})?$')


def read_conda_variables(path: Path) -> Dict[str, str]:
    variables = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = JINJA_SET_RE.fullmatch(line.strip())
        if match is not None:
            variables[match.group(1)] = match.group(2)
    return variables


def require_equal(label: str, values: Dict[str, str]) -> None:
    unique = set(values.values())
    if len(unique) != 1:
        details = ", ".join(f"{name}={value!r}" for name, value in values.items())
        raise ValueError(f"{label} is not synchronized: {details}")


def evaluate_constant(node: ast.AST, values: Dict[str, str]) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Mult)
        and isinstance(node.left, ast.Constant)
        and isinstance(node.left.value, str)
        and isinstance(node.right, ast.Constant)
        and isinstance(node.right.value, int)
    ):
        return node.left.value * node.right.value
    raise ValueError(f"unsupported configuration expression: {ast.dump(node)}")


def read_python_constants(path: Path, class_name: str = "") -> Dict[str, str]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    statements = module.body
    if class_name:
        class_node = next(
            (
                node
                for node in module.body
                if isinstance(node, ast.ClassDef) and node.name == class_name
            ),
            None,
        )
        if class_node is None:
            raise ValueError(f"{path} does not define {class_name}")
        statements = class_node.body

    values = {}
    for statement in statements:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        target = statement.targets[0] if isinstance(statement, ast.Assign) else statement.target
        value_node = statement.value
        if not isinstance(target, ast.Name) or value_node is None:
            continue
        try:
            values[target.id] = evaluate_constant(value_node, values)
        except ValueError:
            continue
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="permit the checksum/source placeholders used before canonical promotion",
    )
    parser.add_argument(
        "--print-runner-filename",
        action="store_true",
        help="print only the verified canonical Runner filename",
    )
    parser.add_argument(
        "--print-runner-source-commit",
        action="store_true",
        help="print only the verified canonical Runner source commit",
    )
    args = parser.parse_args()

    package_constants = read_python_constants(ROOT / "pyzxing" / "__version__.py")
    config = read_python_constants(ROOT / "pyzxing" / "config.py", "Config")
    package_version = package_constants["__version__"]
    config["VERSION"] = package_version

    pom_text = (ROOT / "java-runner" / "pom.xml").read_text(encoding="utf-8")
    pom_version_match = re.search(
        r"<artifactId>pyzxing-runner</artifactId>\s*<version>([^<]+)</version>", pom_text
    )
    zxing_version_match = re.search(r"<zxing\.version>([^<]+)</zxing\.version>", pom_text)
    final_name_match = re.search(r"<finalName>([^<]+)</finalName>", pom_text)
    if pom_version_match is None or zxing_version_match is None or final_name_match is None:
        raise ValueError("java-runner/pom.xml is missing project version, zxing.version, or finalName")
    pom_version = pom_version_match.group(1)
    zxing_version = zxing_version_match.group(1)
    final_name = final_name_match.group(1)

    conda_path = ROOT / "conda-recipe" / "meta.yaml"
    conda_text = conda_path.read_text(encoding="utf-8")
    conda = read_conda_variables(conda_path)
    required_conda = {
        "version",
        "runner_version",
        "zxing_version",
        "runner_filename",
        "runner_sha256",
        "runner_source_commit",
    }
    missing = sorted(required_conda.difference(conda))
    if missing:
        raise ValueError(f"conda-recipe/meta.yaml is missing variables: {', '.join(missing)}")
    required_recipe_lines = {
        "url: https://github.com/ChenjieXu/pyzxing/releases/download/"
        "v{{ runner_version }}/{{ runner_filename }}",
        "fn: {{ runner_filename }}",
        "sha256: {{ runner_sha256 }}",
    }
    for required_line in required_recipe_lines:
        if required_line not in conda_text:
            raise ValueError(f"conda-recipe/meta.yaml is missing canonical source line: {required_line}")

    require_equal(
        "package/Runner version",
        {
            "pyzxing.__version__": package_version,
            "Config.VERSION": config["VERSION"],
            "Config.RUNNER_VERSION": config["RUNNER_VERSION"],
            "Config.JAR_RELEASE_VERSION": config["JAR_RELEASE_VERSION"],
            "pom project.version": pom_version,
            "conda version": conda["version"],
            "conda runner_version": conda["runner_version"],
        },
    )
    require_equal(
        "ZXing version",
        {
            "Config.DEFAULT_ZXING_VERSION": config["DEFAULT_ZXING_VERSION"],
            "pom zxing.version": zxing_version,
            "conda zxing_version": conda["zxing_version"],
        },
    )

    expected_name = f"pyzxing-runner-{pom_version}-zxing-{zxing_version}.jar"
    interpolated_final_name = (
        final_name.replace("${project.version}", pom_version)
        .replace("${zxing.version}", zxing_version)
        + ".jar"
    )
    require_equal(
        "canonical Runner filename",
        {
            "derived filename": expected_name,
            "Config.JAR_FILENAME": config["JAR_FILENAME"],
            "pom finalName": interpolated_final_name,
            "conda runner_filename": conda["runner_filename"],
        },
    )

    expected_url = (
        f"https://github.com/ChenjieXu/pyzxing/releases/download/v{pom_version}/{expected_name}"
    )
    configured_url = config["JAR_URL_PREFIX"].format(version=config["JAR_RELEASE_VERSION"]) + config["JAR_FILENAME"]
    if configured_url != expected_url:
        raise ValueError(
            f"Config.get_jar_url() is {configured_url!r}, expected {expected_url!r}"
        )

    require_equal(
        "canonical Runner SHA-256",
        {
            "Config.JAR_SHA256": config["JAR_SHA256"],
            "conda runner_sha256": conda["runner_sha256"],
        },
    )
    require_equal(
        "canonical Runner source commit",
        {
            "Config.RUNNER_SOURCE_COMMIT": config["RUNNER_SOURCE_COMMIT"],
            "conda runner_source_commit": conda["runner_source_commit"],
        },
    )

    checksum_is_placeholder = config["JAR_SHA256"] == "0" * 64
    commit_is_placeholder = config["RUNNER_SOURCE_COMMIT"] == ""
    if checksum_is_placeholder != commit_is_placeholder:
        raise ValueError("Runner checksum and source commit must be finalized together")
    if checksum_is_placeholder:
        if not args.allow_placeholders:
            raise ValueError("canonical Runner checksum/source commit placeholders are not publishable")
    else:
        if SHA256_RE.fullmatch(config["JAR_SHA256"]) is None:
            raise ValueError("Config.JAR_SHA256 must be one lowercase SHA-256")
        if COMMIT_RE.fullmatch(config["RUNNER_SOURCE_COMMIT"]) is None:
            raise ValueError("Config.RUNNER_SOURCE_COMMIT must be one lowercase full commit SHA")

    if args.print_runner_filename and args.print_runner_source_commit:
        raise ValueError("select only one print-only output")
    if args.print_runner_filename:
        print(expected_name)
    elif args.print_runner_source_commit:
        print(config["RUNNER_SOURCE_COMMIT"])
    else:
        print(
            f"synchronized: pyzxing={pom_version} zxing={zxing_version} "
            f"asset={expected_name} finalized={not checksum_is_placeholder}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

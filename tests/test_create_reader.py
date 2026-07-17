import hashlib
from types import SimpleNamespace

import pytest

from pyzxing import BarCodeReader, DecodeError, JavaNotFoundError
from pyzxing.config import Config


def test_reader_initialization_is_lazy(monkeypatch, tmp_path):
    def unexpected_download(*args, **kwargs):
        raise AssertionError("initialization must not download the JAR")

    monkeypatch.setattr("pyzxing.reader.get_file", unexpected_download)
    reader = BarCodeReader(cache_dir=tmp_path, build_dir=tmp_path / "missing")
    assert reader.lib_path is None


def test_reader_uses_valid_cached_jar(monkeypatch, tmp_path):
    monkeypatch.delenv("PYZXING_TEST_JAR", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    cached_jar = tmp_path / Config.JAR_FILENAME
    cached_jar.write_bytes(b"fixture jar")
    monkeypatch.setattr("pyzxing.utils.sha256", lambda path: Config.JAR_SHA256)

    reader = BarCodeReader(cache_dir=tmp_path, build_dir=tmp_path / "missing")
    assert reader._ensure_jar() == str(cached_jar)


def test_reader_downloads_into_isolated_cache(monkeypatch, tmp_path):
    monkeypatch.delenv("PYZXING_TEST_JAR", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    expected = tmp_path / Config.JAR_FILENAME

    def fake_download(fname, origin, cache_dir, **kwargs):
        assert cache_dir == tmp_path
        assert kwargs["expected_sha256"] == Config.JAR_SHA256
        expected.write_bytes(b"test jar")
        return str(expected)

    monkeypatch.setattr("pyzxing.reader.get_file", fake_download)
    reader = BarCodeReader(cache_dir=tmp_path, build_dir=tmp_path / "missing")
    assert reader._ensure_jar() == str(expected)


def test_missing_java_has_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setattr("pyzxing.reader.shutil.which", lambda command: None)
    with pytest.raises(JavaNotFoundError, match="Install JDK 17"):
        BarCodeReader(cache_dir=tmp_path)


def test_runner_release_coordinates_are_versioned():
    assert Config.RUNNER_VERSION == "1.2.2"
    assert Config.DEFAULT_ZXING_VERSION == "3.5.4"
    assert Config.JAR_FILENAME == "pyzxing-runner-1.2.2-zxing-3.5.4.jar"
    assert Config.get_jar_url() == (
        "https://github.com/ChenjieXu/pyzxing/releases/download/v1.2.2/"
        "pyzxing-runner-1.2.2-zxing-3.5.4.jar"
    )


def test_reader_uses_checksum_verified_interpreter_prefix_runner(
        monkeypatch, tmp_path):
    payload = b"interpreter prefix runner"
    expected_sha256 = hashlib.sha256(payload).hexdigest()
    installed_jar = (
        tmp_path / "share" / "pyzxing" / "runner" / Config.JAR_FILENAME
    )
    installed_jar.parent.mkdir(parents=True)
    installed_jar.write_bytes(payload)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.setattr(
        "pyzxing.reader.sys", SimpleNamespace(prefix=str(tmp_path))
    )
    monkeypatch.setattr(Config, "JAR_SHA256", expected_sha256)

    reader = BarCodeReader(
        cache_dir=tmp_path / "cache",
        build_dir=tmp_path / "missing",
        java_command="java",
    )
    assert reader._ensure_jar() == str(installed_jar)


def test_reader_prefers_interpreter_prefix_over_stale_conda_prefix(
        monkeypatch, tmp_path):
    active_prefix = tmp_path / "active"
    stale_prefix = tmp_path / "stale"
    installed_jar = (
        active_prefix / "share" / "pyzxing" / "runner" / Config.JAR_FILENAME
    )
    stale_jar = (
        stale_prefix / "share" / "pyzxing" / "runner" / Config.JAR_FILENAME
    )
    installed_jar.parent.mkdir(parents=True)
    stale_jar.parent.mkdir(parents=True)
    installed_jar.write_bytes(b"active runner")
    stale_jar.write_bytes(b"tampered stale runner")
    monkeypatch.setattr(
        "pyzxing.reader.sys", SimpleNamespace(prefix=str(active_prefix))
    )
    monkeypatch.setenv("CONDA_PREFIX", str(stale_prefix))
    monkeypatch.setattr(
        Config,
        "JAR_SHA256",
        hashlib.sha256(installed_jar.read_bytes()).hexdigest(),
    )

    reader = BarCodeReader(
        cache_dir=tmp_path / "cache",
        build_dir=tmp_path / "missing",
        java_command="java",
    )
    assert reader._ensure_jar() == str(installed_jar)


def test_reader_rejects_tampered_interpreter_prefix_runner(
        monkeypatch, tmp_path):
    active_prefix = tmp_path / "active"
    stale_prefix = tmp_path / "stale"
    installed_jar = (
        active_prefix / "share" / "pyzxing" / "runner" / Config.JAR_FILENAME
    )
    stale_jar = (
        stale_prefix / "share" / "pyzxing" / "runner" / Config.JAR_FILENAME
    )
    installed_jar.parent.mkdir(parents=True)
    stale_jar.parent.mkdir(parents=True)
    installed_jar.write_bytes(b"tampered active runner")
    stale_jar.write_bytes(b"otherwise valid runner")
    monkeypatch.setattr(
        "pyzxing.reader.sys", SimpleNamespace(prefix=str(active_prefix))
    )
    monkeypatch.setenv("CONDA_PREFIX", str(stale_prefix))
    monkeypatch.setattr(
        Config,
        "JAR_SHA256",
        hashlib.sha256(stale_jar.read_bytes()).hexdigest(),
    )

    reader = BarCodeReader(
        cache_dir=tmp_path / "cache",
        build_dir=tmp_path / "missing",
        java_command="java",
    )
    with pytest.raises(DecodeError, match="Installed Runner SHA-256 mismatch"):
        reader._ensure_jar()

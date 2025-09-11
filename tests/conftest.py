"""
Pytest configuration and fixtures.
"""
import os
import tempfile
import pytest
from pyzxing import BarCodeReader


@pytest.fixture
def test_data_dir():
    """Return the test data directory path."""
    return os.path.join(os.path.dirname(__file__), '..', 'src', 'resources')


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_barcode_files(test_data_dir):
    """Return paths to sample barcode files."""
    return {
        'codabar': os.path.join(test_data_dir, 'codabar.png'),
        'code39': os.path.join(test_data_dir, 'code39.png'),
        'code128': os.path.join(test_data_dir, 'code128.png'),
        'pdf417': os.path.join(test_data_dir, 'pdf417.png'),
        'qrcode': os.path.join(test_data_dir, 'qrcode.png'),
        'multibarcodes': os.path.join(test_data_dir, 'multibarcodes.jpg'),
        'no_barcode': os.path.join(test_data_dir, 'ou.jpg'),
    }


@pytest.fixture
def barcode_reader():
    """Return a BarCodeReader instance."""
    return BarCodeReader()


@pytest.fixture
def corrupted_file(temp_dir):
    """Create a corrupted image file for testing."""
    corrupted_path = os.path.join(temp_dir, 'corrupted.png')
    with open(corrupted_path, 'wb') as f:
        f.write(b'corrupted image data')
    return corrupted_path


@pytest.fixture
def empty_file(temp_dir):
    """Create an empty file for testing."""
    empty_path = os.path.join(temp_dir, 'empty.png')
    with open(empty_path, 'wb') as f:
        f.write(b'')
    return empty_path


@pytest.fixture
def non_existent_file():
    """Return a path to a non-existent file."""
    return '/path/that/does/not/exist.png'
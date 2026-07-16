"""
Test edge cases and error handling.
"""
import os
import shutil
import pytest
from pyzxing import BarCodeReader, DecodeError
from pyzxing.platform_utils import PlatformUtils


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_corrupted_image_file(self, barcode_reader, corrupted_file):
        """Test handling of corrupted image files."""
        with pytest.raises(DecodeError, match="INVALID_IMAGE") as raised:
            barcode_reader.decode(corrupted_file)
        assert raised.value.code == "INVALID_IMAGE"
    
    def test_empty_file(self, barcode_reader, empty_file):
        """Test handling of empty files."""
        with pytest.raises(DecodeError, match="INVALID_IMAGE") as raised:
            barcode_reader.decode(empty_file)
        assert raised.value.code == "INVALID_IMAGE"
    
    def test_non_existent_file(self, barcode_reader, non_existent_file):
        """Test handling of non-existent files."""
        with pytest.raises(FileNotFoundError):
            barcode_reader.decode(non_existent_file)
    
    def test_invalid_file_pattern(self, barcode_reader):
        """Test handling of invalid file patterns."""
        with pytest.raises(FileNotFoundError):
            barcode_reader.decode('/path/that/does/not/exist/*.png')
    
    def test_real_barcode_in_special_path(
            self, barcode_reader, temp_dir, test_data_dir):
        """Regression for #33: URI escaping must preserve special paths."""
        special_dir = os.path.join(temp_dir, '问题 path 100% #1')
        os.makedirs(special_dir)
        special_path = os.path.join(special_dir, '二维码 #33 100%.png')
        shutil.copyfile(os.path.join(test_data_dir, 'qrcode.png'), special_path)

        result = barcode_reader.decode(special_path)
        with open(os.path.join(test_data_dir, 'qrcode.txt'), 'rb') as stream:
            expected = stream.readline().strip()

        assert result[0]['parsed'] == expected


class TestPlatformUtils:
    """Test platform utility functions."""
    
    def test_normalize_path(self):
        """Test path normalization."""
        # Test Windows path
        if PlatformUtils.is_windows():
            normalized = PlatformUtils.normalize_path('C:/path/to/file')
            assert '\\' in normalized
            assert 'C:\\' in normalized
        
        # Test Unix path
        else:
            normalized = PlatformUtils.normalize_path('C:\\path\\to\\file')
            assert '/' in normalized
            assert '\\' not in normalized
    
    def test_get_java_command(self):
        """Test Java command detection."""
        java_cmd = PlatformUtils.get_java_command()
        assert isinstance(java_cmd, str)
        assert 'java' in java_cmd.lower()
    
    def test_get_process_environment(self):
        """Test environment variable setup."""
        env = PlatformUtils.get_process_environment()
        assert isinstance(env, dict)
        
        assert env == os.environ
    
    def test_decode_output(self):
        """Test output decoding."""
        # Test UTF-8
        utf8_data = '测试数据'.encode('utf-8')
        decoded = PlatformUtils.decode_output(utf8_data)
        assert isinstance(decoded, str)
        
        # Test empty data
        assert PlatformUtils.decode_output(b'') == ''
        
        # Test None
        assert PlatformUtils.decode_output(None) == ''

        # Invalid diagnostic bytes remain visible instead of being discarded.
        assert PlatformUtils.decode_output(b'\xff') == '\ufffd'
    
    def test_get_cache_dir(self):
        """Test cache directory detection."""
        cache_dir = PlatformUtils.get_cache_dir()
        assert isinstance(cache_dir, str)
        assert 'pyzxing' in cache_dir or '.local' in cache_dir
    
    def test_is_windows(self):
        """Test Windows detection."""
        is_win = PlatformUtils.is_windows()
        assert isinstance(is_win, bool)


class TestErrorHandling:
    """Test error handling improvements."""

    def test_barcode_reader_initialization_with_missing_jar(self, monkeypatch, temp_dir):
        """Test BarCodeReader initialization with missing JAR file."""
        monkeypatch.delenv("PYZXING_TEST_JAR", raising=False)
        monkeypatch.delenv("CONDA_PREFIX", raising=False)
        # Mock get_file to raise an exception
        def mock_get_file(*args, **kwargs):
            raise Exception("Network error")
        
        monkeypatch.setattr('pyzxing.reader.get_file', mock_get_file)
        
        with pytest.raises(Exception, match="Network error"):
            BarCodeReader(cache_dir=temp_dir, build_dir=temp_dir)._ensure_jar()

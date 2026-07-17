"""
Configuration settings for pyzxing.
"""
import os
import tempfile


class Config:
    """Configuration constants and settings."""
    
    # Version information
    from .__version__ import __version__
    VERSION = __version__
    MIN_PYTHON_VERSION = '>=3.8.0'
    
    # pyzxing Runner / ZXing settings
    RUNNER_VERSION = '1.2.2'
    DEFAULT_ZXING_VERSION = '3.5.4'
    JAR_RELEASE_VERSION = RUNNER_VERSION
    JAR_URL_PREFIX = "https://github.com/ChenjieXu/pyzxing/releases/download/v{version}/"
    JAR_FILENAME = "pyzxing-runner-1.2.2-zxing-3.5.4.jar"
    # PRE-RELEASE GATE: replace both placeholders from the canonical draft asset.
    JAR_SHA256 = "0000000000000000000000000000000000000000000000000000000000000000"
    RUNNER_SOURCE_COMMIT = ""
    
    # Performance settings
    PARALLEL_THRESHOLD = 3  # Files below this count use sequential processing
    MAX_WORKERS = 4
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB maximum file size
    
    # Path settings
    BUILD_DIR = "java-runner/target"
    TEMP_DIR = os.path.join(tempfile.gettempdir(), 'pyzxing')
    
    # Logging settings
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Error handling settings
    TIMEOUT_SECONDS = 30
    
    @classmethod
    def get_jar_url(cls, release_version=None):
        """Get JAR URL for specific release version."""
        if release_version is None:
            release_version = cls.JAR_RELEASE_VERSION
        return cls.JAR_URL_PREFIX.format(version=release_version) + cls.JAR_FILENAME
    
    @classmethod
    def get_cache_dir(cls):
        """Get cache directory path."""
        if os.name == 'nt':  # Windows
            return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'pyzxing')
        else:  # Unix/Linux/Mac
            return os.path.join(os.path.expanduser('~'), '.local', 'pyzxing')
    
    @classmethod
    def get_temp_dir(cls):
        """Get temporary directory path."""
        return cls.TEMP_DIR

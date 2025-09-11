"""
Configuration settings for pyzxing.
"""
import os


class Config:
    """Configuration constants and settings."""
    
    # Version information
    from .__version__ import __version__
    VERSION = __version__
    MIN_PYTHON_VERSION = '>=3.8.0'
    
    # ZXing settings
    DEFAULT_ZXING_VERSION = '3.4.1'
    JAR_RELEASE_VERSION = '1.1.0'  # Only v1.1.0 has pre-built JAR file
    JAR_URL_PREFIX = "https://github.com/ChenjieXu/pyzxing/releases/download/v{version}/"
    JAR_FILENAME = "javase-{version}-SNAPSHOT-jar-with-dependencies.jar"
    
    # Performance settings
    PARALLEL_THRESHOLD = 3  # Files below this count use sequential processing
    MAX_CACHE_SIZE = 128  # Maximum number of cached results
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB maximum file size
    
    # Path settings
    BUILD_DIR = "zxing/javase/target"
    TEMP_DIR = '.cache'
    
    # Logging settings
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Error handling settings
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30
    
    @classmethod
    def get_jar_url(cls, release_version=None):
        """Get JAR URL for specific release version."""
        if release_version is None:
            # Use v0.1 as default since it's the only release with pre-built JAR
            release_version = cls.JAR_RELEASE_VERSION
        return cls.JAR_URL_PREFIX.format(version=release_version) + cls.JAR_FILENAME.format(version=cls.DEFAULT_ZXING_VERSION)
    
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
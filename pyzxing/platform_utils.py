"""
Platform utilities for cross-platform compatibility.
"""
import os
import platform


class PlatformUtils:
    """Utility class for platform-specific operations."""
    
    @staticmethod
    def normalize_path(path):
        """Normalize path for the current platform."""
        if not path:
            return path
            
        # Convert to absolute path
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        
        # Platform-specific normalization
        if platform.system() == 'Windows':
            # Windows: use backslashes and handle spaces
            path = path.replace('/', '\\')
            if ' ' in path:
                path = f'"{path}"'
        else:
            # Unix: use forward slashes
            path = path.replace('\\', '/')
        
        return path
    
    @staticmethod
    def get_java_command():
        """Get the appropriate Java command for the platform."""
        if platform.system() == 'Windows':
            return 'java.exe'
        else:
            return 'java'
    
    @staticmethod
    def get_process_environment():
        """Preserve the caller's process environment."""
        return os.environ.copy()
    
    @staticmethod
    def decode_output(data):
        """Decode UTF-8 Java diagnostics while preserving invalid-byte evidence."""
        if not data:
            return ''
        return data.decode('utf-8', errors='replace')
    
    @staticmethod
    def is_windows():
        """Check if running on Windows."""
        return platform.system() == 'Windows'
    
    @staticmethod
    def get_cache_dir():
        """Get the appropriate cache directory for the platform."""
        if platform.system() == 'Windows':
            return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'pyzxing')
        else:
            return os.path.join(os.path.expanduser('~'), '.local', 'pyzxing')

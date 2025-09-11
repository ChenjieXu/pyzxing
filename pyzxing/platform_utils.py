"""
Platform utilities for cross-platform compatibility.
"""
import os
import sys
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
        """Get appropriate environment variables for the platform."""
        env = os.environ.copy()
        
        if platform.system() == 'Windows':
            # Windows-specific settings
            env['PYTHONIOENCODING'] = 'utf-8'
            env['JAVA_TOOL_OPTIONS'] = '-Dfile.encoding=UTF-8'
        else:
            # Unix-specific settings
            env['LANG'] = 'en_US.UTF-8'
            env['LC_ALL'] = 'en_US.UTF-8'
        
        return env
    
    @staticmethod
    def decode_output(data):
        """Decode subprocess output with proper encoding handling."""
        if not data:
            return ''
        
        # Try different encodings based on platform
        encodings = ['utf-8']
        
        if platform.system() == 'Windows':
            # Windows: try Chinese encodings too
            encodings.extend(['gbk', 'gb2312', 'big5'])
        
        # Add fallback encodings
        encodings.extend(['latin-1', 'cp1252'])
        
        for encoding in encodings:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # Ultimate fallback
        return data.decode('latin-1', errors='ignore')
    
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
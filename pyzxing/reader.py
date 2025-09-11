import ast
import glob
import logging
import os
import os.path as osp
import re
import shutil
import subprocess
import sys
import uuid
from functools import lru_cache

from joblib import Parallel, delayed

from .utils import get_file
from .platform_utils import PlatformUtils
from .config import Config

preset_jar_url = Config.get_jar_url()
preset_jar_filename = Config.JAR_FILENAME.format(version=Config.DEFAULT_ZXING_VERSION)
build_jar_dir = Config.BUILD_DIR


class BarCodeReader:
    lib_path = ""

    def __init__(self):
        """Prepare necessary jar file."""
        cache_dir = Config.get_cache_dir()
        os.makedirs(cache_dir, exist_ok=True)
        # Check build dir
        build_jar_path = glob.glob(osp.join(build_jar_dir, "javase-*-jar-with-dependencies.jar"))
        if build_jar_path:
            build_jar_filename = build_jar_path[-1].split(osp.sep)[-1]
            # Move built jar file to cache dir
            self.lib_path = osp.join(cache_dir, build_jar_filename)
            if not osp.exists(self.lib_path):
                try:
                    shutil.copyfile(build_jar_path[-1], self.lib_path)
                except Exception as e:
                    logging.error(f"Failed to copy jar file: {e}")
                    raise
        else:
            # Check cache dir
            cache_jar_path = glob.glob(osp.join(cache_dir, "javase-*-jar-with-dependencies.jar"))
            if cache_jar_path:
                self.lib_path = cache_jar_path[-1]
            else:
                # Download preset jar if not built or cache jar
                try:
                    get_file(preset_jar_filename, preset_jar_url, cache_dir)
                    logging.debug("Download completed.")
                except Exception as e:
                    logging.error(f"Failed to download jar file: {e}")
                    logging.error(f"Please ensure internet connection or manually place jar file in {cache_dir}")
                    raise
                self.lib_path = osp.join(cache_dir, preset_jar_filename)

        self.lib_path = '"' + self.lib_path + '"'  # deal with blank in path

    def decode(self, filename_pattern):
        try:
            filenames = glob.glob(osp.abspath(filename_pattern))
            if not len(filenames):
                logging.warning(f"No files found matching pattern: {filename_pattern}")
                raise FileNotFoundError(f"No files found: {filename_pattern}")

            elif len(filenames) == 1:
                results = self._decode(filenames[0].replace('\\', '/').replace(' ', '\\ '))

            elif len(filenames) <= Config.PARALLEL_THRESHOLD:
                # For small number of files, use sequential processing to avoid overhead
                results = [self._decode(filename.replace('\\', '/')) for filename in filenames]

            else:
                # For larger number of files, use parallel processing
                results = Parallel(n_jobs=-1)(
                    delayed(self._decode)(filename.replace('\\', '/'))
                    for filename in filenames)

            return results
        except Exception as e:
            logging.error(f"Error in decode method: {e}")
            raise

    def decode_array(self, array):
        try:
            import cv2 as cv
            temp_dir = Config.get_temp_dir()
            os.makedirs(temp_dir, exist_ok=True)
            filename = osp.join(temp_dir, f'{uuid.uuid4().hex}.jpg')
            
            if len(array.shape) == 3:
                array = array[:, :, ::-1]
            
            # Use better quality settings for JPEG
            cv.imwrite(filename, array, [cv.IMWRITE_JPEG_QUALITY, 90])
            result = self.decode(filename)
            return result
        except ImportError:
            logging.error("OpenCV not installed. Please install opencv-python to use decode_array method.")
            raise
        except Exception as e:
            logging.error(f"Error in decode_array method: {e}")
            raise
        finally:
            # Clean up temporary file
            if 'filename' in locals() and osp.exists(filename):
                try:
                    os.remove(filename)
                except Exception as e:
                    logging.warning(f"Failed to remove temporary file {filename}: {e}")

    def _decode(self, filename):
        try:
            cmd = ' '.join(
                [PlatformUtils.get_java_command(), '-jar', self.lib_path, 'file:///' + filename, '--multi', '--try_harder'])
            
            # Setup environment variables for better encoding support
            env = PlatformUtils.get_process_environment()
            
            process = subprocess.Popen(cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     shell=True,
                                     env=env)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error_msg = PlatformUtils.decode_output(stderr)
                logging.error(f"Java process failed with return code {process.returncode}")
                logging.error(f"Error output: {error_msg}")
                return []
            
            lines = stdout.splitlines()
            if not lines:
                return []
            
            separator_idx = [
                                i for i in range(len(lines)) if lines[i].startswith(b'file')
                            ] + [len(lines)]

            result = [
                self._parse_single(lines[separator_idx[i]:separator_idx[i + 1]])
                for i in range(len(separator_idx) - 1)
            ]
            return result
            
        except Exception as e:
            logging.error(f"Failed to execute subprocess: {e}")
            return []

    @staticmethod
    def _parse_single(lines):
        """parse stdout and return structured result

            raw stdout looks like this:
            file://02.png (format: CODABAR, type: TEXT):
            Raw result:
            0000
            Parsed result:
            0000
            Found 2 result points.
            Point 0: (50.0,202.0)
            Point 1: (655.0,202.0)
        """
        result = {}
        
        if not lines:
            return result
            
        # Parse filename
        result['filename'] = lines[0].split(b' ', 1)[0]

        if len(lines) > 1:
            # Parse header line more efficiently
            header_line = lines[0].split(b' ', 1)[1]
            for ch in [b'(', b')', b':', b',']:
                header_line = header_line.replace(ch, b'')
            
            header_parts = header_line.split(b' ')
            if len(header_parts) >= 4:
                _, result['format'], _, result['type'] = header_parts[:4]

            # Find indices efficiently
            raw_index = find_line_index(lines, b"Raw result:", 1)
            parsed_index = find_line_index(lines, b"Parsed result:", raw_index)
            points_index = find_line_index(lines, b"Found", parsed_index)

            if not raw_index or not parsed_index or not points_index:
                logging.warning("Parse error: could not find required output sections")
                return result  # Return partial result

            # Extract raw and parsed results efficiently
            result['raw'] = b'\n'.join(lines[raw_index + 1:parsed_index])
            result['parsed'] = b'\n'.join(lines[parsed_index + 1:points_index])

            # Parse points more efficiently
            points_start = points_index + 1
            points_end = points_start + sum(1 for line in lines[points_start:] if b'Point' in line)
            
            result['points'] = []
            for line in lines[points_start:points_end]:
                try:
                    if b':' in line:
                        point_str = line.split(b": ", 1)[1].decode()
                        result['points'].append(ast.literal_eval(point_str))
                except (ValueError, SyntaxError) as e:
                    logging.warning(f"Failed to parse point: {line}, error: {e}")
                    continue

        return result


def find_line_index(lines, content, start=0):
    for i in range(start, len(lines)):
        if lines[i].startswith(content):
            return i

    return None

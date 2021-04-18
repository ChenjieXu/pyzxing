import ast
import glob
import logging
import os
import os.path as osp
import re
import shutil
import subprocess

from joblib import Parallel, delayed

from .utils import get_file

preset_jar_url_prefix = "https://github.com/ChenjieXu/pyzxing/releases/download/v0.1/"
preset_jar_filename = "javase-3.4.1-SNAPSHOT-jar-with-dependencies.jar"
build_jar_dir = str(osp.sep).join(["zxing", "javase", "target"])


class BarCodeReader:
    lib_path = ""

    def __init__(self):
        """Prepare necessary jar file."""
        cache_dir = osp.join(osp.expanduser('~'), '.local')
        os.makedirs(cache_dir, exist_ok=True)
        # Check build dir
        build_jar_path = glob.glob(osp.join(build_jar_dir, "javase-*-jar-with-dependencies.jar"))
        if build_jar_path:
            build_jar_filename = build_jar_path[-1].split(osp.sep)[-1]
            # Move built jar file to cache dir
            self.lib_path = osp.join(cache_dir, build_jar_filename)
            if not osp.exists(self.lib_path):
                shutil.copyfile(build_jar_path[-1], self.lib_path)
            return
        # Check cache dir
        cache_jar_path = glob.glob(osp.join(cache_dir, "javase-*-jar-with-dependencies.jar"))
        if cache_jar_path:
            self.lib_path = cache_jar_path[-1]
            return
        else:
            # Download preset jar if not built or cache jar
            download_url = osp.join(preset_jar_url_prefix, preset_jar_filename)
            get_file(preset_jar_filename, download_url, cache_dir)
            logging.debug("Download completed.")
            self.lib_path = osp.join(cache_dir, preset_jar_filename)

    def decode(self, filename_pattern):
        filenames = glob.glob(osp.abspath(filename_pattern))
        if not len(filenames):
            raise FileNotFoundError

        elif len(filenames) == 1:
            results = self._decode(filenames[0].replace('\\', '/'))

        else:
            results = Parallel(n_jobs=-1)(
                delayed(self._decode)(filename.replace('\\', '/'))
                for filename in filenames)

        return results

    def decode_array(self, array):
        import cv2 as cv
        import time
        os.makedirs('.cache', exist_ok=True)
        filename = f'.cache/{time.time()}.jpg'
        if len(array.shape) == 3:
            array = array[:, :, ::-1]
        cv.imwrite(filename, array)
        result = self.decode(filename)
        os.remove(filename)

        return result

    def _decode(self, filename):
        cmd = ' '.join(
            ['java -jar', self.lib_path, 'file:///' + filename, '--multi', '--try_harder'])
        (stdout, _) = subprocess.Popen(cmd,
                                       stdout=subprocess.PIPE,
                                       # universal_newlines=True,
                                       shell=True).communicate()
        lines = stdout.splitlines()
        separator_idx = [
                            i for i in range(len(lines)) if lines[i].startswith(b'file')
                        ] + [len(lines)]

        result = [
            self._parse_single(lines[separator_idx[i]:separator_idx[i + 1]])
            for i in range(len(separator_idx) - 1)
        ]
        return result

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
        result = dict()
        result['filename'] = lines[0].split(b' ', 1)[0]

        if len(lines) > 1:
            lines[0] = lines[0].split(b' ', 1)[1]
            for ch in [b'(', b')', b':', b',']:
                lines[0] = lines[0].replace(ch, b'')
            _, result['format'], _, result['type'] = lines[0].split(b' ')

            raw_index = find_line_index(lines, b"Raw result:", 1)
            parsed_index = find_line_index(lines, b"Parsed result:", raw_index)
            points_index = find_line_index(lines, b"Found", parsed_index)

            if not raw_index or not parsed_index or not points_index:
                raise Exception("Parse Error")

            result['raw'] = b'\n'.join(lines[raw_index + 1:parsed_index])
            result['parsed'] = b'\n'.join(lines[parsed_index + 1:points_index])

            points_num = int(re.search(r"(?<=Found )\d?", lines[points_index].decode()).group())
            result['points'] = [
                ast.literal_eval(line.split(b": ")[1].decode())
                for line in lines[points_index + 1:points_index + 1 + points_num]
            ]

        return result


def find_line_index(lines, content, start=0):
    for i in range(start, len(lines)):
        if lines[i].startswith(content):
            return i

    return None

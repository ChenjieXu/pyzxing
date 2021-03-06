import ast
import glob
import os
import shutil
import subprocess

from joblib import Parallel, delayed

from .utils import get_file

jar_filename = "javase-3.4.1-SNAPSHOT-jar-with-dependencies.jar"
jar_url = "https://github.com/ChenjieXu/pyzxing/releases/download/v0.1/"
jar_path = "zxing/javase/target/"


class BarCodeReader:
    command = "java -jar"
    lib_path = ""

    def __init__(self):
        """Prepare necessary jar file."""
        cache_dir = os.path.join(os.path.expanduser('~'), '.local')
        res = glob.glob(jar_path + "javase-*-jar-with-dependencies.jar")
        if res:
            self.lib_path = res[0]
            os.makedirs(cache_dir, exist_ok=True)
            shutil.move(res[0], cache_dir)
        else:
            print("Use local jar file.")
            download_url = os.path.join(jar_url, jar_filename)
            save_path = os.path.join(cache_dir, jar_filename)
            if not os.path.exists(save_path):
                get_file(jar_filename, download_url, cache_dir)
                print("Download completed.")
            self.lib_path = save_path

    def decode(self, filename_pattern):
        filenames = glob.glob(os.path.abspath(filename_pattern))
        if len(filenames) == 0:
            print("File not found!")
            results = None

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

        return self.decode(filename)

    def _decode(self, filename):
        cmd = ' '.join(
            [self.command, self.lib_path, 'file:///' + filename, '--multi'])
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

            raw_index = find_line_index(lines, b"Raw result:")
            parsed_index = find_line_index(lines, b"Parsed result:")
            points_index = find_line_index(lines, b"Found")

            if not raw_index or not parsed_index or not points_index:
                raise Exception("Parse Error")

            result['raw'] = b'\n'.join(lines[raw_index + 1:parsed_index])
            result['parsed'] = b'\n'.join(lines[parsed_index + 1:points_index])
            result['points'] = [
                ast.literal_eval(line.split(b": ")[1].decode())
                for line in lines[points_index + 1:-1]
            ]

        return result


def find_line_index(lines, content):
    for i, line in enumerate(lines):
        if line.startswith(content):
            return i

    return None

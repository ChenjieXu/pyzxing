import glob
import os.path as osp
import shutil
import unittest

from pyzxing import BarCodeReader
from pyzxing.reader import build_jar_dir
from pyzxing.utils import get_file


class TestCreateBarCodeReader(unittest.TestCase):
    def test_create_reader_no_local(self):
        cache_dir = osp.join(osp.expanduser('~'), '.local')
        if osp.exists(cache_dir):
            shutil.rmtree(cache_dir)
        if osp.exists(build_jar_dir):
            shutil.rmtree(build_jar_dir)
        self.reader = BarCodeReader()

    def test_create_reader_with_built_jar(self):
        cache_dir = osp.join(osp.expanduser('~'), '.local')
        if osp.exists(cache_dir):
            shutil.rmtree(cache_dir)
        # Check build dir
        build_jar_path = glob.glob(osp.join(build_jar_dir, "javase-*-jar-with-dependencies.jar"))
        if not build_jar_path:
            # Prepare fake built jar file
            from pyzxing.reader import preset_jar_url_prefix, preset_jar_filename
            build_jar_dir_abs = osp.join(osp.abspath('.'), build_jar_dir)
            download_url = osp.join(preset_jar_url_prefix, preset_jar_filename)
            get_file(preset_jar_filename, download_url, build_jar_dir_abs)

        self.reader = BarCodeReader()

    def test_create_reader_with_cache_jar(self):
        self.reader = BarCodeReader()

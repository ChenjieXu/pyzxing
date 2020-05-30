import os
import shutil
import unittest
from pyzxing import BarCodeReader
from pyzxing.reader import jar_filename, jar_path


class TestCreateBarCodeReader(unittest.TestCase):
    def test_create_reader_no_local(self):
        if os.path.exists(jar_path+jar_filename):
            os.remove(jar_path+jar_filename)
        self.reader = BarCodeReader()

    def test_create_reader_with_local(self):
        if os.path.exists(jar_path):
            shutil.rmtree(jar_path)
        self.reader = BarCodeReader()
        self.reader = BarCodeReader()

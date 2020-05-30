import unittest
from pyzxing import BarCodeReader


class TestBarCodeReaderDecode(unittest.TestCase):
    def setUp(self):
        self.reader = BarCodeReader()

    def test_codabar(self):
        basename = 'src/resources/codabar'
        result = self.reader.decode(basename + '.png')
        with open(basename+'.txt', 'r') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result['parsed'], gt)

    def test_code39(self):
        basename = 'src/resources/code39'
        result = self.reader.decode(basename + '.png')
        with open(basename+'.txt', 'r') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result['parsed'], gt)

    def test_code128(self):
        basename = 'src/resources/code128'
        result = self.reader.decode(basename + '.png')
        with open(basename+'.txt', 'r') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result['parsed'], gt)

    def test_pdf417(self):
        basename = 'src/resources/pdf417'
        result = self.reader.decode(basename + '.png')
        with open(basename+'.txt', 'r') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result['parsed'], gt)

    def test_qrcode(self):
        basename = 'src/resources/qrcode'
        result = self.reader.decode(basename + '.png')
        with open(basename+'.txt', 'r') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result['parsed'], gt)

    def test_nonexistfile(self):
        basename = 'src/resources/nonexistfile'
        result = self.reader.decode(basename + '.png')
        self.assertEqual(result, None)

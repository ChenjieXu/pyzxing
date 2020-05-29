import unittest
from pyzxing import BarCodeReader


class TestBarCodeReader(unittest.TestCase):
    def setUp(self):
        self.reader = BarCodeReader()

    def test_codabar(self):
        basename = 'test/resources/codabar'
        result = self.reader.decode(basename + '.png')
        with open(basename+'.txt', 'r') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result['parsed'], gt)

    def test_code39(self):
        basename = 'test/resources/code39'
        result = self.reader.decode(basename + '.png')
        with open(basename+'.txt', 'r') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result['parsed'], gt)

    def test_code128(self):
        basename = 'test/resources/code128'
        result = self.reader.decode(basename + '.png')
        with open(basename+'.txt', 'r') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result['parsed'], gt)

    def test_pdf417(self):
        basename = 'test/resources/pdf417'
        result = self.reader.decode(basename + '.png')
        with open(basename+'.txt', 'r') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result['parsed'], gt)

    def test_qrcode(self):
        basename = 'test/resources/qrcode'
        result = self.reader.decode(basename + '.png')
        with open(basename+'.txt', 'r') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result['parsed'], gt)


if __name__ == '__main__':
    unittest.main()

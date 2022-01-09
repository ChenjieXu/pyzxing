import os
import glob
import unittest
from pyzxing import BarCodeReader


class TestBarCodeReaderDecode(unittest.TestCase):
    def setUp(self):
        self.reader = BarCodeReader()

    def test_codabar(self):
        basename = 'src/resources/codabar'
        result = self.reader.decode(basename + '.png')
        with open(basename + '.txt', 'rb') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result[0]['parsed'], gt)

    def test_code39(self):
        basename = 'src/resources/code39'
        result = self.reader.decode(basename + '.png')
        with open(basename + '.txt', 'rb') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result[0]['parsed'], gt)

    def test_code128(self):
        basename = 'src/resources/code128'
        result = self.reader.decode(basename + '.png')
        with open(basename + '.txt', 'rb') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result[0]['parsed'], gt)

    def test_pdf417(self):
        basename = 'src/resources/pdf417'
        result = self.reader.decode(basename + '.png')
        with open(basename + '.txt', 'rb') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result[0]['parsed'], gt)

    def test_qrcode(self):
        basename = 'src/resources/qrcode'
        result = self.reader.decode(basename + '.png')
        with open(basename + '.txt', 'rb') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result[0]['parsed'], gt)

    def test_nonexistfile(self):
        basename = 'src/resources/nonexistfile'
        try:
            result = self.reader.decode(basename + '.png')
            raise Exception('Exception not raise properly')
        except FileNotFoundError as e:
            pass
        except Exception as e:
            raise e

    def test_nobarcodefile(self):
        basename = 'src/resources/ou'
        result = self.reader.decode(basename + '.jpg')
        self.assertEqual(result[0].get('parsed', None), None)

    def test_multibarcodes(self):
        basename = 'src/resources/multibarcodes'
        results = self.reader.decode(basename + '.jpg')
        result_string = [result['parsed'] for result in results]

        with open(basename + '.txt', 'rb') as fp:
            gt = [line.strip() for line in fp.readlines()]

        self.assertEqual(set(result_string), set(gt))

    def test_multifiles(self):
        filename_pattern = 'src/resources/*.png'
        results = self.reader.decode(filename_pattern)
        results_string = [x['parsed'] for result in results for x in result]

        filenames = glob.glob(filename_pattern)
        annofiles = [
            os.path.splitext(filename.replace('\\', '/'))[0] + '.txt'
            for filename in filenames
        ]
        gt = []
        for annofile in annofiles:
            with open(annofile, 'rb') as fp:
                gt.append(fp.readline().strip())

        self.assertEqual(set(results_string), set(gt))

import os
import glob
import unittest
import logging
from pyzxing import BarCodeReader


class TestBarCodeReaderDecode(unittest.TestCase):
    def setUp(self):
        self.reader = BarCodeReader()
        # Set up logging for tests
        logging.basicConfig(level=logging.DEBUG)

    def test_codabar(self):
        basename = 'src/resources/codabar'
        result = self.reader.decode(basename + '.png')
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        with open(basename + '.txt', 'rb') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result[0]['parsed'], gt)
    
    def test_codabar_result_structure(self):
        """Test that codabar result has proper structure."""
        basename = 'src/resources/codabar'
        result = self.reader.decode(basename + '.png')
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        barcode = result[0]
        self.assertIn('filename', barcode)
        self.assertIn('format', barcode)
        self.assertIn('parsed', barcode)
        self.assertIn('raw', barcode)
        self.assertIn('points', barcode)

    def test_code39(self):
        basename = 'src/resources/code39'
        result = self.reader.decode(basename + '.png')
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        with open(basename + '.txt', 'rb') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result[0]['parsed'], gt)

    def test_code128(self):
        basename = 'src/resources/code128'
        result = self.reader.decode(basename + '.png')
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        with open(basename + '.txt', 'rb') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result[0]['parsed'], gt)

    def test_pdf417(self):
        basename = 'src/resources/pdf417'
        result = self.reader.decode(basename + '.png')
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        with open(basename + '.txt', 'rb') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result[0]['parsed'], gt)

    def test_qrcode(self):
        basename = 'src/resources/qrcode'
        result = self.reader.decode(basename + '.png')
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        with open(basename + '.txt', 'rb') as fp:
            gt = fp.readline().strip()
        self.assertEqual(result[0]['parsed'], gt)

    def test_nonexistfile(self):
        basename = 'src/resources/nonexistfile'
        with self.assertRaises(FileNotFoundError):
            self.reader.decode(basename + '.png')

    def test_nobarcodefile(self):
        basename = 'src/resources/ou'
        result = self.reader.decode(basename + '.jpg')
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIsNone(result[0].get('parsed', None))

    def test_multibarcodes(self):
        basename = 'src/resources/multibarcodes'
        results = self.reader.decode(basename + '.jpg')
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        result_string = [result['parsed'] for result in results if result.get('parsed')]

        with open(basename + '.txt', 'rb') as fp:
            gt = [line.strip() for line in fp.readlines()]

        self.assertEqual(set(result_string), set(gt))

    def test_multifiles(self):
        filename_pattern = 'src/resources/*.png'
        results = self.reader.decode(filename_pattern)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        results_string = [x['parsed'] for result in results for x in result if x.get('parsed')]

        filenames = glob.glob(filename_pattern)
        annofiles = [
            os.path.splitext(filename.replace('\\', '/'))[0] + '.txt'
            for filename in filenames
        ]
        gt = []
        for annofile in annofiles:
            if os.path.exists(annofile):
                with open(annofile, 'rb') as fp:
                    gt.append(fp.readline().strip())

        self.assertEqual(set(results_string), set(gt))

import glob
import os

import pytest


class TestBarCodeReaderDecode:
    def test_codabar(self, barcode_reader):
        basename = 'src/resources/codabar'
        result = barcode_reader.decode(basename + '.png')
        assert isinstance(result, list)
        assert result

        with open(basename + '.txt', 'rb') as stream:
            expected = stream.readline().strip()
        assert result[0]['parsed'] == expected

    def test_codabar_result_structure(self, barcode_reader):
        result = barcode_reader.decode('src/resources/codabar.png')
        assert result

        barcode = result[0]
        for field in ('filename', 'format', 'parsed', 'raw', 'points'):
            assert field in barcode
        assert all(isinstance(point, tuple) for point in barcode['points'])

    def test_code39(self, barcode_reader):
        self._assert_decoded_payload(barcode_reader, 'src/resources/code39')

    def test_code128(self, barcode_reader):
        self._assert_decoded_payload(barcode_reader, 'src/resources/code128')

    def test_pdf417(self, barcode_reader):
        self._assert_decoded_payload(barcode_reader, 'src/resources/pdf417')

    def test_qrcode(self, barcode_reader):
        self._assert_decoded_payload(barcode_reader, 'src/resources/qrcode')

    def test_nonexistfile(self, barcode_reader):
        with pytest.raises(FileNotFoundError):
            barcode_reader.decode('src/resources/nonexistfile.png')

    def test_nobarcodefile(self, barcode_reader):
        result = barcode_reader.decode('src/resources/ou.jpg')
        assert result
        assert result[0].get('parsed') is None

    def test_multibarcodes(self, barcode_reader):
        results = barcode_reader.decode('src/resources/multibarcodes.jpg')
        assert results
        decoded = [result['parsed'] for result in results if result.get('parsed')]

        with open('src/resources/multibarcodes.txt', 'rb') as stream:
            expected = [line.strip() for line in stream]
        assert set(decoded) == set(expected)

    def test_multifiles(self, barcode_reader):
        filename_pattern = 'src/resources/*.png'
        results = barcode_reader.decode(filename_pattern)
        assert results
        decoded = [result['parsed'] for result in results if result.get('parsed')]

        annotation_files = [
            os.path.splitext(filename.replace('\\', '/'))[0] + '.txt'
            for filename in glob.glob(filename_pattern)
        ]
        expected = []
        for annotation_file in annotation_files:
            if os.path.exists(annotation_file):
                with open(annotation_file, 'rb') as stream:
                    expected.append(stream.readline().strip())
        assert set(decoded) == set(expected)

    @staticmethod
    def _assert_decoded_payload(barcode_reader, basename):
        result = barcode_reader.decode(basename + '.png')
        assert result
        with open(basename + '.txt', 'rb') as stream:
            expected = stream.readline().strip()
        assert result[0]['parsed'] == expected

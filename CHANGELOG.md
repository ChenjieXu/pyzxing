Unreleased

1.2.2 (17 July 2026)
- Restore automatic Runner downloads with newly versioned immutable release coordinates
- Rebuild the canonical ZXing 3.5.4 Runner and publish synchronized Python and conda metadata
- Reorganize the English and Chinese README files and add versioned Sphinx documentation for Read the Docs

1.2.1 (17 July 2026)
- Upgrade the bundled Jackson Databind runtime to 2.18.9 to address two high- and two medium-severity security advisories
- Add an OpenCV webcam demonstration that periodically samples frames through the existing one-shot `decode_array()` API

1.2.0 (16 July 2026)
- Replace ZXing's prose-oriented CLI with a versioned pyzxing JSONL Runner built on ZXing 3.5.4
- Preserve the existing byte-valued result fields while adding text, raw bytes, byte segments, metadata, numeric points, and orientation source
- Add `multi`, `try_harder`, `pure_barcode`, `character_set`, and `possible_formats` decode hints
- Preserve binary QR BYTE segments as Base64 across the Java/Python boundary instead of reconstructing them from decoded text
- Normalize public orientation to clockwise image rotation, preserve raw ZXing correction orientation in metadata, and derive QR orientation only from ordered finder points when reliable
- Fix URI handling for paths containing non-ASCII text, spaces, `%`, or `#`
- Invoke Java without a shell and add explicit timeout/runtime errors
- Publish a pyzxing-owned Runner JAR, checksum, and source commit before PyPI artifacts, and coordinate verified concurrent cache writes
- Return one flat barcode-result list for both single-file and glob decoding
- Isolate tests from user cache directories and add security/runtime regressions
- Document binary/orientation semantics, PyInstaller bundling, decode-only scope, and format-support boundaries
- Add synchronized package/Runner/ZXing/conda metadata gates and a provenance-first workflow that publishes only a verified draft Release
- Package the checksum-pinned canonical Runner in the conda recipe and require a real decode during conda testing
- Keep `decode_array()` as a one-shot API; a persistent JVM remains a separate performance optimization
- Modernize Python 3.8-3.14, PyPI Trusted Publishing, GitHub Release, and conda-forge workflows

dev (17 Jan 2022)
- Use navdeep-G/setup.py as template

1.0.2 (9 Jan 2022)
- Using poetry to manage project and change structure
- Support blank in path

1.0.1 (18 April 2021)
- Fix jar preparation and add test case

1.0.0 (12 April 2021)
- Better decoding performance

0.3.5 (6 March 2021)
- Support decoding qrcode with bytes format content
- Support passing array into BarCodeReader

0.3.4 (2 March 2021)
- add points information in result

0.3.3 (29 Nov 2020)
- Update result parser
- support using absolute path

0.3.1 (28 July 2020)
- Add command line runner
- Fix download link
- Optimize cache logic

0.3 (31 May 2020)
- Support read multiple barcodes in a picture
- Scan multiple files in parallel
- Fix Linux runtime error

0.2 (29 May 2020)
- Parse raw output into structured result
- Enable using pre-compiled jar file

0.1 (28 May 2020)
- Initial release

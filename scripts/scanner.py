import argparse

from pyzxing import BarCodeReader


def build_parser():
    parser = argparse.ArgumentParser(description="Decode barcodes with pyzxing")
    parser.add_argument("-f", "--file", required=True, help="Input path or glob")
    parser.add_argument(
        "--single",
        action="store_true",
        help="Return at most one barcode per input image",
    )
    parser.add_argument(
        "--no-try-harder",
        action="store_true",
        help="Disable ZXing's TRY_HARDER hint",
    )
    parser.add_argument("--pure-barcode", action="store_true")
    parser.add_argument("--character-set")
    parser.add_argument(
        "--possible-formats",
        help="Comma-separated ZXing BarcodeFormat names, for example QR_CODE,DATA_MATRIX",
    )
    return parser


def main(args):
    possible_formats = None
    if args.possible_formats:
        possible_formats = [
            value.strip() for value in args.possible_formats.split(",") if value.strip()
        ]

    results = BarCodeReader().decode(
        args.file,
        multi=not args.single,
        try_harder=not args.no_try_harder,
        pure_barcode=args.pure_barcode,
        character_set=args.character_set,
        possible_formats=possible_formats,
    )
    for result in results:
        parsed = result.get("parsed_text")
        if parsed is not None:
            print(parsed)


if __name__ == "__main__":
    main(build_parser().parse_args())

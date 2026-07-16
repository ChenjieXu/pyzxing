package io.github.chenjiexu.pyzxing;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.BinaryBitmap;
import com.google.zxing.DecodeHintType;
import com.google.zxing.MultiFormatReader;
import com.google.zxing.NotFoundException;
import com.google.zxing.ReaderException;
import com.google.zxing.Result;
import com.google.zxing.ResultMetadataType;
import com.google.zxing.ResultPoint;
import com.google.zxing.client.j2se.BufferedImageLuminanceSource;
import com.google.zxing.client.result.ParsedResult;
import com.google.zxing.client.result.ResultParser;
import com.google.zxing.common.HybridBinarizer;
import com.google.zxing.multi.GenericMultipleBarcodeReader;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintStream;
import java.net.URI;
import java.net.URISyntaxException;
import java.nio.charset.Charset;
import java.nio.charset.IllegalCharsetNameException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collection;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import javax.imageio.ImageIO;

/** One-shot, stdout-pure JSONL bridge between pyzxing and ZXing. */
public final class PyzxingRunner {

  static final int SCHEMA_VERSION = 1;
  private static final ObjectMapper JSON = new ObjectMapper();
  private static final Set<BarcodeFormat> ONE_DIMENSIONAL_FORMATS = EnumSet.of(
      BarcodeFormat.CODABAR,
      BarcodeFormat.CODE_39,
      BarcodeFormat.CODE_93,
      BarcodeFormat.CODE_128,
      BarcodeFormat.EAN_8,
      BarcodeFormat.EAN_13,
      BarcodeFormat.ITF,
      BarcodeFormat.RSS_14,
      BarcodeFormat.RSS_EXPANDED,
      BarcodeFormat.UPC_A,
      BarcodeFormat.UPC_E,
      BarcodeFormat.UPC_EAN_EXTENSION);

  private PyzxingRunner() {}

  public static void main(String[] args) {
    PrintStream stdout = new PrintStream(System.out, true, StandardCharsets.UTF_8);
    PrintStream stderr = new PrintStream(System.err, true, StandardCharsets.UTF_8);
    int exitCode = execute(args, stdout, stderr);
    if (exitCode != 0) {
      System.exit(exitCode);
    }
  }

  static int execute(String[] args, PrintStream stdout, PrintStream stderr) {
    CliOptions options;
    try {
      options = CliOptions.parse(args);
    } catch (RunnerException exception) {
      emit(stdout, errorRecord(exception.input(), exception.code(), exception.getMessage()));
      diagnostic(stderr, exception);
      return 2;
    }

    try {
      BufferedImage image = readImage(options.input());
      List<Result> results = decode(image, options);
      if (results.isEmpty()) {
        emit(stdout, notFoundRecord(options.input()));
      } else {
        for (Result result : results) {
          emit(stdout, okRecord(options, result));
        }
      }
      return 0;
    } catch (NotFoundException exception) {
      emit(stdout, notFoundRecord(options.input()));
      return 0;
    } catch (RunnerException exception) {
      emit(stdout, errorRecord(options.input(), exception.code(), exception.getMessage()));
      diagnostic(stderr, exception);
      return 3;
    } catch (ReaderException exception) {
      RunnerException wrapped = new RunnerException(
          "DECODE_FAILED", "ZXing could not complete decoding", options.input(), exception);
      emit(stdout, errorRecord(options.input(), wrapped.code(), wrapped.getMessage()));
      diagnostic(stderr, wrapped);
      return 3;
    } catch (Throwable throwable) {
      RunnerException wrapped = new RunnerException(
          "INTERNAL_ERROR", "Unexpected internal runner error", options.input(), throwable);
      emit(stdout, errorRecord(options.input(), wrapped.code(), wrapped.getMessage()));
      diagnostic(stderr, wrapped);
      return 4;
    }
  }

  private static BufferedImage readImage(String input) throws RunnerException {
    URI uri;
    try {
      uri = new URI(input);
    } catch (URISyntaxException exception) {
      throw new RunnerException("INVALID_INPUT_URI", "Input is not a valid URI", input, exception);
    }
    if (!uri.isAbsolute()) {
      throw new RunnerException("INVALID_INPUT_URI", "Input URI must be absolute", input);
    }
    if (!"file".equalsIgnoreCase(uri.getScheme())) {
      throw new RunnerException(
          "UNSUPPORTED_URI_SCHEME", "Only file: input URIs are supported", input);
    }

    Path path;
    try {
      path = Paths.get(uri);
    } catch (IllegalArgumentException exception) {
      throw new RunnerException("INVALID_INPUT_URI", "Input file URI is invalid", input, exception);
    }
    if (!Files.exists(path)) {
      throw new RunnerException("INPUT_NOT_FOUND", "Input file does not exist", input);
    }
    if (!Files.isRegularFile(path)) {
      throw new RunnerException("INPUT_READ_FAILED", "Input is not a regular file", input);
    }

    try (InputStream stream = Files.newInputStream(path)) {
      BufferedImage image = ImageIO.read(stream);
      if (image == null) {
        throw new RunnerException("INVALID_IMAGE", "Input is not a supported image", input);
      }
      return image;
    } catch (RunnerException exception) {
      throw exception;
    } catch (IOException | SecurityException exception) {
      throw new RunnerException("INPUT_READ_FAILED", "Input image could not be read", input, exception);
    }
  }

  private static List<Result> decode(BufferedImage image, CliOptions options)
      throws ReaderException {
    BinaryBitmap bitmap = new BinaryBitmap(
        new HybridBinarizer(new BufferedImageLuminanceSource(image)));
    Map<DecodeHintType, Object> hints = options.toDecodeHints();
    MultiFormatReader reader = new MultiFormatReader();
    try {
      if (options.multi()) {
        Result[] decoded = new GenericMultipleBarcodeReader(reader).decodeMultiple(bitmap, hints);
        return List.of(decoded);
      }
      return List.of(reader.decode(bitmap, hints));
    } finally {
      reader.reset();
    }
  }

  private static Map<String, Object> okRecord(CliOptions options, Result result) {
    ParsedResult parsed = ResultParser.parseResult(result);
    Map<String, Object> record = baseRecord("ok", options.input());
    record.put("format", result.getBarcodeFormat().name());
    record.put("type", parsed.getType().name());
    record.put("text", result.getText() == null ? "" : result.getText());
    record.put("parsed_text", parsed.getDisplayResult() == null ? "" : parsed.getDisplayResult());
    record.put("raw_bytes_base64", encodeNullable(result.getRawBytes()));
    record.put("num_bits", result.getNumBits());
    record.put("byte_segments_base64", byteSegments(result));
    record.put("points", points(result.getResultPoints()));

    Orientation orientation = orientation(result);
    record.put("orientation", orientation.degrees());
    record.put("orientation_source", orientation.source());
    record.put("metadata", metadata(options, result));
    return record;
  }

  private static Map<String, Object> notFoundRecord(String input) {
    return baseRecord("not_found", input);
  }

  private static Map<String, Object> errorRecord(String input, String code, String message) {
    Map<String, Object> record = baseRecord("error", input);
    Map<String, Object> error = new LinkedHashMap<>();
    error.put("code", code);
    error.put("message", message);
    record.put("error", error);
    return record;
  }

  private static Map<String, Object> baseRecord(String status, String input) {
    Map<String, Object> record = new LinkedHashMap<>();
    record.put("schema_version", SCHEMA_VERSION);
    record.put("status", status);
    record.put("input", input);
    record.put("format", null);
    record.put("type", null);
    record.put("text", null);
    record.put("parsed_text", null);
    record.put("raw_bytes_base64", null);
    record.put("num_bits", null);
    record.put("byte_segments_base64", List.of());
    record.put("points", List.of());
    record.put("orientation", null);
    record.put("orientation_source", "unavailable");
    record.put("metadata", Map.of());
    record.put("error", null);
    return record;
  }

  private static String encodeNullable(byte[] bytes) {
    return bytes == null ? null : Base64.getEncoder().encodeToString(bytes);
  }

  private static List<String> byteSegments(Result result) {
    Map<ResultMetadataType, Object> resultMetadata = result.getResultMetadata();
    if (resultMetadata == null) {
      return List.of();
    }
    Object value = resultMetadata.get(ResultMetadataType.BYTE_SEGMENTS);
    if (!(value instanceof Iterable<?> iterable)) {
      return List.of();
    }
    List<String> encoded = new ArrayList<>();
    for (Object segment : iterable) {
      if (segment instanceof byte[] bytes) {
        encoded.add(Base64.getEncoder().encodeToString(bytes));
      }
    }
    return List.copyOf(encoded);
  }

  private static List<List<Float>> points(ResultPoint[] resultPoints) {
    if (resultPoints == null || resultPoints.length == 0) {
      return List.of();
    }
    List<List<Float>> points = new ArrayList<>(resultPoints.length);
    for (ResultPoint point : resultPoints) {
      if (point != null && Float.isFinite(point.getX()) && Float.isFinite(point.getY())) {
        points.add(List.of(point.getX(), point.getY()));
      }
    }
    return List.copyOf(points);
  }

  private static Orientation orientation(Result result) {
    if (result.getBarcodeFormat() == BarcodeFormat.QR_CODE) {
      Integer derived = deriveQrOrientation(result.getResultPoints());
      if (derived != null) {
        return new Orientation(derived, "derived");
      }
    }

    Integer rawOrientation = rawMetadataOrientation(result);
    if (rawOrientation != null) {
      Integer normalized = normalizeRightAngle(rawOrientation);
      if (normalized != null) {
        // ZXing reports the counter-clockwise correction required to make a
        // decoded image upright. The public protocol reports the image's
        // clockwise rotation from upright, so the two values are inverses.
        return new Orientation(Math.floorMod(-normalized, 360), "metadata");
      }
    }

    if (ONE_DIMENSIONAL_FORMATS.contains(result.getBarcodeFormat())) {
      // OneDReader only adds ORIENTATION for reverse/rotated paths. A successful
      // forward horizontal decode therefore has orientation zero.
      return new Orientation(0, "derived");
    }
    return new Orientation(null, "unavailable");
  }

  private static Integer rawMetadataOrientation(Result result) {
    Map<ResultMetadataType, Object> resultMetadata = result.getResultMetadata();
    if (resultMetadata == null) {
      return null;
    }
    Object value = resultMetadata.get(ResultMetadataType.ORIENTATION);
    return value instanceof Number number ? number.intValue() : null;
  }

  private static Integer normalizeRightAngle(int degrees) {
    int normalized = Math.floorMod(degrees, 360);
    return normalized % 90 == 0 ? normalized : null;
  }

  private static Integer deriveQrOrientation(ResultPoint[] resultPoints) {
    // QRCode detector order is bottomLeft, topLeft, topRight, alignmentPattern?.
    if (resultPoints == null || resultPoints.length < 3
        || resultPoints[1] == null || resultPoints[2] == null) {
      return null;
    }
    double dx = resultPoints[2].getX() - resultPoints[1].getX();
    double dy = resultPoints[2].getY() - resultPoints[1].getY();
    if (!Double.isFinite(dx) || !Double.isFinite(dy) || Math.hypot(dx, dy) < 1.0) {
      return null;
    }
    double angle = Math.toDegrees(Math.atan2(dy, dx));
    if (angle < 0.0) {
      angle += 360.0;
    }
    int snapped = ((int) Math.round(angle / 90.0) * 90) % 360;
    double difference = Math.abs(angle - snapped);
    difference = Math.min(difference, 360.0 - difference);
    return difference <= 30.0 ? snapped : null;
  }

  private static Map<String, Object> metadata(CliOptions options, Result result) {
    Map<String, Object> stable = new LinkedHashMap<>();
    if (options.characterSet() != null) {
      stable.put("character_set", options.characterSet());
    }
    Map<ResultMetadataType, Object> resultMetadata = result.getResultMetadata();
    if (resultMetadata == null) {
      return stable;
    }
    // Keep ZXing's raw correction orientation in metadata. The normalized
    // clockwise image rotation is exposed only by the top-level field.
    copyInteger(resultMetadata, ResultMetadataType.ORIENTATION, "orientation", stable);
    copyString(resultMetadata, ResultMetadataType.ERROR_CORRECTION_LEVEL,
        "error_correction_level", stable);
    copyInteger(resultMetadata, ResultMetadataType.ERRORS_CORRECTED,
        "errors_corrected", stable);
    copyInteger(resultMetadata, ResultMetadataType.ERASURES_CORRECTED,
        "erasures_corrected", stable);
    copyInteger(resultMetadata, ResultMetadataType.ISSUE_NUMBER, "issue_number", stable);
    copyString(resultMetadata, ResultMetadataType.SUGGESTED_PRICE, "suggested_price", stable);
    copyString(resultMetadata, ResultMetadataType.POSSIBLE_COUNTRY, "possible_country", stable);
    copyString(resultMetadata, ResultMetadataType.UPC_EAN_EXTENSION, "upc_ean_extension", stable);
    copyInteger(resultMetadata, ResultMetadataType.STRUCTURED_APPEND_SEQUENCE,
        "structured_append_sequence", stable);
    copyInteger(resultMetadata, ResultMetadataType.STRUCTURED_APPEND_PARITY,
        "structured_append_parity", stable);
    copyString(resultMetadata, ResultMetadataType.SYMBOLOGY_IDENTIFIER,
        "symbology_identifier", stable);
    return stable;
  }

  private static void copyString(
      Map<ResultMetadataType, Object> source,
      ResultMetadataType sourceKey,
      String targetKey,
      Map<String, Object> target) {
    Object value = source.get(sourceKey);
    if (value instanceof String stringValue) {
      target.put(targetKey, stringValue);
    }
  }

  private static void copyInteger(
      Map<ResultMetadataType, Object> source,
      ResultMetadataType sourceKey,
      String targetKey,
      Map<String, Object> target) {
    Object value = source.get(sourceKey);
    if (value instanceof Number number) {
      target.put(targetKey, number.intValue());
    }
  }

  private static void emit(PrintStream stdout, Map<String, Object> record) {
    try {
      stdout.println(JSON.writeValueAsString(record));
      stdout.flush();
    } catch (JsonProcessingException exception) {
      throw new IllegalStateException("Could not serialize protocol record", exception);
    }
  }

  private static void diagnostic(PrintStream stderr, RunnerException exception) {
    stderr.printf("pyzxing-runner: %s: %s%n", exception.code(), exception.getMessage());
  }

  private record Orientation(Integer degrees, String source) {}

  private record CliOptions(
      String input,
      boolean multi,
      boolean tryHarder,
      boolean pureBarcode,
      String characterSet,
      Collection<BarcodeFormat> possibleFormats) {

    static CliOptions parse(String[] args) throws RunnerException {
      String input = null;
      boolean multi = false;
      boolean tryHarder = false;
      boolean pureBarcode = false;
      String characterSet = null;
      Collection<BarcodeFormat> possibleFormats = null;

      for (int index = 0; index < args.length; index++) {
        String argument = args[index];
        switch (argument) {
          case "--multi" -> multi = true;
          case "--try-harder" -> tryHarder = true;
          case "--pure-barcode" -> pureBarcode = true;
          case "--character-set" -> {
            if (index + 1 >= args.length || args[index + 1].startsWith("--")) {
              throw new RunnerException(
                  "MISSING_OPTION_VALUE", "--character-set requires a value", input);
            }
            if (characterSet != null) {
              throw new RunnerException(
                  "INVALID_ARGUMENT", "--character-set may only be specified once", input);
            }
            String requested = args[++index];
            try {
              characterSet = Charset.forName(requested).name();
            } catch (IllegalCharsetNameException | java.nio.charset.UnsupportedCharsetException exception) {
              throw new RunnerException(
                  "INVALID_CHARACTER_SET", "Unsupported character set: " + requested, input, exception);
            }
          }
          case "--possible-formats" -> {
            if (index + 1 >= args.length || args[index + 1].startsWith("--")) {
              throw new RunnerException(
                  "MISSING_OPTION_VALUE", "--possible-formats requires a value", input);
            }
            if (possibleFormats != null) {
              throw new RunnerException(
                  "INVALID_ARGUMENT", "--possible-formats may only be specified once", input);
            }
            possibleFormats = parseFormats(args[++index], input);
          }
          default -> {
            if (argument.startsWith("-")) {
              throw new RunnerException(
                  "INVALID_ARGUMENT", "Unknown option: " + argument, input);
            }
            if (input != null) {
              throw new RunnerException(
                  "MULTIPLE_INPUTS", "Exactly one input image URI is required", input);
            }
            input = argument;
          }
        }
      }

      if (input == null || input.isBlank()) {
        throw new RunnerException("MISSING_INPUT", "Exactly one input image URI is required", null);
      }
      return new CliOptions(
          input,
          multi,
          tryHarder,
          pureBarcode,
          characterSet,
          possibleFormats == null ? List.of() : List.copyOf(possibleFormats));
    }

    private static Collection<BarcodeFormat> parseFormats(String csv, String input)
        throws RunnerException {
      if (csv.isBlank()) {
        throw new RunnerException(
            "INVALID_FORMAT", "--possible-formats must not be empty", input);
      }
      Set<BarcodeFormat> formats = EnumSet.noneOf(BarcodeFormat.class);
      for (String token : csv.split(",", -1)) {
        String value = token.trim();
        if (value.isEmpty()) {
          throw new RunnerException(
              "INVALID_FORMAT", "--possible-formats contains an empty format", input);
        }
        try {
          formats.add(BarcodeFormat.valueOf(value.toUpperCase(Locale.ROOT)));
        } catch (IllegalArgumentException exception) {
          throw new RunnerException(
              "INVALID_FORMAT", "Unsupported barcode format: " + value, input, exception);
        }
      }
      return formats;
    }

    Map<DecodeHintType, Object> toDecodeHints() {
      Map<DecodeHintType, Object> hints = new EnumMap<>(DecodeHintType.class);
      if (tryHarder) {
        hints.put(DecodeHintType.TRY_HARDER, Boolean.TRUE);
      }
      if (pureBarcode) {
        hints.put(DecodeHintType.PURE_BARCODE, Boolean.TRUE);
      }
      if (characterSet != null) {
        hints.put(DecodeHintType.CHARACTER_SET, characterSet);
      }
      if (!possibleFormats.isEmpty()) {
        hints.put(DecodeHintType.POSSIBLE_FORMATS, possibleFormats);
      }
      return hints;
    }
  }

  private static final class RunnerException extends Exception {
    private final String code;
    private final String input;

    RunnerException(String code, String message, String input) {
      super(message);
      this.code = code;
      this.input = input;
    }

    RunnerException(String code, String message, String input, Throwable cause) {
      super(message, cause);
      this.code = code;
      this.input = input;
    }

    String code() {
      return code;
    }

    String input() {
      return input;
    }
  }
}

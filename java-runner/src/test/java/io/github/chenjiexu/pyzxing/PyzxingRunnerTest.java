package io.github.chenjiexu.pyzxing;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.EncodeHintType;
import com.google.zxing.MultiFormatWriter;
import com.google.zxing.WriterException;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class PyzxingRunnerTest {

  private static final ObjectMapper JSON = new ObjectMapper();

  @TempDir
  Path tempDirectory;

  @Test
  void emitsStrictOneLineJsonForEscapedUnicodeAndControlCharacters() throws Exception {
    String payload = "第一行\n第二行\u0000雪";
    Path image = writeBarcode(
        "escaped.png", payload, BarcodeFormat.QR_CODE, 280, 280, "UTF-8");

    RunResult run = run(image.toUri().toASCIIString(), "--character-set", "UTF-8");

    assertEquals(0, run.exitCode());
    assertEquals(1, run.records().size());
    assertEquals("ok", run.record().path("status").asText());
    assertEquals(payload, run.record().path("text").asText());
    assertEquals(payload, run.record().path("parsed_text").asText());
    assertFalse(run.stdout().substring(0, run.stdout().length() - 1).contains("\n"));
    assertTrue(run.stdout().contains("\\n"));
    assertTrue(run.stdout().contains("\\u0000"));
    assertTrue(run.stderr().isEmpty());
  }

  @Test
  void independentlyGeneratedNoEciQrRequiresExplicitGb18030AndPreservesBytes() throws Exception {
    String payload = "生产许可证号：测试-123";
    String defaultMojibake = "Éú²úÐí¿ÉÖ¤ºÅ£º²âÊÔ-123";
    byte[] expectedBytes = Base64.getDecoder().decode(
        "yfqy+tDtv8nWpLrFo7qy4srULTEyMw==");
    Path image = copyFixture("fixtures/gb18030/gb18030-byte-no-eci.png");

    RunResult defaultRun = run(
        image.toUri().toASCIIString(),
        "--possible-formats", "QR_CODE");

    RunResult explicitRun = run(
        image.toUri().toASCIIString(),
        "--character-set", "GB18030",
        "--possible-formats", "QR_CODE");

    assertEquals(0, defaultRun.exitCode());
    assertEquals(defaultMojibake, defaultRun.record().path("text").asText());
    assertFalse(defaultRun.record().path("text").asText().equals(payload));
    assertEquals(1, defaultRun.record().path("byte_segments_base64").size());
    assertArrayEquals(expectedBytes, decodedByteSegment(defaultRun.record()));

    assertEquals(0, explicitRun.exitCode());
    assertEquals(payload, explicitRun.record().path("text").asText());
    assertFalse(explicitRun.record().path("raw_bytes_base64").isNull());
    assertTrue(explicitRun.record().path("num_bits").asInt() > 0);
    assertEquals(
        "GB18030", explicitRun.record().path("metadata").path("character_set").asText());
    assertEquals(1, explicitRun.record().path("byte_segments_base64").size());
    assertArrayEquals(expectedBytes, decodedByteSegment(explicitRun.record()));
  }

  @Test
  void reportsNotFoundAsOneSuccessfulProtocolRecord() throws Exception {
    BufferedImage white = new BufferedImage(160, 120, BufferedImage.TYPE_INT_RGB);
    Graphics2D graphics = white.createGraphics();
    graphics.setColor(Color.WHITE);
    graphics.fillRect(0, 0, white.getWidth(), white.getHeight());
    graphics.dispose();
    Path image = tempDirectory.resolve("blank.png");
    ImageIO.write(white, "PNG", image.toFile());

    RunResult run = run(image.toUri().toASCIIString(), "--multi", "--try-harder");

    assertEquals(0, run.exitCode());
    assertEquals(1, run.records().size());
    assertEquals("not_found", run.record().path("status").asText());
    assertEquals(image.toUri().toASCIIString(), run.record().path("input").asText());
    assertTrue(run.record().path("format").isNull());
    assertTrue(run.record().path("byte_segments_base64").isArray());
    assertTrue(run.record().path("byte_segments_base64").isEmpty());
    assertTrue(run.record().path("error").isNull());
  }

  @Test
  void multiEmitsOneOkRecordPerBarcodeAndNoOtherStatuses() throws Exception {
    BufferedImage left = barcodeImage("left", BarcodeFormat.QR_CODE, 220, 220, "UTF-8");
    BufferedImage right = barcodeImage("right", BarcodeFormat.QR_CODE, 220, 220, "UTF-8");
    BufferedImage combined = new BufferedImage(520, 260, BufferedImage.TYPE_INT_RGB);
    Graphics2D graphics = combined.createGraphics();
    graphics.setColor(Color.WHITE);
    graphics.fillRect(0, 0, combined.getWidth(), combined.getHeight());
    graphics.drawImage(left, 10, 20, null);
    graphics.drawImage(right, 290, 20, null);
    graphics.dispose();
    Path image = tempDirectory.resolve("multi.png");
    ImageIO.write(combined, "PNG", image.toFile());

    RunResult run = run(
        "--multi", image.toUri().toASCIIString(), "--possible-formats", "QR_CODE");

    assertEquals(0, run.exitCode());
    assertEquals(2, run.records().size());
    Set<String> payloads = new HashSet<>();
    for (JsonNode record : run.records()) {
      assertEquals("ok", record.path("status").asText());
      payloads.add(record.path("text").asText());
    }
    assertEquals(Set.of("left", "right"), payloads);
  }

  @Test
  void invalidImageIsStructuredExitThreeAndStdoutRemainsPure() throws Exception {
    Path invalid = tempDirectory.resolve("invalid.png");
    Files.writeString(invalid, "not an image", StandardCharsets.UTF_8);

    RunResult run = run(invalid.toUri().toASCIIString());

    assertEquals(3, run.exitCode());
    assertEquals(1, run.records().size());
    assertEquals("error", run.record().path("status").asText());
    assertEquals("INVALID_IMAGE", run.record().path("error").path("code").asText());
    assertTrue(run.stderr().contains("INVALID_IMAGE"));
    assertEquals(1, run.stdout().lines().count());
  }

  @Test
  void specialCharactersInFileUriRoundTripExactly() throws Exception {
    Path directory = Files.createDirectories(tempDirectory.resolve("问题 路径%#"));
    Path image = directory.resolve("二维码 100%#雪.png");
    ImageIO.write(
        barcodeImage("special-path", BarcodeFormat.QR_CODE, 240, 240, "UTF-8"),
        "PNG",
        image.toFile());
    String input = image.toUri().toASCIIString();

    RunResult run = run(input, "--possible-formats", "QR_CODE");

    assertEquals(0, run.exitCode());
    assertEquals("ok", run.record().path("status").asText());
    assertEquals(input, run.record().path("input").asText());
    assertEquals("special-path", run.record().path("text").asText());
  }

  @Test
  void invalidCliAndHintsUseStableCodesAndExitTwo() throws Exception {
    assertCliError(new String[] {}, "MISSING_INPUT");
    assertCliError(new String[] {"--unknown"}, "INVALID_ARGUMENT");
    assertCliError(new String[] {"--character-set"}, "MISSING_OPTION_VALUE");
    assertCliError(new String[] {"--character-set", "not-a-charset", "file:///tmp/x"},
        "INVALID_CHARACTER_SET");
    assertCliError(new String[] {"file:///tmp/a", "file:///tmp/b"}, "MULTIPLE_INPUTS");
    assertCliError(new String[] {"file:///tmp/x", "--possible-formats", "QR_CODE,NOPE"},
        "INVALID_FORMAT");
  }

  @Test
  void inputFailuresUseStableStructuredCodes() throws Exception {
    RunResult unsupported = run("https://example.invalid/barcode.png");
    assertEquals(3, unsupported.exitCode());
    assertEquals("UNSUPPORTED_URI_SCHEME",
        unsupported.record().path("error").path("code").asText());

    RunResult missing = run(tempDirectory.resolve("missing.png").toUri().toASCIIString());
    assertEquals(3, missing.exitCode());
    assertEquals("INPUT_NOT_FOUND", missing.record().path("error").path("code").asText());
  }

  @Test
  void qrOrientationIsDerivedForAllRightAngleRotations() throws Exception {
    BufferedImage original = barcodeImage(
        "qr-orientation", BarcodeFormat.QR_CODE, 240, 240, "UTF-8");
    for (int degrees : List.of(0, 90, 180, 270)) {
      Path image = tempDirectory.resolve("qr-" + degrees + ".png");
      ImageIO.write(rotateClockwise(original, degrees), "PNG", image.toFile());
      RunResult run = run(
          image.toUri().toASCIIString(),
          "--try-harder",
          "--possible-formats", "QR_CODE");

      assertEquals(0, run.exitCode(), () -> "rotation=" + degrees + " " + run.stderr());
      assertEquals("qr-orientation", run.record().path("text").asText());
      assertEquals(degrees, run.record().path("orientation").asInt());
      assertEquals("derived", run.record().path("orientation_source").asText());
      assertTrue(run.record().path("points").size() >= 3);
      assertFalse(run.record().path("metadata").has("orientation"));
    }
  }

  @Test
  void oneDimensionalOrientationUsesClockwisePublicConventionAndRawMetadata() throws Exception {
    BufferedImage original = barcodeImage(
        "CODE128-ORIENTATION", BarcodeFormat.CODE_128, 420, 140, null);
    for (int degrees : List.of(0, 90, 180, 270)) {
      Path image = tempDirectory.resolve("code128-" + degrees + ".png");
      ImageIO.write(rotateClockwise(original, degrees), "PNG", image.toFile());
      RunResult run = run(
          image.toUri().toASCIIString(),
          "--try-harder",
          "--possible-formats", "CODE_128");

      assertEquals(0, run.exitCode(), () -> "rotation=" + degrees + " " + run.stderr());
      assertEquals("CODE128-ORIENTATION", run.record().path("text").asText());
      assertEquals(degrees, run.record().path("orientation").asInt());
      assertEquals(degrees == 0 ? "derived" : "metadata",
          run.record().path("orientation_source").asText());
      int upstreamOrientation = switch (degrees) {
        case 90 -> 270;
        case 270 -> 90;
        default -> degrees;
      };
      if (degrees == 0) {
        assertFalse(run.record().path("metadata").has("orientation"));
      } else {
        assertEquals(
            upstreamOrientation,
            run.record().path("metadata").path("orientation").asInt());
      }
    }
  }

  @Test
  void allOkFieldsArePresentWithDocumentedTypes() throws Exception {
    Path image = writeBarcode(
        "schema.png", "https://example.com/a?b=1", BarcodeFormat.QR_CODE, 240, 240, "UTF-8");

    JsonNode record = run(image.toUri().toASCIIString()).record();

    for (String field : List.of(
        "schema_version", "status", "input", "format", "type", "text", "parsed_text",
        "raw_bytes_base64", "num_bits", "byte_segments_base64", "points", "orientation",
        "orientation_source", "metadata", "error")) {
      assertTrue(record.has(field), field);
    }
    assertEquals(PyzxingRunner.SCHEMA_VERSION, record.path("schema_version").asInt());
    assertEquals("QR_CODE", record.path("format").asText());
    assertEquals("URI", record.path("type").asText());
    assertTrue(record.path("byte_segments_base64").isArray());
    assertTrue(record.path("points").isArray());
    assertTrue(record.path("metadata").isObject());
    assertNull(record.get("error").textValue());
    assertNotNull(record.path("metadata").path("symbology_identifier").textValue());
  }

  private void assertCliError(String[] arguments, String code) throws Exception {
    RunResult run = run(arguments);
    assertEquals(2, run.exitCode());
    assertEquals(1, run.records().size());
    assertEquals("error", run.record().path("status").asText());
    assertEquals(code, run.record().path("error").path("code").asText());
    assertEquals(1, run.stdout().lines().count());
  }

  private Path writeBarcode(
      String name,
      String payload,
      BarcodeFormat format,
      int width,
      int height,
      String characterSet) throws IOException, WriterException {
    Path path = tempDirectory.resolve(name);
    ImageIO.write(
        barcodeImage(payload, format, width, height, characterSet), "PNG", path.toFile());
    return path;
  }

  private Path copyFixture(String resourceName) throws IOException {
    Path destination = tempDirectory.resolve(Path.of(resourceName).getFileName().toString());
    try (InputStream stream = PyzxingRunnerTest.class.getClassLoader()
        .getResourceAsStream(resourceName)) {
      assertNotNull(stream, resourceName);
      Files.copy(stream, destination);
    }
    return destination;
  }

  private static byte[] decodedByteSegment(JsonNode record) {
    return Base64.getDecoder().decode(record.path("byte_segments_base64").get(0).asText());
  }

  private static BufferedImage barcodeImage(
      String payload,
      BarcodeFormat format,
      int width,
      int height,
      String characterSet) throws WriterException {
    Map<EncodeHintType, Object> hints = new EnumMap<>(EncodeHintType.class);
    hints.put(EncodeHintType.MARGIN, 4);
    if (characterSet != null) {
      hints.put(EncodeHintType.CHARACTER_SET, characterSet);
    }
    BitMatrix matrix = new MultiFormatWriter().encode(payload, format, width, height, hints);
    return MatrixToImageWriter.toBufferedImage(matrix);
  }

  private static BufferedImage rotateClockwise(BufferedImage source, int degrees) {
    int normalized = Math.floorMod(degrees, 360);
    if (normalized == 0) {
      return source;
    }
    if (normalized % 90 != 0) {
      throw new IllegalArgumentException("Only right-angle rotations are supported");
    }
    int width = source.getWidth();
    int height = source.getHeight();
    int targetWidth = normalized == 180 ? width : height;
    int targetHeight = normalized == 180 ? height : width;
    BufferedImage target = new BufferedImage(targetWidth, targetHeight, source.getType());
    for (int y = 0; y < height; y++) {
      for (int x = 0; x < width; x++) {
        int rgb = source.getRGB(x, y);
        switch (normalized) {
          case 90 -> target.setRGB(height - 1 - y, x, rgb);
          case 180 -> target.setRGB(width - 1 - x, height - 1 - y, rgb);
          case 270 -> target.setRGB(y, width - 1 - x, rgb);
          default -> throw new IllegalStateException("Unexpected rotation");
        }
      }
    }
    return target;
  }

  private static RunResult run(String... arguments) throws Exception {
    ByteArrayOutputStream stdoutBytes = new ByteArrayOutputStream();
    ByteArrayOutputStream stderrBytes = new ByteArrayOutputStream();
    int exitCode;
    try (PrintStream stdout = new PrintStream(stdoutBytes, true, StandardCharsets.UTF_8);
         PrintStream stderr = new PrintStream(stderrBytes, true, StandardCharsets.UTF_8)) {
      exitCode = PyzxingRunner.execute(arguments, stdout, stderr);
    }
    String stdout = stdoutBytes.toString(StandardCharsets.UTF_8);
    String stderr = stderrBytes.toString(StandardCharsets.UTF_8);
    List<JsonNode> records = new ArrayList<>();
    for (String line : stdout.lines().toList()) {
      assertFalse(line.isBlank());
      records.add(JSON.readTree(line));
    }
    return new RunResult(exitCode, stdout, stderr, List.copyOf(records));
  }

  private record RunResult(int exitCode, String stdout, String stderr, List<JsonNode> records) {
    JsonNode record() {
      assertEquals(1, records.size());
      return records.get(0);
    }
  }
}

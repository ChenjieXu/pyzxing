#!/bin/bash
set -e

# ZXing JAR Build Script
# This script builds ZXing JAR file from source

echo "🔨 Building ZXing JAR file..."

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "❌ Java is not installed. Please install Java 8 or higher."
    exit 1
fi

if ! command -v mvn &> /dev/null; then
    echo "❌ Maven is not installed. Please install Maven 3.6 or higher."
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ZXING_DIR="$PROJECT_DIR/zxing"

# Check if ZXing submodule exists
if [ ! -d "$ZXING_DIR" ]; then
    echo "📥 Initializing ZXing submodule..."
    cd "$PROJECT_DIR"
    git submodule update --init --recursive
fi

cd "$ZXING_DIR"

# Get ZXing version from config
cd "$PROJECT_DIR"
ZXING_VERSION=$(python3 -c "from pyzxing.config import Config; print(Config.DEFAULT_ZXING_VERSION)")
echo "🎯 Building ZXing version: $ZXING_VERSION"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
cd "$ZXING_DIR"
mvn clean -DskipTests -Dmaven.javadoc.skip=true

# Build ZXing core
echo "📦 Building ZXing core..."
mvn install -DskipTests -Drat.skip=true -Dmaven.javadoc.skip=true

# Build JAR with dependencies
echo "🔧 Building JAR with dependencies..."
cd javase
mvn package -DskipTests -Drat.skip=true -Dmaven.javadoc.skip=true assembly:single

# Find the built JAR file
JAR_FILE=$(find target -name "*jar-with-dependencies.jar" | head -1)

if [ -z "$JAR_FILE" ]; then
    echo "❌ JAR file not found in target directory"
    exit 1
fi

# Copy JAR to project's release directory
RELEASE_DIR="$PROJECT_DIR/releases"
mkdir -p "$RELEASE_DIR"

JAR_FILENAME="javase-$ZXING_VERSION-SNAPSHOT-jar-with-dependencies.jar"
cp "$JAR_FILE" "$RELEASE_DIR/$JAR_FILENAME"

echo "✅ JAR file built successfully!"
echo "📁 Location: $RELEASE_DIR/$JAR_FILENAME"
echo "📏 Size: $(du -h "$RELEASE_DIR/$JAR_FILENAME" | cut -f1)"

# Test the JAR file
echo "🧪 Testing JAR file..."
java -jar "$RELEASE_DIR/$JAR_FILENAME" --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ JAR file test passed!"
else
    echo "⚠️  JAR file test failed, but file was created successfully"
fi

echo "🎉 ZXing JAR build completed!"
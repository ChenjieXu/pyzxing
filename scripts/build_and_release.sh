#!/bin/bash
set -e

# Complete Build and Release Script
# This script builds JAR, runs tests, and prepares for release

echo "🚀 Starting complete build and release process..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Get version from config
cd "$PROJECT_DIR"
VERSION=$(python3 -c "from pyzxing.config import Config; print(Config.VERSION)")
ZXING_VERSION=$(python3 -c "from pyzxing.config import Config; print(Config.DEFAULT_ZXING_VERSION)")

echo "📦 Building version: $VERSION"
echo "🔧 ZXing version: $ZXING_VERSION"

# Step 1: Run tests
echo "🧪 Running tests..."
python3 -m pytest tests/ -v --cov=pyzxing --cov-report=term-missing

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Aborting build."
    exit 1
fi

echo "✅ All tests passed!"

# Step 2: Build JAR file
echo "🔨 Building ZXing JAR file..."
"$SCRIPT_DIR/build_jar.sh"

# Step 3: Update JAR filename in config
echo "📝 Updating JAR filename in config..."
JAR_FILENAME="javase-$ZXING_VERSION-SNAPSHOT-jar-with-dependencies.jar"
sed -i "s/preset_jar_filename = .*/preset_jar_filename = \"$JAR_FILENAME\"/" pyzxing/reader.py

# Step 4: Test the updated package
echo "🧪 Testing updated package..."
python3 -c "
import sys
sys.path.insert(0, '.')
from pyzxing import BarCodeReader
reader = BarCodeReader()
print('✅ Package test passed!')
"

# Step 5: Create distribution packages
echo "📦 Creating distribution packages..."
python3 -m build

# Step 6: Copy JAR to dist directory for release
echo "📋 Preparing release assets..."
mkdir -p dist/releases
cp "releases/$JAR_FILENAME" "dist/"

# Step 7: Generate release notes
echo "📝 Generating release notes..."
cat > "release_notes.md" << EOF
# pyzxing $VERSION Release Notes

## What's New

### Bug Fixes
- Fixed path handling bug in utils.py that caused duplicate path joining
- Improved error handling throughout the codebase
- Fixed Windows encoding issues that caused data loss
- Fixed QR code detection edge cases (PR #42)

### Improvements
- Upgraded minimum Python version from 3.6 to 3.7
- Enhanced cross-platform compatibility
- Improved performance with intelligent parallel processing
- Added comprehensive test coverage
- Added configuration management system

### New Features
- Added PlatformUtils class for platform-specific operations
- Added performance optimizations and caching
- Enhanced error logging and debugging
- Added comprehensive CI/CD pipeline

### Technical Details
- Total commits: $(git rev-list --count HEAD)
- Files changed: $(git diff --name-only HEAD~1 HEAD | wc -l)
- Tests added: $(find tests/ -name "*.py" -newer HEAD~1 | wc -l)

## Installation
\`\`\`bash
pip install pyzxing==$VERSION
\`\`\`

## Documentation
- [GitHub Repository](https://github.com/ChenjieXu/pyzxing)
- [PyPI Package](https://pypi.org/project/pyzxing/)
- [Conda Package](https://anaconda.org/conda-forge/pyzxing)

## Contributors
- Chenjie Xu (@ChenjieXu)
- Community contributors

## License
MIT License
EOF

echo "✅ Release notes generated!"

# Step 8: Summary
echo ""
echo "🎉 Build and release preparation completed!"
echo ""
echo "📦 Generated files:"
echo "  - dist/ (Python packages)"
echo "  - dist/releases/$JAR_FILENAME (JAR file)"
echo "  - release_notes.md (Release notes)"
echo ""
echo "🚀 Ready for release!"
echo ""
echo "Next steps:"
echo "1. Review the generated files"
echo "2. Create a new GitHub release with tag v$VERSION"
echo "3. Upload the files from dist/ directory"
echo "4. The CI/CD pipeline will automatically publish to PyPI and Conda"
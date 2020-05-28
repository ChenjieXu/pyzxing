# pyzxing

python-zxing does not work properly and is out of maintenance. So I decide to create this repository so that Pythoneer can take advantage of zxing library with minimum cost.

## Install Zxing Module

```bash
git submodule init
git submodule update
cd zxing
mvn install -DskipTests
cd javase
mvn -DskipTests package assembly:single
```

## Quick Start

```python
from pyzxing import BarCodeReader
reader = BarCodeReader()
output = reader.decode('/PATH/TO/FILE')
print(output)
```


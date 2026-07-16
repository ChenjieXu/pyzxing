Development
===========

Python environment
------------------

.. code-block:: console

   python -m pip install -e '.[dev]'
   python -m pytest tests/
   python -m ruff check .

Java Runner
-----------

Use the checked-in Maven wrapper so local and CI builds use the same Maven
version:

.. code-block:: console

   ./mvnw -f java-runner/pom.xml clean verify

Windows uses ``mvnw.cmd``.

Documentation
-------------

.. code-block:: console

   python -m pip install -r docs/requirements.txt
   python -m pip install -e .
   sphinx-build -W --keep-going -b html docs docs/_build/html

Warnings fail the documentation build locally, in GitHub Actions, and on Read
the Docs.

Release checks
--------------

Version, Runner, ZXing, checksum, and conda metadata must remain synchronized.
Run these checks before preparing a release:

.. code-block:: console

   python scripts/verify_version_sync.py
   python scripts/verify_release_evidence.py
   python -m build
   python -m twine check dist/*

The full release procedure and immutable-asset rules are documented in
``RELEASING.md`` in the repository root.

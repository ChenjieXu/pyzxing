from setuptools import setup, find_packages

with open('README.md', encoding="utf8") as f:
    readme = f.read()
with open('requirements.txt') as f:
    reqs = f.read()

setup(
    name="pyzxing",
    version="0.3.2",
    url="https://github.com/ChenjieXu/pyzxing",
    description="Python wrapper for ZXing Java library",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Chenjie Xu",
    author_email="cxuscience@gmail.com",
    keywords='zxing',
    packages=find_packages(),
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
    ],
    install_requires=reqs.strip().split('\n'),
)

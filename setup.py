from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="waverider-sdr",
    version="0.1.0",
    author="WaveRiderSDR Team",
    description="The only SDR with full features and rolling updates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "PyQt5>=5.15.0",
        "h5py>=3.1.0",
        "pandas>=1.3.0",
        "pyrtlsdr>=0.2.9",
        "pyyaml>=5.4.0",
    ],
    entry_points={
        'console_scripts': [
            'waverider=waverider.main:main',
        ],
    },
)

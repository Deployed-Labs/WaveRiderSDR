"""
WaveRider SDR Setup Configuration
Standard Python package setup using setuptools
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

# Read requirements
requirements_file = Path(__file__).parent / 'requirements.txt'
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = [
        'numpy>=1.21.0',
        'matplotlib>=3.4.0',
        'scipy>=1.7.0',
        'pyserial>=3.5',
    ]

# Optional dependencies for different features
extras_require = {
    'desktop': ['PyQt5>=5.15.0'],
    'web': ['flask>=2.3.0', 'flask-socketio>=5.3.0', 'python-socketio>=5.9.0'],
    'sdr': ['pyrtlsdr>=0.2.9'],
    'all': [
        'PyQt5>=5.15.0',
        'flask>=2.3.0',
        'flask-socketio>=5.3.0',
        'python-socketio>=5.9.0',
        'pyrtlsdr>=0.2.9',
    ],
}

setup(
    name='waverider-sdr',
    version='1.0.0',
    author='1090mb',
    description='Universal Cross-Platform SDR Application with Desktop and Web Interfaces',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/1090mb/WaveRiderSDR',
    project_urls={
        'Bug Reports': 'https://github.com/1090mb/WaveRiderSDR/issues',
        'Source': 'https://github.com/1090mb/WaveRiderSDR',
    },
    
    # Package configuration
    py_modules=['waverider_sdr', 'waverider_web', 'waverider_common', 'run'],
    packages=find_packages(),
    package_data={
        '': ['templates/*.html', 'README.md', 'LICENSE', 'PLATFORM_GUIDE.md'],
    },
    include_package_data=True,
    
    # Dependencies
    install_requires=requirements,
    extras_require=extras_require,
    python_requires='>=3.8',
    
    # Entry points for command-line scripts
    entry_points={
        'console_scripts': [
            'waverider=run:main',
            'waverider-sdr=waverider_sdr:main',
            'waverider-web=waverider_web:main',
        ],
    },
    
    # Metadata
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Telecommunications Industry',
        'Topic :: Communications :: Ham Radio',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
    ],
    
    keywords='sdr radio rtl-sdr hackrf ham-radio signal-processing waterfall spectrum-analyzer',
    
    # Additional metadata
    license='MIT',
    zip_safe=False,
)

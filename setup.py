from setuptools import setup


setup(
    name="waverider-sdr",
    version="0.1.0",
    description="WaveRider SDR Python launcher and GUI",
    py_modules=["run", "waverider_common", "waverider_web", "waverider_sdr"],
    include_package_data=True,
    install_requires=["flask>=3.0.0", "numpy>=1.26.0", "pyserial>=3.5"],
    entry_points={
        "console_scripts": [
            "waverider-sdr=run:main",
            "waverider-sdr-web=waverider_web:main",
            "waverider-sdr-desktop=waverider_sdr:main",
        ]
    },
)


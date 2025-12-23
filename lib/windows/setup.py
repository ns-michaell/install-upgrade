import setuptools

setuptools.setup(
    name="windows",
    version=1.1,
    packages=setuptools.find_packages(),
    py_modules=['windows'],
    install_requires=[
        'paramiko',
        "urllib3==1.26.16",
        "selenium==3.141.0",
        "Appium-Python-Client==1.2.0"
    ],
    entry_points={
        'windows': [
            ('windows = windows'),
        ]
    },
)
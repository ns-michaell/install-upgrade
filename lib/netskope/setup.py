import setuptools

setuptools.setup(
    name="netskope",
    version=2.7,
    packages=setuptools.find_packages(),
    py_modules=['check','client','customer','display','fetcher','installer','service'],
    install_requires=[
        'paramiko',
        'pyyaml',
        'requests'
    ],
    entry_points={
        'netskope': [
            # ('check = check'), # deprecated
            ('display = display'),
            ('client = client'),
            ('fetcher = fetcher'),
            ('service = service'),
            ('installer = installer'),
            ('customer = customer')
        ]
    },
)
from setuptools import setup, find_packages

setup(
    name='docsismodem',
    version='0.0.34',
    install_requires=[
        'requests',
        'importlib-metadata; python_version<"3.11"',
    ],
    packages=find_packages(
        # All keyword arguments below are optional:
        where='src',  # '.' by default
        include=['mypackage*'],  # ['*'] by default
        exclude=['mypackage.tests'],  # empty by default
    ),
)
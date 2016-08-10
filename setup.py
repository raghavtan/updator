try:
    from setuptools import setup, find_packages, Extension
except ImportError:
    from distutils.core import setup, find_packages, Extension

__version__ = '1.0.0'

setup(
    name='updator',
    version=__version__,
    packages=find_packages(),
    url='',
    license='BSD',
    author='raghav',
    author_email='raghavtan@gmail.com',
    description='updation script',
    entry_points={'console_scripts': [
        'up-rev=reload:main',
    ]},
    requires=['boto'],
    data_files=[
        ('conf', ['logging.yml']),
    ],
)
import sys
from setuptools import setup


if sys.version_info[:2] < (3, 4):
    raise SystemExit('require Python3.4+')


setup(
    name='plsmake',
    version='0.0.1.dev0',
    packages=['plsmake'],
    install_requires=['structlog'],
    extras_require={
        ':python_version<"3.5"': ['typing'],
        'ci': ['pytest', 'pytest-sugar', 'pytest-cov', 'codecov'],
    },
    entry_points={
        'console_scripts': ['plsmake=plsmake.__main__:main'],
    },
    python_requires='>=3.4',
    url='https://github.com/account-login/plsmake',
    license='MIT',
    author='account-login',
    author_email='',
    description='A `make` replacement aims at simplicity.',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        'Operating System :: OS Independent',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='build build-tool build-system make makefile',
)

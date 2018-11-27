"""Setup script for pipexl (pipe - ex - el). This package provides support
for treating sections of Excel worksheets as lists of records, in order to
support creating pipelines of Excel data"""

from setuptools import setup, find_packages

REQUIREMENTS = [
    'openpyxl',
]

SETUP_REQUIREMENTS = [
    'pytest-runner',
]

TEST_REQUIREMENTS = [
    'pytest',
]

setup(
    name='pipexl',
    version='0.0.0+wip',
    description=(
        'Classes to ease automation pipelines involving tabular data '
        'embedded inside Excel worksheets'
    ),
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='excel',  # Optional
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required
    install_requires=REQUIREMENTS,  # Optional
    tests_require=TEST_REQUIREMENTS,
    setup_requires=SETUP_REQUIREMENTS,
    python_requires='~=3.6',
)

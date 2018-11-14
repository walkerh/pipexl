from setuptools import setup, find_packages

requirements = [
    'openpyxl',
]

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
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
    install_requires=requirements,  # Optional
    tests_require=test_requirements,
    setup_requires=setup_requirements,
    python_requires='~=3.6',
)

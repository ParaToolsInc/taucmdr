from setuptools import setup, find_packages

setup(
    name="taucmdr",
    version="0.1",
    packages=find_packages("packages"),
    package_dir={"": "packages"},
    scripts=['bin/tau'],
    zip_safe=False,

    # Testing
    test_suite='tau.tests.run_tests',
    tests_require=['pylint'], # Because we run pylint as a unit test

    # Metadata for upload to PyPI
    author="ParaTools, Inc.",
    author_email="info@paratools.com",
    description="An intuitive interface for the TAU Performance System",
    license="BSD",
    keywords="TAU performance analysis profile profiling trace tracing",
    url="http://www.taucommander.com/",

    # PyPI classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Profilers',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)

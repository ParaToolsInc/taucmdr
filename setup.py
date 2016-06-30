from setuptools import setup, find_packages

long_description="""
TAU Commander from ParaTools, Inc. is a production-grade performance engineering solution that makes The TAU Performance System users more productive. It presents a simple, intuitive, and systemized interface that guides users through performance engineering workflows and offers constructive feedback in case of error. TAU Commander also enhances the performance engineer's ability to mine actionable information from the application performance data by connecting to a suite of cloud-based data analysis, storage, visualization, and reporting services.
"""

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
    long_description=long_description,
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
        'Topic :: Software Development :: User Interfaces',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)

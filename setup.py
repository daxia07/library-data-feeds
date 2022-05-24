# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="library-data-feeds",  # Required
    # Versions should comply with PEP 440:
    version="0.0.2",  # Required
    description="A sample Python project",  # Optional
    long_description=long_description,  # Optional
    long_description_content_type="text/markdown",  # Optional (see note above)
    author="alienz",  # Optional
    # This should be a valid email address corresponding to the author listed
    # above.
    author_email="leemingxia@outlook.com",  # Optional
    classifiers=[  # Optional
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    url="https://github.com/daxia07/library-data-feeds",
    keywords="books, library, reviews",  # Optional
    package_dir={"": "src"},  # Optional
    packages=find_packages(where="src"),  # Required
    python_requires=">=3.8, <4",
    install_requires=[
        "Flask==2.1.2",
        "gunicorn==20.1.0",
        "python-dotenv==0.20.0",
        "Scrapy==2.6.1",
        "scrapy-splash==0.8.0"
    ],
    extras_require={  # Optional
        "dev": ["check-manifest"],
        "test": ["coverage"],
    },
    # If there are data files included in your packages that need to be
    # installed, specify them here.
    # package_data={  # Optional
    #     "sample": ["package_data.dat"],
    # },
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[("my_data", ["data/data_file"])],  # Optional
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    entry_points={  # Optional
        "console_scripts": [
            "lib-job=jobs.crawler:main",
        ],
    },
)

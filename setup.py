import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="openapi_resolver",
    version="0.0.6",
    author="Roberto Polli",
    author_email="robipolli@gmail.com",
    description="Resolve and bundle openapi v3 specs.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ioggstream/openapi-resolver",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    keywords=['openapi', 'rest', 'swagger'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)


import setuptools

with open('README.md', "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name="py-lspci",
    version="0.0.9",
    author="Sergey Parshin",
    author_email="s.parshin@yadro.com",
    description="Parser for lspci output on remote or local machines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YADRO-KNS/py-lspci",
    packages=setuptools.find_packages(),
    install_requires=[
        "Fabric>=2.6.0"
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
    ]
)

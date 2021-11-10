from setuptools import find_packages, setup

setup(
    name="filereaderx",
    version="0.1",
    author="minskiter",
    author_email="minskiter@gmail.com",
    license="MIT",
    description="File Reader Wrapper",
    keywords="file reader",
    packages=find_packages(),
    requires=["tqdm"]
)

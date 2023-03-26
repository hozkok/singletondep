from pathlib import Path
from setuptools import setup, find_packages


here = Path(__file__).parent


install_requires = [
    "fastapi",
    "pydantic",
]


tests_require = [
    "pytest",
    "requests",
]


v = {}
exec((here / "singletonoid" / "__version__.py").read_text(), v)


setup(
    name="singletonoid",
    version=v["__version__"],
    install_requires=install_requires,
    tests_require=tests_require,
    packages=find_packages(exclude=["tests"]),
)

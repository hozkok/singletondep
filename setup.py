from pathlib import Path

from setuptools import find_packages, setup

here = Path(__file__).parent

install_requires = [
    "fastapi",
    "pydantic",
]

tests_require = [
    "pytest",
    "httpx",
]

v = {}
exec((here / "singletondep" / "__version__.py").read_text(), v)


setup(
    name="singletondep",
    version=v["__version__"],
    install_requires=install_requires,
    tests_require=tests_require,
    packages=find_packages(exclude=["tests"]),
)

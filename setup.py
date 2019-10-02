from setuptools import setup, find_packages

PACKAGE_NAME = "philly_311_bot"


def find_version(path):
    import re

    # path shall be a plain ascii text file.
    s = open(path, "rt").read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", s, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Version not found")


def get_requirements(filename):
    with open(filename, "r") as fh:
        return [l.strip() for l in fh]


setup(
    name=PACKAGE_NAME,
    version=find_version(f"{PACKAGE_NAME}/__init__.py"),
    author="Nick Hand",
    maintainer="Nick Hand",
    maintainer_email="nick.hand@phila.gov",
    packages=find_packages(),
    description="Tweeting information about yesterday's 311 requests in Philadelphia",
    license="MIT",
    python_requires=">=3.6",
    install_requires=get_requirements("requirements.txt"),
)

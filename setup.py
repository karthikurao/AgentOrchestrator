from setuptools import find_packages, setup

setup(
    name="cortex",
    version="2.0.0",
    description="Cortex — Parallel Multi-Agent Orchestration System",
    packages=find_packages(),
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "cortex=cli.main:main",
        ],
    },
)

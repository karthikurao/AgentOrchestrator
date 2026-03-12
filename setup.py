from setuptools import setup, find_packages

setup(
    name="agent-orchestrator",
    version="1.0.0",
    description="Multi-Agent Orchestrator System with Master-Slave Architecture",
    packages=find_packages(),
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "agent-orchestrator=cli.main:main",
        ],
    },
)

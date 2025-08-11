"""
Setup script for Prompt Stacker - Cursor Automation System
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="prompt-stacker",
    version="2.0.0",
    author="Automation System",
    author_email="",
    description="A powerful automation system for Cursor with beautiful Monokai-themed UI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/prompt-stacker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Desktop Environment",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "prompt-stacker=automator:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="automation, cursor, gui, tkinter, pyautogui",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/prompt-stacker/issues",
        "Source": "https://github.com/yourusername/prompt-stacker",
        "Documentation": "https://github.com/yourusername/prompt-stacker#readme",
    },
)

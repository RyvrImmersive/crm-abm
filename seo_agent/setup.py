from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="seo-agent",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive SEO analysis and optimization toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/seo-agent",
    packages=find_packages(),
    package_data={
        "seo_agent": ["py.typed"],
    },
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "beautifulsoup4>=4.11.1",
        "google-ads>=21.1.0",
        "pydantic>=1.10.0",
        "python-dotenv>=0.21.0",
        "tqdm>=4.64.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=0.990",
        ],
    },
    entry_points={
        "console_scripts": [
            "seo-agent=seo_agent.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Marketing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Topic :: Internet :: WWW/HTTP :: Site Management :: Link Checking",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Utilities",
    ],
)

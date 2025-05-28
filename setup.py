from setuptools import setup, find_packages

setup(
    name="langflow",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "aiohttp==3.9.1",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "python-multipart==0.0.6",
        "pydantic==2.4.2",
        "cassandra-driver==3.28.0",
        "hubspot-api-client==4.0.0"
    ],
)

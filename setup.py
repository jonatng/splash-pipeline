from setuptools import setup, find_packages

setup(
    name="splash-pipeline",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "streamlit>=1.28.0",
        "sqlalchemy>=1.4.28,<2.0",
        "psycopg2-binary>=2.9.9",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "pydantic>=2.0.0",
        "supabase>=2.0.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.5",
        "email-validator>=2.0.0"
    ],
) 
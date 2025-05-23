from setuptools import setup, find_packages

setup(
    name="kb",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'faiss-cpu',
        'numpy',
        'openai',
        'python-dotenv',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'kb=src.cli:main',
        ],
    },
) 
from setuptools import setup, find_packages

setup(
    name="ai-utils-assist",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        'console_scripts': [
            'assist=assist.main:main',
        ],
    },
    install_requires=[
        'typing_extensions',
        'openai',
        'pyyaml'
    ],
)
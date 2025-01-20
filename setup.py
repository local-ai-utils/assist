from setuptools import setup, find_packages

setup(
    name="local-ai-utils-assist",
    version="0.1.0",
    packages=['assist'],
    package_dir={"assist": "assist"},
    entry_points={
        'console_scripts': [
            'assist=assist.cli:main',
        ],
    },
    install_requires=[
        'typing_extensions',
        'openai',
        'fire',
        'pyyaml'
    ],
)
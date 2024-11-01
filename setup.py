from setuptools import setup, find_packages

setup(
    name="local-ai-utils-assist",
    version="0.1.0",
    packages=['local_ai_utils_assist'],
    package_dir={"local_ai_utils_assist": "assist"},
    entry_points={
        'console_scripts': [
            'assist=local_ai_utils_assist.cli:main',
        ],
    },
    install_requires=[
        'typing_extensions',
        'openai',
        'fire',
        'pyyaml'
    ],
)
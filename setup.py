from setuptools import setup, find_packages

setup(
    name="local-ai-utils-assist",
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
        'pyyaml',
        'local_ai_utils_core==0.1.0'
    ],
)
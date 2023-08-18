from setuptools import setup
setup(
    name='tl',
    version='0.0.1',
    entry_points={
        'console_scripts': [
            'tl=tl:run'
        ]
    }
)

from distutils.core import setup

DESCRIPTION = ''
with open("README.md", "r") as f:
    DESCRIPTION = f.read()

setup(
    name='silly-server',
    description='One more silly server for mocking HTTP services',
    long_description=DESCRIPTION,
    author='Anton Baklanov',
    author_email='antonbaklanov@gmail.com',
    url='https://github.com/bak1an/silly-server',
    py_modules=[],
    license='MIT',
    scripts=['ss.py'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
    ],
    version='0.2',
)


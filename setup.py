from setuptools import setup, find_packages

setup(
    name='bifrost_enterobase',
    version='v1_1_5__',
    description='Enterobase component for salmonella serotyping',
    url='https://github.com/ssi-dk/bifrost_enterobase',
    author="Kristoffer Kiil",
    author_email="krki@ssi.dk",
    packages=find_packages(),
    install_requires=[
        'bifrostlib >= 2.1.9',
    ],
    package_data={"bifrost_enterobase": ['config.yaml']},
    include_package_data=True
)

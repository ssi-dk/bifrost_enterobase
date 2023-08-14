from setuptools import setup, find_namespace_packages

setup(
    name='bifrost_enterobase',
    version='1.1.5',
    description='Enterobase component for salmonella serotyping',
    url='https://github.com/ssi-dk/bifrost_enterobase',
    author="Kristoffer Kiil",
    author_email="krki@ssi.dk",
    packages=find_namespace_packages(),
    install_requires=[
        'bifrostlib >= 2.1.9',
    ],
    package_data={"bifrost_enterobase": ['config.yaml', 'pipeline.smk']},
    include_package_data=True
)

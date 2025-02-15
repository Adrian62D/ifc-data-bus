from setuptools import setup, find_packages

setup(
    name="ifc_databus",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "compas_eve>=1.0.0",
        "paho-mqtt",
        "automerge==1.0.0rc1",
        "python-dotenv>=1.0.0",
        "ifcopenshell>=0.8.0",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A data bus for IFC entities using CRDTs",
    keywords="ifc, crdt, mqtt, databus",
)

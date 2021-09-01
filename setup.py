from setuptools import setup, find_packages

setup(
    name='mps_spatial_helper',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/Data-Science-Policing-Security/MPS_Spatial_Helper',
    license='GPL-3.0 License',
    author='Andreas Varotsis',
    author_email='andreas.varotsis@met.police.uk',
    description='A collection of code designed to help ingestion, manipulation and visualisation of MPS spatial data',
    install_requires=[
        "geopandas",
        "folium",
        "h3"],
)

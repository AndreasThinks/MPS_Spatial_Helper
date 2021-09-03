# `MPS_Spatial_Helper` package

A collection of code designed to help ingestion, manipulation and visualisation of MPS spatial data

Due to issues with Geopandas and PIP, if you are running Windows, we recommend installing this first using Conda.

### Installation
Install directly from github using:
`python -m pip install git+https://github.com/Data-Science-Policing-Security/MPS_Spatial_Helper`


### Usage

The package contains 3 sub-modules
#### Live
- `create`: For creating geographical objects for analysis and processing using H3 grids

Please see [the sample notebook](https://github.com/Data-Science-Policing-Security/MPS_Spatial_Helper/blob/main/sample_notebooks/making_h3_grid.ipynb) for detailed instructions and examples.

#### Test
- `display`: *[in testing] For creating and displaying maps;*
- `ingest`: *[in testing] For ingesting data from MPS sources;*

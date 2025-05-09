# How to Create a Conda Environment to run this software
# Tested on Ubuntu 24 LTS 64 bits

conda create -n BCSOphyd
conda install conda-forge::bluesky
conda install conda-forge::happi
conda activate BCSOphyd
python main.py

# Requires ALS Labview Machine
# Tested on Labview 2018
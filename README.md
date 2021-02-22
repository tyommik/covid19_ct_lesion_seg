# COVID-19 Lung Infection Segmentation from CT Images 

Medical image segmentation pipeline to segment background and three lesions:
- Ground-glass opacity
- Consilidation
- Pleural Effusion

[![COVID-19](https://raw.githubusercontent.com/tyommik/covid19_ct_lesion_seg/main/docs/covid.png)]

## Reproducibility
- Ubuntu > 18.04
- Python > 3.6
- NVIDIA card with CUDA support (RTX 1070Ti or better)

### Step-by-Step workflow:

Download the code repository via git clone to your disk. Afterwards, install all required dependencies, download the dataset and setup the file structure.
```
git clone https://github.com/tyommik/covid19_ct_lesion_seg
cd covid19_ct_lesion_seg

conda env create --file environment.yml
jupyter lab
```
Run train.ipynb using your own data

## Dataset
Using private dataset. There is no option to provide it :(

## Results
Demo will be available soon
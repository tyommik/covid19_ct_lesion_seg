import shutil
import subprocess
import zipfile
import pathlib
import uuid
import torch
from lungmask import mask as lm
import lung_inference
import SimpleITK as sitk
import nibabel as nib
import os
import json

os.environ['CUDA_VISIBLE_DEVICES'] = ""

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f'Device: {device}')
# lungmask = lm.get_model('unet', 'R231CovidWeb')
lungmask_covid = torch.jit.load(f'models/covid19_last_jit.pth', map_location=device)


def get_inference(file_path, out_mask_file):
    slice_lung_volume = 0
    # Get lungmask inference from nii file
    input_image = sitk.ReadImage(str(file_path))

    # Calculate lung volume
    # segmentation = lm.inference(input_image, lungmask)

    # Calculate covid lesions
    result = lung_inference.apply(input_image, lungmask_covid, force_cpu=True)
    segmentation = result['mask']

    input_img = nib.load(str(file_path))
    new_img = input_img.__class__(segmentation.T, input_img.affine, input_img.header)
    new_img.to_filename(str(out_mask_file))
    return segmentation


def unzip(file_path):
    output_dir = file_path.parent / file_path.stem
    output_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

    return output_dir


def dcm2niix(file_path, fout):
    p = subprocess.run(f'bin/dcm2niix -o {fout} -f "%j_%s" -p y -z n  {file_path}', shell=True)
    if p.returncode != 0:
        return False
    return True


def get_data(path):
    """
    Search appopriate nii-file
    :param path: nii-files
    :return: file with chest and lung
    """
    correct_file = None
    for file in path.glob('*.json'):
        with pathlib.Path.open(file, 'r') as inf:
            try:
                data = json.load(inf)
            except Exception as err:
                continue
            if 'chest' in data.get('BodyPartExamined', "").lower() and 'lung' in data.get('SeriesDescription', "").lower():
                correct_file = file.with_suffix('.nii')
    return correct_file


def process_file(file_path):
    file_path = pathlib.Path(file_path)
    if file_path.suffix !='.nii' and \
        file_path.suffix !='.nii.gz' and \
        file_path.suffix != '.zip':
        return None

    guid = str(uuid.uuid4())[:8]
    fout = pathlib.Path('downloads') / guid
    fout.mkdir(exist_ok=True)

    if file_path.suffix == '.zip': # perhaps its DICOM
        unarchive_dir = unzip(file_path)
        is_successful = dcm2niix(unarchive_dir, fout)
        if not is_successful:
            return None
        correct_file = get_data(fout)

    elif file_path.suffix =='.nii' or file_path.suffix =='.nii.gz':
        correct_file = fout / file_path.name
        shutil.copy(file_path, correct_file)

    if correct_file:
        mask_file = correct_file.parent / (correct_file.stem + '_mask.nii')
        get_inference(correct_file, mask_file)
        return [str(correct_file), str(mask_file)]
    else:
        return None


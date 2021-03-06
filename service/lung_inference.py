import torch
from torch import tensor
import numpy as np
import scipy.ndimage as ndimage

import tqdm
import SimpleITK as sitk

from lungmask import utils


def reshape_mask(mask,tbox,origsize):
    res = np.ones(origsize)*0
    resize=[tbox[2]-tbox[0], tbox[3]-tbox[1]]
    imgres = ndimage.zoom(mask,resize/np.asarray(mask.shape),order=0)

    res[tbox[0]:tbox[2],tbox[1]:tbox[3]] = imgres
    return res


def broadcast_stats(dim, ndim, *t):
    v = [1]*ndim
    v[dim] = -1
    return [tensor(o).view(*v) for o in t[0]]


def inference(image, model=None, force_cpu=False):
    xs, ys, zs = image.GetSpacing()
    voxvol = np.prod(image.GetSpacing())
    inimg_raw = sitk.GetArrayFromImage(image)
    del image

    tvolslices, xnew_box = utils.preprocess(inimg_raw, resolution=[512, 512])
    tvolslices[tvolslices > 600] = 600
    tvolslices = np.divide((tvolslices+1024), 1624)
    outmask = np.empty((np.append(0, tvolslices[0].shape)), dtype=np.uint8)

    stats = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
    mean, std = broadcast_stats(1, 4, stats)

    for idx in tqdm.tqdm(range(tvolslices.shape[0])):
        data = tvolslices[idx, :, :]
        with torch.no_grad():

            data = np.expand_dims(np.expand_dims(data, 0), 0)
            data = torch.tensor(data)
            data = (data-mean) / std
            data = data.float() if force_cpu else data.cuda().float()
            pred = model(data)
            pls = torch.max(pred, 1)[1].detach().cpu().numpy().astype(np.uint8)
            outmask = np.vstack((outmask, pls))

    outmask = np.asarray([reshape_mask(outmask[i], xnew_box[i], inimg_raw.shape[1:]) for i in range(outmask.shape[0])], dtype=np.uint8)

    ggo = np.sum(outmask.T == 1) * xs * ys * zs * 0.001  # mm * mm * mm * 0.001 (cm)
    consolidation = np.sum(outmask.T == 2) * xs * ys * zs * 0.001  # mm * mm * mm * 0.001 (cm)
    pleural_effusion = np.sum(outmask.T == 3) * xs * ys * zs * 0.001  # mm * mm * mm * 0.001 (cm)

    return {"mask": outmask,
            "ggo": ggo,
            "consolidation": consolidation,
            "pleural_effusion": pleural_effusion
            }


def apply(image, net, force_cpu=False):
    return inference(image, net, force_cpu=force_cpu)


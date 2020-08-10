#!/usr/bin/env python3

import os.path as osp

import time

import copy
import numpy as np
from PIL import Image
import torch
from torchvision import transforms

from equilib.equi2equi import TorchEqui2Equi


def run(equi, rot):
    h_equi, w_equi = equi.shape[-2:]
    print('equirectangular image size:')
    print(h_equi, w_equi)

    # Variables:
    h_out = 320
    w_out = 640

    tic = time.perf_counter()
    equi2equi = TorchEqui2Equi(
        w_out=w_out,
        h_out=h_out,
    )
    toc = time.perf_counter()
    print(f"Init Equi2Equi: {toc - tic:0.4f} seconds")

    tic = time.perf_counter()
    sample = equi2equi(
        src=equi,
        rot=rot,
        sampling_method="torch",
        mode="bilinear",
        debug=True,
    )
    toc = time.perf_counter()
    print(f"Sample: {toc - tic:0.4f} seconds")

    return sample


def test_torch_single():
    data_path = osp.join('.', 'tests', 'data')
    result_path = osp.join('.', 'tests', 'results')
    equi_path = osp.join(data_path, 'test.jpg')
    device = torch.device('cuda')

    # Transforms
    to_tensor = transforms.Compose([
        transforms.ToTensor(),
    ])

    to_PIL = transforms.Compose([
        transforms.ToPILImage(),
    ])

    tic = time.perf_counter()
    equi_img = Image.open(equi_path)
    # NOTE: Sometimes images are RGBA
    equi_img = equi_img.convert('RGB')
    equi = to_tensor(equi_img)
    equi = equi.to(device)
    toc = time.perf_counter()
    print(f"Process equirectangular image: {toc - tic:0.4f} seconds")

    rot = {
        'roll': 0.,
        'pitch': 0.,
        'yaw': 0.,
    }

    sample = run(equi, rot)

    tic = time.perf_counter()
    out = sample.to('cpu')
    out_img = to_PIL(out)
    toc = time.perf_counter()
    print(f"post process: {toc - tic:0.4f} seconds")

    out_path = osp.join(result_path, 'equi2equi_torch_single.jpg')
    out_img.save(out_path)


def test_torch_batch():
    data_path = osp.join('.', 'tests', 'data')
    result_path = osp.join('.', 'tests', 'results')
    equi_path = osp.join(data_path, 'test.jpg')
    device = torch.device('cuda')
    batch_size = 16

    # Transforms
    to_tensor = transforms.Compose([
        transforms.ToTensor(),
    ])

    to_PIL = transforms.Compose([
        transforms.ToPILImage(),
    ])

    tic = time.perf_counter()
    equi_img = Image.open(equi_path)
    # NOTE: Sometimes images are RGBA
    equi_img = equi_img.convert('RGB')
    batched_equi = []
    for i in range(batch_size):
        equi = to_tensor(equi_img)
        batched_equi.append(copy.deepcopy(equi))
    batched_equi = torch.stack(batched_equi, dim=0)
    batched_equi = batched_equi.to(device)
    toc = time.perf_counter()
    print(f"Process equirectangular image: {toc - tic:0.4f} seconds")

    batched_rot = []
    inc = np.pi/8
    for i in range(batch_size):
        rot = {
            'roll': 0,
            'pitch': i * inc,
            'yaw': 0,
        }
        batched_rot.append(rot)

    batched_sample = run(batched_equi, batched_rot)
    tic = time.perf_counter()
    batched_out = []
    for i in range(batch_size):
        sample = copy.deepcopy(batched_sample[i])
        sample = sample.to('cpu')
        out_img = to_PIL(sample)
        batched_out.append(out_img)
    toc = time.perf_counter()
    print(f"post process: {toc - tic:0.4f} seconds")

    for i, out in enumerate(batched_out):
        out_path = osp.join(result_path, f'equi2equi_torch_batch_{i}.jpg')
        out.save(out_path)
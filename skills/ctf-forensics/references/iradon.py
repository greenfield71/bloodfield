#!/usr/bin/env python3
"""Inverse Radon (CT sinogram -> image) for forensics imaging challenges.

A "sinogram" is an (N_detectors x N_angles) projection array, often stored inside
a SQLite DB, a .npy, or a flat binary. iradon reconstructs the slice; the flag is
usually drawn in the reconstructed image. Volumetric variants stack many slices
and sum along an axis to reveal text.

Usage:
    python3 -I iradon.py sino.npy out.png
    python3 -I iradon.py --test            # self-test (forward then inverse Radon)

Deps: scikit-image + numpy (pure numpy FBP fallback included if skimage is missing).
"""
import sys
import numpy as np


def _fbp_numpy(sino, theta=None):
    """Pure NumPy Filtered Back Projection (Ram-Lak ramp filter)."""
    det, n_angles = sino.shape
    if theta is None:
        theta = np.linspace(0.0, 180.0, n_angles, endpoint=False)
    angles_rad = np.deg2rad(theta)

    # 1. Ramp filter in frequency domain
    n_pad = int(2 ** np.ceil(np.log2(max(2 * det, 64))))
    freqs = np.fft.fftfreq(n_pad)
    ramp = 2.0 * np.abs(freqs)

    sino_pad = np.pad(sino, ((0, n_pad - det), (0, 0)), mode="constant")
    f_sino = np.fft.fft(sino_pad, axis=0)
    filtered = np.fft.ifft(f_sino * ramp[:, None], axis=0).real[:det, :]

    # 2. Backprojection grid
    out_dim = det
    x = np.arange(out_dim) - out_dim / 2.0
    y = np.arange(out_dim) - out_dim / 2.0
    xx, yy = np.meshgrid(x, y)

    recon = np.zeros((out_dim, out_dim), dtype=float)
    det_center = det / 2.0

    for i, ang in enumerate(angles_rad):
        t = xx * np.cos(ang) + yy * np.sin(ang) + det_center
        t_floor = np.floor(t).astype(int)
        t_ceil = t_floor + 1
        valid = (t_floor >= 0) & (t_ceil < det)

        weight = t - t_floor
        proj = filtered[:, i]

        val = np.zeros_like(t)
        val[valid] = (1.0 - weight[valid]) * proj[t_floor[valid]] + weight[valid] * proj[t_ceil[valid]]
        recon += val

    recon *= np.pi / (2.0 * n_angles)
    return recon


def reconstruct(sino, theta=None, filter_name="ramp", center_pad=False):
    """sino: 2-D array (detector_pixels, n_angles) -> reconstructed slice."""
    sino = np.asarray(sino, dtype=float)
    if center_pad:
        max_dim = max(sino.shape[0], sino.shape[1])
        if sino.shape[0] < max_dim:
            pad_before = (max_dim - sino.shape[0]) // 2
            pad_after = max_dim - sino.shape[0] - pad_before
            sino = np.pad(sino, ((pad_before, pad_after), (0, 0)), mode="constant")

    if theta is None:
        theta = np.linspace(0.0, 180.0, sino.shape[1], endpoint=False)

    try:
        from skimage.transform import iradon
        return iradon(sino, theta=theta, filter_name=filter_name)
    except ImportError:
        return _fbp_numpy(sino, theta=theta)


def reconstruct_volume(slices, axis=0, center_pad=False):
    """slices: list/array of 2-D sinograms. Reconstruct each, sum along `axis`."""
    recons = [reconstruct(s, center_pad=center_pad) for s in slices]
    return np.sum(np.stack(recons), axis=axis)


def _save(img, path):
    from PIL import Image
    a = img - img.min()
    a = (255 * a / (a.max() or 1)).astype(np.uint8)
    Image.fromarray(a).save(path)


def _self_test():
    # Construct a synthetic phantom (bright rectangular bar)
    img = np.zeros((64, 64), dtype=float)
    img[20:44, 28:36] = 1.0

    theta = np.linspace(0.0, 180.0, 90, endpoint=False)
    det = 64

    try:
        from skimage.transform import radon
        sino = radon(img, theta=theta)
    except ImportError:
        # Pure numpy forward Radon simulation
        sino = np.zeros((det, len(theta)), dtype=float)
        x = np.arange(64) - 32.0
        xx, yy = np.meshgrid(x, x)
        for i, ang in enumerate(np.deg2rad(theta)):
            rot_x = xx * np.cos(-ang) - yy * np.sin(-ang) + 32.0
            rot_y = xx * np.sin(-ang) + yy * np.cos(-ang) + 32.0
            valid = (rot_x >= 0) & (rot_x < 63) & (rot_y >= 0) & (rot_y < 63)
            rx0, ry0 = rot_x.astype(int), rot_y.astype(int)
            sample = np.zeros_like(img)
            sample[valid] = img[ry0[valid], rx0[valid]]
            sino[:, i] = sample.sum(axis=0)

    recon = reconstruct(sino, theta=theta)
    c = np.corrcoef(img.ravel(), recon.ravel())[0, 1]
    assert c > 0.6, f"Correlation too low: {c}"

    # Also test volumetric reconstruction
    vol = reconstruct_volume([sino, sino], axis=0)
    assert vol.shape == (64, 64), f"Unexpected volume shape: {vol.shape}"

    print(f"[ok] iradon reconstructed phantom, corr={c:.3f}, volume shape={vol.shape}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--test":
        _self_test()
    elif len(sys.argv) >= 3:
        sino = np.load(sys.argv[1])
        _save(reconstruct(sino), sys.argv[2])
        print("wrote", sys.argv[2])
    else:
        print(__doc__)

#!/usr/bin/env python3
"""Extract Gamma(q) from F_incoh(q,t) and estimate diffusion coefficient."""

import argparse
import numpy as np
from scipy.optimize import curve_fit


def single_exponential(t, a, gamma):
    return a * np.exp(-gamma * t)


def extract_linewidths(npz_path, fit_range_ps=(0.1, 30.0)):
    data = np.load(npz_path)
    q_norms = data["q_norms"]
    time_fs = data["time_fs"]
    fqt_incoh = data["Fqt_incoh"]

    time_ps = time_fs / 1000.0
    t_min, t_max = fit_range_ps
    mask = (time_ps >= t_min) & (time_ps <= t_max)
    t_fit = time_ps[mask]

    gamma_q = np.full(len(q_norms), np.nan)
    gamma_q_err = np.full(len(q_norms), np.nan)

    for iq in range(len(q_norms)):
        if np.isnan(q_norms[iq]):
            continue
        y = fqt_incoh[iq, mask]
        if np.any(np.isnan(y)):
            continue
        try:
            popt, pcov = curve_fit(
                single_exponential,
                t_fit,
                y.real,
                p0=[1.0, 0.1],
                bounds=([0.0, 0.0], [2.0, 100.0]),
                maxfev=10000,
            )
            gamma_q[iq] = popt[1]
            gamma_q_err[iq] = np.sqrt(pcov[1, 1])
        except (RuntimeError, ValueError):
            continue

    hbar_meV_ps = 0.6582119514
    gamma_meV = gamma_q * hbar_meV_ps
    gamma_meV_err = gamma_q_err * hbar_meV_ps

    return q_norms, gamma_meV, gamma_meV_err


def fit_diffusion_coefficient(q_norms, gamma_meV, q_max_fit=1.0):
    # q_norms are in rad/Angstrom; convert to 1/Angstrom
    q_ainv = q_norms / (2.0 * np.pi)
    valid = (
        (~np.isnan(q_ainv))
        & (~np.isnan(gamma_meV))
        & (q_ainv < q_max_fit)
        & (q_ainv > 0)
    )

    if np.sum(valid) < 3:
        return np.nan

    q2 = q_ainv[valid] ** 2
    g = gamma_meV[valid]
    slope = np.polyfit(q2, g, 1)[0]

    hbar = 0.6582119514
    d_a2_per_ps = slope / hbar
    d_cm2_per_s = d_a2_per_ps * 1e-4
    return d_cm2_per_s


def main():
    parser = argparse.ArgumentParser(description="Extract Gamma(q) from F_incoh")
    parser.add_argument("npz", help="Path to _sqw_arrays.npz")
    args = parser.parse_args()

    q, gamma, gamma_err = extract_linewidths(args.npz)
    d = fit_diffusion_coefficient(q, gamma)

    print(f"D = {d:.3e} cm^2/s")


if __name__ == "__main__":
    main()

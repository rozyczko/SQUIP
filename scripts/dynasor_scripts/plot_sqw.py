#!/usr/bin/env python3
"""Plot S(q,w) and F(q,t) diagnostics."""

import argparse
import numpy as np
import matplotlib.pyplot as plt


def plot_sqw_heatmap(npz_path, title, output_path, energy_max=5.0):
    data = np.load(npz_path)
    q_norms = data["q_norms"]
    omega_meV = data["omega_meV"]
    sqw_incoh = data["Sqw_incoh"]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

    mask_w = (omega_meV >= 0) & (omega_meV <= energy_max)
    mask_q = ~np.isnan(q_norms)

    im = ax.pcolormesh(
        q_norms[mask_q],
        omega_meV[mask_w],
        sqw_incoh[np.ix_(mask_q, mask_w)].T,
        cmap="hot_r",
        shading="auto",
    )
    ax.set_xlabel("|q| (rad/Angstrom)")
    ax.set_ylabel("hbar*omega (meV)")
    ax.set_title(title)
    plt.colorbar(im, ax=ax, label="S_incoh(q,w)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fqt_decay(npz_path, title, output_path, q_targets=None):
    if q_targets is None:
        q_targets = [0.5, 1.0, 1.5]

    data = np.load(npz_path)
    q_norms = data["q_norms"]
    time_fs = data["time_fs"]
    fqt_incoh = data["Fqt_incoh"]
    time_ps = time_fs / 1000.0

    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)

    for q_target in q_targets:
        idx = np.nanargmin(np.abs(q_norms - q_target))
        if np.isnan(q_norms[idx]):
            continue
        label = f"|q| = {q_norms[idx]:.2f} rad/Angstrom"
        ax.plot(time_ps, fqt_incoh[idx, :].real, label=label, alpha=0.8)

    ax.set_xlabel("Time (ps)")
    ax.set_ylabel("F_incoh(q,t)")
    ax.set_title(title)
    ax.set_xlim([0, 30])
    ax.set_yscale("log")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Plot S(q,w) diagnostics")
    parser.add_argument("npz", help="Path to _sqw_arrays.npz")
    parser.add_argument("--out", required=True, help="Output PNG")
    parser.add_argument("--type", choices=["heatmap", "fqt"], default="heatmap")
    args = parser.parse_args()

    if args.type == "heatmap":
        plot_sqw_heatmap(args.npz, args.npz, args.out)
    else:
        plot_fqt_decay(args.npz, args.npz, args.out)


if __name__ == "__main__":
    main()

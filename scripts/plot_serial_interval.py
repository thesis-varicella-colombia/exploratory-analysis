"""Plot the discrete serial-interval weights used by the daily Rt estimator."""
from pathlib import Path
import inspect
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/varicella-matplotlib")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np

from epiestim_parametric_weekly import discr_si
from rt_daily_sivigila import estimate_daily

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/data_processed/numero_reproductivo"


def main():
    defaults = inspect.signature(estimate_daily).parameters
    mean = defaults["mean_si"].default
    sd = defaults["sd_si"].default
    days = np.arange(121)
    weights = discr_si(days, mean, sd)
    if weights[0] != 0 or not np.isclose(weights.sum(), 1, atol=1e-9, rtol=0):
        raise ValueError("Serial interval weights must sum to one and have no day-zero mass")

    shown = (days >= 1) & (days <= 35)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, ax = plt.subplots(figsize=(10, 5.3), layout="constrained")
    markers, stems, baseline = ax.stem(days[shown], weights[shown])
    plt.setp(markers, color="#176b68", markersize=5)
    plt.setp(stems, color="#176b68", linewidth=1.8)
    plt.setp(baseline, visible=False)
    ax.set_title("Distribución discreta del intervalo serial", loc="left", fontsize=16, pad=36)
    ax.text(0, 1.035, f"Pesos del modelo de Rₜ · media {mean:g} días · DE {sd:g} días".replace(".", ","),
            transform=ax.transAxes, color="#425c68", fontsize=11)
    ax.set_xlabel("Intervalo serial s (días)", labelpad=10)
    ax.set_ylabel("Probabilidad wₛ = P(S = s)", labelpad=10)
    ax.set(xlim=(0, 36), ylim=(0, .20), xticks=np.arange(0, 36, 2),
           yticks=np.arange(0, .201, .04))
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.grid(axis="y", color="#e4ecee")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    probability = weights[14]
    ax.annotate(f"14 días: {probability:.2%}".replace(".", ","), xy=(14, probability),
                xytext=(19, .16), color="#173042",
                arrowprops={"arrowstyle": "->", "color": "#425c68"})
    fig.text(.01, -.025, "Cada punto es una probabilidad para un día entero. Se muestran 1–35 días, sin renormalizar los pesos.",
             fontsize=9, color="#425c68")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for extension in ["png", "svg"]:
        path = OUTPUT / f"serial_interval.{extension}"
        fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
        print(path.relative_to(ROOT))
    plt.close(fig)
    print(f"w_14={probability:.8f}; total mass={weights.sum():.12f}")


if __name__ == "__main__":
    main()

import os
import matplotlib.pyplot as plt

from osdagbridge.core.reports.styles import CHART, COLORS

_STYLE_NAME = "seaborn-v0_8-whitegrid"
if _STYLE_NAME in plt.style.available:
  plt.style.use(_STYLE_NAME)

CHART_PRIMARY_COLOR = "#" + COLORS.get("steelBlue", "2B6CB0")
CHART_SECONDARY_COLOR = "#" + COLORS.get("osdagGreen", "91B014")
CHART_ACCENT_COLOR = "#" + COLORS.get("rebarAmber", "D97706")
CHART_FAIL_COLOR = "#" + COLORS.get("failRed", "C62828")
CHART_THRESHOLD_COLOR = CHART.get("threshold_color", "#C62828")
CHART_THRESHOLD_STYLE = CHART.get("threshold_style", "--")
CHART_THRESHOLD_VALUE = float(CHART.get("threshold_value", 1.0))
CHART_DPI = int(CHART.get("dpi", 300))
CHART_GRID_STYLE = CHART.get("grid_style", ":")
CHART_GRID_ALPHA = float(CHART.get("grid_alpha", 0.6))


def _ensure_parent_dir(out_abs: str) -> None:
  out_dir = os.path.dirname(out_abs)
  if out_dir:
    os.makedirs(out_dir, exist_ok=True)


def generate_ur_chart(
    ur_data: dict[str, float], output_path: str = "ur_summary_chart.png"
) -> str:
  """Vertical bar chart with Utilization Ratio on Y-axis and horizontal threshold at UR = 1.0."""
  if not ur_data:
    return ""

  labels = list(ur_data.keys())
  values = [max(0.0, float(v)) for v in ur_data.values()]

  fig, ax = plt.subplots(figsize=(8.0, 4.4), dpi=CHART_DPI)

  bar_colors = [
      CHART_FAIL_COLOR if v > CHART_THRESHOLD_VALUE else CHART_PRIMARY_COLOR
      for v in values
  ]
  bars = ax.bar(labels, values, color=bar_colors, width=0.48, edgecolor="none")

  # Horizontal red dashed threshold line at UR = 1.0
  ax.axhline(
      CHART_THRESHOLD_VALUE,
      color=CHART_THRESHOLD_COLOR,
      linestyle=CHART_THRESHOLD_STYLE,
      linewidth=1.6,
      label=f"Threshold (UR = {CHART_THRESHOLD_VALUE:.1f})",
      zorder=3,
  )

  max_val = max(values + [CHART_THRESHOLD_VALUE])
  ax.set_ylim(0, max_val * 1.20)

  for bar, val in zip(bars, values):
    # Offset label slightly above or below threshold line to avoid collision
    y_pos = val + max_val * 0.025
    va = "bottom"
    if abs(val - CHART_THRESHOLD_VALUE) < 0.08:
      y_pos = val - max_val * 0.06
      va = "top"
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        max(0.02, y_pos),
        f"{val:.2f}",
        ha="center",
        va=va,
        fontsize=9.5,
        fontweight="bold",
        color="#1a202c",
        zorder=4,
    )

  ax.set_ylabel(
      "Utilization Ratio (Demand / Capacity)", fontsize=10, fontweight="bold"
  )
  ax.set_title(
      "Overall Element Utilization Ratio Summary",
      fontsize=11.5,
      fontweight="bold",
      pad=10,
  )
  ax.tick_params(axis="x", labelsize=9, rotation=20)
  ax.grid(axis="y", linestyle=CHART_GRID_STYLE, alpha=CHART_GRID_ALPHA)
  ax.set_axisbelow(True)
  ax.legend(loc="upper right", frameon=True, fontsize=9)

  plt.tight_layout()
  out_abs = os.path.abspath(output_path)
  _ensure_parent_dir(out_abs)
  fig.savefig(out_abs, dpi=CHART_DPI, bbox_inches="tight")
  plt.close(fig)
  return out_abs


def generate_steel_breakdown_chart(
    quantities: dict, output_path: str = "steel_breakdown_chart.png"
) -> str:
  """Bar chart splitting structural steel tonnage (MT) by component."""
  quantities = quantities or {}
  labels = ["Steel Girders", "Cross Bracing", "End Diaphragms"]
  try:
    girders = float(quantities.get("steel_girders_wt_total", 0) or 0)
    bracing = float(quantities.get("steel_bracing_wt_total", 0) or 0)
    diaphragms = float(quantities.get("steel_diaphragm_wt_total", 0) or 0)
  except Exception:
    girders = bracing = diaphragms = 0.0

  vals = [girders, bracing, diaphragms]
  fig, ax = plt.subplots(figsize=(6.8, 3.6), dpi=CHART_DPI)
  steel_colors = [
      CHART_PRIMARY_COLOR,
      "#" + COLORS.get("steelMid", "3182CE"),
      "#" + COLORS.get("steelLight", "63B3ED"),
  ]
  bars = ax.bar(labels, vals, color=steel_colors, width=0.45)

  max_val = max(vals + [1.0])
  ax.set_ylim(0, max_val * 1.18)
  ax.set_ylabel("Weight (MT)", fontsize=10, fontweight="bold")
  ax.set_title(
      "Structural Steel Tonnage Breakdown (MT)",
      fontsize=11,
      fontweight="bold",
      pad=10,
  )
  ax.grid(axis="y", linestyle=CHART_GRID_STYLE, alpha=CHART_GRID_ALPHA)
  ax.set_axisbelow(True)

  for bar, v in zip(bars, vals):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        v + max_val * 0.02,
        f"{v:.2f}",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )

  plt.tight_layout()
  out_abs = os.path.abspath(output_path)
  _ensure_parent_dir(out_abs)
  fig.savefig(out_abs, dpi=CHART_DPI, bbox_inches="tight")
  plt.close(fig)
  return out_abs


def generate_concrete_rebar_chart(
    quantities: dict, output_path: str = "concrete_rebar_chart.png"
) -> str:
  """Side-by-side comparison of Concrete Deck Volume (m³) vs. Reinforcement Weight (MT)."""
  quantities = quantities or {}
  try:
    conc_vol = float(quantities.get("concrete_deck_vol_total", 0) or 0)
    rebar_wt = float(quantities.get("rebar_deck_wt_total", 0) or 0)
  except Exception:
    conc_vol = rebar_wt = 0.0

  fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.4, 3.6), dpi=CHART_DPI)

  b1 = ax1.bar(
      ["Concrete Deck"], [conc_vol], color=CHART_SECONDARY_COLOR, width=0.4
  )
  ax1.set_ylim(0, max(conc_vol, 1.0) * 1.2)
  ax1.set_ylabel("Volume (m³)", fontsize=9.5, fontweight="bold")
  ax1.set_title("Concrete Volume (m³)", fontsize=10, fontweight="bold")
  ax1.grid(axis="y", linestyle=CHART_GRID_STYLE, alpha=CHART_GRID_ALPHA)
  ax1.set_axisbelow(True)
  ax1.text(
      b1[0].get_x() + b1[0].get_width() / 2,
      conc_vol + max(conc_vol, 1.0) * 0.02,
      f"{conc_vol:.2f}",
      ha="center",
      va="bottom",
      fontsize=9,
      fontweight="bold",
  )

  b2 = ax2.bar(
      ["Reinforcement (Rebar)"], [rebar_wt], color=CHART_ACCENT_COLOR, width=0.4
  )
  ax2.set_ylim(0, max(rebar_wt, 1.0) * 1.2)
  ax2.set_ylabel("Weight (MT)", fontsize=9.5, fontweight="bold")
  ax2.set_title("Rebar Weight (MT)", fontsize=10, fontweight="bold")
  ax2.grid(axis="y", linestyle=CHART_GRID_STYLE, alpha=CHART_GRID_ALPHA)
  ax2.set_axisbelow(True)
  ax2.text(
      b2[0].get_x() + b2[0].get_width() / 2,
      rebar_wt + max(rebar_wt, 1.0) * 0.02,
      f"{rebar_wt:.2f}",
      ha="center",
      va="bottom",
      fontsize=9,
      fontweight="bold",
  )

  plt.tight_layout()
  out_abs = os.path.abspath(output_path)
  _ensure_parent_dir(out_abs)
  fig.savefig(out_abs, dpi=CHART_DPI, bbox_inches="tight")
  plt.close(fig)
  return out_abs


def generate_material_chart(
    quantities: dict, output_path: str = "material_summary_chart.png"
):
  """Backwards-compatible wrapper generating both steel breakdown and concrete/rebar charts."""
  out_abs = os.path.abspath(output_path)
  base, ext = os.path.splitext(out_abs)
  ext = ext or ".png"
  steel_path = generate_steel_breakdown_chart(quantities, f"{base}_steel{ext}")
  conc_path = generate_concrete_rebar_chart(
      quantities, f"{base}_concrete_rebar{ext}"
  )
  return steel_path if steel_path else conc_path
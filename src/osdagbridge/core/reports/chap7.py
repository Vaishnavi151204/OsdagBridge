# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# =============================================================================

import os
from osdagbridge.core.reports.report_charts import (
    generate_steel_breakdown_chart,
    generate_concrete_rebar_chart,
)
from osdagbridge.core.reports.styles import TABLE


def _figure_snippet(img_path: str, caption: str, label: str) -> str:
  if not img_path or not os.path.exists(img_path):
    return ""
  p = os.path.abspath(img_path).replace("\\", "/")
  return (
      "\n"
      r"\begin{figure}[htbp!]"
      "\n"
      r"\centering"
      "\n"
      r"\includegraphics[width=0.82\textwidth]{"
      + p
      + r"}"
      "\n"
      r"\caption{"
      + caption
      + r"}"
      "\n"
      r"\label{"
      + label
      + r"}"
      "\n"
      r"\end{figure}"
      "\n"
  )


def ch7_quantities(input_dict, output_dict=None):
  input_dict = input_dict or {}
  if output_dict is None:
    output_dict = {}

  def to_number(value):
    try:
      if value is None or str(value).strip() in (
          "",
          "N.A.",
          "N/A",
          "None",
          "---",
      ):
        return None
      return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
      return None

  def get_num(keys, default=0.0):
    if isinstance(keys, str):
      keys = [keys]
    for key in keys:
      val = to_number(input_dict.get(key))
      if val is not None:
        return val
      val = to_number(output_dict.get(key))
      if val is not None:
        return val
    return default

  def fmt_val(val):
    return f"{val:.2f}" if val is not None else "---"

  girders_total = get_num(
      ["steel_girders_wt_total", "girder_steel_wt", "girders_wt_total"], 0.0
  )
  bracing_total = get_num(
      ["steel_bracing_wt_total", "cross_bracing_wt_total", "bracing_wt_total"],
      0.0,
  )
  diaphragm_total = get_num(
      [
          "steel_diaphragm_wt_total",
          "end_diaphragm_wt_total",
          "diaphragms_wt_total",
      ],
      bracing_total,
  )
  concrete_total = get_num(
      ["concrete_deck_vol_total", "deck_concrete_vol_total", "concrete_vol"],
      0.0,
  )
  rebar_total = get_num(
      ["rebar_deck_wt_total", "reinforcement_wt_total", "rebar_wt"], 0.0
  )

  quantities = {
      "steel_girders_wt_total": girders_total,
      "steel_bracing_wt_total": bracing_total,
      "steel_diaphragm_wt_total": diaphragm_total,
      "concrete_deck_vol_total": concrete_total,
      "rebar_deck_wt_total": rebar_total,
  }

  charts_block = ""
  try:
    steel_chart = generate_steel_breakdown_chart(quantities)
    conc_chart = generate_concrete_rebar_chart(quantities)
    charts_block += _figure_snippet(
        steel_chart,
        (
            "Structural Steel Tonnage Breakdown (Girders, Cross Bracing \\&"
            " End Diaphragms)"
        ),
        "fig:steel_breakdown",
    )
    charts_block += _figure_snippet(
        conc_chart,
        "Concrete Deck Volume ($\\text{m}^3$) vs. Reinforcement Steel Weight"
        " (MT)",
        "fig:concrete_rebar",
    )
  except Exception:
    charts_block = ""

  tabcolsep = TABLE.get("tabcolsep", "6pt")
  arraystretch = TABLE.get("arraystretch", "1.12")

  report = (
      r"""
\chapter{Material Take-off \& Quantity Summary}

This chapter provides a summary of material quantities required for the bridge superstructure, including structural steel tonnage, concrete deck volume, and reinforcement steel weight.

\begingroup
\setlength{\tabcolsep}{"""
      + tabcolsep
      + r"""}
\renewcommand{\arraystretch}{"""
      + arraystretch
      + r"""}
\vspace{1em}
\begin{longtable}{|L{7.2cm}|c|c|c|}
\caption{\textbf{Bill of Materials Summary}} \\
\hline
\textbf{Item Description} & \textbf{Qty} & \textbf{Unit} & \textbf{Total Weight / Volume} \\
\hline
\endfirsthead
\multicolumn{4}{c}%
{{\tablename\ \thetable\ -- \textit{Continued from previous page}}} \\
\hline
\textbf{Item Description} & \textbf{Qty} & \textbf{Unit} & \textbf{Total Weight / Volume} \\
\hline
\endhead
\hline \multicolumn{4}{r}{\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot

Structural Steel Girders & -- & MT & """
      + fmt_val(quantities["steel_girders_wt_total"])
      + r""" \\
\hline
Cross Bracing & -- & MT & """
      + fmt_val(quantities["steel_bracing_wt_total"])
      + r""" \\
\hline
End Diaphragms & -- & MT & """
      + fmt_val(quantities["steel_diaphragm_wt_total"])
      + r""" \\
\hline
Concrete Deck Slab & -- & m$^3$ & """
      + fmt_val(quantities["concrete_deck_vol_total"])
      + r""" \\
\hline
Reinforcement Steel (Rebar) & -- & MT & """
      + fmt_val(quantities["rebar_deck_wt_total"])
      + r""" \\
\hline
\end{longtable}
\endgroup
"""
  )

  report += "\n" + charts_block
  return report
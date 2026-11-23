# =============================================================================
# OsdagBridge — Report Generator
# =============================================================================

import datetime
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional

from osdagbridge.core.reports import styles as S
from osdagbridge.core.reports.report_utils import _tex, add_longtable_headers
from osdagbridge.core.utils.common import (
    KEY_DESIGN_MODE,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
)

from .chap1 import ch1_project_info
from .chap2 import ch2_input_parameters
from .chap3 import ch3_loads
from .chap4 import ch4_analysis
from .chap5 import ch5_design_checks
from .chap6 import ch6_drawings
from .chap7 import ch7_quantities
from .chap8 import ch8_design_log
from .chap9 import references
from .executive_summary import executive_summary

logger = logging.getLogger(__name__)


def _find_pdflatex() -> Optional[str]:
  """Locate pdflatex via PATH or common MiKTeX / TeX Live directories."""
  found = shutil.which("pdflatex")
  if found:
    return found

  candidate_dirs = [
      os.path.expandvars(r"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64"),
      r"C:\Program Files\MiKTeX\miktex\bin\x64",
      r"C:\Program Files (x86)\MiKTeX\miktex\bin\x64",
  ]

  texlive_root = r"C:\texlive"
  if os.path.isdir(texlive_root):
    for entry in sorted(os.listdir(texlive_root), reverse=True):
      candidate_dirs.append(
          os.path.join(texlive_root, entry, "bin", "windows")
      )

  for folder in candidate_dirs:
    exe_path = os.path.join(folder, "pdflatex.exe")
    if os.path.isfile(exe_path):
      return exe_path

  return None


# ═══════════════════════════════════════════════════════════════════════════════
# PREAMBLE / TITLE PAGE / TOC
# ═══════════════════════════════════════════════════════════════════════════════


def preamble(project_name, job_number, report_date, report_version="Rev 0"):
  pn = _tex(project_name)
  jn = _tex(job_number)
  rd = _tex(report_date)
  rv = _tex(report_version)
  head_l = pn + r" $|$ " + jn
  head_r = rd + r" $|$ " + rv
  return "\n".join([
      r"\documentclass[" + S.DOCUMENT_CLASS_OPTIONS + r"]{report}",
      "",
      r"% Packages",
      r"\usepackage[" + S.geometry_options() + r"]{geometry}",
      S.PACKAGES,
      "",
      r"\numberwithin{table}{chapter}",
      r"\numberwithin{figure}{chapter}",
      S.table_settings(),
      "",
      S.color_definitions(),
      "",
      S.pagestyle("main", head_l, head_r),
      S.pagestyle("plain", head_l, head_r),
      S.firstpage_style(),
      r"\pagestyle{main}",
      r"\setstretch{" + str(S.LINE_STRETCH) + r"}",
      "",
      S.LATEX_HELPERS,
      "",
      (
          r"\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source"
          r" Software for Steel Girder Bridge Design \\ \vspace{2cm} \large"
          r" Design Report}"
      ),
      r"\author{}",
      r"\date{}",
      "",
      r"\begin{document}",
      "",
  ])


def title_page(m, osdag_logo, org_logo):
  if osdag_logo:
    lhs = (
        r"\includegraphics[width=\linewidth,keepaspectratio]{"
        + osdag_logo.replace("\\", "/")
        + r"}"
    )
  else:
    lhs = r"\textit{(Osdag Logo)}"

  if org_logo:
    rhs = (
        r"\includegraphics[width=\linewidth,height=2.2cm,keepaspectratio]{"
        + org_logo.replace("\\", "/")
        + r"}"
    )
  else:
    rhs = r""

  logos_tex = (
      r"""\noindent
\begin{minipage}[c]{0.6\textwidth}
\raggedright
"""
      + lhs
      + r"""
\end{minipage}%
\hfill
\begin{minipage}[c]{0.35\textwidth}
\raggedleft
"""
      + rhs
      + r"""
\end{minipage}
\\[1cm]
"""
  )

  return (
      r"""
\begin{titlepage}
\thispagestyle{firstpage}
\centering
\vspace*{1.5cm}
"""
      + logos_tex
      + r"""
{\Huge \textbf{OsdagBridge}}\\[0.3cm]
{\large Open Source Software for Steel Girder Bridge Design}\\[1.5cm]
{\Large Design Report}\\[1.5cm]
\begin{tabular}{|L{4cm}|L{10cm}|}
\hline
\textbf{Project Name} & """
      + _tex(m.project_name)
      + r""" \\
\hline
\textbf{Project Location} & """
      + _tex(m.project_location)
      + r""" \\
\hline
\textbf{Author / Designer} & """
      + _tex(m.designer)
      + r""" \\
\hline
\textbf{Reviewer} & """
      + _tex(m.reviewer)
      + r""" \\
\hline
\textbf{Organization} & """
      + _tex(m.company)
      + r""" \\
\hline
\textbf{Client Name and Organization} & """
      + _tex(m.client)
      + r""" \\
\hline
\textbf{Job Number} & """
      + _tex(m.job_number)
      + r""" \\
\hline
\textbf{Date} & """
      + _tex(m.report_date)
      + r""" \\
\hline
\textbf{Report Version} & """
      + (_tex(m.subtitle) if m.subtitle else "")
      + r""" \\
\hline
\end{tabular}
\end{titlepage}
"""
  )


def toc_section():
  return r"""
% Chapter / TOC Formatting
\titleformat{\chapter}[block]
  {\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{0pt}{10pt}
\setcounter{tocdepth}{2}

% TOC styling using titletoc
\titlecontents{chapter}[1.5em]
  {\normalfont\vspace{2pt}}
  {\contentslabel{1.5em}}
  {\hspace*{-1.5em}}
  {\hfill\contentspage}

\titlecontents{section}[3.8em]
  {\normalfont}
  {\contentslabel{2.3em}}
  {\hspace*{-2.3em}}
  {\hfill\contentspage}

\titlecontents{subsection}[7.0em]
  {\normalfont}
  {\contentslabel{3.2em}}
  {\hspace*{-3.2em}}
  {\hfill\contentspage}

\newpage
\renewcommand{\contentsname}{\centering\Large\bfseries Table of Contents}
\tableofcontents
"""


# ---------------------------------------------------------------------------
# Public data-classes
# ---------------------------------------------------------------------------


@dataclass
class ReportMetadata:
  project_name: str
  project_location: str
  designer: str
  client: str
  company: str
  group_name: str = ""
  subtitle: str = ""
  job_number: str = ""
  additional_comments: str = ""
  logo_path: Optional[str] = None
  report_date: str = ""
  reviewer: str = ""


@dataclass
class ReportOptions:
  sections: List[str]
  include_figures: bool
  include_toc: bool
  include_pdf: bool


@dataclass
class ReportRequest:
  metadata: ReportMetadata
  options: ReportOptions
  output_dir: str
  file_stem: str


@dataclass
class ReportFigures:
  plan: Optional[str] = None
  cross_section: Optional[str] = None
  final_geometry: Optional[str] = None
  longitudinal_elevation: Optional[str] = None
  girder_3d: Optional[str] = None
  girder_front: Optional[str] = None
  girder_top: Optional[str] = None
  girder_end: Optional[str] = None
  bm_envelope: Optional[str] = None
  sf_envelope: Optional[str] = None
  defl_ll: Optional[str] = None
  shear_connector: Optional[str] = None
  cross_bracing: Optional[str] = None


@dataclass
class ReportPayload:
  metadata: ReportMetadata
  options: ReportOptions
  inputs: dict
  analysis_summary: dict
  design_checks: list
  figures: ReportFigures
  log_entries: List[str] = field(default_factory=list)
  output_dict: dict = field(default_factory=dict)
  figure_data: dict = field(default_factory=dict)


@dataclass
class ReportResult:
  pdf_path: Optional[str]
  tex_path: Optional[str]


class ReportDataBridge:
  """Centralized data extraction for the OsdagBridge report."""

  def __init__(
      self, output_dict: dict, input_dict: dict, payload: "ReportPayload"
  ):
    self.output_dict = output_dict
    self.input_dict = input_dict
    self.payload = payload

  def _cb_forces_dict(self) -> dict:
    return self.output_dict.get("crossbracing_forces_dict", {})

  def _cb_pair_designs(self) -> dict:
    return self.output_dict.get("crossbracing_design_results", {})

  def _cb_osdag(self, pair: str, member: str, force_type: str) -> dict:
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

    try:
      raw = self._cb_pair_designs()[pair][member][force_type]
      return _extract_osdag_summary(raw or {})
    except (KeyError, TypeError):
      return {}

  def get_cb_pairs(self) -> list:
    try:
      return sorted(self._cb_forces_dict().get("pairs", {}).keys())
    except Exception:
      return []

  def get_cb_geometry(self) -> dict:
    return self._cb_forces_dict().get("geometry", {})

  def get_cb_brace_type(self) -> str:
    try:
      return self._cb_forces_dict().get("brace_type", "X")
    except Exception:
      return "X"

  def get_cb_force(self, pair: str, member: str, force_type: str) -> str:
    try:
      pairs = self._cb_forces_dict()["pairs"][pair]
      key = (
          f"diag_{force_type}_kN"
          if member == "diagonal"
          else f"chord_{force_type}_kN"
      )
      val = pairs.get(key)
      if val is not None:
        return f"{val:.3f}"
    except (KeyError, TypeError):
      pass
    return ""

  def get_cb_nature(self, pair: str, member: str) -> str:
    try:
      pairs = self._cb_forces_dict()["pairs"][pair]
      t_key = "diag_tension_kN" if member == "diagonal" else "chord_tension_kN"
      c_key = (
          "diag_compression_kN"
          if member == "diagonal"
          else "chord_compression_kN"
      )
      has_t = pairs.get(t_key) is not None
      has_c = pairs.get(c_key) is not None
      if has_t and has_c:
        return "T / C"
      if has_t:
        return "T"
      if has_c:
        return "C"
    except (KeyError, TypeError):
      pass
    return ""

  def get_cb_governing_force(self, pair: str, member: str) -> tuple:
    try:
      pairs = self._cb_forces_dict()["pairs"][pair]
      t_key = "diag_tension_kN" if member == "diagonal" else "chord_tension_kN"
      c_key = (
          "diag_compression_kN"
          if member == "diagonal"
          else "chord_compression_kN"
      )
      t_val = pairs.get(t_key)
      c_val = pairs.get(c_key)
      if t_val is not None and c_val is not None:
        if abs(c_val) >= abs(t_val):
          return (f"{c_val:.3f}", "compression")
        return (f"{t_val:.3f}", "tension")
      if c_val is not None:
        return (f"{c_val:.3f}", "compression")
      if t_val is not None:
        return (f"{t_val:.3f}", "tension")
    except (KeyError, TypeError):
      pass
    return ("", "compression")

  def get_cb_section(self, pair: str, member: str, force_type: str) -> str:
    val = self._cb_osdag(pair, member, force_type).get("section")
    return _tex(val) if val else ""

  def get_cb_capacity(self, pair: str, member: str, force_type: str) -> str:
    val = self._cb_osdag(pair, member, force_type).get("capacity_kN")
    return f"{float(val):.3f}" if val is not None else ""

  def get_cb_efficiency(self, pair: str, member: str, force_type: str) -> str:
    val = self._cb_osdag(pair, member, force_type).get("efficiency")
    return f"{float(val):.3f}" if val is not None else ""

  def get_cb_slenderness(self, pair: str, member: str) -> str:
    for ft in ("compression", "tension"):
      val = self._cb_osdag(pair, member, ft).get("slenderness")
      if val is not None:
        return f"{float(val):.1f}"
    return ""

  def get_cb_status(self, pair: str, member: str, force_type: str) -> str:
    try:
      val = self._cb_osdag(pair, member, force_type).get("efficiency")
      if val is not None:
        ur = float(val)
        if ur <= 1.0:
          return r"\textcolor{black}{PASS}"
        return r"\textcolor{red}{FAIL}"
    except (TypeError, ValueError):
      pass
    return ""

  def get_cb_gov_lc(self, pair: str, member: str, force_type: str) -> str:
    try:
      pfx = "diag" if member == "diagonal" else "chord"
      key = f"{pfx}_{force_type}_gov_lc"
      val = self._cb_forces_dict()["pairs"][pair].get(key)
      return _tex(val) if val else ""
    except (KeyError, TypeError):
      return ""

  def get_cb_connection(self, pair: str, member: str, force_type: str) -> str:
    val = self._cb_osdag(pair, member, force_type).get("connection")
    return str(val) if val else ""

  def get_cb_effective_length(self, member: str) -> str:
    try:
      geom = self.get_cb_geometry()
      if member == "diagonal":
        L_m = geom.get("diagonal_length_m", 0)
      else:
        L_m = geom.get("horiz_proj_m", 0)
      return f"{L_m * 1000:.0f}"
    except (TypeError, ValueError):
      return ""

  def get_cb_alpha_deg(self) -> str:
    try:
      return f"{self.get_cb_geometry().get('alpha_deg', 0):.2f}"
    except Exception:
      return ""


def _format_project_location(pl_data):
  if not pl_data:
    return ""
  if isinstance(pl_data, str):
    try:
      import ast

      pl_dict = ast.literal_eval(pl_data)
    except Exception:
      return pl_data
  elif isinstance(pl_data, dict):
    pl_dict = pl_data
  else:
    return str(pl_data)

  method = pl_dict.get("method")
  data = pl_dict.get("data", {})

  if method == "location_name":
    dist = data.get("district", "")
    state = data.get("state", "")
    if dist and state:
      return f"{dist}, {state}"
    return dist or state or r""
  elif method == "map":
    lat = data.get("latitude", "")
    lon = data.get("longitude", "")
    if lat and lon:
      try:
        from osdagbridge.core.bridge_types.plate_girder.ui_fields_project_location import DB_PATH
        from osdagbridge.core.data.project_location.database import Database

        db = Database(DB_PATH)
        db.connect()
        nearest = db.get_nearest_station_temperature(float(lat), float(lon))
        db.close()
        if nearest:
          return f"{nearest['station']}, {nearest['state']}"
      except Exception as e:
        logger.warning(f"Reverse geocode error: {e}")
      return f"Lat: {lat}°, Lon: {lon}°"
    return "Map Location"
  elif method == "custom_data":
    return "Custom Location Data"

  return str(pl_data)


def build_report_payload(request, input_dict, output_dict):
  try:
    rd = request.metadata.report_date or datetime.date.today().isoformat()
    lp = request.metadata.logo_path
    raw_pl = (
        request.metadata.project_location
        or input_dict.get("project.location")
        or ""
    )
    pl = _format_project_location(raw_pl)

    md = ReportMetadata(
        project_name=request.metadata.project_name,
        project_location=pl,
        designer=request.metadata.designer,
        client=request.metadata.client,
        company=request.metadata.company,
        group_name=request.metadata.group_name,
        subtitle=request.metadata.subtitle,
        job_number=request.metadata.job_number,
        additional_comments=request.metadata.additional_comments,
        logo_path=lp,
        report_date=rd,
        reviewer=getattr(request.metadata, "reviewer", ""),
    )

    try:
      import ast

      if isinstance(raw_pl, str) and "{" in raw_pl:
        pl_dict = ast.literal_eval(raw_pl)
      elif isinstance(raw_pl, dict):
        pl_dict = raw_pl
      else:
        pl_dict = {}

      if pl_dict and isinstance(pl_dict, dict):
        data = pl_dict.get("data", {})
        weather = pl_dict.get("weather_data", {})

        lat_val = data.get("latitude") or weather.get("latitude")
        lon_val = data.get("longitude") or weather.get("longitude")

        if "latitude" not in input_dict and lat_val:
          input_dict["latitude"] = lat_val
        if "longitude" not in input_dict and lon_val:
          input_dict["longitude"] = lon_val

        if "seismic_zone" not in input_dict and weather.get("zone"):
          input_dict["seismic_zone"] = weather.get("zone")
        if "wind_speed" not in input_dict and weather.get("wind_speed"):
          input_dict["wind_speed"] = weather.get("wind_speed")
        if "shade_temp_max" not in input_dict and weather.get("max_temp"):
          input_dict["shade_temp_max"] = weather.get("max_temp")
        if "shade_temp_min" not in input_dict and weather.get("min_temp"):
          input_dict["shade_temp_min"] = weather.get("min_temp")
    except Exception as e:
      logger.warning(f"Failed to parse project location data: {e}")

    for _tkey in (
        KEY_TL_BRIDGE_TEMP_MIN,
        KEY_TL_BRIDGE_TEMP_MAX,
        KEY_TL_TEMP_RISE,
        KEY_TL_TEMP_FALL,
    ):
      if not input_dict.get(_tkey) and output_dict.get(_tkey):
        input_dict[_tkey] = output_dict[_tkey]

    if not input_dict.get(KEY_TL_BRIDGE_TEMP_MIN):
      try:
        max_str = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get(
            "shade_temp_max"
        )
        min_str = input_dict.get(KEY_TL_LOWEST_MIN_TEMP) or input_dict.get(
            "shade_temp_min"
        )
        if max_str and min_str:
          from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

          res = IRC6_2017.cl_215_2_effective_bridge_temperature(
              float(max_str), float(min_str), "metallic", False
          )
          t_min = res.get("T_min", 0)
          t_max = res.get("T_max", 0)
          mean = (t_max + t_min) / 2.0
          input_dict[KEY_TL_BRIDGE_TEMP_MIN] = f"{t_min:.2f}"
          input_dict[KEY_TL_BRIDGE_TEMP_MAX] = f"{t_max:.2f}"
          input_dict[KEY_TL_TEMP_RISE] = f"{t_max - mean:.2f}"
          input_dict[KEY_TL_TEMP_FALL] = f"{mean - t_min:.2f}"
      except Exception as _te:
        logger.warning(f"Could not compute temperature values for report: {_te}")

    asum = output_dict.get("analysis_summary", {}) if output_dict else {}
    dc = output_dict.get("design_checks", []) if output_dict else []
    le = output_dict.get("design_log", []) if output_dict else []

    if not le:
      try:
        from osdagbridge.core.utils.logger import bridge_logger

        le = bridge_logger.get_success_log()
      except Exception as _le:
        logger.warning("Could not read design log from logger: %s", _le)

    return ReportPayload(
        metadata=md,
        options=request.options,
        inputs=input_dict,
        analysis_summary=asum,
        design_checks=dc,
        figures=ReportFigures(),
        log_entries=le,
        output_dict=output_dict or {},
    )

  except Exception as exc:
    logger.warning("build_report_payload error: %s", exc)
    return ReportPayload(
        metadata=request.metadata,
        options=request.options,
        inputs={},
        analysis_summary={},
        design_checks=[],
        figures=ReportFigures(),
        log_entries=[],
        output_dict={},
    )


_FIGURE_MAP = [
    ("plan", "plan.png"),
    ("cross_section", "cross_section.png"),
    ("final_geometry", "final_geometry.png"),
    ("longitudinal_elevation", "longitudinal_elevation.png"),
    ("girder_3d", "girder_3d.png"),
    ("girder_top", "girder_top.png"),
    ("section_preview", "section_preview.png"),
    ("stiffener_preview", "stiffener_preview.png"),
    ("cb_diagram", "cb_diagram.png"),
    ("cb_bracing", "cb_bracing.png"),
    ("cb_top_chord", "cb_top_chord.png"),
    ("cb_bottom_chord", "cb_bottom_chord.png"),
    ("ed_diagram", "ed_diagram.png"),
    ("ed_bracing", "ed_bracing.png"),
    ("ed_top_chord", "ed_top_chord.png"),
    ("ed_bottom_chord", "ed_bottom_chord.png"),
    ("bm_envelope", "bm_envelope.png"),
    ("sf_envelope", "sf_envelope.png"),
    ("defl_ll", "defl_ll.png"),
]


def generate_report(payload, request):
  # type: (ReportPayload, ReportRequest) -> ReportResult
  """Compile the full OsdagBridge Design Report to PDF (+ .tex source)."""
  tex_path = None
  try:
    pdflatex_bin = _find_pdflatex()

    os.makedirs(request.output_dir, exist_ok=True)
    assets_dir = os.path.join(request.output_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    m = payload.metadata
    inputs_dict = payload.inputs or {}
    outputs_dict = payload.output_dict or {}

    proj_name = (
        m.project_name
        or inputs_dict.get("project.name")
        or "OsdagBridge Project"
    )
    job_no = m.job_number or inputs_dict.get("job_number") or "JOB-001"
    rep_date = m.report_date or datetime.date.today().isoformat()
    rep_ver = m.subtitle or "Rev 0"

    osdag_logo_tex = None
    if m.logo_path and os.path.exists(m.logo_path):
      dst_logo = os.path.join(assets_dir, "osdag_logo.png")
      shutil.copy2(m.logo_path, dst_logo)
      osdag_logo_tex = "assets/osdag_logo.png"

    org_logo_tex = None
    fig_paths = {}
    for attr, fname in _FIGURE_MAP:
      src_path = getattr(payload.figures, attr, None)
      if src_path and os.path.exists(src_path):
        dst_fig = os.path.join(assets_dir, fname)
        shutil.copy2(src_path, dst_fig)
        fig_paths[attr] = f"assets/{fname}"

    bridge = ReportDataBridge(
        output_dict=outputs_dict,
        input_dict=inputs_dict,
        payload=payload,
    )

    parts = [
        preamble(proj_name, job_no, rep_date, rep_ver),
        title_page(m, osdag_logo_tex, org_logo_tex),
    ]

    if getattr(payload.options, "include_toc", True):
      parts.append(toc_section())

    parts.append(executive_summary(inputs_dict, outputs_dict, fig_paths))
    parts.append(add_longtable_headers(ch1_project_info(m)))
    parts.append(
        add_longtable_headers(ch2_input_parameters(m, inputs_dict, outputs_dict))
    )
    parts.append(add_longtable_headers(ch3_loads(inputs_dict)))
    asum = payload.analysis_summary or outputs_dict.get("analysis_summary") or {}
    _raw_span = (
        inputs_dict.get(KEY_SPAN)
        or inputs_dict.get("member_properties.girder_details.total_span")
        or inputs_dict.get("typical_section.girder_details.total_span")
        or 0.0
    )
    try:
      _span = float(_raw_span)
    except (TypeError, ValueError):
      _span = 0.0

    parts.append(
        add_longtable_headers(ch4_analysis(asum, fig_paths, bridge, _span))
    )
    parts.append(
        add_longtable_headers(ch5_design_checks(payload.design_checks, bridge))
    )
    parts.append(ch6_drawings(fig_paths))
    parts.append(
        add_longtable_headers(ch7_quantities(inputs_dict, outputs_dict))
    )
    parts.append(add_longtable_headers(ch8_design_log(getattr(payload, "log_entries", []), inputs_dict)))
    parts.append(references())
    parts.append(r"\end{document}")

    full_tex = "\n".join(parts)
    from osdagbridge.core.reports.report_fixes import fix_latex_source
    full_tex = fix_latex_source(full_tex)

    tex_path = os.path.join(request.output_dir, f"{request.file_stem}.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
      f.write(full_tex)

    pdf_path = os.path.join(request.output_dir, f"{request.file_stem}.pdf")
    if not pdflatex_bin:
      logger.warning(
          "pdflatex not found; wrote .tex source to %s without compiling PDF.",
          tex_path,
      )
      return ReportResult(pdf_path=None, tex_path=tex_path)

    with tempfile.TemporaryDirectory() as tmpdir:
      tmp_tex = os.path.join(tmpdir, f"{request.file_stem}.tex")
      shutil.copy2(tex_path, tmp_tex)
      tmp_assets = os.path.join(tmpdir, "assets")
      if os.path.exists(assets_dir):
        shutil.copytree(assets_dir, tmp_assets, dirs_exist_ok=True)

      for _ in range(2):
        subprocess.run(
            [
                pdflatex_bin,
                "-interaction=nonstopmode",
                "-halt-on-error",
                tmp_tex,
            ],
            cwd=tmpdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

      tmp_pdf = os.path.join(tmpdir, f"{request.file_stem}.pdf")
      if os.path.exists(tmp_pdf):
        shutil.copy2(tmp_pdf, pdf_path)
      else:
        pdf_path = None

    return ReportResult(pdf_path=pdf_path, tex_path=tex_path)

  except Exception as exc:
    logger.exception("generate_report failed: %s", exc)
    return ReportResult(pdf_path=None, tex_path=tex_path)
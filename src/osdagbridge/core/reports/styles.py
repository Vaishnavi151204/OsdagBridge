"""
styles.py - single source of truth for the OsdagBridge design report.

Fonts, colours, margins, table padding, header/footer and chart appearance
are defined ONLY here. report_generator.preamble() and the chapter files
import from this module.
"""

# ── 1. Document ──────────────────────────────────────────────────────────
DOCUMENT_CLASS_OPTIONS = "12pt,a4paper"
LINE_STRETCH = 1.15

# ── 2. Page geometry ─────────────────────────────────────────────────────
MARGIN_TOP = "1in"
MARGIN_BOTTOM = "1.1in"
MARGIN_LEFT = "1in"
MARGIN_RIGHT = "1in"
HEAD_HEIGHT = "15pt"
FOOT_SKIP = "32pt"


def geometry_options():
  return (
      f"a4paper, top={MARGIN_TOP}, bottom={MARGIN_BOTTOM}, "
      f"left={MARGIN_LEFT}, right={MARGIN_RIGHT}, "
      f"headheight={HEAD_HEIGHT}, footskip={FOOT_SKIP}"
  )


# ── 3. Colour palette (hex, no #) ────────────────────────────────────────
COLORS = {
    "osdagGreen": "91B014",
    "osdagTint": "EEF3D6",  # light green: table header background
    "rowAlt": "F7F9EE",  # zebra stripe
    "passGreen": "2E7D32",
    "failRed": "C62828",
    "steelBlue": "2B6CB0",
    "steelMid": "3182CE",
    "steelLight": "63B3ED",
    "rebarAmber": "D97706",
}


def color_definitions():
  return "\n".join(
      r"\definecolor{%s}{HTML}{%s}" % (n, h) for n, h in COLORS.items()
  )


# ── 4. Table style ───────────────────────────────────────────────────────
TABLE = {
    "tabcolsep": "6pt",  # cell padding (left/right)
    "arraystretch": "1.12",  # row height multiplier
    "extrarowheight": "0.6pt",
    "arrayrulewidth": "0.5pt",  # border thickness
    "LTpre": "0pt",
    "LTpost": "6pt",
    "needspace_lines": 5,  # start a table on a new page if fewer lines remain
}


def table_settings():
  t = TABLE
  return "\n".join([
      r"\setlength{\tabcolsep}{%s}" % t["tabcolsep"],
      r"\renewcommand{\arraystretch}{%s}" % t["arraystretch"],
      r"\setlength{\LTpre}{%s}" % t["LTpre"],
      r"\setlength{\LTpost}{%s}" % t["LTpost"],
      r"\setlength{\arrayrulewidth}{%s}" % t["arrayrulewidth"],
      r"\setlength{\extrarowheight}{%s}" % t["extrarowheight"],
  ])


# ── 5. Header / footer ───────────────────────────────────────────────────
FOOTER_LEFT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
RULE_WIDTH = "1pt"
SD_NOTE_TEXT = r"* Software default value"
SD_NOTE_RAISE = "-20pt"  # how far the note is pulled up into the body area
SD_NOTE_GAP = "4pt"
FOOT_RULE_RAISE = "-8pt"
FOOT_RULE_GAP = "6pt"


def _footrule():
  return (
      r"\renewcommand{\footrule}{%"
      "\n"
      r"    \ifbool{hasSDonPage}{%"
      "\n"
      r"      \vspace{"
      + SD_NOTE_RAISE
      + r"}%"
      "\n"
      r"      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{"
      + SD_NOTE_TEXT
      + r"}}\hfil}%"
      "\n"
      r"      \vspace{"
      + SD_NOTE_GAP
      + r"}%"
      "\n"
      r"    }{%"
      "\n"
      r"      \vspace{"
      + FOOT_RULE_RAISE
      + r"}%"
      "\n"
      r"    }%"
      "\n"
      r"    \color{osdagGreen}\hrule width\headwidth height "
      + RULE_WIDTH
      + r" \vspace{"
      + FOOT_RULE_GAP
      + r"}%"
      "\n"
      r"  }"
  )


def pagestyle(name, head_left, head_right):
  return "\n".join([
      r"\fancypagestyle{" + name + r"}{",
      r"  \fancyhf{}",
      r"  \fancyhead[L]{" + head_left + r"}",
      r"  \fancyhead[R]{" + head_right + r"}",
      r"  \fancyfoot[L]{" + FOOTER_LEFT + r"}",
      r"  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}",
      r"  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height "
      + RULE_WIDTH
      + r" \vspace{2pt}}",
      r"  " + _footrule(),
      r"}",
  ])


def firstpage_style():
  return "\n".join([
      r"\fancypagestyle{firstpage}{",
      r"  \fancyhf{}",
      r"  \renewcommand{\headrulewidth}{0pt}",
      r"  \fancyfoot[L]{" + FOOTER_LEFT + r"}",
      r"  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}",
      r"  \renewcommand{\footrule}{\vspace{"
      + FOOT_RULE_RAISE
      + r"}\color{osdagGreen}\hrule width\headwidth height "
      + RULE_WIDTH
      + r" \vspace{"
      + FOOT_RULE_GAP
      + r"}}",
      r"}",
  ])


# ── 6. LaTeX packages and helper commands ────────────────────────────────
PACKAGES = r"""\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}

\captionsetup{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\setlength{\LTleft}{\fill}
\setlength{\LTright}{\fill}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}"""

LATEX_HELPERS = r"""% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% Software-default asterisk
\newcommand{\sdstar}{\textsuperscript{*}}
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}"""


# ── 7. Chart style (single source of truth for report_charts.py) ────────
CHART = {
    "figsize": (7.5, 4.2),
    "dpi": 300,
    "font_size": 10,
    "bar_pass": "#" + COLORS["passGreen"],
    "bar_fail": "#" + COLORS["failRed"],
    "bar_neutral": "#" + COLORS["osdagGreen"],
    "bar_steel": "#" + COLORS["steelBlue"],
    "bar_steel_mid": "#" + COLORS["steelMid"],
    "bar_steel_light": "#" + COLORS["steelLight"],
    "bar_concrete": "#" + COLORS["osdagGreen"],
    "bar_rebar": "#" + COLORS["rebarAmber"],
    "threshold_color": "#" + COLORS["failRed"],
    "threshold_style": "--",
    "threshold_value": 1.0,
    "grid_style": ":",
    "grid_alpha": 0.6,
}
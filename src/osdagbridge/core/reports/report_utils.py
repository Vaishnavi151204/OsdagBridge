import re

from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS,
)


def _tex(value):
  """Escape a Python value for safe LaTeX embedding."""
  s = str(value) if value is not None else ""
  if not s:
    return r""
  # Normalise non-ASCII glyphs from section designations (e.g. "∠ 100 ⅹ 100ⅹ 10")
  # that pdflatex cannot render.
  for uni, ascii_ in [("∠", "L"), ("ⅹ", "x"), ("×", "x")]:
    s = s.replace(uni, ascii_)
  s = s.replace("\\", r"\textbackslash{}")
  for ch, esc in [
      ("&", r"\&"),
      ("%", r"\%"),
      ("$", r"\$"),
      ("#", r"\#"),
      ("{", r"\{"),
      ("}", r"\}"),
      ("_", r"\_\allowbreak{}"),
      ("~", r"\textasciitilde{}"),
      ("^", r"\^{}"),
  ]:
    s = s.replace(ch, esc)
  s = s.replace(":", r":\allowbreak{}")
  return s


def _render_value(source_dict, key, unit=""):
  val = source_dict.get(key)
  if val in ("", None):
    return ""
  return _tex(val) + unit


def get_girder_entries(input_dict):
  """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)
    
    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
        
    # 2. Get total number of girders safely
    n_girders = len(girder_entries)
    
    # 3. Iterate over the girders to build table rows
    for lbl, mid in girder_entries:
        # lbl will be e.g., "G1", mid will be e.g., "G1M1"
        # Access girder specific keys dynamically:
        # val = input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.{lbl}.{mid}")
        pass

    Returns:
        List[Tuple[str, str]]
    """
  n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))

  entries = []

  for i in range(1, n + 1):
    entries.append((
        input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", ""),
        input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", ""),
    ))

  return entries


def _fig_or_placeholder(path, caption, width=r"0.9\textwidth"):
  """Embed figure if path is provided (file already copied to assets), else show placeholder box.
    path is the relative path as pdflatex will see it (e.g. 'assets/plan.png').
    """
  if path:
    p = path.replace("\\", "/")
    return (
        r"\begin{figure}[H]"
        + "\n"
        + r"\centering"
        + "\n"
        + r"\includegraphics[width="
        + width
        + "]{"
        + p
        + "}\n"
        + r"\caption*{"
        + caption
        + "}\n"
        + r"\end{figure}"
    )
  return (
      r"\begin{figure}[H]"
      + "\n"
      + r"\centering"
      + "\n"
      + r"\fbox{\parbox{0.97\textwidth}{"
      + "\n"
      + r"\textit{[ PLACEHOLDER: "
      + caption
      + r" ]}"
      + "\n"
      + r"}}"
      + "\n"
      + r"\caption*{"
      + caption
      + "}\n"
      + r"\end{figure}"
  )


def _fig_embed(path, caption, width=r"\textwidth", height=None):
  """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
  if path:
    p = path.replace("\\", "/")
    opts = "width=" + width
    if height:
      opts += ",height=" + height + ",keepaspectratio"
    return (
        r"\begin{figure}[H]"
        + "\n"
        + r"\vspace{-0.5em}"
        + "\n"
        + r"\centering"
        + "\n"
        + r"\includegraphics["
        + opts
        + "]{"
        + p
        + "}\n"
        + r"\vspace{0.5em}"
        + "\n"
        + r"\caption*{\small "
        + caption
        + "}\n"
        + r"\vspace{-0.5em}"
        + "\n"
        + r"\end{figure}"
    )
  # fbox placeholder — matches template exactly
  return (
      r"\noindent\fbox{\parbox{0.97\textwidth}{"
      + "\n"
      + r"\textit{[ PLACEHOLDER: "
      + caption
      + r" ]}"
      + "\n"
      + r"}}"
  )


# ── Longtable fixes (Items 1 and 2) ──────────────────────────────────────
_LT_BEGIN = r"\begin{longtable}"
_LT_END = r"\end{longtable}"
_WS = re.compile(r"\s*")
_ROW_END = re.compile(r"\\\\(?:\[[^\]]*\])?")
_P_COL = re.compile(r"(p\{)([^}]+)(})")


def _match_brace(s, i):
  """s[i] must be '{'. Return the index just after its matching '}', or -1."""
  depth = 0
  j = i
  n = len(s)
  while j < n:
    c = s[j]
    if c == "\\":
      j += 2
      continue
    if c == "{":
      depth += 1
    elif c == "}":
      depth -= 1
      if depth == 0:
        return j + 1
    j += 1
  return -1


def _clamp_longtable_spec(spec, max_total_cm=15.6):
  """Scale down explicit p{...cm} column widths if their sum exceeds max_total_cm."""
  cm_matches = []
  total_cm = 0.0
  for m in _P_COL.finditer(spec):
    width_expr = m.group(2).strip()
    if width_expr.endswith("cm"):
      try:
        val = float(width_expr[:-2].strip())
        cm_matches.append((m, val))
        total_cm += val
      except ValueError:
        pass
  if not cm_matches or total_cm <= max_total_cm:
    return spec

  scale = max_total_cm / total_cm
  parts = []
  last = 0
  for m, val in cm_matches:
    parts.append(spec[last : m.start(2)])
    new_val = max(0.75, round(val * scale, 2))
    parts.append(f"{new_val:.2f}cm")
    last = m.end(2)
  parts.append(spec[last:])
  return "".join(parts)


def _patch_longtable(block):
  """Repeat the header row on every page, clamp over-wide p{...cm} columns,
    and move the closing rule into the table footer."""
  i = len(_LT_BEGIN)
  if i < len(block) and block[i] == "{":
    k = _match_brace(block, i)
    if k > 0:
      orig_spec = block[i + 1 : k - 1]
      clamped_spec = _clamp_longtable_spec(orig_spec)
      if clamped_spec != orig_spec:
        block = block[: i + 1] + clamped_spec + block[k - 1 :]

  if r"\endhead" in block or r"\endfirsthead" in block:
    return block  # chapter file already handles it
  if i >= len(block) or block[i] != "{":
    return block
  k = _match_brace(block, i)  # skip the column spec
  if k < 0:
    return block
  k = _WS.match(block, k).end()
  if block.startswith(r"\caption", k):  # keep the caption where it is
    q = k + len(r"\caption")
    if q < len(block) and block[q] == "[":
      close = block.find("]", q)
      if close < 0:
        return block
      q = close + 1
    q = _WS.match(block, q).end()
    if q >= len(block) or block[q] != "{":
      return block
    q = _match_brace(block, q)
    if q < 0:
      return block
    k = _WS.match(block, q).end()
  if not block.startswith(r"\hline", k):
    return block
  head_start = k + len(r"\hline")
  m = _ROW_END.search(block, head_start)
  if not m:
    return block
  head_row = block[head_start : m.end()].strip()
  if r"\textbf" not in head_row:  # key/value tables have no header row
    return block
  m2 = re.compile(r"\s*\\hline").match(block, m.end())
  if not m2:
    return block
  cut = m2.end()
  head = (
      block[:cut]
      + ("\n\\endfirsthead\n\\hline\n" + head_row + "\n\\hline\n\\endhead")
  )
  body = block[cut:]
  stripped = re.sub(r"\s*\\hline\s*$", "\n", body)
  if stripped != body:
    body = "\n\\hline\n\\endfoot\n\\hline\n\\endlastfoot" + stripped
  return head + body


def add_longtable_headers(tex):
  """Post-process the finished LaTeX source:
1. every longtable with a bold header row repeats it on each page;
2. \\multirow group labels (G1, G2 ...) are top-aligned so that a label can
       never be drawn below the last row of a page, over the footer."""
  out, pos = [], 0
  while True:
    b = tex.find(_LT_BEGIN, pos)
    if b < 0:
      out.append(tex[pos:])
      break
    e = tex.find(_LT_END, b)
    if e < 0:
      out.append(tex[pos:])
      break
    out.append(tex[pos:b])
    block = _patch_longtable(tex[b:e])
    out.append(re.sub(r"\\multirow\{", r"\\multirow[t]{", block))
    pos = e
  return "".join(out)
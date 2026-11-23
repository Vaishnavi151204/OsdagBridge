"""
report_fixes.py - last-step repairs applied to the finished LaTeX source.

Call once, right after the document parts are joined:

    from osdagbridge.core.reports.report_fixes import fix_latex_source
    full_tex = "\\n".join(parts)
    full_tex = fix_latex_source(full_tex)

What it repairs
1. Longtable captions: with the `caption` package loaded, every
   \\caption{...} inside a longtable must end with a row break (\\\\).
   Without it LaTeX raises "Misplaced \\noalign" for every table.
   A \\label{...} written after the caption is moved inside the caption.
2. The characters <= and >= (U+2264 / U+2265) are declared for pdfLaTeX.
3. Windows line endings (CRLF) are normalised to LF.
4. Tables wider than the text area get their fixed column widths scaled
   down so that they stay inside the page margins.
5. Figure placeholder boxes are kept inside the margins, one per line.

It is safe to run more than once.
"""
import re

_LT_BEGIN = r'\begin{longtable}'
_LT_END = r'\end{longtable}'
_LABEL = re.compile(r'\s*(\\label\{[^{}]*\})')
_ROW_BREAK = re.compile(r'\s*\\\\')
_UNICODE_DECL = (
    "\\DeclareUnicodeCharacter{2264}{\\ensuremath{\\leq}}\n"
    "\\DeclareUnicodeCharacter{2265}{\\ensuremath{\\geq}}\n"
)


def _match_brace(s, i):
    """s[i] must be '{'. Return the index just after its matching '}', or -1."""
    depth, j, n = 0, i, len(s)
    while j < n:
        c = s[j]
        if c == '\\':
            j += 2
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return -1


def _fix_caption(block):
    c = block.find(r'\caption')
    if c < 0:
        return block
    q = c + len(r'\caption')
    if q < len(block) and block[q] == '[':          # optional short title
        close = block.find(']', q)
        if close < 0:
            return block
        q = close + 1
    while q < len(block) and block[q] in ' \n\r\t':
        q += 1
    if q >= len(block) or block[q] != '{':
        return block
    end = _match_brace(block, q)
    if end < 0:
        return block
    m = _LABEL.match(block, end)                     # label after caption
    if m:
        block = block[:end - 1] + m.group(1) + '}' + block[m.end():]
        end = end - 1 + len(m.group(1)) + 1
    if not _ROW_BREAK.match(block, end):             # caption row must end
        block = block[:end] + r'\\' + block[end:]
    return block


def fix_longtable_captions(tex):
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
        out.append(_fix_caption(tex[b:e]))
        pos = e
    return ''.join(out)


# -- fit tables to the text width ---------------------------------------------
_COL_W = re.compile(r'([pLCRmb])\{\s*([0-9]*\.?[0-9]+)\s*(cm|mm|pt|in)\s*\}')
_UNIT_PT = {'cm': 28.4528, 'mm': 2.84528, 'pt': 1.0, 'in': 72.27}
_A4_WIDTH_PT = 597.5


def _to_pt(value):
    m = re.match(r'\s*([0-9]*\.?[0-9]+)\s*(cm|mm|pt|in)', value)
    return float(m.group(1)) * _UNIT_PT[m.group(2)] if m else None


def _text_width_pt(tex):
    """Text width in pt, read from the geometry options in the preamble."""
    left = right = 72.27
    g = re.search(r'\\usepackage\[([^\]]*)\]\{geometry\}', tex)
    if g:
        opts = g.group(1)
        for key in ('margin', 'left', 'right'):
            m = re.search(r'(?<![a-z])' + key + r'\s*=\s*([0-9.]+\s*(?:cm|mm|pt|in))', opts)
            if m and _to_pt(m.group(1)) is not None:
                if key in ('margin', 'left'):
                    left = _to_pt(m.group(1))
                if key in ('margin', 'right'):
                    right = _to_pt(m.group(1))
    return _A4_WIDTH_PT - left - right


def _fit_spec(spec, avail_pt, tabcolsep_pt=6.0):
    cols = list(_COL_W.finditer(spec))
    if not cols:
        return spec
    rest = _COL_W.sub('', spec)
    rest = re.sub(r'>\{[^{}]*(\{[^{}]*\}[^{}]*)*\}', '', rest)
    k = len(re.findall(r'(?<![\\a-zA-Z])[clr](?![a-zA-Z])', rest))  # plain c/l/r
    widths = [float(m.group(2)) * _UNIT_PT[m.group(3)] for m in cols]
    n = len(cols) + k
    # plain c/l/r columns are assumed to need about 30 pt each
    avail = avail_pt - n * 2 * tabcolsep_pt - (n + 1) * 0.5 - 1.0 - k * 30.0
    total = sum(widths)
    if total <= avail or avail <= 0:
        return spec
    f = avail / total
    out, last = [], 0
    for m, w in zip(cols, widths):
        out.append(spec[last:m.start()])
        out.append('%s{%.2fcm}' % (m.group(1), w * f / _UNIT_PT['cm']))
        last = m.end()
    out.append(spec[last:])
    return ''.join(out)


def fit_tables_to_width(tex):
    avail = _text_width_pt(tex)
    tc = re.search(r'\\setlength\{\\tabcolsep\}\{([0-9.]+\s*pt)\}', tex)
    tabcolsep = _to_pt(tc.group(1)) if tc else 6.0
    out, pos = [], 0
    pat = re.compile(r'\\begin\{(longtable|tabular)\}')
    while True:
        m = pat.search(tex, pos)
        if not m:
            out.append(tex[pos:])
            break
        i = j = m.end()
        while j < len(tex) and tex[j] in ' \n':
            j += 1
        if j < len(tex) and tex[j] == '[':
            j = tex.find(']', j) + 1
        e = _match_brace(tex, j) if j < len(tex) and tex[j] == '{' else -1
        if e < 0:
            out.append(tex[pos:i])
            pos = i
            continue
        out.append(tex[pos:j])
        out.append('{' + _fit_spec(tex[j + 1:e - 1], avail, tabcolsep) + '}')
        pos = e
    return ''.join(out)


# -- figure placeholders: stay inside the margins, one per line ---------------
_PLACEHOLDER = re.compile(
    r'(\\noindent\\fbox\{\\parbox\{)0\.97(\\textwidth\}\{\s*'
    r'\\textit\{\[ PLACEHOLDER:.*?\]\}\s*\}\})', re.S)


def fix_placeholders(tex):
    return _PLACEHOLDER.sub(lambda m: m.group(1) + '0.94' + m.group(2)
                            + '\n\\par\\vspace{0.6em}', tex)


def fix_latex_source(tex):
    tex = tex.replace('\r\n', '\n')
    tex = fix_longtable_captions(tex)
    tex = fit_tables_to_width(tex)
    tex = fix_placeholders(tex)
    if r'\DeclareUnicodeCharacter{2264}' not in tex:
        tex = tex.replace(r'\begin{document}',
                          _UNICODE_DECL + r'\begin{document}', 1)
    return tex

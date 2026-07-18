from pathlib import Path

_FONT_REGULAR = "/usr/share/fonts/Adwaita/AdwaitaMono-Regular.ttf"
_FONT_BOLD = "/usr/share/fonts/Adwaita/AdwaitaMono-Bold.ttf"


def generate_chord_pdf(title: str, artist: str, content: str) -> Path:
    from fpdf import FPDF

    # A4 portrait, all units in mm
    PAGE_W, PAGE_H = 210, 297
    M_LR, M_TOP, M_BOT = 15, 22, 12
    GUTTER = 5
    FONT_SIZE = 8
    # AdwaitaMono has slightly wider chars than Courier (~0.62 em)
    CHAR_W = FONT_SIZE * 0.62 * 0.352778  # ~1.746 mm per char
    LINE_H = FONT_SIZE * 1.25 * 0.352778  # ~3.528 mm per line

    content_w = PAGE_W - 2 * M_LR        # 180 mm
    content_h = PAGE_H - M_TOP - M_BOT   # 263 mm
    lines_per_col = int(content_h / LINE_H)

    lines = content.splitlines()
    max_chars = max((len(l) for l in lines), default=1)

    # Pick the highest column count where lines still fit horizontally
    n_cols = 1
    for n in [4, 3, 2]:
        col_w = (content_w - GUTTER * (n - 1)) / n
        if max_chars <= col_w / CHAR_W:
            n_cols = n
            break

    col_w = (content_w - GUTTER * (n_cols - 1)) / n_cols
    chars_per_col = int(col_w / CHAR_W)

    def _add_fonts(pdf: "FPDF") -> None:
        pdf.add_font("Mono", style="", fname=_FONT_REGULAR)
        pdf.add_font("Mono", style="B", fname=_FONT_BOLD)

    def _header(pdf: "FPDF", suffix: str = "") -> None:
        pdf.set_font("Mono", "B", 10)
        label = f"{title}  —  {artist}{suffix}"
        pdf.set_xy(M_LR, 8)
        pdf.cell(content_w, 8, label, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    _add_fonts(pdf)
    pdf.add_page()
    _header(pdf)

    pdf.set_font("Mono", size=FONT_SIZE)
    col_idx = 0
    line_in_col = 0

    for line in lines:
        if line_in_col >= lines_per_col:
            col_idx += 1
            line_in_col = 0
            if col_idx >= n_cols:
                pdf.add_page()
                _header(pdf, " (cont.)")
                pdf.set_font("Mono", size=FONT_SIZE)
                col_idx = 0

        x = M_LR + col_idx * (col_w + GUTTER)
        y = M_TOP + line_in_col * LINE_H
        pdf.set_xy(x, y)
        pdf.cell(col_w, LINE_H, line[:chars_per_col])
        line_in_col += 1

    safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()
    safe_artist = "".join(c for c in artist if c not in r'\/:*?"<>|').strip()
    output = Path.home() / "Downloads" / f"{safe_artist} - {safe_title}.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output))
    return output

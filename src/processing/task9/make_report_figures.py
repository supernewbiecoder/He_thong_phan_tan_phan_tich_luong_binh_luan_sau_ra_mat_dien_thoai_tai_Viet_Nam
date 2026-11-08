"""Create lightweight SVG figures for the Task 9 report (standard library only)."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_METRICS = ROOT / "data/task9/model/metrics.json"
DEFAULT_OUT = ROOT / "docs/reports/task9/figures"
LABELS = ["pos", "neg", "neu"]
ASPECT_LABELS = {
    "BATTERY": "Pin & sạc",
    "DISPLAY": "Màn hình",
    "PERFORMANCE": "Hiệu năng",
    "CAMERA": "Camera",
    "DESIGN": "Thiết kế",
    "SOFTWARE": "Phần mềm",
    "HARDWARE_OTHER": "Phần cứng khác",
    "PRICE": "Giá",
    "WARRANTY": "Bảo hành",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_start(width: int, height: int, title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,"DejaVu Sans",sans-serif;fill:#243044}.title{font-size:22px;font-weight:700}.sub{font-size:13px;fill:#667085}.label{font-size:13px}.small{font-size:11px;fill:#667085}.value{font-size:13px;font-weight:700}</style>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="32" y="38" class="title">{esc(title)}</text>',
        f'<text x="32" y="62" class="sub">{esc(subtitle)}</text>',
    ]


def save_svg(parts: list[str], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts + ["</svg>"]), encoding="utf-8")
    return path


def confusion_matrix(metrics: dict, out: Path) -> Path:
    cm = metrics["confusion_matrix_pos_neg_neu"]
    cell, x0, y0 = 100, 190, 115
    width, height = 620, 465
    parts = svg_start(width, height, "Ma trận nhầm lẫn trên validation", "Hàng: nhãn LLM · Cột: dự đoán mô hình · số lượng mẫu")
    for j, label in enumerate(LABELS):
        parts.append(f'<text x="{x0 + j * cell + cell / 2}" y="{y0 - 12}" text-anchor="middle" class="label">Đoán {label}</text>')
    for i, label in enumerate(LABELS):
        parts.append(f'<text x="{x0 - 18}" y="{y0 + i * cell + cell / 2 + 5}" text-anchor="end" class="label">Thật {label}</text>')
        for j, _ in enumerate(LABELS):
            value = cm[i][j]
            intensity = int(234 - 155 * value / max(max(row) for row in cm))
            fill = f"rgb({intensity - 25},{intensity - 5},255)" if i == j else f"rgb({intensity},{intensity + 4},{intensity + 8})"
            parts.append(f'<rect x="{x0 + j * cell}" y="{y0 + i * cell}" width="{cell}" height="{cell}" rx="5" fill="{fill}" stroke="#ffffff" stroke-width="3"/>')
            parts.append(f'<text x="{x0 + j * cell + cell / 2}" y="{y0 + i * cell + cell / 2 + 6}" text-anchor="middle" class="value">{value}</text>')
    parts.append(f'<text x="{x0 + 150}" y="{y0 + 3 * cell + 33}" text-anchor="middle" class="small">Macro-F1 validation: {metrics["val_macro_f1"]:.3f} (đối chiếu nhãn LLM)</text>')
    return save_svg(parts, out / "confusion_matrix.svg")


def aspect_scores(metrics: dict, out: Path) -> Path:
    data = sorted(metrics["per_aspect"].items(), key=lambda item: item[1]["macro_f1"])
    width, height = 760, 470
    left, top, row_h, bar_w = 185, 105, 34, 420
    parts = svg_start(width, height, "Macro-F1 validation theo khía cạnh", "Validation gồm nhãn LLM; số bên phải là số cặp, không phải khoảng tin cậy")
    for tick in range(0, 11, 2):
        x = left + bar_w * tick / 10
        parts.append(f'<line x1="{x}" y1="{top - 8}" x2="{x}" y2="{top + len(data) * row_h}" stroke="#e7eaf0"/>')
        parts.append(f'<text x="{x}" y="{top + len(data) * row_h + 20}" text-anchor="middle" class="small">{tick / 10:.1f}</text>')
    for i, (aspect, values) in enumerate(data):
        y = top + i * row_h
        score = values["macro_f1"]
        color = "#d97706" if score < 0.60 else "#3274a1"
        parts.append(f'<text x="{left - 12}" y="{y + 17}" text-anchor="end" class="label">{esc(ASPECT_LABELS.get(aspect, aspect))}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_w * score:.1f}" height="22" rx="4" fill="{color}"/>')
        parts.append(f'<text x="{left + bar_w + 10}" y="{y + 16}" class="small">{score:.2f} · n={values["n"]}</text>')
    return save_svg(parts, out / "aspect_macro_f1.svg")


def class_distribution(metrics: dict, out: Path) -> Path:
    width, height = 720, 360
    x0, y0, chart_h = 115, 115, 170
    train, val = metrics["train_dist"], metrics["val_dist"]
    maximum = max(max(train.values()), max(val.values()))
    parts = svg_start(width, height, "Phân bố nhãn trong train và validation", "Số mẫu theo lớp; cả hai tập được gán nhãn LLM")
    colors = {"pos": "#2f855a", "neg": "#c2413b", "neu": "#64748b"}
    for tick in range(0, maximum + 1, 300):
        y = y0 + chart_h - chart_h * tick / maximum
        parts.append(f'<line x1="{x0}" y1="{y}" x2="650" y2="{y}" stroke="#e7eaf0"/>')
        parts.append(f'<text x="{x0 - 10}" y="{y + 4}" text-anchor="end" class="small">{tick}</text>')
    for i, label in enumerate(LABELS):
        x = x0 + 70 + i * 155
        for offset, data, color in [(0, train, colors[label]), (42, val, "#aab4c3")]:
            count = data[label]
            h = chart_h * count / maximum
            parts.append(f'<rect x="{x + offset}" y="{y0 + chart_h - h}" width="34" height="{h}" rx="3" fill="{color}"/>')
            parts.append(f'<text x="{x + offset + 17}" y="{y0 + chart_h - h - 6}" text-anchor="middle" class="small">{count}</text>')
        parts.append(f'<text x="{x + 38}" y="{y0 + chart_h + 22}" text-anchor="middle" class="label">{label}</text>')
    parts.extend(['<rect x="250" y="326" width="12" height="12" fill="#2f855a"/><text x="268" y="337" class="small">train</text>', '<rect x="340" y="326" width="12" height="12" fill="#aab4c3"/><text x="358" y="337" class="small">validation</text>'])
    return save_svg(parts, out / "class_distribution.svg")


def learning_curve(metrics: dict, out: Path) -> Path:
    values = metrics["learning_curve"]
    points = [(int(key.rstrip("%")), value["val_macro_f1"]) for key, value in values.items()]
    width, height = 720, 390
    x0, y0, chart_w, chart_h = 105, 105, 535, 210
    lo, hi = 0.50, 0.70
    parts = svg_start(width, height, "Learning curve", "Macro-F1 validation theo lượng video dùng để train · nhãn tham chiếu là LLM")
    for tick in [0.50, 0.55, 0.60, 0.65, 0.70]:
        y = y0 + chart_h - (tick - lo) / (hi - lo) * chart_h
        parts.append(f'<line x1="{x0}" y1="{y}" x2="{x0 + chart_w}" y2="{y}" stroke="#e7eaf0"/>')
        parts.append(f'<text x="{x0 - 12}" y="{y + 4}" text-anchor="end" class="small">{tick:.2f}</text>')
    coords = []
    for pct, score in points:
        x = x0 + chart_w * pct / 100
        y = y0 + chart_h - (score - lo) / (hi - lo) * chart_h
        coords.append((x, y, pct, score))
    parts.append('<polyline fill="none" stroke="#3274a1" stroke-width="3" points="' + " ".join(f"{x},{y}" for x, y, _, _ in coords) + '"/>')
    for x, y, pct, score in coords:
        parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#3274a1"/>')
        parts.append(f'<text x="{x}" y="{y - 12}" text-anchor="middle" class="small">{score:.3f}</text>')
        parts.append(f'<text x="{x}" y="{y0 + chart_h + 22}" text-anchor="middle" class="small">{pct}%</text>')
    parts.append(f'<text x="{x0 + chart_w / 2}" y="{y0 + chart_h + 50}" text-anchor="middle" class="label">Tỷ lệ video train</text>')
    return save_svg(parts, out / "learning_curve.svg")


def make_figures(metrics_path: Path = DEFAULT_METRICS, out_dir: Path = DEFAULT_OUT) -> list[Path]:
    metrics = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
    return [
        confusion_matrix(metrics, Path(out_dir)),
        aspect_scores(metrics, Path(out_dir)),
        class_distribution(metrics, Path(out_dir)),
        learning_curve(metrics, Path(out_dir)),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    for path in make_figures(args.metrics, args.outdir):
        print(path)


if __name__ == "__main__":
    main()

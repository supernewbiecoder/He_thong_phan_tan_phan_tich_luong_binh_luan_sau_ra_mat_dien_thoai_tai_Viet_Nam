"""Prepare span-level ABSA data and a small FEATURES review UI."""

from __future__ import annotations

import argparse
import csv
import html
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


SPLITS = ("train", "dev", "test")
SENTIMENTS = {"POSITIVE": "pos", "NEGATIVE": "neg", "NEUTRAL": "neu"}
ASPECTS = {
    "BATTERY": ("BATTERY", "exact"),
    "CAMERA": ("CAMERA", "exact"),
    "SCREEN": ("DISPLAY", "exact"),
    "PERFORMANCE": ("PERFORMANCE", "exact"),
    "DESIGN": ("DESIGN", "exact"),
    "PRICE": ("PRICE", "exact"),
    "STORAGE": ("HARDWARE_OTHER", "approximate"),
    "SER&ACC": ("WARRANTY", "approximate"),
    "FEATURES": (None, "needs_review"),
    "GENERAL": (None, "unmapped"),
    "OTHERS": (None, "unmapped"),
}
VISFD_FILES = {"train": "Train.csv", "dev": "Dev.csv", "test": "Test.csv"}


def _parse_tag(tag: str) -> tuple[str, str | None]:
    parts = tag.split("#")
    if len(parts) == 1 and parts[0] == "OTHERS":
        return "OTHERS", None
    if len(parts) != 2:
        raise ValueError(f"Malformed source label: {tag!r}")
    aspect, raw_sentiment = parts
    if aspect not in ASPECTS:
        raise ValueError(f"Unknown source aspect: {aspect}")
    try:
        sentiment = SENTIMENTS[raw_sentiment.upper()]
    except KeyError as exc:
        raise ValueError(f"Unknown source sentiment: {raw_sentiment}") from exc
    return aspect, sentiment


def normalize_visd4sa_row(row: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    text = row["text"]
    labels: list[list[Any]] = []
    review_examples: list[dict[str, Any]] = []
    invalid_offsets: list[dict[str, Any]] = []
    for label_index, raw_label in enumerate(row["labels"]):
        if not isinstance(raw_label, list) or len(raw_label) != 3:
            raise ValueError(f"Malformed span label at index {label_index}")
        start, end, tag = raw_label
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
        ):
            raise ValueError(f"Non-integer span offsets at index {label_index}")
        if not isinstance(tag, str):
            raise ValueError(f"Non-string span tag at index {label_index}")
        source_aspect, sentiment = _parse_tag(tag)
        if source_aspect == "FEATURES":
            review_examples.append(
                {
                    "source_dataset": "UIT-ViSD4SA",
                    "source_aspect": source_aspect,
                    "source_sentiment": sentiment,
                    "start": start,
                    "end": end,
                    "span_text": text[start:end] if 0 <= start < end <= len(text) else None,
                    "text": text,
                }
            )
        if not 0 <= start < end <= len(text):
            invalid_offsets.append(
                {"source_aspect": source_aspect, "start": start, "end": end}
            )
            continue
        aspect, _ = ASPECTS[source_aspect]
        if aspect is not None and sentiment is not None:
            labels.append([start, end, f"{aspect}#{sentiment}"])
    return {"text": text, "labels": labels}, review_examples + [
        {"_invalid_offset": item} for item in invalid_offsets
    ]


def _visfd_features(row: dict[str, str], split: str) -> list[dict[str, Any]]:
    examples = []
    for token in row["label"].strip().split(";"):
        token = token.strip()
        if not token:
            continue
        if not token.startswith("{") or not token.endswith("}"):
            raise ValueError(f"Malformed UIT-ViSFD label for row {row['index']}: {token!r}")
        aspect, sentiment = _parse_tag(token[1:-1])
        if aspect == "FEATURES":
            examples.append(
                {
                    "source_dataset": "UIT-ViSFD",
                    "source_split": split,
                    "source_record_id": row["index"],
                    "source_aspect": aspect,
                    "source_sentiment": sentiment,
                    "span_text": None,
                    "text": row["comment"],
                }
            )
    return examples


def _review_html(examples: list[dict[str, Any]]) -> str:
    payload = json.dumps(examples, ensure_ascii=False)
    for char, escaped in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026")):
        payload = payload.replace(char, escaped)
    payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    title = html.escape("Duyệt nhãn FEATURES")
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ font: 16px/1.5 system-ui, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; color: #202124; }}
header {{ position: sticky; top: 0; background: white; padding: 1rem 0; border-bottom: 1px solid #ddd; }}
.card {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
.meta {{ color: #555; font-size: .9rem; }}
.text {{ white-space: pre-wrap; background: #f6f8fa; padding: .8rem; border-radius: 5px; }}
.span {{ font-weight: 700; color: #7a2ca0; }}
button {{ margin: .25rem .4rem .25rem 0; padding: .5rem .75rem; cursor: pointer; }}
button.selected {{ background: #1769aa; color: white; }}
#status {{ margin-left: 1rem; }}
</style>
</head>
<body>
<header>
<h1>Duyệt nhãn FEATURES</h1>
<p>Xem mẫu từ cả hai nguồn. Chọn ý nghĩa phù hợp nhất; lựa chọn được giữ trong trang hiện tại.
Khi xong, xuất JSON kết quả và gửi lại để chốt quy tắc ánh xạ.</p>
<button id="export">Tải kết quả JSON</button><span id="status"></span>
<p>Nếu trình duyệt không tải file, sao chép JSON trong ô bên dưới.</p>
<textarea id="export-output" hidden readonly rows="12" style="width:100%"></textarea>
</header>
<main id="examples"></main>
<script>
const examples = {payload};
const decisions = new Map();
const choices = [
  ["HARDWARE_OTHER", "Phần cứng khác"],
  ["SOFTWARE", "Phần mềm"],
  ["SPLIT", "Tùy ngữ cảnh / cần tách"],
  ["OTHER", "Khác / không rõ"],
];
const root = document.getElementById("examples");
examples.forEach((item, index) => {{
  const card = document.createElement("section");
  card.className = "card";
  const heading = document.createElement("h2");
  heading.textContent = `Mẫu ${{index + 1}}`;
  card.appendChild(heading);
  const meta = document.createElement("p");
  meta.className = "meta";
  meta.textContent = `${{item.source_dataset}} ${{item.source_split || ""}} · nhãn cảm xúc nguồn: ${{item.source_sentiment || "không có"}}`;
  card.appendChild(meta);
  if (item.span_text !== null) {{
    const span = document.createElement("p");
    span.className = "span";
    span.textContent = `Span FEATURES: “${{item.span_text}}”`;
    card.appendChild(span);
  }}
  const text = document.createElement("p");
  text.className = "text";
  text.textContent = item.text;
  card.appendChild(text);
  const controls = document.createElement("div");
  choices.forEach(([value, label]) => {{
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", () => {{
      decisions.set(index, value);
      controls.querySelectorAll("button").forEach(candidate => candidate.classList.remove("selected"));
      button.classList.add("selected");
      document.getElementById("status").textContent =
        `${{decisions.size}} / ${{examples.length}} mẫu đã xem`;
    }});
    controls.appendChild(button);
  }});
  card.appendChild(controls);
  root.appendChild(card);
}});
document.getElementById("status").textContent = `0 / ${{examples.length}} mẫu đã xem`;
document.getElementById("export").addEventListener("click", () => {{
  const result = examples.map((item, index) => ({{...item, decision: decisions.get(index) || null}}));
  const json = JSON.stringify(result, null, 2);
  const output = document.getElementById("export-output");
  output.hidden = false;
  output.value = json;
  const blob = new Blob([json], {{type: "application/json"}});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "features-review.json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}});
</script>
</body>
</html>
"""


def _audit_output(path: Path) -> dict[str, Any]:
    records = 0
    labels: Counter[str] = Counter()
    sentiments: Counter[str] = Counter()
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            record = json.loads(line)
            if set(record) != {"text", "labels"}:
                raise ValueError(f"Unexpected output fields in {path}:{line_number}")
            if not isinstance(record["text"], str) or not isinstance(record["labels"], list):
                raise ValueError(f"Invalid record shape in {path}:{line_number}")
            records += 1
            for label in record["labels"]:
                if (
                    not isinstance(label, list)
                    or len(label) != 3
                    or not isinstance(label[0], int)
                    or not isinstance(label[1], int)
                    or not 0 <= label[0] < label[1] <= len(record["text"])
                ):
                    raise ValueError(f"Invalid output span in {path}:{line_number}")
                if record["text"][label[0] : label[1]] == "":
                    raise ValueError(f"Empty output span in {path}:{line_number}")
                aspect, separator, sentiment = label[2].partition("#")
                if not separator:
                    raise ValueError(f"Invalid output tag in {path}:{line_number}")
                labels[aspect] += 1
                sentiments[sentiment] += 1
    return {
        "records": records,
        "labels": dict(sorted(labels.items())),
        "sentiments": dict(sorted(sentiments.items())),
    }


def normalize_datasets(visfd_dir: Path, visd4sa_dir: Path, output_dir: Path) -> dict[str, Any]:
    output_dataset = output_dir / "uit_visd4sa"
    output_dataset.mkdir(parents=True, exist_ok=True)
    feature_examples: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "output_format": {"text": "string", "labels": "[start, end, aspect#sentiment]"},
        "mapping_status": {
            "exact": ["BATTERY", "CAMERA", "SCREEN -> DISPLAY", "PERFORMANCE", "DESIGN", "PRICE"],
            "accepted_approximate": ["SER&ACC -> WARRANTY", "STORAGE -> HARDWARE_OTHER"],
            "needs_review": ["FEATURES"],
            "excluded_without_mapping": ["GENERAL"],
            "excluded_without_sentiment": ["OTHERS"],
        },
        "datasets": {"uit_visd4sa": {}},
    }
    invalid_offset_examples: list[dict[str, Any]] = []
    invalid_offset_count = 0
    source_aspects: Counter[str] = Counter()
    unmapped_aspects: Counter[str] = Counter()
    approximate_aspects: Counter[str] = Counter()
    for split in SPLITS:
        input_path = visd4sa_dir / "data" / f"{split}.jsonl"
        output_path = output_dataset / f"{split}.jsonl"
        with input_path.open(encoding="utf-8-sig") as source_file, output_path.open(
            "w", encoding="utf-8", newline="\n"
        ) as out:
            for record_index, line in enumerate(source_file):
                if not line.strip():
                    continue
                source_record = json.loads(line)
                normalized, auxiliary = normalize_visd4sa_row(source_record)
                for item in auxiliary:
                    if "_invalid_offset" in item:
                        invalid_offset_count += 1
                        if len(invalid_offset_examples) < 20:
                            invalid_offset_examples.append(
                                {
                                    "split": split,
                                    "record_index": record_index,
                                    **item["_invalid_offset"],
                                }
                            )
                    else:
                        item["source_split"] = split
                        item["source_record_id"] = str(record_index)
                        feature_examples.append(item)
                for _, _, tag in source_record["labels"]:
                    source_aspect, _ = _parse_tag(tag)
                    source_aspects[source_aspect] += 1
                    aspect, status = ASPECTS[source_aspect]
                    if aspect is None:
                        unmapped_aspects[source_aspect] += 1
                    elif status == "approximate":
                        approximate_aspects[source_aspect] += 1
                out.write(json.dumps(normalized, ensure_ascii=False) + "\n")
        report["datasets"]["uit_visd4sa"][split] = _audit_output(output_path)

    visfd_feature_examples: list[dict[str, Any]] = []
    for split, filename in VISFD_FILES.items():
        with (visfd_dir / filename).open(encoding="utf-8-sig", newline="") as source_file:
            for row in csv.DictReader(source_file):
                visfd_feature_examples.extend(_visfd_features(row, split))
    sample_rng = random.Random(20261109)
    sample_size = 25
    review_sample = []
    for group in (visfd_feature_examples, feature_examples):
        review_sample.extend(sample_rng.sample(group, min(sample_size, len(group))))
    review_path = output_dir / "features_review.html"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(_review_html(review_sample), encoding="utf-8")

    report["source_label_counts"] = dict(sorted(source_aspects.items()))
    report["unmapped_source_label_counts"] = dict(sorted(unmapped_aspects.items()))
    report["accepted_approximate_label_counts"] = dict(sorted(approximate_aspects.items()))
    report["invalid_span_offsets"] = {
        "count": invalid_offset_count,
        "examples": invalid_offset_examples,
    }
    report["features_review"] = {
        "sample_size": len(review_sample),
        "uit_visfd_candidates": len(visfd_feature_examples),
        "uit_visd4sa_candidates": len(feature_examples),
        "html_file": review_path.name,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visfd-dir", type=Path, default=repo_root.parent / "UIT-ViSFD")
    parser.add_argument("--visd4sa-dir", type=Path, default=repo_root.parent / "UIT-ViSD4SA")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "data" / "external" / "normalized",
    )
    args = parser.parse_args()
    report = normalize_datasets(args.visfd_dir, args.visd4sa_dir, args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

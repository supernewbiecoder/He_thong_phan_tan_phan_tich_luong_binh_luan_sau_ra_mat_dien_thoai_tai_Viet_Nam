import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
# Import bộ luật Baseline từ file aspect_baseline.py cùng thư mục
from aspect_baseline import ASPECT_LABELS, RuleBasedAspectBaseline
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import LinearSVC


# =====================================================================
# 1. HÀM TỰ ĐỘNG TÌM FILE & ĐỌC DỮ LIỆU ĐA NHÃN
# =====================================================================
def find_file_in_repo(rel_path: str) -> Optional[Path]:
  """Tự động tìm file từ thư mục hiện tại đi ngược lên gốc repo."""
  if not rel_path:
    return None
  p = Path(rel_path)
  if p.exists():
    return p.resolve()
  for base in [Path.cwd(), *Path.cwd().parents]:
    candidate = base / rel_path
    if candidate.exists():
      return candidate.resolve()
  return None


def load_clause_dataset(jsonl_path: Path) -> Tuple[List[str], List[List[str]]]:
  """Đọc file .jsonl và tự động nhận diện cả 3 định dạng:

  1. Định dạng Span ABSA (train/dev/test.jsonl của UIT-ViSD4SA): {"text": "...",
  "labels": [[start, end, "BATTERY#pos"], ...]}
  2. Định dạng aspect-mention.schema.json: {"clause_text": "...", "aspect":
  "BATTERY"}
  3. Định dạng mảng aspects: {"clause_text": "...", "aspects": ["BATTERY",
  "CAMERA"]}
  """
  clause_to_aspects = defaultdict(set)
  clause_texts_ordered = []
  seen_keys = set()

  with jsonl_path.open("r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
      if not line.strip():
        continue
      record = json.loads(line)

      text = (record.get("clause_text") or record.get("text") or "").strip()
      if not text:
        continue

      cid = record.get("comment_id", "")
      cidx = record.get("clause_idx", "")
      key = (
          f"{cid}#{cidx}" if (cid != "" and cidx != "") else f"row_{idx}_{text}"
      )

      if key not in seen_keys:
        seen_keys.add(key)
        clause_texts_ordered.append((key, text))

      # Format 1: Cột "labels": [[start, end, "ASPECT#sentiment"], ...]
      if "labels" in record and isinstance(record["labels"], list):
        for item in record["labels"]:
          if isinstance(item, list) and len(item) >= 3:
            raw_label = str(item[2])
            aspect_name = raw_label.split("#")[0].strip().upper()
            if aspect_name in ASPECT_LABELS:
              clause_to_aspects[key].add(aspect_name)

      # Format 2: Mảng "aspects": ["BATTERY", "CAMERA"]
      elif "aspects" in record and isinstance(record["aspects"], list):
        for asp in record["aspects"]:
          asp_upper = str(asp).split("#")[0].strip().upper()
          if asp_upper in ASPECT_LABELS:
            clause_to_aspects[key].add(asp_upper)

      # Format 3: Theo aspect-mention.schema.json (mỗi dòng 1 trường 'aspect')
      elif "aspect" in record and record["aspect"]:
        asp_upper = str(record["aspect"]).split("#")[0].strip().upper()
        if asp_upper in ASPECT_LABELS:
          clause_to_aspects[key].add(asp_upper)

  texts = [text for _, text in clause_texts_ordered]
  labels = [
      sorted(list(clause_to_aspects[key])) for key, _ in clause_texts_ordered
  ]
  return texts, labels


def create_mock_data() -> (
    Tuple[List[str], List[List[str]], List[str], List[List[str]]]
):
  """Tạo dữ liệu giả lập khi chưa có file thật."""
  train_data = [
      ("pin con nay trau that su dung ca ngay khong het", ["BATTERY"]),
      ("sac nhanh 120w cam 20 phut day pin luon", ["BATTERY"]),
      ("man hinh 120hz vuot muot nhung hoi am vang", ["DISPLAY", "PERFORMANCE"]),
      ("tam nen oled hien thi ruc ro ra nang nhin ro", ["DISPLAY"]),
      ("choi genshin max setting khong he giat lag", ["PERFORMANCE"]),
      ("chip snapdragon 8 gen 3 nam nay toi uu ngon", ["PERFORMANCE"]),
      ("chup dem xoa phong mu mit cam tele zoom xa net", ["CAMERA"]),
      ("quay video 4k chong rung tot", ["CAMERA"]),
      ("khung titan cam nhe tay ma vien dep", ["DESIGN"]),
      ("mat lung kinh nham khong bam van tay", ["DESIGN"]),
      ("len ios 18 hay bi vang app va loi thong bao", ["SOFTWARE"]),
      ("one ui 6 cap nhat nhieu tinh nang ai hay", ["SOFTWARE"]),
      (
          "may choi game 15 phut la nong ran len",
          ["HARDWARE_OTHER", "PERFORMANCE"],
      ),
      ("loa kep nghe to ro nhung song 4g hoi yeu", ["HARDWARE_OTHER"]),
      ("muc gia 25 trieu qua chat so voi cau hinh", ["PRICE", "PERFORMANCE"]),
      ("giam gia con 15tr thi qua dang tien", ["PRICE"]),
      ("mua chinh hang vna tai tgdd bao hanh yen tam", ["WARRANTY"]),
      ("hang xach tay re nhung kho bao hanh", ["PRICE", "WARRANTY"]),
      ("chuc anh reviewer nhieu suc khoe", []),
      ("ai xem video nam 2026 diem danh", []),
  ] * 5

  test_data = [
      ("pin tut nhanh nhu tut quan sac cung cham", ["BATTERY"]),
      ("man oled 120hz dep nhung gia hoi cao", ["DISPLAY", "PRICE"]),
      ("cam chup anh selfie dep ma quay phim hoi rung", ["CAMERA"]),
      (
          "chip exynos nong may va choi game bi tut fps",
          ["PERFORMANCE", "HARDWARE_OTHER"],
      ),
      ("thiet ke vien titan sang chanh", ["DESIGN"]),
      ("cap nhat phan mem xong muot han", ["SOFTWARE", "PERFORMANCE"]),
      ("ra cellphones mua chinh hang cho yen tam bao hanh", ["WARRANTY"]),
      ("hello anh em nha", []),
  ]
  return (
      [x for x, _ in train_data],
      [y for _, y in train_data],
      [x for x, _ in test_data],
      [y for _, y in test_data],
  )


# =====================================================================
# 2. CLASS MÔ HÌNH HỌC MÁY ĐA NHÃN & TỐI ƯU NGƯỠNG TRÊN TẬP DEV
# =====================================================================
class AspectMLClassifier:

  def __init__(
      self,
      model_type: str = "logreg",
      model_version: str = "aspect-lr-v1",
      threshold: float = 0.45,
  ):
    self.model_type = model_type
    self.model_version = model_version
    self.threshold = threshold
    # Hỗ trợ lưu ngưỡng tối ưu riêng cho từng khía cạnh (9 khía cạnh) từ tập Dev
    self.class_thresholds: Optional[np.ndarray] = None
    self.mlb = MultiLabelBinarizer(classes=ASPECT_LABELS)
    self.vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), max_features=30000, sublinear_tf=True
    )

    if model_type == "logreg":
      base_clf = LogisticRegression(
          C=2.0, max_iter=1000, class_weight="balanced", random_state=42
      )
      self.clf = OneVsRestClassifier(base_clf)
    elif model_type == "svm":
      base_svm = LinearSVC(C=1.0, class_weight="balanced", random_state=42)
      self.clf = OneVsRestClassifier(CalibratedClassifierCV(base_svm, cv=3))
    else:
      raise ValueError("model_type chỉ nhận 'logreg' hoặc 'svm'")

  def fit(self, clause_texts: List[str], aspect_lists: List[List[str]]):
    Y = self.mlb.fit_transform(aspect_lists)
    X = self.vectorizer.fit_transform(clause_texts)
    self.clf.fit(X, Y)
    return self

  def tune_thresholds_on_dev(
      self, dev_texts: List[str], dev_aspect_lists: List[List[str]]
  ) -> float:
    """Dùng tập dev.jsonl để tìm ngưỡng xác suất (threshold) tối ưu cho từng khía cạnh."""
    Y_dev = self.mlb.transform(dev_aspect_lists)
    X_dev = self.vectorizer.transform(dev_texts)
    probs = self.clf.predict_proba(X_dev)

    best_thresholds = np.full(len(ASPECT_LABELS), self.threshold)
    candidate_grid = np.arange(0.20, 0.75, 0.05)

    for idx in range(len(ASPECT_LABELS)):
      y_true_col = Y_dev[:, idx]
      if y_true_col.sum() == 0:
        continue
      best_f1_col = -1.0
      best_th_col = self.threshold
      for th in candidate_grid:
        y_pred_col = (probs[:, idx] >= th).astype(int)
        score = f1_score(y_true_col, y_pred_col, zero_division=0)
        if score > best_f1_col:
          best_f1_col = score
          best_th_col = float(round(th, 2))
      best_thresholds[idx] = best_th_col

    self.class_thresholds = best_thresholds
    Y_dev_pred = (probs >= self.class_thresholds).astype(int)
    dev_macro_f1 = float(
        f1_score(Y_dev, Y_dev_pred, average="macro", zero_division=0)
    )
    return round(dev_macro_f1, 4)

  def predict_binary(self, clause_texts: List[str]) -> np.ndarray:
    X = self.vectorizer.transform(clause_texts)
    probs = self.clf.predict_proba(X)
    if self.class_thresholds is not None:
      return (probs >= self.class_thresholds).astype(int)
    return (probs >= self.threshold).astype(int)

  def predict_mentions(self, clause_text: str) -> List[Dict]:
    """Hàm chuẩn tích hợp vào Pipeline nhóm (khớp contracts/aspect-mention.schema.json)."""
    X = self.vectorizer.transform([clause_text])
    probs = self.clf.predict_proba(X)[0]
    thresholds = (
        self.class_thresholds
        if self.class_thresholds is not None
        else [self.threshold] * len(ASPECT_LABELS)
    )

    results = []
    for aspect, prob, th in zip(ASPECT_LABELS, probs, thresholds):
      if prob >= th:
        results.append({
            "aspect": aspect,
            "confidence": round(float(prob), 4),
            "label_source": "model",
            "model_version": self.model_version,
        })
    return results


# =====================================================================
# 3. HÀM CHẤM ĐIỂM VÀ XUẤT BẢNG SO SÁNH F1 TỪNG KHÍA CẠNH
# =====================================================================
def evaluate_predictions(
    y_true_bin: np.ndarray, y_pred_bin: np.ndarray
) -> Dict[str, float]:
  """Tính F1 cho từng khía cạnh trong 9 khía cạnh + Macro-F1 + Micro-F1."""
  _, _, f1, _ = precision_recall_fscore_support(
      y_true_bin, y_pred_bin, average=None, zero_division=0
  )
  metrics = {
      aspect: round(float(score), 4) for aspect, score in zip(ASPECT_LABELS, f1)
  }
  metrics["MACRO_F1"] = round(
      float(f1_score(y_true_bin, y_pred_bin, average="macro", zero_division=0)),
      4,
  )
  metrics["MICRO_F1"] = round(
      float(f1_score(y_true_bin, y_pred_bin, average="micro", zero_division=0)),
      4,
  )
  return metrics


def dataframe_to_markdown_safe(df: pd.DataFrame) -> str:
  """Xuất DataFrame sang bảng Markdown an toàn."""
  try:
    return df.to_markdown()
  except ImportError:
    cols = ["Aspect / Metric"] + list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = [header, sep]
    for idx, row in df.iterrows():
      vals = [str(idx)] + [f"{val:.4f}" for val in row.values]
      rows.append("| " + " | ".join(vals) + " |")
    return "\n".join(rows)


def main():
  parser = argparse.ArgumentParser(
      description="Huấn luyện và đánh giá mô hình phân loại 9 khía cạnh (STT 8)"
  )
  parser.add_argument(
      "--train_file",
      type=str,
      default="data/uit_visd4sa/train.jsonl",
      help="Đường dẫn file train.jsonl",
  )
  parser.add_argument(
      "--dev_file",
      type=str,
      default="data/uit_visd4sa/dev.jsonl",
      help="Đường dẫn file dev.jsonl",
  )
  parser.add_argument(
      "--test_file",
      type=str,
      default="data/uit_visd4sa/test.jsonl",
      help="Đường dẫn file test.jsonl",
  )
  parser.add_argument(
      "--output_dir",
      type=str,
      default="artifacts/aspect_models",
      help="Thư mục lưu model và bảng điểm",
  )
  args = parser.parse_args()

  out_dir = Path(args.output_dir)
  out_dir.mkdir(parents=True, exist_ok=True)

  train_path = find_file_in_repo(args.train_file)
  dev_path = find_file_in_repo(args.dev_file)
  test_path = find_file_in_repo(args.test_file)

  X_dev, y_dev = [], []

  # 1. Nạp dữ liệu
  if train_path and train_path.exists():
    X_train, y_train = load_clause_dataset(train_path)
    if dev_path and dev_path.exists():
      X_dev, y_dev = load_clause_dataset(dev_path)

    if test_path and test_path.exists():
      X_test, y_test = load_clause_dataset(test_path)
      print("[*] Đã nạp bộ dữ liệu thật:")
      print(f"    - Train: {train_path} ({len(X_train):,} mẫu)")
      if X_dev:
        print(f"    - Dev:   {dev_path} ({len(X_dev):,} mẫu)")
      print(f"    - Test:  {test_path} ({len(X_test):,} mẫu)")
    else:
      print(
          f"[*] Chỉ tìm thấy {train_path}. Tự động tách 20% làm Test..."
      )
      X_train, X_test, y_train, y_test = train_test_split(
          X_train, y_train, test_size=0.2, random_state=42
      )
  else:
    print(
        "[!] Chưa tìm thấy file trong data/uit_visd4sa/. Đang chạy bằng Mock"
        " Data để kiểm tra code..."
    )
    X_train, y_train, X_test, y_test = create_mock_data()

  mlb = MultiLabelBinarizer(classes=ASPECT_LABELS)
  Y_test_bin = mlb.fit_transform(y_test)

  results_table = {}

  # 2. Đánh giá Mô hình 0: Baseline bộ luật từ khóa (rule-v0)
  print("\n[1/3] Đang chấm điểm Baseline (rule-v0) trên tập Test...")
  baseline_model = RuleBasedAspectBaseline(model_version="rule-v0")
  y_pred_rule_lists = baseline_model.predict_aspects_list(X_test)
  Y_pred_rule_bin = mlb.transform(y_pred_rule_lists)
  results_table["Baseline (rule-v0)"] = evaluate_predictions(
      Y_test_bin, Y_pred_rule_bin
  )

  # 3. Huấn luyện & Đánh giá Mô hình 1: TF-IDF + Logistic Regression
  print("[2/3] Đang huấn luyện TF-IDF + Logistic Regression (aspect-lr-v1)...")
  lr_model = AspectMLClassifier(
      model_type="logreg", model_version="aspect-lr-v1", threshold=0.45
  )
  lr_model.fit(X_train, y_train)
  if X_dev:
    dev_f1_lr = lr_model.tune_thresholds_on_dev(X_dev, y_dev)
    print(
        f"      -> Đã tối ưu ngưỡng trên tập Dev (Dev Macro-F1 = {dev_f1_lr}) |"
        f" Ngưỡng 9 nhãn: {lr_model.class_thresholds.tolist()}"
    )
    # Huấn luyện lại trên gộp (Train + Dev) với bộ ngưỡng tối ưu vừa tìm được
    saved_th_lr = lr_model.class_thresholds
    lr_model.fit(X_train + X_dev, y_train + y_dev)
    lr_model.class_thresholds = saved_th_lr

  Y_pred_lr_bin = lr_model.predict_binary(X_test)
  results_table["TF-IDF + LogReg (aspect-lr-v1)"] = evaluate_predictions(
      Y_test_bin, Y_pred_lr_bin
  )

  # 4. Huấn luyện & Đánh giá Mô hình 2: TF-IDF + Linear SVM
  print("[3/3] Đang huấn luyện TF-IDF + Linear SVM (aspect-svm-v1)...")
  svm_model = AspectMLClassifier(
      model_type="svm", model_version="aspect-svm-v1", threshold=0.45
  )
  svm_model.fit(X_train, y_train)
  if X_dev:
    dev_f1_svm = svm_model.tune_thresholds_on_dev(X_dev, y_dev)
    print(
        "      -> Đã tối ưu ngưỡng trên tập Dev (Dev Macro-F1 ="
        f" {dev_f1_svm}) | Ngưỡng 9 nhãn:"
        f" {svm_model.class_thresholds.tolist()}"
    )
    saved_th_svm = svm_model.class_thresholds
    svm_model.fit(X_train + X_dev, y_train + y_dev)
    svm_model.class_thresholds = saved_th_svm

  Y_pred_svm_bin = svm_model.predict_binary(X_test)
  results_table["TF-IDF + LinearSVM (aspect-svm-v1)"] = evaluate_predictions(
      Y_test_bin, Y_pred_svm_bin
  )

  # 5. Tạo bảng so sánh F1 và xuất ra màn hình + file
  df_report = pd.DataFrame(results_table)
  print(
      "\n================ BẢNG SO SÁNH F1 TỪNG KHÍA CẠNH TRÊN TẬP TEST (STT 8)"
      " ================"
  )
  print(df_report.to_string())

  csv_path = out_dir / "aspect_f1_comparison.csv"
  md_path = out_dir / "aspect_f1_comparison.md"
  df_report.to_csv(csv_path, encoding="utf-8")
  with md_path.open("w", encoding="utf-8") as f:
    f.write("# Bảng so sánh F1 phân loại khía cạnh (Công việc STT 8)\n\n")
    f.write(dataframe_to_markdown_safe(df_report) + "\n")

  # 6. Lưu model tốt nhất ra ổ cứng để bàn giao cho nhóm
  best_model = (
      svm_model
      if results_table["TF-IDF + LinearSVM (aspect-svm-v1)"]["MACRO_F1"]
      >= results_table["TF-IDF + LogReg (aspect-lr-v1)"]["MACRO_F1"]
      else lr_model
  )
  model_path = out_dir / "best_aspect_model.pkl"
  joblib.dump(best_model, model_path)
  print(f"\n[+] Đã lưu bảng điểm F1 tại: {csv_path} và {md_path}")
  print(
      f"[+] Đã lưu model tốt nhất ({best_model.model_version}) tại:"
      f" {model_path}"
  )


if __name__ == "__main__":
  main()
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import re
from typing import Dict, List, Optional, Tuple
import unicodedata

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
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import LinearSVC

# =====================================================================
# 1. CHUẨN HÓA NHÃN & ĐỌC DỮ LIỆU ĐA NGUỒN
# =====================================================================
SOFTWARE_HINT_REGEX = re.compile(
    r"\b(ios|android|one\s*ui|hyper\s*os|miui|color\s*os|oxygen\s*os|"
    r"phan\s*mem|he\s*dieu\s*hanh|cap\s*nhat|update|ung\s*dung|app|"
    r"vang\s*app|loi\s*ung\s*dung|tu\s*dong|thong\s*bao|giao\s*dien|"
    r"rom|os|ch\s*play|app\s*store|zalo|facebook|mess|messenger|youtube|"
    r"da\s*nhiem|chia\s*doi\s*man\s*hinh|nhan\s*ban\s*ung\s*dung)\b",
    re.IGNORECASE,
)

# Quy đổi các nhãn ngoài Schema phát sinh từ LLM trong tập Train của Kiệt
EXTRA_ASPECT_MAP = {
    "AUDIO": "HARDWARE_OTHER",
    "SPEAKER": "HARDWARE_OTHER",
    "STORAGE": "PERFORMANCE",
    "FEATURES": "HARDWARE_OTHER",
}


def _to_ascii_lower(text: str) -> str:
  text = text.replace("đ", "d").replace("Đ", "d").lower()
  return (
      unicodedata.normalize("NFKD", text)
      .encode("ascii", "ignore")
      .decode("utf-8")
  )


def find_file_in_repo(rel_path: str) -> Optional[Path]:
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


def _normalize_aspect(raw_name: str, map_extra: bool = True) -> str:
  name = str(raw_name).split("#")[0].strip().upper()
  if map_extra and name in EXTRA_ASPECT_MAP:
    return EXTRA_ASPECT_MAP[name]
  return name


def load_clause_dataset(
    jsonl_path: Path,
    split_filter: Optional[str] = None,
    map_extra_labels: bool = True,
    drop_uit_warranty: bool = False,
) -> Tuple[List[str], List[List[str]]]:
  """Đọc dữ liệu từ Đạt (UIT-ViSD4SA), Kiệt (gold_labels train/test) và Schema v2."""
  clause_to_aspects = defaultdict(set)
  clause_texts_ordered = []
  seen_keys = set()
  skipped_lines = 0

  with jsonl_path.open("r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
      if not line.strip():
        continue
      try:
        record = json.loads(line)
      except json.JSONDecodeError as e:
        skipped_lines += 1
        print(
            f"    [!] Bỏ qua dòng {idx + 1} lỗi JSON trong"
            f" {jsonl_path.name}: {e}"
        )
        continue

      if split_filter and "split" in record and record["split"]:
        if str(record["split"]).lower() != split_filter.lower():
          continue

      text = (record.get("clause_text") or record.get("text") or "").strip()
      if not text:
        continue

      cid = record.get("clause_id") or record.get("comment_id") or ""
      cidx = record.get("clause_idx", "")
      key = (
          f"{cid}#{cidx}" if (cid != "" and cidx != "") else f"row_{idx}_{text}"
      )

      if key not in seen_keys:
        seen_keys.add(key)
        clause_texts_ordered.append((key, text))

      # Format Đạt (UIT-ViSD4SA): "labels": [[start, end, "ASPECT#sentiment"], ...]
      if record.get("labels") and isinstance(record["labels"], list):
        for item in record["labels"]:
          if isinstance(item, list) and len(item) >= 3:
            start, end, raw_label = int(item[0]), int(item[1]), str(item[2])
            aspect_name = _normalize_aspect(raw_label, map_extra=True)

            if drop_uit_warranty and aspect_name == "WARRANTY":
              continue

            span_text = (
                text[start:end] if (0 <= start < end <= len(text)) else text
            )
            if aspect_name in ("PERFORMANCE", "HARDWARE_OTHER"):
              if SOFTWARE_HINT_REGEX.search(_to_ascii_lower(span_text)):
                aspect_name = "SOFTWARE"

            if aspect_name in ASPECT_LABELS:
              clause_to_aspects[key].add(aspect_name)

      # Format Kiệt (YouTube): hỗ trợ cả kiểu Train ({"aspect": "DISPLAY", ...})
      # và kiểu Test ({"HARDWARE_OTHER": "neu"})
      elif record.get("aspects") and isinstance(record["aspects"], list):
        for asp_item in record["aspects"]:
          if isinstance(asp_item, dict):
            if "aspect" in asp_item:
              asp_name = _normalize_aspect(
                  asp_item.get("aspect", ""), map_extra=map_extra_labels
              )
              if asp_name in ASPECT_LABELS:
                clause_to_aspects[key].add(asp_name)
            else:
              for k in asp_item.keys():
                asp_name = _normalize_aspect(k, map_extra=map_extra_labels)
                if asp_name in ASPECT_LABELS:
                  clause_to_aspects[key].add(asp_name)
          else:
            asp_name = _normalize_aspect(asp_item, map_extra=map_extra_labels)
            if asp_name in ASPECT_LABELS:
              clause_to_aspects[key].add(asp_name)

      # Format Schema v2: "aspect": "BATTERY"
      elif record.get("aspect"):
        asp_upper = _normalize_aspect(
            record["aspect"], map_extra=map_extra_labels
        )
        if asp_upper in ASPECT_LABELS:
          clause_to_aspects[key].add(asp_upper)

  if skipped_lines > 0:
    print(
        f"    [!] Tổng số dòng lỗi JSON bị bỏ qua trong {jsonl_path.name}:"
        f" {skipped_lines}"
    )

  texts = [text for _, text in clause_texts_ordered]
  labels = [
      sorted(list(clause_to_aspects[key])) for key, _ in clause_texts_ordered
  ]
  return texts, labels


def generate_balanced_pseudo_labels(
    teacher_model,
    clean_data_path: Path,
    pos_threshold: float = 0.92,
    neg_threshold: float = 0.12,
    max_pos: int = 2000,
    max_neg: int = 2000,
) -> Tuple[List[str], List[List[str]]]:
  """Sinh nhãn giả cân bằng gồm cả mẫu dương (confidence >= 0.92) và mẫu âm (max_prob <= 0.12)."""
  candidate_clauses = []
  with clean_data_path.open("r", encoding="utf-8") as f:
    for line in f:
      if not line.strip():
        continue
      rec = json.loads(line)
      if rec.get("is_spam", False):
        continue
      clauses = rec.get("clauses", [])
      if isinstance(clauses, list):
        for cl in clauses:
          if isinstance(cl, dict):
            cl_text = (cl.get("text") or cl.get("clause_text") or "").strip()
          else:
            cl_text = str(cl).strip()
          if len(cl_text) >= 6:
            candidate_clauses.append(cl_text)
      if len(candidate_clauses) >= (max_pos + max_neg) * 8:
        break

  if not candidate_clauses:
    return [], []

  X_vec = teacher_model.vectorizer.transform(candidate_clauses)
  probs = teacher_model.clf.predict_proba(X_vec)

  pos_texts, pos_labels = [], []
  neg_texts, neg_labels = [], []

  for text, prob_row in zip(candidate_clauses, probs):
    if len(pos_texts) < max_pos:
      high_conf_aspects = [
          asp
          for asp, p in zip(ASPECT_LABELS, prob_row)
          if p >= pos_threshold and asp != "WARRANTY"
      ]
      if high_conf_aspects:
        pos_texts.append(text)
        pos_labels.append(high_conf_aspects)
        continue

    if len(neg_texts) < max_neg and float(np.max(prob_row)) <= neg_threshold:
      neg_texts.append(text)
      neg_labels.append([])

    if len(pos_texts) >= max_pos and len(neg_texts) >= max_neg:
      break

  return pos_texts + neg_texts, pos_labels + neg_labels


# =====================================================================
# 2. CLASS MÔ HÌNH HỌC MÁY ĐA NHÃN (WORD + CHAR N-GRAM TF-IDF)
# =====================================================================
class AspectMLClassifier:

  def __init__(
      self,
      model_type: str = "logreg",
      model_version: str = "aspect-lr-v2",
      threshold: float = 0.50,
      use_char_ngrams: bool = True,
  ):
    self.model_type = model_type
    self.model_version = model_version
    self.threshold = threshold
    self.class_thresholds: Optional[np.ndarray] = None
    self.mlb = MultiLabelBinarizer(classes=ASPECT_LABELS)

    if use_char_ngrams:
      self.vectorizer = FeatureUnion([
          (
              "word",
              TfidfVectorizer(
                  ngram_range=(1, 2),
                  max_features=30000,
                  min_df=2,
                  sublinear_tf=True,
              ),
          ),
          (
              "char",
              TfidfVectorizer(
                  analyzer="char_wb",
                  ngram_range=(3, 5),
                  max_features=35000,
                  min_df=3,
                  sublinear_tf=True,
              ),
          ),
      ])
    else:
      self.vectorizer = TfidfVectorizer(
          ngram_range=(1, 2), max_features=35000, sublinear_tf=True
      )

    if model_type == "logreg":
      base_clf = LogisticRegression(
          C=2.5, max_iter=1000, class_weight="balanced", random_state=42
      )
      self.clf = OneVsRestClassifier(base_clf)
    elif model_type == "svm":
      base_svm = LinearSVC(C=0.8, class_weight="balanced", random_state=42)
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
    Y_dev = self.mlb.transform(dev_aspect_lists)
    X_dev = self.vectorizer.transform(dev_texts)
    probs = self.clf.predict_proba(X_dev)

    best_thresholds = np.full(len(ASPECT_LABELS), self.threshold)
    # Mở rộng dải dò ngưỡng lên tới 0.90 để chặn đoán thừa trên câu rỗng YouTube
    candidate_grid = np.arange(0.15, 0.91, 0.05)

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
    return round(
        float(f1_score(Y_dev, Y_dev_pred, average="macro", zero_division=0)), 4
    )

  def predict_binary(self, clause_texts: List[str]) -> np.ndarray:
    X = self.vectorizer.transform(clause_texts)
    probs = self.clf.predict_proba(X)
    if self.class_thresholds is not None:
      return (probs >= self.class_thresholds).astype(int)
    return (probs >= self.threshold).astype(int)

  def predict_mentions(self, clause_text: str) -> List[Dict]:
    """Xuất kết quả đúng chuẩn contracts/aspect-mention.schema.json cho STT 12."""
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
# 3. CHẤM ĐIỂM & CHẠY PIPELINE TINH CHỈNH (TEACHER -> BALANCED STUDENT)
# =====================================================================
def evaluate_predictions(
    y_true_bin: np.ndarray, y_pred_bin: np.ndarray
) -> Dict[str, float]:
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


def subsample_dataset(
    texts: List[str], labels: List[List[str]], max_n: int, seed: int = 42
) -> Tuple[List[str], List[List[str]]]:
  if len(texts) <= max_n:
    return texts, labels
  rng = random.Random(seed)
  indices = list(range(len(texts)))
  rng.shuffle(indices)
  chosen = indices[:max_n]
  return [texts[i] for i in chosen], [labels[i] for i in chosen]


def main():
  parser = argparse.ArgumentParser(
      description="Pipeline Teacher-Student tinh chỉnh phân loại 9 khía cạnh (STT 8)"
  )
  parser.add_argument(
      "--ext_train", type=str, default="data/uit_visd4sa/train.jsonl"
  )
  parser.add_argument(
      "--ext_dev", type=str, default="data/uit_visd4sa/dev.jsonl"
  )
  parser.add_argument(
      "--ext_test", type=str, default="data/uit_visd4sa/test.jsonl"
  )
  parser.add_argument(
      "--yt_train", type=str, default="data/gold_labels_train.jsonl"
  )
  parser.add_argument(
      "--yt_test", type=str, default="data/gold_labels_test.jsonl"
  )
  parser.add_argument("--clean_data", type=str, default="data/clean_data.jsonl")
  parser.add_argument(
      "--output_dir", type=str, default="artifacts/aspect_models"
  )
  args = parser.parse_args()

  out_dir = Path(args.output_dir)
  out_dir.mkdir(parents=True, exist_ok=True)

  ext_train_p = find_file_in_repo(args.ext_train)
  ext_dev_p = find_file_in_repo(args.ext_dev)
  ext_test_p = find_file_in_repo(args.ext_test)
  yt_train_p = find_file_in_repo(args.yt_train)
  yt_test_p = find_file_in_repo(args.yt_test)
  clean_data_p = find_file_in_repo(args.clean_data)

  # 1. Nạp dữ liệu Đạt cho Teacher (đủ nhãn) và bản lọc nhiễu WARRANTY cho Student
  X_ext_train, y_ext_train = load_clause_dataset(ext_train_p)
  X_ext_dev, y_ext_dev = (
      load_clause_dataset(ext_dev_p)
      if (ext_dev_p and ext_dev_p.exists())
      else ([], [])
  )
  X_ext_test, y_ext_test = (
      load_clause_dataset(ext_test_p)
      if (ext_test_p and ext_test_p.exists())
      else ([], [])
  )

  # Bản UIT nhẹ cho Student: lược bỏ nhãn WARRANTY lệch nghĩa và lấy mẫu 4.000 dòng
  X_ext_clean_tr, y_ext_clean_tr = load_clause_dataset(
      ext_train_p, drop_uit_warranty=True
  )
  X_ext_light, y_ext_light = subsample_dataset(
      X_ext_clean_tr, y_ext_clean_tr, max_n=4000, seed=42
  )

  # 2. Nạp dữ liệu YouTube: Train (có map AUDIO/SPEAKER/STORAGE), Test (giữ nguyên chuẩn gốc)
  X_yt_train, y_yt_train = (
      load_clause_dataset(yt_train_p, map_extra_labels=True)
      if (yt_train_p and yt_train_p.exists())
      else ([], [])
  )
  X_yt_test, y_yt_test = (
      load_clause_dataset(yt_test_p, map_extra_labels=False)
      if (yt_test_p and yt_test_p.exists())
      else ([], [])
  )

  if X_yt_test:
    X_eval, y_eval = X_yt_test, y_yt_test
    eval_name = f"YouTube Test ({len(X_eval):,} mệnh đề)"
  else:
    X_eval, y_eval = X_ext_test, y_ext_test
    eval_name = f"UIT-ViSD4SA Test ({len(X_eval):,} mẫu)"

  labeled_eval = sum(1 for lbs in y_eval if lbs)
  print("[*] Đã nạp đầy đủ nguồn dữ liệu:")
  print(f"    - Đạt (UIT-ViSD4SA full):  {len(X_ext_train) + len(X_ext_dev):,} mẫu")
  print(f"    - Đạt (UIT nhẹ cho Student): {len(X_ext_light):,} mẫu (đã lọc nhiễu WARRANTY)")
  print(f"    - Kiệt (YouTube Train):    {len(X_yt_train):,} mệnh đề (đã quy đổi nhãn phụ)")
  print(f"    - Tập Đánh giá (Test):     {eval_name} (có nhãn: {labeled_eval:,} dòng)")

  mlb = MultiLabelBinarizer(classes=ASPECT_LABELS)
  Y_eval_bin = mlb.fit_transform(y_eval)
  results_table = {}
  candidate_models = {}

  # [1/5] Baseline (rule-v0)
  print("\n[1/5] Đang chấm điểm Baseline (rule-v0)...")
  baseline = RuleBasedAspectBaseline(model_version="rule-v0")
  Y_pred_rule = mlb.transform(baseline.predict_aspects_list(X_eval))
  results_table["1. Baseline (rule-v0)"] = evaluate_predictions(
      Y_eval_bin, Y_pred_rule
  )

  # [2/5] Teacher SVM (Chỉ học Đạt)
  print("[2/5] Lượt 1: Đang huấn luyện Teacher SVM trên dữ liệu Đạt...")
  teacher_svm = AspectMLClassifier(
      model_type="svm",
      model_version="aspect-teacher-svm-v1",
      threshold=0.45,
      use_char_ngrams=False,
  )
  teacher_svm.fit(X_ext_train, y_ext_train)
  if X_ext_dev:
    teacher_svm.tune_thresholds_on_dev(X_ext_dev, y_ext_dev)
    saved_th = teacher_svm.class_thresholds
    teacher_svm.fit(X_ext_train + X_ext_dev, y_ext_train + y_ext_dev)
    teacher_svm.class_thresholds = saved_th

  results_table["2. Teacher SVM (UIT)"] = evaluate_predictions(
      Y_eval_bin, teacher_svm.predict_binary(X_eval)
  )
  candidate_models["2. Teacher SVM (UIT)"] = teacher_svm

  # [3/5] Sinh nhãn giả cân bằng (dương >= 0.92 + âm <= 0.12)
  X_pseudo, y_pseudo = [], []
  if clean_data_p and clean_data_p.exists():
    print(
        f"[3/5] Đang dùng Teacher quét {clean_data_p.name} sinh nhãn giả cân"
        " bằng (dương >= 0.92 & âm <= 0.12)..."
    )
    X_pseudo, y_pseudo = generate_balanced_pseudo_labels(
        teacher_svm,
        clean_data_p,
        pos_threshold=0.92,
        neg_threshold=0.12,
        max_pos=2000,
        max_neg=2000,
    )
    n_pos = sum(1 for y in y_pseudo if y)
    n_neg = len(y_pseudo) - n_pos
    print(f"      -> Thu được {len(X_pseudo):,} nhãn giả ({n_pos:,} dương + {n_neg:,} âm)!")
  else:
    print("[3/5] Chưa thấy data/clean_data.jsonl, bỏ qua bước nhãn giả.")

  if X_yt_train:
    X_yt_subtrain, X_yt_dev, y_yt_subtrain, y_yt_dev = train_test_split(
        X_yt_train, y_yt_train, test_size=0.20, random_state=42
    )

    # [4/5] Đối chứng: Pure YouTube LogReg (Chỉ học 3.000 mẫu Kiệt + Char/Word N-gram)
    print("[4/5] Đang huấn luyện Pure YouTube LogReg (chỉ học dữ liệu Kiệt)...")
    pure_yt_lr = AspectMLClassifier(
        model_type="logreg",
        model_version="aspect-yt-lr-v2",
        threshold=0.50,
        use_char_ngrams=True,
    )
    pure_yt_lr.fit(X_yt_subtrain, y_yt_subtrain)
    dev_f1_pure = pure_yt_lr.tune_thresholds_on_dev(X_yt_dev, y_yt_dev)
    saved_th_pure = pure_yt_lr.class_thresholds
    pure_yt_lr.fit(X_yt_train, y_yt_train)
    pure_yt_lr.class_thresholds = saved_th_pure
    print(
        f"      -> Pure YT LogReg tối ưu ngưỡng trên YT Dev (Macro-F1 = {dev_f1_pure})"
    )
    results_table["3. Pure YT LogReg"] = evaluate_predictions(
        Y_eval_bin, pure_yt_lr.predict_binary(X_eval)
    )
    candidate_models["3. Pure YT LogReg"] = pure_yt_lr

    # [5/5] Student LogReg & Student SVM (Kiệt x4 + UIT nhẹ + Nhãn giả cân bằng)
    print(
        "[5/5] Lượt 2: Đang huấn luyện Student (LogReg & SVM) trên"
        " (Kiệt x4 + UIT nhẹ + Nhãn giả cân bằng)..."
    )
    X_sub_all = (X_yt_subtrain * 4) + X_ext_light + X_pseudo
    y_sub_all = (y_yt_subtrain * 4) + y_ext_light + y_pseudo

    X_full_all = (X_yt_train * 4) + X_ext_light + X_pseudo
    y_full_all = (y_yt_train * 4) + y_ext_light + y_pseudo

    # Student LogReg
    student_lr = AspectMLClassifier(
        model_type="logreg",
        model_version="aspect-student-lr-v2",
        threshold=0.50,
        use_char_ngrams=True,
    )
    student_lr.fit(X_sub_all, y_sub_all)
    dev_f1_lr = student_lr.tune_thresholds_on_dev(X_yt_dev, y_yt_dev)
    saved_th_lr = student_lr.class_thresholds
    student_lr.fit(X_full_all, y_full_all)
    student_lr.class_thresholds = saved_th_lr
    print(
        f"      -> Student LogReg tối ưu ngưỡng trên YT Dev (Macro-F1 = {dev_f1_lr})"
    )
    print(f"         Ngưỡng 9 nhãn: {saved_th_lr.tolist()}")
    results_table["4. Student LogReg"] = evaluate_predictions(
        Y_eval_bin, student_lr.predict_binary(X_eval)
    )
    candidate_models["4. Student LogReg"] = student_lr

    # Student SVM
    student_svm = AspectMLClassifier(
        model_type="svm",
        model_version="aspect-student-svm-v2",
        threshold=0.50,
        use_char_ngrams=True,
    )
    student_svm.fit(X_sub_all, y_sub_all)
    dev_f1_svm = student_svm.tune_thresholds_on_dev(X_yt_dev, y_yt_dev)
    saved_th_svm = student_svm.class_thresholds
    student_svm.fit(X_full_all, y_full_all)
    student_svm.class_thresholds = saved_th_svm
    print(
        f"      -> Student SVM tối ưu ngưỡng trên YT Dev (Macro-F1 = {dev_f1_svm})"
    )
    results_table["5. Student SVM"] = evaluate_predictions(
        Y_eval_bin, student_svm.predict_binary(X_eval)
    )
    candidate_models["5. Student SVM"] = student_svm

  # Chọn model tốt nhất theo MACRO_F1
  best_name = max(
      candidate_models.keys(), key=lambda name: results_table[name]["MACRO_F1"]
  )
  best_model = candidate_models[best_name]

  # Xuất báo cáo & Lưu model tốt nhất
  df_report = pd.DataFrame(results_table)
  print(
      f"\n================ BẢNG SO SÁNH F1 TRÊN {eval_name.upper()} ================"
  )
  print(df_report.to_string())

  csv_path = out_dir / "aspect_f1_comparison.csv"
  md_path = out_dir / "aspect_f1_comparison.md"
  df_report.to_csv(csv_path, encoding="utf-8")
  with md_path.open("w", encoding="utf-8") as f:
    f.write(
        f"# Bảng so sánh F1 phân loại khía cạnh (STT 8) — Tập đánh giá:"
        f" {eval_name}\n\n"
    )
    f.write(dataframe_to_markdown_safe(df_report) + "\n")

  model_path = out_dir / "best_aspect_model.pkl"
  joblib.dump(best_model, model_path)
  print(f"\n[+] Đã lưu bảng điểm F1 tại: {csv_path} và {md_path}")
  print(
      f"[+] Đã lưu model tốt nhất ({best_name} / {best_model.model_version})"
      f" tại: {model_path}"
  )


if __name__ == "__main__":
  main()
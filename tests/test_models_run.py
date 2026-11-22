"""Mục đích: Kiểm bước suy luận theo bình luận (src/models/run.py và các luật mốc, docs/4-mo-hinh/dac-ta-suy-luan.md), kể cả việc đầu ra qua được bước kiểm đầu vào của Công việc 12; cập nhật lần cuối: 2026-11-20.

Chỉ dùng câu và danh mục máy tự soạn. Chạy: python -m pytest tests/test_models_run.py
"""

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from src.models import run as SL
from src.models.aspect.keywords import khia_canh
from src.models.owner_defect import da_dung_may, loai_loi
from src.models.sentiment.rules import NEG, NEU, POS, cam_xuc
from src.models.target_model import (BINH_LUAN_CHA, KHONG_RO, MENH_DE, MENH_DE_TRUOC, VIDEO, BoNhanMay,
                                     so_ngay_tu_ra_mat, xac_dinh_may)
from src.processing.run import xu_ly_ban_ghi

DANH_MUC = {
    "s26u": {"title": "Samsung Galaxy S26 Ultra", "launch_date": "2026-02-25", "aliases": ["Galaxy S26 Ultra", "s26 ultra"]},
    "s25u": {"title": "Samsung Galaxy S25 Ultra", "launch_date": "2025-01-22", "aliases": ["Galaxy S25 Ultra", "s25 ultra"]},
    "ip17prm": {"title": "iPhone 17 Pro Max", "launch_date": "2025-09-15", "aliases": ["iPhone 17 Pro Max", "ip17 prm"]},
    "xiaomi17u": {"title": "Xiaomi 17 Ultra", "launch_date": "2026-02-26", "aliases": ["Xiaomi 17 Ultra"]},
}
NHAN_MAY = BoNhanMay(DANH_MUC)


def ban_ghi(cid, text, model="s26u", parent_text=None, published_at="2026-03-01T03:00:00Z"):
    """Một bình luận đủ trường raw (schema 3) đã qua tầng 2."""
    rec = {
        "comment_id": cid, "video_id": "vid1", "parent_id": "p1" if parent_text else None, "parent_text": parent_text,
        "model": model, "source": "youtube", "text": text, "text_norm": "", "author_hash": "a" * 64,
        "published_at": published_at, "like_count": 0, "reply_count": 0, "fetched_at": "2026-04-30T00:00:00Z",
        "ingested_at": "2026-04-30T00:00:00Z", "schema_version": 3, "author_name": None,
        "author_channel_created_at": None, "author_video_count": None, "author_subscriber_count": None,
        "author_is_creator": False, "author_fetched_at": None,
    }
    return xu_ly_ban_ghi(rec, "2026-03-20T00:00:00Z")


def gon(mentions):
    return sorted((m["target_model"], m["aspect"], m["sentiment"], m["clause_idx"]) for m in mentions)


class LuatMoc(unittest.TestCase):
    def test_khia_canh(self):
        self.assertEqual(khia_canh("Pin trâu, cam đẹp"), ["BATTERY", "CAMERA"])
        self.assertEqual(khia_canh("trẻ trâu quá, cam on anh"), [])

    def test_cam_xuc(self):
        ca = {"pin trâu": POS, "pin yếu": NEG, "không lag chút nào": POS, "không đẹp lắm": NEG, "pin tụt nhanh": NEG,
              "sạc nhanh": POS, "có lag không": NEU, "camera 200mp": NEU, "hết lag rồi": POS, "": NEU}
        for s, nhan in ca.items():
            self.assertEqual(cam_xuc(s), nhan, s)

    def test_da_dung_va_loai_loi(self):
        self.assertTrue(da_dung_may("mình dùng được 2 tháng rồi"))
        self.assertIsNone(da_dung_may("anh dùng thử chưa"))
        self.assertEqual(loai_loi("BATTERY", "pin hao quá"), "BATTERY_DRAIN")
        self.assertEqual(loai_loi("PERFORMANCE", "máy nóng quá"), "OVERHEAT")
        self.assertEqual(loai_loi("PERFORMANCE", "chơi game lag"), "LAG")
        self.assertIsNone(loai_loi("DISPLAY", "màn tối"))

    def test_nhan_may(self):
        self.assertEqual(NHAN_MAY.tim("iPhone 17 Pro Max pin trâu hơn S26 Ultra"), ["ip17prm", "s26u"])
        self.assertEqual(NHAN_MAY.tim("ip 17 prm ngon"), ["ip17prm"])
        self.assertEqual(NHAN_MAY.tim("táo với ss ngon"), [])

    def test_xac_dinh_may(self):
        md = [["ip17prm"], [], []]
        self.assertEqual(xac_dinh_may(0, md, [], "s26u", DANH_MUC), ("ip17prm", MENH_DE))
        self.assertEqual(xac_dinh_may(2, md, [], "s26u", DANH_MUC), ("ip17prm", MENH_DE_TRUOC))
        self.assertEqual(xac_dinh_may(0, [[]], ["s25u"], "s26u", DANH_MUC), ("s25u", BINH_LUAN_CHA))
        self.assertEqual(xac_dinh_may(0, [[]], [], "s26u", DANH_MUC), ("s26u", VIDEO))
        self.assertEqual(xac_dinh_may(0, [[]], [], "s26u|ip17prm", DANH_MUC), (None, KHONG_RO))

    def test_so_ngay(self):
        self.assertEqual(so_ngay_tu_ra_mat("2026-02-24T17:30:00Z", "2026-02-25"), 0)   # 00:30 giờ VN ngày 25
        self.assertIsNone(so_ngay_tu_ra_mat("2026-02-24T17:30:00Z", None))


class SuyLuanBinhLuan(unittest.TestCase):
    def test_may_lay_tu_menh_de_truoc(self):
        m = SL.suy_luan_binh_luan(ban_ghi("c1", "iPhone 17 Pro Max thì pin trâu, camera đẹp"), NHAN_MAY)
        self.assertEqual(gon(m), [("ip17prm", "BATTERY", POS, 0), ("ip17prm", "CAMERA", POS, 1)])

    def test_cung_khia_canh_vua_khen_vua_che(self):
        m = SL.suy_luan_binh_luan(ban_ghi("c2", "camera ngày đẹp, đêm thì chụp kém"), NHAN_MAY)
        self.assertEqual(gon(m), [("s26u", "CAMERA", NEG, 1), ("s26u", "CAMERA", POS, 0)])

    def test_moi_may_khia_canh_mot_phieu(self):
        m = SL.suy_luan_binh_luan(ban_ghi("c3", "pin tốt, pin trâu, pin ngon"), NHAN_MAY)
        self.assertEqual(gon(m), [("s26u", "BATTERY", POS, 0)])
        m = SL.suy_luan_binh_luan(ban_ghi("c4", "camera 200mp, chụp đẹp"), NHAN_MAY)
        self.assertEqual(gon(m), [("s26u", "CAMERA", POS, 1)])   # có khen thì bỏ dòng trung tính

    def test_bo_qua_spam_ngoai_ngu_rong(self):
        for text in ["pin trâu, liên hệ zalo 0912345678", "nice phone battery bro", "   ", "😂😂"]:
            self.assertEqual(SL.suy_luan_binh_luan(ban_ghi("c5", text), NHAN_MAY), [], text)

    def test_reply_va_video_nhieu_may(self):
        m = SL.suy_luan_binh_luan(ban_ghi("c6", "pin trâu thật", model="ip17prm", parent_text="S26 Ultra pin sao ae"),
                                  NHAN_MAY)
        self.assertEqual([x["target_model"] for x in m], ["s26u"])
        m = SL.suy_luan_binh_luan(ban_ghi("c7", "pin trâu thật", model="s26u|ip17prm"), NHAN_MAY)
        self.assertEqual([(x["target_model"], x["days_since_launch"]) for x in m], [(None, None)])

    def test_dung_contract(self):
        try:
            from src.analysis.validation import load_schema_validator, validate_schema
        except ImportError:   # chưa cài jsonschema
            self.skipTest("cần jsonschema (pip install -r src/analysis/requirements.txt)")
        v = load_schema_validator()
        rec = ban_ghi("c8", "S26 Ultra pin hao quá, mình dùng được 2 tháng, camera thì đẹp")
        m = SL.suy_luan_binh_luan(rec, NHAN_MAY)
        self.assertTrue(m)
        for x in m:
            self.assertEqual(list(x), list(SL.CAC_TRUONG))
            self.assertEqual(validate_schema(x, v), [], x)
            self.assertEqual(x["clause_text"], rec["clauses"][x["clause_idx"]]["text"])
            self.assertEqual(x["mention_id"], f"{x['comment_id']}#{x['clause_idx']}#{x['aspect']}")
        pin = next(x for x in m if x["aspect"] == "BATTERY")
        self.assertEqual((pin["sentiment"], pin["defect_type"], pin["is_owner"], pin["days_since_launch"]),
                         (NEG, "BATTERY_DRAIN", True, 4))


class QuaKiemTraCV12(unittest.TestCase):
    """Chạy lệnh suy luận trên file giả rồi cho đầu ra qua bước kiểm đầu vào và tính aggregates của Công việc 12."""

    def test_chuoi_suy_luan_den_aggregates(self):
        try:
            import yaml
            from src.analysis import build_aggregates
            from src.analysis.validate_inputs import build_parser, run as kiem
        except ImportError:
            self.skipTest("cần jsonschema, PyYAML (pip install -r src/analysis/requirements.txt)")
        cau = ["pin trâu, camera đẹp", "pin hao quá", "màn hình đẹp nhưng giá đắt", "S25 Ultra pin yếu hơn",
               "camera chụp đêm kém", "chơi game mượt", "nice phone bro", "pin trâu, liên hệ zalo 0912345678"]
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            vao = d / "comments.jsonl"
            with open(vao, "w", encoding="utf-8") as f:
                for i in range(40):   # 40 bình luận, 8 video, đều trong cửa sổ 4 tuần của s26u
                    rec = ban_ghi(f"c{i}", cau[i % len(cau)], published_at=f"2026-03-{1 + i % 20:02d}T03:00:00Z")
                    rec["video_id"] = f"vid{i % 8}"
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            danh_muc = d / "pipeline.yaml"
            danh_muc.write_text(yaml.safe_dump({"models": [{"name": k, **v} for k, v in DANH_MUC.items()]},
                                               allow_unicode=True), encoding="utf-8")
            cau_hinh = d / "analysis.yaml"
            cau_hinh.write_text(yaml.safe_dump({"target_model": "s26u", "predecessor_model": "s25u",
                                                "rival_models": ["ip17prm", "xiaomi17u"],
                                                "expected_model_version": SL.MODEL_VERSION}), encoding="utf-8")
            ra = d / "aspect_mentions.jsonl"
            man = SL.chay(vao, ra, danh_muc, in_tien_do=False)
            self.assertGreater(man["ra"]["so_mention"], 0)
            self.assertEqual(man["so_binh_luan_bo_qua"], {"spam": 5, "không phải tiếng Việt": 5})

            args = build_parser().parse_args(["--mentions", str(ra), "--comments", str(SL.file_binh_luan_cv12(ra)),
                                              "--models", str(danh_muc), "--config", str(cau_hinh),
                                              "--output", str(d / "kiem")])
            bao_cao, _ = kiem(args)
            self.assertEqual(bao_cao["status"], "passed")
            self.assertEqual(bao_cao["counts"]["rejected"], 0)

            ma = build_aggregates.main(["--mentions", str(ra), "--comments", str(SL.file_binh_luan_cv12(ra)),
                                        "--models", str(danh_muc), "--config", str(cau_hinh),
                                        "--output", str(d / "agg")])
            self.assertEqual(ma, 0)
            self.assertTrue((d / "agg" / "business_questions.json").exists())


if __name__ == "__main__":
    unittest.main()

"""Mục đích: Kiểm tra bước 2.1 làm sạch (clean.py), 2.2 chuẩn hóa (normalize.py) và lệnh chạy (run.py) theo docs/2-tien-xu-ly/; cập nhật lần cuối: 2026-11-19.

Chạy từ gốc repo:  python -m unittest tests.test_processing -v
Chỉ dùng câu tự soạn, không đọc dữ liệu thật.
"""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.processing import PIPELINE_VERSION, chuan_hoa, chuan_hoa_tung_buoc, lam_sach, tach_emoji, tach_tu
from src.processing import run as CHAY
from src.processing import clean as L1
from src.processing import normalize as L2

ZWJ = "‍"


def full(s: str) -> str:
    return chuan_hoa(lam_sach(s))


class Level1(unittest.TestCase):
    def test_b1_rong(self):
        for s in (None, float("nan"), "", "   ", "\n\t"):
            self.assertTrue(L1.la_rong(s), repr(s))
        self.assertFalse(L1.la_rong(" a "))
        self.assertEqual(lam_sach(None), "")
        self.assertEqual(lam_sach(" ​ "), "")   # chỉ có ký tự vô hình: rỗng sau làm sạch (B7)

    def test_b2_html_entity(self):
        self.assertEqual(L1.giai_ma_html("Tom &amp; Jerry &#39;hay&#39; &quot;x&quot;"), "Tom & Jerry 'hay' \"x\"")
        self.assertEqual(L1.giai_ma_html("&amp;amp;"), "&")   # mã hóa hai lần
        self.assertEqual(L1.giai_ma_html("R&D, a & b"), "R&D, a & b")   # không phải entity thì giữ

    def test_b3_ky_tu_vo_hinh(self):
        self.assertEqual(L1.bo_ky_tu_dieu_khien("pin​trâu﻿\x07"), "pintrâu")
        gia_dinh = "👨" + ZWJ + "👩" + ZWJ + "👧"
        self.assertEqual(L1.bo_ky_tu_dieu_khien(gia_dinh), gia_dinh)   # ZWJ giữa hai emoji: giữ
        self.assertEqual(L1.bo_ky_tu_dieu_khien("a" + ZWJ + "b"), "ab")   # ZWJ giữa chữ: bỏ
        co = "🏴\U000E0067\U000E0062\U000E007F"
        self.assertEqual(L1.bo_ky_tu_dieu_khien(co), co)   # ký tự tag của cờ: giữ
        self.assertEqual(L1.bo_ky_tu_dieu_khien("a\tb\nc"), "a\tb\nc")   # tab, xuống dòng để B5, B6

    def test_b4_nfc(self):
        self.assertEqual(L1.chuan_unicode("tiếng Việt"), "tiếng Việt")

    def test_b5_b6_xuong_dong_khoang_trang(self):
        self.assertEqual(L1.chuan_xuong_dong("a\r\nb\rc\x85d"), "a\nb\nc\nd")
        self.assertEqual(L1.chuan_xuong_dong("a\n\n \n\nb"), "a\nb")
        self.assertEqual(L1.chuan_khoang_trang("  a  b\t c \n d  "), "a b c\nd")
        self.assertEqual(lam_sach("a b"), "a b")   # U+2028 là khoảng trắng: B6 đổi thành dấu cách

    def test_lam_sach_ca_chuoi(self):
        self.assertEqual(lam_sach("  Pin &amp; sạc\r\n\r\n\r\ntốt​  "), "Pin & sạc\ntốt")


class Level2TungBuoc(unittest.TestCase):
    def test_n1_token(self):
        t = L2.thay_token
        self.assertEqual(t("xem https://tgdd.vn/a?x=1). ok"), "xem <url>). ok")
        self.assertEqual(t("mua ở tgdd.vn hoặc bit.ly/abc"), "mua ở <url> hoặc <url>")
        self.assertEqual(t("gửi abc.xyz@gmail.com nhé"), "gửi <email> nhé")
        self.assertEqual(t("gọi 0912 345 678, 0912.345.678 hoặc +84912345678"), "gọi <phone>, <phone> hoặc <phone>")
        self.assertEqual(t("@nguyen.van-a123. đúng"), "<user>. đúng")
        self.assertEqual(t("giá 3.990.000đ, 1.5tr, v.v, 6.7 inch"), "giá 3.990.000đ, 1.5tr, v.v, 6.7 inch")   # không phải URL/số ĐT
        self.assertEqual(t("0123 456 789"), "0123 456 789")   # đầu số không phải di động

    def test_n2_chu_thuong(self):
        self.assertEqual(L2.chu_thuong("ĐẸP Quá AI"), "đẹp quá ai")

    def test_n3_dau_thanh(self):
        d = L2.chuan_dau_thanh
        self.assertEqual(d("hoà thuỷ khoẻ xoá tuỳ"), "hòa thủy khỏe xóa tùy")
        self.assertEqual(d("quý quỳ toàn hoàng huỳnh thuyền"), "quý quỳ toàn hoàng huỳnh thuyền")   # không thuộc diện đổi
        self.assertEqual(d("hòa thủy", kieu="moi"), "hoà thuỷ")
        self.assertEqual(L2.kieu_dau_cua_tu("hoà"), "moi")
        self.assertEqual(L2.kieu_dau_cua_tu("hòa"), "cu")
        self.assertIsNone(L2.kieu_dau_cua_tu("quý"))

    def test_n4_cuoi_emoticon_lap(self):
        r = L2.rut_gon_lap
        self.assertEqual(r("kkkkk hahahaa hihi hjhj hehe"), "haha haha haha haha haha")
        self.assertEqual(r("huhu k ha"), "huhu k ha")   # khóc, "k" đơn, "ha" đơn: giữ
        self.assertEqual(r("=))))) :((( :v <333 ^^^"), "=)) :(( :v <33 ^^")
        self.assertEqual(r("quáaaaa đẹppppp nhéeee"), "quá đẹp nhé")
        self.assertEqual(r("zzz aaaa xoong đẹpp"), "zzz aaaa xoong đẹpp")   # cả chữ một ký tự, chữ có 2 ký tự lặp: giữ
        self.assertEqual(r("sao!!! ??? ,,, .. .... …"), "sao! ? , ... ... ...")
        self.assertEqual(r("10000000"), "10000000")   # số không rút

    def test_n5_dau_cau(self):
        t = L2.tach_dau_cau
        self.assertEqual(t("đẹp,pin ổn;giá?mua!luôn"), "đẹp, pin ổn; giá? mua! luôn")
        self.assertEqual(t("đẹp.pin ổn...mà"), "đẹp. pin ổn... mà")
        self.assertEqual(t("6.7 inch 12,5tr v.v ;d"), "6.7 inch 12,5tr v.v ;d")

    def test_n6_viet_tat(self):
        m = L2.mo_viet_tat
        self.assertEqual(m("ko biết dc ko, mn ơi"), "không biết được không, mọi người ơi")
        self.assertEqual(m("(ko) \"dc\" ko."), "(không) \"được\" không.")
        self.assertEqual(m("giá 500 k, 500k, nặng 1 kg, sạc 9 v, trễ 50 ms"), "giá 500 k, 500k, nặng 1 kg, sạc 9 v, trễ 50 ms")
        self.assertEqual(m("k biết, v thì sao, ms ra"), "không biết, vậy thì sao, mới ra")
        self.assertEqual(m("kon :v vs bh a e"), "kon :v vs bh a e")   # trong chữ khác, emoticon, mục cố ý chưa đưa vào

    def test_tu_dien(self):
        td = L2.doc_tu_dien()
        self.assertGreater(len(td), 40)
        for k in ("vs", "bh", "bn", "a", "e", "ss", "ip"):
            self.assertNotIn(k, td, f"'{k}' nhập nhằng, đặc tả nói chưa đưa vào")
        for k, v in td.items():
            self.assertEqual(k, k.lower())
            self.assertNotIn(" ", k)
            self.assertTrue(v)

    def test_tu_dien_sai_dinh_dang(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "td.tsv"
            p.write_text("ko\tkhông\nko\tkhong\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                L2.doc_tu_dien(str(p))
            p.write_text("bay h\tbây giờ\n", encoding="utf-8")
            with self.assertRaises(ValueError):   # lần trước lỗi nên lru_cache không lưu, đọc lại file mới
                L2.doc_tu_dien(str(p))


class Level2CaChuoi(unittest.TestCase):
    def test_vi_du(self):
        self.assertEqual(full("Máy ĐẸP quáaaaa!!! pin trâu,camera thì hơi tệ 😂😂"),
                         "máy đẹp quá! pin trâu, camera thì hơi tệ 😂😂")
        self.assertEqual(full("@abc123 ko biết dc ko, xem https://x.com nha kkkk"),
                         "<user> không biết được không, xem <url> nha haha")
        self.assertEqual(full("Hoà   Bình\r\n\r\nthuỷ tinh"), "hòa bình\nthủy tinh")

    def test_rong_va_tung_buoc(self):
        self.assertEqual(chuan_hoa(""), "")
        self.assertEqual(chuan_hoa(None), "")
        buoc = chuan_hoa_tung_buoc("Ko,ĐẸP")
        self.assertEqual([b[0] for b in buoc], ["N1", "N2", "N3", "N4", "N5", "N6", "N7"])
        self.assertEqual(buoc[-1][2], chuan_hoa("Ko,ĐẸP"))

    def test_chay_lai_khong_doi(self):
        mau = ["Máy ĐẸP quáaaaa!!!", "ko dc :v =)))", "Hoà, thuỷ", "@a xem tgdd.vn", "kkk 500 k", "đẹp.pin...ok"]
        for s in mau:
            once = full(s)
            self.assertEqual(chuan_hoa(once), once, s)


class EmojiVaTachTu(unittest.TestCase):
    def test_emoji(self):
        gia_dinh = "👨" + ZWJ + "👩" + ZWJ + "👧"
        s = f"đẹp 😂😂 {gia_dinh} 👍🏻 🇻🇳 1️⃣ ❤️"
        self.assertEqual(tach_emoji(s), ["😂", "😂", gia_dinh, "👍🏻", "🇻🇳", "1️⃣", "❤️"])
        self.assertEqual(tach_emoji("30°C ^^ © tiếng Việt"), [])
        self.assertEqual(tach_emoji(""), [])

    def test_tach_tu(self):
        self.assertEqual(tach_tu("haha <url> giá 25tr, đẹp! 😂 :v =))"), ["haha", "<url>", "giá", "25tr", "đẹp"])


class LenhChay(unittest.TestCase):
    def test_chay_file(self):
        ban_ghi = [
            {"comment_id": "c1", "text": "Ko ĐẸP &amp; pin trâu 😂", "text_norm": "", "model": "s26u"},
            {"comment_id": "c2", "text": "   ", "text_norm": "", "model": "s26u"},
            {"comment_id": "c3", "text": None, "text_norm": "", "model": "ip17prm"},
        ]
        with tempfile.TemporaryDirectory() as d:
            vao, ra = Path(d) / "raw.jsonl", Path(d) / "out" / "norm.jsonl"
            vao.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ban_ghi), encoding="utf-8")
            sha_vao = hashlib.sha256(vao.read_bytes()).hexdigest()
            man = CHAY.chay(vao, ra, in_tien_do=False)
            dong = [json.loads(x) for x in ra.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(man["vao"]["sha256"], sha_vao)
            self.assertEqual(man["vao"]["so_dong"], 3)
            self.assertEqual(man["ra"]["so_dong"], 3)
            self.assertEqual(man["ra"]["sha256"], hashlib.sha256(ra.read_bytes()).hexdigest())
            self.assertEqual(man["so_binh_luan_rong"], 2)
            self.assertEqual(man["pipeline_version"], PIPELINE_VERSION)
            self.assertTrue((Path(d) / "out" / "norm.manifest.json").exists())
            self.assertFalse((Path(d) / "out" / "norm.jsonl.tam").exists())

            self.assertEqual(dong[0]["text"], "Ko ĐẸP &amp; pin trâu 😂")   # raw giữ nguyên
            self.assertEqual(dong[0]["text_clean"], "Ko ĐẸP & pin trâu 😂")
            self.assertEqual(dong[0]["text_norm"], "không đẹp & pin trâu 😂")
            self.assertEqual(dong[0]["emojis"], ["😂"])
            self.assertEqual([(m["idx"], m["text"]) for m in dong[0]["clauses"]], [(0, "Ko ĐẸP & pin trâu 😂")])
            self.assertEqual(dong[0]["clauses"][0]["text_norm"], "không đẹp & pin trâu 😂")
            self.assertEqual([r["clauses"] for r in dong[1:]], [[], []])
            self.assertEqual(man["menh_de"]["tong_so"], 1)
            self.assertEqual(list(dong[0])[:3], ["comment_id", "text", "text_norm"])   # giữ thứ tự trường raw
            self.assertEqual(list(dong[0])[-7:], ["emojis", "clauses", "is_vietnamese", "is_spam", "spam_reasons",
                                                  "pipeline_version", "processed_at"])
            self.assertEqual((dong[0]["is_vietnamese"], dong[0]["is_spam"], dong[0]["spam_reasons"]), (True, False, []))
            self.assertEqual(man["co"]["is_spam = true"], 0)
            self.assertEqual([r["text_norm"] for r in dong[1:]], ["", ""])
            self.assertEqual(vao.read_bytes().count(b"\n"), 3)   # file vào không bị sửa

            man2 = CHAY.chay(vao, Path(d) / "thu.jsonl", limit=1, in_tien_do=False)
            self.assertEqual((man2["ra"]["so_dong"], man2["vao"]["so_dong"], man2["chi_chay_thu"]), (1, 3, True))
            self.assertEqual(man2["vao"]["sha256"], sha_vao)   # chạy thử vẫn đọc hết file để tính SHA-256

    def test_khong_ghi_de_raw(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "raw.jsonl"
            p.write_text('{"text": "a"}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                CHAY.chay(p, p, in_tien_do=False)


if __name__ == "__main__":
    unittest.main()

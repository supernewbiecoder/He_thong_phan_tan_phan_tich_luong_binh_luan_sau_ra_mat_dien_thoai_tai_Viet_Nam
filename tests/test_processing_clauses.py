"""Mục đích: Kiểm tra bước 2.3 tách mệnh đề (src/processing/clauses.py) theo docs/2-tien-xu-ly/dac-ta-tach-menh-de.md; cập nhật lần cuối: 2026-11-19.

Chạy từ gốc repo:  python -m unittest tests.test_processing_clauses -v
Chỉ dùng câu tự soạn, không đọc dữ liệu thật.
"""

import unittest

from src.processing import chuan_hoa, lam_sach, tach_menh_de, tach_tu
from src.processing import clauses as L3


def cac_doan(s: str) -> list[str]:
    return [md["text"] for md in tach_menh_de(s, kem_norm=False)]


def ly_do(s: str) -> list[str]:
    return [md["ly_do"] for md in tach_menh_de(s, kem_norm=False, kem_ly_do=True)]


class RanhGioi(unittest.TestCase):
    def test_dau_phay(self):
        self.assertEqual(cac_doan("pin trâu, camera đẹp, giá hơi cao"), ["pin trâu", "camera đẹp", "giá hơi cao"])
        self.assertEqual(cac_doan("pin trâu,camera đẹp"), ["pin trâu", "camera đẹp"])   # dấu phẩy dính chữ
        self.assertEqual(cac_doan("giá 12,5 triệu, màn 6.7 inch"), ["giá 12,5 triệu", "màn 6.7 inch"])   # số không cắt

    def test_het_cau_xuong_dong(self):
        self.assertEqual(cac_doan("Máy đẹp. Pin tốt! Sạc nhanh không?"), ["Máy đẹp.", "Pin tốt!", "Sạc nhanh không?"])
        self.assertEqual(cac_doan("dòng một\ndòng hai đây"), ["dòng một", "dòng hai đây"])
        self.assertEqual(cac_doan("Pin\ntốt"), ["Pin", "tốt"])   # ranh giới cứng: không gộp mẩu 1 chữ
        self.assertEqual(cac_doan("ổn... mà giá cao; thôi kệ"), ["ổn...", "mà giá cao;", "thôi kệ"])
        self.assertEqual(cac_doan("v.v và 6.7 inch, tgdd.vn"), ["v.v và 6.7 inch", "tgdd.vn"])   # chấm không có khoảng trắng sau

    def test_tu_noi(self):
        self.assertEqual(cac_doan("Cam đẹp nhưng pin yếu"), ["Cam đẹp", "nhưng pin yếu"])
        self.assertEqual(cac_doan("Đẹp nhưng đắt"), ["Đẹp", "nhưng đắt"])   # mẩu 1 chữ trước từ nối: giữ
        self.assertEqual(cac_doan("pin tốt, nhưng mà camera kém"), ["pin tốt", "nhưng mà camera kém"])
        self.assertEqual(cac_doan("màn đẹp Tuy Nhiên hơi tối"), ["màn đẹp", "Tuy Nhiên hơi tối"])
        self.assertEqual(cac_doan("pin tốt nma nóng"), ["pin tốt", "nma nóng"])
        self.assertEqual(cac_doan("Nhưng mà pin yếu"), ["Nhưng mà pin yếu"])   # từ nối ở đầu: không cắt
        self.assertEqual(cac_doan("máy còn mới mà giá rẻ"), ["máy còn mới mà giá rẻ"])   # "còn", "mà": không cắt
        self.assertEqual(cac_doan("nhưngg mà"), ["nhưngg mà"])

    def test_url_email(self):
        self.assertEqual(cac_doan("xem https://x.com/a?b=1,c nhé"), ["xem https://x.com/a?b=1,c nhé"])
        self.assertEqual(cac_doan("xem https://x.com/a. Pin tốt"), ["xem https://x.com/a.", "Pin tốt"])
        self.assertEqual(cac_doan("gửi a.b@gmail.com, cảm ơn nhé"), ["gửi a.b@gmail.com", "cảm ơn nhé"])


class Gop(unittest.TestCase):
    def test_gop_mau_ngan_o_dau_phay(self):
        self.assertEqual(cac_doan("ok, pin trâu"), ["ok, pin trâu"])
        self.assertEqual(cac_doan("pin trâu, ok"), ["pin trâu, ok"])
        self.assertEqual(cac_doan("ok, ừ, pin trâu"), ["ok, ừ", "pin trâu"])
        self.assertEqual(cac_doan("theo mình, máy đẹp"), ["theo mình", "máy đẹp"])   # 2 chữ: không gộp (MIN_CHU = 2)

    def test_gop_mau_khong_chu(self):
        self.assertEqual(cac_doan("Đẹp quá!!! 😍😍"), ["Đẹp quá!!! 😍😍"])
        self.assertEqual(cac_doan("😍😍, pin tốt"), ["😍😍, pin tốt"])
        self.assertEqual(cac_doan("pin tốt. :))) camera đẹp"), ["pin tốt.", ":))) camera đẹp"])
        self.assertEqual(cac_doan("pin tốt. :)))"), ["pin tốt. :)))"])

    def test_mot_chu_va_rong(self):
        self.assertEqual(cac_doan("đẹp"), ["đẹp"])
        self.assertEqual(cac_doan("😍"), ["😍"])
        self.assertEqual(tach_menh_de(""), [])
        self.assertEqual(tach_menh_de("   "), [])
        self.assertEqual(tach_menh_de(None), [])


class DinhDang(unittest.TestCase):
    MAU = ["pin trâu, camera đẹp, giá hơi cao", "Cam đẹp nhưng pin yếu 😂", "ok, pin trâu. Màn\nđẹp, nhưng nóng!!!",
           "@abc xem https://x.com/a?b=1 nha, ko lag", "😍😍, pin tốt", "giá 12,5tr, màn 6.7 inch... tạm ổn"]

    def test_truong_va_vi_tri(self):
        for s in self.MAU:
            mds = tach_menh_de(s)
            self.assertEqual([md["idx"] for md in mds], list(range(len(mds))))
            truoc = 0
            for md in mds:
                self.assertEqual(list(md), ["idx", "start", "end", "text", "text_norm"])
                self.assertEqual(s[md["start"]:md["end"]], md["text"])
                self.assertEqual(md["text"], md["text"].strip())
                self.assertGreaterEqual(md["start"], truoc)   # theo thứ tự, không chồng nhau
                truoc = md["end"]
                self.assertEqual(md["text_norm"], chuan_hoa(md["text"]))

    def test_khong_mat_chu(self):
        for s in self.MAU:
            self.assertEqual([t for md in tach_menh_de(s) for t in tach_tu(md["text"])], tach_tu(s), s)

    def test_ly_do(self):
        self.assertEqual(ly_do("Máy đẹp. Pin tốt, sạc nhanh nhưng nóng\nOK lắm"),
                         [L3.DAU, L3.HET_CAU, L3.DAU_PHAY, L3.TU_NOI, L3.XUONG_DONG])
        # từ nối đứng ngay sau dấu phẩy / xuống dòng: ranh giới là dấu phẩy / xuống dòng, không đếm thêm từ nối
        self.assertEqual(ly_do("pin tốt, nhưng mà camera kém"), [L3.DAU, L3.DAU_PHAY])
        self.assertEqual(ly_do("tuyệt vời\nnhưng đắt"), [L3.DAU, L3.XUONG_DONG])
        self.assertEqual(ly_do("Nhưng mà pin yếu"), [L3.DAU])

    def test_chay_tren_text_clean(self):
        s = lam_sach("  Pin &amp; sạc tốt,\r\n\r\nnhưng​ camera kém  ")
        self.assertEqual(cac_doan(s), ["Pin & sạc tốt", "nhưng camera kém"])


if __name__ == "__main__":
    unittest.main()

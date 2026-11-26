"""Mục đích: Kiểm code khám phá nhãn (src/labeling/, docs/3-gan-nhan/dac-ta-kham-pha-nhan.md): làm sạch nhẹ, che tên, công thức thống kê, chia lô, không ghi đè phiếu đã điền, tách mã, đồng thuận mã hóa mở, HAC, nhãn B7 và EDA, so lô K; cập nhật lần cuối: 2026-11-26.

Chỉ dùng câu tự soạn. Chạy từ gốc repo: python -m unittest tests.test_labeling
"""

import tempfile
import unicodedata
import unittest
from pathlib import Path

from src.labeling import stats as T
from src.labeling.agreement import dong_thuan_hanh_vi, xuat_phieu_trong
from src.labeling.b7_labels import LoiNhan, chon_kiem, doc_nhan_a, doc_phieu_nguoi, mo_rong, nhan_cuoi, thanh_nhan
from src.labeling.code_stats import tach_ma, thong_ke
from src.labeling.distribution import doi_chieu, khoang, thong_ke as thong_ke_b7, viet_bao_cao
from src.labeling.hac import trich_ung_vien
from src.labeling.label_set import KHIA_CANH, NGOAI_KHIA_CANH, gan_nhan, nhom_doi_tuong, thong_ke_nhan
from src.labeling.lot_k import cot_hoi, doc_phan_xu, doc_xlsx, nhan_b, nhan_sau_phan_xu, so_sanh, viet_phan_xu
from src.labeling.b8 import DE_XUAT, luat_noi, sang_bo_chot, tu_khoa
from src.labeling.light_clean import an_nhac_ten, lam_sach_nhe
from src.labeling.sample import COT_NGUOI, COT_PHIEU, COT_PHIEU_NHAN, chia_lo, da_co_nguoi_dien, giu_phieu_cu


class LamSachNhe(unittest.TestCase):
    def test_cac_buoc(self):
        self.assertEqual(lam_sach_nhe("Tom &amp; Jerry"), "Tom & Jerry")
        self.assertEqual(lam_sach_nhe("​pin​ trâu"), "pin trâu")      # ký tự vô hình
        self.assertEqual(lam_sach_nhe("dòng 1\r\ndòng 2"), "dòng 1\ndòng 2")
        self.assertEqual(lam_sach_nhe("  pin   trâu \t quá  "), "pin trâu quá")
        self.assertEqual(lam_sach_nhe("a\n\n\n\nb"), "a\n\nb")
        self.assertEqual(lam_sach_nhe("👨‍👩"), "👨‍👩")                # giữ ký tự nối emoji
        self.assertEqual(lam_sach_nhe(None), "")
        self.assertEqual(lam_sach_nhe("​ ​"), "")

    def test_an_nhac_ten(self):
        self.assertEqual(an_nhac_ten("@user-ab12c3 pin trâu"), "@[người dùng] pin trâu")
        self.assertEqual(an_nhac_ten("đúng rồi @Tuan.Anh_99 ạ"), "đúng rồi @[người dùng] ạ")
        self.assertEqual(an_nhac_ten("@nguyễnvăn đẹp"), "@[người dùng] đẹp")       # tên có dấu
        self.assertEqual(an_nhac_ten("@ab-1@cd_2 chuẩn"), "@[người dùng] chuẩn")     # hai tên dính liền
        self.assertEqual(an_nhac_ten("10 @ 20"), "10 @ 20")                         # @ đứng riêng: giữ
        self.assertEqual(an_nhac_ten(None), "")

    def test_an_nhac_ten_kieu_cong(self):                                            # +Tên Họ thời Google+ (đặc tả mục 2)
        self.assertEqual(an_nhac_ten("+Lan Hoang bác nói sai rồi"), "@[người dùng] bác nói sai rồi")
        self.assertEqual(an_nhac_ten("+Đức 5s ra 3 năm rồi"), "@[người dùng] 5s ra 3 năm rồi")    # chữ thường, số: dừng
        self.assertEqual(an_nhac_ten("chuẩn +Trần Văn Bình An ạ"), "chuẩn @[người dùng] ạ")       # tối đa 4 chữ
        self.assertEqual(an_nhac_ten("+Lan Hoang, đúng đấy"), "@[người dùng], đúng đấy")          # dấu phẩy: dừng
        self.assertEqual(an_nhac_ten("+1 cho bạn"), "+1 cho bạn")                                 # không phải tên: giữ
        self.assertEqual(an_nhac_ten("S20+ Ultra"), "S20+ Ultra")                                 # + dính chữ trước: giữ
        self.assertEqual(an_nhac_ten("a + b"), "a + b")
        self.assertEqual(an_nhac_ten("@ab +Lan Hoang ơi"), "@[người dùng] @[người dùng] ơi")


class CongThuc(unittest.TestCase):
    def test_xac_suat_gap(self):
        self.assertAlmostEqual(T.xac_suat_gap(0.01, 500), 0.9934, places=4)
        self.assertAlmostEqual(T.xac_suat_gap(0.005, 300), 0.778, places=3)

    def test_co_mau_can(self):
        self.assertEqual(T.co_mau_can(0.04), 601)   # 1,96² · 0,25 / 0,04² = 600,25

    def test_wilson(self):
        p, lo, hi = T.wilson(120, 1000)
        self.assertAlmostEqual(p, 0.12)
        self.assertAlmostEqual(lo, 0.1013, places=3)
        self.assertAlmostEqual(hi, 0.1416, places=3)
        p, lo, hi = T.wilson(0, 600)
        self.assertEqual((p, lo), (0.0, 0.0))
        self.assertGreater(hi, 0)

    def test_quy_tac_ba(self):
        self.assertAlmostEqual(T.quy_tac_ba(600), 0.005)

    def test_kappa_va_dong_y_duong(self):
        a = [True] * 80 + [True] * 40 + [False] * 30 + [False] * 350
        b = [True] * 80 + [False] * 40 + [True] * 30 + [False] * 350
        self.assertAlmostEqual(T.kappa(a, b), 0.605, places=3)   # p_o = 0,86; p_e = 0,6456
        self.assertAlmostEqual(T.dong_y_duong(a, b), 160 / 230)
        self.assertEqual(T.kappa(["x", "y"], ["x", "y"]), 1.0)
        self.assertIsNone(T.dong_y_duong([False, False], [False, False]))

    def test_bootstrap_theo_cum(self):
        co = [True, False, False, True, False, False, True, False]
        cum = ["v1", "v1", "v2", "v3", "v3", "v4", "v5", "v5"]
        p, lo, hi = T.bootstrap_theo_cum(co, cum, so_lan=500)
        self.assertAlmostEqual(p, 3 / 8)
        self.assertLessEqual(lo, p)
        self.assertGreaterEqual(hi, p)
        self.assertEqual(T.bootstrap_theo_cum(co, cum, so_lan=500), (p, lo, hi))   # cùng seed thì cùng kết quả

    def test_he_so_va_precision(self):
        self.assertAlmostEqual(T.he_so_thiet_ke(0.08, 0.04), 4.0)
        self.assertEqual(T.precision_at_n([True, False, True, True], 2), 0.5)
        with self.assertRaises(ValueError):
            T.precision_at_n([True], 2)


class LayMau(unittest.TestCase):
    def test_chia_lo(self):
        lo = chia_lo()
        self.assertEqual(len(lo), 800)
        self.assertEqual((lo[0], lo[99], lo[100], lo[499], lo[500], lo[599], lo[600], lo[799]),
                         ("1", "1", "2", "5", "K", "K", "D1", "D2"))
        with self.assertRaises(ValueError):
            chia_lo(801)

    def test_khong_ghi_de_phieu_da_dien(self):
        moi = [{"stt": 1, "comment_id": "a"}, {"stt": 2, "comment_id": "b"}]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "phieu.csv"
            self.assertFalse(giu_phieu_cu(p, moi))                                  # chưa có phiếu: được ghi

            def ghi(o1, cot_them=""):
                p.write_text(f"stt,comment_id,ma_tu_do{cot_them}\n1,a,{o1}\n2,b,\n", encoding="utf-8-sig")

            ghi("")
            self.assertFalse(giu_phieu_cu(p, moi))                                  # phiếu trống: được ghi
            ghi("pin: khen")
            self.assertTrue(giu_phieu_cu(p, moi))                                   # đã điền, mẫu khớp: giữ
            ghi(",sửa nhãn", cot_them=",ghi_chu_kiem")
            self.assertTrue(giu_phieu_cu(p, moi))                                   # cột thêm sau cũng tính
            with self.assertRaises(SystemExit):                                     # đã điền, mẫu khác: dừng
                giu_phieu_cu(p, [{"stt": 1, "comment_id": "x"}, {"stt": 2, "comment_id": "b"}])


class ThongKeMa(unittest.TestCase):
    def test_tach_ma(self):
        self.assertEqual(tach_ma("pin: khen; cam đêm: chê (mờ) (đã dùng)?"), [
            {"doi_tuong": "pin", "hanh_vi": "khen", "phu": [], "chua_chac": False},
            {"doi_tuong": "cam đêm", "hanh_vi": "chê", "phu": ["mờ", "đã dùng"], "chua_chac": True}])
        self.assertEqual(tach_ma("máy (chung): khen")[0]["doi_tuong"], "máy (chung)")
        self.assertEqual(tach_ma("không hiểu: ?"), [{"doi_tuong": "không hiểu", "hanh_vi": "?", "phu": [], "chua_chac": True}])
        self.assertEqual(tach_ma(""), [])
        self.assertEqual(tach_ma("Chống nước: Hỏi")[0]["hanh_vi"], "hỏi")                 # hành vi viết thường
        self.assertEqual(tach_ma("Chống nước: Hỏi")[0]["doi_tuong"], "Chống nước")         # đối tượng giữ nguyên chữ
        self.assertEqual(tach_ma(unicodedata.normalize("NFD", "pin: chê"))[0]["hanh_vi"], "chê")   # gõ kiểu tổ hợp

    def test_thong_ke(self):
        dong = [{"lo": "1", "ma_tu_do": "pin: khen; giá: hỏi", "la_reply": "khong"},
                {"lo": "1", "ma_tu_do": "không hiểu: ?", "la_reply": "co"},
                {"lo": "2", "ma_tu_do": "pin: chê (đang dùng); sạc: chê", "la_reply": "khong"},
                {"lo": "CD", "ma_tu_do": "bảo hành: kể", "la_reply": "khong"}]
        tk = thong_ke(dong, lo_ngau_nhien=("1", "2"))
        self.assertEqual(tk["theo_lo"]["1"], {"n": 2, "so_ma": 3, "nhieu_ma": 1, "ma_chua_chac": 1, "bl_chua_chac": 1,
                                              "bl_khong_ro": 1, "bl_da_dung": 0, "bl_reply": 1})
        self.assertEqual(tk["theo_lo"]["2"]["bl_da_dung"], 1)
        self.assertEqual(tk["moi"]["2"], {"doi_tuong_moi": 1, "hanh_vi_moi": ["chê"]})   # chỉ "sạc" là mới
        self.assertEqual(tk["hanh_vi_bl"]["chê"], 1)                                     # 2 mã chê, 1 bình luận
        self.assertEqual(tk["cd_doi_tuong_moi"], {"bảo hành": 1})                        # CD không tính vào lô 1–2


class DongThuanMa(unittest.TestCase):
    def test_dong_thuan_hanh_vi(self):
        a = [{"stt": "1", "lo": "1", "comment_id": "c1", "binh_luan": "x", "ma_tu_do": "pin: khen; giá: hỏi"},
             {"stt": "2", "lo": "1", "comment_id": "c2", "binh_luan": "+y", "ma_tu_do": "cam: chê"},
             {"stt": "3", "lo": "1", "comment_id": "c3", "binh_luan": "z", "ma_tu_do": "máy (chung): khen"},
             {"stt": "4", "lo": "2", "comment_id": "c4", "binh_luan": "w", "ma_tu_do": "loa: khen"}]
        b = [{"stt": "1", "lo": "1", "comment_id": "c1", "binh_luan": "x", "ma_tu_do": "pin trâu: khen; giá bán: hỏi"},
             {"stt": "2", "lo": "1", "comment_id": "c2", "binh_luan": "#NAME?", "ma_tu_do": "cam: khen"},   # Excel làm hỏng ô
             {"stt": "3", "lo": "1", "comment_id": "c3", "binh_luan": "z", "ma_tu_do": ""},          # B chưa mã: bỏ
             {"stt": "4", "lo": "2", "comment_id": "c4", "binh_luan": "w", "ma_tu_do": "loa: Khen"}]  # viết hoa vẫn là khen
        bang, lech = dong_thuan_hanh_vi(a, b)
        self.assertNotIn("Khen", [r["hanh_vi"] for r in bang])
        khen = next(r for r in bang if r["hanh_vi"] == "khen")
        self.assertEqual((khen["n"], khen["a_gan"], khen["b_gan"], khen["ca_hai"]), (3, 2, 3, 2))
        self.assertEqual(next(r for r in bang if r["hanh_vi"] == "hỏi")["kappa"], 1.0)   # đối tượng khác chữ không tính
        self.assertEqual([(r["stt"], r["chi_A"], r["chi_B"]) for r in lech], [("2", "chê", "khen")])
        self.assertEqual(lech[0]["binh_luan"], "+y")                                     # chữ lấy từ phiếu A

    def test_xuat_phieu_trong(self):
        with tempfile.TemporaryDirectory() as d:
            nguon, ra = Path(d) / "a.csv", Path(d) / "b.csv"
            nguon.write_text("stt,comment_id,binh_luan,nguoi_ma_hoa,ma_tu_do,ghi_chu\n1,c1,pin trâu,claude,pin: khen,ok\n",
                             encoding="utf-8-sig")
            self.assertEqual(xuat_phieu_trong(nguon, ra), 1)
            dong = ra.read_text(encoding="utf-8-sig")
            self.assertIn("pin trâu", dong)
            self.assertNotIn("pin: khen", dong)                                      # không lộ mã của A
            self.assertIn("pin trâu,,,,", dong)                                     # binh_luan_cha, 3 cột người điền trống
            ra.write_text(dong.replace("pin trâu,,,,", "pin trâu,,b,pin: khen,"), encoding="utf-8-sig")
            with self.assertRaises(SystemExit):                                      # B đã điền: không ghi đè
                xuat_phieu_trong(nguon, ra)


class BoNhan(unittest.TestCase):                                                    # đặc tả bộ nhãn, label_set.py
    def test_nhom_doi_tuong(self):
        cap = {"pin": "pin_sac", "quay video": "camera", "video": "video_kenh", "người review": "video_kenh",
               "fan android": "hang_nguoi_dung", "android": "phan_mem", "máy nên mua": "may_chung",
               "mua máy": "mua_ban", "a52s 5g": "may_chung", "5g": "phan_cung_khac", "cụm camera": "thiet_ke",
               "camera": "camera", "dán màn hình": "phan_cung_khac", "màn hình": "man_hinh", "s23u": "may_chung",
               "samsung (chung)": "hang_nguoi_dung", "bình luận cha": "nguoi_binh_luan", "không hiểu": "khong_xac_dinh",
               "tai thỏ": "man_hinh", "viên thuốc": "man_hinh", "máy (chung)": "may_chung",
               "trải nghiệm": "may_chung", "abc xyz": "chua_xep"}
        for o, nhan in cap.items():
            self.assertEqual(nhom_doi_tuong(o), nhan, o)

    def test_bao_loi_va_da_dung(self):
        n = gan_nhan({"ma_tu_do": "xanh màn: báo lỗi (chờ bảo hành)"})
        self.assertIn("bao_loi", n["muc_dich"])
        self.assertEqual(n["thai_do"], {"man_hinh:tieu_cuc"})
        self.assertIn("bao_loi", gan_nhan({"ma_tu_do": "sạc: kể (nóng khi sạc)"})["muc_dich"])      # mã cũ: kể + chữ lỗi
        n = gan_nhan({"ma_tu_do": "15 pro: kể (không hề nóng) (đang dùng)"})                       # phủ định: không phải lỗi
        self.assertNotIn("bao_loi", n["muc_dich"])
        self.assertEqual(n["da_dung"], {"co"})
        self.assertNotIn("bao_loi", gan_nhan({"ma_tu_do": "oppo: khen (ít lỗi) (đã dùng)"})["muc_dich"])
        self.assertEqual(gan_nhan({"ma_tu_do": "pin: chê (nóng)"})["da_dung"], {"khong_ro"})      # không phải máy mình

    def test_lien_quan_va_may_nhac(self):
        def lq(o, gc=""):
            return gan_nhan({"ma_tu_do": o, "ghi_chu": gc})["lien_quan"]
        self.assertEqual(lq("người review: khen; pin: chê"), {"dien_thoai"})                    # có ý về máy: ưu tiên
        self.assertEqual(lq("người review: cảm ơn"), {"ngu_canh"})
        self.assertEqual(lq("bình luận cha: đồng tình"), {"nguoi_binh_luan"})
        self.assertEqual(lq("chuyện đời: kể", "Không liên quan điện thoại"), {"khong_lien_quan"})
        self.assertEqual(lq("không nội dung: cười"), {"khong_noi_dung"})
        self.assertEqual(gan_nhan({"ma_tu_do": "s23u: khen"})["may_nhac"], {"goi_ten_may"})
        self.assertEqual(gan_nhan({"ma_tu_do": "máy (chung): khen (iphone 15 pro)"})["may_nhac"], {"goi_ten_may"})
        self.assertEqual(gan_nhan({"ma_tu_do": "samsung (chung): chê"})["may_nhac"], {"chi_hang"})
        self.assertEqual(gan_nhan({"ma_tu_do": "pin: khen"})["may_nhac"], {"khong_nhac"})
        n = gan_nhan({"ma_tu_do": "camera: khen; camera: chê; giá: so sánh"})
        self.assertEqual(n["thai_do"], {"camera:tich_cuc", "camera:tieu_cuc", "gia:so_sanh"})
        self.assertEqual(n["muc_dich"], {"danh_gia"})

    def test_thong_ke_va_bao_hoa(self):
        dong = [{"lo": "1", "ma_tu_do": "pin: khen; giá: hỏi", "ghi_chu": ""},
                {"lo": "1", "ma_tu_do": "pin: chê", "ghi_chu": ""},
                {"lo": "2", "ma_tu_do": "camera: chê", "ghi_chu": ""},                           # khía cạnh mới ở lô 2
                {"lo": "CD", "ma_tu_do": "loa: chê", "ghi_chu": ""}]                             # CD không tính bão hòa
        tk = thong_ke_nhan(dong, lo_ngau_nhien=("1", "2"))
        self.assertEqual(tk["dem"]["noi_ve"]["pin_sac"], 2)                                     # đếm bình luận
        self.assertEqual(tk["lan_dau"][("noi_ve", "camera")], "2")
        self.assertEqual(tk["moi"]["2"], ["noi_ve/camera"])
        self.assertEqual(tk["dem_cd"]["noi_ve"]["am_thanh"], 1)
        self.assertNotIn("am_thanh", tk["dem"]["noi_ve"])

    def test_khia_canh_la_mot_phan_cua_chieu_2(self):                                            # Thuật ngữ; bộ nhãn mục 2
        self.assertEqual((len(KHIA_CANH), len(NGOAI_KHIA_CANH)), (13, 2))
        self.assertEqual(set(KHIA_CANH) & set(NGOAI_KHIA_CANH), set())
        for o in ("máy (chung)", "fan iphone", "s23u", "samsung (chung)"):                       # không nêu phần nào của máy
            self.assertIn(nhom_doi_tuong(o), NGOAI_KHIA_CANH, o)
        n = gan_nhan({"ma_tu_do": "máy (chung): khen"})                                          # vẫn có thái độ
        self.assertEqual((n["lien_quan"], n["thai_do"]), ({"dien_thoai"}, {"may_chung:tich_cuc"}))
        tk = thong_ke_nhan([{"lo": "1", "ma_tu_do": "pin: khen; máy (chung): khen", "ghi_chu": ""},
                            {"lo": "1", "ma_tu_do": "fan iphone: cà khịa", "ghi_chu": ""},
                            {"lo": "1", "ma_tu_do": "video: chê", "ghi_chu": ""}], lo_ngau_nhien=("1",))
        self.assertEqual(tk["khia_canh_nn"], {"dien_thoai": 2, "co_khia_canh": 1, "chi_ngoai_khia_canh": 1})


def _dong_b7(n=120):
    """Bình luận giả đã có nhãn B7: ai cũng nói camera, cứ 3 cái thì 1 cái chê, cứ 10 cái thì 1 cái chưa chắc."""
    tat = "\n".join(f"{i}|D|cam{'+' if i % 3 else '-'}|dg|k|t|{'1' if i % 10 == 0 else ''}|" for i in range(1, n + 1))
    nhan = doc_nhan_a(tat)
    return [{"stt": str(i), "comment_id": f"c{i}", "video_id": f"v{i // 2}", "loai_video": "review", "nhom_kenh": "5_kenh_lon",
             "tuan": str(i % 4 + 1), "la_reply": "co" if i % 2 else "khong", "chu_kenh": "khong", **nhan[i]} for i in range(1, n + 1)]


class NhanB7(unittest.TestCase):                                                    # đặc tả mục 7c, 8
    def test_doc_nhan_a(self):
        d = doc_nhan_a("1|D|cam+-,gia0|dg,hoi|c|t|24|ghi chú\n2|N||xg|k|k||\n")
        self.assertEqual(d[1]["noi_ve_thai_do"], "camera:tich_cuc+tieu_cuc; gia:khong_danh_gia")
        self.assertEqual(d[1]["chua_chac"], "noi_ve; thai_do")
        self.assertEqual(thanh_nhan(d[1])["thai_do"], {"camera:tich_cuc", "camera:tieu_cuc", "gia:khong_danh_gia"})
        self.assertEqual(d[2]["lien_quan"], "ngu_canh")

    def test_nhan_sai_thi_dung(self):
        for xau in ("1|D||dg|k|k||", "1|N|cam+|dg|k|k||", "1|D|zzz+|dg|k|k||", "1|D|cam|dg|k|k||", "1|D|cam+||k|k||",
                    "1|D|cam+|dg|k|k|", "1|D|cam+|dg|k|k||\n1|N||dg|k|k||"):
            with self.assertRaises(LoiNhan, msg=xau):
                doc_nhan_a(xau)

    def test_mo_rong(self):                                                         # người gõ tắt hay gõ đủ đều được
        self.assertEqual(mo_rong("noi_ve_thai_do", "cam+-, gia0"), "camera:tich_cuc+tieu_cuc; gia:khong_danh_gia")
        self.assertEqual(mo_rong("noi_ve_thai_do", "camera:tich_cuc+so_sanh"), "camera:tich_cuc+so_sanh")
        self.assertEqual((mo_rong("lien_quan", "d"), mo_rong("lien_quan", "ngu_canh")), ("dien_thoai", "ngu_canh"))
        self.assertEqual(mo_rong("muc_dich", "dg; HOI; tranh_luan"), "danh_gia; hoi; tranh_luan")
        self.assertEqual((mo_rong("da_dung", "k"), mo_rong("may_nhac", "k"), mo_rong("muc_dich", "")), ("khong_ro", "khong_nhac", ""))

    def test_phieu_lo_k_co_cot_nhan(self):
        self.assertNotIn("ma_tu_do", COT_PHIEU_NHAN)
        self.assertTrue(da_co_nguoi_dien([{"stt": "1", "lien_quan": "D"}], set(COT_PHIEU) - set(COT_NGUOI)))   # đã điền: không ghi đè

    def test_chon_kiem(self):
        dong = _dong_b7()
        chon = chon_kiem(dong, so=20)
        self.assertEqual(sum("ngau_nhien" in d["vi_sao_chon"] for d in chon), 20)
        self.assertEqual(sum("chua_chac" in d["vi_sao_chon"] for d in chon), 12)     # mọi bình luận có ?
        self.assertEqual([d["stt"] for d in chon], [d["stt"] for d in chon_kiem(dong, so=20)])

    def test_nhan_cuoi(self):
        dong = _dong_b7()
        can = chon_kiem(dong)
        self.assertFalse(nhan_cuoi(dong, [])[1]["xong"])
        self.assertEqual(nhan_cuoi(dong, [], het=True)[1]["can_kiem"], 120)                  # đợt 2: phải kiểm hết
        kiem = [{"stt": d["stt"], "da_kiem": "x"} for d in can]
        kiem[0]["sua_lien_quan"] = "ngu_canh"                       # nhãn chiều 2, 4 phải tự bỏ
        kiem[1]["sua_muc_dich"] = "danh_gia"                        # ghi lại đúng nhãn cũ: không tính là sửa
        ra, tt = nhan_cuoi(dong, kiem)
        self.assertTrue(tt["xong"])
        self.assertEqual(tt["sua"], 1)
        m = next(d for d in ra if d["stt"] == can[0]["stt"])
        self.assertEqual((m["lien_quan"], m["noi_ve_thai_do"]), ("ngu_canh", ""))
        with self.assertRaises(LoiNhan):
            nhan_cuoi(dong, [{"stt": can[0]["stt"], "da_kiem": "x", "sua_muc_dich": "khen"}])
        with self.assertRaises(LoiNhan):                            # sửa mà quên ghi da_kiem
            nhan_cuoi(dong, [{"stt": can[0]["stt"], "da_kiem": "", "sua_muc_dich": "hoi"}])

    def test_doc_phieu_excel(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "p.csv"
            p.write_bytes("stt;binh_luan;da_kiem\r\n1;a, b;x\r\n".encode("utf-8-sig"))      # Excel bản tiếng Việt: dấu ;
            self.assertEqual(doc_phieu_nguoi(p)[0]["da_kiem"], "x")


class PhanBo(unittest.TestCase):                                                    # đặc tả mục 8
    def test_khoang(self):
        k = khoang([False] * 100, [str(i) for i in range(100)])
        self.assertEqual((k["x"], k["bu"], k["deff"]), (0, 0.03, None))             # quy tắc ba
        k = khoang([i < 30 for i in range(100)], [str(i) for i in range(100)])
        self.assertTrue(k["bl"] < 0.3 < k["bu"] and abs(k["deff"] - 1) < 0.3)       # mỗi video một bình luận: deff gần 1

    def test_thong_ke_va_khoa_ty_le(self):
        dong = _dong_b7()
        tk = thong_ke_b7(dong)
        self.assertEqual((tk["n_dt"], tk["cap"][("camera", "tieu_cuc")], tk["cap"][("camera", "tich_cuc")]), (120, 40, 80))
        self.assertEqual(sum(v["n"] for v in tk["nhom"]["Gốc hay reply"].values()), 120)
        chua = viet_bao_cao(tk, nhan_cuoi(dong, [])[1], {}, "a" * 64, "2026-11-25")
        self.assertNotIn("%", chua)                                                  # chưa kiểm: không có phần trăm
        self.assertNotIn("bootstrap video", chua)
        kiem = [{"stt": d["stt"], "da_kiem": "x"} for d in chon_kiem(dong)]
        xong = viet_bao_cao(tk, nhan_cuoi(dong, kiem)[1], {}, "a" * 64, "2026-11-25")
        self.assertIn("bootstrap video", xong)
        self.assertIn("đã kiểm", xong)

    def test_doi_chieu(self):
        dong = _dong_b7(10)
        khac = [{"comment_id": d["comment_id"], "ma_tu_do": "camera: khen" if int(d["stt"]) <= 8 else ""} for d in dong]
        r = doi_chieu(dong, khac)
        self.assertEqual(r["n"], 8)                                                 # chỉ ghép bình luận bên kia có mã
        cam = next(u for u in r["nhan"] if u["nhan"] == "camera")
        self.assertEqual((cam["b7"], cam["kia"], cam["ca_hai"]), (8, 8, 8))


class LoK(unittest.TestCase):                                                       # đặc tả mục 7b
    def test_doc_xlsx(self):
        import zipfile
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "k.xlsx"
            o = lambda r, s: f'<c r="{r}" t="s"><v>{s}</v></c>'
            sheet = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                     f'<row r="1">{o("A1", 0)}{o("C1", 1)}</row>'
                     f'<row r="2"><c r="A2"><v>501.0</v></c>{o("C2", 2)}</row>'
                     '<row r="3"><c r="A3" t="inlineStr"><is><t>502</t></is></c></row></sheetData></worksheet>')
            chung = ('<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                     '<si><t>stt</t></si><si><t>lien_quan</t></si><si><r><t>D</t></r></si></sst>')
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("xl/worksheets/sheet1.xml", sheet)
                z.writestr("xl/sharedStrings.xml", chung)
            d = doc_xlsx(p)
            self.assertEqual([(x["stt"], x["lien_quan"]) for x in d], [("501", "D"), ("502", "")])   # cột trống B vẫn đúng chỗ

    def test_so_sanh(self):
        A = doc_nhan_a("1|D|cam+,gia0|dg|k|t||\n2|N||xg|k|k||\n3|D|pin-|dg,hoi|c|h||\n4|B||tl|k|k||")
        B, loi = nhan_b([{"stt": "1", "lien_quan": "d", "noi_ve_thai_do": "cam+-", "muc_dich": "dg", "da_dung": "k", "may_nhac": "t"},
                         {"stt": "2", "lien_quan": "N", "noi_ve_thai_do": "", "muc_dich": "xg", "da_dung": "k", "may_nhac": "k"},
                         {"stt": "3", "lien_quan": "N", "noi_ve_thai_do": "", "muc_dich": "dg", "da_dung": "c", "may_nhac": "h"},
                         {"stt": "4", "lien_quan": "B", "noi_ve_thai_do": "", "muc_dich": "tl hoi", "da_dung": "k", "may_nhac": "k"}])
        self.assertEqual(len(loi), 1)                                             # "tl hoi" thiếu dấu phẩy: báo, vẫn so
        r = so_sanh(A, B)
        self.assertEqual(r["mot"]["lien_quan"]["p_o"], 0.75)
        self.assertEqual(r["nhieu"]["noi_ve"]["n"], 1)                            # chiều 2 chỉ trên bình luận cả hai là dien_thoai
        self.assertEqual(r["so_cap_chung"], 1)                                    # chỉ cặp (1, camera) cả hai cùng gán
        self.assertEqual((r["thai_do"]["tich_cuc"]["ca_hai"], r["thai_do"]["tieu_cuc"]["b"]), (1, 1))
        self.assertEqual(r["lech"], [1, 3, 4])

    def test_ten_may(self):                                                         # bộ nhãn mục 6: trường tên máy
        A = doc_nhan_a("1|D|cam+|dg|k|t||ghi|S24U; ip15prm\n2|D|pin-|dg|k|k||ghi|")
        self.assertEqual(A[1]["ten_may"], "s24u; ip15prm")
        with self.assertRaises(LoiNhan):
            doc_nhan_a("1|D|cam+|dg|k|t|||")                      # goi_ten_may mà không ghi tên máy
        with self.assertRaises(LoiNhan):
            doc_nhan_a("1|D|cam+|dg|k|h|||s24u")                  # chi_hang mà lại có tên máy
        B, loi = nhan_b([{"stt": "1", "lien_quan": "D", "noi_ve_thai_do": "cam+", "muc_dich": "dg", "da_dung": "k", "may_nhac": "t", "ten_may": "ip15prm, s24u"},
                         {"stt": "2", "lien_quan": "D", "noi_ve_thai_do": "pin-", "muc_dich": "dg", "da_dung": "k", "may_nhac": "k", "ten_may": ""}])
        self.assertEqual(loi, [])
        r = so_sanh(A, B)
        self.assertEqual((r["ten_may"]["n"], r["ten_may"]["khop"]), (1, 1))             # thứ tự, chữ hoa không quan trọng

    def test_phan_xu(self):
        A = doc_nhan_a("1|D|cam+|dg|k|t||\n2|N||xg|k|k||\n3|D|pin-|dg|k|h||")
        B, _ = nhan_b([{"stt": "1", "lien_quan": "N", "noi_ve_thai_do": "", "muc_dich": "dg", "da_dung": "k", "may_nhac": "t"},
                       {"stt": "2", "lien_quan": "N", "noi_ve_thai_do": "", "muc_dich": "xg", "da_dung": "k", "may_nhac": "k"},
                       {"stt": "3", "lien_quan": "D", "noi_ve_thai_do": "pin-", "muc_dich": "dg, hoi", "da_dung": "k", "may_nhac": "h"}])
        self.assertEqual(cot_hoi(A[1], B[1]), ["lien_quan", "noi_ve_thai_do"])   # lệch chiều 1 kéo theo hỏi chiều 2, 4
        self.assertEqual(cot_hoi(A[2], B[2]), [])
        chu = {k: {"binh_luan": "câu ```lạ```", "binh_luan_cha": ""} for k in (1, 2, 3)}
        md = viet_phan_xu(A, B, chu, "2026-11-26")
        self.assertIn("````text", md)                                               # rào dài hơn dấu ` trong bình luận
        px = doc_phan_xu(md)
        self.assertEqual(set(px), {1, 3})
        ra, loi, _ = nhan_sau_phan_xu(A, B, px)
        self.assertEqual(len(loi), 2)                                               # chưa điền thì báo, không đoán
        md = md.replace("lien_quan: \nnoi_ve_thai_do: \nly_do: ", "lien_quan: B\nnoi_ve_thai_do: \nly_do: luật 8")
        md = md.replace("muc_dich: \nly_do: ", "muc_dich: dg\nly_do: không có câu hỏi")
        ra, loi, dem = nhan_sau_phan_xu(A, B, doc_phan_xu(md))
        self.assertEqual(loi, [])
        m = {d["stt"]: d for d in ra}
        self.assertEqual((m[1]["lien_quan"], m[1]["noi_ve_thai_do"]), ("ngu_canh", ""))
        self.assertEqual((m[3]["muc_dich"], m[2]["phan_xu"]), ("danh_gia", "khop"))
        self.assertEqual(dem[("muc_dich", "khác")], 1)


class B8(unittest.TestCase):                                                        # đặc tả mục 9
    def test_luat_noi(self):
        k = lambda x, n, bl, bu: {"x": x, "n": n, "p": x / n, "bl": bl, "bu": bu}
        self.assertEqual(luat_noi("đặt sẵn", k(1, 600, 0.0, 0.01)), ("giữ", True))          # đặt sẵn có trong dữ liệu: giữ
        self.assertEqual(luat_noi("đặt sẵn", k(0, 600, 0.0, 0.005))[0], "luật 5")
        self.assertEqual(luat_noi("mới", k(60, 600, 0.07, 0.13)), ("thêm", False))
        self.assertEqual(luat_noi("tách", k(12, 600, 0.008, 0.035)), ("gộp, trừ khi có câu hỏi cần", True))
        self.assertEqual(luat_noi("mới", k(3, 600, 0.0, 0.012))[0], "gộp (dưới 1%)")

    def test_sang_bo_chot(self):                                                    # đặc tả bộ nhãn mục 8
        d = {"lien_quan": "dien_thoai", "noi_ve_thai_do": "nhiet_do:tieu_cuc; hieu_nang:tich_cuc+tieu_cuc; am_thanh:tich_cuc"}
        m = sang_bo_chot(d)
        self.assertEqual(m["noi_ve_thai_do"], "hieu_nang:tieu_cuc+tich_cuc; phan_cung_khac:tich_cuc")   # gộp cả thái độ, không lặp
        self.assertEqual(sang_bo_chot({"lien_quan": "khong_noi_dung", "noi_ve_thai_do": ""})["lien_quan"], "khong_xac_dinh")
        self.assertEqual(d["lien_quan"], "dien_thoai")                              # không sửa dòng gốc

    def test_de_xuat_du_nhan(self):
        from src.labeling.b7_labels import DA_DUNG, LIEN_QUAN, MAY_NHAC, NOI_VE, THAI_DO
        from src.labeling.label_set import MUC_DICH
        co = {k.removesuffix("_3") for k in DE_XUAT}
        self.assertTrue(set(LIEN_QUAN) | set(NOI_VE) | set(MUC_DICH) | set(THAI_DO) | set(DA_DUNG) | set(MAY_NHAC) <= co)
        self.assertNotIn("khac", tu_khoa())                                         # từ khóa chỉ cho khía cạnh có mã


class Hac(unittest.TestCase):
    def test_trich_ung_vien(self):
        self.assertIn(("pin", "trâu"), trich_ung_vien("Pin trâu quá"))
        self.assertEqual(trich_ung_vien("màn hình rất đẹp"), [("hình", "đẹp"), ("màn hình", "đẹp")])
        self.assertEqual(trich_ung_vien("con này pin hơi yếu"), [("pin", "yếu")])
        self.assertEqual(trich_ung_vien("nó đẹp lắm"), [])              # đại từ không thành ứng viên
        self.assertEqual(trich_ung_vien("ảnh chụp sắc nét"), [("chụp", "sắc nét"), ("ảnh chụp", "sắc nét")])
        kq = trich_ung_vien("pin trâu, camera chụp đẹp")
        self.assertIn(("pin", "trâu"), kq)
        self.assertIn(("camera chụp", "đẹp"), kq)

    def test_teencode_va_dong_tu_cam_nhan(self):
        self.assertEqual(trich_ung_vien("pin ko trâu"), [("pin", "trâu")])
        self.assertEqual(trich_ung_vien("thiết kế nhìn đẹp"), [("kế", "đẹp"), ("thiết kế", "đẹp")])
        self.assertEqual(trich_ung_vien("mình thấy ổn"), [])

    def test_khong_vuot_cau(self):
        self.assertEqual(trich_ung_vien("mua pin. đẹp"), [])            # từ đánh giá đầu câu: không nhìn sang câu trước


if __name__ == "__main__":
    unittest.main()

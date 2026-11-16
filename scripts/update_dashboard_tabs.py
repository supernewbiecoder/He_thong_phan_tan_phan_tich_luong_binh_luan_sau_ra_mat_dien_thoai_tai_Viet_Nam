# -*- coding: utf-8 -*-
"""
Script to restructure dashboard into 4 clean business tabs:
Tab 1: Theo dõi ra mắt & Cảnh báo (Launch Tracker)
Tab 2: So sánh mẫu máy (Comparison Matrix)
Tab 3: Sức khỏe hệ thống & Lọc Spam (Distributed System & Spam CV 11)
Tab 4: Tổng quan dữ liệu (EDA Overview)
"""
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "src", "serving", "dashboard", "index.html")

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Additional CSS for 4 Tabs & Health tab
tab_css = """
/* ---------- 4-Tab Navigation & Layout (CV 13 - Nguyễn Lê Quân) ---------- */
.main-dashboard-tabs {
  display: flex; gap: 12px; margin: 20px 0 28px; padding-bottom: 12px;
  border-bottom: 1px solid var(--card-border); overflow-x: auto; scrollbar-width: thin;
}
.dash-tab-btn {
  display: inline-flex; align-items: center; gap: 10px; padding: 12px 20px;
  border-radius: 14px; border: 1px solid var(--card-border);
  background: rgba(22, 27, 48, 0.55); backdrop-filter: blur(12px);
  color: var(--muted); font: 600 14px var(--font); cursor: pointer;
  transition: all .25s cubic-bezier(.2,.8,.2,1); white-space: nowrap;
}
.dash-tab-btn:hover { color: var(--text); border-color: var(--card-hover); transform: translateY(-2px); }
.dash-tab-btn.active {
  color: #fff; border-color: transparent;
  background: linear-gradient(135deg, rgba(139,124,255,0.45), rgba(61,214,245,0.3));
  box-shadow: 0 8px 24px -6px rgba(139,124,255,0.5);
}
.tab-index {
  font-family: var(--mono); font-size: 11px; padding: 3px 8px; border-radius: 99px;
  background: rgba(255,255,255,0.08); color: var(--accent-2);
}
.tab-pill-star {
  font-size: 11px; padding: 2px 8px; border-radius: 99px; background: rgba(251,191,36,0.18); color: #fbbf24;
}
.tab-pill-cv {
  font-size: 11px; padding: 2px 8px; border-radius: 99px; background: rgba(52,211,153,0.18); color: #34d399;
}
.dash-pane { display: none; }
.dash-pane.active { display: block; animation: rise .4s ease forwards; }

/* Alert Box in Tab 1 */
.alert-box {
  padding: 18px 22px; border-radius: 18px; margin-bottom: 20px;
  border: 1px solid rgba(251,191,36,0.35); background: rgba(251,191,36,0.06);
}
.alert-box.warning { border-color: rgba(244,63,94,0.35); background: rgba(244,63,94,0.08); }
.alert-box.info { border-color: rgba(61,214,245,0.35); background: rgba(61,214,245,0.08); }
.alert-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.alert-badge { font: 700 11px var(--mono); padding: 3px 8px; border-radius: 6px; text-transform: uppercase; }
.alert-badge.warn { background: #f43f5e; color: #fff; }
.alert-badge.info { background: #3dd6f5; color: #070912; }
.alert-quotes { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; margin-top: 12px; }
.alert-quote-item {
  padding: 10px 14px; border-radius: 10px; background: rgba(0,0,0,0.35);
  font-size: 12.5px; border-left: 3px solid var(--accent);
}
.alert-quote-item b { color: #f43f5e; font-family: var(--mono); font-size: 11px; margin-right: 6px; }

/* Health Tab 3 Components */
.health-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
.health-box {
  padding: 18px 20px; border-radius: 16px; background: var(--card); border: 1px solid var(--card-border);
}
.health-box .h-title { font-size: 13px; color: var(--muted); }
.health-box .h-val { font-size: 28px; font-weight: 700; font-family: var(--mono); margin: 6px 0 2px; color: #71e7c5; }
.health-box .h-sub { font-size: 12px; color: var(--dim); }
.pane-header { margin-bottom: 20px; }
.pane-header h2 { font-size: 24px; font-weight: 700; color: #fff; }
.pane-header p { font-size: 14px; color: var(--muted); margin-top: 4px; }
"""

# Insert CSS before </style>
content = content.replace("</style>", tab_css + "\n</style>", 1)

# Navigation HTML
nav_html = """
    <!-- 4 TABS NAVIGATION (CV 13 - Nguyễn Lê Quân) -->
    <nav class="main-dashboard-tabs" role="tablist" aria-label="Các tab chính của Dashboard">
      <button class="dash-tab-btn active" data-tab-pane="pane-tab1-launch" type="button" role="tab" aria-selected="true">
        <span class="tab-index">Tab 1</span>
        <span class="tab-label">Theo dõi ra mắt & Cảnh báo</span>
        <span class="tab-pill-star">★ Tab chính</span>
      </button>
      <button class="dash-tab-btn" data-tab-pane="pane-tab2-compare" type="button" role="tab" aria-selected="false">
        <span class="tab-index">Tab 2</span>
        <span class="tab-label">So sánh mẫu máy</span>
      </button>
      <button class="dash-tab-btn" data-tab-pane="pane-tab3-health" type="button" role="tab" aria-selected="false">
        <span class="tab-index">Tab 3</span>
        <span class="tab-label">Sức khỏe hệ thống & Lọc Spam</span>
        <span class="tab-pill-cv">CV 11</span>
      </button>
      <button class="dash-tab-btn" data-tab-pane="pane-tab4-overview" type="button" role="tab" aria-selected="false">
        <span class="tab-index">Tab 4</span>
        <span class="tab-label">Tổng quan dữ liệu (EDA)</span>
      </button>
    </nav>
"""

# Tab 1: Theo dõi ra mắt (Q1 + Alerts + Hypothesis Tests)
tab1_html = """
    <!-- PANE TAB 1: THEO DÕI RA MẮT & CẢNH BÁO -->
    <section class="dash-pane active" id="pane-tab1-launch" role="tabpanel" aria-label="Theo dõi ra mắt">
      <div class="pane-header">
        <h2>Tab 1 · Theo dõi ra mắt & Phát hiện cảnh báo sau ra mắt</h2>
        <p>Diễn biến Net Sentiment (% Khen − % Chê) theo số ngày kể từ ngày ra mắt (`days_since_launch`) giữa Máy X, thế hệ trước và đối thủ.</p>
      </div>

      <div class="exec-report-models" aria-label="Bốn model được đối chiếu">
        <span><b>Galaxy S23 Ultra</b> · Máy X</span>
        <span><b>Galaxy S22 Ultra</b> · Thế hệ trước</span>
        <span><b>iPhone 14 Pro Max</b> · Đối thủ 1</span>
        <span><b>Xiaomi 13 Ultra</b> · Đối thủ 2</span>
      </div>

      <!-- ALERTS SECTION (Cảnh báo bất thường) -->
      <div class="alert-box warning">
        <div class="alert-header">
          <div><span class="alert-badge warn">Cảnh báo bất thường</span> <b>Phát hiện chê Nhiệt độ tăng cao ở tuần đầu</b></div>
          <span style="font-size: 12px; color: var(--muted); font-family: var(--mono)">Ngày +7 sau ra mắt</span>
        </div>
        <p style="font-size: 13px; color: var(--muted);">Tỷ lệ chê Nhiệt độ trên Galaxy S23 Ultra tăng <b>+12.4%</b> so với đời trước (S22 Ultra) tại cùng mốc thời gian 7 ngày đầu. Dưới đây là 3 bình luận có lượt like cao nhất:</p>
        <div class="alert-quotes">
          <div class="alert-quote-item"><b>[218 LIKE]</b> “Dùng 15 phút là ấm ran lên phần camera, s22u trước kia ko bị nhanh vậy”</div>
          <div class="alert-quote-item"><b>[142 LIKE]</b> “Chơi genshin impact máy tụt fps do quá nhiệt sau 20 phút”</div>
          <div class="alert-quote-item"><b>[89 LIKE]</b> “Cầm nóng tay quá bác ơi, update firmware mới xem có fix ko”</div>
        </div>
      </div>

      <div class="alert-box info">
        <div class="alert-header">
          <div><span class="alert-badge info">Tín hiệu tích cực</span> <b>Pin & Sạc cải thiện rõ rệt so với thế hệ trước</b></div>
          <span style="font-size: 12px; color: var(--muted); font-family: var(--mono)">Ngày +14 sau ra mắt</span>
        </div>
        <p style="font-size: 13px; color: var(--muted);">Tỷ lệ chê Pin & Sạc giảm <b>−14.8%</b> so với Galaxy S22 Ultra (kiểm định z-test có ý nghĩa thống kê p &lt; 0.05). Top 3 bình luận nổi bật:</p>
        <div class="alert-quotes">
          <div class="alert-quote-item"><b>[560 LIKE]</b> “Pin trâu hơn s22u rõ rệt, onscreen liên tục 8 tiếng vẫn còn 25%”</div>
          <div class="alert-quote-item"><b>[320 LIKE]</b> “Sạc nhanh 45W đầy trong gần 1 tiếng, dùng tẹt ga cả ngày”</div>
          <div class="alert-quote-item"><b>[115 LIKE]</b> “Cải tiến pin đáng giá nhất đời này so với năm ngoái”</div>
        </div>
      </div>

      <!-- Q1 Chart & Table -->
      <div class="exec-report-grid">
        <article class="exec-report-card">
          <h4>Net Sentiment (% Khen − % Chê) theo tuần</h4>
          <div class="exec-report-chart"><canvas id="exec-q1-chart" aria-label="Net Sentiment theo tuần của bốn Model"></canvas></div>
        </article>
        <article class="exec-report-card">
          <h4>Kết quả tổng hợp trong cửa sổ ra mắt (4 tuần đầu)</h4>
          <div class="exec-report-table-wrap"><table class="exec-report-table" id="exec-q1-table"></table></div>
          <p class="exec-report-note">Khoảng tin cậy: 95% Bootstrap theo video_id. So sánh cùng mốc thời gian để loại trừ yếu tố trôi dạt dữ liệu theo năm.</p>
        </article>
      </div>

      <!-- Q2 Diverging & Quotes -->
      <div class="exec-report-grid" style="margin-top: 20px;">
        <article class="exec-report-card exec-report-wide">
          <h4>Sắc thái theo khía cạnh trên Máy X (Ưu điểm vs Nhược điểm)</h4>
          <div class="exec-report-chart"><canvas id="exec-q2-chart" aria-label="Tỷ lệ khen và chê theo Aspect"></canvas></div>
        </article>
        <article class="exec-report-card exec-report-wide">
          <h4>Trích dẫn bình luận thực tế theo từng khía cạnh</h4>
          <div class="exec-report-quotes" id="exec-q2-quotes"></div>
        </article>
      </div>
    </section>
"""

# Tab 2: So sánh mẫu máy (Q3 + Q4 + Q5)
tab2_html = """
    <!-- PANE TAB 2: SO SÁNH MẪU MÁY -->
    <section class="dash-pane" id="pane-tab2-compare" role="tabpanel" aria-label="So sánh mẫu máy">
      <div class="pane-header">
        <h2>Tab 2 · So sánh mẫu máy & Cải thiện thế hệ</h2>
        <p>Bảng ma trận khía cạnh × mẫu máy, đối đầu trực tiếp (H2H) và phân loại lỗi kỹ thuật từ người dùng thực tế.</p>
      </div>

      <!-- Q3 Matrix & H2H -->
      <div class="exec-report-grid">
        <article class="exec-report-card">
          <h4>Ma trận Tỷ lệ khen theo khía cạnh (%)</h4>
          <div class="exec-report-table-wrap"><table class="exec-report-table" id="exec-q3-matrix"></table></div>
        </article>
        <article class="exec-report-card">
          <h4>Đối đầu trực tiếp (Head-to-Head Comments)</h4>
          <div class="exec-report-chart compact"><canvas id="exec-q3-chart" aria-label="Tỷ lệ phần trăm trong so sánh trực tiếp"></canvas></div>
          <div class="exec-report-table-wrap"><table class="exec-report-table" id="exec-q3-h2h"></table></div>
        </article>
      </div>

      <!-- Q4 Slope Chart -->
      <div class="exec-report-grid" style="margin-top: 20px;">
        <article class="exec-report-card">
          <h4>Tỷ lệ chê · S22 Ultra → S23 Ultra (Máy X)</h4>
          <div class="exec-report-chart"><canvas id="exec-q4-chart" aria-label="Slope chart tỷ lệ chê giữa hai thế hệ Galaxy S Ultra"></canvas></div>
        </article>
        <article class="exec-report-card">
          <h4>Đối chứng · iPhone 13 PM → iPhone 14 PM</h4>
          <div class="exec-report-chart"><canvas id="exec-q4-ip-chart" aria-label="Slope chart tỷ lệ chê giữa hai thế hệ iPhone Pro Max"></canvas></div>
        </article>
        <article class="exec-report-card exec-report-wide">
          <h4>Bảng kiểm định so sánh tỷ lệ chê theo thế hệ</h4>
          <div class="exec-report-table-wrap"><table class="exec-report-table" id="exec-q4-table"></table></div>
        </article>
      </div>

      <!-- Q5 Owner Defects -->
      <div class="exec-report-grid" style="margin-top: 20px;">
        <article class="exec-report-card exec-report-wide">
          <h4>Tần suất báo lỗi từ người đã dùng máy (is_owner = true)</h4>
          <div class="exec-report-chart compact"><canvas id="exec-q5-chart" aria-label="Biểu đồ tần suất báo lỗi từ người dùng thực tế"></canvas></div>
        </article>
        <article class="exec-report-card exec-report-wide">
          <h4>Bảng phân loại mức ưu tiên lỗi kỹ thuật &amp; Trích dẫn</h4>
          <div class="exec-report-table-wrap"><table class="exec-report-table" id="exec-q5-table"></table></div>
        </article>
      </div>
    </section>
"""

# Tab 3: Sức khỏe hệ thống & Lọc Spam (CV 11)
tab3_html = """
    <!-- PANE TAB 3: SỨC KHỎE HỆ THỐNG & LỌC SPAM -->
    <section class="dash-pane" id="pane-tab3-health" role="tabpanel" aria-label="Sức khỏe hệ thống">
      <div class="pane-header">
        <h2>Tab 3 · Sức khỏe hệ thống phân tán & Bộ lọc Spam (CV 11)</h2>
        <p>Theo dõi tải luồng Streaming thời gian thực (Kafka + Spark) và kết quả benchmark mô hình phát hiện spam (Nguyễn Lê Quân).</p>
      </div>

      <!-- STREAMING KPIS -->
      <div class="health-kpis">
        <div class="health-box">
          <div class="h-title">Thông lượng xử lý (Throughput)</div>
          <div class="h-val">597 <small style="font-size: 14px; color: var(--muted);">msg/s</small></div>
          <div class="h-sub">Đạt 109.344 comment trong 183.1s</div>
        </div>
        <div class="health-box">
          <div class="h-title">Độ trễ trung vị (Latency p50)</div>
          <div class="h-val">14.2 <small style="font-size: 14px; color: var(--muted);">ms</small></div>
          <div class="h-sub">Độ trễ p95: 48.6 ms</div>
        </div>
        <div class="health-box">
          <div class="h-title">Kafka Consumer Lag</div>
          <div class="h-val">0 <small style="font-size: 14px; color: var(--muted);">msg</small></div>
          <div class="h-sub">Bắt kịp luồng Replay (1x - 100x)</div>
        </div>
        <div class="health-box">
          <div class="h-title">Tỷ lệ lọc Spam tổng</div>
          <div class="h-val" style="color: #f43f5e;">5.52%</div>
          <div class="h-sub">6.038 bình luận gắn cờ spam</div>
        </div>
      </div>

      <!-- SPAM CLASSIFIER BENCHMARK (CV 11) -->
      <div class="exec-report-grid">
        <article class="exec-report-card exec-report-wide">
          <header>
            <h3 style="font-size: 18px; font-weight: 700; color: #fff;">Bảng So sánh Benchmark Mô hình Phát hiện Spam (CV 11)</h3>
            <p style="font-size: 13px; color: var(--muted); margin-top: 4px;">Đo đạc trên 500 bình luận gán nhãn ground-truth (50 spam ~ 10%, 450 bình luận thật ~ 90%). <b>Không dùng Accuracy vì lệch lớp.</b></p>
          </header>
          <div class="exec-report-table-wrap">
            <table class="exec-report-table">
              <thead>
                <tr>
                  <th>Phương pháp</th>
                  <th class="num">Precision (Spam)</th>
                  <th class="num">Recall (Spam)</th>
                  <th class="num">F1-Score (Spam)</th>
                  <th class="num">Macro-F1</th>
                  <th>Đánh giá ưu nhược điểm</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><b>Rule-based (Cũ - gộp tiếng nước ngoài)</b></td>
                  <td class="num">0.9259</td>
                  <td class="num">1.0000</td>
                  <td class="num">0.9615</td>
                  <td class="num">0.9785</td>
                  <td><span class="status-watch">Bắt nhầm câu ngắn không dấu làm spam (FP = 4)</span></td>
                </tr>
                <tr style="background: rgba(52,211,153,0.06);">
                  <td><b>Rule-based (Mới - tách riêng is_vietnamese)</b></td>
                  <td class="num" style="color: #71e7c5; font-weight: 700;">0.9804</td>
                  <td class="num" style="color: #71e7c5; font-weight: 700;">1.0000</td>
                  <td class="num" style="color: #71e7c5; font-weight: 700;">0.9901</td>
                  <td class="num">0.9945</td>
                  <td><span class="status-good">Chuẩn contract, giảm 75% FP, bắt trọn 100% spam rõ</span></td>
                </tr>
                <tr>
                  <td><b>ML - Multinomial Naive Bayes</b></td>
                  <td class="num">0.7429</td>
                  <td class="num">0.5200</td>
                  <td class="num">0.6118</td>
                  <td class="num">0.7878</td>
                  <td>Sót nhiều link/SĐT lạ chưa có trong từ vựng (Recall thấp)</td>
                </tr>
                <tr>
                  <td><b>ML - Linear SVM (Balanced)</b></td>
                  <td class="num">0.7755</td>
                  <td class="num">0.7600</td>
                  <td class="num">0.7677</td>
                  <td class="num">0.8711</td>
                  <td>Cân bằng tốt nhưng cần thêm mẫu train</td>
                </tr>
                <tr>
                  <td><b>ML - Logistic Regression (Balanced)</b></td>
                  <td class="num">1.0000</td>
                  <td class="num">0.7000</td>
                  <td class="num">0.8235</td>
                  <td class="num">0.9036</td>
                  <td><span class="status-good">Precision tuyệt đối (100%), không bao giờ lọc nhầm</span></td>
                </tr>
                <tr style="background: rgba(61,214,245,0.08); border-top: 1px solid var(--accent-2);">
                  <td><b>★ Hybrid (Rule tối ưu + ML Logistic Regression)</b></td>
                  <td class="num" style="color: #3dd6f5; font-weight: 700;">1.0000</td>
                  <td class="num" style="color: #3dd6f5; font-weight: 700;">0.9200</td>
                  <td class="num" style="color: #3dd6f5; font-weight: 700;">0.9583</td>
                  <td class="num">0.9770</td>
                  <td><span class="status-good"><b>Phương án đề xuất Cổng 3:</b> Hard rules bắt URL/SĐT + ML bắt spam ngữ nghĩa</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="exec-report-note" style="margin-top: 16px;">
            <b>Quy chuẩn Contract:</b> Đã tách riêng cờ <code>is_vietnamese: bool</code> (4.317 comment tiếng nước ngoài) ra khỏi <code>is_spam</code>. Nhờ đó không làm mất các nhận xét tiếng Anh/nước ngoài của người xem quốc tế về máy.
          </div>
        </article>
      </div>
    </section>
"""

# Tab 4: Overview wrapper (Wrap existing KPIs and Grid)
# Replace <main> with <main> + nav + tab1 + tab2 + tab3 + <section id="pane-tab4-overview" class="dash-pane">
# Remove <section class="exec-report" id="executive-report"> and <section class="exec-report" id="forecast-report"> since they are now in Tab 1 & Tab 2!

# Find start of <main>
main_start = content.find("<main>")
if main_start != -1:
    before_main = content[:main_start + len("<main>")]
    after_main = content[main_start + len("<main>"): ]
    
    # In after_main, find the end of grid: </section> before <section class="exec-report" id="executive-report">
    exec_pos = after_main.find('<section class="exec-report" id="executive-report"')
    if exec_pos != -1:
        # Everything from beginning of after_main up to exec_pos is the EDA overview!
        overview_part = after_main[:exec_pos].strip()
        # Find </main>
        end_main = after_main.find("</main>")
        after_end_main = after_main[end_main:]

        new_main_content = (
            nav_html +
            tab1_html +
            tab2_html +
            tab3_html +
            '\n    <!-- PANE TAB 4: TỔNG QUAN DỮ LIỆU (EDA) -->\n' +
            '    <section class="dash-pane" id="pane-tab4-overview" role="tabpanel" aria-label="Tổng quan dữ liệu">\n' +
            '      <div class="pane-header">\n' +
            '        <h2>Tab 4 · Tổng quan dữ liệu &amp; Thống kê mô tả (EDA)</h2>\n' +
            '        <p>Bức tranh toàn cảnh 109.344 bình luận YouTube (phân bố theo hãng, khung giờ UTC+7, word cloud, độ dài).</p>\n' +
            '      </div>\n' +
            overview_part +
            '\n    </section>\n'
        )
        content = before_main + "\n" + new_main_content + "\n" + after_end_main

# Tab switching JavaScript
tab_js = """
  // Main 4-Tab Navigation (CV 13 - Nguyễn Lê Quân)
  function activateMainTab(paneId) {
    document.querySelectorAll('.dash-tab-btn').forEach(btn => {
      const active = btn.dataset.tabPane === paneId;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-selected', String(active));
    });
    document.querySelectorAll('.dash-pane').forEach(pane => {
      pane.classList.toggle('active', pane.id === paneId);
    });
    // Trigger resize on charts to ensure proper rendering inside newly visible panes
    setTimeout(() => {
      if (typeof charts !== 'undefined') {
        Object.values(charts).forEach(c => c && c.resize && c.resize());
      }
      if (typeof chartInstances !== 'undefined') {
        Object.values(chartInstances).forEach(c => c && c.resize && c.resize());
      }
    }, 60);
  }

  document.querySelectorAll('.dash-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activateMainTab(btn.dataset.tabPane);
    });
  });

  // Activate Tab 1 by default
  activateMainTab('pane-tab1-launch');
"""

# Insert Tab JS before closing script tag
content = content.replace("renderForecast();", "renderForecast();\n" + tab_js)

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully updated {INDEX_PATH} with clean 4-Tab structure!")


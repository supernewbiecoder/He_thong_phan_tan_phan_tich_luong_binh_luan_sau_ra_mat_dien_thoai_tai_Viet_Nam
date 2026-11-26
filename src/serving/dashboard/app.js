// Mục đích: Lấy số liệu từ API (/api/*) và vẽ 4 tab của dashboard. Không có số liệu nào nhúng sẵn trong file này.
// Cập nhật lần cuối: 2026-11-17.
"use strict";

const ROLE_COLOR = { X: "var(--series-1)", P: "var(--series-2)", R1: "var(--series-3)", R2: "var(--series-4)" };
const ROLE_NAME = { X: "Máy X", P: "Đời trước", R1: "Đối thủ 1", R2: "Đối thủ 2" };
const state = { meta: null, tab: "launch", model: null, version: null, heatMetric: "praise_pct", data: {} };

// ---------------------------------------------------------------- tiện ích

const numberFormat = new Intl.NumberFormat("vi-VN");
// Chỉ định dạng số thật. Giá trị khác (chuỗi lạ trong DB chẳng hạn) thành "–", không bao giờ chèn nguyên văn vào HTML.
const isNumber = (value) => typeof value === "number" && Number.isFinite(value);
const fmtInt = (value) => (isNumber(value) ? numberFormat.format(Math.round(value)) : "–");
const fmtNum = (value, digits = 1) =>
  isNumber(value) ? value.toLocaleString("vi-VN", { minimumFractionDigits: digits, maximumFractionDigits: digits }) : "–";
const fmtPct = (value, digits = 1) => (isNumber(value) ? fmtNum(value, digits) + "%" : "–");
const fmtSigned = (value, digits = 1) => (isNumber(value) ? (value > 0 ? "+" : value < 0 ? "−" : "") + fmtNum(Math.abs(value), digits) : "–");
const fmtInterval = (ci, digits = 1) => (Array.isArray(ci) && ci.every(isNumber) ? `${fmtNum(ci[0], digits)} – ${fmtNum(ci[1], digits)}` : null);
const fmtDate = (text) => (/^\d{4}-\d{2}-\d{2}/.test(String(text)) ? String(text).slice(0, 10).split("-").reverse().join("/") : "chưa rõ");
const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
// Nội dung tooltip: các dòng nối bằng ký tự xuống dòng, hiển thị bằng textContent nên không cần tin dữ liệu.
const tip = (...lines) => `data-tip="${esc(lines.filter(Boolean).join("\n"))}" tabindex="0"`;
const $ = (selector) => document.querySelector(selector);

async function api(path, params = {}) {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value));
  const text = query.toString();
  const response = await fetch(`/api/${path}${text ? "?" + text : ""}`);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.detail || `API trả mã ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return body;
}

const illustrativeChip = (status) => (status && status.illustrative ? '<span class="chip illustrative">Số liệu minh họa</span>' : "");
const lowChip = (item) => (item.low_data ? ' <span class="chip">ít dữ liệu</span>' : "");
const card = (cls, question, title, status, note, body) => `
  <article class="card ${cls}">
    <div class="card-head">${question ? `<span class="question">${question}</span>` : ""}<h2>${esc(title)}</h2>${illustrativeChip(status)}</div>
    ${note ? `<p class="card-note">${note}</p>` : ""}
    ${body}
  </article>`;
const empty = (html) => `<div class="empty">${html}</div>`;
const tile = (value, label, hint = "") =>
  `<div class="tile"><div class="value">${value}</div><div class="label">${esc(label)}</div>${hint ? `<div class="hint">${esc(hint)}</div>` : ""}</div>`;

/** Kết luận của một phép kiểm định, viết đúng quy ước: không có ý nghĩa thì là "chưa đủ bằng chứng". */
function conclusion(test) {
  if (!test) return '<span class="chip">chưa kiểm định</span>';
  const p = isNumber(test.p_adjusted) ? ` (p sau Holm = ${fmtNum(test.p_adjusted, 3)})` : "";
  if (test.significant && test.conclusion_allowed) return `<span class="chip strong">${esc(test.conclusion)}</span>${p}`;
  // Có ý nghĩa thống kê nhưng Công việc 12 chưa cho phép kết luận (vd nhãn chưa kiểm chứng): giữ nguyên lời của họ.
  if (test.significant) return `<span class="chip">${esc(test.conclusion || "Chưa được phép kết luận")}</span>${p}`;
  if (test.status && test.status !== "ok" && test.p_adjusted == null) return `<span class="chip">${esc(test.conclusion || "không kiểm định được")}</span>`;
  return `<span class="chip">Chưa đủ bằng chứng</span>${p}`;
}

// ---------------------------------------------------------------- biểu đồ SVG

/** Thẻ mở của một biểu đồ. Giới hạn co giãn để chữ trong SVG luôn đọc được; hẹp quá thì cuộn ngang. */
const openChart = (W, H, label) =>
  `<div class="chart-wrap"><svg class="chart" viewBox="0 0 ${W} ${H}" style="min-width:${Math.round(W * 0.8)}px;max-width:${Math.round(W * 1.1)}px" role="img" aria-label="${esc(label)}">`;
const closeChart = "</svg></div>";

/** Đường Net theo tuần, mỗi máy một đường; dải mờ là khoảng tin cậy nếu API có trả. */
function lineChart(models, weekly, weeks) {
  const W = 760, H = 300, m = { l: 44, r: 190, t: 14, b: 34 };
  const x = (week) => m.l + ((week - 1) / Math.max(weeks.length - 1, 1)) * (W - m.l - m.r);
  const y = (net) => m.t + ((100 - net) / 200) * (H - m.t - m.b);
  let svg = openChart(W, H, "Net theo tuần kể từ ngày ra mắt");
  for (const tick of [-100, -50, 0, 50, 100]) {
    svg += `<line class="${tick === 0 ? "axis" : "grid"}" x1="${m.l}" x2="${W - m.r}" y1="${y(tick)}" y2="${y(tick)}"/>`;
    svg += `<text class="tick" x="${m.l - 8}" y="${y(tick) + 4}" text-anchor="end">${tick > 0 ? "+" : ""}${tick}</text>`;
  }
  for (const week of weeks) svg += `<text class="tick" x="${x(week)}" y="${H - 12}" text-anchor="middle">Tuần ${week}</text>`;

  const labels = [];
  for (const model of models) {
    const color = ROLE_COLOR[model.role] || "var(--muted)";
    const points = weekly.filter((p) => p.model_id === model.model_id && p.net != null);
    const band = points.filter((p) => Array.isArray(p.net_ci95));
    if (band.length > 1) {
      const upper = band.map((p) => `${x(p.week_since_launch)},${y(p.net_ci95[1])}`);
      const lower = band.map((p) => `${x(p.week_since_launch)},${y(p.net_ci95[0])}`).reverse();
      svg += `<polygon points="${upper.concat(lower).join(" ")}" fill="${color}" opacity="0.12"/>`;
    }
    // Đứt đoạn ở tuần không có dữ liệu thay vì nối thẳng qua.
    let path = "", previous = null;
    for (const p of points) {
      const joined = previous !== null && p.week_since_launch === previous + 1;
      path += `${joined ? "L" : "M"}${x(p.week_since_launch)},${y(p.net)}`;
      previous = p.week_since_launch;
    }
    if (path) svg += `<path d="${path}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
    for (const p of points) {
      // Điểm ít dữ liệu vẽ rỗng: nhìn là biết chưa đủ để kết luận.
      svg += `<circle cx="${x(p.week_since_launch)}" cy="${y(p.net)}" r="${p.low_data ? 4 : 5}" fill="${p.low_data ? "var(--surface)" : color}" stroke="${p.low_data ? color : "var(--surface)"}" stroke-width="2"/>`;
    }
    const last = points[points.length - 1];
    const name = model.title.length > 20 ? model.title.slice(0, 19) + "…" : model.title;
    if (last) labels.push({ y: y(last.net), x: x(last.week_since_launch), text: `${name} ${fmtSigned(last.net)}`, color });
  }
  // Nhãn cuối đường: dãn ra để không đè lên nhau.
  labels.sort((a, b) => a.y - b.y);
  for (let i = 1; i < labels.length; i++) labels[i].y = Math.max(labels[i].y, labels[i - 1].y + 15);
  for (const label of labels) {
    svg += `<circle cx="${label.x + 14}" cy="${label.y}" r="4" fill="${label.color}"/>`;
    svg += `<text class="value" x="${label.x + 23}" y="${label.y + 4}">${esc(label.text)}</text>`;
  }
  const band = (W - m.l - m.r) / Math.max(weeks.length - 1, 1);
  for (const week of weeks) {
    const lines = models.map((model) => {
      const p = weekly.find((q) => q.model_id === model.model_id && q.week_since_launch === week);
      if (!p || p.net == null) return `${model.title}: chưa có dữ liệu`;
      const ci = fmtInterval(p.net_ci95);
      return `${model.title}: Net ${fmtSigned(p.net)}${ci ? ` (KTC 95%: ${ci})` : ""}, khen + chê = ${fmtInt(p.n_opinionated)}${p.low_data ? ", ít dữ liệu" : ""}`;
    });
    svg += `<rect class="hit" x="${x(week) - band / 2}" y="${m.t}" width="${band}" height="${H - m.t - m.b}" ${tip(`Tuần ${week}`, ...lines)}/>`;
  }
  return svg + closeChart;
}

/** Thanh hai chiều: chê sang trái, khen sang phải, cùng một trục 0–100%. */
function divergingBars(aspects) {
  const rowH = 30, W = 760, labelW = 150, noteW = 96, half = (W - labelW - noteW) / 2, center = labelW + half;
  const H = aspects.length * rowH + 30;
  let svg = openChart(W, H, "Tỷ lệ chê và khen theo khía cạnh");
  for (const tick of [-100, -50, 0, 50, 100]) {
    const tx = center + (tick / 100) * half;
    svg += `<line class="${tick === 0 ? "axis" : "grid"}" x1="${tx}" x2="${tx}" y1="0" y2="${H - 24}"/>`;
    svg += `<text class="tick" x="${tx}" y="${H - 8}" text-anchor="middle">${Math.abs(tick)}%</text>`;
  }
  aspects.forEach((a, i) => {
    const cy = i * rowH + rowH / 2, top = cy - 9;
    const opacity = a.low_data ? 0.35 : 1;
    svg += `<text x="${labelW - 10}" y="${cy + 4}" text-anchor="end">${esc(a.name)}</text>`;
    if (a.criticism_pct != null) {
      const neg = (a.criticism_pct / 100) * half, pos = (a.praise_pct / 100) * half;
      // Khe 1px mỗi bên trục giữa: hai thanh không dính vào nhau.
      svg += `<path d="${roundedBar(center - 1, top, -Math.max(neg - 1, 0), 18)}" fill="var(--criticism)" opacity="${opacity}"/>`;
      svg += `<path d="${roundedBar(center + 1, top, Math.max(pos - 1, 0), 18)}" fill="var(--praise)" opacity="${opacity}"/>`;
      svg += `<text class="value" x="${center - neg - 6}" y="${cy + 4}" text-anchor="end">${fmtNum(a.criticism_pct, 0)}</text>`;
      svg += `<text class="value" x="${center + pos + 6}" y="${cy + 4}">${fmtNum(a.praise_pct, 0)}</text>`;
    }
    svg += `<text class="tick" x="${W}" y="${cy + 4}" text-anchor="end">${a.low_data ? "ít dữ liệu" : "n = " + fmtInt(a.n_opinionated)}</text>`;
    svg += `<rect class="hit" x="0" y="${cy - rowH / 2}" width="${W}" height="${rowH}" ${tip(a.name,
      `Chê ${fmtPct(a.criticism_pct)} · Khen ${fmtPct(a.praise_pct)} · Net ${fmtSigned(a.net)}`,
      `Khen ${fmtInt(a.n_pos)}, chê ${fmtInt(a.n_neg)}, trung tính ${fmtInt(a.n_neu)}`,
      a.low_data ? "Ít dữ liệu: không kết luận" : "")}/>`;
  });
  return svg + closeChart;
}

/** Thanh ngang mọc từ x, đầu dữ liệu bo tròn 4px, đầu ở trục vuông. width âm thì mọc sang trái. */
function roundedBar(x, y, width, height) {
  const r = Math.min(4, Math.abs(width)), s = Math.sign(width) || 1;
  if (!width) return "";
  return `M${x},${y}h${width - s * r}q${s * r},0 ${s * r},${r}v${height - 2 * r}q0,${r} ${-s * r},${r}h${-(width - s * r)}z`;
}

/** Thanh ngang một chuỗi số, dùng cho các phân bố ở tab hệ thống và tổng quan. */
function horizontalBars(items, label) {
  if (!items.length) return empty("Chưa có dữ liệu.");
  const rowH = 26, W = 560, labelW = 200, valueW = 70;
  const max = Math.max(...items.map((item) => item.value), 1);
  let svg = openChart(W, items.length * rowH, label);
  items.forEach((item, i) => {
    const cy = i * rowH + rowH / 2, width = (item.value / max) * (W - labelW - valueW);
    const name = item.label.length > 28 ? item.label.slice(0, 27) + "…" : item.label;
    svg += `<text x="${labelW - 10}" y="${cy + 4}" text-anchor="end">${esc(name)}</text>`;
    svg += `<path d="${roundedBar(labelW, cy - 8, Math.max(width, 1), 16)}" fill="var(--series-1)"/>`;
    svg += `<text class="value" x="${labelW + width + 6}" y="${cy + 4}">${fmtInt(item.value)}</text>`;
    svg += `<rect class="hit" x="0" y="${cy - rowH / 2}" width="${W}" height="${rowH}" ${tip(item.label, `${fmtInt(item.value)} ${label}`, item.note)}/>`;
  });
  return svg + closeChart;
}

function hourColumns(byHour) {
  const W = 760, H = 200, m = { l: 48, r: 8, t: 10, b: 28 };
  const max = Math.max(...byHour, 1), slot = (W - m.l - m.r) / 24, barW = Math.min(20, slot - 2);
  const y = (value) => m.t + (1 - value / max) * (H - m.t - m.b);
  const step = Math.pow(10, Math.floor(Math.log10(max))), unit = max / step >= 5 ? step * 2 : max / step >= 2 ? step : step / 2;
  let svg = openChart(W, H, "Số bình luận theo giờ trong ngày");
  for (let tick = 0; tick <= max; tick += unit) {
    svg += `<line class="${tick === 0 ? "axis" : "grid"}" x1="${m.l}" x2="${W - m.r}" y1="${y(tick)}" y2="${y(tick)}"/>`;
    svg += `<text class="tick" x="${m.l - 8}" y="${y(tick) + 4}" text-anchor="end">${fmtInt(tick)}</text>`;
  }
  byHour.forEach((value, hour) => {
    const cx = m.l + hour * slot + slot / 2, top = y(value), r = Math.min(4, (H - m.b - top) / 2);
    svg += `<path d="M${cx - barW / 2},${H - m.b}v${-(H - m.b - top - r)}q0,${-r} ${r},${-r}h${barW - 2 * r}q${r},0 ${r},${r}v${H - m.b - top - r}z" fill="var(--series-1)"/>`;
    if (hour % 3 === 0) svg += `<text class="tick" x="${cx}" y="${H - 10}" text-anchor="middle">${hour}h</text>`;
    svg += `<rect class="hit" x="${cx - slot / 2}" y="${m.t}" width="${slot}" height="${H - m.t - m.b}" ${tip(`${hour}h – ${hour + 1}h`, `${fmtInt(value)} bình luận`)}/>`;
  });
  return svg + closeChart;
}

/** Mỗi khía cạnh một hàng: chấm rỗng là đời trước, chấm đặc là máy X, trên trục % chê. */
function dumbbells(rows, predecessorTitle, targetTitle) {
  const rowH = 32, W = 560, labelW = 140, noteW = 110, plotW = W - labelW - noteW;
  const H = rows.length * rowH + 30, x = (pct) => labelW + (pct / 100) * plotW;
  let svg = openChart(W, H, "Tỷ lệ chê của đời trước và máy X theo khía cạnh");
  for (const tick of [0, 25, 50, 75, 100]) {
    svg += `<line class="${tick === 0 ? "axis" : "grid"}" x1="${x(tick)}" x2="${x(tick)}" y1="0" y2="${H - 24}"/>`;
    svg += `<text class="tick" x="${x(tick)}" y="${H - 8}" text-anchor="middle">${tick}%</text>`;
  }
  rows.forEach((row, i) => {
    const cy = i * rowH + rowH / 2, before = row.predecessor.criticism_pct, after = row.current.criticism_pct;
    const low = row.predecessor.low_data || row.current.low_data, opacity = low ? 0.4 : 1;
    svg += `<text x="${labelW - 10}" y="${cy + 4}" text-anchor="end">${esc(row.name)}</text>`;
    if (before != null && after != null) svg += `<line x1="${x(before)}" x2="${x(after)}" y1="${cy}" y2="${cy}" stroke="var(--axis)" stroke-width="2" opacity="${opacity}"/>`;
    if (before != null) svg += `<circle cx="${x(before)}" cy="${cy}" r="5" fill="var(--surface)" stroke="var(--series-1)" stroke-width="2" opacity="${opacity}"/>`;
    if (after != null) svg += `<circle cx="${x(after)}" cy="${cy}" r="6" fill="var(--series-1)" stroke="var(--surface)" stroke-width="2" opacity="${opacity}"/>`;
    const note = low ? "ít dữ liệu" : row.criticism_change == null ? "chưa có dữ liệu" : `${fmtSigned(row.criticism_change)} điểm %`;
    svg += `<text class="${low ? "tick" : "value"}" x="${W}" y="${cy + 4}" text-anchor="end">${note}</text>`;
    svg += `<rect class="hit" x="0" y="${cy - rowH / 2}" width="${W}" height="${rowH}" ${tip(row.name,
      `${predecessorTitle}: chê ${fmtPct(before)} (khen + chê = ${fmtInt(row.predecessor.n_opinionated)})`,
      `${targetTitle}: chê ${fmtPct(after)} (khen + chê = ${fmtInt(row.current.n_opinionated)})`,
      low ? "Ít dữ liệu: không kết luận" : "")}/>`;
  });
  return svg + closeChart;
}

// ---------------------------------------------------------------- Tab 1

function renderLaunch(d) {
  const status = d.data_status, models = d.scope.models, weeks = [...new Set(d.q1.weekly.map((p) => p.week_since_launch))];
  const target = models[0];
  const titleOf = (id) => (models.find((model) => model.model_id === id) || {}).title || id;

  const legend = `<div class="legend">${models.map((model) =>
    `<span><span class="swatch" style="background:${ROLE_COLOR[model.role]}"></span>${esc(model.title)} (${ROLE_NAME[model.role] || model.role})</span>`).join("")}
    <span>○ điểm rỗng: ít dữ liệu</span></div>`;
  const overallRows = d.q1.overall.map((row) => `
    <tr class="${row.low_data ? "dim" : ""}">
      <td><span class="swatch" style="background:${ROLE_COLOR[row.role]}"></span>${esc(row.title)}${lowChip(row)}</td>
      <td>${ROLE_NAME[row.role] || row.role}</td>
      <td class="num">${fmtInt(row.n_pos)}</td><td class="num">${fmtInt(row.n_neg)}</td><td class="num">${fmtInt(row.n_neu)}</td>
      <td class="num">${fmtPct(row.praise_pct)}${row.praise_ci95 ? `<br><small>${fmtInterval(row.praise_ci95)}</small>` : ""}</td>
      <td class="num">${fmtSigned(row.net)}${row.net_ci95 ? `<br><small>${fmtInterval(row.net_ci95)}</small>` : ""}</td>
    </tr>`).join("");
  const tests = d.q1.tests.length
    ? `<h3 style="margin-top:14px">Kiểm định (hiệu chỉnh Holm)</h3><div class="table-wrap"><table><tbody>${d.q1.tests.map((test) => `
        <tr><td>${test.compare_with ? `${esc(target.title)} so với ${esc(titleOf(test.compare_with))}` : `${esc(target.title)}: % khen so với 50%`}</td>
        <td>${conclusion(test)}</td></tr>`).join("")}</tbody></table></div>`
    : `<p class="card-note">Chưa có kết quả kiểm định cho bộ số liệu này, nên bảng trên chỉ là số mô tả.</p>`;
  const q1 = card("", "Q1", `${target.title} được đón nhận tốt hay dở?`, status,
    `Net = % khen − % chê, theo tuần kể từ ngày ra mắt của <b>từng máy</b> (ngày 0 khác nhau, cùng giai đoạn). Đời trước và đối thủ vẽ đè để so sánh.`,
    `${legend}${lineChart(models, d.q1.weekly, weeks)}
     <div class="table-wrap"><table><thead><tr><th>Máy</th><th>Vai trò</th><th class="num">Khen</th><th class="num">Chê</th><th class="num">Trung tính</th><th class="num">% khen (KTC 95%)</th><th class="num">Net (KTC 95%)</th></tr></thead>
     <tbody>${overallRows}</tbody></table></div>${tests}`);

  const aspectRows = d.q2.aspects.map((a) => `
    <tr class="${a.low_data ? "dim" : ""}"><td>${esc(a.name)}${lowChip(a)}</td>
      <td class="num">${fmtInt(a.n_pos)}</td><td class="num">${fmtInt(a.n_neg)}</td><td class="num">${fmtInt(a.n_neu)}</td>
      <td class="num">${fmtPct(a.criticism_pct)}</td><td class="num">${fmtSigned(a.criticism_gap_vs_overall)}</td>
      <td>${a.low_data ? "" : conclusion(a.test)}</td></tr>
    ${a.samples.length ? `<tr><td colspan="7"><details class="samples"><summary>Bình luận mẫu về ${esc(a.name.toLowerCase())}</summary>
      ${a.samples.map((s) => `<div class="quote ${s.sentiment}">${esc(s.clause_text)}
        <div class="meta">${s.sentiment === "neg" ? "chê" : "khen"} · nguồn nhãn: ${esc(s.label_source)}${s.confidence == null ? "" : ` · độ tin cậy ${fmtNum(s.confidence, 2)}`}${s.requires_human_review ? " · chưa có người duyệt" : ""}</div></div>`).join("")}
      </details></td></tr>` : ""}`).join("");
  const q2 = card("", "Q2", `Ưu điểm và nhược điểm của ${target.title}`, status,
    `Chê sang trái, khen sang phải; trung tính không vào mẫu số. Mức chê chung của máy: <b>${fmtPct(d.q2.overall.criticism_pct)}</b>. Một khía cạnh chỉ được gọi là nhược điểm khi % chê cao hơn mức chung có ý nghĩa thống kê.`,
    `<div class="legend"><span><span class="swatch" style="background:var(--criticism)"></span>% chê</span><span><span class="swatch" style="background:var(--praise)"></span>% khen</span></div>
     ${divergingBars(d.q2.aspects)}
     <details class="samples"><summary>Bảng số liệu, kiểm định và bình luận mẫu</summary><div class="table-wrap"><table>
       <thead><tr><th>Khía cạnh</th><th class="num">Khen</th><th class="num">Chê</th><th class="num">Trung tính</th><th class="num">% chê</th><th class="num">So với mức chung</th><th>Kết luận</th></tr></thead>
       <tbody>${aspectRows}</tbody></table></div></details>`);

  const defects = d.q5.defects.filter((row) => row.n_defect > 0);
  const priorityOf = (row) => row.priority ? `<span class="chip strong">${esc(row.priority)}</span>`
    : row.priority_candidate ? `<span class="chip">${esc(row.priority_candidate)} (gợi ý, nhãn chưa kiểm chứng)</span>`
    : row.n_defect < 20 ? '<span class="chip">theo dõi, chưa đủ dữ liệu</span>' : '<span class="chip">chưa kiểm định xu hướng</span>';
  const q5 = card("half", "Q5", "Lỗi do người đã dùng máy báo", status,
    `${fmtInt(d.q5.n_owner_defect_mentions)} lời chê của người đã dùng máy trên ${fmtInt(d.q5.n_target_mentions)} mention về máy, chia theo khía cạnh (bộ loại lỗi chưa chốt). Đây là tỷ lệ <b>lượt nhắc</b>, không phải tỷ lệ máy bị lỗi.`,
    defects.length ? `<div class="table-wrap"><table><thead><tr><th>Khía cạnh</th><th class="num">Lượt nhắc</th>${weeks.map((w) => `<th class="num">T${w}</th>`).join("")}<th>Ưu tiên</th></tr></thead><tbody>
      ${defects.map((row) => `<tr><td>${esc(row.name)}</td><td class="num">${fmtInt(row.n_defect)}</td>
        ${row.weekly.map((w) => `<td class="num" ${tip(`${row.name}, tuần ${w.week_since_launch}`, `${fmtInt(w.n_defect)} / ${fmtInt(w.n_denominator)} mention = ${fmtPct(w.defect_mention_pct, 2)}`)}>${fmtInt(w.n_defect)}</td>`).join("")}
        <td>${priorityOf(row)}</td></tr>`).join("")}</tbody></table></div>`
      : empty("Không có lời chê nào do người đã dùng máy viết."));

  const alerts = card("half", "", "Cảnh báo", d.alerts.length ? status : null,
    "So tỷ lệ chê với đời trước tại cùng số ngày sau ra mắt. Đọc từ collection <code>alerts</code>.",
    d.alerts.length ? `<div class="table-wrap"><table><thead><tr><th>Thời điểm</th><th>Khía cạnh</th><th class="num">Giá trị</th><th class="num">Mốc so sánh</th><th>Mức</th></tr></thead><tbody>
      ${d.alerts.map((a) => `<tr><td>${fmtDate(a.created_at)}</td><td>${esc(a.aspect_name)}</td><td class="num">${fmtNum(a.value)}</td><td class="num">${fmtNum(a.baseline)}</td><td><span class="chip strong">${esc(a.severity)}</span></td></tr>
        ${(a.samples || []).map((s) => `<tr><td colspan="5"><div class="quote neg">${esc(s.clause_text)}</div></td></tr>`).join("")}`).join("")}</tbody></table></div>`
      : empty("Chưa có cảnh báo nào cho máy này. Phần sinh cảnh báo thuộc luồng streaming (tùy chọn) và chưa chạy."));

  $("#tab-launch").innerHTML = q1 + q2 + q5 + alerts;
}

// ---------------------------------------------------------------- Tab 2

function renderCompare(d) {
  const status = d.data_status, models = d.scope.models, target = models[0];
  const metric = state.heatMetric, metricName = metric === "praise_pct" ? "% khen" : "% chê";
  const step = (value) => "s" + Math.min(6, Math.floor(value / (100 / 6)) + 1);
  const heatRows = d.q3a.matrix.map((row) => `<tr><th>${esc(row.name)}</th>
    ${row.cells.map((cell) => {
      const value = cell[metric], ci = fmtInterval(metric === "praise_pct" ? cell.praise_ci95 : cell.criticism_ci95);
      const title = (models.find((model) => model.model_id === cell.model_id) || {}).title;
      const hover = tip(`${row.name} · ${title}`, `${metricName} ${fmtPct(value)}${ci ? ` (KTC 95%: ${ci})` : ""}`,
        `Khen ${fmtInt(cell.n_pos)}, chê ${fmtInt(cell.n_neg)}, trung tính ${fmtInt(cell.n_neu)}`, cell.low_data ? "Ít dữ liệu: không kết luận" : "");
      if (value == null) return `<td class="cell low" ${hover}>–<small>chưa có</small></td>`;
      if (cell.low_data) return `<td class="cell low" ${hover}>${fmtPct(value, 0)}<small>ít dữ liệu · n=${fmtInt(cell.n_opinionated)}</small></td>`;
      return `<td class="cell ${step(value)}" ${hover}>${fmtPct(value, 0)}<small>n=${fmtInt(cell.n_opinionated)}</small></td>`;
    }).join("")}
    <td>${conclusion(row.omnibus)}</td></tr>`).join("");
  const q3a = card("", "Q3a", `${target.title} so với đời trước và đối thủ, theo khía cạnh`, status,
    `Mỗi ô là ${metricName} của một máy ở một khía cạnh, màu càng đậm giá trị càng lớn. Ô gạch chéo là ô có khen + chê &lt; ${state.meta.min_opinionated}. Cột cuối là kiểm định khác biệt giữa các máy.`,
    `<div class="toggle" role="group" aria-label="Chỉ số">
       <button type="button" data-metric="praise_pct" aria-pressed="${metric === "praise_pct"}">% khen</button>
       <button type="button" data-metric="criticism_pct" aria-pressed="${metric === "criticism_pct"}">% chê</button></div>
     <div class="table-wrap"><table class="heat"><thead><tr><th></th>${models.map((model) => `<th>${esc(model.title)}<br><small>${ROLE_NAME[model.role] || model.role}</small></th>`).join("")}<th>Khác biệt giữa các máy</th></tr></thead>
     <tbody>${heatRows}</tbody></table></div>`);

  const duels = d.q3b.filter((row) => row.n_decisive + row.n_tie > 0);
  const duelBar = (row) => {
    if (!row.n_decisive) return '<span class="chip">chỉ có mệnh đề hòa</span>';
    const W = 300, win = (row.n_x_win / row.n_decisive) * W;
    return `<svg class="chart" viewBox="0 0 ${W} 18" style="max-width:${W}px" role="img" aria-label="Tỷ lệ thắng">
      <path d="${roundedBar(Math.max(win - 1, 0), 2, -Math.max(win - 1, 0), 14)}" fill="var(--series-1)" opacity="${row.low_data ? 0.35 : 1}"/>
      <path d="${roundedBar(Math.min(win + 1, W), 2, Math.max(W - win - 1, 0), 14)}" fill="var(--series-2)" opacity="${row.low_data ? 0.35 : 1}"/></svg>`;
  };
  const q3b = card("half", "Q3b", "So sánh trực tiếp trong cùng một mệnh đề", status,
    `Chỉ tính mệnh đề nêu cả ${esc(target.title)} và một máy khác (vd "chụp đêm thua iPhone"). Hòa không vào mẫu số.`,
    duels.length ? `<div class="legend"><span><span class="swatch" style="background:var(--series-1)"></span>${esc(target.title)} thắng</span><span><span class="swatch" style="background:var(--series-2)"></span>máy kia thắng</span></div>
      <div class="table-wrap"><table><thead><tr><th>Khía cạnh</th><th>Tỷ lệ</th><th class="num">Thắng</th><th class="num">Thua</th><th class="num">Hòa</th><th>Kết luận</th></tr></thead><tbody>
      ${duels.map((row) => `<tr class="${row.low_data ? "dim" : ""}"><td>${esc(row.name)}${lowChip(row)}</td><td>${duelBar(row)}</td>
        <td class="num">${fmtInt(row.n_x_win)}</td><td class="num">${fmtInt(row.n_x_loss)}</td><td class="num">${fmtInt(row.n_tie)}</td>
        <td>${row.low_data ? "" : row.test ? conclusion(row.test) : '<span class="chip">chưa phân định</span>'}</td></tr>`).join("")}</tbody></table></div>`
      : empty("Chưa có mệnh đề so sánh trực tiếp nào cho máy này."));

  const predecessor = models.find((model) => model.role === "P");
  const q4 = card("half", "Q4", "Đời trước bị chê gì, đời này đã sửa chưa?", status,
    predecessor ? `% chê theo khía cạnh, cùng công thức với Q2. Chấm rỗng: ${esc(predecessor.title)}; chấm đặc: ${esc(target.title)}. Sang trái là bớt chê.` : "",
    predecessor ? `${dumbbells(d.q4.aspects, predecessor.title, target.title)}
      <details class="samples"><summary>Bảng số liệu và kiểm định</summary><div class="table-wrap"><table><thead><tr><th>Khía cạnh</th><th class="num">${esc(predecessor.title)}</th><th class="num">${esc(target.title)}</th><th class="num">Thay đổi</th><th>Kết luận</th></tr></thead><tbody>
      ${d.q4.aspects.map((row) => { const low = row.predecessor.low_data || row.current.low_data; return `<tr class="${low ? "dim" : ""}"><td>${esc(row.name)}${low ? ' <span class="chip">ít dữ liệu</span>' : ""}</td>
        <td class="num">${fmtPct(row.predecessor.criticism_pct)}</td><td class="num">${fmtPct(row.current.criticism_pct)}</td><td class="num">${fmtSigned(row.criticism_change)}</td>
        <td>${low ? "" : conclusion(row.test)}</td></tr>`; }).join("")}</tbody></table></div></details>`
      : empty(`Chưa biết đời trước của ${esc(target.title)}: trường <code>predecessor_id</code> trong collection <code>models</code> đang trống (Công việc 2), và chưa có cấu hình phân tích của Công việc 12 cho máy này.`));

  $("#tab-compare").innerHTML = q3a + q3b + q4;
  for (const button of document.querySelectorAll("#tab-compare [data-metric]")) {
    button.addEventListener("click", () => { state.heatMetric = button.dataset.metric; renderCompare(d); });
  }
}

// ---------------------------------------------------------------- Tab 3 và 4

const COLLECTION_NAME = { models: "Máy", videos: "Video", comments: "Bình luận", aspect_mentions: "Mention", aggregates: "Dòng aggregates", alerts: "Cảnh báo", gold_labels: "Nhãn vàng", analysis_results: "Kết quả phân tích" };
// Mã lý do spam của luật gắn cờ src/processing/flags.py (docs/2-tien-xu-ly/dac-ta-gan-co.md)
const REASON_NAME = { lien_ket: "Có link", so_dien_thoai: "Có số điện thoại", moi_lien_he: "Mời liên hệ (Zalo, inbox…)", co_bac_lua_dao: "Cờ bạc, lừa đảo" };

function renderSystem(d) {
  const c = d.comments, total = c.total || 0, share = (n) => (total ? fmtPct((100 * n) / total, 2) : "–");
  const collections = card("", "", "Dữ liệu đang có trong MongoDB", null, "Số bản ghi từng collection theo thiết kế dữ liệu của nhóm.",
    `<div class="tiles">${Object.entries(d.collections).map(([name, n]) => tile(fmtInt(n), COLLECTION_NAME[name] || name, name)).join("")}</div>`);
  const cleaning = card("half", "", "Tiền xử lý và lọc spam", null,
    `Cờ spam trong DB hiện do bộ luật <code>rule-v0</code> gắn, và bộ luật này tính cả "không phải tiếng Việt" là spam. Đánh giá tạm thời ở Công việc 11 (nhãn chưa có người duyệt) cho thấy phần lớn bình luận bị luật gắn cờ không phải spam.`,
    total ? `<div class="tiles">${tile(fmtInt(total), "Bình luận đã xử lý")}${tile(fmtInt(c.usable), "Đưa vào phân tích", share(c.usable))}${tile(fmtInt(c.spam), "Bị luật gắn cờ spam", share(c.spam))}${tile(fmtInt(c.not_vietnamese), "Bị coi là không phải tiếng Việt", share(c.not_vietnamese))}</div>
      <h3 style="margin-top:14px">Lý do gắn cờ (một bình luận có thể có nhiều lý do)</h3>
      ${horizontalBars(Object.entries(c.spam_reasons).map(([reason, n]) => ({ label: REASON_NAME[reason] || reason, value: n })), "bình luận")}`
      : empty("Collection <code>comments</code> đang trống."));
  const labels = card("half", "", "Nhãn đang được phục vụ", null, "Mỗi phiên bản nhãn kèm nguồn gốc. Nguồn <code>rule</code> và <code>llm</code> chỉ được hiển thị kèm chữ “số liệu minh họa”.",
    d.labels.length ? `<div class="table-wrap"><table><thead><tr><th>Phiên bản</th><th>Nguồn nhãn</th><th class="num">Mention trong aggregates</th></tr></thead><tbody>
      ${d.labels.map((v) => `<tr><td>${esc(v.model_version)}</td><td>${Object.entries(v.label_sources).map(([s, n]) => `<span class="chip ${s === "rule" || s === "llm" ? "illustrative" : "strong"}">${esc(s)}: ${fmtInt(n)}</span>`).join(" ") || "không rõ"}</td><td class="num">${fmtInt(v.n_mentions_in_aggregates)}</td></tr>`).join("")}</tbody></table></div>
      <p class="card-note" style="margin-top:10px">Aggregates cập nhật lần cuối: ${d.aggregates_updated_at ? esc(String(d.aggregates_updated_at).replace("T", " ").slice(0, 19)) + " UTC" : "chưa có"}.</p>`
      : empty("Chưa có aggregates nào."));
  const apiCard = card("half", "", "Độ trễ của API", null, "Đo trực tiếp trên các request gần nhất tới API này (tối đa 500), không tính request của chính trang này tới <code>/api/system</code>.",
    `<div class="tiles">${tile(d.api.latency_ms_p50 == null ? "–" : fmtNum(d.api.latency_ms_p50, 0) + " ms", "p50")}${tile(d.api.latency_ms_p95 == null ? "–" : fmtNum(d.api.latency_ms_p95, 0) + " ms", "p95")}${tile(fmtInt(d.api.n_requests_measured), "Request đã đo")}${tile(fmtInt(d.api.uptime_seconds / 60) + " phút", "Thời gian chạy")}</div>`);
  const streaming = card("half", "", "Luồng streaming (Kafka, Spark)", null, "", empty(esc(d.streaming.note)));
  $("#tab-system").innerHTML = collections + cleaning + labels + apiCard + streaming;
}

function renderOverview(d) {
  const t = d.totals;
  const totals = card("", "", "Tổng quan tập dữ liệu đã thu thập", null,
    "Số liệu đếm trực tiếp từ collection <code>comments</code>. Phần này là bối cảnh, không phải kết quả phân tích.",
    `<div class="tiles">${tile(fmtInt(t.total), "Bình luận")}${tile(fmtInt(t.total - t.replies), "Bình luận gốc")}${tile(fmtInt(t.replies), "Phản hồi")}${tile(fmtInt(t.n_videos), "Video")}${tile(fmtInt(t.n_video_models), "Nhóm máy theo video")}${tile(fmtInt(t.n_catalog_models), "Máy trong danh mục")}</div>`);
  const brands = card("half", "", "Bình luận theo hãng", null, "Hãng của máy mà video nói tới, không phải máy được nhắc trong bình luận.",
    horizontalBars(d.by_brand.map((b) => ({ label: b.brand, value: b.n_comments })), "bình luận"));
  const models = card("half", "", "15 nhóm máy có nhiều bình luận nhất", null, "",
    horizontalBars(d.by_model.slice(0, 15).map((m) => ({ label: m.title, value: m.n_comments, note: m.brand })), "bình luận"));
  const hours = card("", "", `Bình luận theo giờ trong ngày (${esc(d.timezone)})`, null,
    "Giờ Việt Nam, đổi từ <code>published_at</code> (UTC).", hourColumns(d.by_hour));
  $("#tab-overview").innerHTML = totals + brands + models + hours;
}

// ---------------------------------------------------------------- điều phối

const RENDER = { launch: renderLaunch, compare: renderCompare, system: renderSystem, overview: renderOverview };
const SCOPED = new Set(["launch", "compare"]);

function showBanner(status, scope) {
  const banner = $("#status-banner");
  banner.className = "banner";
  if (status && status.illustrative) {
    banner.innerHTML = `<strong>SỐ LIỆU MINH HỌA</strong> — chưa dùng được để kết luận về sản phẩm.<ul>${status.reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>`;
    banner.hidden = false;
  } else banner.hidden = true;
  if (scope) {
    const role = (name) => scope.models.filter((model) => model.role.startsWith(name));
    const target = scope.models[0];
    $("#scope-line").textContent = [
      `${target.title} (ra mắt ${fmtDate(target.launch_date)})`,
      role("P").length ? `đời trước: ${role("P")[0].title}` : "chưa khai báo đời trước",
      role("R").length ? `đối thủ: ${role("R").map((model) => model.title).join(", ")}` : "chưa có đối thủ có dữ liệu",
      `${scope.window_weeks} tuần đầu sau ra mắt`, `nhãn ${scope.model_version}`,
    ].join(" · ");
  }
}

async function loadTab() {
  const tab = state.tab, panel = $(`#tab-${tab}`);
  const key = SCOPED.has(tab) ? `${tab}|${state.model}|${state.version}` : tab;
  try {
    if (SCOPED.has(tab) && !state.version) {
      $("#status-banner").hidden = true;
      $("#scope-line").textContent = "Chưa có số liệu phân tích trong DB.";
      panel.innerHTML = `<article class="card">${empty("Collection <code>aggregates</code> đang trống. Nạp dữ liệu bằng <code>python -m src.run --den nap_db</code> (xem docs/7-hien-thi/huong-dan.md).")}</article>`;
      return;
    }
    if (!state.data[key]) {
      panel.innerHTML = '<article class="card">Đang tải…</article>';
      state.data[key] = await api(tab, SCOPED.has(tab) ? { model: state.model, model_version: state.version } : {});
    }
    // Người dùng đã chuyển tab, đổi máy hoặc đổi phiên bản trong lúc chờ: bỏ kết quả cũ này.
    const current = SCOPED.has(state.tab) ? `${state.tab}|${state.model}|${state.version}` : state.tab;
    if (current !== key) return;
    const data = state.data[key];
    RENDER[tab](data);
    if (SCOPED.has(tab)) showBanner(data.data_status, data.scope);
    else { $("#status-banner").hidden = true; $("#scope-line").textContent = "Số liệu đếm trực tiếp từ DB, không qua mô hình."; }
    $("#loaded-at").textContent = "Tải lúc " + new Date().toLocaleTimeString("vi-VN");
  } catch (error) {
    const banner = $("#status-banner");
    banner.className = "banner error";
    banner.textContent = `Không tải được dữ liệu: ${error.message}`;
    banner.hidden = false;
    panel.innerHTML = `<article class="card">${empty("Không có dữ liệu để hiển thị. Kiểm tra API và MongoDB rồi tải lại trang.")}</article>`;
  }
}

function selectTab(tab) {
  state.tab = RENDER[tab] ? tab : "launch";
  for (const button of document.querySelectorAll(".tabs button")) button.setAttribute("aria-selected", String(button.dataset.tab === state.tab));
  for (const panel of document.querySelectorAll(".tab-panel")) panel.hidden = panel.id !== `tab-${state.tab}`;
  $("#filters").style.visibility = SCOPED.has(state.tab) ? "visible" : "hidden";
  const hash = new URLSearchParams({ tab: state.tab, ...(state.model ? { model: state.model } : {}), ...(state.version ? { version: state.version } : {}) });
  history.replaceState(null, "", "#" + hash);
  loadTab();
}

function fillSelect(select, items, selected) {
  select.innerHTML = items.map((item) => `<option value="${esc(item.value)}">${esc(item.label)}</option>`).join("");
  if (items.some((item) => item.value === selected)) select.value = selected;
}

async function refreshTargets() {
  const meta = await api("meta", { model_version: state.version });
  if (!meta.targets.some((target) => target.model_id === state.model)) state.model = meta.targets.length ? meta.targets[0].model_id : null;
  fillSelect($("#model-select"), meta.targets.map((target) => ({ value: target.model_id, label: `${target.title} (${fmtInt(target.n_total)} mention)` })), state.model);
}

async function init() {
  const tooltip = $("#tooltip");
  const showTip = (target, x, y) => {
    tooltip.replaceChildren(...target.dataset.tip.split("\n").map((line, i) => {
      const row = document.createElement(i === 0 ? "b" : "div");
      row.textContent = line;
      return row;
    }));
    tooltip.hidden = false;
    const box = tooltip.getBoundingClientRect();
    tooltip.style.left = Math.max(8, Math.min(x + 14, window.innerWidth - box.width - 8)) + "px";
    tooltip.style.top = Math.max(8, Math.min(y + 14, window.innerHeight - box.height - 8)) + "px";
  };
  document.addEventListener("mousemove", (event) => {
    const target = event.target.closest && event.target.closest("[data-tip]");
    if (target) showTip(target, event.clientX, event.clientY); else tooltip.hidden = true;
  });
  document.addEventListener("focusin", (event) => {
    const target = event.target.closest && event.target.closest("[data-tip]");
    if (target) { const box = target.getBoundingClientRect(); showTip(target, box.left + box.width / 2, box.top + box.height / 2); }
  });
  document.addEventListener("focusout", () => { tooltip.hidden = true; });

  try {
    state.meta = await api("meta");
  } catch (error) {
    const banner = $("#status-banner");
    banner.className = "banner error";
    banner.textContent = `Không kết nối được API hoặc MongoDB: ${error.message}`;
    banner.hidden = false;
    $("#scope-line").textContent = "";
    return;
  }
  $("#min-n").textContent = state.meta.min_opinionated;
  const hash = new URLSearchParams(location.hash.slice(1));
  const versions = state.meta.versions.map((v) => v.model_version);
  // Phiên bản phải là một phiên bản đang có số đếm; nếu không thì lấy phiên bản đầu danh sách.
  const wanted = [hash.get("version"), state.meta.defaults.model_version, versions[0]];
  state.version = wanted.find((version) => versions.includes(version)) || null;
  state.model = hash.get("model") || state.meta.defaults.model;
  fillSelect($("#version-select"), versions.map((v) => ({ value: v, label: v })), state.version);
  if (state.version) await refreshTargets();

  $("#version-select").addEventListener("change", async (event) => { state.version = event.target.value; await refreshTargets(); selectTab(state.tab); });
  $("#model-select").addEventListener("change", (event) => { state.model = event.target.value; selectTab(state.tab); });
  for (const button of document.querySelectorAll(".tabs button")) button.addEventListener("click", () => selectTab(button.dataset.tab));
  selectTab(hash.get("tab") || "launch");
}

init();

document.addEventListener("DOMContentLoaded", () => {
  const menu = document.getElementById("mobileMenu");
  const sidebar = document.getElementById("sidebar");
  if (menu && sidebar) menu.addEventListener("click", () => sidebar.classList.toggle("sidebar-open"));

  document.querySelectorAll(".flash-close").forEach((button) => {
    button.addEventListener("click", () => button.closest(".flash")?.remove());
  });

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm || "Are you sure?")) event.preventDefault();
    });
  });

  document.querySelectorAll("[data-current-year]").forEach((node) => {
    node.textContent = new Date().getFullYear();
  });

  // Lightweight responsive charts using Canvas; no chart library or new dependency.
  const readJson = (id) => { try { return JSON.parse(document.getElementById(id)?.textContent || "[]"); } catch { return []; } };
  const drawBars = (canvas, labels, values, horizontal = false) => {
    if (!canvas || !labels.length) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.clientWidth || 360; const height = 220; const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr; canvas.height = height * dpr; ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);
    const max = Math.max(1, ...values); const gap = 12; const left = horizontal ? 95 : 18; const bottom = horizontal ? 10 : 42;
    const plotW = width - left - 12; const plotH = height - bottom - 12;
    ctx.font = "11px sans-serif"; ctx.fillStyle = "#7c8798"; ctx.strokeStyle = "#e8ecf2";
    for (let i = 0; i < 4; i++) { const y = 8 + plotH * i / 3; ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(width - 8, y); ctx.stroke(); }
    const slot = horizontal ? plotH / labels.length : plotW / labels.length;
    labels.forEach((label, i) => {
      const val = Number(values[i]) || 0; ctx.fillStyle = "#456fe8";
      if (horizontal) { const y = 8 + i * slot + gap / 2; const bw = plotW * val / max; ctx.fillRect(left, y, bw, Math.max(5, slot - gap)); ctx.fillStyle = "#536174"; ctx.textAlign = "right"; ctx.fillText(String(label).slice(0, 14), left - 8, y + Math.max(5, slot - gap) / 2 + 4); }
      else { const bw = Math.max(5, slot - gap); const bh = plotH * val / max; const x = left + i * slot + gap / 2; const y = 8 + plotH - bh; ctx.fillRect(x, y, bw, bh); ctx.fillStyle = "#536174"; ctx.textAlign = "center"; ctx.fillText(String(label).slice(0, 8), x + bw / 2, height - 17); }
    });
  };
  const categoryLabels = readJson("categoryData");
  drawBars(document.getElementById("categoryChart"), categoryLabels, readJson("categoryValues"), true);
  drawBars(document.getElementById("loanChart"), readJson("monthLabels"), readJson("monthValues"));
  window.addEventListener("resize", () => {
    drawBars(document.getElementById("categoryChart"), categoryLabels, readJson("categoryValues"), true);
    drawBars(document.getElementById("loanChart"), readJson("monthLabels"), readJson("monthValues"));
  });
});

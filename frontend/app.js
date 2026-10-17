const state = { charts: [], pacientes: [] };

const $ = (sel) => document.querySelector(sel);

async function api(path, options = {}) {
  const resp = await fetch(path, options);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detalhe = data.detail;
    throw new Error(typeof detalhe === "string" ? detalhe : JSON.stringify(detalhe || resp.statusText));
  }
  return data;
}

function setStatus(el, texto, tipo = "") {
  el.textContent = texto;
  el.className = `status ${tipo}`;
}

function escapeHtml(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

function renderMarkdown(texto) {
  return escapeHtml(texto)
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h3>$1</h3>")
    .replace(/^# (.*)$/gm, "<h3>$1</h3>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[-*] (.*)$/gm, "• $1");
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR");
}

function chartColor(index) {
  const paleta = ["#38bdf8", "#34d399", "#fbbf24", "#f87171", "#a78bfa", "#f472b6", "#2dd4bf", "#fb923c"];
  return paleta[index % paleta.length];
}

function destroyCharts() {
  state.charts.forEach((c) => c.destroy());
  state.charts = [];
}

function renderCharts(serieTemporal) {
  destroyCharts();
  const container = $("#charts");
  container.innerHTML = "";

  const entradas = Object.entries(serieTemporal).filter(([, pontos]) => pontos.length >= 2);
  if (!entradas.length) {
    container.innerHTML = '<p class="empty">Paciente precisa de pelo menos 2 medições por exame.</p>';
    return;
  }

  entradas.forEach(([nome, pontos], index) => {
    const box = document.createElement("div");
    box.className = "chart-box";
    box.innerHTML = `<h3>${escapeHtml(nome)}</h3><canvas></canvas>`;
    container.appendChild(box);

    const chart = new Chart(box.querySelector("canvas"), {
      type: "line",
      data: {
        labels: pontos.map((p) => formatDate(p.data)),
        datasets: [{
          label: nome,
          data: pontos.map((p) => p.valor),
          borderColor: chartColor(index),
          backgroundColor: chartColor(index) + "33",
          fill: true,
          tension: 0.3,
          pointRadius: 3,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#94a3b8", maxTicksLimit: 8 }, grid: { color: "rgba(45,59,85,0.5)" } },
          y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(45,59,85,0.5)" } },
        },
      },
    });
    state.charts.push(chart);
  });
}

function renderAlertas(alertas) {
  const container = $("#alertas");
  if (!alertas.length) {
    container.innerHTML = '<p class="empty">Nenhum alerta crítico identificado.</p>';
    return;
  }
  container.innerHTML = alertas.map((a) => `
    <div class="alerta ${a.tipo}">
      <h3>${escapeHtml(a.titulo)}</h3>
      <p>${escapeHtml(a.mensagem)}</p>
      <p class="rec">Recomendação: ${escapeHtml(a.recomendacao)}</p>
    </div>`).join("");
}

function renderTendencias(tendencias) {
  const tbody = $("#tendencias-table tbody");
  const linhas = Object.entries(tendencias);
  if (!linhas.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty">Sem dados suficientes.</td></tr>';
    return;
  }
  tbody.innerHTML = linhas.map(([nome, t]) => {
    const dir = t.tendencia_direcao || "-";
    const classe = dir === "crescente" ? "up" : dir === "decrescente" ? "down" : "";
    const sig = t.significativa ? '<span class="tag sim">sim</span>' : '<span class="tag nao">não</span>';
    return `<tr>
      <td>${escapeHtml(nome)}</td>
      <td>${t.ultimo_valor.toFixed(2)}</td>
      <td class="${classe}">${t.delta_percentual.toFixed(1)}%</td>
      <td class="${classe}">${escapeHtml(dir)}</td>
      <td>${sig}</td>
    </tr>`;
  }).join("");
}

function renderLiteratura(itens) {
  const container = $("#literatura");
  if (!itens.length) {
    container.innerHTML = '<p class="empty">Nenhum trecho recuperado. Indexe arquivos em data/literatura com scripts/popular_rag.py.</p>';
    return;
  }
  container.innerHTML = itens.map((t) => `<div class="literatura-item">${escapeHtml(t)}</div>`).join("");
}

function renderPacienteCard(paciente) {
  const card = $("#paciente-card");
  card.classList.remove("hidden");
  card.innerHTML = `
    <div class="info-chip"><b>Paciente</b>${escapeHtml(paciente.nome_anon)}</div>
    <div class="info-chip"><b>Sexo</b>${escapeHtml(paciente.sexo || "-")}</div>
    <div class="info-chip"><b>Idade aprox.</b>${escapeHtml(paciente.idade_aprox)} anos</div>
    <div class="info-chip"><b>Exames</b>${paciente.exames.length}</div>
    <div class="info-chip"><b>Anotações</b>${paciente.anotacoes.length}</div>`;
}

function fillPacienteSelect(select, pacientes) {
  select.innerHTML = pacientes.map((p) =>
    `<option value="${p.id}">#${p.id} — ${p.nome_anon} (${p.total_exames} exames)</option>`
  ).join("");
}

async function carregarPacientes() {
  state.pacientes = await api("/api/pacientes");
  fillPacienteSelect($("#paciente-select"), state.pacientes);
  fillPacienteSelect($("#prontuario-paciente"), state.pacientes);
  if (!state.pacientes.length) {
    $("#paciente-select").innerHTML = '<option value="">Nenhum paciente — importe um CSV</option>';
  }
}

async function carregarConfig() {
  const cfg = await api("/api/config");
  const badge = $("#llm-badge");
  if (cfg.llm_configured) {
    badge.textContent = "IA conectada";
    badge.className = "badge ok";
  } else {
    badge.textContent = "IA não configurada (.env)";
    badge.className = "badge warn";
  }
  $("#modelo-select").innerHTML = cfg.available_models
    .map((m) => `<option value="${m}" ${m === cfg.llm_model ? "selected" : ""}>${m}</option>`)
    .join("");
}

async function analisar() {
  const id = $("#paciente-select").value;
  if (!id) return;
  const btn = $("#btn-analisar");
  btn.disabled = true;
  setStatus($("#analise-status"), "Analisando…");

  try {
    const paciente = await api(`/api/pacientes/${id}`);
    renderPacienteCard(paciente);

    const resultado = await api("/api/analisar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        paciente_id: Number(id),
        modelo: $("#modelo-select").value || null,
      }),
    });

    renderAlertas(resultado.alertas);
    renderTendencias(resultado.tendencias);
    renderCharts(resultado.serie_temporal);
    renderLiteratura(resultado.literatura_usada);

    const alvo = $("#analise-llm");
    if (resultado.analise_llm) {
      alvo.innerHTML = renderMarkdown(resultado.analise_llm);
      setStatus($("#analise-status"), "Análise concluída", "ok");
    } else {
      alvo.innerHTML = `<p class="empty">IA indisponível: ${escapeHtml(resultado.erro_llm || "erro desconhecido")}</p>`;
      setStatus($("#analise-status"), "IA indisponível — dados e alertas exibidos", "error");
    }
  } catch (erro) {
    setStatus($("#analise-status"), erro.message, "error");
  } finally {
    btn.disabled = false;
  }
}

async function gerarProntuario() {
  const id = $("#prontuario-paciente").value;
  if (!id) return;
  const btn = $("#btn-prontuario");
  btn.disabled = true;
  setStatus($("#prontuario-status"), "Gerando…");

  try {
    const resp = await api("/api/gerar_prontuario", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        paciente_id: Number(id),
        conduta_medica: $("#prontuario-conduta").value || "(conduta não informada)",
        observacoes_medico: $("#prontuario-observacoes").value || "(sem observações)",
        medicamentos_atual: $("#prontuario-medicamentos").value || null,
      }),
    });
    const output = $("#prontuario-output");
    output.textContent = resp.prontuario;
    output.classList.remove("hidden");
    setStatus($("#prontuario-status"), "Prontuário gerado", "ok");
  } catch (erro) {
    setStatus($("#prontuario-status"), erro.message, "error");
  } finally {
    btn.disabled = false;
  }
}

async function enviarUpload() {
  const arquivo = $("#upload-file").files[0];
  if (!arquivo) {
    setStatus($("#upload-status"), "Selecione um CSV", "error");
    return;
  }
  const btn = $("#btn-upload");
  btn.disabled = true;
  setStatus($("#upload-status"), "Enviando…");

  try {
    const form = new FormData();
    form.append("file", arquivo);
    const pacienteId = $("#upload-paciente-id").value;
    if (pacienteId) form.append("paciente_id", pacienteId);

    const resp = await api("/api/upload_exame", { method: "POST", body: form });
    setStatus($("#upload-status"), `${resp.exames_inseridos} exames importados (paciente #${resp.paciente_id})`, "ok");
    await carregarPacientes();
    $("#paciente-select").value = String(resp.paciente_id);
    $("#prontuario-paciente").value = String(resp.paciente_id);
  } catch (erro) {
    setStatus($("#upload-status"), erro.message, "error");
  } finally {
    btn.disabled = false;
  }
}

function configurarTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      $(`#${tab.dataset.tab}`).classList.add("active");
    });
  });
}

async function init() {
  configurarTabs();
  $("#btn-analisar").addEventListener("click", analisar);
  $("#btn-prontuario").addEventListener("click", gerarProntuario);
  $("#btn-upload").addEventListener("click", enviarUpload);

  try {
    await carregarConfig();
  } catch {
    $("#llm-badge").textContent = "API offline";
    $("#llm-badge").className = "badge warn";
  }
  try {
    await carregarPacientes();
  } catch {
    $("#paciente-select").innerHTML = '<option value="">Erro ao carregar pacientes</option>';
  }
}

init();

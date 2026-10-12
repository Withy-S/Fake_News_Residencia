import { captureActiveTab } from "../shared/page-context.js";
import { analyzeText, findRelatedNews } from "../shared/api.js";

const get = (id) => document.getElementById(id);
let searchController;
let generation = 0;
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * 42;

// RF12/RF14: como mostrar cada classificação e cada método ao usuário.
const CLASSIFICATION_INFO = {
  confiavel: { title: "Conteúdo possivelmente confiável", tone: "safe" },
  suspeito: { title: "Conteúdo possivelmente suspeito", tone: "alert" },
  nao_verificado: { title: "Não foi possível verificar", tone: "neutral" },
};
const METHOD_LABELS = {
  whitelist: "FONTE CONFIÁVEL",
  ml_model: "MODELO DE ML",
  ai_fallback: "ANÁLISE COMPLEMENTAR",
  analise_linguistica: "ANÁLISE LINGUÍSTICA",
};

function setGauge(percent, tone) {
  // className é só leitura em elementos SVG (<svg>/<circle>): precisa usar classList.
  const svg = get("gauge-svg");
  const progress = get("gauge-progress");
  const percentElement = get("fake-percent");
  svg.classList.toggle("gauge__svg--safe", tone === "safe");
  svg.classList.toggle("gauge__svg--neutral", tone === "neutral");
  progress.classList.toggle("gauge__progress--safe", tone === "safe");
  progress.classList.toggle("gauge__progress--neutral", tone === "neutral");
  percentElement.className = `gauge__percent${tone === "alert" ? "" : ` gauge__percent--${tone}`}`;
  progress.style.setProperty("stroke-dashoffset", `${GAUGE_CIRCUMFERENCE * (1 - percent / 100)}`);
  percentElement.textContent = `${Math.round(percent)}%`;
}

function renderAnalyzing() {
  get("result-title").textContent = "Analisando…";
  get("verdict-tag").hidden = true;
  get("verdict-detail").textContent = "Consultando o modelo de Machine Learning…";
  setGauge(0, "neutral");
}

function renderVerdict(result) {
  if (!result.classification) {
    renderVerdictError(new Error(result.error?.message || "Não foi possível analisar o conteúdo."));
    return;
  }
  const info = CLASSIFICATION_INFO[result.classification] ?? CLASSIFICATION_INFO.nao_verificado;
  const confidence = result.confidence ?? 0;
  const fakePercent = result.classification === "suspeito" ? confidence * 100
    : result.classification === "confiavel" ? (1 - confidence) * 100
    : 50;
  setGauge(fakePercent, info.tone);
  get("result-title").textContent = info.title;
  const methodLabel = METHOD_LABELS[result.method];
  get("verdict-tag").hidden = !methodLabel;
  get("verdict-tag").textContent = methodLabel ?? "";
  get("verdict-tag").className = `tag${info.tone === "alert" ? "" : ` tag--${info.tone}`}`;
  get("verdict-detail").textContent = result.justifications.length
    ? result.justifications.join(" ")
    : `Confiança do modelo: ${Math.round(confidence * 100)}%.`;
}

function renderVerdictError(error) {
  setGauge(0, "neutral");
  get("result-title").textContent = "Análise indisponível";
  get("verdict-tag").hidden = true;
  get("verdict-detail").textContent = error?.message || "Não foi possível consultar a análise.";
}

function renderSources(result) {
  get("sources").replaceChildren();
  const publishers = new Set(["R7", "Correio Braziliense", "CNN Brasil"]);
  for (const source of result.sources) {
    let url;
    try { url = new URL(source.url); } catch { continue; }
    if (url.protocol !== "https:" || url.host !== "news.google.com" ||
        !/^\/(rss\/)?articles\//.test(url.pathname) || !publishers.has(source.publisher)) continue;
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = url.href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = source.title;
    const label = document.createElement("small");
    label.textContent = source.relation === 'context'
      ? `${source.publisher} • Contexto sobre o tema`
      : source.publisher;
    link.append(label);
    item.append(link);
    get("sources").append(item);
  }
  const count = get("sources").children.length;
  const unavailable = result.unavailable_publishers;
  get("search-status").textContent = count
    ? "Encontramos estas possíveis coberturas da notícia:"
    : unavailable.length
      ? "A busca não foi concluída em todos os veículos. Tente novamente."
      : "Não encontramos matérias suficientemente semelhantes nos outros veículos consultados.";
  if (count && unavailable.length) {
    get("search-status").textContent += ` Busca indisponível em: ${unavailable.join(", ")}.`;
  }
}

async function openResult(analysisType) {
  const current = ++generation;
  get("read-page").disabled = true;
  get("read-selection").disabled = true;
  get("status").textContent = "Lendo o conteúdo…";
  let timeout;
  try {
    const data = await captureActiveTab(analysisType);
    if (current !== generation) return;
    get("page-title").textContent = data.title || "Página sem título disponível";
    get("sources").replaceChildren();
    get("search-status").textContent = "Procurando esta notícia nos outros veículos…";
    get("home-screen").hidden = true;
    get("result-screen").hidden = false;
    get("result-title").focus();
    get("status").textContent = "";
    renderAnalyzing();
    const controller = new AbortController();
    searchController = controller;
    timeout = setTimeout(() => controller.abort(), 180_000);
    const analysis = analyzeText(data, controller.signal)
      .then(result => { if (current === generation) renderVerdict(result); })
      .catch(error => { if (current === generation) renderVerdictError(error); });
    const result = await findRelatedNews(data, controller.signal, message => {
      if (current === generation) get("search-status").textContent = message;
    });
    if (current === generation) renderSources(result);
    await analysis;
  } catch (error) {
    if (current !== generation) return;
    const message = error.name === "AbortError"
      ? "A busca demorou demais. Tente novamente."
      : error.message || "Não foi possível consultar as notícias.";
    get(get("result-screen").hidden ? "status" : "search-status").textContent = message;
  } finally {
    clearTimeout(timeout);
    if (current === generation) {
      get("read-page").disabled = false;
      get("read-selection").disabled = false;
    }
  }
}

get("read-page").addEventListener("click", () => openResult("pagina_completa"));
get("read-selection").addEventListener("click", () => openResult("selecao"));
get("back").addEventListener("click", () => {
  generation += 1;
  searchController?.abort();
  get("sources").replaceChildren();
  get("result-screen").hidden = true;
  get("home-screen").hidden = false;
  get("read-page").disabled = false;
  get("read-selection").disabled = false;
  get("status").textContent = "";
  get("home-title").focus();
});
get("close").addEventListener("click", () => window.close());
get("minimize").addEventListener("click", () => window.close());

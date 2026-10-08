import { captureActiveTab } from "../shared/page-context.js";
import { findRelatedNews } from "../shared/api.js";
import { analyzeText } from "../shared/analysis-api.js";

const get = (id) => document.getElementById(id);
let searchController;
let analysisController;
let generation = 0;

function renderAnalysis(result) {
  const percentage = Number.isFinite(result.fake_probability)
    ? `${Math.round(result.fake_probability * 100)}%`
    : "—";
  const classifications = {
    confiavel: "Fonte na lista confiável",
    suspeito: "Suspeito",
    nao_verificado: "Não verificado",
  };
  const methods = {
    ml_model: "modelo de aprendizado de máquina",
    ai_fallback: "análise complementar",
    whitelist: "lista de fontes confiáveis",
    analise_linguistica: "análise linguística",
  };
  get("fake-percent").textContent = percentage;
  get("analysis-status").textContent = `Classificação: ${classifications[result.classification] || "Não verificado"}. Confiança: ${Math.round(result.confidence * 100)}%. Método: ${methods[result.method] || result.method}.`;
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
    get("fake-percent").textContent = "…";
    get("analysis-status").textContent = "Analisando o texto no modelo local…";
    analysisController = new AbortController();
    searchController = new AbortController();
    const analysisTimeout = setTimeout(() => analysisController.abort(), 30_000);
    timeout = setTimeout(() => searchController.abort(), 180_000);
    const analysisTask = analyzeText({ ...data, analysis_type: analysisType }, analysisController.signal)
      .then(result => {
        if (current === generation) renderAnalysis(result);
      })
      .catch(error => {
        if (current === generation) {
          get("fake-percent").textContent = "—";
          get("analysis-status").textContent = error.name === "AbortError"
            ? "A análise local demorou demais. Tente novamente."
            : error.message || "Não foi possível consultar o modelo local.";
        }
      })
      .finally(() => clearTimeout(analysisTimeout));
    const sourcesTask = findRelatedNews(data, searchController.signal, message => {
      if (current === generation) get("search-status").textContent = message;
    })
      .then(result => { if (current === generation) renderSources(result); })
      .catch(error => {
        if (current === generation) {
          get("search-status").textContent = error.name === "AbortError"
            ? "A busca demorou demais. Tente novamente."
            : error.message || "Não foi possível consultar as notícias.";
        }
      });
    await Promise.all([analysisTask, sourcesTask]);
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
      analysisController = undefined;
      searchController = undefined;
    }
  }
}

get("read-page").addEventListener("click", () => openResult("pagina_completa"));
get("read-selection").addEventListener("click", () => openResult("selecao"));
get("back").addEventListener("click", () => {
  generation += 1;
  searchController?.abort();
  analysisController?.abort();
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

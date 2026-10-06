import { captureActiveTab } from "../shared/page-context.js";
import { findRelatedNews } from "../shared/api.js";

const get = (id) => document.getElementById(id);
let animationFrame;
let searchController;
let generation = 0;
function animatePercentage() {
  cancelAnimationFrame(animationFrame);
  const percentElement = get("fake-percent");
  let atual = 0;
  let waveX = 0;
  function frame() {
    atual = Math.min(50, atual + 0.5);
    waveX -= 1;
    percentElement.textContent = `${Math.floor(atual)}%`;
    percentElement.style.setProperty("--wave-x", `${waveX}px`);
    percentElement.style.setProperty("--fill-y", `${30 - atual * 0.36}px`);
    animationFrame = requestAnimationFrame(frame);
  }
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    percentElement.textContent = "50%";
    percentElement.style.setProperty("--fill-y", "12px");
    return;
  }
  frame();
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
    animatePercentage();
    const controller = new AbortController();
    searchController = controller;
    timeout = setTimeout(() => controller.abort(), 180_000);
    const result = await findRelatedNews(data, controller.signal, message => {
      if (current === generation) get("search-status").textContent = message;
    });
    if (current === generation) renderSources(result);
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
  cancelAnimationFrame(animationFrame);
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

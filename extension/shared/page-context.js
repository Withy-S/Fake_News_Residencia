export function capturePageContext(analysisType = "selecao") {
  const clean = (value) => (value || "").replace(/\s+/g, " ").trim();
  const title = [
    document.querySelector("article h1")?.textContent,
    document.querySelector("main h1")?.textContent,
    document.querySelector("h1")?.textContent,
    document.querySelector('meta[property="og:title"]')?.content,
    document.title,
  ].map(clean).find(Boolean) || null;
  const pageText = analysisType === "pagina_completa"
    ? [document.querySelector("article"), document.querySelector("main"), document.body]
      .map((element) => element?.innerText?.trim()).find(Boolean) || ""
    : (window.getSelection()?.toString() || "").trim();

  return {
    analysis_type: analysisType,
    text: pageText,
    title: title ? Array.from(title).slice(0, 500).join("") : null,
    url: window.location.href,
  };
}

export async function captureActiveTab(analysisType = "selecao") {
  if (!["selecao", "pagina_completa"].includes(analysisType)) {
    throw new Error("Modo de leitura inválido.");
  }
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !/^https?:\/\//i.test(tab.url || "")) {
    throw new Error("Abra uma notícia em uma página HTTP ou HTTPS para analisar.");
  }
  let results;
  try {
    results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: capturePageContext,
      args: [analysisType],
    });
  } catch {
    throw new Error("Não foi possível ler esta página. Algumas páginas do navegador são protegidas.");
  }
  const data = results[0]?.result;
  if (!data?.text) {
    if (analysisType === "pagina_completa") {
      throw new Error("Não foi encontrado texto nesta página. Abra uma notícia e tente novamente.");
    }
    throw new Error("Selecione um trecho da notícia e abra a extensão novamente. Não precisa selecionar o título.");
  }
  if (analysisType === "selecao" && Array.from(data.text).length > 20_000) {
    throw new Error("Selecione um trecho menor, com até 20.000 caracteres.");
  }
  return data;
}

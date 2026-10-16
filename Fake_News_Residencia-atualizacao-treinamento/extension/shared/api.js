import { searchArticles, selectCoverage } from './news-search.js';

// API de análise publicada no Amazon API Gateway.
const BACKEND_URL = 'https://8bjadf63m7.execute-api.sa-east-1.amazonaws.com';

export async function analyzeText(data, signal) {
  let response;
  try {
    response = await fetch(`${BACKEND_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal,
      body: JSON.stringify({
        analysis_type: data.analysis_type,
        text: data.text,
        title: data.title || undefined,
        url: data.url || undefined,
      }),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('Não foi possível acessar a API de análise. Verifique sua conexão e tente novamente.');
  }
  const body = await response.json();
  if (!response.ok || body.status === 'error') {
    throw new Error(body.error?.message || 'Não foi possível consultar a análise.');
  }
  return body;
}

export async function findRelatedNews(data, signal, onProgress = () => {}) {
  const found = await searchArticles(data, signal);
  if (!found.articles.length) return { sources: [], unavailable_publishers: found.unavailable_publishers };
  if (signal?.aborted) throw new DOMException('Busca cancelada', 'AbortError');
  onProgress('Comparando as matérias encontradas… O modelo local pode demorar no primeiro uso.');
  const ranked = [];
  for (let offset = 0; offset < found.articles.length; offset += 8) {
    if (signal?.aborted) throw new DOMException('Busca cancelada', 'AbortError');
    const response = await chrome.runtime.sendMessage({
      action: 'comparar_noticias', texto: found.subject.slice(0, 1000),
      noticiasConfiaveis: found.articles.slice(offset, offset + 8),
    });
    if (signal?.aborted) throw new DOMException('Busca cancelada', 'AbortError');
    if (!response?.ok) throw new Error(response?.erro || 'Não foi possível comparar as matérias encontradas.');
    ranked.push(...response.resultados);
  }
  return {
    sources: selectCoverage(found.subject, ranked, data),
    unavailable_publishers: found.unavailable_publishers,
  };
}

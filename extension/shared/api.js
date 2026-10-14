import { searchArticles, selectCoverage } from './news-search.js';

// Backend local (RF10/RF11). Roda com `uvicorn app.main:app --reload` em backend/.
const BACKEND_URL = 'http://127.0.0.1:8000';

export async function analyzeText(data, signal) {
  if (typeof data.text !== 'string' || data.text.length < 20) {
    throw new Error('Envie pelo menos 20 caracteres para análise.');
  }
  if (data.text.length > 20_000) {
    throw new Error('O texto da página excede o limite de 20.000 caracteres da API.');
  }
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
    throw new Error('O backend não está respondendo. Verifique se ele está rodando em localhost:8000.');
  }
  const body = await response.json();
  if (!response.ok || body.status === 'error') {
    throw new Error(body.error?.message || 'Não foi possível consultar a análise.');
  }
  if (body.fake_probability !== null && body.fake_probability !== undefined &&
      (!Number.isFinite(body.fake_probability) || body.fake_probability < 0 || body.fake_probability > 1)) {
    throw new Error('A API retornou uma probabilidade inválida.');
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

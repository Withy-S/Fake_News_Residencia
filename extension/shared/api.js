import { searchArticles, selectCoverage } from './news-search.js';

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

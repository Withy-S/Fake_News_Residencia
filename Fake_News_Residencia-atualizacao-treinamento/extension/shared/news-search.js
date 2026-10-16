export const PUBLISHERS = [
  { name: 'R7', domain: 'r7.com', hosts: ['r7.com', 'www.r7.com', 'noticias.r7.com'] },
  { name: 'Correio Braziliense', domain: 'correiobraziliense.com.br', hosts: ['correiobraziliense.com.br', 'www.correiobraziliense.com.br'] },
  { name: 'CNN Brasil', domain: 'cnnbrasil.com.br', hosts: ['cnnbrasil.com.br', 'www.cnnbrasil.com.br'] },
];
const STOP = new Set('que para com dos das uma pelo pela como mais sobre apos entre esta esse essa noticia noticias veja saiba entenda cnn correio braziliense'.split(' '));
export function terms(text) {
  return [...new Set((text || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .match(/[a-z0-9]+/g) || [])].filter(word => (word.length > 2 || /^\d+$/.test(word)) && !STOP.has(word));
}
export function searchSubject(data) {
  const title = (data.title || '').replace(/\s+[|–—]\s+.*$/, '').trim();
  return terms(title).length >= 3 ? title : (data.text || '').slice(0, 500);
}

export function parseFeed(xml, publisher) {
  const document = new DOMParser().parseFromString(xml, 'application/xml');
  if (document.querySelector('parsererror') || !document.querySelector('rss > channel')) {
    throw new Error('O serviço de busca retornou uma resposta inválida.');
  }
  const found = new Map();
  for (const item of document.querySelectorAll('channel > item')) {
    const source = item.querySelector('source');
    const link = item.querySelector('link')?.textContent?.trim();
    let sourceUrl, articleUrl;
    try { sourceUrl = new URL(source?.getAttribute('url')); articleUrl = new URL(link); } catch { continue; }
    if (!publisher.hosts.includes(sourceUrl.hostname) || !['http:', 'https:'].includes(sourceUrl.protocol)) continue;
    if (articleUrl.protocol !== 'https:' || articleUrl.host !== 'news.google.com' ||
        !/^\/(rss\/)?articles\//.test(articleUrl.pathname)) continue;
    let title = item.querySelector('title')?.textContent?.trim();
    const suffix = ` - ${source.textContent.trim()}`;
    if (title?.endsWith(suffix)) title = title.slice(0, -suffix.length).trim();
    if (!title || title.length > 1000) continue;
    found.set(articleUrl.pathname, {
      titulo: title, texto: '', link: articleUrl.href,
      publisher: publisher.name, published_at: item.querySelector('pubDate')?.textContent || null,
    });
  }
  return [...found.values()];
}
export function buildQueries(subject) {
  const words = terms(subject).slice(0, 12);
  return [...new Set([
    words.join(' '),
    words.slice(0, 5).join(' '),
    words.slice(0, 3).join(' '),
  ])].filter(query => terms(query).length >= 3);
}

async function searchPublisher(publisher, queries, keywords, signal) {
  const responses = await Promise.all(queries.map(async query => {
    try {
      const url = new URL('https://news.google.com/rss/search');
      url.search = new URLSearchParams({ q: `${query} site:${publisher.domain}`, hl: 'pt-BR', gl: 'BR', ceid: 'BR:pt-419' });
      const response = await fetch(url, { signal });
      if (!response.ok) throw new Error('Busca indisponível');
      return { articles: parseFeed(await response.text(), publisher), failed: false };
    } catch (error) {
      if (signal?.aborted) throw error;
      return { articles: [], failed: true };
    }
  }));
  return {
    articles: diversifyCandidates(responses.map(response => response.articles), keywords),
    publisher, failed: responses.some(response => response.failed),
  };
}
export function diversifyCandidates(results, keywords) {
  const selected = new Map();
  const distinct = new Map();
  const add = (target, article) => target.set(new URL(article.link).pathname, article);
  for (const articles of results) {
    const relevant = articles.filter(article => terms(article.titulo).some(t => keywords.includes(t)));
    for (const article of relevant) add(distinct, article);
    for (const article of relevant.slice(0, 3)) add(selected, article);
  }
  const scored = [...distinct.values()].map(article => {
    const articleTerms = terms(article.titulo);
    const overlap = articleTerms.filter(t => keywords.includes(t)).length;
    return { article, score: overlap / Math.sqrt(Math.max(1, articleTerms.length)) };
  }).sort((a, b) => b.score - a.score);
  for (const { article } of scored) {
    if (selected.size >= 16) break;
    add(selected, article);
  }
  return [...selected.values()].slice(0, 16);
}

export async function searchArticles(data, signal) {
  const subject = searchSubject(data);
  const keywords = terms(subject).slice(0, 12);
  if (keywords.length < 3) throw new Error('Não há informação suficiente para buscar esta notícia. Selecione um trecho maior.');
  const originalHost = new URL(data.url).hostname;
  const publishers = PUBLISHERS.filter(p => originalHost !== p.domain && !originalHost.endsWith(`.${p.domain}`));
  const queries = buildQueries(subject);
  const results = await Promise.all(publishers.map(publisher => searchPublisher(publisher, queries, keywords, signal)));
  return {
    subject, articles: results.flatMap(r => r.articles),
    unavailable_publishers: results.filter(r => r.failed).map(r => r.publisher.name),
  };
}

const GENERIC_NAMES = new Set('copa mundo material policia cientistas governo presidente selecao tribunal justica banco central ministerio veja saiba entenda'.split(' '));
function namedTerms(title) {
  const words = title.match(/\b[\p{Lu}][\p{L}\p{N}-]+/gu) || [];
  return [...new Set(words.flatMap(terms))].filter(word => !GENERIC_NAMES.has(word));
}

const RESULT_TERMS = new Set(['resultado', 'resultados', 'apuracao', 'totalizacao', 'boletim']);
const PLACE_TERMS = new Set(['mapa', 'mapas', 'local', 'locais', 'secao', 'secoes', 'municipio', 'municipios', 'cidade', 'cidades', 'estado', 'estados', 'escola', 'escolas']);
const EXPLAIN_TERMS = new Set(['entenda', 'como', 'caminho', 'divulgacao', 'horas', 'funciona', 'conferir']);
function rawTerms(title) {
  return (title || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().match(/[a-z0-9]+/g) || [];
}
const has = (words, vocabulary) => words.some(word => vocabulary.has(word));

export function coverageRelation(subject, candidate) {
  const sourceTerms = rawTerms(subject), candidateTerms = rawTerms(candidate);
  const electionResults = sourceTerms.some(t => ['eleicao', 'eleicoes', 'eleitoral'].includes(t)) && has(sourceTerms, RESULT_TERMS);
  if (electionResults) {
    if (candidateTerms.some(t => ['pesquisa', 'pesquisas', 'intencoes', 'candidatos'].includes(t))) return null;
    if (!has(candidateTerms, RESULT_TERMS)) return null;
    if (has(sourceTerms, PLACE_TERMS) && !has(candidateTerms, PLACE_TERMS)) {
      return has(candidateTerms, EXPLAIN_TERMS) ? 'context' : null;
    }
  }
  return 'coverage';
}

export function selectCoverage(subject, ranked, context = {}) {
  const keywords = terms(subject).slice(0, 12);
  const names = namedTerms(subject);
  const years = keywords.filter(t => /^(19|20)\d{2}$/.test(t));
  const urlDate = context.url?.match(/\/(20\d{2})\/(\d{2})\/(\d{2})\//);
  const originalDate = urlDate ? Date.UTC(Number(urlDate[1]), Number(urlDate[2]) - 1, Number(urlDate[3])) : null;
  const candidates = [...ranked].sort((a, b) => b.similaridade - a.similaridade).filter(article => {
    const articleTerms = terms(article.titulo);
    const articleYears = articleTerms.filter(t => /^(19|20)\d{2}$/.test(t));
    const overlap = articleTerms.filter(t => keywords.includes(t)).length;
    const differentYear = years.length && articleYears.length && !years.some(y => articleYears.includes(y));
    const namedOverlap = names.filter(name => articleTerms.includes(name)).length;
    const differentNames = names.length >= 2 && namedOverlap / names.length < 0.6;
    const published = Date.parse(article.published_at);
    const differentDate = originalDate !== null && Number.isFinite(published) && Math.abs(published - originalDate) > 30 * 86400_000;
    return Number.isFinite(article.similaridade) && article.similaridade >= 60 && overlap >= 2 &&
      !differentYear && !differentNames && !differentDate && PUBLISHERS.some(p => p.name === article.publisher);
  });
  const sources = [];
  const publishers = [...new Set(candidates.map(a => a.publisher))];
  for (const publisher of publishers) {
    const articles = candidates.filter(a => a.publisher === publisher);
    const coverage = articles.filter(a => coverageRelation(subject, a.titulo) === 'coverage').slice(0, 1);
    const contextual = articles.filter(a => coverageRelation(subject, a.titulo) === 'context' && a.similaridade >= 70).slice(0, 2);
    for (const article of [...coverage, ...contextual]) {
      sources.push({ title: article.titulo, url: article.link, publisher: article.publisher,
        published_at: article.published_at, relation: coverageRelation(subject, article.titulo) });
    }
  }
  return sources;
}

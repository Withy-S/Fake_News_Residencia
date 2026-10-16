import { env, pipeline } from './lib/transformers.js';
env.allowLocalModels = false;
env.allowRemoteModels = true;
env.useBrowserCache = true;
env.backends.onnx.wasm.wasmPaths = chrome.runtime.getURL('lib/wasm/');
env.backends.onnx.wasm.numThreads = 1;
env.backends.onnx.wasm.proxy = false;

let extractorPromise = null;

export function getExtractor() {
  if (!extractorPromise) {
    extractorPromise = pipeline('feature-extraction', 'Xenova/paraphrase-multilingual-MiniLM-L12-v2')
      .catch((error) => {
        extractorPromise = null;
        throw error;
      });
  }
  return extractorPromise;
}

export function cosineSimilarity(a, b) {
  if (!a.length || a.length !== b.length) {
    throw new Error('Os vetores precisam ter a mesma dimensão e não podem ser vazios.');
  }
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    if (!Number.isFinite(a[i]) || !Number.isFinite(b[i])) {
      throw new Error('Os vetores devem conter apenas números finitos.');
    }
    dot += a[i] * b[i];
    normA += a[i] ** 2;
    normB += b[i] ** 2;
  }
  if (normA === 0 || normB === 0) return 0;
  return Math.max(-1, Math.min(1, dot / (Math.sqrt(normA) * Math.sqrt(normB))));
}

export async function compararNoticias(texto, noticias) {
  if (typeof texto !== 'string' || !texto.trim() || texto.length > 1000) {
    throw new Error('O título deve ter entre 1 e 1.000 caracteres.');
  }
  if (!Array.isArray(noticias) || noticias.length < 1 || noticias.length > 20) {
    throw new Error('Envie entre 1 e 20 notícias de referência.');
  }
  for (const noticia of noticias) {
    if (!noticia || typeof noticia.titulo !== 'string' || !noticia.titulo.trim() ||
        noticia.titulo.length > 1000 || typeof noticia.texto !== 'string' ||
        noticia.texto.length > 4000 || typeof noticia.link !== 'string' ||
        !['https:', 'http:'].includes(new URL(noticia.link).protocol)) {
      throw new Error('Notícia de referência inválida.');
    }
  }
  const extractor = await getExtractor();
  const output = await extractor([texto.trim(), ...noticias.map(n => n.titulo.trim())], {
    pooling: 'mean', normalize: true,
  });
  const [userVector, ...referenceVectors] = output.tolist();
  return noticias.map((noticia, i) => ({
    ...noticia,
    similaridade: Math.max(0, cosineSimilarity(userVector, referenceVectors[i])) * 100,
  })).sort((a, b) => b.similaridade - a.similaridade);
}
let queue = Promise.resolve();
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.action !== 'comparar_noticias' || sender.id !== chrome.runtime.id) return false;
  queue = queue.then(() => compararNoticias(message.texto, message.noticiasConfiaveis))
    .then(
      resultados => sendResponse({ ok: true, resultados }),
      error => sendResponse({ ok: false, erro: error.message || 'Não foi possível executar o modelo.' }),
    ).catch(() => {});
  return true;
});

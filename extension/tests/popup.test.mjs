import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';

const source = await readFile(new URL('../popup/popup.js', import.meta.url), 'utf8');

function setup() {
  const elements = new Map();
  const element = () => ({
    hidden: false, textContent: '', disabled: false, children: [], style: { setProperty() {} },
    classList: { toggle() {}, add() {}, remove() {} },
    listeners: {}, addEventListener(event, fn) { this.listeners[event] = fn; },
    focus() {}, replaceChildren() { this.children = []; }, append(child) { this.children.push(child); },
  });
  const get = (id) => {
    if (!elements.has(id)) { const el = element(); el.hidden = id === 'result-screen'; elements.set(id, el); }
    return elements.get(id);
  };
  const state = {
    calls: [], captureError: false, newsError: false, analyzeError: false,
    result: { sources: [], unavailable_publishers: [] },
    analysis: { status: 'ok', classification: 'suspeito', confidence: 0.7, method: 'ml_model', justifications: ['Linguagem sensacionalista.'] },
  };
  const context = vm.createContext({
    document: { getElementById: get, createElement: element },
    window: { matchMedia: () => ({ matches: true }), close() {} },
    setTimeout, clearTimeout, AbortController, URL,
    captureActiveTab: async (mode) => {
      state.calls.push(mode);
      if (state.captureError) throw new Error('Selecione um trecho');
      return { title: '<Título>', url: 'https://example.org/', text: 'Texto' };
    },
    findRelatedNews: async () => {
      if (state.newsError) throw new Error('Busca indisponível');
      return state.result;
    },
    analyzeText: async () => {
      if (state.analyzeError) throw new Error('Backend indisponível');
      return state.analysis;
    },
  });
  vm.runInContext(source.replace(/^import .*;\n/gm, ''), context);
  return { get, state, context };
}

test('dois modos, resultado, retorno e falha de captura', async () => {
  const { get, state } = setup();
  assert.equal(state.calls.length, 0);
  for (const [button, mode] of [['read-page', 'pagina_completa'], ['read-selection', 'selecao']]) {
    await get(button).listeners.click();
    assert.equal(state.calls.at(-1), mode);
    assert.equal(get('result-screen').hidden, false);
    assert.equal(get('home-screen').hidden, true);
    assert.equal(get('fake-percent').textContent, '70%');
    assert.equal(get('result-title').textContent, 'Conteúdo possivelmente suspeito');
    assert.equal(get('verdict-tag').textContent, 'MODELO DE ML');
    assert.equal(get('verdict-detail').textContent, 'Linguagem sensacionalista.');
    assert.equal(get('page-title').textContent, '<Título>');
    get('back').listeners.click();
    assert.equal(get('result-screen').hidden, true);
  }
  state.captureError = true;
  await get('read-selection').listeners.click();
  assert.equal(get('status').textContent, 'Selecione um trecho');
  assert.equal(get('result-screen').hidden, true);
});

test('análise indisponível não impede de ver as fontes relacionadas', async () => {
  const { get, state } = setup();
  state.analyzeError = true;
  await get('read-page').listeners.click();
  assert.equal(get('result-screen').hidden, false);
  assert.equal(get('result-title').textContent, 'Análise indisponível');
  assert.equal(get('verdict-detail').textContent, 'Backend indisponível');
  assert.equal(get('verdict-tag').hidden, true);
});

test('classificação confiável mostra baixa chance de fake, em tom seguro', async () => {
  const { get, state } = setup();
  state.analysis = { status: 'ok', classification: 'confiavel', confidence: 0.9, method: 'whitelist', justifications: [] };
  await get('read-page').listeners.click();
  assert.equal(get('fake-percent').textContent, '10%');
  assert.equal(get('verdict-tag').textContent, 'FONTE CONFIÁVEL');
  assert.equal(get('verdict-detail').textContent, 'Confiança do modelo: 90%.');
});

test('só cria botões de matérias retornadas e permite resultado vazio', async () => {
  const { get, state } = setup();
  state.result.sources = [
    { title: 'Matéria encontrada', publisher: 'CNN Brasil', url: 'https://news.google.com/rss/articles/real', relation: 'context' },
    { title: 'Portal', publisher: 'R7', url: 'https://www.r7.com/' },
    { title: 'Inválido', publisher: 'R7', url: 'javascript:alert(1)' },
  ];
  await get('read-page').listeners.click();
  assert.equal(get('sources').children.length, 1);
  const link = get('sources').children[0].children[0];
  assert.equal(link.textContent, 'Matéria encontrada');
  assert.equal(link.href, 'https://news.google.com/rss/articles/real');
  assert.equal(link.children[0].textContent, 'CNN Brasil • Contexto sobre o tema');
  get('back').listeners.click();
  state.result.sources = [];
  await get('read-page').listeners.click();
  assert.equal(get('sources').children.length, 0);
  assert.match(get('search-status').textContent, /Não encontramos matérias/);
});

test('falha de busca não é apresentada como ausência de matérias', async () => {
  const { get, state } = setup();
  state.newsError = true;
  await get('read-page').listeners.click();
  assert.equal(get('result-screen').hidden, false);
  assert.equal(get('search-status').textContent, 'Busca indisponível');
  assert.equal(get('sources').children.length, 0);
});

test('resposta atrasada não sobrescreve tela depois de nova consulta', async () => {
  const { get, context } = setup();
  let resolve;
  context.findRelatedNews = () => new Promise(r => { resolve = r; });
  const pending = get('read-page').listeners.click();
  await new Promise(r => setImmediate(r));
  get('back').listeners.click();
  resolve({ sources: [], unavailable_publishers: [] });
  await pending;
  assert.equal(get('result-screen').hidden, true);
  assert.equal(get('home-screen').hidden, false);
});

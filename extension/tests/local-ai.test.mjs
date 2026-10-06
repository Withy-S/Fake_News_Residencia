import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';

const code = await readFile(new URL('../background.js', import.meta.url), 'utf8');
function setup(pipeline) {
  let listener;
  const context = vm.createContext({
    env: { backends: { onnx: { wasm: {} } } }, pipeline, URL,
    chrome: { runtime: { id: 'test', getURL: p => `chrome-extension://test/${p}`,
      onMessage: { addListener: callback => { listener = callback; } } } },
  });
  vm.runInContext(code.replace(/^import .*;\n/gm, '').replace(/^export /gm, ''), context);
  return { context, listener };
}

test('cosseno: iguais, ortogonais, opostos e norma zero', () => {
  const { context: c } = setup();
  assert.equal(c.cosineSimilarity([1, 0], [1, 0]), 1);
  assert.equal(c.cosineSimilarity([1, 0], [0, 1]), 0);
  assert.equal(c.cosineSimilarity([1, 0], [-1, 0]), -1);
  assert.equal(c.cosineSimilarity([0, 0], [1, 0]), 0);
  assert.throws(() => c.cosineSimilarity([], []));
  assert.throws(() => c.cosineSimilarity([1], [1, 2]));
  assert.throws(() => c.cosineSimilarity([NaN], [1]));
});

test('singleton compartilha carregamento e permite tentar novamente após erro', async () => {
  let calls = 0;
  const extractor = () => {};
  const { context: c } = setup(async () => {
    calls++;
    if (calls === 1) throw new Error('offline');
    return extractor;
  });
  await assert.rejects(c.getExtractor(), /offline/);
  const [a, b] = await Promise.all([c.getExtractor(), c.getExtractor()]);
  assert.equal(calls, 2);
  assert.equal(a, b);
});

const news = [
  { titulo: 'Ortogonal', texto: 'Exemplo', link: 'https://example.com/1' },
  { titulo: 'Igual', texto: 'Exemplo', link: 'https://example.com/2' },
  { titulo: 'Oposto', texto: 'Exemplo', link: 'https://example.com/3' },
];

test('pooling, percentuais e ordenação calculados a partir dos embeddings', async () => {
  const { context: c } = setup(async (task, model) => {
    assert.equal(task, 'feature-extraction');
    assert.equal(model, 'Xenova/paraphrase-multilingual-MiniLM-L12-v2');
    return async (texts, options) => {
      assert.deepEqual(Array.from(texts), ['Meu título', 'Ortogonal', 'Igual', 'Oposto']);
      assert.equal(options.pooling, 'mean');
      assert.equal(options.normalize, true);
      return { tolist: () => [[1, 0], [0, 1], [1, 0], [-1, 0]] };
    };
  });
  const result = await c.compararNoticias('Meu título', news);
  assert.equal(result[0].titulo, 'Igual');
  assert.equal(result[0].similaridade, 100);
  assert.equal(result[1].similaridade, 0);
  assert.equal(result[2].similaridade, 0);
  assert.equal(news[0].titulo, 'Ortogonal');
});

test('listener mantém canal assíncrono e responde falhas sem travar a fila', async () => {
  const { listener } = setup(async () => async () => ({ tolist: () => [[1], [1]] }));
  assert.equal(listener({ action: 'outro' }, { id: 'test' }, () => {}), false);
  assert.equal(listener({ action: 'comparar_noticias' }, { id: 'outro' }, () => {}), false);
  const send = (texto, noticiasConfiaveis) => new Promise(resolve => {
    assert.equal(listener({ action: 'comparar_noticias', texto, noticiasConfiaveis },
      { id: 'test' }, resolve), true);
  });
  assert.equal((await send('', news)).ok, false);
  assert.equal((await send('Título', [news[0]])).ok, true);
  assert.equal((await send('Título', [{ ...news[0], link: 'javascript:alert(1)' }])).ok, false);
});

test('manifest aponta para o novo popup e permite WASM local sem backend', async () => {
  const manifest = JSON.parse(await readFile(new URL('../manifest.json', import.meta.url)));
  assert.equal(manifest.background.type, 'module');
  assert.equal(manifest.action.default_popup, 'popup/popup.html');
  assert.match(manifest.content_security_policy.extension_pages, /wasm-unsafe-eval/);
  assert.deepEqual(manifest.host_permissions, ['https://news.google.com/*']);
});

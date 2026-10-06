import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test, afterEach } from 'node:test';

const source = await readFile(new URL('../shared/page-context.js', import.meta.url), 'utf8');
const { capturePageContext, captureActiveTab } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
);

function page({ og, article, main, title = 'Título da aba', selection = 'Trecho selecionado', articleText, mainText, bodyText } = {}) {
  globalThis.document = {
    title,
    body: { innerText: bodyText },
    querySelector(selector) {
      return {
        'meta[property="og:title"]': og === undefined ? null : { content: og },
        'article': { innerText: articleText },
        'main': { innerText: mainText },
        'article h1': article === undefined ? null : { textContent: article },
        'main h1': main === undefined ? null : { textContent: main },
      }[selector];
    },
  };
  globalThis.window = {
    getSelection: () => ({ toString: () => selection }),
    location: { href: 'https://example.org/noticia' },
  };
  globalThis.chrome = {
    tabs: { query: async () => [{ id: 1, url: window.location.href }] },
    scripting: { executeScript: async ({ func, args }) => [{ result: func(...args) }] },
  };
}
afterEach(() => {
  delete globalThis.document;
  delete globalThis.window;
  delete globalThis.chrome;
});

test('captura título sem incluí-lo no trecho selecionado', async () => {
  page({ og: 'Título abreviado para compartilhar', article: '  Título\n da notícia ' });
  assert.deepEqual(await captureActiveTab(), {
    analysis_type: 'selecao', text: 'Trecho selecionado',
    title: 'Título da notícia', url: 'https://example.org/noticia',
  });
});

test('ignora títulos vazios e usa article, main e título da aba em ordem', () => {
  page({ og: '  ', article: 'Matéria', main: 'Principal' });
  assert.equal(capturePageContext().title, 'Matéria');
  page({ article: ' ', main: 'Principal' });
  assert.equal(capturePageContext().title, 'Principal');
  page();
  assert.equal(capturePageContext().title, 'Título da aba');
  page({ title: '' });
  assert.equal(capturePageContext().title, null);
});

test('limita o título a 500 caracteres sem cortar pares Unicode', () => {
  page({ og: '😀'.repeat(501) });
  assert.equal(capturePageContext().title, '😀'.repeat(500));
});

test('orienta usuário quando não há seleção', async () => {
  page({ selection: ' ' });
  await assert.rejects(captureActiveTab(), /Selecione um trecho/);
});

test('não trunca silenciosamente seleções maiores que o contrato da API', async () => {
  page({ selection: 'a'.repeat(20_001) });
  await assert.rejects(captureActiveTab(), /20.000 caracteres/);
});

test('explica bloqueio em páginas internas e falhas de permissão', async () => {
  page();
  chrome.tabs.query = async () => [{ id: 1, url: 'chrome://extensions' }];
  await assert.rejects(captureActiveTab(), /HTTP ou HTTPS/);
  page();
  chrome.scripting.executeScript = async () => { throw new Error('denied'); };
  await assert.rejects(captureActiveTab(), /páginas.*protegidas/);
});


test('página inteira captura a matéria sem precisar de seleção', async () => {
  page({ selection: '', articleText: 'Conteúdo da matéria', mainText: 'Outros conteúdos', bodyText: 'Menus e rodapé' });
  const data = await captureActiveTab('pagina_completa');
  assert.equal(data.analysis_type, 'pagina_completa');
  assert.equal(data.text, 'Conteúdo da matéria');
});

test('página inteira usa main e body quando a matéria está ausente ou vazia', async () => {
  page({ articleText: ' ', mainText: 'Conteúdo principal' });
  assert.equal((await captureActiveTab('pagina_completa')).text, 'Conteúdo principal');
  page({ bodyText: 'Texto da página' });
  assert.equal((await captureActiveTab('pagina_completa')).text, 'Texto da página');
});

test('captura local da página inteira não corta textos longos', async () => {
  page({ articleText: 'a'.repeat(25_000) });
  assert.equal((await captureActiveTab('pagina_completa')).text.length, 25_000);
});

test('página vazia e modo inválido recebem mensagens específicas', async () => {
  page();
  await assert.rejects(captureActiveTab('pagina_completa'), /Não foi encontrado texto/);
  await assert.rejects(captureActiveTab('invalido'), /Modo de leitura inválido/);
});


test('usa metadados quando não há título visível da matéria', () => {
  page({ og: 'Título de compartilhamento', title: 'Nome do portal' });
  assert.equal(capturePageContext().title, 'Título de compartilhamento');
});

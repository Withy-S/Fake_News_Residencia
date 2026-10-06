import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const code = await readFile(new URL('../shared/news-search.js', import.meta.url), 'utf8');
const { selectCoverage, searchSubject, buildQueries, diversifyCandidates, coverageRelation } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
const title = 'Argentina vence França nos pênaltis na Copa do Mundo 2022';
const article = (publisher, score, titulo = title) => ({ publisher, similaridade: score, titulo, link: 'https://news.google.com/rss/articles/test' });

test('ordena coberturas reais e limita a uma por veículo, sem retornar score como veracidade', () => {
  const results = selectCoverage(title, [article('CNN Brasil', 80), article('R7', 90), article('CNN Brasil', 95)]);
  assert.deepEqual(results.map(r => r.publisher), ['CNN Brasil', 'R7']);
  assert.equal(results[0].similaridade, undefined);
});

test('rejeita baixa similaridade, fonte externa, assunto distinto e ano contraditório', () => {
  assert.deepEqual(selectCoverage(title, [
    article('R7', 59), article('Outro portal', 99),
    article('CNN Brasil', 90, 'Chuvas causam alagamentos no litoral'),
    article('Correio Braziliense', 99, 'Espanha domina Argentina e conquista o bicampeonato da Copa Mundo'),
    article('Correio Braziliense', 95, title.replace('2022', '2018')),
  ]), []);
});

test('não preenche resultados vazios com notícias fixas', () => {
  assert.deepEqual(selectCoverage(title, []), []);
});

test('usa título capturado ou texto como alternativa', () => {
  assert.equal(searchSubject({ title: title + ' | Portal', text: 'Trecho' }), title);
  assert.equal(searchSubject({ title: '', text: 'Trecho da matéria' }), 'Trecho da matéria');
});


const radioTitle = 'Material radioativo roubado de van é localizado em terreno baldio em SP; produto seria usado para tratar paciente com câncer';
const radioUrl = 'https://g1.globo.com/sp/sao-paulo/noticia/2026/10/06/material-radioativo.ghtml';
const correioTitle = 'Polícia acha material radioativo roubado em SP; carga trataria câncer';

test('busca o caso G1/Correio com consulta curta que não exige a redação inteira', () => {
  assert.ok(buildQueries(radioTitle).includes('material radioativo roubado'));
  assert.equal(new Set(buildQueries(radioTitle)).size, buildQueries(radioTitle).length);
});

test('aceita a mesma notícia com título menor e sinônimos sem exigir 65% de palavras iguais', () => {
  const result = selectCoverage(radioTitle, [{
    ...article('Correio Braziliense', 68, correioTitle), published_at: 'Tue, 06 Oct 2026 12:00:00 GMT',
  }], { url: radioUrl });
  assert.equal(result.length, 1);
  assert.equal(result[0].title, correioTitle);
});

test('não confunde câncer ou material radioativo com outro acontecimento', () => {
  const result = selectCoverage(radioTitle, [
    article('CNN Brasil', 55, 'Cientistas descobrem nova terapia para tratar câncer'),
    { ...article('R7', 90, 'Material radioativo roubado em São Paulo é localizado'), published_at: 'Mon, 06 Oct 2014 12:00:00 GMT' },
  ], { url: radioUrl });
  assert.deepEqual(result, []);
});


const electionTitle = 'Resultado das eleições 2026 por local de votação e urna: veja no mapa quem venceu na sua escola e seção eleitoral';
const cnnExplanation = 'Eleições 2026: entenda o caminho do voto até a divulgação do resultado';

test('preserva a matéria relevante da consulta curta mesmo com muitos títulos repetindo mais palavras', () => {
  const keywords = ['resultado', 'eleicoes', '2026', 'local', 'votacao', 'urna', 'mapa'];
  const similarTitles = Array.from({ length: 25 }, (_, i) => ({
    ...article('CNN Brasil', 90, 'Resultado eleições 2026 mapa local urna votação'), link: `https://news.google.com/rss/articles/near-${i}`,
  }));
  const wanted = { ...article('CNN Brasil', 83, cnnExplanation), link: 'https://news.google.com/rss/articles/wanted' };
  const candidates = diversifyCandidates([similarTitles, [wanted, ...similarTitles]], keywords);
  assert.ok(candidates.some(a => a.link === wanted.link));
  assert.ok(candidates.length <= 16);
  assert.equal(new Set(candidates.map(a => a.link)).size, candidates.length);
});

test('G1/CNN: explicação sobre o processo é contexto, não cobertura do mesmo fato', () => {
  const results = selectCoverage(electionTitle, [article('CNN Brasil', 83, cnnExplanation)]);
  assert.equal(results.length, 1);
  assert.equal(results[0].relation, 'context');
  assert.equal(coverageRelation(electionTitle, 'Eleições 2026: confira os resultados por seção eleitoral'), 'coverage');
});

test('pesquisas e listas de candidatos não confirmam apuração mesmo com cosseno alto', () => {
  const results = selectCoverage(electionTitle, [
    article('CNN Brasil', 95, 'Pesquisa eleitoral mostra resultado das intenções de voto nas eleições 2026'),
    article('CNN Brasil', 95, 'Eleições 2026: conheça os candidatos à Presidência'),
  ]);
  assert.deepEqual(results, []);
});

test('pode apresentar uma cobertura e conteúdo contextual do mesmo veículo com rótulo correto', () => {
  const results = selectCoverage(electionTitle, [
    article('CNN Brasil', 90, 'Eleições 2026: confira o resultado por seção eleitoral'),
    article('CNN Brasil', 83, cnnExplanation),
    article('CNN Brasil', 90, 'Resultado das eleições de 2022 mostra vencedor em cada urna'),
  ]);
  assert.deepEqual(results.map(r => r.relation), ['coverage', 'context']);
});

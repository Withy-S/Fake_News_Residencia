const API_BASE_URL = 'http://127.0.0.1:8000';

export async function analyzeText(data, signal) {
  if (typeof data.text !== 'string' || data.text.length < 20) {
    throw new Error('Envie pelo menos 20 caracteres para análise.');
  }
  if (data.text.length > 20_000) {
    throw new Error('O texto da página excede o limite de 20.000 caracteres da API.');
  }
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analysis_type: data.analysis_type,
        text: data.text,
        title: data.title,
        url: data.url,
      }),
      signal,
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('Backend local indisponível. Inicie a API em http://127.0.0.1:8000.');
  }
  if (!response.ok) throw new Error('A API local não respondeu corretamente.');
  const result = await response.json();
  if (result.status !== 'ok') {
    throw new Error(result.error?.message || 'Não foi possível analisar este texto.');
  }
  if (result.fake_probability !== null &&
      (!Number.isFinite(result.fake_probability) || result.fake_probability < 0 || result.fake_probability > 1)) {
    throw new Error('A API retornou uma probabilidade inválida.');
  }
  return result;
}
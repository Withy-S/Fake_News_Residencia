import { API_BASE_URL, API_TIMEOUT_MS, MAX_TEXT_CHARS } from "./config.js";

export class AnalysisError extends Error {
  constructor(code) {
    super(code);
    this.name = "AnalysisError";
    this.code = code;
  }
}

// As mensagens ficam na extensão: a API só devolve códigos.
const MESSAGES = {
  texto_insuficiente: "O texto é curto demais para análise. Selecione um trecho maior.",
  analise_indisponivel: "A análise está indisponível no momento. Tente novamente em instantes.",
  erro_interno: "Ocorreu um erro no servidor. Tente novamente em instantes.",
  requisicao_invalida: "O servidor recusou o conteúdo enviado.",
  resposta_invalida: "O servidor devolveu uma resposta inesperada.",
  rede: "Não foi possível falar com o servidor de análise.",
  timeout: "A análise demorou demais. Tente novamente.",
};

export function messageFor(code) {
  return MESSAGES[code] ?? MESSAGES.erro_interno;
}

export async function analyzeContent(data, signal) {
  const body = {
    analysis_type: data.analysis_type,
    text: Array.from(data.text).slice(0, MAX_TEXT_CHARS).join(""),
    title: data.title,
    url: data.url,
  };

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  signal?.addEventListener("abort", () => controller.abort(), { once: true });

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    if (signal?.aborted) throw error; // cancelado pelo usuário
    throw new AnalysisError(error.name === "AbortError" ? "timeout" : "rede");
  } finally {
    clearTimeout(timer);
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new AnalysisError("resposta_invalida");
  }

  if (payload?.status === "error") {
    throw new AnalysisError(payload.error?.code ?? "erro_interno");
  }
  if (response.status === 422) throw new AnalysisError("requisicao_invalida");
  if (!response.ok || payload?.status !== "ok") {
    throw new AnalysisError("resposta_invalida");
  }
  return payload;
}

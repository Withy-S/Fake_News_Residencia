import re

from app.schemas.analyze import Classification, Method
from app.services.classifiers import ClassifierResult

# Pontos de partida para o RF07. Os pesos e o limiar precisam ser calibrados
# com dados rotulados (ex.: Fake.Br) antes de irem para produção.
SENSATIONAL_TERMS = (
    "urgente",
    "compartilhe",
    "compartilhem",
    "divulguem",
    "antes que apaguem",
    "a mídia não mostra",
    "ninguém está falando",
    "chocante",
    "bomba",
    "vazou",
)
EXTRAORDINARY_TERMS = ("cura definitiva", "100% comprovado", "cientistas escondem")
SOURCE_MARKERS = ("segundo", "de acordo com", "fonte", "http", "estudo", "pesquisa")
REPEATED_PUNCTUATION = re.compile(r"[!?]{2,}")
WORD = re.compile(r"\b\w{4,}\b")


class LinguisticClassifier:
    """Análise linguística por regras (RF07). Não precisa de modelo treinado.

    Só sinaliza "suspeito" quando há indícios; na falta deles devolve
    "não verificado" com confiança zero, para o pipeline seguir o fallback.
    Nunca devolve "confiável": ausência de indício não é evidência (RF13).
    """

    SUSPICIOUS_THRESHOLD = 0.5

    def classify(self, text: str) -> ClassifierResult:
        lower = text.lower()
        score = 0.0
        reasons: list[str] = []

        found = [t for t in SENSATIONAL_TERMS if t in lower]
        if found:
            score += min(0.4, 0.15 * len(found))
            reasons.append("Linguagem sensacionalista ou apelo para compartilhar.")

        words = WORD.findall(text)
        if words and sum(w.isupper() for w in words) / len(words) > 0.3:
            score += 0.2
            reasons.append("Tom emocional: muitas palavras em caixa alta.")

        if REPEATED_PUNCTUATION.search(text):
            score += 0.15
            reasons.append("Tom emocional: pontuação exagerada.")

        if any(t in lower for t in EXTRAORDINARY_TERMS):
            score += 0.25
            reasons.append("Alegação extraordinária sem evidência apresentada.")

        if not any(m in lower for m in SOURCE_MARKERS):
            score += 0.1
            reasons.append("O texto não cita fontes identificáveis.")

        score = round(min(score, 1.0), 2)
        if score >= self.SUSPICIOUS_THRESHOLD:
            return ClassifierResult(
                Classification.SUSPICIOUS, score, reasons, Method.LINGUISTIC
            )
        return ClassifierResult(
            Classification.UNVERIFIED,
            0.0,
            ["Nenhum indício linguístico forte foi encontrado."],
            Method.LINGUISTIC,
        )

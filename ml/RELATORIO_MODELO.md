# Relatório de Treinamento e Avaliação do Modelo de Machine Learning

**Data:** 15/10/2026 09:57:42  
**Origem dos Dados:** [Fake.br-Corpus (NILC/USP)](https://github.com/roneysco/Fake.br-Corpus) (`size_normalized_texts`)  
**Tamanho do Dataset:** 7.200 notícias (3.600 Fake / 3.600 Real), normalizadas em extensão para mitigar viés de tamanho de texto.  
**Divisão dos Dados:** 80% Treino (5.760 notícias) / 20% Teste cego (1.440 notícias), estratificado por classe.  
**Arquitetura:** Stacking Ensemble de 5 classificadores base combinados por Meta-Regressão Logística treinada via 5-Fold Out-Of-Fold Cross-Validation.

---

## 1. Diagnóstico do Modelo Anterior vs. Nova Abordagem

| Aspecto | Modelo Anterior (Descartado) | Novo Modelo (Produção) |
|---|---|---|
| **Dataset de Origem** | FakeRecogna | Fake.br-Corpus (NILC / USP) |
| **Integridade do Texto** | **Mutilado** (verbos forçados, artigos colapsados em 'o') | **Português Natural** autêntico, limpo e com estrutura sintática preservada |
| **Vazamento de Rótulo** | 64% das notícias tinham "#boato" ou "É #FAKE" no título | Sem vazamento de metadados; treino estritamente sobre o corpo da notícia |
| **Viés de Tamanho** | Sem controle de tamanho de texto | `size_normalized_texts`: pares de notícias ajustados em extensão equivalente |
| **Desempenho em Texto Real** | 80% a 99% de **falso alarme** em notícias normais | Estimativas calibradas (notícia legítima ~0% fake; fake sensacionalista ~95% fake) |

---

## 2. Modelos Base e Hiperparâmetros

1. **Baseline (TF-IDF + Regressão Logística):**
   - Vetorizador: n-gramas de palavras (1, 2), `sublinear_tf=True`, `min_df=3`, `max_df=0.85`.
   - Estimador: `LogisticRegression(max_iter=1000, random_state=42)`.
2. **SVM Calibrado (TF-IDF + LinearSVC):**
   - Vetorizador: n-gramas de palavras (1, 2), `sublinear_tf=True`.
   - Estimador: `CalibratedClassifierCV(LinearSVC(max_iter=10000), cv=5)` com calibração isotônica/sigmoide para probabilidades reais.
3. **Naive Bayes Calibrado (TF-IDF + MultinomialNB):**
   - Estimador: `CalibratedClassifierCV(MultinomialNB(alpha=0.5), cv=5)`.
4. **Char n-grams (TF-IDF de Caracteres + LinearSVC Calibrado):**
   - Vetorizador: n-gramas de caracteres com fronteira de palavra `char_wb` (3 a 5 caracteres, até 100.000 features). Captura morfologia, pontuação repetida e estilo.
5. **GBM (TF-IDF + TruncatedSVD + HistGradientBoosting):**
   - Redução de dimensionalidade via SVD (100 componentes) + Árvores de Gradiente Boosting para capturar interações não lineares.

---

## 3. Meta-Modelo (Stacking)

- **Entrada:** Logits $L_i = \ln(p_i / (1 - p_i))$ das predições out-of-fold dos 5 modelos base geradas durante a validação cruzada (5 folds) no conjunto de treino.
- **Estimador:** `LogisticRegression(max_iter=1000, random_state=42)`.
- **Coeficientes aprendidos:**
  - Baseline (LR): `-2.995`
  - SVM (Palavras): `0.938`
  - Naive Bayes: `0.132`
  - Char n-grams: `0.895`
  - GBM (SVD): `0.068`
  - Intercepto: `0.159`

---

## 4. Resultados no Conjunto de Teste Independente (1.440 notícias)

| Modelo | Acurácia | ROC-AUC | Brier Score (Calibração) |
|---|---|---|---|
| baseline (TF-IDF + LR) | 0.9167 | 0.9725 | 0.1003 |
| svm (TF-IDF + LinearSVC) | 0.9340 | 0.9811 | 0.0518 |
| nb (TF-IDF + MultinomialNB) | 0.8799 | 0.9497 | 0.0887 |
| char (Char n-grams + SVM) | 0.9437 | 0.9873 | 0.0430 |
| gbm (SVD + HistGBM) | 0.8750 | 0.9512 | 0.0896 |
| **Stacking Final (Meta-LR)** | **0.9465 (94.65%)** | **0.9896** | **0.0387** |

- **F1-Score:** `0.9464`
- **Precisão:** `0.9484`
- **Recall:** `0.9444`
- **Matriz de Confusão:**
  - Verdadeiros Negativos (Reais classificadas como Reais): `683`
  - Falsos Positivos (Reais classificadas como Fake): `37`
  - Falsos Negativos (Fake classificadas como Reais): `40`
  - Verdadeiros Positivos (Fake classificadas como Fake): `680`

---

## 5. Como Reproduzir o Treinamento

```bash
cd Fake_News_Residencia
backend/.venv/bin/python ml/treinar_modelo_fakebr.py
```

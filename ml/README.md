# ml/ — Modelo de Machine Learning (RF10)

Treina e exporta o classificador de produção: um **stacking de 5 modelos clássicos**
(TF-IDF + Regressão Logística, SVM, Naive Bayes, SVM em n-gramas de caractere,
SVD+GBM), combinados por um meta-modelo de regressão logística. O protocolo de
treino, validação e a decisão do modelo final **já foram definidos** pelo time de
dados (Mayara, Rayssa e Rafaella) num desafio paralelo de ML.

## Histórico: por que não tem BERTopic

O protocolo original (`decisao_modelo.md` do desafio de ML) decidiu por um
stacking de **6** modelos, incluindo BERTopic+LR. Duas integrações independentes
foram feitas no mesmo dia (12-13/10) — uma com os 6 modelos (Tayrine) e outra só
com os 5 clássicos (Mayara, `backend/app/adapters/stacking_classifier.py`) — e
foram consolidadas na segunda, por três motivos:

1. BERTopic era o modelo com **menor peso no meta-modelo** (0.08, o menor dos 6)
   e a **pior performance individual** (ROC-AUC 0.835 vs 0.98+ dos outros).
2. Em produção (Docker), o artefato do BERTopic quebrou por incompatibilidade de
   versão do Python entre treino e runtime (pickle de objetos compilados pelo
   `numba`, usado pelo UMAP/HDBSCAN internos do BERTopic) — um problema de
   fragilidade operacional que os outros 5 modelos não têm.
3. O artefato do BERTopic sozinho tinha 78MB (baixa um modelo de embeddings do
   Hugging Face na primeira execução) — bem mais pesado que os outros 5 somados.

O meta-modelo foi re-treinado só com os 5 modelos (não é só remover o peso do
BERTopic do vetor original — os pesos mudam quando se re-ajusta sem ele).

## Dataset

O dataset **não está neste repositório** (datasets não vão para o git). É o
**FakeRecogna** (notícias em português rotuladas Fake/Real), já tratado e
deduplicado pelo time de dados: `NoRemovalWords_tratada_dedup.csv` (11.670 linhas,
colunas `Titulo`, `Noticia`, `Rotulo`, entre outras). Peça o arquivo a quem fez o
desafio de ML e informe o caminho local com `--dataset-csv`.

**Importante**: os modelos usam **somente a coluna `Noticia`**. Uma auditoria de
vazamento de rótulo mostrou que `Titulo` traz o veredito escrito em ~64% das
notícias Fake (ex.: "É #FAKE: ...", "...#boato") — usar o título inflaria
artificialmente as métricas. Nenhuma outra coluna (`Categoria`, `Dominio`, `URL`,
`Autor`, `Data`, features estruturais etc.) é usada.

## Decisão do modelo (resumo, protocolo original com os 6)

Protocolo (seção 9 do desafio de ML): validação cruzada de 5 folds, ROC-AUC com
IC95% por bootstrap, Brier como métrica de calibração, e ensembles só adotados se
houver ganho **consistente** (IC95% do ganho pareado excluindo 0 e vitória em ≥4/5
folds, tanto em AUC quanto em Brier).

| modelo | roc_auc | brier | accuracy |
|---|---|---|---|
| baseline (LR) | 0.989 | 0.055 | 0.951 |
| svm (calibrado) | 0.992 | 0.030 | 0.962 |
| nb (calibrado) | 0.981 | 0.052 | 0.930 |
| char (SVM n-gramas) | 0.992 | 0.031 | 0.960 |
| gbm (SVD+HistGBM) | 0.982 | 0.050 | 0.933 |
| ~~bertopic (tópicos+LR)~~ | ~~0.835~~ | ~~0.167~~ | ~~0.752~~ |
| **stacking (meta-LR), 5 modelos** | **~0.993** | **~0.028** | **~0.964** |

Detalhes completos do protocolo original (pesos, correlação entre modelos,
gráficos) ficam só no material de origem do time de dados
(`modelos_outputs/stacking/decisao_modelo.md`), que não faz parte deste repositório.

## Artefato gerado

`backend/models/stacking.joblib` — um único pacote (dict serializado via joblib)
carregado por `backend/app/adapters/stacking_classifier.py::StackingClassifier`:

| chave | conteúdo |
|---|---|
| `base_models` | lista de nomes, na ordem usada pelo meta-modelo: `baseline`, `svm`, `nb`, `char`, `gbm` |
| `models` | dict nome → `Pipeline`/`CalibratedClassifierCV` do scikit-learn, já ajustado |
| `meta_model` | `LogisticRegression` sobre o logit das probabilidades dos modelos base |
| `version`, `input` | versão do formato do pacote e modo de entrada (`"noticia"`) |
| `sklearn_version`, `python_version` | gravados no treino; o `StackingClassifier` **recusa carregar** se não baterem com o ambiente de execução (evita o tipo de quebra silenciosa que o BERTopic teve) |
| `training_rows`, `training_split` | proveniência do treino |

## Como treinar/re-exportar

```bash
cd ml
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python treinar_e_exportar_stacking.py --dataset-csv /caminho/para/NoRemovalWords_tratada_dedup.csv
```

Treina os 5 modelos clássicos (rápido, segundos a poucos minutos) e grava o
pacote em `backend/models/stacking.joblib`, no formato acima.

## ⚠️ Limitação conhecida: pré-processamento do texto de entrada (2026-10-12)

A coluna `Noticia` do FakeRecogna **já vem lematizada/normalizada na fonte**
(ex.: "saúde" → "saudar", "fila" → "filar", "multa" → "multar", artigos
("a"/"as"/"os"/"um"...) colapsados para "o"). Os modelos foram treinados em
cima dessa forma, não em texto natural.

O `StackingClassifier` hoje recebe o texto **da forma como a extensão captura
da página, sem nenhum pré-processamento**. Isso causa uma incompatibilidade de
vocabulário: testei a API com texto real (neutro e até notícia formal de saúde)
e o modelo deu "suspeito" com 56-99% de confiança de forma sistemática — mas,
ao mandar uma linha do próprio dataset (já na forma lematizada, rótulo
conhecido), ele acertou os dois casos (Real→fake_probability 6%, Fake→98%).
Confirmei que **isso acontece igual nas duas integrações independentes**
(a de 6 modelos e a de 5) — não é bug de implementação, é a mesma incompatibilidade
de vocabulário nos dois casos. Ou seja: **o modelo e os pesos estão corretos**,
falta só replicar o pré-processamento de texto que gerou a coluna `Noticia`
antes de chamar o classificador em produção.

Tentei aproximar com spaCy (`pt_core_news_sm` e `pt_core_news_lg`) e com o
stemmer RSLP do NLTK — nenhum dos dois reproduz o padrão observado (substantivos
virando verbo cognato: saúde→saudar, fila→filar, deputado→deputar). Isso não é
lematização nem stemming padrão; é algo customizado. **Quem souber qual
ferramenta/script gerou `FakeRecogna_no_removal_words.xlsx` original precisa
confirmar** — a resposta certa provavelmente está com quem montou essa base
antes da limpeza (`tratamento/rodar_limpeza.py` não faz essa transformação,
ela já vem pronta no xlsx de origem).

Até isso ser resolvido, trate o percentual do `stacking` como não confiável
para texto real da web (a API já inclui esse aviso nas `justifications` da
resposta).

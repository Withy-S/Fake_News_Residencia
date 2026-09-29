# Testes da trustlist

## Ambiente
- API local: http://127.0.0.1:8000
- Rota: POST /api/v1/analyze
- Trustlist: gov.br e who.int
- Ferramenta: Swagger
- Data: 29 de setembro de 2026

## Casos de teste

| ID | Cenário | Resultado esperado | Resultado obtido | Situação |
|---|---|---|---|---|
| CT01 | URL https://saude.gov.br/noticia | Indicador trusted_domain | Preencher | Pendente |
| CT02 | URL https://example.org/noticia | indicators vazio | Preencher | Pendente |
| CT03 | Texto com menos de 20 caracteres | Erro texto_insuficiente | Retornou texto_insuficiente | Aprovado |

## Dados enviados em CT01

{
  "analysis_type": "selecao",
  "text": "Teste de exemplo com mais de vinte caracteres",
  "url": "https://saude.gov.br/noticia"
}

Para CT02, repetir os dados e trocar a URL por:
https://example.org/noticia

## Observação sobre o requisito

Atualmente, domínio desconhecido retorna indicators vazio.
A mensagem explícita "domínio não reconhecido" não está implementada.

## Testes automatizados

Executar dentro da pasta backend:

python -m pytest tests/test_trustlist.py tests/test_analyze_endpoint.py -v

Resultado da execução: Com o uso do swagger foi possível validar que a api retorna, o domínio estar dentro da trustlist corretamente e quando não está ele continua sua execução normal.

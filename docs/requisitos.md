# Requisitos Funcionais

## RF01 - Verificação de domínio
O sistema deve verificar se o domínio da página analisada está presente
na whitelist de fontes confiáveis definida pelo projeto.

Caso o domínio seja reconhecido, essa informação deve ser considerada
durante a análise do conteúdo.

Prioridade: MVP


## RF02 - Seleção manual de texto
A extensão deve permitir que o usuário selecione manualmente um trecho
de texto presente em uma página para solicitar sua análise.

Prioridade: MVP


## RF03 - Análise completa da página
A extensão deve permitir que o usuário solicite uma análise do conteúdo
textual principal da página atual.

O sistema deve extrair informações relevantes, como:

- título;
- conteúdo textual principal;
- URL;
- domínio da página.

Prioridade: MVP


## RF04 - Seleção de imagem
A extensão deve permitir que o usuário selecione uma imagem presente
na página para submetê-la a uma análise.

Prioridade: V2


## RF05 - Análise de manipulação de imagem
O sistema deve analisar uma imagem selecionada e retornar indícios de
possível:

- manipulação;
- edição;
- geração por inteligência artificial.

O resultado deve ser apresentado como uma estimativa ou indicação,
sem afirmar de forma absoluta que uma imagem é verdadeira ou falsa.

Prioridade: V2


## RF06 - Envio de conteúdo para a API
A extensão deve enviar para a API o conteúdo selecionado pelo usuário
ou extraído automaticamente da página.

A requisição deve conter, quando disponível:

- título;
- texto;
- URL;
- domínio;
- tipo de análise solicitada.

Prioridade: MVP


## RF07 - Análise linguística do conteúdo
O sistema deve analisar características do conteúdo textual que possam
auxiliar na identificação de desinformação.

A análise pode considerar:

- linguagem sensacionalista;
- tom emocional;
- ausência de fontes;
- afirmações sem evidências;
- alegações extraordinárias;
- contexto;
- estrutura textual;
- possíveis indicadores de viés.

Prioridade: MVP


## RF08 - Exibição de alertas
O sistema deve alertar o usuário quando forem identificados indícios de
conteúdo:

- suspeito;
- potencialmente desinformativo;
- ou não verificado.

O sistema não deve apresentar uma classificação probabilística como uma
determinação absoluta de verdade ou falsidade.

Prioridade: MVP


## RF09 - Recomendação de fontes
Após a análise de um conteúdo, o sistema deve permitir a busca por
informações relacionadas ao mesmo assunto em fontes pertencentes à
whitelist definida pelo projeto.

As fontes encontradas devem ser apresentadas ao usuário como referências
adicionais para comparação.

Prioridade: V2


## RF10 - Classificação por Machine Learning
Quando a classificação não puder ser realizada apenas pela verificação
do domínio, o sistema deve utilizar um modelo de Machine Learning para
analisar o conteúdo textual.

O resultado deve incluir:

- classificação;
- nível de confiança do modelo.

Prioridade: MVP


## RF11 - Fallback para análise por IA
Quando o nível de confiança do modelo de Machine Learning estiver abaixo
do limite definido pelo sistema, o conteúdo deve ser encaminhado para
um mecanismo adicional de análise.

Esse mecanismo poderá utilizar um modelo de IA generativa como uma
segunda análise.

Prioridade: MVP


## RF12 - Exibição do resultado da análise
O sistema deve apresentar ao usuário o resultado da análise de forma
compreensível.

A resposta deve conter, quando possível:

- classificação;
- justificativa;
- nível de confiança;
- método utilizado para a classificação;
- fontes adicionais relacionadas ao conteúdo.

Prioridade: MVP


## RF13 - Conteúdo não verificado
Quando não existirem informações suficientes para classificar um
conteúdo com confiança adequada, o sistema deve classificá-lo como
"não verificado".

O sistema não deve classificar automaticamente como falso um conteúdo
para o qual não existam evidências suficientes.

Prioridade: MVP
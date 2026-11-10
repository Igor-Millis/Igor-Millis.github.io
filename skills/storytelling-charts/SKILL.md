---
name: storytelling-charts
description: Monta gráficos explicativos que comunicam uma mensagem, seguindo os princípios de "Storytelling com Dados" (Cole Nussbaumer Knaflic). Use sempre que o usuário pedir um gráfico, visualização, slide com dados, relatório com figuras ou dashboard para apresentar a alguém — em matplotlib, plotly, Excel, HTML/SVG ou qualquer outra ferramenta —, e também quando pedir para revisar, melhorar ou "deixar mais claro" um gráfico existente. Não use para gráficos exploratórios rápidos que só o próprio analista vai olhar, a menos que o usuário peça.
---

# Gráficos com storytelling

Esta skill transforma "fazer um gráfico" em "comunicar uma conclusão com dados". O processo tem seis etapas, nesta ordem. Não pule a primeira: a maior parte dos gráficos ruins nasce de começar pela ferramenta em vez de pela mensagem.

Os princípios completos, com o porquê de cada um, estão em `references/principios.md`. Leia esse arquivo na primeira vez que usar a skill numa conversa. Para escolher o tipo de gráfico, use `references/escolha-do-grafico.md`. Antes de entregar, passe pelo `references/checklist.md`. Se o código for Python/matplotlib, use os ajudantes de `scripts/sc_style.py`.

## 1. Contexto antes de qualquer pixel

Responda (ou pergunte ao usuário, se não der para inferir) três coisas:

- **Quem** vai ver: uma pessoa ou grupo específico, não "a diretoria em geral". O que essa pessoa já sabe, o que a preocupa.
- **O que** você quer que ela saiba ou faça depois de ver. Se não houver uma ação, pelo menos uma decisão ou entendimento.
- **Como** vai ser visto: apresentado ao vivo (você narra, o slide pode ser enxuto) ou lido sozinho (o gráfico precisa se explicar).

Escreva então a **ideia central** numa frase completa, com um ponto de vista e o que está em jogo. Exemplo: "As devoluções da linha infantil dobraram desde março por causa do novo fornecedor; trocar de fornecedor antes do Natal evita cerca de R$ 80 mil em perdas." Se a frase não sai, ainda não há gráfico explicativo para fazer — há análise exploratória por terminar.

Distinga **exploratório** (procurar o que é interessante; muitos gráficos) de **explicativo** (mostrar a uma audiência a coisa interessante que você encontrou; um ou poucos gráficos). Esta skill é para o explicativo.

## 2. Escolher o visual certo

Use o tipo mais simples que mostre a comparação que importa. A regra prática:

| A mensagem é sobre… | Use |
|---|---|
| um ou dois números | o número em texto grande, com uma frase de apoio |
| poucos números exatos para consulta | tabela leve |
| padrão em uma tabela | tabela com cor de fundo (mapa de calor) |
| tendência no tempo | linhas |
| comparação de categorias | barras (horizontais se os nomes são longos) |
| antes × depois, dois momentos | gráfico de inclinação (slope) |
| relação entre duas variáveis | dispersão |
| partes de um total, poucas partes | barras empilhadas a 100% ou barras simples |

Evite pizza e rosca (olho compara mal ângulos e áreas), 3D (distorce valores) e eixo duplo (sugere relações que não existem). Barras **sempre** começam no zero. Detalhes e casos especiais em `references/escolha-do-grafico.md`.

## 3. Eliminar a poluição

Cada elemento que não ajuda a mensagem custa atenção. Remova por padrão e só devolva o que fizer falta:

- borda do gráfico, linhas de grade (ou deixe-as cinza-claro e finas), marcadores em todos os pontos, rótulos de dados em todos os pontos, fundo colorido, sombra, efeito 3D;
- legenda separada → rotule as séries **diretamente** no fim das linhas ou ao lado das barras;
- eixo que repete o que os rótulos já dizem; casas decimais desnecessárias; rótulos diagonais (troque por barras horizontais);
- texto centralizado em blocos → alinhe à esquerda.

Use espaço em branco e alinhamento para dar ordem visual: elementos alinhados entre si, margens generosas, nada espremido.

## 4. Dirigir a atenção

Comece com **tudo em cinza** e depois ponha cor só onde está a mensagem. Uma cor de destaque, no máximo duas. Atributos que o olho percebe antes de ler (pré-atentivos): cor, intensidade, tamanho, negrito, posição, marcações e contorno. Use-os com parcimônia: se tudo está destacado, nada está.

Teste rápido: feche os olhos, abra, e veja para onde o olhar vai primeiro. Deve ser para o ponto que sustenta a ideia central.

Cor com propósito: a mesma cor significa a mesma coisa em todos os gráficos da apresentação; considere daltonismo (evite vermelho × verde como único contraste; use também intensidade ou rótulo); respeite a cor da marca só se ela não atrapalhar.

## 5. Pensar como designer

- **Forma segue a função**: decida o que a audiência deve fazer com o gráfico e escolha o que torna isso fácil.
- **Acessibilidade**: título que afirma a conclusão, eixos com rótulo e unidade, texto legível, notas de rodapé para fonte e definições. Prefira palavras simples a jargão.
- **Estética**: alinhamento, espaço em branco, consistência. Um gráfico bonito ganha mais paciência da audiência.
- **Aceitação**: se a mudança de formato for grande para quem vai ver, explique o ganho, mostre lado a lado com o antigo ou mude aos poucos.

O título do gráfico é uma **frase de conclusão**, não uma descrição. "Devoluções da linha infantil dobraram após troca de fornecedor" — não "Devoluções por mês".

## 6. Contar a história

Estruture a apresentação ou o relatório com começo, meio e fim:

- **Começo**: o contexto e o problema (o "conflito" que justifica a atenção).
- **Meio**: os dados que mostram o problema, as opções, o que acontece se nada for feito.
- **Fim**: a recomendação e o pedido de ação.

Verificações de narrativa: a **ideia central em 3 minutos** (você consegue contar tudo em três minutos?); o **título-resumo horizontal** (lendo só os títulos dos slides em sequência, a história faz sentido?); a **lógica vertical** (o conteúdo de cada slide sustenta o título dele?). Repita a mensagem principal no começo e no fim. Em apresentações, revele o gráfico em camadas: primeiro os eixos, depois a série de contexto, depois o destaque.

## Formato da resposta

Ao entregar um gráfico, entregue também:

1. a **ideia central** em uma frase;
2. o gráfico (código ou arquivo), já com título de conclusão, rótulos diretos, cinza + uma cor de destaque;
3. uma linha dizendo **por que** escolheu esse tipo de gráfico;
4. se estiver revisando um gráfico existente, a lista curta do que foi removido e do que foi destacado.

Se faltar contexto (audiência, ação desejada), faça no máximo duas perguntas curtas; se o usuário não quiser responder, assuma o mais provável, diga o que assumiu e siga.

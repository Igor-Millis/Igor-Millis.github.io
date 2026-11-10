# Princípios, com o porquê

Resumo, com palavras próprias e exemplos originais, das ideias de *Storytelling com Dados* (Cole Nussbaumer Knaflic, 2015; ed. brasileira Alta Books). Não substitui o livro: para os exemplos originais, os estudos de caso e as figuras, leia a obra.

## Sumário

1. Contexto
2. Escolher um visual eficaz
3. Poluição visual e carga cognitiva
4. Atenção e atributos pré-atentivos
5. Pensar como designer
6. Dissecando modelos visuais (padrões recorrentes)
7. Lições de história
8. O processo completo

---

## 1. Contexto

**Exploratório × explicativo.** Na análise exploratória você revira os dados atrás de algo interessante — talvez 100 gráficos para achar 2 que importam. Na explicativa, você leva à audiência essas 2 coisas. O erro clássico é apresentar a exploração inteira ("veja tudo o que eu fiz"). A audiência não quer o caminho, quer o destino e o motivo de se importar.

**Quem, o quê, como.**
- *Quem*: quanto mais específico, melhor. "Gerente comercial da região Sul, que acha que o problema é preço" orienta muito mais do que "stakeholders". Pense na relação: ela confia em você? Você precisa ganhar credibilidade (então mostre mais método) ou já tem (então vá direto)?
- *O quê*: o que a pessoa deve saber ou fazer. Mesmo quando a decisão não é sua, recomende algo — é mais fácil reagir a uma proposta do que começar do zero. Defina também o tom (alerta, comemoração, neutro).
- *Como*: apresentação ao vivo (você controla a ordem, pode ter menos texto) × documento lido sozinho (precisa de mais texto e anotações). O "slideument" — slide feito para servir aos dois — costuma servir mal a ambos; se precisar, faça o slide enxuto e um apêndice/versão de leitura.

**Ideia central.** Uma frase que (1) expressa seu ponto de vista único e (2) diz o que está em jogo. Ex.: "O tempo médio de atendimento caiu 30% com o novo roteiro de triagem; estendê-lo às outras duas filiais em janeiro libera o equivalente a quatro atendentes."

**Storyboard.** Antes de abrir qualquer software, rascunhe a sequência em papel ou post-its: um quadro por ideia. É barato reordenar post-its e caro refazer slides. Valide o storyboard com quem pediu o trabalho antes de produzir.

**História de 3 minutos.** Se você tivesse só três minutos (o elevador, o executivo que entra atrasado), o que diria? Se conseguir, a mensagem está clara para você — condição para ficar clara para os outros.

## 2. Escolher um visual eficaz

Um pequeno repertório cobre quase tudo:

- **Texto simples.** Um ou dois números importantes ficam melhores como texto grande + frase de contexto do que como gráfico com duas barras. "68% dos clientes recompraram em 90 dias, contra 41% no ano passado."
- **Tabela.** Para consulta de valores exatos e públicos mistos (cada um procura uma linha). Bordas leves ou nenhuma; deixe os dados, não a grade, em evidência.
- **Mapa de calor.** Tabela com cor de fundo proporcional ao valor: guia o olho para os altos e baixos sem tirar os números. Inclua legenda ou explique a escala.
- **Pontos (dispersão).** Relação entre duas variáveis. Ajuda incluir linha de referência (média, meta) e destacar os pontos que fogem.
- **Linhas.** Dados contínuos, geralmente tempo. Intervalos regulares no eixo x. Uma variação útil: o **gráfico de inclinação**, com só dois pontos no tempo, para mostrar quem subiu e quem caiu.
- **Barras.** Comparar categorias. O olho compara bem as extremidades alinhadas numa base comum. **Base zero obrigatória** — barras cortadas exageram diferenças. Barras horizontais quando os nomes são longos (lêem-se como texto, sem rótulos inclinados). Ordene as categorias por valor quando a ordem não tiver significado próprio. Largura: barras mais largas que os espaços entre elas, mas não coladas.
- **Barras empilhadas.** Total e composição ao mesmo tempo, mas só a primeira série (a da base) é fácil de comparar; as do meio flutuam. Use com poucas séries.
- **Cascata (waterfall).** Do valor inicial ao final, mostrando as contribuições que somam e subtraem (ex.: headcount início do ano + contratações − saídas = fim do ano).
- **Área quadrada.** Raro; útil quando os números têm ordens de grandeza muito diferentes. Rotule os valores.

**O que evitar e por quê:**
- *Pizza e rosca*: o olho não compara ângulos e áreas com precisão; com fatias parecidas, ninguém sabe qual é maior sem ler os números. Se os números precisam ser lidos, uma barra os mostra melhor.
- *3D*: adiciona elementos inúteis e distorce — a perspectiva faz partes da frente parecerem maiores e dificulta ler valores no eixo.
- *Eixo y secundário*: o leitor precisa descobrir qual série vai com qual eixo, e a escala escolhida cria (ou esconde) cruzamentos arbitrários. Alternativas: rotular os pontos de uma série diretamente e tirar o segundo eixo; ou dois gráficos empilhados com o mesmo eixo x.

## 3. Poluição visual e carga cognitiva

Toda vez que o leitor olha um gráfico, gasta esforço mental para processá-lo (carga cognitiva). Parte é necessária — entender a informação. O resto é desperdício: elementos que ocupam espaço sem informar. O objetivo é reduzir o desperdício.

**Princípios da Gestalt** (como o olho agrupa coisas sem pensar) — use-os para remover elementos:
- *Proximidade*: o que está perto parece do mesmo grupo. Espaço resolve o que bordas resolveriam.
- *Similaridade*: mesma cor/forma parece mesmo grupo. Colorir o rótulo da série com a cor da série elimina a legenda.
- *Fechamento*: o olho completa formas. Não precisa de borda em volta do gráfico.
- *Continuidade*: o olho segue o caminho mais suave. Barras alinhadas não precisam de eixo para "parecerem alinhadas".
- *Conexão*: elementos ligados por uma linha parecem um grupo (é por isso que gráficos de linha funcionam).
- *Fechamento por cerco*: um fundo sombreado leve agrupa uma região (ex.: "previsão") sem precisar de texto extra.

**Ordem visual.** Alinhamento claro (prefira alinhar à esquerda, inclusive títulos de gráficos e de eixos, para o olho começar no canto superior esquerdo), uso estratégico do espaço em branco (não preencha só porque sobrou lugar) e contraste com propósito.

**Passo a passo de limpeza** (aplicar a quase todo gráfico padrão de software):
1. Remover borda do gráfico.
2. Remover ou clarear linhas de grade.
3. Remover marcadores de ponto.
4. Limpar rótulos de eixo (menos casas decimais, sem zeros à direita, formato de data curto).
5. Rotular dados diretamente e remover a legenda.
6. Usar cor de forma consistente (série e seu rótulo na mesma cor).

## 4. Atenção e atributos pré-atentivos

Antes de "ler" um gráfico, o cérebro já percebeu algumas diferenças em frações de segundo: cor, intensidade, tamanho, orientação, forma, marcações, contorno, posição espacial, movimento. São os **atributos pré-atentivos**. Num bloco de dígitos, achar todos os "3" é lento; se os "3" estiverem em negrito e cor, é instantâneo.

Usos práticos:
- **Em texto**: negrito em uma ou duas palavras-chave por parágrafo, não em metade dele.
- **Em gráficos**: série/barra de interesse em cor saturada; o resto em cinza. Rótulo de dado só no ponto que importa.
- **Hierarquia**: tamanho indica importância. O que é maior parece mais importante — reserve para o que é.

**Cor:** com moderação (cores demais tiram o poder de destacar), com consistência (se o azul é "nossa empresa" num slide, é no deck inteiro), pensando em daltonismo (vermelho/verde é o par mais confundido; azul × laranja funciona melhor, e intensidade + rótulo garantem leitura sem cor) e considerando o tom emocional (vermelho sugere alerta).

**Posição na página.** O leitor tende a começar no canto superior esquerdo e fazer zigue-zague. Ponha lá o que importa primeiro (a conclusão), não o logo.

## 5. Pensar como designer

**Affordances** — o design indica como algo deve ser usado. No gráfico: destaque o importante (até ~10% do conteúdo), elimine distrações, crie hierarquia clara (o leitor deve saber o que olhar primeiro, segundo, terceiro).

**Acessibilidade** — o gráfico não deve exigir esforço demais nem conhecimento que o leitor não tem:
- Não complique demais: palavras simples, sem siglas sem definição.
- Texto é aliado: título de conclusão, título de eixos, anotações explicando picos ou quedas ("lançamento da campanha"), rodapé com fonte e definições.
- Fonte legível, tamanho suficiente para a sala ou a tela.

**Estética** — pessoas toleram mais e confiam mais em designs bem acabados. Seja inteligente com a cor, cuide do alinhamento, mantenha o espaço em branco.

**Aceitação** — se a audiência está acostumada a um formato (o relatório de sempre, o gráfico de pizza da reunião mensal), mudanças radicais geram resistência. Explique o benefício, mostre antes e depois, peça a um influenciador da audiência que valide.

## 6. Padrões recorrentes de bons gráficos

Ao dissecar gráficos eficazes aparecem sempre os mesmos movimentos — use-os como modelo:
- **Linha com destaque e anotação**: todas as séries em cinza, uma em cor; um ponto marcado com o valor e uma frase curta explicando o evento.
- **Linha com previsão**: dados reais em linha sólida, projeção em tracejado ou mais clara; área sombreada separando passado e futuro.
- **Barras horizontais ordenadas**: categorias ordenadas pelo valor, rótulos à esquerda, valores no fim das barras, eixo removido.
- **Barras empilhadas a 100% (horizontais)**: para respostas de pesquisa (discorda → concorda), com as categorias extremas em cor e as neutras em cinza; ordenadas pela proporção positiva.
- **Texto ao lado do gráfico**: o gráfico à esquerda e, à direita, o texto com a conclusão, com as palavras-chave na mesma cor da série destacada (a cor liga texto e dado).

## 7. Lições de história

**Estrutura em três atos.** Começo: cenário, personagem principal (geralmente a audiência), desequilíbrio/conflito — por que isto importa agora. Meio: desenvolva o conflito com dados, mostre o que acontece se nada mudar, apresente opções. Fim: chamada à ação clara. Uma história sem conflito não prende ninguém: o conflito em dados costuma ser uma lacuna (meta × real), uma mudança (antes × depois), um risco ou uma oportunidade.

**Ordem narrativa.** Cronológica (o que aconteceu, como analisamos, o que achamos, o que recomendamos) agrada audiências que precisam confiar no processo. Começar pelo fim (recomendação primeiro, depois a sustentação) agrada executivos com pouco tempo. Escolha conforme a audiência.

**Narrativa falada × escrita.** Ao vivo, o apresentador conduz e o slide pode ser mínimo. Num documento, o texto precisa fazer o papel da narração: títulos que afirmam, anotações nos gráficos.

**O poder da repetição.** "Diga o que vai dizer, diga, diga o que disse": abertura com a mensagem, corpo com a sustentação, fecho repetindo a mensagem e a ação. Repetir ajuda a memória.

**Táticas para checar clareza:**
- *Lógica horizontal*: leia só os títulos dos slides em sequência — eles contam a história completa?
- *Lógica vertical*: em cada slide, tudo sustenta o título? O que não sustenta sai ou vai para o apêndice.
- *Storyboard reverso*: escreva o título-resumo de cada slide do deck pronto e veja se a estrutura bate com a planejada.
- *Olhar novo*: mostre para alguém sem contexto e peça para dizer o que entendeu, em voz alta.

**Revelação gradual.** Ao apresentar, construa o gráfico em etapas (eixos → contexto em cinza → série de interesse → anotação). A audiência acompanha seu raciocínio em vez de se perder no gráfico completo.

## 8. O processo completo

1. Entenda o contexto (quem, o quê, como; ideia central; história de 3 minutos).
2. Escolha o visual adequado.
3. Elimine a poluição.
4. Dirija a atenção para onde você quer.
5. Pense como designer.
6. Conte uma história.

A ideia que amarra tudo: o software não sabe qual é a sua história — você sabe. Os padrões do Excel, do PowerPoint ou do matplotlib existem para funcionar com qualquer dado; o trabalho de quem comunica é sair deles.

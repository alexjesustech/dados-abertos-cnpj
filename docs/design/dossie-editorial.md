# Dossiê editorial — Design System

> Documento de briefing tratado como **nota de pesquisa impressa**.
> Variante "B" do projeto `dados-abertos-cnpj`.
>
> Diferente do tratamento mono-clínico (que herda o sistema PF na
> íntegra), o **dossiê editorial** é um sistema visual paralelo:
> mantém os princípios de copy do PF (factual, sem moralismo, sem
> emoji), mas substitui a paleta neutra + destrutivo por um par
> **tinta sobre papel** com um único acento de ocre queimado.

Referência rendered: [`dossie-editorial-referencia.html`](./dossie-editorial-referencia.html)

---

## 1. Identidade

A página deve parecer um relatório de fundação ou um caderno
acadêmico tipografado com cuidado — não um app, não um dashboard.
A composição é regida por:

- **Tinta sobre papel**: warm black (#1a1916) sobre papel creme
  (#f5f1e8). Sem `oklch(1 0 0)`, sem branco puro em lugar nenhum.
- **Serifa editorial para tudo que carrega significado** (título,
  lead, section heads, valores numéricos grandes, títulos de
  segmento).
- **Sans para corpo factual** (parágrafo de mercado, bullets,
  body de solução).
- **Monospace para metadata** (kicker, rótulos uppercase, header
  de tabela, ficha técnica da solução).
- **Um único acento**: vermillion/ocre queimado (#b9532b), usado
  exclusivamente para sinalizar **lacuna, risco ou aviso** —
  não para destacar nem decorar.

Posicionamento ao lado das outras opções:

| Eixo | Faithful (A) | **Editorial (B)** | Mono-clínico (C) |
|---|---|---|---|
| Fundo | branco | **creme #f5f1e8** | branco |
| Display | Inter 32 | **Newsreader 52** | Inter 30 |
| Status | cor de fundo | **tag mono pill** | rótulo mono uppercase |
| Acento | semáforo completo | **vermillion único** | destrutivo só em risco |
| Densidade | média | **alta editorial** | alta tabular |
| Tom | claro | **jornalístico** | clínico |

---

## 2. Filosofia — quatro regras

### 2.1. Toda hierarquia vem do tipo, não da caixa

Cartões com `box-shadow`, gradientes, fundos coloridos para
diferenciar seções estão **proibidos**. Hierarquia é construída por:

1. Tamanho da serifa (52 → 26 → 17)
2. Itálico (citações, títulos de caminho, referências, trade-off)
3. Pesos serifa (500 / 600)
4. Versalete (`font-variant: small-caps`) no início do lead
5. Hairlines (1px sólido escuro, 1px dotted ocre claro)

### 2.2. Apenas um acento — vermillion

`#b9532b` aparece em **quatro lugares e nada mais**:

- `tag` de `Atenção` no card de status (fundo do pill)
- Linha "GAP" da paisagem do mercado (kicker + título em vermillion)
- Cabeçalho de coluna `stop` no semáforo (`#a13d1e` — variante
  ligeiramente mais escura para legibilidade)
- Linha de receita (`A + I + J`) em cada Caminho
- Sublinhado e bullet do bloco "O que não fazer"

Se um novo elemento "merece" vermillion, ele provavelmente é
metadata e pertence ao monospace cinza.

### 2.3. Floating numeral é o anchor

Cada seção tem um **numeral serifa 64 px**, peso 400, cor ocre
claro (`#c9bda3`), com `float: left` e `width: 80 px`. O corpo da
seção ganha `margin-left: 80 px` e uma hairline preta no topo. O
numeral funciona como capitular: leitor escaneia a página vendo
01 → 02 → 03... mesmo sem ler título.

### 2.4. Sem emoji, sem ícone

Idêntico ao mono-clínico. A única marca não-textual aceita é a
estrela unicode `★` (sempre em vermillion, sempre dentro de
metadata mono), marcando gap real em soluções. Bullets usam
em-dash (`—`) ou marcador padrão.

---

## 3. Tokens

Sistema visual paralelo ao PF — valores **não** vêm de
`oklch()` mas de hex tipográficos calibrados em câmara de papel.

### 3.1. Cor (paleta de impressão)

```
Papel
  paper           #f5f1e8         fundo da página
  paper-card-code #ebe3cf         fundo de <code> inline
  paper-toast     #1a1916         "O que não fazer" — papel invertido

Tinta
  ink             #0d0c0a         título, valor numérico, body em destaque
  ink-body        #1a1916         strong, header de coluna
  ink-text        #2d2a23         parágrafo padrão
  ink-soft        #3d3a32         body de status
  ink-italic      #4a4438         caption itálica, body do em do título

Khaki / metadata
  kk-mono-fg      #807966         label kicker, sub-meta
  kk-caption      #6b6557         masthead direito, legenda, ref
  kk-toast-body   #d9cfb8         body sobre #1a1916

Hairlines
  rule-dark       #1a1916         hairline forte (masthead, secbody-top, table head)
  rule-soft       #c9bda3         hairline soft (metric, sem, table tbody)
  rule-divider    #d9cfb8         divisor interno de solution grid

Acento (único)
  accent          #b9532b         tag warn, linha gap, ingredientes do caminho, marcador "não fazer"
  accent-deep     #a13d1e         apenas para label da coluna stop do semáforo
  accent-soft     #8a6a1e         apenas para label da coluna caution
  accent-go       #2a5a3a         apenas para label da coluna go (verde sóbrio, único uso)
```

> Os três tons "verde · âmbar · vermilhão" do semáforo são o
> **único momento em que mais de uma cor aparece na página**.
> Eles vivem apenas nos labels italic-serifa das três colunas
> do semáforo e não devem ser reutilizados em nenhum outro lugar.

### 3.2. Tipografia

```
Famílias
  --font-serif   Newsreader (400, 500, 600, 400-italic)
                 fallback: Source Serif Pro, Georgia, serif
  --font-sans    Inter (400, 500, 600)
  --font-mono    JetBrains Mono (400, 500)

Features
  serif       lnum + tnum (lining + tabular)
  root        font-variant-numeric: tabular-nums
```

**Escala** (sempre que o tamanho aumenta, troca para serifa):

| px   | Família     | Peso | Estilo  | Onde |
|------|-------------|------|---------|------|
| 52   | Newsreader  | 600  | mixed   | Título do dossiê (com `em` itálico 500 em ocre) |
| 48   | Newsreader  | 500  | regular | Numeral do caminho |
| 64   | Newsreader  | 400  | regular | Numeral da seção (cor `#c9bda3`) |
| 32   | Newsreader  | 500  | regular | Valor da métrica |
| 28   | Newsreader  | 500  | italic  | ID da solução (`A`, `B`...) em ocre |
| 26   | Newsreader  | 600  | regular | Título de seção (`h2`) |
| 22   | Newsreader  | 500  | regular | Título do "Não fazer" sobre papel invertido |
| 20   | Newsreader  | 500  | italic  | Masthead `pub` (esquerda) |
| 18   | Newsreader  | 600  | italic  | Label de coluna do semáforo |
| 17   | Newsreader  | 500  | regular | Lead, título do caminho |
| 17   | Newsreader  | 500  | regular | Título da linha de mercado (italic se gap) |
| 16   | Newsreader  | 600  | regular | Título da solução |
| 13.5 | Inter       | 400  | regular | **Corpo base do documento** |
| 12.5 | Inter       | 400  | regular | Body de status, mkt, semáforo, "não fazer" |
| 12   | Inter       | 400  | regular | Body de solução, tabela, semáforo |
| 11   | Mono        | 400  | regular | Footer (itálico serifa, na verdade) |
| 10.5 | Mono        | 500  | regular | Ingredientes do caminho (em ocre) |
| 10   | Mono        | 500  | uppercase | Todos os kickers, tags, table head, masthead |

**Letter-spacing:**
- Display 52 px: `-0.025em` (apertado, balance)
- Métrica 32 px: `-0.025em`
- Numeral caminho 48 px: `-0.03em`
- Numeral seção 64 px: `-0.04em`
- Section h2 26 px: `-0.015em`
- Mono uppercase 10 px: `+0.08em` a `+0.16em`

**Detalhe único do lead** — primeira linha em versalete:

```css
.vb-lead::first-line {
  font-variant: small-caps;
  letter-spacing: 0.04em;
}
```

Não usar `::first-letter` (capitular) — quebra com `text-wrap:
pretty` e parece marketing. O `::first-line` em versalete é
contido e tipograficamente clássico.

### 3.3. Espaço e raio

```
Página
  width                 900 px
  padding              64 64 56 (top horizontal bottom)
  background           #f5f1e8

Section
  margin-bottom        44 px
  numeral float        80 px, margem-superior 4 px
  secbody margin-left  80 px, padding-top 10 px, border-top 1px #1a1916

Card / componente
  metric padding       14 px 16 px 14 px 0  (right-padded para divisor)
  status gap           24 px (sem borda — apenas espaço)
  mkt-row padding-y    14 px com `1px dotted #c9bda3` embaixo
  sem-col padding      16 px 18 px com `1px solid #d9cfb8` à direita
  solution padding     16 px 18 px com `1px solid #d9cfb8` à direita e embaixo
  caminho padding-top  14 px com `3px solid #1a1916` no topo
  nope (toast)         22 px 28 px, sem radius

Radius
  pill warn            2 px
  pill solução code    2 px
  toast "não fazer"    0 px (página dentro da página, sem arredondar)
```

**Importante**: o tratamento editorial **não usa `border-radius`
maior que 2 px em nenhum container**. Tudo é canto reto — pertence
ao gesto de "papel impresso". Apenas pills inline têm raio mínimo.

### 3.4. Hairlines (vocabulário)

Quatro hairlines distintas, cada uma com função:

| Estilo | Cor | Função |
|---|---|---|
| `2px solid #1a1916` | escura forte | divisor entre masthead e título |
| `1px solid #1a1916` | escura simples | topo do `vb-secbody` (logo abaixo do numeral) |
| `1.5px solid #1a1916` | tabela | borda inferior do `<th>` |
| `1px solid #c9bda3` | soft khaki | bordas externas de tabela, metric grid, semáforo |
| `1px solid #d9cfb8` | divisor interno | divisores entre metrics, sem-cols, solutions |
| `1px dotted #c9bda3` | tracejado | linha entre mkt-rows, dentro de tabela, trade-off no caminho |
| `3px solid #1a1916` | espessa | topo de cada cartão de Caminho (substitui o numeral floating) |

A escolha entre **sólida / tracejada / espessa / soft** comunica:
- sólida escura → "fim de seção"
- soft khaki → "fim de linha tabular"
- dotted → "fim de item dentro de uma lista densa"
- 3 px → "início de um bloco autônomo no rodapé"

---

## 4. Estrutura de página

```
┌─────────────────────────────────────────────────────────────┐
│ Briefing de planejamento [italic]          23 maio 2026     │
│ PESQUISA DE VIABILIDADE · Nº 001           VOL. 1 · SESSÃO  │ ◀ 2px solid black
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  dados-abertos-cnpj —                                       │ ◀ 52px serif
│  o que dá pra construir? [italic]                           │
│                                                              │
│  PIPELINE JÁ INGERE 30 GB... [::first-line small-caps]      │ ◀ 17px serif
│  ...resumo do briefing em duas linhas e meia.               │
│                                                              │
│  ┌───┐                                                       │
│  │01 │ ─────────────────────────────────────────             │ ◀ secbody border-top
│  │   │ O que já temos rodando                                │
│  └───┘                                                       │
│         [metric grid]                                        │
│         [3 status]                                           │
│                                                              │
│  ┌───┐                                                       │
│  │02 │ ─────────────────────────────────────────             │
│  ...                                                         │
├─────────────────────────────────────────────────────────────┤
│ briefing gerado em 2026-05-23 ... [italic serifa]           │
└─────────────────────────────────────────────────────────────┘
```

### 4.1. Masthead

Bloco no topo da página, sempre presente, sempre o mesmo padrão:

```html
<div class="vb-mast">
  <div class="left">
    <div class="pub">Briefing de planejamento</div>
    <div class="sub">PESQUISA DE VIABILIDADE · Nº 001</div>
  </div>
  <div class="right">
    23 maio 2026
    VOL. 1 · SESSÃO ÚNICA
  </div>
</div>
```

A `2px solid #1a1916` embaixo é a única hairline forte da página
inteira (junto com o `border-bottom` do `<th>` da tabela). Funciona
como "linha do título" de um jornal.

### 4.2. Section header

Numeral 64 px **flutuante**, hairline 1 px no topo do corpo, `h2`
serifa 26 px. Pode ser variante `.full` (sem margem esquerda)
quando o conteúdo é uma toast como o "Não fazer".

### 4.3. Footer

Linha italic em serifa 11 px com hairline soft no topo. Carrega
sempre: data + autoria + próximo passo factual.

---

## 5. Componentes

### 5.1. Metric grid (Section 1)

Linha horizontal sem cartões — apenas hairlines soft em cima e
embaixo, e divisores `#d9cfb8` entre métricas. Padding right
exceto última coluna.

- Label: mono uppercase 10 px ocre
- Valor: serifa 32 px peso 500, letter-spacing -0.025em

A serifa nos valores é o que diferencia este sistema dos outros:
um número em Inter parece "métrica de dashboard"; em Newsreader
parece "cifra de relatório".

### 5.2. Status item (Section 1, baixo)

3 itens em grid com gap 24 px, sem cartão.

```
┌─ EM PÉ ─┐   ← pill mono 10 px, bg #1a1916, color #f5f1e8
Pipeline...   ← serifa? Não — Inter 600 13 px ink-body
Streaming...  ← Inter 400 12.5 px ink-soft
```

A tag pill (`ok`/`warn`) é o **único uso de fundo escuro/ocre em
componente de status**. Não existe wash de fundo no cartão
inteiro — a hierarquia vem da pill superior. Variantes:
- `ok` → `bg: #1a1916` (papel invertido)
- `warn` → `bg: #b9532b` (acento)

### 5.3. Linha de paisagem (Section 2)

Grade de 180 px + 1fr com `dotted` ocre embaixo. Coluna esquerda
em serifa 17 px peso 500. Coluna direita em **duas colunas
CSS** (`column-count: 2`) para acomodar o card "GAPS PERCEPTÍVEIS"
sem mudar layout — bullets fluem em duas colunas dentro do `<ul>`.

Se a linha é o gap (`.gap`):
- kicker em vermillion
- título em vermillion **e itálico**
- marcador `—` em ocre semi-translúcido
- corpo permanece em texto neutro

### 5.4. Semáforo (Section 3)

3 colunas dentro de hairlines soft top/bottom, divisores
internos `#d9cfb8`. Cabeçalho de cada coluna:

```
┌──────────────────────────────┐
│ Permitido    DEC. 8.777/2016 │  ← serif italic + mono uppercase
├──────────────────────────────┤  ← hairline soft
│ · Redistribuir os dados      │  ← bullet padrão, lista solta
│ · ...                        │
```

A coluna `go` recebe `#2a5a3a` (verde sóbrio), `caution`
recebe `#8a6a1e` (âmbar discreto), `stop` recebe `#a13d1e`
(vermillion profundo) — **apenas no `.label` italic**. Nada no
fundo, nada nos bullets.

Referência ao final em **serifa itálica 11 px ocre claro** —
contém citações jurisprudenciais sem destaque.

### 5.5. Tabela (Section 4)

Não tem container — vive direto na página com `<th>` em mono
uppercase com `border-bottom: 1.5px solid #1a1916` (linha forte
do título de coluna). Linhas separadas por `dotted` ocre. Primeira
coluna em **serifa itálica 13.5 px** — torna a tabela legível
como prosa.

### 5.6. Solution grid (Section 5)

2 colunas, sem container externo (apenas as divisórias internas
`#d9cfb8`). Primeira coluna sem padding-left, última sem
padding-right (a tabela "encaixa" no flow do documento).

Anatomia:
- **ID** em serifa italic 28 px peso 500 cor `#807966`, com
  `float: left`. Letra única (A, B, C…) — parece capitular.
- **Título** serifa 16 px 600
- **Body** Inter 12 px
- **Meta** em row mono: `dado: CNPJ only`, `esforço: P`, `gap:
  baixo`, `lgpd: nenhum` — pares chave-valor inline separados
  por gap 14 px. Estrela `★` em vermillion antes do valor quando
  é gap real.

### 5.7. Caminho (Section 6)

3 colunas com `gap: 24 px`, **sem cartão e sem container** —
cada coluna é uma "coluna de jornal" com `border-top: 3px solid
#1a1916` (a única hairline 3 px da página).

Anatomia vertical:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ← 3px solid black
KICKER MONO UPPERCASE
48
"Título italic do caminho"
A + I + J · 3–4 SEMANAS  ← mono vermillion
Corpo Inter
---------------------------- ← dotted khaki
Trade-off. detalhe italic    ← serifa italic
```

O numeral 48 px é desenhado **logo abaixo** do kicker, não
flutuante como nas seções. Faz o caminho parecer um capítulo
autônomo.

A linha de ingredientes em vermillion é o **único uso textual
do acento na seção 6** — comunica composição matemática
("este caminho = A + I + J") sem precisar de ícone.

### 5.8. "O que não fazer" (Section 7)

Bloco invertido — `bg: #1a1916`, texto em `#d9cfb8`. Sem
border-radius. Vive dentro de um `vb-secbody` (mantém o numeral
07 flutuante).

```
┌─ #1a1916 ──────────────────────────────────────┐
│  O que não fazer [serif italic h2]             │
│      └ sublinhado em #b9532b 2px               │
│                                                 │
│  • Replicar Casa dos Dados...   ← bullet ocre   │
│  • Tentar score de crédito...                   │
└─────────────────────────────────────────────────┘
```

O `<u>` em "não" do título recebe `text-decoration-color:
#b9532b` com `text-decoration-thickness: 2px` e
`text-underline-offset: 4px`. É o único sublinhado decorativo
do documento — funciona como ênfase visual no veto.

---

## 6. Voz e linguagem

Herda do PF, com duas extensões editoriais:

### 6.1. O lead é uma frase, não um pitch

A primeira linha em versalete obriga o lead a começar com algo
escaneável — geralmente uma constatação numérica. Padrão:
`Pipeline já ingere 30 GB...`, não `Você precisa entender que...`

### 6.2. Trade-off, não "limitações"

Cada Caminho termina com `Trade-off.` (ponto final, italic
serifa), seguido da concessão em texto neutro. Nunca "Limitações",
"Cuidados", "Pontos de atenção". A palavra "Trade-off" carrega
honestidade comercial — você ganha X em troca de Y — sem o
peso moral de "limitação".

### 6.3. Banido

Idêntico ao PF, mais:

- "Spoiler:", "Vale destacar:", "Importante:"
- Negrito em sentença inteira (negrito é só para keyword
  específica — `nome de sócio PF`, não "tentar score de
  crédito sem base própria")
- Quebra de linha forçada em prosa (use `<p>` separados)
- Emoji, inclusive ⭐ — a estrela `★` (caractere unicode) é
  aceita apenas em metadata mono de soluções

---

## 7. Anti-patterns

| ❌ Errado | ✅ Certo |
|---|---|
| Cartão com sombra cobrindo fundo creme | Componente sem fundo, hairlines como contenção |
| Métrica grande em Inter 600 | Métrica em Newsreader 500 italic-friendly |
| ID da solução em mono `A.` 18 px | ID em Newsreader italic 28 px peso 500 |
| Coluna do semáforo com `bg: #f0e6d0` | Sem fundo — só `label` italic colorido |
| Pill rounded para tag de status | Pill `border-radius: 2px` (papel impresso) |
| Acento azul/verde para "link" | Sublinhado em texto neutro, hover em ink |
| Drop cap clássico (`::first-letter`) no lead | Versalete `::first-line` |
| "Importante!" em destrutivo no topo | Apenas masthead + título + lead |
| Numeral de seção em cor de acento | Numeral em ocre claro (`#c9bda3`) — quase invisível, ainda funcional |
| Tabela com radius nas pontas | Tabela sem container, apenas hairlines |

---

## 8. Checklist de implementação

Antes de publicar uma nova página neste tratamento:

- [ ] Background é `#f5f1e8`. Nenhuma superfície usa branco puro.
- [ ] Newsreader carregada com pesos 400/500/600 + italic 400.
- [ ] Inter carregada com pesos 400/500/600.
- [ ] JetBrains Mono carregada com pesos 400/500.
- [ ] `font-variant-numeric: tabular-nums` no root.
- [ ] Nenhum `box-shadow`, nenhum gradiente, nenhum blur.
- [ ] Hierarquia construída por **tamanho/peso/italic da serifa**,
      não por cor de fundo.
- [ ] Vermillion `#b9532b` aparece **somente** em: pill warn,
      kicker+title de mkt-row gap, ingredientes de caminho,
      sublinhado do "não fazer", marcador `★` de solução com gap.
- [ ] As cores verde/âmbar/vermelho do semáforo aparecem
      **somente** nos `.label` italic das três colunas.
- [ ] Numeral da seção 64 px ocre claro com `float: left` e
      `border-top: 1px solid #1a1916` no `secbody`.
- [ ] Masthead presente, com `border-bottom: 2px solid #1a1916`.
- [ ] Lead com `::first-line` em versalete.
- [ ] Tabela tem `<th>` com `border-bottom: 1.5px solid #1a1916`,
      primeira coluna em serifa italic 13.5 px.
- [ ] Trade-off do caminho nomeado como `Trade-off.` (ponto), em
      serifa italic com hairline dotted acima.
- [ ] Bloco "Não fazer" é uma toast `bg: #1a1916`, com sublinhado
      vermillion no título.
- [ ] Footer em serifa italic 11 px com hairline soft no topo.
- [ ] `border-radius` máximo de 2 px em qualquer componente.

---

*Variante extraída de `Briefing dados-abertos-cnpj.html`,
opção B. Sistema visual independente, mas alinhado aos
princípios de copy do design system PF (factual, sem moralismo,
sem emoji). Se um dia for adotado para outros documentos longos
de pesquisa, este markdown deve viver em
`docs/design/dossie-editorial.md`.*

# Relatório do Projeto: Agentes Lógicos no Pac-Man

## 1. Definição do Problema e Objetivos

O objetivo deste projeto é explorar a aplicação de **Lógica Formal** no controlo de agentes autónomos num ambiente de jogo dinâmico e parcialmente observável. Ao contrário de abordagens baseadas em heurísticas simples ou aprendizagem por reforço, este projeto foca-se na representação explícita do conhecimento e no raciocínio dedutivo.

Os desafios centrais abordados são:
1.  **Observabilidade Parcial**: Os agentes não têm acesso ao estado global do jogo. Apenas percecionam uma vizinhança local (raio de 4 células). Isto obriga à criação de modelos mentais (crenças) sobre o mundo não visível.
2.  **Tomada de Decisão Racional**: Os agentes devem deduzir a melhor ação possível com base em regras lógicas pré-definidas e no estado atual das suas crenças.
3.  **Navegação em Labirinto**: O ambiente contém obstáculos (paredes) que exigem planeamento ou regras de movimento robustas para evitar bloqueios.

## 2. Arquitetura do Sistema

A solução foi implementada em Python, seguindo uma arquitetura modular orientada a objetos.

### 2.1. O Ambiente (`Environment`)
A classe `Environment` (em `pacman.py`) atua como o "Mundo". É responsável por:
*   Manter a "Verdade do Solo" (Ground Truth): posições reais de todos os atores, paredes e pastilhas.
*   Gerir a Física: Validar movimentos e detetar colisões.
*   Fornecer Sensores: O método `get_view(x, y)` simula os sensores do agente, devolvendo apenas a informação visível a partir de uma coordenada.

### 2.2. Os Agentes (`Ghost`)
A classe base `Ghost` (em `src/agents/ghost.py`) define a interface comum para todos os fantasmas.
*   **Estado Interno**: Mantém a posição atual e um mapa de crenças (`belief_map`) que agrega a informação recolhida ao longo do tempo.
*   **Ciclo de Vida**: O método `update(view)` atualiza as crenças com nova informação sensorial, e `decide_move(grid)` solicita ao motor de lógica a próxima ação.

### 2.3. Motores de Inferência
O "cérebro" dos agentes reside nos módulos de lógica, que implementam algoritmos clássicos de Inteligência Artificial:
*   **Lógica Proposicional (`src/logic/propositional.py`)**: Implementa um verificador de modelos baseado em tabelas de verdade (`tt_entails`). Este algoritmo verifica se uma sentença é verdadeira em todos os modelos possíveis que satisfazem a Base de Conhecimento (KB). É robusto mas computacionalmente custoso (exponencial no número de símbolos), sendo adequado apenas para domínios pequenos ou raciocínio local.
*   **Lógica de Primeira Ordem (`src/logic/first_order.py`)**: Implementa um motor de inferência baseado em **Backward Chaining** (`fol_bc_ask`). Este algoritmo utiliza **Unificação** para encontrar substituições de variáveis que tornem uma query verdadeira dada a KB. Permite regras universais e raciocínio sobre objetos e relações.

## 3. Implementação dos Agentes e Lógica

Abaixo detalha-se a implementação específica de cada tipo de agente.

### 3.1. Agentes Proposicionais (`StalkerGhost` e `PatrolGhost`)
Estes agentes operam num ciclo "sem memória lógica" entre turnos. A cada passo, a KB é limpa e reconstruída com factos sobre a vizinhança imediata.

**Processo de Tradução (Percept-to-Sentence):**
1.  O agente observa as células vizinhas (Norte, Sul, Este, Oeste).
2.  Para cada direção `D`, se a célula é livre, adiciona o facto `Symbol("{D}Safe")`.
3.  Se o Pac-Man é visível numa direção `D`, adiciona o facto `Symbol("Pacman{D}")`.

**StalkerGhost (O Perseguidor):**
*   **Estratégia**: Agressividade máxima.
*   **Axiomas (Regras)**:
    *   *Axioma de Ataque*: `Pacman{D} ∧ {D}Safe ⇒ BestMove{D}`
    *   *Axioma de Movimento*: `{D}Safe ⇒ SafeMove{D}`
*   **Comportamento Observado**: O agente move-se aleatoriamente (escolhendo entre `SafeMove`s) até que o Pac-Man entre no seu campo de visão adjacente. Nesse momento, o axioma de ataque é ativado e o agente persegue.

**PatrolGhost (O Patrulhador):**
*   **Estratégia**: Cobertura de área e consistência de movimento.
*   **Axiomas (Regras)**:
    *   Define-se `Backtrack` como a direção oposta ao último movimento.
    *   *Axioma de Exploração*: `{D}Safe ∧ ¬{D}Backtrack ⇒ GoodMove{D}`
*   **Comportamento Observado**: O agente evita oscilações (ir Norte, depois Sul, depois Norte). Ele mantém a direção até encontrar uma parede ou cruzamento, resultando numa patrulha mais natural e abrangente do labirinto.

### 3.2. Agente de Primeira Ordem (`FOLGhost`)
Este agente demonstra um nível superior de inteligência ao manter memória persistente.

**Representação do Conhecimento:**
Utiliza predicados para descrever o mundo.
*   `At(Me, C_x_y)`: O agente está na célula (x, y).
*   `Visited(C_x_y)`: A célula (x, y) já foi visitada. Este predicado é crucial pois permite ao agente distinguir novidade.

**Motor de Inferência (Backward Chaining):**
O agente pergunta à KB: "Existe algum `m` tal que `BestMove(m)`?". O motor tenta provar esta afirmação procurando regras que concluam `BestMove`.

**Regras e Hierarquia de Decisão:**
1.  **Regra de Caça**: `PacmanAt(m) ∧ Safe(m) ⇒ BestMove(m)`
    *   Se esta regra for satisfeita, o agente persegue imediatamente.
2.  **Regra de Possibilidade**: `Safe(m) ⇒ PossibleMove(m)`
    *   Se não houver caça, o agente recolhe todos os movimentos possíveis.
    *   **Filtragem Inteligente (Python + Lógica)**: O agente cruza os resultados de `PossibleMove` com a sua memória de `Visited`. Se existirem movimentos para células *não visitadas*, ele escolhe um desses. Isto implementa um comportamento de **Exploração Curiosa**.

## 4. Comparação Crítica e Conclusão

| Característica | Agentes Proposicionais | Agente FOL (Primeira Ordem) |
| :--- | :--- | :--- |
| **Complexidade** | Baixa (Regras simples, KB volátil) | Alta (Unificação, Variáveis, Memória) |
| **Memória** | Reativa (Apenas estado atual) | Persistente (Mapa de visitados) |
| **Comportamento** | Aleatório ou Padrão Fixo | Exploração Sistemática |
| **Desempenho** | Rápido (Tabela de verdade pequena) | Mais lento (Inferência complexa) |

**Conclusão:**
A implementação demonstrou com sucesso que a lógica formal pode ser usada para controlar agentes em tempo real.
*   A **Lógica Proposicional** mostrou-se adequada para reflexos rápidos e comportamentos simples (evitar paredes, perseguir se adjacente).
*   A **Lógica de Primeira Ordem** permitiu comportamentos cognitivos mais avançados, como o mapeamento e a exploração sistemática de território desconhecido, superando a aleatoriedade dos agentes mais simples.

O sistema final resulta numa simulação onde diferentes "personalidades" de fantasmas emergem não de código imperativo complexo ("if-then-else" em Python), mas de conjuntos elegantes de regras lógicas declarativas.

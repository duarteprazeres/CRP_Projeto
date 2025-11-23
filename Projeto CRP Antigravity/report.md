# Relatório do Projeto Pac-Man Inteligente

## 1. Introdução
Este projeto implementa uma versão baseada em texto do jogo Pac-Man em Python. O foco central é a implementação de agentes inteligentes para os fantasmas utilizando Lógica Simbólica (Proposicional e de Primeira Ordem), sem recurso a bibliotecas externas de IA. A interface do jogo foi desenvolvida utilizando a biblioteca `curses` para permitir input fluido e gráficos coloridos no terminal.

## 2. Arquitetura do Sistema
### 2.1 Ambiente (Grid)
O mapa do jogo é representado por uma grelha ASCII.
- **Observabilidade Parcial**: Os fantasmas têm um campo de visão limitado e bloqueado por paredes, exigindo manutenção de estado e crenças.
- **Design do Nível**: O mapa foi desenhado com uma densidade reduzida de pastilhas (pellets), concentrando-as em corredores e pontos estratégicos para incentivar a exploração e evitar que o jogo se torne uma tarefa repetitiva de limpeza de células adjacentes.

### 2.2 Motor de Jogo
O ficheiro `main.py` contém o loop principal, gerindo a renderização e o input.
- **Input**: Utiliza `curses` para capturar as setas do teclado de forma não-bloqueante.
- **Renderização**: Desenha o estado do jogo a cada frame, atribuindo cores distintas a cada elemento (Paredes, Pac-Man, Fantasmas).

## 3. Motores de Lógica
Implementámos dois motores de inferência de raiz:
1.  **Lógica Proposicional (`src/logic/propositional.py`)**:
    -   Base de Conhecimento (KB) baseada em sentenças lógicas.
    -   Inferência via algoritmo `tt_entails` (Verificação de Modelos).
2.  **Lógica de Primeira Ordem (`src/logic/first_order.py`)**:
    -   KB baseada em cláusulas de Horn.
    -   Inferência via Unificação e Encadeamento para Trás (`Backward Chaining`).

## 4. Agentes Fantasmas
O jogo inclui três fantasmas com comportamentos e cores distintas:

### 4.1 Stalker Ghost (Vermelho) - Lógica Proposicional
-   **Estratégia**: Perseguição direta.
-   **Lógica**: A cada turno, o agente constrói uma KB temporária com factos sobre a sua percepção imediata (quais direções são seguras) e a direção relativa do Pac-Man.
-   **Regras**: Utiliza implicações como `PacmanNorth & NorthSafe -> ShouldMoveNorth` para escolher o movimento que minimiza a distância ao alvo.

### 4.2 Patroller Ghost (Verde) - Lógica Proposicional
-   **Estratégia**: Patrulha e exploração contínua.
-   **Lógica**: Este agente foca-se em evitar movimentos repetitivos e "becos sem saída" lógicos.
-   **Regras**:
    -   Mantém em memória o seu último movimento.
    -   Define um `GoodMove` como qualquer movimento seguro que **não** seja o inverso do movimento anterior (evita backtracking imediato).
    -   Se existirem múltiplos `GoodMove`s, escolhe um aleatoriamente.
    -   Só inverte a marcha se não houver outra opção (beco sem saída).
    -   Esta lógica impede que o agente fique preso em loops de 2 células (ir e vir), forçando-o a percorrer corredores inteiros.

### 4.3 Strategist Ghost (Rosa) - Lógica de Primeira Ordem
-   **Estratégia**: Planeamento e Exploração Estocástica.
-   **Lógica**: Modela o ambiente local como um grafo de conexões (`Connected(A, B)`).
-   **Regras**:
    -   **Modo Perseguição**: Se o Pac-Man for percebido, tenta unificar uma regra `BestMove` que encontre uma célula adjacente segura e mais próxima do alvo (`Closer`).
    -   **Modo Exploração**: Se o Pac-Man não for visível, o agente deduz todos os `PossibleMove`s (células seguras conectadas). A escolha entre estas possibilidades é feita de forma aleatória para garantir uma cobertura imprevisível do mapa.

## 5. Conclusão
O sistema cumpre todos os requisitos propostos: jogabilidade estilo Pac-Man, múltiplos agentes com lógicas distintas (PL e FOL), e um ambiente parcialmente observável. A utilização de lógica simbólica permite explicar o comportamento dos agentes através das regras na sua Base de Conhecimento.

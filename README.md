# Sistema de Navegação Autônoma para Identificação de Caixas Leves em Ambiente Simulado

Este projeto implementa um sistema de navegação autônoma utilizando o simulador Webots. O objetivo do robô é localizar caixas dispostas no ambiente, empurrá-las e determinar, com base no deslocamento observado, se são leves ou pesadas.

## 1. Descrição Geral

O código controla um robô móvel via WeBots, utilizando sensores de proximidade para navegação e desvio de obstáculos. Após localizar uma caixa, o robô realiza um empurrão controlado e verifica o deslocamento em relação à posição inicial, até encontrar a caixa mais leve da simulação.

## 2. Tecnologias Utilizadas

- WeBots
- Python 3
- Sensores de proximidade (ps0 a ps7)
- Supervisor do Webots
- Atuadores/motores de rodas

## 3. Estrutura do Sistema

O sistema é dividido em três partes principais:

### a. Detecção e Localização de Caixas

As caixas seguem a nomenclatura `CAIXA01`, `CAIXA02`, ..., até `CAIXAn`, de acordo com a constante `NUM_CAIXAS`. O Supervisor coleta suas posições iniciais para avaliação posterior de deslocamento.

### b. Navegação e Controle

O robô utiliza um controle proporcional para alinhar-se com o destino com base no erro angular. A lógica de navegação é ajustada dinamicamente com base na distância até o alvo. Obstáculos são evitados por meio de leitura dos sensores frontais e manobras de evasão temporárias.

### c. Classificação de Caixas

Após alcançar a caixa, o robô a empurra por dois segundos. Em seguida, compara a nova posição com a original. Se o deslocamento for maior que uma tolerância definida (`0.01 m`), a caixa é considerada leve e a simulação é encerrada.

## 4. Algoritmo de Navegação

O controle de orientação é baseado na diferença entre o ângulo atual do robô e o ângulo em direção à caixa. O erro é ajustado para o intervalo `[-π, π]`, e um fator de correção proporcional é aplicado às velocidades dos motores.

O sistema também monitora se há progresso no deslocamento para realizar correções caso o robô esteja parado e desalinhado.

## 5. Lógica de Evasão de Obstáculos

Quando os sensores frontais detectam valores superiores ao limite definido (`LIMITE_SENSOR`), o robô executa uma manobra de evasão, girando no eixo oposto ao lado de maior leitura. Um contador (`EvasionCounter`) determina a duração da evasão.

## 6. Classificação de Leveza

A identificação das caixas leves é feita por comparação entre posições antes e depois do empurrão. Ao final da execução (ou após detectar a primeira caixa leve), o sistema:

1. Compara todas as posições iniciais e finais.
2. Identifica as caixas com maior deslocamento.
3. Retorna até a caixa leve mais deslocada.
4. Gira indefinidamente à sua frente, indicando que a missão foi concluída.

## 7. Parâmetros Principais

| Parâmetro             | Valor padrão | Descrição |
|----------------------|--------------|-----------|
| `NUM_CAIXAS`         | 20           | Quantidade de caixas na simulação |
| `MAX_VELOCIDADE`     | 6.28         | Velocidade máxima dos motores |
| `TIME_STEP`          | 450          | Passo de tempo da simulação |
| `TOLERANCIA_DISTANCIA` | 0.10       | Distância mínima para considerar chegada à caixa |
| `LIMITE_SENSOR`      | 150          | Limiar de ativação de evasão |
| `EVASION_DURANTION`  | 5            | Duração da manobra evasiva (em steps) |

## 8. Execução

Para executar o projeto no Webots:

1. Certifique-se de que o robô está definido com o nome `"ROBO"`.
2. As caixas devem estar nomeadas conforme o padrão `"CAIXA01"`, `"CAIXA02"`, etc.
3. Execute o controlador supervisor Python.
4. Acompanhe o terminal para visualização das mensagens de estado e resultados de classificação.

## 9. Resultados Esperados

- Classificação precisa das caixas com base em deslocamento.
- Comportamento adaptativo do robô frente a obstáculos e desalinhamentos.
- Encontrar qual é a caixa leve da simulação.

## 10. Considerações Finais

O sistema foi projetado para ser escalável e modular. A lógica de controle, desvio e empurrão é baseada em princípios simples de navegação autônoma e pode ser facilmente adaptada para tarefas similares em outros cenários simulados.


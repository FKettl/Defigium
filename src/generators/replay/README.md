# Estrategia: ReplayGenerator

## 1. Introdução

O `ReplayGenerator` é a estratégia de geração mais fundamental do Defigium. Ele implementa uma lógica de passagem direta.

Seu objetivo principal não é gerar uma carga nova, mas sim servir como uma linha de base para validar a fidelidade do Módulo Executor.

Ao usá-lo, o rastro sintético gerado é uma cópia idêntica do rastro original. Isso permite uma comparação direta e isolada entre o que o Executor deveria executar e o que ele realmente executou.

## 2. Implementação

A implementação é a mais simples possível, aderindo à interface `IGenerator`.

O método `generate` recebe a lista de eventos `FEIEvent` do rastro original e retorna a mesma lista, sem qualquer modificação. Nenhuma análise estatística ou síntese é realizada.

## 3. Configuração

Para usar esta estratégia, defina no arquivo `config.yaml`:

```yaml
generator:
  type: replay

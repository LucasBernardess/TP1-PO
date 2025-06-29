
# Implementação do Método Simplex

**Autores:**

* Lucas Eduardo Bernardes de Paula
* Messias Feres Curi Melo

## 1. Descrição do Projeto

Este trabalho é uma implementação computacional do método Simplex para resolver Problemas de Programação Linear (PPL). O programa foi desenvolvido em Python para tratar problemas de maximização, aceitando restrições dos tipos `<=` ou `>=`.

Para problemas que incluem restrições do tipo `>=`, o programa utiliza o **Método Simplex de Duas Fases** para encontrar uma solução básica viável inicial. Além disso, conforme solicitado, a implementação é capaz de detectar se uma solução ótima não é única e, nesse caso, encontrar o outro ponto extremo que resulta no mesmo valor ótimo.

## 2. Como Executar

### Pré-requisitos

* Python 3
* Biblioteca `numpy`

Para instalar a biblioteca `numpy`, execute:

```bash
pip install numpy
```

### Execução do Programa

**O programa é executado via linha de comando, passando como argumento o caminho para o arquivo de entrada que descreve o PPL**.

**Bash**

```
python main.py <caminho_para_o_arquivo_de_entrada>
```

## 3. Formato do Arquivo de Entrada

O arquivo de entrada deve ser um arquivo de texto `.txt` com a seguinte estrutura:

1. **Primeira linha:** Coeficientes da função objetivo, separados por espaço.
2. **Linhas seguintes:** Coeficientes de cada restrição, seguidos pelo tipo de desigualdade `<=` ou `>=` e pelo valor do lado direito (vetor `b`), também separados por espaço.

### Exemplo

Considere o seguinte PPL:

**Maximizar Z = 3x₁ + 6x₂**

**Sujeito a:**

* x₁ + x₃ = 4 
* 2x₂ + x₄ = 6 

O arquivo de entrada `exemplo_otimo.txt` correspondente a este modelo seria:

```
3 6 0 0
1 0 1 0 <= 4
1 0 1 0 >= 4
0 2 0 1 <= 6
0 2 0 1 >= 6
```

Ao executar o comando `python main.py exemplo_otimo.txt`, o programa exibirá as iterações do tableau Simplex e, ao final, a solução ótima esperada:

```
--- SOLUÇÃO ÓTIMA ---
x1 = 4.0000
x2 = 3.0000
x3 = 0.0000
x4 = 0.0000
Z = 30.0000
```

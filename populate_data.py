# populate_data.py
import os
import django
import json

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maratona_brasil.settings')
django.setup()

from challenges.models import BrazilState, ProgrammingLanguage, Challenge
from django.contrib.auth.models import User

def populate_states():
    """Popula o banco de dados com os estados brasileiros"""
    # Verificar se já existem estados no banco de dados e limpar para evitar duplicidade
    BrazilState.objects.all().delete()
    
    states_data = [
        {'name': 'Acre', 'abbreviation': 'AC', 'region': 'norte', 'x': 12, 'y': 25, 'order': 1},
        {'name': 'Amazonas', 'abbreviation': 'AM', 'region': 'norte', 'x': 25, 'y': 30, 'order': 2},
        {'name': 'Roraima', 'abbreviation': 'RR', 'region': 'norte', 'x': 32, 'y': 19, 'order': 3},
        {'name': 'Amapá', 'abbreviation': 'AP', 'region': 'norte', 'x': 43, 'y': 24, 'order': 4},
        {'name': 'Pará', 'abbreviation': 'PA', 'region': 'norte', 'x': 41, 'y': 32, 'order': 5},
        {'name': 'Rondônia', 'abbreviation': 'RO', 'region': 'norte', 'x': 26, 'y': 38, 'order': 6},
        {'name': 'Tocantins', 'abbreviation': 'TO', 'region': 'norte', 'x': 40, 'y': 42, 'order': 7},
        {'name': 'Maranhão', 'abbreviation': 'MA', 'region': 'nordeste', 'x': 51, 'y': 36, 'order': 8},
        {'name': 'Piauí', 'abbreviation': 'PI', 'region': 'nordeste', 'x': 58, 'y': 40, 'order': 9},
        {'name': 'Ceará', 'abbreviation': 'CE', 'region': 'nordeste', 'x': 64, 'y': 35, 'order': 10},
        {'name': 'Rio Grande do Norte', 'abbreviation': 'RN', 'region': 'nordeste', 'x': 70, 'y': 33, 'order': 11},
        {'name': 'Paraíba', 'abbreviation': 'PB', 'region': 'nordeste', 'x': 72, 'y': 37, 'order': 12},
        {'name': 'Pernambuco', 'abbreviation': 'PE', 'region': 'nordeste', 'x': 68, 'y': 41, 'order': 13},
        {'name': 'Alagoas', 'abbreviation': 'AL', 'region': 'nordeste', 'x': 71, 'y': 44, 'order': 14},
        {'name': 'Sergipe', 'abbreviation': 'SE', 'region': 'nordeste', 'x': 70, 'y': 47, 'order': 15},
        {'name': 'Bahia', 'abbreviation': 'BA', 'region': 'nordeste', 'x': 61, 'y': 49, 'order': 16},
        {'name': 'Mato Grosso', 'abbreviation': 'MT', 'region': 'centro-oeste', 'x': 34, 'y': 50, 'order': 17},
        {'name': 'Mato Grosso do Sul', 'abbreviation': 'MS', 'region': 'centro-oeste', 'x': 37, 'y': 58, 'order': 18},
        {'name': 'Goiás', 'abbreviation': 'GO', 'region': 'centro-oeste', 'x': 45, 'y': 53, 'order': 19},
        {'name': 'Distrito Federal', 'abbreviation': 'DF', 'region': 'centro-oeste', 'x': 49, 'y': 52, 'order': 27},  # Desafio final
        {'name': 'Minas Gerais', 'abbreviation': 'MG', 'region': 'sudeste', 'x': 56, 'y': 58, 'order': 20},
        {'name': 'Espírito Santo', 'abbreviation': 'ES', 'region': 'sudeste', 'x': 65, 'y': 55, 'order': 21},
        {'name': 'Rio de Janeiro', 'abbreviation': 'RJ', 'region': 'sudeste', 'x': 63, 'y': 62, 'order': 22},
        {'name': 'São Paulo', 'abbreviation': 'SP', 'region': 'sudeste', 'x': 52, 'y': 63, 'order': 23},
        {'name': 'Paraná', 'abbreviation': 'PR', 'region': 'sul', 'x': 47, 'y': 69, 'order': 24},
        {'name': 'Santa Catarina', 'abbreviation': 'SC', 'region': 'sul', 'x': 48, 'y': 76, 'order': 25},
        {'name': 'Rio Grande do Sul', 'abbreviation': 'RS', 'region': 'sul', 'x': 46, 'y': 83, 'order': 26},
    ]
    
    for state_data in states_data:
        BrazilState.objects.create(
            name=state_data['name'],
            abbreviation=state_data['abbreviation'],
            region=state_data['region'],
            map_x_position=state_data['x'],
            map_y_position=state_data['y'],
            order=state_data['order']
        )
    
    print(f"Adicionados {len(states_data)} estados brasileiros.")

def populate_languages():
    """Popula o banco de dados com as linguagens de programação"""
    # Limpar linguagens existentes para evitar duplicidade
    ProgrammingLanguage.objects.all().delete()
    
    languages = [
        {'name': 'Python', 'extension': 'py'},
        {'name': 'C', 'extension': 'c'},
        {'name': 'Java', 'extension': 'java'},
        {'name': 'JavaScript', 'extension': 'js'},
        {'name': 'C++', 'extension': 'cpp'},  # Adicionado C++ para completar as linguagens dos desafios
    ]
    
    for lang_data in languages:
        ProgrammingLanguage.objects.create(
            name=lang_data['name'],
            extension=lang_data['extension']
        )
    
    print(f"Adicionadas {len(languages)} linguagens de programação.")

def populate_challenges():
    """Popula o banco de dados com desafios iniciais"""
    # Certifique-se de que temos estados e linguagens
    if BrazilState.objects.count() == 0 or ProgrammingLanguage.objects.count() == 0:
        print("Erro: Popule estados e linguagens primeiro.")
        return
    
    # Limpar desafios existentes para evitar duplicidade
    Challenge.objects.all().delete()
    
    # Obter linguagens
    python = ProgrammingLanguage.objects.get(name='Python')
    c_lang = ProgrammingLanguage.objects.get(name='C')
    cpp = ProgrammingLanguage.objects.get(name='C++')
    java = ProgrammingLanguage.objects.get(name='Java') # Para uso futuro
    
    # Alguns exemplos de desafios
    challenges_data = [
        {
            'title': 'Olá Mundo',
            'state': 'Acre',
            'language': java,
            'difficulty': 'easy',
            'points': 10,
            'description': 'Seu primeiro desafio é simples: escreva um programa que imprima "Olá, Maratona de Programação!" na tela.',
            'input_description': 'Não há entrada para este problema.',
            'output_description': 'Seu programa deve imprimir exatamente "Olá, Maratona de Programação!" (sem as aspas).',
            'example_input': 'Olá, Mundo!',
            'example_output': 'Olá, Mundo!',
            'test_cases': [
                {'input': '', 'output': 'Olá, Maratona de Programação!'}
            ],
            'time_limit': 2000
        },
        {
            'title': 'Soma de Dois Números',
            'state': 'Amazonas',
            'language': python,
            'difficulty': 'easy',
            'points': 20,
            'description': 'Escreva um programa que receba dois números inteiros como entrada e imprima a soma deles.',
            'input_description': 'A entrada consiste em dois números inteiros A e B (1 ≤ A, B ≤ 1000), um em cada linha.',
            'output_description': 'Seu programa deve imprimir um único número inteiro, representando a soma de A e B.',
            'example_input': '5\n7',
            'example_output': '12',
            'test_cases': [
                {'input': '5\n7', 'output': '12'},
                {'input': '10\n20', 'output': '30'},
                {'input': '100\n200', 'output': '300'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Números Primos',
            'state': 'Roraima',
            'language': c_lang,
            'difficulty': 'medium',
            'points': 30,
            'description': 'Escreva um programa que determine se um número é primo ou não.',
            'input_description': 'A entrada consiste em um único número inteiro N (1 ≤ N ≤ 10^6).',
            'output_description': 'Seu programa deve imprimir "Sim" se N for primo, ou "Nao" caso contrário (sem acento).',
            'example_input': '7',
            'example_output': 'Sim',
            'test_cases': [
                {'input': '7', 'output': 'Sim'},
                {'input': '4', 'output': 'Nao'},
                {'input': '1', 'output': 'Nao'},
                {'input': '97', 'output': 'Sim'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Tabuada',
            'state': 'Amapá',
            'language': java,
            'difficulty': 'easy',
            'points': 15,
            'description': 'Crie um programa que gere a tabuada de um número inteiro fornecido pelo usuário.',
            'input_description': 'Um número inteiro N (1 ≤ N ≤ 10).',
            'output_description': 'A tabuada de N do 1 ao 10, no formato "N x i = resultado", um por linha.',
            'example_input': '5',
            'example_output': '5 x 1 = 5\n5 x 2 = 10\n5 x 3 = 15\n5 x 4 = 20\n5 x 5 = 25\n5 x 6 = 30\n5 x 7 = 35\n5 x 8 = 40\n5 x 9 = 45\n5 x 10 = 50',
            'test_cases': [
                {'input': '5', 'output': '5 x 1 = 5\n5 x 2 = 10\n5 x 3 = 15\n5 x 4 = 20\n5 x 5 = 25\n5 x 6 = 30\n5 x 7 = 35\n5 x 8 = 40\n5 x 9 = 45\n5 x 10 = 50'},
                {'input': '2', 'output': '2 x 1 = 2\n2 x 2 = 4\n2 x 3 = 6\n2 x 4 = 8\n2 x 5 = 10\n2 x 6 = 12\n2 x 7 = 14\n2 x 8 = 16\n2 x 9 = 18\n2 x 10 = 20'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Palindromo',
            'state': 'Pará',
            'language': python,
            'difficulty': 'easy',
            'points': 25,
            'description': 'Verifique se uma palavra ou frase é um palíndromo (lê-se da mesma forma de trás para frente, ignorando espaços e pontuação).',
            'input_description': 'Uma string contendo apenas letras e possivelmente espaços e pontuação.',
            'output_description': 'Imprima "Sim" se a entrada for um palíndromo, ou "Nao" caso contrário.',
            'example_input': 'ana',
            'example_output': 'Sim',
            'test_cases': [
                {'input': 'ana', 'output': 'Sim'},
                {'input': 'arara', 'output': 'Sim'},
                {'input': 'banana', 'output': 'Nao'},
                {'input': 'A man a plan a canal Panama', 'output': 'Sim'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Fibonacci',
            'state': 'Rondônia',
            'language': java,
            'difficulty': 'easy',
            'points': 25,
            'description': 'Calcule o N-ésimo número da sequência de Fibonacci.',
            'input_description': 'Um número inteiro N (1 ≤ N ≤ 40).',
            'output_description': 'O N-ésimo número da sequência de Fibonacci.',
            'example_input': '6',
            'example_output': '8',
            'test_cases': [
                {'input': '1', 'output': '1'},
                {'input': '2', 'output': '1'},
                {'input': '6', 'output': '8'},
                {'input': '10', 'output': '55'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Conversão Binária',
            'state': 'Tocantins',
            'language': c_lang,
            'difficulty': 'medium',
            'points': 30,
            'description': 'Converta um número decimal para binário.',
            'input_description': 'Um número inteiro N (0 ≤ N ≤ 1000).',
            'output_description': 'A representação binária de N.',
            'example_input': '10',
            'example_output': '1010',
            'test_cases': [
                {'input': '0', 'output': '0'},
                {'input': '1', 'output': '1'},
                {'input': '10', 'output': '1010'},
                {'input': '42', 'output': '101010'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Ordenação Simples',
            'state': 'Alagoas',
            'language': python,
            'difficulty': 'easy',
            'points': 20,
            'description': 'Ordene uma lista de números inteiros em ordem crescente.',
            'input_description': 'A primeira linha contém um inteiro N (1 ≤ N ≤ 1000), o número de elementos. A segunda linha contém N números inteiros separados por espaços.',
            'output_description': 'Os N números ordenados em ordem crescente, separados por espaços.',
            'example_input': '5\n3 1 4 5 2',
            'example_output': '1 2 3 4 5',
            'test_cases': [
                {'input': '5\n3 1 4 5 2', 'output': '1 2 3 4 5'},
                {'input': '3\n10 5 8', 'output': '5 8 10'},
                {'input': '4\n9 9 8 8', 'output': '8 8 9 9'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Verificador de Anagramas',
            'state': 'Bahia',
            'language': java,
            'difficulty': 'medium',
            'points': 35,
            'description': 'Determine se duas palavras são anagramas uma da outra.',
            'input_description': 'Duas strings separadas por uma nova linha, cada uma contendo apenas letras minúsculas.',
            'output_description': 'Imprima "Sim" se as palavras forem anagramas, ou "Nao" caso contrário.',
            'example_input': 'amor\nroma',
            'example_output': 'Sim',
            'test_cases': [
                {'input': 'amor\nroma', 'output': 'Sim'},
                {'input': 'hello\nworld', 'output': 'Nao'},
                {'input': 'listen\nsilent', 'output': 'Sim'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Máximo Divisor Comum',
            'state': 'Ceará',
            'language': c_lang,
            'difficulty': 'medium',
            'points': 30,
            'description': 'Calcule o Máximo Divisor Comum (MDC) de dois números inteiros usando o algoritmo de Euclides.',
            'input_description': 'Dois números inteiros positivos A e B (1 ≤ A, B ≤ 10^9), separados por espaço.',
            'output_description': 'O MDC de A e B.',
            'example_input': '48 18',
            'example_output': '6',
            'test_cases': [
                {'input': '48 18', 'output': '6'},
                {'input': '100 75', 'output': '25'},
                {'input': '35 15', 'output': '5'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Frequência de Caracteres',
            'state': 'Distrito Federal',
            'language': java,
            'difficulty': 'medium',
            'points': 35,
            'description': 'Conte a frequência de cada caractere em uma string e apresente em ordem decrescente de frequência.',
            'input_description': 'Uma única string contendo apenas letras minúsculas, sem espaços.',
            'output_description': 'Para cada caractere que aparece na string, imprima o caractere seguido de sua frequência, um por linha, em ordem decrescente de frequência. Em caso de empate, use a ordem alfabética.',
            'example_input': 'banana',
            'example_output': 'a 3\nn 2\nb 1',
            'test_cases': [
                {'input': 'banana', 'output': 'a 3\nn 2\nb 1'},
                {'input': 'abracadabra', 'output': 'a 5\nb 2\nr 2\nc 1\nd 1'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Validador de Parênteses',
            'state': 'Espírito Santo',
            'language': python,
            'difficulty': 'medium',
            'points': 40,
            'description': 'Verifique se uma expressão com parênteses, colchetes e chaves está balanceada.',
            'input_description': 'Uma string contendo apenas os caracteres "(", ")", "[", "]", "{" e "}".',
            'output_description': 'Imprima "Sim" se a expressão estiver balanceada, ou "Nao" caso contrário.',
            'example_input': '({[]})',
            'example_output': 'Sim',
            'test_cases': [
                {'input': '({[]})', 'output': 'Sim'},
                {'input': '([)]', 'output': 'Nao'},
                {'input': '((([])))', 'output': 'Sim'},
                {'input': '{', 'output': 'Nao'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Busca Binária',
            'state': 'Goiás',
            'language': c_lang,
            'difficulty': 'medium',
            'points': 45,
            'description': 'Implemente o algoritmo de busca binária para encontrar um elemento em um array ordenado.',
            'input_description': 'A primeira linha contém dois inteiros N e X (1 ≤ N ≤ 10^5, 1 ≤ X ≤ 10^9), onde N é o tamanho do array e X é o valor a ser buscado. A segunda linha contém N inteiros ordenados em ordem crescente.',
            'output_description': 'Imprima o índice onde X foi encontrado (considerando que o primeiro elemento tem índice 0) ou "-1" se X não estiver no array.',
            'example_input': '5 4\n1 2 4 7 9',
            'example_output': '2',
            'test_cases': [
                {'input': '5 4\n1 2 4 7 9', 'output': '2'},
                {'input': '6 10\n1 3 5 7 9 11', 'output': '-1'},
                {'input': '7 7\n1 2 3 4 7 8 9', 'output': '4'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Números de Armstrong',
            'state': 'Maranhão',
            'language': python,
            'difficulty': 'medium',
            'points': 40,
            'description': 'Verifique se um número é um número de Armstrong. Um número de Armstrong é um número que é igual à soma de seus próprios dígitos elevados à quantidade de dígitos.',
            'input_description': 'Um único número inteiro N (1 ≤ N ≤ 10^8).',
            'output_description': 'Imprima "Sim" se N for um número de Armstrong, ou "Nao" caso contrário.',
            'example_input': '153',
            'example_output': 'Sim',
            'test_cases': [
                {'input': '153', 'output': 'Sim'},  # 1^3 + 5^3 + 3^3 = 1 + 125 + 27 = 153
                {'input': '370', 'output': 'Sim'},  # 3^3 + 7^3 + 0^3 = 27 + 343 + 0 = 370
                {'input': '123', 'output': 'Nao'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Criptografia Simples',
            'state': 'Mato Grosso',
            'language': c_lang,
            'difficulty': 'medium',
            'points': 45,
            'description': 'Implemente uma cifra de César, onde cada letra é deslocada N posições no alfabeto.',
            'input_description': 'A primeira linha contém um inteiro N (1 ≤ N ≤ 25), o deslocamento. A segunda linha contém uma string de letras minúsculas, que é a mensagem a ser criptografada.',
            'output_description': 'A mensagem criptografada, também em letras minúsculas.',
            'example_input': '3\nhello',
            'example_output': 'khoor',
            'test_cases': [
                {'input': '3\nhello', 'output': 'khoor'},
                {'input': '13\nroman', 'output': 'ebzna'},
                {'input': '1\nzebra', 'output': 'afcsb'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Números Perfeitos',
            'state': 'Mato Grosso do Sul',
            'language': java,
            'difficulty': 'medium',
            'points': 35,
            'description': 'Determine se um número é perfeito. Um número perfeito é um número que é igual à soma de seus divisores positivos, excluindo ele mesmo.',
            'input_description': 'Um número inteiro N (1 ≤ N ≤ 10^8).',
            'output_description': 'Imprima "Sim" se N for um número perfeito, ou "Nao" caso contrário.',
            'example_input': '28',
            'example_output': 'Sim',
            'test_cases': [
                {'input': '6', 'output': 'Sim'},    # 1 + 2 + 3 = 6
                {'input': '28', 'output': 'Sim'},   # 1 + 2 + 4 + 7 + 14 = 28
                {'input': '12', 'output': 'Nao'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Algoritmo de Dijkstra',
            'state': 'Minas Gerais',
            'language': cpp,
            'difficulty': 'hard',
            'points': 70,
            'description': 'Implemente o algoritmo de Dijkstra para encontrar o caminho mais curto em um grafo ponderado.',
            'input_description': 'A primeira linha contém três inteiros N, M e S (1 ≤ N ≤ 10^4, 1 ≤ M ≤ 10^5, 1 ≤ S ≤ N), onde N é o número de vértices, M é o número de arestas e S é o vértice de origem. As próximas M linhas contêm três inteiros cada: U, V e W, indicando uma aresta do vértice U para o vértice V com peso W (1 ≤ U, V ≤ N, 1 ≤ W ≤ 10^6).',
            'output_description': 'Para cada vértice de 1 a N, imprima a distância mínima do vértice S até ele, ou "-1" se não houver caminho.',
            'example_input': '4 4 1\n1 2 10\n1 3 5\n2 4 1\n3 4 3',
            'example_output': '0 10 5 8',
            'test_cases': [
                {'input': '4 4 1\n1 2 10\n1 3 5\n2 4 1\n3 4 3', 'output': '0 10 5 8'},
                {'input': '3 3 1\n1 2 5\n2 3 7\n1 3 10', 'output': '0 5 10'}
            ],
            'time_limit': 2000
        },
        {
            'title': 'Árvore AVL',
            'state': 'Paraíba',
            'language': cpp,
            'difficulty': 'hard',
            'points': 75,
            'description': 'Implemente uma árvore AVL e as operações de inserção, remoção e busca.',
            'input_description': 'A primeira linha contém um inteiro Q (1 ≤ Q ≤ 10^5), o número de operações. As próximas Q linhas contêm operações no formato "I X" (inserir X), "R X" (remover X) ou "S X" (buscar X), onde X é um inteiro (1 ≤ X ≤ 10^9).',
            'output_description': 'Para cada operação de busca ("S X"), imprima "Sim" se X está na árvore, ou "Nao" caso contrário.',
            'example_input': '7\nI 10\nI 5\nI 15\nS 10\nS 20\nR 10\nS 10',
            'example_output': 'Sim\nNao\nNao',
            'test_cases': [
                {'input': '7\nI 10\nI 5\nI 15\nS 10\nS 20\nR 10\nS 10', 'output': 'Sim\nNao\nNao'},
                {'input': '5\nI 1\nI 2\nI 3\nS 2\nS 4', 'output': 'Sim\nNao'}
            ],
            'time_limit': 2000
        },
        {
            'title': 'Problema do Caixeiro Viajante',
            'state': 'Paraná',
            'language': java,
            'difficulty': 'hard',
            'points': 80,
            'description': 'Resolva o Problema do Caixeiro Viajante usando programação dinâmica.',
            'input_description': 'A primeira linha contém um inteiro N (1 ≤ N ≤ 15), o número de cidades. As próximas N linhas contêm N inteiros cada, representando a matriz de distâncias entre as cidades.',
            'output_description': 'A distância mínima para completar o circuito visitando cada cidade exatamente uma vez e retornando à cidade de origem.',
            'example_input': '4\n0 10 15 20\n10 0 35 25\n15 35 0 30\n20 25 30 0',
            'example_output': '80',
            'test_cases': [
                {'input': '4\n0 10 15 20\n10 0 35 25\n15 35 0 30\n20 25 30 0', 'output': '80'},
                {'input': '3\n0 10 15\n10 0 20\n15 20 0', 'output': '45'}
            ],
            'time_limit': 3000
        },
        {
            'title': 'Detecção de Ciclos em Grafos',
            'state': 'Pernambuco',
            'language': cpp,
            'difficulty': 'medium',
            'points': 50,
            'description': 'Dado um grafo direcionado, determine se ele contém ciclos.',
            'input_description': 'A primeira linha contém dois inteiros N e M (1 ≤ N ≤ 10^4, 1 ≤ M ≤ 10^5), o número de vértices e arestas. As próximas M linhas contêm dois inteiros U e V cada (1 ≤ U, V ≤ N), indicando uma aresta do vértice U para o vértice V.',
            'output_description': 'Imprima "Sim" se o grafo contém pelo menos um ciclo, ou "Nao" caso contrário.',
            'example_input': '4 4\n1 2\n2 3\n3 4\n4 2',
            'example_output': 'Sim',
            'test_cases': [
                {'input': '4 4\n1 2\n2 3\n3 4\n4 2', 'output': 'Sim'},
                {'input': '4 3\n1 2\n2 3\n3 4', 'output': 'Nao'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Árvore Binária de Busca',
            'state': 'Piauí',
            'language': c_lang,
            'difficulty': 'medium',
            'points': 55,
            'description': 'Implemente uma árvore binária de busca (BST) e as operações de inserção, remoção e travessia em ordem.',
            'input_description': 'A primeira linha contém um inteiro Q (1 ≤ Q ≤ 10^4), o número de operações. As próximas Q linhas contêm operações no formato "I X" (inserir X), "R X" (remover X) ou "P" (imprimir os elementos em ordem), onde X é um inteiro (1 ≤ X ≤ 10^4).',
            'output_description': 'Para cada operação de impressão ("P"), imprima os elementos da árvore em ordem crescente, separados por espaços.',
            'example_input': '7\nI 5\nI 3\nI 7\nP\nR 5\nI 8\nP',
            'example_output': '3 5 7\n3 7 8',
            'test_cases': [
                {'input': '7\nI 5\nI 3\nI 7\nP\nR 5\nI 8\nP', 'output': '3 5 7\n3 7 8'},
                {'input': '5\nI 10\nI 5\nI 15\nI 20\nP', 'output': '5 10 15 20'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Ordenação Topológica',
            'state': 'Rio de Janeiro',
            'language': cpp,
            'difficulty': 'hard',
            'points': 65,
            'description': 'Implemente um algoritmo para ordenação topológica de um grafo direcionado acíclico (DAG).',
            'input_description': 'A primeira linha contém dois inteiros N e M (1 ≤ N ≤ 10^4, 1 ≤ M ≤ 10^5), o número de vértices e arestas. As próximas M linhas contêm dois inteiros U e V cada (1 ≤ U, V ≤ N), indicando uma aresta do vértice U para o vértice V.',
            'output_description': 'Uma possível ordenação topológica dos vértices, separados por espaços. Se houver um ciclo, imprima "Impossivel".',
            'example_input': '4 4\n1 2\n1 3\n2 4\n3 4',
            'example_output': '1 2 3 4',
            'test_cases': [
                {'input': '4 4\n1 2\n1 3\n2 4\n3 4', 'output': '1 2 3 4'},
                {'input': '3 3\n1 2\n2 3\n3 1', 'output': 'Impossivel'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Menor Ancestral Comum',
            'state': 'Rio Grande do Norte',
            'language': cpp,
            'difficulty': 'hard',
            'points': 70,
            'description': 'Encontre o menor ancestral comum (LCA) de dois nós em uma árvore.',
            'input_description': 'A primeira linha contém um inteiro N (1 ≤ N ≤ 10^5), o número de nós na árvore. As próximas N-1 linhas contêm dois inteiros U e V cada (1 ≤ U, V ≤ N), indicando uma aresta entre os nós U e V. A próxima linha contém um inteiro Q (1 ≤ Q ≤ 10^5), o número de consultas. As próximas Q linhas contêm dois inteiros A e B cada (1 ≤ A, B ≤ N), os nós para os quais você deve encontrar o LCA.',
            'output_description': 'Para cada consulta, imprima o LCA dos nós A e B.',
            'example_input': '5\n1 2\n1 3\n2 4\n2 5\n3\n4 5\n1 5\n3 4',
            'example_output': '2\n1\n1',
            'test_cases': [
                {'input': '5\n1 2\n1 3\n2 4\n2 5\n3\n4 5\n1 5\n3 4', 'output': '2\n1\n1'},
                {'input': '7\n1 2\n1 3\n2 4\n2 5\n3 6\n3 7\n2\n4 5\n6 7', 'output': '2\n3'}
            ],
            'time_limit': 2000
        },
        {
            'title': 'Problema da Mochila',
            'state': 'Rio Grande do Sul',
            'language': java,
            'difficulty': 'hard',
            'points': 75,
            'description': 'Resolva o Problema da Mochila usando programação dinâmica.',
            'input_description': 'A primeira linha contém dois inteiros N e W (1 ≤ N ≤ 100, 1 ≤ W ≤ 10^5), o número de itens e a capacidade da mochila. As próximas N linhas contêm dois inteiros cada: o valor V e o peso P do item i (1 ≤ V, P ≤ 10^3).',
            'output_description': 'O valor máximo que pode ser obtido colocando itens na mochila sem exceder a capacidade.',
            'example_input': '4 8\n10 5\n40 4\n30 6\n50 3',
            'example_output': '90',
            'test_cases': [
                {'input': '4 8\n10 5\n40 4\n30 6\n50 3', 'output': '90'},
                {'input': '3 50\n60 10\n100 20\n120 30', 'output': '220'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Árvore Geradora Mínima',
            'state': 'Santa Catarina',
            'language': cpp,
            'difficulty': 'hard',
            'points': 70,
            'description': 'Implemente o algoritmo de Kruskal para encontrar a árvore geradora mínima de um grafo.',
            'input_description': 'A primeira linha contém dois inteiros N e M (1 ≤ N ≤ 10^5, 1 ≤ M ≤ 10^5), o número de vértices e arestas. As próximas M linhas contêm três inteiros U, V e W cada (1 ≤ U, V ≤ N, 1 ≤ W ≤ 10^6), indicando uma aresta entre os vértices U e V com peso W.',
            'output_description': 'O peso total da árvore geradora mínima. Se não for possível conectar todos os vértices, imprima "Impossivel".',
            'example_input': '4 5\n1 2 10\n1 3 6\n2 3 5\n2 4 15\n3 4 4',
            'example_output': '19',
            'test_cases': [
                {'input': '4 5\n1 2 10\n1 3 6\n2 3 5\n2 4 15\n3 4 4', 'output': '19'},
                {'input': '3 2\n1 2 10\n2 3 5', 'output': '15'}
            ],
            'time_limit': 2000
        },
        {
            'title': 'Contador de Palavras',
            'state': 'Sergipe',
            'language': python,
            'difficulty': 'medium',
            'points': 40,
            'description': 'Em Sergipe, terra da cultura rica, conte quantas vezes cada palavra aparece em um texto!',
            'input_description': 'Uma linha contendo um texto com palavras separadas por espaços. Apenas letras minúsculas e espaços.',
            'output_description': 'Para cada palavra única, imprima "palavra:frequencia", uma por linha, em ordem alfabética.',
            'example_input': 'o gato subiu no telhado o gato desceu',
            'example_output': 'desceu:1\ngato:2\nno:1\no:2\nsubiu:1\ntelhado:1',
            'test_cases': [
                {'input': 'o gato subiu no telhado o gato desceu', 'output': 'desceu:1\ngato:2\nno:1\no:2\nsubiu:1\ntelhado:1'},
                {'input': 'python e legal python e facil', 'output': 'e:2\nfacil:1\nlegal:1\npython:2'},
                {'input': 'a b c a b a', 'output': 'a:3\nb:2\nc:1'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Coloração de Grafos',
            'state': 'São Paulo',
            'language': cpp,
            'difficulty': 'hard',
            'points': 80,
            'description': 'Implemente um algoritmo para colorir um grafo não direcionado com o mínimo de cores possível, de modo que vértices adjacentes tenham cores diferentes.',
            'input_description': 'A primeira linha contém dois inteiros N e M (1 ≤ N ≤ 100, 1 ≤ M ≤ 10^4), o número de vértices e arestas. As próximas M linhas contêm dois inteiros U e V cada (1 ≤ U, V ≤ N), indicando uma aresta entre os vértices U e V.',
            'output_description': 'Na primeira linha, imprima K, o número de cores utilizadas. Na segunda linha, imprima N inteiros, onde o i-ésimo inteiro é a cor atribuída ao vértice i (as cores são numeradas de 1 a K).',
            'example_input': '5 6\n1 2\n1 3\n2 3\n2 4\n3 4\n4 5',
            'example_output': '3\n1 2 3 1 2',
            'test_cases': [
                {'input': '5 6\n1 2\n1 3\n2 3\n2 4\n3 4\n4 5', 'output': '3\n1 2 3 1 2'},
                {'input': '4 6\n1 2\n1 3\n1 4\n2 3\n2 4\n3 4', 'output': '4\n1 2 3 4'}
            ],
            'time_limit': 2000
        },
        {
            'title': 'Subsequência Contígua Máxima',
            'state': 'Alagoas',
            'language': python,
            'difficulty': 'medium',
            'points': 35,
            'description': 'Encontre a subsequência contígua de soma máxima em um array de números inteiros.',
            'input_description': 'A primeira linha contém um inteiro N (1 ≤ N ≤ 10^5), o tamanho do array. A segunda linha contém N inteiros separados por espaços, representando o array.',
            'output_description': 'A soma máxima de uma subsequência contígua do array.',
            'example_input': '9\n-2 1 -3 4 -1 2 1 -5 4',
            'example_output': '6',
            'test_cases': [
                {'input': '9\n-2 1 -3 4 -1 2 1 -5 4', 'output': '6'},
                {'input': '5\n-1 -2 -3 -4 -5', 'output': '-1'},
                {'input': '3\n1 2 3', 'output': '6'}
            ],
            'time_limit': 1000
        },
        {
            'title': 'Permutações',
            'state': 'Ceará',
            'language': java,
            'difficulty': 'medium',
            'points': 45,
            'description': 'Gere todas as permutações possíveis de uma string.',
            'input_description': 'Uma única string S (1 ≤ |S| ≤ 8) contendo apenas letras minúsculas.',
            'output_description': 'Todas as permutações possíveis da string S, uma por linha, em ordem lexicográfica.',
            'example_input': 'abc',
            'example_output': 'abc\nacb\nbac\nbca\ncab\ncba',
            'test_cases': [
                {'input': 'abc', 'output': 'abc\nacb\nbac\nbca\ncab\ncba'},
                {'input': 'aa', 'output': 'aa'}
            ],
            'time_limit': 1000
        }
    ]
    
    # Verifique se há desafios duplicados para o mesmo estado
    state_challenges = {}
    for challenge_data in challenges_data:
        state_name = challenge_data['state']
        if state_name in state_challenges:
            print(f"AVISO: Já existe um desafio para o estado {state_name}. Ignorando o novo desafio.")
            continue
            
        state_challenges[state_name] = True
        
        try:
            state = BrazilState.objects.get(name=challenge_data['state'])
            Challenge.objects.create(
                title=challenge_data['title'],
                state=state,
                language=challenge_data['language'],
                difficulty=challenge_data['difficulty'],
                points=challenge_data['points'],
                description=challenge_data['description'],
                input_description=challenge_data['input_description'],
                output_description=challenge_data['output_description'],
                example_input=challenge_data['example_input'],
                example_output=challenge_data['example_output'],
                test_cases=challenge_data['test_cases'],
                time_limit=challenge_data['time_limit']
            )
        except BrazilState.DoesNotExist:
            print(f"Erro: Estado '{challenge_data['state']}' não encontrado no banco de dados.")
        except Exception as e:
            print(f"Erro ao criar desafio para {challenge_data['state']}: {e}")
    
    print(f"Adicionados {Challenge.objects.count()} desafios.")

def create_admin_user():
    """Cria um usuário admin para testes"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("Usuário admin criado com sucesso.")
    else:
        print("Usuário admin já existe.")

if __name__ == '__main__':
    print("Iniciando população do banco de dados...")
    populate_states()
    populate_languages()
    populate_challenges()
    create_admin_user()
    print("População do banco de dados concluída.")
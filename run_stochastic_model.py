from networkx.convert_matrix import _generate_weighted_edges
import pyomo.pysp.util.rapper as rapper
from pyomo.pysp.scenariotree.tree_structure_model import CreateAbstractScenarioTreeModel
import pyomo.environ as pyo
import numpy as np
import matplotlib.pyplot as plt
import random as rnd
import pathlib
import time
import sys

import matplotlib.cm as cm
sys.path.append(str(pathlib.Path(__file__).parent.absolute()))
from generate_scenarios import main as update_scenarios

def main(data, verbose=True):
    start_time = time.time()
    retry = False
    while True:
        if retry:
            data['node_id'] += 1
        update_scenarios(scenarios_qtd=9, reduced_scenarios_qtd=3, data=data)
        solvername = 'cplex'
        path = str(pathlib.Path(__file__).parent.absolute())
        abstract_tree = CreateAbstractScenarioTreeModel()
        concrete_tree = abstract_tree.create_instance(path + '/ScenarioStructure.dat')
        stsolver = rapper.StochSolver(fsfile=path + '/ReferenceModel.py', tree_model=concrete_tree)
        ef_sol = stsolver.solve_ef(solvername,tee=True, generate_weighted_cvar=True, cvar_weight=1.0, risk_alpha=0.1)
        if ef_sol.solver.termination_condition != pyo.TerminationCondition.optimal:
            if verbose:
                print(f'Not optimal solution: {ef_sol.solver.termination_condition}')
            retry = True
            continue
        else:
            if verbose:
                print(f'Optimal solution found: {ef_sol.solver.termination_condition}')
            retry = False
        scenarios = stsolver.scenario_tree.scenarios
        # print(scenarios.instance)
        # model = rnd.choice(scenarios).instance
        model = scenarios[0].instance
        print(model)
        model.pprint()
        break

    del scenarios
    del stsolver
    del ef_sol
    del abstract_tree
    del concrete_tree
    end_time = time.time()  # Captura o tempo após a execução
    execution_time = end_time - start_time  # Calcula o tempo de execução
    if verbose:
        print(f'Tempo de execução: {execution_time:.2f} segundos')

    return model

# São dois gráficos, onde o primeiro mostra a quantidade de potência (kW) spot e bilateral comprada/vendida durante o dia
# O segundo mostra o preço do kWh do mercado bilateral e spot
def plot_energy_results(model):
    """
    Função para extrair os valores das variáveis de potência (spot e bilateral) e preços,
    e gerar os gráficos correspondentes.
    """
    # Extração dos dados das variáveis do modelo
    TIME_INDEX = list(range(96))  # Intervalos de 15 minutos
    spot_prices_values = [pyo.value(model.spot_prices[t]) for t in TIME_INDEX]
    bilateral_prices_values = [pyo.value(model.bilateral_price) for t in TIME_INDEX]  # Pode ser constante, verifique
    p_spot_values = [pyo.value(model.p_spot[t]) for t in TIME_INDEX]
    # print('potencia spot')
    # print(p_spot_values)
    p_bilateral_values = [pyo.value(model.p_bilateral[t]) for t in TIME_INDEX]
    # print('potencia bilateral')
    # print(p_bilateral_values)
    # Configuração do gráfico
    plt.figure(figsize=(14, 8))
    # Potência Spot vs Potência Bilateral
    plt.subplot(2, 1, 1)
    plt.plot(TIME_INDEX, p_spot_values, label='Potência Spot', color='blue', linestyle='-', marker='o')
    plt.plot(TIME_INDEX, p_bilateral_values, label='Potência Bilateral', color='red', linestyle='-', marker='x')
    plt.title('Potência Spot vs Potência Bilateral')
    plt.xlabel('Hora (Intervalos de 15 minutos)')
    plt.ylabel('Potência (kW)')
    plt.legend()
    plt.grid(True)
    # Preço Spot vs Preço Bilateral
    plt.subplot(2, 1, 2)
    plt.plot(TIME_INDEX, spot_prices_values, label='Preço Spot', color='green', linestyle='-', marker='o')
    plt.plot(TIME_INDEX, bilateral_prices_values, label='Preço Bilateral', color='orange', linestyle='-', marker='x')
    plt.title('Preço Spot vs Preço Bilateral')
    plt.xlabel('Hora (Intervalos de 15 minutos)')
    plt.ylabel('Preço (EUR/kWh)')
    plt.legend()
    plt.grid(True)
    # Exibindo o gráfico
    plt.tight_layout()
    plt.show()

# São 4 Gráficos em uma tela:
# 1°: Mostram os momentos nos quais as cargas estão ligadas durante o dia
# 2°: Demanda dos equipamentos da resposta da demanda durante o dia
# 3°: Potência spot (kWh) comprada/vendida durante o dia
# 4°: Potência bilateral (kWh) comprada durante o dia
def plotar_cargas_demanda_precos(model):
    # Definindo o intervalo de tempo
    time_index = list(range(96))  # Intervalos de 15 minutos
    # Dados das variáveis de carga, demanda e preços
    cargas_ligadas = {carga: [] for carga in model.cargas}
    demanda_total_por_tempo = []
    p_spot_por_tempo = []
    p_bilateral_por_tempo = []
    # Calculando os valores para cada intervalo de tempo
    for t in time_index:
        # Cargas ligadas
        for carga in model.cargas:
            if 0.95<= pyo.value(model.cargas_var_ligadas[carga, t]) <= 1.05:
                cargas_ligadas[carga].append(t)
        # Demanda total
        demanda_total = sum([
            pyo.value(model.cargas_potencia[carga] * model.cargas_var_ligadas[carga, t])
            for carga in model.cargas
        ])
        demanda_total_por_tempo.append(demanda_total)
        # Preços spot e bilateral
        p_spot_por_tempo.append(pyo.value(model.p_spot[t]))
        
        p_bilateral_por_tempo.append(pyo.value(model.p_bilateral[t]))
    print('SPOT')
    print(p_spot_por_tempo)  
    print('BILATERAL')
    print(p_bilateral_por_tempo)
    # Plotando os gráficos
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    # Cargas Ligadas
    axs[0, 0].set_title('Cargas Ligadas ao Longo do Tempo')
    for carga, horarios_t in cargas_ligadas.items():
        axs[0, 0].scatter(horarios_t, [carga] * len(horarios_t), label=carga, s=100)
    axs[0, 0].set_xlabel("Hora do dia")
    axs[0, 0].set_ylabel("Cargas")
    axs[0, 0].grid(True)
    axs[0, 0].legend(loc='upper right')
    # Demanda Total
    axs[0, 1].plot(time_index, demanda_total_por_tempo, label='Demanda Total', color='green', linestyle='-', linewidth=2)
    axs[0, 1].set_title('Demanda Total das cargas deslocáveis')
    axs[0, 1].set_xlabel("Tempo (intervalos de 15 minutos)")
    axs[0, 1].set_ylabel("Demanda Total (kW)")
    axs[0, 1].grid(True)
    axs[0, 1].legend()
    # Preço Spot
    axs[1, 0].plot(time_index, p_spot_por_tempo, label='Potência Spot', color='blue', linestyle='-', linewidth=2)
    axs[1, 0].set_title('Potência Spot ao Longo do Tempo')
    axs[1, 0].set_xlabel("Tempo (intervalos de 15 minutos)")
    axs[1, 0].set_ylabel("Potência Spot (kWh)")
    axs[1, 0].grid(True)
    axs[1, 0].legend()
    # Preço Bilateral
    axs[1, 1].plot(time_index, p_bilateral_por_tempo, label='Potência Bilateral', color='orange', linestyle='-', linewidth=2)
    axs[1, 1].set_title('Potência Bilateral ao Longo do Tempo')
    axs[1, 1].set_xlabel("Tempo (intervalos de 15 minutos)")
    axs[1, 1].set_ylabel("Potência Bilateral (kWh)")
    axs[1, 1].grid(True)
    axs[1, 1].legend()
    plt.tight_layout()
    plt.show()
# São dois gráficos, onde o primeiro mostra a quantidade de potência (kW) spot e bilateral comprada/vendida durante o dia
# O segundo mostra o preço do kWh do mercado bilateral e spot
def plot_energy_results(model):
    """
    Função para extrair os valores das variáveis de potência (spot e bilateral) e preços,
    e gerar os gráficos correspondentes.
    """
    # Extração dos dados das variáveis do modelo
    TIME_INDEX = list(range(96))  # Intervalos de 15 minutos
    spot_prices_values = [pyo.value(model.spot_prices[t]) for t in TIME_INDEX]
    bilateral_prices_values = [pyo.value(model.bilateral_price) for t in TIME_INDEX]  # Pode ser constante, verifique
    p_spot_values = [pyo.value(model.p_spot[t]) for t in TIME_INDEX]
    p_bilateral_values = [pyo.value(model.p_bilateral[t]) for t in TIME_INDEX]
    # Configuração do gráfico
    plt.figure(figsize=(14, 8))
    # Potência Spot vs Potência Bilateral
    plt.subplot(2, 1, 1)
    plt.plot(TIME_INDEX, p_spot_values, label='Potência Spot', color='blue', linestyle='-', marker='o')
    plt.plot(TIME_INDEX, p_bilateral_values, label='Potência Bilateral', color='red', linestyle='-', marker='x')
    plt.title('Potência Spot vs Potência Bilateral')
    plt.xlabel('Hora (Intervalos de 15 minutos)')
    plt.ylabel('Potência (kW)')
    plt.legend()
    plt.grid(True)
    # Preço Spot vs Preço Bilateral
    plt.subplot(2, 1, 2)
    plt.plot(TIME_INDEX, spot_prices_values, label='Preço Spot', color='green', linestyle='-', marker='o')
    plt.plot(TIME_INDEX, bilateral_prices_values, label='Preço Bilateral', color='orange', linestyle='-', marker='x')
    plt.title('Preço Spot vs Preço Bilateral')
    plt.xlabel('Hora (Intervalos de 15 minutos)')
    plt.ylabel('Preço (EUR/kWh)')
    plt.legend()
    plt.grid(True)
    # Exibindo o gráfico
    plt.tight_layout()
    plt.show()
# São 4 gráficos:
# 1°: Mostra o armazenamento da bateria em kWh durante o dia
# 2°: Mostra a potência adquirida/vendida nos mercados spot/bilateral em kWh
# 3°: Mostra a demanda líquida, armazenada e total em kWh durante o dia
# 4°: Mostra o preço da tarifa do mercado spot durante o dia
def plotar_soc_e_power(model):
    TIME_INDEX = list(range(96)) 
    soc_data = [pyo.value(model.soc[t]) for t in TIME_INDEX]
    print('SOC Bateria')
    print(soc_data)
    #time_data = [t / 4 for t in range(len(soc_data))]
    p_spot_data = [pyo.value(model.p_spot[t]) for t in TIME_INDEX]
    p_bilateral_data = [pyo.value(model.p_bilateral[t]) for t in TIME_INDEX]
    demand_data = [pyo.value(model.demanda_total[t]) for t in TIME_INDEX]
    p_charge_data =[pyo.value(model.p_charge[t]) for t in TIME_INDEX]
    p_discharge_data = [pyo.value(model.p_discharge[t]) for t in TIME_INDEX]
    p_storage_data = [pyo.value(p_charge_data[t] - p_discharge_data[t]) for t in TIME_INDEX]
    aux_data = [pyo.value(demand_data[t] + p_storage_data[t]) for t in TIME_INDEX]
    spot_prices_data = [pyo.value(model.spot_prices[t]) for t in TIME_INDEX]
    bilateral_prices_data = [pyo.value(model.bilateral_price) for t in TIME_INDEX]
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    axs[0, 0].step(TIME_INDEX, soc_data)
    axs[0, 0].set_title('Estado da carga da bateria')
    axs[0, 0].grid(True)
    axs[0, 0].set_ylabel("Potência armazenada (kWh)")
    axs[0, 0].set_xlabel("Espaços de Tempo de 15 minutos")
    axs[0, 1].step(TIME_INDEX, p_spot_data, label='Spot')
    axs[0, 1].step(TIME_INDEX, p_bilateral_data, label='Bilateral')
    axs[0, 1].set_title('Potência adquirida/vendida nos mercados')
    axs[0, 1].legend()
    axs[0, 1].set_ylabel("Potência (kWh)")
    axs[0, 1].set_xlabel("Espaços de Tempo de 15 minutos")
    axs[0, 1].grid(True)
    axs[1, 0].step(TIME_INDEX, demand_data, label='Carga + Geração')
    axs[1, 0].step(TIME_INDEX, p_storage_data, label='Armazenamento')
    axs[1, 0].step(TIME_INDEX, aux_data, label='Total')
    axs[1, 0].set_title('Demanda Líquida')
    axs[1, 0].set_ylabel("Potência (kWh)")
    axs[1, 0].set_xlabel("Espaços de Tempo de 15 minutos")
    axs[1, 0].legend()
    axs[1, 0].grid(True)
    axs[1, 1].step(TIME_INDEX, spot_prices_data, label='Spot')
    axs[1, 1].step(TIME_INDEX, bilateral_prices_data, label='Bilateral')
    axs[1, 1].set_title('Preço Spot e Preço Bilateral')
    axs[1, 1].set_ylabel("Preço (EUR/kWh)")
    axs[1, 1].set_xlabel("Espaços de Tempo de 15 minutos")
    axs[1, 1].legend()
    axs[1, 1].grid(True)
    plt.tight_layout()
    plt.show()

def plotar_variavel_em_funcionamento(model, var_name, title, ax):
    horarios = {carga: [] for carga in model.cargas}
    for t in range(24*4):  # Assumindo que TIME_INDEX é de 0 a 96
        for carga in model.cargas:
            if 0.95<=pyo.value(getattr(model, var_name)[carga, t]) <= 1.05:
                horarios[carga].append(t)
    for carga, horarios_t in horarios.items():
        ax.scatter(horarios_t, [carga] * len(horarios_t), label=carga, s=100)
    ax.set_yticks(range(len(model.cargas)))
    ax.set_yticklabels(model.cargas)
    ax.set_xticks(range(0, 96, 4))
    ax.set_xticklabels([f"{int(t/4)}:{(t%4)*15:02d}" for t in range(0, 96, 4)], rotation=45)
    ax.set_xlabel("Hora do dia")
    ax.set_title(title)
    ax.grid(True)
    # ax.legend()

def plotar_potencia_cargas(model, ax):
    # Definindo o intervalo de tempo
    time_index = list(range(96))
    # Lista para armazenar as potências totais das cargas ao longo do tempo
    potencia_total_por_tempo = {carga: [] for carga in model.cargas}
    # Loop sobre todas as cargas e calcular a potência consumida em cada intervalo de tempo
    for carga in model.cargas:
        # Calculando a potência da carga para cada instante de tempo
        potencia_carga = [
            pyo.value(model.cargas_potencia[carga] * model.cargas_var_ligadas[carga, t])
            for t in time_index
        ]
        potencia_total_por_tempo[carga] = potencia_carga
    # Plotando as potências das cargas ao longo do tempo
    for carga, potencias in potencia_total_por_tempo.items():
        ax.plot(time_index, potencias, label=carga)
    # Adicionando título, rótulos e legenda
    ax.set_title('Potência das Cargas ao Longo do Tempo')
    ax.set_xlabel('Tempo (intervalos de 15 minutos)')
    ax.set_ylabel('Potência (kW)')
    ax.legend()
    ax.grid(True)
def plotar_todos_os_graficos(model):
    # Criar uma figura com 2 linhas e 2 colunas de subgráficos
    fig, axs = plt.subplots(2, 2, figsize=(14, 12))
    # Plotar os 4 gráficos nos subgráficos
    plotar_variavel_em_funcionamento(model, "cargas_var_ligadas", "Cargas em Funcionamento", axs[0, 0])
    plotar_variavel_em_funcionamento(model, "cargas_flag_partida", "Flag de partida", axs[0, 1])
    plotar_variavel_em_funcionamento(model, "cargas_flag_desliga", "Flag de desligamento", axs[1, 0])
    plotar_potencia_cargas(model, axs[1, 1])
    # Ajustar layout para evitar sobreposição
    plt.tight_layout()
    plt.show()

def plotar_potencia_cargas_com_total(model):
    # Definindo o intervalo de tempo
    time_index = list(range(96))  # Intervalos de 15 minutos
    # Lista para armazenar as potências totais das cargas e da demanda ao longo do tempo
    potencia_total_por_tempo = {carga: [] for carga in model.cargas}
    demanda_por_tempo = []  # Lista para armazenar a demanda total ao longo do tempo
    # Loop sobre todas as cargas e calcular a potência consumida em cada intervalo de tempo
    for carga in model.cargas:
        # Calculando a potência da carga para cada instante de tempo
        potencia_carga = [
            pyo.value(model.cargas_potencia[carga] * model.cargas_var_ligadas[carga, t])
            for t in time_index
        ]
        potencia_total_por_tempo[carga] = potencia_carga
    # Calculando a demanda total ao longo do tempo (soma das potências das cargas em cada instante de tempo)
    for t in time_index:
        demanda_total = sum([
            pyo.value(model.cargas_potencia[carga] * model.cargas_var_ligadas[carga, t])
            for carga in model.cargas
        ])
        demanda_por_tempo.append(demanda_total)
    # Plotando as potências das cargas ao longo do tempo
    plt.figure(figsize=(12, 6))
    # Plotando a potência das cargas
    for carga, potencias in potencia_total_por_tempo.items():
        plt.plot(time_index, potencias, label=f'Potência {carga}')
    # Plotando a demanda total
    plt.plot(time_index, demanda_por_tempo, label='Demanda Total', color='black', linestyle='--', linewidth=2)
    # Adicionando título, rótulos e legenda
    plt.title('Potência das Cargas e Demanda Total ao Longo do Tempo')
    plt.xlabel('Tempo (intervalos de 15 minutos)')
    plt.ylabel('Potência (kW)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Gráfico que plota quando a carga está em funcionamento, a janela de tempo inicial, final e desejado
def Plotar_cargas_com_janelas(model):
    # Gerar uma lista de cores distintas para cada carga
    num_cargas = len(model.cargas)
    cores = cm.get_cmap("tab10", num_cargas)  # Usando uma paleta de cores distintas
    cores_cargas = {carga: cores(i) for i, carga in enumerate(model.cargas)}  # Mapear carga -> cor
    # Dicionários para armazenar os horários de funcionamento, início, término e desejado das cargas
    horarios = {carga: [] for carga in model.cargas}
    tempos_inicio = {carga: [] for carga in model.cargas}
    tempos_termino = {carga: [] for carga in model.cargas}
    tempos_desejados = {carga: [] for carga in model.cargas}
    # Iterando sobre os tempos (de 0 a 96, assumindo 15 minutos por intervalo)
    for t in range(24*4):  # Considerando que o índice de tempo vai de 0 a 96 (24 horas * 4 intervalos por hora)
        for carga in model.cargas:
            # Verificando se a carga está ligada no tempo t
            if 0.95<=pyo.value(getattr(model, "cargas_var_ligadas")[carga, t]) <=1.05:
                horarios[carga].append(t)
            
            # Verificando os tempos de início, término e desejado
            # O valor é armazenado diretamente nos parâmetros, sem necessidade de indexar com t
            if pyo.value(model.cargas_tempo_inicio[carga]) == t:
                tempos_inicio[carga].append(t)
            
            if pyo.value(model.cargas_tempo_termino[carga]) == t:
                tempos_termino[carga].append(t)
            
            if pyo.value(model.cargas_tempo_desejado[carga]) == t:
                tempos_desejados[carga].append(t)
    
    # Criando o gráfico
    plt.figure(figsize=(10, 6))
    
    # Para cada carga, plotar os pontos de funcionamento e tempos
    for carga in model.cargas:
        # Definir a cor para a carga
        cor = cores_cargas[carga]

        # Plotando os horários de funcionamento das cargas
        plt.scatter(horarios[carga], [carga] * len(horarios[carga]), label=f'{carga} Funcionando', color=cor, s=100)

        # Plotando os tempos de início (linha tracejada)
        # for t_inicio in tempos_inicio[carga]:
        #     plt.axvline(x=t_inicio, color=cor, linestyle='--', lw=2,alpha=1)
        
        # Plotando os tempos de término (linha tracejada)
        # for t_termino in tempos_termino[carga]:
        #     plt.axvline(x=t_termino, color=cor, linestyle='-', lw=3,alpha=0.5)
        
        # Plotando os tempos desejados (quadrado)
        for t_desejado in tempos_desejados[carga]:
            plt.plot(t_desejado, carga, 's',markersize=12, color=cor, label=f'{carga} Tempo Desejado')

    # Ajustando os eixos e rótulos
    plt.yticks(range(len(model.cargas)), model.cargas)
    plt.xticks(range(0, 96, 4), [f"{int(t/4)}:{(t%4)*15:02d}" for t in range(0, 96, 4)], rotation=45)
    plt.xlabel("Hora do dia")
    plt.title("Funcionamento das Cargas com Tempos de Início, Término e Desejado")
    plt.grid(True, linestyle='--', alpha=0.5)    
    plt.tight_layout()

    # Adicionando a legenda e ajustando o espaço para evitar que ela seja cortada
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=10)

    # Ajustando a área do gráfico para que a legenda não seja cortada
    plt.subplots_adjust(right=0.8)

    # Exibindo o gráfico
    plt.show()

# Gráfico com a função objetivo constante
# Implementar o gráfico em função do tempo da função objetivo

def plotar_funcao_objetivo(model):
    # Definindo o intervalo de tempo
    time_index = list(range(96))  # Intervalos de 15 minutos
    
    # Lista para armazenar os valores da função objetivo ao longo do tempo
    valores_objetivo_por_tempo = []

    # Calculando o valor da função objetivo para cada intervalo de tempo
    for t in time_index:
        # Atualiza as variáveis de decisão do modelo para o instante t (se necessário)
        # Você pode precisar ajustar isso dependendo de como o seu modelo de otimização é estruturado
        # Exemplo: model.temporal_var[t] = valor_desejado
        
        # Avaliando a função objetivo para o intervalo de tempo t
        valor_objetivo = pyo.value(model.obj)  # Aqui, substitua 'objetivo' pela sua variável de função objetivo
        
        # Armazenando o valor da função objetivo
        valores_objetivo_por_tempo.append(valor_objetivo)
    
    # Plotando o valor da função objetivo ao longo do tempo
    plt.figure(figsize=(12, 6))
    plt.plot(time_index, valores_objetivo_por_tempo, label='Função Objetivo', color='blue', linestyle='-', linewidth=2)
    
    # Adicionando título, rótulos e legenda
    plt.title('Valor da Função Objetivo ao Longo do Tempo')
    plt.xlabel('Tempo (intervalos de 15 minutos)')
    plt.ylabel('Valor da Função Objetivo')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# def plotar_funcao_objetivo_e_demanda_total(model):
#     # Definindo o intervalo de tempo
#     time_index = list(range(96))  # 96 intervalos de 15 minutos
    
#     # Lista para armazenar os valores da função objetivo ao longo do tempo
#     valores_objetivo_por_tempo = []
#     demanda_total_por_tempo = []

#     # Calculando o valor da função objetivo e a demanda total para cada intervalo de tempo
#     for t in time_index:
#         # Calculando a função objetivo sem penalização de conforto
#         custo_t = pyo.value(model.p_bilateral[t]) * pyo.value(model.bilateral_price) + pyo.value(model.p_spot[t]) * pyo.value(model.spot_prices[t])
#         valor_objetivo_sem_conforto = custo_t * 0.25  # dt = 0.25 (15 minutos)
#         valores_objetivo_por_tempo.append(valor_objetivo_sem_conforto)

    
#     # Criando o gráfico com dois eixos Y
#     fig, ax1 = plt.subplots(figsize=(12, 6))
    
#     # Plotando a função objetivo no primeiro eixo Y
#     ax1.plot(time_index, valores_objetivo_por_tempo, label='Função Objetivo Sem Conforto', color='blue', linestyle='-', linewidth=2)
#     ax1.set_xlabel('Tempo (intervalos de 15 minutos)')
#     ax1.set_ylabel('Valor da Função Objetivo', color='blue')
#     ax1.tick_params(axis='y', labelcolor='blue')
#     ax1.grid(True)
    
#     # Criando o segundo eixo Y para a demanda total
#     ax2 = ax1.twinx()  # Cria o segundo eixo Y compartilhando o eixo X
#     ax2.plot(time_index, demanda_total_por_tempo, label='Demanda Total', color='green', linestyle='-', linewidth=2)
#     ax2.set_ylabel('Demanda Total (kW)', color='green')
#     ax2.tick_params(axis='y', labelcolor='green')
    
#     # Adicionando título e legenda
#     plt.title('Função Objetivo Sem Conforto e Demanda Total ao Longo do Tempo')
#     fig.tight_layout()  # Ajusta o layout para evitar sobreposição
    
#     # Exibindo o gráfico
#     plt.show()
def plotar_funcao_objetivo_e_demanda_total(model):
    # Definindo o intervalo de tempo
    time_index = list(range(96))  # 96 intervalos de 15 minutos
    
    # Listas para armazenar os valores da função objetivo e o valor acumulado
    valores_objetivo_por_tempo = []
    acumulado_por_tempo = []
    acumulado = 0
    print ('Custo acumulado')
    # Calculando a função objetivo e seu acumulado para cada intervalo de tempo
    for t in time_index:
        # Calculando a função objetivo sem penalização de conforto
        custo_t = pyo.value(model.p_bilateral[t]) * pyo.value(model.bilateral_price) + pyo.value(model.p_spot[t]) * pyo.value(model.spot_prices[t])
        valor_objetivo_sem_conforto = custo_t * 0.25  # dt = 0.25 (15 minutos)
        
        # Atualizando o acumulado
        acumulado += valor_objetivo_sem_conforto
        
        print (acumulado)
        # Adicionando os valores nas listas
        valores_objetivo_por_tempo.append(valor_objetivo_sem_conforto)
        acumulado_por_tempo.append(acumulado)

    # Criando o gráfico com dois eixos Y
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plotando a função objetivo no primeiro eixo Y
    ax1.plot(time_index, valores_objetivo_por_tempo, label='Função Objetivo Sem Conforto', color='blue', linestyle='-', linewidth=2)
    ax1.set_xlabel('Tempo (intervalos de 15 minutos)')
    ax1.set_ylabel('Valor da Função Objetivo', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True)
    
    # Criando o segundo eixo Y para o acumulado
    ax2 = ax1.twinx()  # Cria o segundo eixo Y compartilhando o eixo X
    ax2.plot(time_index, acumulado_por_tempo, label='Acumulado da Função Objetivo', color='orange', linestyle='--', linewidth=2)
    ax2.set_ylabel('Custo de energia acumulado (EUR)', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')
    
    # Adicionando título e legenda
    plt.title('Função Objetivo Sem Conforto e Acumulado da Função Objetivo ao Longo do Tempo')
    fig.tight_layout()  # Ajusta o layout para evitar sobreposição
    
    # Exibindo o gráfico
    plt.show()

def plotar_demanda(model):
    # Definindo o intervalo de tempo
    time_index = list(range(96))  # Assumindo 96 intervalos de 15 minutos (24 horas)

    # Inicializar as listas para armazenar a demanda das cargas não deslocáveis e deslocáveis
    demanda_nao_deslocavel = [pyo.value(model.demand[t]) for t in time_index]
    
    # Inicializar a demanda total das cargas deslocáveis ao longo do tempo
    demanda_deslocavel = [sum(pyo.value(model.cargas_potencia[carga] * model.cargas_var_ligadas[carga, t])
                              for carga in model.cargas) for t in time_index]
    
    # Calcular a soma das demandas (deslocáveis + não deslocáveis)
    demanda_total = [demanda_nao_deslocavel[t] + demanda_deslocavel[t] for t in time_index]
    print('demanda total')
    print(demanda_total)

def exportar_todas_as_cargas_para_json(model, caminho="cargas_status.json"):
    import json  # Certifique-se de importar o módulo json

    resultado = {}

    for carga in model.cargas:
        nome = str(carga)
        resultado[nome] = []
        for t in range(96):
            valor = pyo.value(model.cargas_var_ligadas[carga, t])
            resultado[nome].append(1 if valor >= 0.5 else 0)

    with open(caminho, "w") as f:
        json.dump(resultado, f, indent=4)

    print(f"JSON exportado para: {caminho}")
    return caminho


    # Plotar a demanda das cargas não deslocáveis
    plt.figure(figsize=(12, 6))
    plt.plot(time_index, demanda_nao_deslocavel, label="Demanda Cargas Não Deslocáveis", color='blue', linestyle='-', linewidth=2)

    # Plotar a demanda das cargas deslocáveis
    plt.plot(time_index, demanda_deslocavel, label="Demanda Cargas Deslocáveis", color='red', linestyle='--', linewidth=2)

    # Plotar a soma das demandas (deslocáveis + não deslocáveis)
    plt.plot(time_index, demanda_total, label="Soma das Demandas (Total)", color='green', linestyle=':', linewidth=2)

    # Adicionar título e rótulos aos eixos
    plt.title('Demanda Total das Cargas (Deslocáveis e Não Deslocáveis) ao Longo do Tempo')
    plt.xlabel('Tempo (intervalos de 15 minutos)')
    plt.ylabel('Demanda (kW)')
    
    # Adicionar a legenda
    plt.legend()

    # Adicionar uma grade
    plt.grid(True)

    # Ajustar o layout para evitar sobreposição
    plt.tight_layout()

    # Exibir o gráfico
    plt.show()

if __name__ == '__main__':
    config = {
        'has_storage': True,
        'storage_rate': 0.2,
        'storage_size': 10.0,
        'max_energy_flow': 0.2 * 10.0,
        'max_soc': 10.0,
        'min_soc': 0.1 * 10.0,
        'bilateral_price': 0.038,
        #38 euros/mWh
        'bilateral_max': 10.0,
        'node_id': 32,
        'load_kw': 4,
        'gen_kw': 1.0
        }
        
    plot_energy_results(model)
    plotar_cargas_demanda_precos(model)
    plotar_soc_e_power(model)
    # plotar_cargas_em_funcionamento(model)
    # plotar_flag_em_funcionamento(model)
    # plotar_desflag_em_funcionamento(model)
    plotar_todos_os_graficos(model)
    plotar_potencia_cargas_com_total(model)
    plotar_funcao_objetivo(model)
    Plotar_cargas_com_janelas(model)
    plotar_funcao_objetivo_e_demanda_total(model)
    plotar_demanda(model)
    exportar_todas_as_cargas_para_json(model)

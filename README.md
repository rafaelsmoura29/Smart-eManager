# ⚡ Smart-eManager: Gerenciamento Energético de Prosumidores com Otimização Estocástica e Hardware-in-the-Loop

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pyomo](https://img.shields.io/badge/Modeling-Pyomo%20%2F%20PySP-orange.svg)](https://pyomo.readthedocs.io/)
[![Solver CPLEX](https://img.shields.io/badge/Solver-IBM%20ILOG%20CPLEX-red.svg)](https://www.ibm.com/products/ilog-cplex-optimization-studio)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Raspberry Pi](https://img.shields.io/badge/Hardware-Raspberry%20Pi-C51A4A.svg)](https://www.raspberrypi.com/)
[![GREI UFC](https://img.shields.io/badge/Research-GREI%20--%20UFC-005691.svg)](http://www.grei.ufc.br/)

O **Smart-eManager** é uma plataforma integrada de **Gerenciamento Inteligente de Recursos Energéticos Residenciais (HEMS - Home Energy Management System)** baseada em **Programação Matemática Estocástica em Dois Estágios**, **Resposta da Demanda (DR)** e validação experimental em **Hardware-in-the-Loop (HIL)** utilizando **Raspberry Pi**.

O sistema calcula o despacho ótimo de cargas residenciais, contratos bilaterais e banco de baterias (BESS) sob as incertezas de geração solar fotovoltaica, demanda não-gerenciável e preços do mercado de energia (Mercado Spot). Em seguida, os sinais de despacho diário são transmitidos via rede para uma **Raspberry Pi**, que atua fisicamente em um painel de LEDs emulando o acionamento real dos aparelhos eletrodomésticos.

---

## 🏛️ Contexto Acadêmico e Institucional

Este projeto é fruto da pesquisa de formação acadêmica (Trabalho de Conclusão de Curso / Pesquisa Científica) desenvolvida no:
* **Laboratório/Grupo:** **GREI - Grupo de Redes Elétricas Inteligentes**
* **Instituição:** **Universidade Federal do Ceará (UFC)**
* **Autor:** Rafael dos Santos Moura
* **Orientador:** Prof. Dr. Lucas Silveira Melo

---

## 🧭 Índice

1. [Visão Geral e Arquitetura](#-visão-geral-e-arquitetura)
2. [Fundamentação Matemática e Modelagem](#-fundamentação-matemática-e-modelagem)
3. [Estrutura do Repositório](#-estrutura-do-repositório)
4. [Mapeamento de Cargas e Hardware](#-mapeamento-de-cargas-e-hardware)
5. [Pré-requisitos e Dependências](#-pré-requisitos-e-dependências)
6. [Guia de Instalação](#-guia-de-instalação)
7. [Como Utilizar](#-como-utilizar)
8. [Documentação da API (Servidor Raspberry)](#-documentação-da-api-servidor-raspberry)
9. [Citação Acadêmica](#-citação-acadêmica)
10. [Licença e Autoria](#-licença-e-autoria)

---

## 🔭 Visão Geral e Arquitetura

A arquitetura do **Smart-eManager** divide-se em duas camadas principais conectadas via rede local:

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 ESTAÇÃO PC / SERVIDOR                  │
                  │                                                        │
                  │  • Dados Históricos (Geração PV, Cargas, Nord Pool)    │
                  │  • Geração e Redução de Cenários (Dist. Kantorovich)   │
                  │  • Modelo Algébrico Estocástico (Pyomo / PySP)         │
                  │  • Resolução Ótima via IBM ILOG CPLEX                  │
                  │  • Exportação da Matriz de Despacho (cargas_status.json)│
                  └───────────────────────────┬────────────────────────────┘
                                              │
                                              │ HTTP POST /atualizar_cargas
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │            DISPOSITIVO BORDA (RASPBERRY PI)            │
                  │                                                        │
                  │  • Servidor FastAPI (serv2.py)                         │
                  │  • Mapeamento de Cargas -> Pinos GPIO (BCM)            │
                  │  • Temporização assíncrona por intervalos (15 min)     │
                  │  • Mock GPIO automático para testes no PC              │
                  └───────────────────────────┬────────────────────────────┘
                                              │
                                              │ Sinais Elétricos (GPIO HIGH/LOW)
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │               BANCADA DE ATUAÇÃO FÍSICA                │
                  │                                                        │
                  │  [LED 17] Máquina de Lavar  [LED 23] Ar Condicionado 1 │
                  │  [LED 18] Forno Elétrico    [LED 24] Ar Condicionado 2 │
                  │  [LED 27] Aquecedor         [LED 25] Ar Condicionado 3 │
                  │  [LED 22] Lavadora Pratos   [LED 05] Robô Aspirador    │
                  └────────────────────────────────────────────────────────┘
```

### Principais Destaques:
* **Horizonte de 24 Horas em 96 Intervalos:** Resolução temporal de 15 minutos ($dt = 0{,}25\text{ h}$).
* **Gestão Integrada BESS:** Considera limites operacionais de potência de carga/descarga e State-of-Charge (SoC).
* **Conforto do Usuário:** O modelo penaliza atrasos ou adiantamentos em relação ao horário desejado de operação de cada equipamento.
* **Operação Ininterrupta das Cargas:** Cada equipamento, ao ser iniciado, cumpre seu ciclo de trabalho integral sem interrupções artificiais.
* **Hardware-in-the-Loop:** Validação em tempo quase-real da viabilidade física dos comandos.

---

## 📐 Fundamentação Matemática e Modelagem

O problema é formulado como um **Problema de Programação Estocástica Linear Inteira Mista (MILP) em Dois Estágios**:

### 1. Primeiro Estágio (Decisões Here-and-Now)
Tomadas no início do horizonte de planejamento, antes da revelação das incertezas:
* Contratação de volume de energia no mercado bilateral ($p^{\text{bilateral}}_t$);
* Programação inicial do banco de baterias ($SoC_t$, $p^{\text{ch}}_t$, $p^{\text{dch}}_t$).

### 2. Segundo Estágio (Decisões Wait-and-See)
Ajustes realizados para cada cenário $\omega \in \Omega$ após a revelação da incerteza:
* Compra e venda de energia no Mercado Spot ($p^{\text{spot}}_{t, \omega}$);
* Acionamento das cargas deslocáveis ($x_{c, t} \in \{0, 1\}$);
* Gestão dos desvios de conforto temporal ($\delta^+_c, \delta^-_c$).

### 3. Função Objetivo
Minimiza o custo operacional total esperado de energia somado à penalização por desconforto do usuário e à métrica de aversão ao risco **CVaR (Conditional Value at Risk)**:

$$\min \sum_{\omega \in \Omega} \pi_\omega \left[ \sum_{t=1}^{96} \left( p^{\text{bilateral}}_t \cdot \lambda^{\text{bilateral}} + p^{\text{spot}}_{t, \omega} \cdot \lambda^{\text{spot}}_{t, \omega} \right) \Delta t \right] + \sum_{c \in \mathcal{C}} \left( \delta^+_c + \delta^-_c \right)$$

### 4. Geração e Redução de Cenários
A incerteza conjunta de radiação solar, consumo de fundo e preços de energia é tratada por meio de amostragem de dados históricos e subsequente redução ótima de cenários utilizando o algoritmo baseado na **Distância de Kantorovich (Wasserstein)** implementado em `generate_scenarios.py`.

---

## 📁 Estrutura do Repositório

```text
Smart-eManager/
├── .gitignore                           # Exclusões de arquivos de compilação, logs e venvs
├── README.md                            # Guia completo e documentação técnica do sistema
├── requirements.txt                     # Dependências Python para a estação de otimização (PC)
├── requirements-rpi.txt                 # Dependências específicas para a Raspberry Pi (GPIO)
│
├── prosumer-stochastic-model/           # MÓDULO DE OTIMIZAÇÃO ESTOCÁSTICA
│   ├── ReferenceModel.py                # Modelo matemático algébrico escrito em Pyomo
│   ├── ScenarioStructure.dat            # Estrutura em árvore de cenários para o PySP
│   ├── config.json                      # Parâmetros da bateria, limites e cenários estocásticos
│   ├── generate_scenarios.py            # Geração, combinação e redução de cenários (Kantorovich)
│   ├── load_data.py                     # Carga e tratamento de perfis de rede e mercado
│   └── run_stochastic_model.py          # Script principal de resolução com CPLEX e gráficos
│
├── raspberry/                           # MÓDULO DE HARDWARE / IOT
│   └── serv2.py                         # Servidor FastAPI com controle de pinos GPIO e Mock
│
├── notebooks/                           # NOTEBOOKS INTERATIVOS
│   └── model_test_notebook.ipynb        # Workflow interativo: otimização, gráficos e envio HTTP
│
└── data/                                # DADOS E RESULTADOS
    └── cargas_status.json               # Matriz de despacho resultante exportada para a Raspberry
```

---

## 🔌 Mapeamento de Cargas e Hardware

Na Raspberry Pi, cada carga é controlada através de pinos GPIO no padrão **BCM** (*Broadcom pinout*). Abaixo consta a tabela de especificações técnicas das cargas residenciais modeladas:

| Carga Residencial | Potência ($kW$) | Duração ($h$) | Intervalos ($15\text{ min}$) | Janela Permitida | Horário Desejado | Pino GPIO (BCM) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Máquina de Lavar** | 0.60 | 2.0 | 8 | 02:00 às 18:00 | 08:00 | **GPIO 17** |
| **Forno Elétrico** | 1.50 | 1.0 | 4 | 10:00 às 16:00 | 12:00 | **GPIO 18** |
| **Aquecedor** | 4.00 | 0.25 | 1 | 05:00 às 07:00 | 06:00 | **GPIO 27** |
| **Lavadora de Pratos** | 0.30 | 1.0 | 4 | 18:00 às 23:00 | 21:00 | **GPIO 22** |
| **Ar Condicionado 1** | 1.50 | 3.0 | 12 | 10:00 às 20:00 | 16:00 | **GPIO 23** |
| **Ar Condicionado 2** | 2.00 | 5.0 | 20 | 08:00 às 23:00 | 17:00 | **GPIO 24** |
| **Ar Condicionado 3** | 1.50 | 8.0 | 32 | 02:00 às 20:00 | 02:00 | **GPIO 25** |
| **Robô Aspirador** | 1.00 | 3.0 | 12 | 01:00 às 22:00 | 18:00 | **GPIO 5** |

> [!NOTE]
> Cada intervalo de tempo de 15 minutos da otimização pode ser acelerado na Raspberry Pi (por padrão, 15 segundos em `serv2.py`) para permitir demonstrações laboratoriais rápidas e inspeção visual da sequência de acionamentos.

---

## 💻 Pré-requisitos e Dependências

### No PC (Estação de Cálculo):
* **Python 3.10 ou superior**
* **IBM ILOG CPLEX Optimization Studio** (versões 12.10, 20.1 ou 22.1 recomendadas com suporte ao Python)
  * *Alternativamente, Pyomo suporta outros solvers MILP como CBC ou GLPK, mas a biblioteca PySP foi homologada prioritariamente com CPLEX.*

### Na Raspberry Pi:
* Raspberry Pi 3, 4, 5 ou Raspberry Pi Zero 2W com Raspberry Pi OS (Linux).
* Circuito de LEDs: 8x LEDs (cores variadas), 8x resistores limitadores (330 $\Omega$ a 1 $k\Omega$), protoboard e jumpers macho-fêmea.

---

## 🚀 Guia de Instalação

### 1. Clonando o Repositório
```bash
git clone https://github.com/rafaelsmoura29/Smart-eManager.git
cd Smart-eManager
```

### 2. Configuração no PC (Otimização)
```bash
# Criação do ambiente virtual
python -m venv venv

# Ativação do ambiente
# No Linux/macOS:
source venv/bin/activate
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# No Windows (CMD):
.\venv\Scripts\activate.bat

# Instalação dos pacotes
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configuração na Raspberry Pi (Execução Física)
Na Raspberry Pi conectada à mesma rede local:
```bash
cd Smart-eManager
python3 -m venv venv-rpi
source venv-rpi/bin/activate

# Instalação dos pacotes de hardware e servidor
pip install -r requirements-rpi.txt
```

---

## 🕹️ Como Utilizar

### Passo 1: Iniciar o Servidor na Raspberry Pi
No terminal da Raspberry Pi (ou no PC para testes em modo mock):
```bash
cd raspberry
uvicorn serv2:app --host 0.0.0.0 --port 8000
```
Ao iniciar, o terminal confirmará:
```text
INFO: smart-emanager-server: Modo Raspberry Pi detectado: RPi.GPIO carregado com sucesso.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```
*(Se executado em um PC com Windows/Mac, o servidor detectará a ausência do hardware e ativará automaticamente o **Modo de Simulação / Mock GPIO**, permitindo testar a API sem erros).*

### Passo 2: Executar a Otimização e Transmitir os Resultados

#### Opção A — Via Jupyter Notebook (Recomendado para Análise):
Abra o notebook interativo:
```bash
jupyter notebook notebooks/model_test_notebook.ipynb
```
1. Configure o IP da sua Raspberry Pi na variável `url` (ex: `http://192.168.1.50:8000/atualizar_cargas`).
2. Execute as células para:
   * Resolver o modelo estocástico;
   * Gerar os gráficos de perfil de carga e evolução do SoC da bateria;
   * Exportar `data/cargas_status.json`;
   * Enviar automaticamente o despacho via HTTP POST para a Raspberry Pi.

#### Opção B — Via Script Direto (Terminal):
```bash
cd prosumer-stochastic-model
python run_stochastic_model.py
```
O script resolverá o modelo via CPLEX, exibirá os gráficos de análise de sensibilidade e salvará o arquivo `cargas_status.json` dentro do diretório `data/`.

---

## 📡 Documentação da API (Servidor Raspberry)

O servidor `serv2.py` disponibiliza endpoints assíncronos de controle:

### `GET /`
Verifica a integridade e estado do servidor.
* **Resposta (200 OK):**
```json
{
  "status": "online",
  "sistema": "Smart-eManager Raspberry Pi Controller",
  "modo_rpi": true,
  "cargas_mapeadas": [
    "MaquinaDeLavar",
    "FornoEletrico",
    "Aquecedor",
    "LavadoraDePratos",
    "ArCondicionado1",
    "ArCondicionado2",
    "ArCondicionado3",
    "RoboAspirador"
  ]
}
```

### `POST /atualizar_cargas`
Recebe o cronograma de 96 passos para cada aparelho e inicia o controle físico dos LEDs.
* **Headers:** `Content-Type: application/json`
* **Payload Exemplo:**
```json
{
  "MaquinaDeLavar": [0, 0, 0, 0, 1, 1, 1, 1, 0, ...],
  "FornoEletrico": [0, 0, 0, 0, 0, 0, 0, 0, 0, ...],
  "Aquecedor": [0, 0, 0, 0, 0, 0, 0, 0, 0, ...],
  "LavadoraDePratos": [0, 0, 0, 0, 0, 0, 0, 0, 0, ...],
  "ArCondicionado1": [0, 0, 0, 0, 0, 0, 0, 0, 0, ...],
  "ArCondicionado2": [0, 0, 0, 0, 0, 0, 0, 0, 0, ...],
  "ArCondicionado3": [0, 0, 0, 0, 0, 0, 0, 0, 0, ...],
  "RoboAspirador": [0, 0, 0, 0, 0, 0, 0, 0, 0, ...]
}
```
* **Resposta (200 OK):**
```json
{
  "mensagem": "📥 JSON recebido com sucesso. Iniciando controle de cargas."
}
```

---

## 📊 Exemplos de Saídas e Gráficos

Durante a execução da otimização, o `Smart-eManager` plota curvas operacionais incluindo:
1. **Despacho Energético Global:** Potência comprada/vendida no mercado Spot vs Mercado Bilateral.
2. **Estado de Carga da Bateria ($SoC$):** Ciclos de carga nos momentos de preço baixo/geração excedente e descarga nos momentos de pico de preço.
3. **Curva de Demanda Total:** Agregação das cargas deslocadas com a demanda essencial.
4. **Função Objetivo Acumulada:** Custo operacional financeiro consolidado ao longo do dia.

---

## 📖 Citação Acadêmica

Se você utilizar este código, modelo ou metodologia em sua pesquisa, por favor cite o trabalho:

```bibtex
@misc{moura2025smartemanager,
  author       = {Rafael dos Santos Moura and Lucas Silveira Melo},
  title        = {Smart-eManager: Gerenciamento Energético de Prosumidores com Programação Estocástica e Validação Hardware-in-the-Loop},
  year         = {2025},
  institution  = {Universidade Federal do Ceará (UFC)},
  note         = {Grupo de Redes Elétricas Inteligentes (GREI - UFC)},
  url          = {https://github.com/rafaelsmoura29/Smart-eManager}
}
```

---

## 👨‍💻 Autoria e Agradecimentos

* **Autor:** Rafael dos Santos Moura ([GitHub](https://github.com/rafaelsmoura29))
* **Orientação:** Prof. Dr. Lucas Silveira Melo
* **Laboratório:** [GREI - Grupo de Redes Elétricas Inteligentes](http://www.grei.ufc.br/) | Departamento de Engenharia Elétrica | Universidade Federal do Ceará (UFC)

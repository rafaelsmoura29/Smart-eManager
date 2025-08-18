# ⚡ Smart-eManager

O **Smart-eManager** é um sistema de **gerenciamento de recursos energéticos** baseado em **Programação Matemática Estocástica** e comunicação com **Raspberry Pi**.  

Ele integra **otimização de cargas** (via Pyomo/CPLEX) com **automação residencial**, permitindo que decisões de despacho de cargas sejam calculadas no **PC** e executadas fisicamente em uma **Raspberry Pi**, que controla LEDs (simulando cargas reais).

---

## 🚀 Funcionalidades
- 🧮 **Otimização com Pyomo/CPLEX** → geração de despacho ótimo das cargas em 96 intervalos (15 minutos cada).
- 📦 **Exportação para JSON** → os resultados da otimização são exportados para um arquivo `cargas_status.json`.
- 📡 **Envio para Raspberry Pi** → o arquivo JSON é enviado via HTTP para o servidor rodando na Raspberry.
- 💡 **Controle de cargas (LEDs)** → a Raspberry interpreta o JSON e liga/desliga LEDs que simulam as cargas.
- 🔄 **Comando manual** → além do envio da otimização, é possível modificar estados das cargas manualmente via API.

---

## 🛠️ Estrutura do Projeto
Smart-eManager/
│── prosumer-stochastic-model/
│ ├── run_stochastic_model.py # Código de otimização
│ ├── ReferenceModel.py # Modelo Pyomo
│ ├── load_data.py # Leitura de dados
│ ├── generate_scenarios.py # Geração de cenários
│ ├── config.json # Arquivo de configuração
│ └── ScenarioStructure.dat # Estrutura de cenários
│
│── raspberry/
│ ├── serv2.py # Servidor FastAPI para controlar GPIOs
│
│── notebooks/
│ └── model_test_notebook.ipynb # Executa otimização e envia JSON para Raspberry
│
│── requirements.txt # Dependências do projeto
│── README.md # Este arquivo


---

## ⚙️ Instalação

### 🔹 No PC (otimização)
1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/Smart-eManager.git
   cd Smart-eManager
2. Crie o ambiente virtual e instale dependências:
python -m venv ambiente
source ambiente/bin/activate   # Linux
ambiente\Scripts\activate      # Windows
pip install -r requirements.txt
3. Instale o IBM ILOG CPLEX Optimization Studio (necessário para resolver o modelo).

### 🔹 Na Raspberry (execução)
1. Clone o repositório também na Raspberry.
2. Ative o ambiente e instale as dependências:
pip install -r requirements.txt
3. Execute o servidor:
uvicorn serv2:app --host 0.0.0.0 --port 8000
Se tudo estiver certo, aparecerá no terminal:
✅ Servidor rodando em http://0.0.0.0:8000

## 🖥️ Fluxo de Operação
1. PC executa a otimização no model_test_notebook.ipynb.
2. Os resultados (despacho das cargas) são exportados para cargas_status.json.
3. O notebook envia o JSON para a Raspberry Pi:
📡 Requisição enviada.
✅ Resposta do servidor: 200
4. Raspberry Pi lê o JSON e liga/desliga os LEDs correspondentes:
LED 8 → Máquina de Lavar
LED 9 → Forno Elétrico
LED 10 → Aquecedor

<img width="1589" height="1011" alt="image" src="https://github.com/user-attachments/assets/bd5e1acb-e3b8-43af-b2be-7816e3768a88" />


## 🔮 Melhorias Futuras
 Permitir que o usuário edite manualmente o JSON antes do envio.
 Suporte para mais cargas e diferentes pinos GPIO.
 Integração com sensores reais de energia.
 Dashboard web para visualização do estado das cargas em tempo real.

## 👨‍💻 Autores
Projeto desenvolvido no GREI - UFC.
Orientador: Lucas Silveira Melo
Aluno: [Rafael dos Santos Moura]

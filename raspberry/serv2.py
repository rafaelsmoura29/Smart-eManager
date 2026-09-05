from fastapi import FastAPI, Request
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart-emanager-server")

# Tratamento para execução em Raspberry Pi ou em modo simulação (PC/Windows/Mac)
try:
    import RPi.GPIO as GPIO
    IS_RPI = True
    logger.info("Modo Raspberry Pi detectado: RPi.GPIO carregado com sucesso.")
except (ImportError, RuntimeError):
    IS_RPI = False
    logger.warning("RPi.GPIO não disponível. Executando em modo de SIMULAÇÃO (Mock GPIO).")

    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        HIGH = 1
        LOW = 0

        @staticmethod
        def setmode(mode):
            pass

        @staticmethod
        def setup(pin, mode):
            pass

        @staticmethod
        def output(pin, val):
            pass

    GPIO = MockGPIO()

app = FastAPI(
    title="Smart-eManager - Raspberry Pi Controller",
    description="Servidor de controle de cargas via GPIO para simulação física em LEDs",
    version="1.0.0"
)

# Mapeamento entre nomes de cargas e pinos dos LEDs
MAPEAMENTO_CARGAS = {
	"MaquinaDeLavar": 17,
	"FornoEletrico": 18,
	"Aquecedor": 27,
	"LavadoraDePratos": 22,
	"ArCondicionado1": 23,
	"ArCondicionado2": 24,
	"ArCondicionado3": 25,
	"RoboAspirador": 5 
}

# Configuração dos pinos GPIO
GPIO.setmode(GPIO.BCM)
for pino in MAPEAMENTO_CARGAS.values():
    GPIO.setup(pino, GPIO.OUT)
    GPIO.output(pino, GPIO.LOW)

@app.get("/")
async def status_servidor():
    return {
        "status": "online",
        "sistema": "Smart-eManager Raspberry Pi Controller",
        "modo_rpi": IS_RPI,
        "cargas_mapeadas": list(MAPEAMENTO_CARGAS.keys())
    }


# Função para aplicar os estados das cargas com intervalo de 15 minutos (simulado como 15 segundos para testes)
async def controlar_leds_por_intervalo(dados):
    total_intervalos = len(next(iter(dados.values())))
    for t in range(total_intervalos):
        print(f"\n⏱️ Intervalo {t}")
        for carga, estados in dados.items():
            if carga in MAPEAMENTO_CARGAS:
                estado = estados[t]
                pino = MAPEAMENTO_CARGAS[carga]
                GPIO.output(pino, GPIO.HIGH if estado == 1 else GPIO.LOW)
                print(f"  🔄 {carga} -> {'Ligado' if estado == 1 else 'Desligado'} (PINO {pino})")
        await asyncio.sleep(15)  # 15 segundos para simular 15 minutos

@app.post("/atualizar_cargas")
async def atualizar_cargas(request: Request):
    try:
        dados = await request.json()

        if not isinstance(dados, dict):
            return {"erro": "Formato inválido. Esperado dicionário JSON."}

        # Inicia o controle assíncrono dos LEDs baseado nos dados recebidos
        asyncio.create_task(controlar_leds_por_intervalo(dados))

        return {"mensagem": "📥 JSON recebido com sucesso. Iniciando controle de cargas."}
    except Exception as e:
        return {"erro": f"Erro ao processar JSON: {e}"}

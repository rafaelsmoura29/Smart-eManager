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


# Função para aplicar os estados das cargas com intervalo de 15 minutos (simulado por padrão como 15 segundos)
async def controlar_leds_por_intervalo(dados, delay_segundos=15):
    total_intervalos = len(next(iter(dados.values())))
    for t in range(total_intervalos):
        logger.info(f"--- [Intervalo {t:02d} / {total_intervalos}] ---")
        for carga, estados in dados.items():
            if carga in MAPEAMENTO_CARGAS:
                estado = estados[t] if t < len(estados) else 0
                pino = MAPEAMENTO_CARGAS[carga]
                GPIO.output(pino, GPIO.HIGH if estado == 1 else GPIO.LOW)
                status_str = "LIGADO (ON)" if estado == 1 else "DESLIGADO (OFF)"
                logger.info(f"  -> {carga:18s} : {status_str} [GPIO {pino}]")
        await asyncio.sleep(delay_segundos)

@app.post("/atualizar_cargas")
async def atualizar_cargas(request: Request, delay: float = 15.0):
    try:
        dados = await request.json()

        if not isinstance(dados, dict):
            return {"erro": "Formato inválido. Esperado dicionário JSON."}

        # Inicia o controle assíncrono dos LEDs baseado nos dados recebidos
        asyncio.create_task(controlar_leds_por_intervalo(dados, delay_segundos=delay))

        return {
            "status": "sucesso",
            "mensagem": "JSON recebido com sucesso. Iniciando controle de cargas.",
            "total_cargas": len(dados),
            "delay_intervalo_s": delay
        }
    except Exception as e:
        logger.error(f"Erro ao processar JSON: {e}")
        return {"erro": f"Erro ao processar JSON: {e}"}


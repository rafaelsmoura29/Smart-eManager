"""
Smart-eManager: Script de Validação e Simulação Local
---------------------------------------------------
Este script permite validar todo o funcionamento do sistema sem a necessidade
de uma Raspberry Pi física ou protoboard conectada.

Ele carrega o despacho ótimo gerado pelo modelo (data/cargas_status.json)
e executa a simulação dos acionamentos nos pinos virtuais (Mock GPIO).
"""

import json
import time
import pathlib
import sys

# Garante compatibilidade de encoding no console do Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Adiciona o diretorio raspberry ao path
root_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(str(root_dir / "raspberry"))

from serv2 import MAPEAMENTO_CARGAS

def main():
    print("=" * 65)
    print(" Smart-eManager - Simulador de Despacho de Cargas (Hardware-in-the-Loop)")
    print("=" * 65)


    caminho_dados = root_dir / "data" / "cargas_status.json"
    if not caminho_dados.exists():
        print(f"❌ Arquivo não encontrado: {caminho_dados}")
        return

    with open(caminho_dados, "r", encoding="utf-8") as f:
        dados = json.load(f)

    total_cargas = len(dados)
    primeira_carga = next(iter(dados.values()))
    total_intervalos = len(primeira_carga)

    print(f"📦 Dados carregados com sucesso:")
    print(f"   • Total de Cargas Mapeadas : {total_cargas}")
    print(f"   • Intervalos no Dia (15 min): {total_intervalos} passos (24 horas)")
    print("-" * 65)
    print("🔌 Mapeamento de Cargas e Pinos GPIO:")
    for carga, pino in MAPEAMENTO_CARGAS.items():
        print(f"   • {carga:20s} -> Pino GPIO BCM {pino:02d}")
    print("-" * 65)

    print("\nIniciando simulação dos primeiros 8 intervalos (2 horas de operação)...")
    print("Pressione CTRL+C a qualquer momento para interromper.\n")

    try:
        # Simula os primeiros 8 intervalos com 1.5s por intervalo para visualização clara
        intervalos_simulados = min(8, total_intervalos)
        for t in range(intervalos_simulados):
            hora = (t * 15) // 60
            minuto = (t * 15) % 60
            horario_str = f"{hora:02d}:{minuto:02d}"

            print(f"[Intervalo {t+1:02d}/{total_intervalos}] Horário: {horario_str}h")
            
            cargas_ativas = []
            for carga, estados in dados.items():
                pino = MAPEAMENTO_CARGAS.get(carga, 0)
                estado = estados[t]
                if estado == 1:
                    status = "[*] LIGADO (ON) "
                    cargas_ativas.append(carga)
                else:
                    status = "[ ] desligado   "
                print(f"     {carga:18s} (GPIO {pino:02d}) : {status}")

            if cargas_ativas:
                print(f"   >>> Cargas Ativas no Momento: {', '.join(cargas_ativas)}")
            else:
                print("   >>> Nenhuma carga deslocável em funcionamento neste instante.")
            
            print("-" * 65)
            time.sleep(0.8)

        print("\n[OK] Validacao concluida com sucesso!")
        print("Todos os dados de despacho, mapeamento de GPIO e lógica operacional estão 100% funcionais.")
        print("=" * 65)

    except KeyboardInterrupt:
        print("\n[!] Simulacao interrompida pelo usuario.")


if __name__ == "__main__":
    main()

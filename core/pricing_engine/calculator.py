from datetime import datetime

def calcular_preco(hora: int, avaliacao: float, demandas_pendentes: int) -> float:
    multiplicador_hora = {
        0: 2.0, 6: 1.5, 12: 1.0, 18: 1.2, 22: 1.8
    }

    multiplicador = 1.0
    for h, m in sorted(multiplicador_hora.items(), reverse=True):
        if hora >= h:
            multiplicador = m
            break

    if demandas_pendentes >= 7:
        demanda_bonus = 0.2
    elif demandas_pendentes >= 4:
        demanda_bonus = 0.1
    else:
        demanda_bonus = 0.0

    preco_base = 100.0
    preco = preco_base * (1 + (avaliacao / 10)) * multiplicador * (1 + demanda_bonus)
    return round(preco, 2)

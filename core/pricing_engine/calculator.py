def obter_multiplicador_por_hora(hora: int) -> float:
    if 0 <= hora < 6:
        return 1.5
    elif 6 <= hora < 12:
        return 1.0
    elif 12 <= hora < 18:
        return 1.2
    else:
        return 1.4

def calcular_preco(hora: int, avaliacao: float, demandas_pendentes: int, detalhado: bool = False):
    multiplicador = obter_multiplicador_por_hora(hora)

    if demandas_pendentes >= 7:
        demanda_bonus = 0.2
    elif demandas_pendentes >= 4:
        demanda_bonus = 0.1
    else:
        demanda_bonus = 0.0

    preco_base = 100.0
    preco = preco_base * (1 + (avaliacao / 10)) * multiplicador * (1 + demanda_bonus)
    preco_final = round(preco, 2)

    if detalhado:
        return {
            "preco_base": preco_base,
            "avaliacao": avaliacao,
            "hora": hora,
            "multiplicador": multiplicador,
            "demanda_bonus": demanda_bonus,
            "preco_final": preco_final
        }

    return preco_final

"""Validação e cálculo de dígitos verificadores do CNPJ.

Cobre os dois formatos coexistentes a partir de 06/07/2026:

* **Numérico** (legado): 14 dígitos `[0-9]`.
* **Alfanumérico** (novo): 12 caracteres `[0-9A-Z]` + 2 dígitos verificadores
  numéricos `[0-9]`.

O algoritmo é único — módulo 11 com pesos posicionais — e usa
``ord(c) - 48`` como valor de cada caractere. Para dígitos `0–9` isso
devolve `0–9`; para letras `A–Z` devolve `17–42`. Como o caso antigo é
matematicamente um sub-caso do novo (`ord('0') - 48 == 0`), o mesmo
validador serve para os dois.

Referências:
* IN RFB nº 2.229/2024 — institui o CNPJ alfanumérico.
* NT Conjunta 2025.001 — vigência 06/07/2026 para documentos fiscais.
* PDF Serpro: cálculo do módulo 11 para o novo CNPJ.
"""

from __future__ import annotations

from cnpj_lib.formatador import normalizar

# Pesos posicionais do módulo 11. Comprimento = 12 e 13 respectivamente.
PESOS_DV1: tuple[int, ...] = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
PESOS_DV2: tuple[int, ...] = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def _valor(caractere: str) -> int:
    """Converte 1 caractere para seu valor no algoritmo CNPJ."""
    return ord(caractere) - 48


def _eh_base_valida(base: str) -> bool:
    """Confere que `base` tem 12 chars todos em `[0-9A-Z]`."""
    return len(base) == 12 and all(c.isdigit() or "A" <= c <= "Z" for c in base)


def _calc_dv(base: str, pesos: tuple[int, ...]) -> int:
    """Aplica o módulo 11 com pesos posicionais."""
    soma = sum(_valor(c) * p for c, p in zip(base, pesos, strict=True))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def calcular_dv(base12: str) -> str:
    """Calcula os dois dígitos verificadores de uma base alfanumérica de 12.

    Aceita a base com ou sem máscara, em qualquer caixa. Retorna sempre 2
    dígitos numéricos como string (ex: ``"35"``).

    Raises:
        ValueError: se a base normalizada não tiver exatamente 12 caracteres
            no alfabeto ``[0-9A-Z]``.
    """
    base = normalizar(base12)
    if not _eh_base_valida(base):
        raise ValueError(
            f"base inválida para cálculo de DV: esperado 12 chars [0-9A-Z], recebido {base!r}"
        )
    d1 = _calc_dv(base, PESOS_DV1)
    d2 = _calc_dv(base + str(d1), PESOS_DV2)
    return f"{d1}{d2}"


def validar(cnpj: str) -> bool:
    """Retorna ``True`` se o CNPJ tem formato e DVs corretos.

    Aceita CNPJ numérico (legado) ou alfanumérico (novo), com ou sem máscara,
    em qualquer caixa. Nunca lança — entrada inválida retorna ``False``.
    """
    try:
        s = normalizar(cnpj)
    except (AttributeError, TypeError):
        return False
    if len(s) != 14:
        return False
    base, dvs = s[:12], s[12:]
    if not dvs.isdigit() or not _eh_base_valida(base):
        return False
    return calcular_dv(base) == dvs


def eh_alfanumerico(cnpj: str) -> bool:
    """Retorna ``True`` se o CNPJ tem ao menos uma letra na base de 12.

    Não valida DV — só inspeciona o formato. CNPJs novos são alfanuméricos
    por definição (qualquer letra na base de 12 caracteres).
    """
    s = normalizar(cnpj)
    return len(s) >= 12 and any(c.isalpha() for c in s[:12])

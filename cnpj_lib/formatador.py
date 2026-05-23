"""Formatação, normalização e parsing de strings vindas do dataset RFB."""
from __future__ import annotations

from datetime import date


def normalizar(cnpj: str) -> str:
    """Remove tudo que não for alfanumérico e converte para maiúsculas.

    Funciona tanto para CNPJ numérico (``00.000.000/0001-91``) quanto alfa
    (``12.ABC.345/01DE-35``). Espaços, máscara e qualquer ruído são removidos.
    """
    return "".join(c for c in cnpj if c.isalnum()).upper()


def formatar(cnpj: str) -> str:
    """Aplica a máscara padrão ``XX.XXX.XXX/XXXX-DD`` a um CNPJ de 14 chars.

    Aceita entrada com ou sem máscara. Raises ``ValueError`` se o tamanho
    normalizado for diferente de 14.
    """
    s = normalizar(cnpj)
    if len(s) != 14:
        raise ValueError(f"esperado CNPJ de 14 caracteres, recebido {s!r} ({len(s)})")
    return f"{s[0:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:14]}"


def fragmentar(cnpj14: str) -> tuple[str, str, str]:
    """Quebra um CNPJ de 14 chars em ``(basico, ordem, dv)``.

    Espelha o storage do schema RFB, onde ``estabelecimentos`` mantém as três
    partes em colunas separadas (``cnpj_basico`` 8 chars, ``cnpj_ordem`` 4,
    ``cnpj_dv`` 2).
    """
    s = normalizar(cnpj14)
    if len(s) != 14:
        raise ValueError(f"esperado CNPJ de 14 caracteres, recebido {s!r} ({len(s)})")
    return s[:8], s[8:12], s[12:14]


def mascarar_cpf(cpf: str) -> str:
    """Mascara um CPF no formato RFB ``***NNNNNN**`` (6 dígitos centrais visíveis).

    Útil para conferir consistência com o valor que vem na coluna
    ``socios.cnpj_cpf_socio`` quando o sócio é PF. RFB sempre publica PF
    mascarado em dados abertos.
    """
    s = "".join(c for c in cpf if c.isdigit())
    if len(s) != 11:
        raise ValueError(f"esperado CPF de 11 dígitos, recebido {s!r} ({len(s)})")
    return f"***{s[3:9]}**"


def parsear_data_yyyymmdd(s: str | None) -> str | None:
    """Converte string ``YYYYMMDD`` (formato RFB) para ISO 8601 ``YYYY-MM-DD``.

    Retorna ``None`` para entrada vazia, ``"00000000"`` ou qualquer string que
    não represente uma data calendar-válida. Nunca lança.
    """
    if not s or s == "00000000" or len(s) != 8 or not s.isdigit():
        return None
    yyyy, mm, dd = s[:4], s[4:6], s[6:8]
    try:
        date(int(yyyy), int(mm), int(dd))
    except ValueError:
        return None
    return f"{yyyy}-{mm}-{dd}"

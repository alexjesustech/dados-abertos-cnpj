"""Tabelas de domínio fixas que não vêm como lookup no SQLite.

A RFB publica essas semânticas no PDF de Metadados do dataset, mas não
distribui como tabela CSV. Mantemos hardcoded aqui para que API e MCP
consigam expor ``{codigo, descricao}`` consistente com as 6 lookups que
vêm como CSV (``cnaes``, ``motivos``, ``municipios``, ``paises``,
``qualificacoes``, ``naturezas``).
"""

from __future__ import annotations

# Situação cadastral do estabelecimento
# Fonte: PDF Metadados RFB / NOVOLAYOUTDOSDADOSABERTOSDOCNPJ.pdf
SITUACAO_CADASTRAL: dict[str, str] = {
    "01": "NULA",
    "02": "ATIVA",
    "03": "SUSPENSA",
    "04": "INAPTA",
    "08": "BAIXADA",
}

# Tipo de sócio (coluna `socios.identificador_socio`)
# Fonte: PDF Metadados RFB
IDENTIFICADOR_SOCIO: dict[str, str] = {
    "1": "Pessoa Jurídica",
    "2": "Pessoa Física",
    "3": "Estrangeiro",
}

# Faixa etária do sócio PF (coluna `socios.faixa_etaria`)
# Fonte: PDF Metadados RFB
FAIXA_ETARIA: dict[str, str] = {
    "0": "Não se aplica",
    "1": "0 a 12 anos",
    "2": "13 a 20 anos",
    "3": "21 a 30 anos",
    "4": "31 a 40 anos",
    "5": "41 a 50 anos",
    "6": "51 a 60 anos",
    "7": "61 a 70 anos",
    "8": "71 a 80 anos",
    "9": "Maiores de 80 anos",
}

# Matriz ou Filial (coluna `estabelecimentos.identificador_matriz_filial`)
IDENTIFICADOR_MATRIZ_FILIAL: dict[str, str] = {
    "1": "Matriz",
    "2": "Filial",
}

# Optante por Simples / MEI (colunas `simples.opcao_pelo_simples`, `opcao_pelo_mei`)
OPCAO_SIMPLES: dict[str, str] = {
    "S": "Optante",
    "N": "Não optante",
}

# Porte da empresa (coluna `empresas.porte_empresa`)
# Fonte: PDF Metadados RFB
PORTE_EMPRESA: dict[str, str] = {
    "00": "Não informado",
    "01": "Micro empresa",
    "03": "Empresa de pequeno porte",
    "05": "Demais",
}

# Registry de tabelas indexadas por nome — usado pela função `descrever`
# e por endpoints/tools que aceitam o nome da tabela como parâmetro.
TABELAS: dict[str, dict[str, str]] = {
    "situacao_cadastral": SITUACAO_CADASTRAL,
    "identificador_socio": IDENTIFICADOR_SOCIO,
    "faixa_etaria": FAIXA_ETARIA,
    "identificador_matriz_filial": IDENTIFICADOR_MATRIZ_FILIAL,
    "opcao_simples": OPCAO_SIMPLES,
    "porte_empresa": PORTE_EMPRESA,
}


def descrever(tabela: str, codigo: str) -> str | None:
    """Devolve a descrição de ``codigo`` na ``tabela`` de domínio hardcoded.

    Retorna ``None`` se o código não existir na tabela. Lança ``KeyError``
    se a tabela for desconhecida (erro de programação, não de dados).
    """
    if tabela not in TABELAS:
        raise KeyError(f"tabela de domínio desconhecida: {tabela!r}")
    return TABELAS[tabela].get(codigo)

"""Fixtures compartilhadas entre tests/integracao/ e tests/mcp/.

`tmp_db_path` constrói um SQLite descartável com o DDL completo das 11
tabelas + dados sintéticos (2 empresas, 3 estabelecimentos, 5 sócios,
6 lookups, 3 entradas em controle_importacao). `cnpjs` devolve os 14
chars completos (basico + ordem + DVs calculados via cnpj_lib).

Suítes filhas (`integracao/`, `mcp/`) consomem essas fixtures
diretamente — pytest faz a injeção pela árvore de conftests.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cnpj_lib.validador import calcular_dv

DDL = """
CREATE TABLE empresas (
    cnpj_basico TEXT PRIMARY KEY,
    razao_social TEXT,
    natureza_juridica TEXT,
    qualificacao_responsavel TEXT,
    capital_social TEXT,
    porte_empresa TEXT,
    ente_federativo_responsavel TEXT
);

CREATE TABLE estabelecimentos (
    cnpj_basico TEXT,
    cnpj_ordem TEXT,
    cnpj_dv TEXT,
    identificador_matriz_filial TEXT,
    nome_fantasia TEXT,
    situacao_cadastral TEXT,
    data_situacao_cadastral TEXT,
    motivo_situacao_cadastral TEXT,
    nome_cidade_exterior TEXT,
    pais TEXT,
    data_inicio_atividade TEXT,
    cnae_fiscal_principal TEXT,
    cnae_fiscal_secundaria TEXT,
    tipo_logradouro TEXT,
    logradouro TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cep TEXT,
    uf TEXT,
    municipio TEXT,
    ddd_1 TEXT,
    telefone_1 TEXT,
    ddd_2 TEXT,
    telefone_2 TEXT,
    ddd_fax TEXT,
    fax TEXT,
    correio_eletronico TEXT,
    situacao_especial TEXT,
    data_situacao_especial TEXT,
    PRIMARY KEY (cnpj_basico, cnpj_ordem, cnpj_dv)
);

CREATE TABLE socios (
    cnpj_basico TEXT,
    identificador_socio TEXT,
    nome_socio_razao_social TEXT,
    cnpj_cpf_socio TEXT,
    qualificacao_socio TEXT,
    data_entrada_sociedade TEXT,
    pais TEXT,
    representante_legal TEXT,
    nome_do_representante TEXT,
    qualificacao_representante_legal TEXT,
    faixa_etaria TEXT
);

CREATE TABLE simples (
    cnpj_basico TEXT PRIMARY KEY,
    opcao_pelo_simples TEXT,
    data_opcao_simples TEXT,
    data_exclusao_simples TEXT,
    opcao_pelo_mei TEXT,
    data_opcao_mei TEXT,
    data_exclusao_mei TEXT
);

CREATE TABLE cnaes (codigo TEXT PRIMARY KEY, descricao TEXT);
CREATE TABLE motivos (codigo TEXT PRIMARY KEY, descricao TEXT);
CREATE TABLE municipios (codigo TEXT PRIMARY KEY, descricao TEXT);
CREATE TABLE paises (codigo TEXT PRIMARY KEY, descricao TEXT);
CREATE TABLE qualificacoes (codigo TEXT PRIMARY KEY, descricao TEXT);
CREATE TABLE naturezas (codigo TEXT PRIMARY KEY, descricao TEXT);

CREATE TABLE controle_importacao (
    arquivo TEXT PRIMARY KEY,
    status TEXT,
    data_importacao TEXT
);

CREATE INDEX idx_socios_cnpj ON socios(cnpj_basico);
CREATE INDEX idx_estab_cnpj ON estabelecimentos(cnpj_basico);
"""

BASICO_A = "11222333"
BASICO_B = "12ABC345"
ORDEM_MATRIZ_A = "0001"
ORDEM_FILIAL_A = "0002"
ORDEM_B = "01DE"
BASICO_INEXISTENTE = "99999999"


def _cnpj14(basico: str, ordem: str) -> str:
    """Monta CNPJ de 14 chars com DVs corretos a partir de basico+ordem."""
    return basico + ordem + calcular_dv(basico + ordem)


@pytest.fixture(scope="session")
def cnpjs() -> dict[str, str]:
    return {
        "matriz_a": _cnpj14(BASICO_A, ORDEM_MATRIZ_A),
        "filial_a": _cnpj14(BASICO_A, ORDEM_FILIAL_A),
        "matriz_b": _cnpj14(BASICO_B, ORDEM_B),
        "inexistente": _cnpj14(BASICO_INEXISTENTE, "0001"),
    }


@pytest.fixture(scope="session")
def tmp_db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """SQLite descartável com 2 empresas, 3 estabelecimentos, 5 sócios.

    Cenário sintético:
      * Empresa A (BASICO_A=11222333): numérica, com Simples, matriz +
        filial, 5 sócios (3 PF mascarados + 1 PJ holding + 1 estrangeiro
        com representante legal). Município RFB 7107 (Porto Velho), UF RO.
      * Empresa B (BASICO_B=12ABC345): alfanumérica (NT 2025), sem
        Simples, sem sócios, só matriz. Município 7107, UF SP.
    """
    db = tmp_path_factory.mktemp("db") / "fixture.db"
    conn = sqlite3.connect(db)
    conn.executescript(DDL)

    conn.executemany("INSERT INTO cnaes VALUES (?,?)", [
        ("6204000", "Consultoria em tecnologia da informação"),
        ("4751201", "Comércio varejista especializado de equipamentos"),
    ])
    conn.executemany("INSERT INTO motivos VALUES (?,?)", [
        ("00", "Sem motivo"),
        ("01", "Extinção por encerramento liquidação voluntária"),
    ])
    conn.executemany("INSERT INTO municipios VALUES (?,?)", [
        ("7107", "PORTO VELHO"),
        ("9999", "EXTERIOR"),
    ])
    conn.executemany("INSERT INTO paises VALUES (?,?)", [
        ("105", "BRASIL"),
        ("249", "EUA"),
    ])
    conn.executemany("INSERT INTO qualificacoes VALUES (?,?)", [
        ("05", "Administrador"),
        ("22", "Sócio"),
        ("49", "Sócio-Administrador"),
    ])
    conn.executemany("INSERT INTO naturezas VALUES (?,?)", [
        ("2062", "Sociedade Empresária Limitada"),
        ("2046", "Sociedade Anônima Aberta"),
    ])

    conn.execute(
        "INSERT INTO empresas VALUES (?,?,?,?,?,?,?)",
        (BASICO_A, "ACME LTDA", "2062", "49", "1000000,00", "03", ""),
    )
    conn.execute(
        "INSERT INTO simples VALUES (?,?,?,?,?,?,?)",
        (BASICO_A, "S", "20200101", "00000000", "N", "00000000", "00000000"),
    )
    conn.execute(
        "INSERT INTO estabelecimentos VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (BASICO_A, ORDEM_MATRIZ_A, calcular_dv(BASICO_A + ORDEM_MATRIZ_A),
         "1", "ACME SEDE", "02", "20100101", "00",
         "", "105", "20100101", "6204000", "4751201",
         "RUA", "DAS FLORES", "100", "SALA 1", "CENTRO",
         "76801000", "RO", "7107",
         "69", "999999999", "", "", "", "",
         "contato@acme.test", "", ""),
    )
    conn.execute(
        "INSERT INTO estabelecimentos VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (BASICO_A, ORDEM_FILIAL_A, calcular_dv(BASICO_A + ORDEM_FILIAL_A),
         "2", "ACME FILIAL", "02", "20150101", "00",
         "", "105", "20150101", "4751201", "",
         "AV", "BRASIL", "200", "", "JARDIM",
         "76802000", "RO", "7107",
         "", "", "", "", "", "",
         "", "", ""),
    )
    conn.executemany(
        "INSERT INTO socios VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            (BASICO_A, "2", "JOAO DA SILVA", "***123456**", "49",
             "20100101", "105", "", "", "", "5"),
            (BASICO_A, "2", "MARIA SANTOS", "***234567**", "22",
             "20100101", "105", "", "", "", "6"),
            (BASICO_A, "1", "EMPRESA HOLDING SA", "99888777000166", "22",
             "20120101", "105", "", "", "", "0"),
            (BASICO_A, "2", "PEDRO LIMA", "***345678**", "22",
             "20130101", "105", "", "", "", "7"),
            (BASICO_A, "3", "JOHN DOE", "***456789**", "22",
             "20140101", "249", "***000111**", "JOSE REPRESENTANTE", "49", "0"),
        ],
    )

    conn.execute(
        "INSERT INTO empresas VALUES (?,?,?,?,?,?,?)",
        (BASICO_B, "ALFANUM TECH", "2046", "05", "50000,5", "01", ""),
    )
    conn.execute(
        "INSERT INTO estabelecimentos VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (BASICO_B, ORDEM_B, calcular_dv(BASICO_B + ORDEM_B),
         "1", "", "02", "20240101", "00",
         "", "105", "20240101", "6204000", "",
         "RUA", "ALFA", "1", "", "BETA",
         "01000000", "SP", "7107",
         "11", "999999999", "", "", "", "",
         "alfanum@test.test", "", ""),
    )

    conn.executemany(
        "INSERT INTO controle_importacao VALUES (?,?,?)",
        [
            ("Empresas0.zip", "concluido", "2026-05-23 04:00:00"),
            ("Estabelecimentos0.zip", "concluido", "2026-05-23 04:15:00"),
            ("Socios0.zip", "concluido", "2026-05-23 04:20:00"),
        ],
    )
    conn.commit()
    conn.close()
    return db

import csv
import io
import sqlite3
import time
import zipfile
from pathlib import Path

from notifier import Notifier

TABLE_SCHEMAS = {
    "empresas": {
        "columns": [
            "cnpj_basico",
            "razao_social",
            "natureza_juridica",
            "qualificacao_responsavel",
            "capital_social",
            "porte_empresa",
            "ente_federativo_responsavel",
        ],
        "ddl": """
            CREATE TABLE IF NOT EXISTS empresas (
                cnpj_basico TEXT PRIMARY KEY,
                razao_social TEXT,
                natureza_juridica TEXT,
                qualificacao_responsavel TEXT,
                capital_social TEXT,
                porte_empresa TEXT,
                ente_federativo_responsavel TEXT
            );
        """,
    },
    "estabelecimentos": {
        "columns": [
            "cnpj_basico",
            "cnpj_ordem",
            "cnpj_dv",
            "identificador_matriz_filial",
            "nome_fantasia",
            "situacao_cadastral",
            "data_situacao_cadastral",
            "motivo_situacao_cadastral",
            "nome_cidade_exterior",
            "pais",
            "data_inicio_atividade",
            "cnae_fiscal_principal",
            "cnae_fiscal_secundaria",
            "tipo_logradouro",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cep",
            "uf",
            "municipio",
            "ddd_1",
            "telefone_1",
            "ddd_2",
            "telefone_2",
            "ddd_fax",
            "fax",
            "correio_eletronico",
            "situacao_especial",
            "data_situacao_especial",
        ],
        "ddl": """
            CREATE TABLE IF NOT EXISTS estabelecimentos (
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
        """,
    },
    "socios": {
        "columns": [
            "cnpj_basico",
            "identificador_socio",
            "nome_socio_razao_social",
            "cnpj_cpf_socio",
            "qualificacao_socio",
            "data_entrada_sociedade",
            "pais",
            "representante_legal",
            "nome_do_representante",
            "qualificacao_representante_legal",
            "faixa_etaria",
        ],
        "ddl": """
            CREATE TABLE IF NOT EXISTS socios (
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
        """,
    },
    "simples": {
        "columns": [
            "cnpj_basico",
            "opcao_pelo_simples",
            "data_opcao_simples",
            "data_exclusao_simples",
            "opcao_pelo_mei",
            "data_opcao_mei",
            "data_exclusao_mei",
        ],
        "ddl": """
            CREATE TABLE IF NOT EXISTS simples (
                cnpj_basico TEXT PRIMARY KEY,
                opcao_pelo_simples TEXT,
                data_opcao_simples TEXT,
                data_exclusao_simples TEXT,
                opcao_pelo_mei TEXT,
                data_opcao_mei TEXT,
                data_exclusao_mei TEXT
            );
        """,
    },
    "cnaes": {
        "columns": ["codigo", "descricao"],
        "ddl": "CREATE TABLE IF NOT EXISTS cnaes (codigo TEXT PRIMARY KEY, descricao TEXT);",
    },
    "motivos": {
        "columns": ["codigo", "descricao"],
        "ddl": "CREATE TABLE IF NOT EXISTS motivos (codigo TEXT PRIMARY KEY, descricao TEXT);",
    },
    "municipios": {
        "columns": ["codigo", "descricao"],
        "ddl": "CREATE TABLE IF NOT EXISTS municipios (codigo TEXT PRIMARY KEY, descricao TEXT);",
    },
    "paises": {
        "columns": ["codigo", "descricao"],
        "ddl": "CREATE TABLE IF NOT EXISTS paises (codigo TEXT PRIMARY KEY, descricao TEXT);",
    },
    "qualificacoes": {
        "columns": ["codigo", "descricao"],
        "ddl": "CREATE TABLE IF NOT EXISTS qualificacoes (codigo TEXT PRIMARY KEY, descricao TEXT);",
    },
    "naturezas": {
        "columns": ["codigo", "descricao"],
        "ddl": "CREATE TABLE IF NOT EXISTS naturezas (codigo TEXT PRIMARY KEY, descricao TEXT);",
    },
    "controle_importacao": {
        "columns": ["arquivo", "status", "data_importacao"],
        "ddl": """
            CREATE TABLE IF NOT EXISTS controle_importacao (
                arquivo TEXT PRIMARY KEY,
                status TEXT,
                data_importacao TEXT
            );
        """,
    },
}


class DatabaseManager:
    def __init__(self, db_path: str, notifier: Notifier):
        self.db_path = db_path
        self.notifier = notifier

    def init_db(self):
        self.notifier.log_and_notify(f"Inicializando o banco de dados em: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        try:
            for schema in TABLE_SCHEMAS.values():
                conn.execute(schema["ddl"])
            conn.commit()
            self.notifier.log_and_notify(
                "Tabelas do banco de dados criadas/verificadas com sucesso."
            )
        except Exception as e:
            self.notifier.log_and_notify(
                f"Erro ao inicializar tabelas do banco de dados: {e}", level=40
            )
            raise e
        finally:
            conn.close()

    def get_table_name_from_file(self, filename: str):
        name = filename.upper()
        if "EMPRE" in name:
            return "empresas"
        elif "ESTABE" in name:
            return "estabelecimentos"
        elif "SOCIOC" in name:
            return "socios"
        elif "SIMPLES" in name:
            return "simples"
        elif "CNAE" in name:
            return "cnaes"
        elif "MOTI" in name:
            return "motivos"
        elif "MUNIC" in name:
            return "municipios"
        elif "PAIS" in name:
            return "paises"
        elif "QUALS" in name:
            return "qualificacoes"
        elif "NATJU" in name:
            return "naturezas"
        return None

    def create_indices(self):
        self.notifier.log_and_notify("Criando índices para otimização de consultas...")
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_socios_cnpj ON socios(cnpj_basico);")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_estab_cnpj ON estabelecimentos(cnpj_basico);"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_estab_mun ON estabelecimentos(municipio);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_estab_uf ON estabelecimentos(uf);")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_estab_cnae ON estabelecimentos(cnae_fiscal_principal);"
            )
            conn.commit()
            self.notifier.log_and_notify("Índices criados com sucesso.")
        except Exception as e:
            self.notifier.log_and_notify(f"Erro ao criar índices: {e}", level=30)
        finally:
            conn.close()

    def import_csv_file(self, csv_path: str, chunk_size: int = 50000):
        path = Path(csv_path)
        table_name = self.get_table_name_from_file(path.name)

        if not table_name:
            self.notifier.log_and_notify(
                f"Arquivo CSV não correspondente a nenhuma tabela: {path.name}", level=30
            )
            return

        self.notifier.log_and_notify(
            f"Importando dados de {path.name} para a tabela '{table_name}'..."
        )

        schema = TABLE_SCHEMAS[table_name]
        cols = schema["columns"]
        cols_count = len(cols)

        # Build statement (INSERT OR REPLACE)
        placeholders = ", ".join(["?"] * cols_count)
        query = f"INSERT OR REPLACE INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders})"

        conn = sqlite3.connect(self.db_path)
        try:
            # Performance optimizations
            conn.execute("PRAGMA synchronous = OFF;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA cache_size = 100000;")
            conn.execute("PRAGMA temp_store = MEMORY;")

            start_time = time.time()
            total_rows = 0
            buffer = []

            # Open CSV with appropriate delimiter and encoding (latin1/iso-8859-1 is the default for RFB files)
            with open(csv_path, encoding="latin-1", errors="ignore") as f:
                reader = csv.reader(f, delimiter=";")

                for row in reader:
                    # Clean/pad the row to fit the columns count exactly
                    if len(row) < cols_count:
                        row = row + [None] * (cols_count - len(row))
                    elif len(row) > cols_count:
                        row = row[:cols_count]

                    buffer.append(row)

                    if len(buffer) >= chunk_size:
                        conn.executemany(query, buffer)
                        conn.commit()
                        total_rows += len(buffer)
                        buffer = []
                        self.notifier.log_and_notify(
                            f"[{table_name}] Ingeridos {total_rows:,} registros..."
                        )

                # Insert remaining records
                if buffer:
                    conn.executemany(query, buffer)
                    conn.commit()
                    total_rows += len(buffer)

            elapsed = time.time() - start_time
            self.notifier.log_and_notify(
                f"Tabela '{table_name}' finalizada. Ingeridos {total_rows:,} registros em {elapsed:.2f} segundos."
            )

        except Exception as e:
            self.notifier.log_and_notify(f"Erro ao importar {path.name}: {e}", level=40)
            conn.rollback()
            raise e
        finally:
            conn.close()

    def is_file_imported(self, filename: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM controle_importacao WHERE arquivo = ?", (filename,))
            row = cursor.fetchone()
            if row and row[0] == "concluido":
                return True
            return False
        except Exception as e:
            self.notifier.log_and_notify(f"Erro ao verificar controle de importação: {e}", level=30)
            return False
        finally:
            conn.close()

    def mark_file_as_imported(self, filename: str):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO controle_importacao (arquivo, status, data_importacao) VALUES (?, ?, ?)",
                (filename, "concluido", time.strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
        except Exception as e:
            self.notifier.log_and_notify(f"Erro ao registrar controle de importação: {e}", level=40)
        finally:
            conn.close()

    def import_csv_from_zip(self, zip_path: str, chunk_size: int = 50000) -> bool:
        path = Path(zip_path)
        filename = path.name

        if self.is_file_imported(filename):
            self.notifier.log_and_notify(
                f"Arquivo ZIP '{filename}' já foi importado anteriormente. Pulando."
            )
            return True

        if not zipfile.is_zipfile(zip_path):
            self.notifier.log_and_notify(f"Arquivo não é um ZIP válido: {filename}", level=40)
            return False

        self.notifier.log_and_notify(
            f"Iniciando leitura por streaming do arquivo ZIP: {filename}..."
        )

        conn = sqlite3.connect(self.db_path)
        try:
            # Otimizações globais de escrita no SQLite
            conn.execute("PRAGMA synchronous = OFF;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA cache_size = 100000;")
            conn.execute("PRAGMA temp_store = MEMORY;")

            with zipfile.ZipFile(zip_path, "r") as z:
                # Filtra apenas os arquivos internos relevantes (geralmente há 1 arquivo de dados por ZIP)
                csv_files = [
                    f
                    for f in z.namelist()
                    if not f.startswith("__MACOSX")
                    and (
                        f.endswith(".csv")
                        or any(
                            keyword in f.upper()
                            for keyword in [
                                ".EMPRE",
                                ".ESTABE",
                                ".SOCIOC",
                                ".SIMPLES",
                                ".CNAE",
                                ".MOTI",
                                ".MUNIC",
                                ".PAIS",
                                ".QUALS",
                                ".NATJU",
                            ]
                        )
                    )
                ]

                if not csv_files:
                    self.notifier.log_and_notify(
                        f"Nenhum arquivo de dados correspondente encontrado dentro do ZIP: {filename}",
                        level=30,
                    )
                    return False

                for csv_internal_name in csv_files:
                    table_name = self.get_table_name_from_file(csv_internal_name)
                    if not table_name:
                        self.notifier.log_and_notify(
                            f"Arquivo interno {csv_internal_name} não corresponde a nenhuma tabela mapeada. Pulando.",
                            level=30,
                        )
                        continue

                    self.notifier.log_and_notify(
                        f"Importando {csv_internal_name} (dentro de {filename}) para a tabela '{table_name}'..."
                    )

                    schema = TABLE_SCHEMAS[table_name]
                    cols = schema["columns"]
                    cols_count = len(cols)

                    # Constrói o statement INSERT OR REPLACE para garantir idempotência em re-execuções parciais
                    placeholders = ", ".join(["?"] * cols_count)
                    query = f"INSERT OR REPLACE INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders})"

                    start_time = time.time()
                    total_rows = 0
                    buffer = []

                    # Abre o arquivo compactado em modo binário de leitura
                    with z.open(csv_internal_name, "r") as f_bytes:
                        # Envolve com io.TextIOWrapper para converter o stream de bytes em strings com codificação ISO-8859-1 (latin-1)
                        f_text = io.TextIOWrapper(f_bytes, encoding="latin-1", errors="ignore")
                        reader = csv.reader(f_text, delimiter=";")

                        for row in reader:
                            # Trata linhas menores ou maiores que a definição de colunas da tabela
                            if len(row) < cols_count:
                                row = row + [None] * (cols_count - len(row))
                            elif len(row) > cols_count:
                                row = row[:cols_count]

                            buffer.append(row)

                            if len(buffer) >= chunk_size:
                                conn.executemany(query, buffer)
                                conn.commit()
                                total_rows += len(buffer)
                                buffer = []
                                self.notifier.log_and_notify(
                                    f"[{table_name}] Ingeridos {total_rows:,} registros..."
                                )

                        # Insere o buffer remanescente
                        if buffer:
                            conn.executemany(query, buffer)
                            conn.commit()
                            total_rows += len(buffer)

                    elapsed = time.time() - start_time
                    self.notifier.log_and_notify(
                        f"Tabela '{table_name}' finalizada. Ingeridos {total_rows:,} registros em {elapsed:.2f} segundos."
                    )

            # Registra a importação bem sucedida na tabela de controle
            self.mark_file_as_imported(filename)
            return True

        except Exception as e:
            self.notifier.log_and_notify(
                f"Erro ao processar streaming do ZIP {filename}: {e}", level=40
            )
            conn.rollback()
            raise e
        finally:
            conn.close()

-- Índices adicionais exigidos pela API/MCP do Caminho 01.
--
-- Por que: a tabela `socios` (27M linhas) não tem PK declarada nem índice
-- em `cnpj_cpf_socio`. As tools `vinculos_pj` (busca por CPF/CNPJ de sócio)
-- e `listar_socios` (paginação por cnpj_basico + tipo) viram table-scan
-- sem isso.
--
-- Idempotente — `IF NOT EXISTS` deixa rodar quantas vezes precisar.
-- Custo: minutos contra os 30 GB de produção. Rode fora de janela de
-- ingestão (writer + index-build no mesmo banco brigam).
--
-- Aplicar:
--   sqlite3 dados_cnpj.db < migrations/add_indices_post_sprint_zero.sql
--
-- Esses índices devem migrar para `database.py::create_indices()` na
-- próxima rodada de manutenção do pipeline.

-- Sprint 02/03 — repos e tools MCP precisam dessas queries:
CREATE INDEX IF NOT EXISTS idx_socios_basico_id
    ON socios (cnpj_basico, identificador_socio);

CREATE INDEX IF NOT EXISTS idx_socios_documento
    ON socios (cnpj_cpf_socio);

-- Sprint 03 — cnaes_por_municipio é GROUP BY que sem este índice
-- escaneia todos os estabelecimentos do município (~70s em Brasília).
CREATE INDEX IF NOT EXISTS idx_estab_municipio_cnae
    ON estabelecimentos (municipio, cnae_fiscal_principal);

-- Sprint 03 — empresas_por_cnae com filtro de UF (3s em "bancos no DF"
-- sem este índice).
CREATE INDEX IF NOT EXISTS idx_estab_cnae_uf
    ON estabelecimentos (cnae_fiscal_principal, uf);

-- Estatísticas atualizadas para o query planner — também resolve /stats
-- lento ao popular sqlite_stat1.
ANALYZE empresas;
ANALYZE estabelecimentos;
ANALYZE socios;
ANALYZE simples;

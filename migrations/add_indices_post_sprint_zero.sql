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

CREATE INDEX IF NOT EXISTS idx_socios_basico_id
    ON socios (cnpj_basico, identificador_socio);

CREATE INDEX IF NOT EXISTS idx_socios_documento
    ON socios (cnpj_cpf_socio);

ANALYZE socios;

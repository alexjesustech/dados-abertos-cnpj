> Fonte canônica: seção "Segredos" de `AGENTS.md` (raiz do projeto).
> Este arquivo é carregado automaticamente pelo Claude Code e contém apenas
> detalhes operacionais específicos do Claude. A regra de negócio/projeto é o AGENTS.md.

- Comandos que leem envs devem ser prefixados por `bin/with-env`.
- Migrado para SOPS + age; nunca editar `.env.sops.yaml` diretamente.
- O `.env` plaintext legado não existe mais, use o wrapper.
- Não versionar o webhook do Discord ou o token do Telegram.

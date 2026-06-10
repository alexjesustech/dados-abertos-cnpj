> Fonte canônica: seção "Convenções de código" de `AGENTS.md` (raiz do projeto).
> Este arquivo é carregado automaticamente pelo Claude Code e contém apenas
> detalhes operacionais específicos do Claude. A regra de negócio/projeto é o AGENTS.md.

- PEP 8 + regras de `.pylintrc`. Comentários só onde o porquê não for óbvio.
- Sem `print()` direto em código de produção — usar sempre `Notifier.log_and_notify(message, level=logging.INFO|WARNING|ERROR)`; cuida de log em arquivo + Discord/Telegram opcionais.
- Path resolution via `pathlib.Path`, nunca `os.path.join`.
- Strings de log em pt-BR (segue a política global do workspace).

# manual-analyzer

Hand-written DFA lexer for "BuildScript" — a Portuguese academic language for hardware assembly scenarios. Zero external dependencies (stdlib only). Python 3.8+.

## Entrypoints

- `main_manual.py` — CLI runner with 3 hardcoded test cases (valid code, invalid var `$1a`, invalid symbol `@`); **does NOT accept file path arguments** (README is outdated on this)
- `server_manual.py` — HTTP server on port **8001** (not 8000, despite README), serves `index_manual.html` IDE and `/run_manual` POST JSON API

## Commands

```bash
python main_manual.py       # run 3 built-in test cases
python server_manual.py     # start web IDE at http://localhost:8001
```

No install step, no virtualenv, no lockfile. No test framework, no linter, no typechecker.

## BuildScript language quirks

- Programs must start with `POWER_ON;` and end with `POWER_OFF;` (enforced inside the lexer itself)
- Variables: `$` followed by lowercase+underscore, max 30 chars (`$pente_um`)
- Function identifiers: `!` followed by letter+alnum, max 30 chars (`!cadastrar_peca`)
- Numbers: max 15 digits, supports decimal (`.`); trailing letters after digits are errors
- Strings: double-quoted, support `\\` escapes, must close before newline/EOF
- Comments: `//` line comments only
- Keywords: `POWER_ON`, `POWER_OFF`, `SLOT`, `VOLTAGE`, `LABEL`, `LED`, `GREENSCREEN`, `BLUESCREEN`, `RUNCIRCUIT`, `SHORTCIRCUIT`, `RUNCOOLER`, `STOPCOOLER`, `CPU`, `EJECT`, `MONITOR`, `KEYBOARD`, `AND`, `OR`, `NOT`
- Brace matching is validated during tokenization (`_check_braces`)

## Files

| File | Role |
|---|---|
| `lexer_manual.py` | `ManualLexer` class, tokenizer DFA, `LexerError` exception |
| `parser_manual.py` | `ManualParser` class, recursive descent parser, `ParserError` exception |
| `main_manual.py` | Hardcoded test runner (6 tests: 3 lexer, 3 parser) |
| `server_manual.py` | HTTP API server + `ManualIDEHandler` |
| `index_manual.html` | Single-page IDE frontend |
| `builds/exemplo{1-5}.bs` | Sample BuildScript sources |

import sys
from lexer_manual import ManualLexer
from parser_manual import ManualParser

TOKEN_NAMES_PT = {
    'PROG_INIT': 'InicioPrograma',
    'PROG_END': 'FimPrograma',
    'TYPE_VAR': 'TipoVariavel',
    'VAL_BOOL': 'ValorBooleano',
    'COND_IF': 'SeCondicional',
    'COND_ELSE': 'SenaoCondicional',
    'LOOP_INIT': 'InicioLoop',
    'LOOP_END': 'FimLoop',
    'FUNC_DEF': 'DefinicaoFuncao',
    'KW_RETURN': 'RetornoFuncao',
    'IO_OUT': 'SaidaDados',
    'IO_IN': 'EntradaDados',
    'ID_FUNC': 'IdentificadorFuncao',
    'VAR': 'Variavel',
    'NUMBER': 'Numero',
    'STRING': 'CadeiaCaracteres',
    'OP_UNARIO': 'OperadorUnario',
    'OP_COMP': 'OperadorComparacao',
    'OP_ATRIB': 'OperadorAtribuicao',
    'OP_LOGICO': 'OperadorLogico',
    'OP_ARIT': 'OperadorAritmetico',
    'LBRACE': 'AbreChaves',
    'RBRACE': 'FechaChaves',
    'LPAREN': 'AbreParenteses',
    'RPAREN': 'FechaParenteses',
    'COMMA': 'Virgula',
    'SEMICOLON': 'PontoVirgula',
    'ID': 'Identificador',
}


def format_tokens(tokens: list[dict]) -> str:
    formatted = []
    for t in tokens:
        if t['token'] == 'EOF':
            continue
        pt_name = TOKEN_NAMES_PT.get(t['token'], t['token'])
        formatted.append(f"Linha: {t['line']} - Coluna {t['col']} - Token:<{pt_name}, {t['valor']}>")
    return "\n".join(formatted)


def _exibe_erros(errors: list[dict]):
    if not errors:
        print("✅ Nenhum erro encontrado.")
        return
    for e in errors:
        label = e.get('tipo', 'erro').capitalize()
        print(f"  ❌ {label}: {e['mensagem']}")


def _analisa(label: str, code: str) -> list[dict]:
    print(f"\n[{label}]:")
    print("----------------------------------------------------------------------")
    print(code)
    print("----------------------------------------------------------------------")
    lexer = ManualLexer(code)
    tokens = lexer.tokenize()
    tokens_str = format_tokens(tokens)
    print(tokens_str if tokens_str else "(sem tokens)")
    parser = ManualParser(tokens)
    parser.parse()
    return lexer.errors + parser.errors


def main():
    print("=" * 70)
    print("           EXECUTANDO TESTE DO ANALISADOR LÉXICO MANUAL")
    print("=" * 70)

    errors = _analisa(
        "TESTE 1 — Código BuildScript válido",
        """POWER_ON;
SLOT $pente_um = 8;
MONITOR("Memoria instalada: ", $pente_um, " GB");
POWER_OFF;"""
    )
    _exibe_erros(errors)

    errors = _analisa(
        "TESTE 2 — Erro léxico ($1a mal formado)",
        """POWER_ON;
SLOT $1a = 8;
POWER_OFF;"""
    )
    _exibe_erros(errors)

    errors = _analisa(
        "TESTE 3 — Símbolo inválido (@)",
        """POWER_ON;
SLOT $x = 10 @;
POWER_OFF;"""
    )
    _exibe_erros(errors)

    errors = _analisa(
        "TESTE 4 — Sintaxe válida",
        """POWER_ON;
CPU !teste() {
    SLOT $x = 10;
    MONITOR("Valor: ", $x);
}
!teste();
POWER_OFF;"""
    )
    _exibe_erros(errors)

    errors = _analisa(
        "TESTE 5 — Múltiplos erros (léxicos + sintáticos)",
        """POWER_ON;
$err1 = ;;
MONITOR("teste";
$1invalido = 5;
POWER_OFF;"""
    )
    _exibe_erros(errors)

    errors = _analisa(
        "TESTE 6 — Erro sintático (faltando STOPCOOLER)",
        """POWER_ON;
RUNCOOLER (SLOT $i = 0; $i < 5; $i++) {

}
POWER_OFF;"""
    )
    _exibe_erros(errors)

    print("\n" + "=" * 70)
    print("                       VERIFICAÇÃO CONCLUÍDA")
    print("=" * 70)


if __name__ == "__main__":
    main()

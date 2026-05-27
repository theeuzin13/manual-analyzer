import sys
from lexer_manual import ManualLexer, LexerError

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


def main():
    print("======================================================================")
    print("           💻 EXECUTANDO TESTE DO ANALISADOR LÉXICO MANUAL 💻         ")
    print("======================================================================")
    
    
    code_ok = """POWER_ON;
SLOT $pente_um = 8;
MONITOR("Memoria instalada: ", $pente_um, " GB");
POWER_OFF;"""

    print("\n[TESTE 1] Executando código BuildScript válido:")
    print("----------------------------------------------------------------------")
    print(code_ok)
    print("----------------------------------------------------------------------")
    try:
        lexer = ManualLexer(code_ok)
        tokens = lexer.tokenize()
        print("Tabela de Tokens Gerada com Sucesso:")
        print(format_tokens(tokens))
    except LexerError as e:
        print(f"Erro Léxico Inesperado: {e}")

    
    code_error = """POWER_ON;
SLOT $1a = 8;
POWER_OFF;"""

    print("\n[TESTE 2] Executando código com Erro Léxico ($1a - mal formado):")
    print("----------------------------------------------------------------------")
    print(code_error)
    print("----------------------------------------------------------------------")
    try:
        lexer = ManualLexer(code_error)
        tokens = lexer.tokenize()
        print(format_tokens(tokens))
    except LexerError as e:
        print("✅ Erro Léxico Detectado pelo Autômato:")
        print(f"Mensagem: {e}")

    
    code_error_symbol = """POWER_ON;
SLOT $x = 10 @;
POWER_OFF;"""

    print("\n[TESTE 3] Executando código com símbolo inválido (@):")
    print("----------------------------------------------------------------------")
    print(code_error_symbol)
    print("----------------------------------------------------------------------")
    try:
        lexer = ManualLexer(code_error_symbol)
        tokens = lexer.tokenize()
        print(format_tokens(tokens))
    except LexerError as e:
        print("✅ Erro Léxico Detectado pelo Autômato:")
        print(f"Mensagem: {e}")

    print("\n======================================================================")
    print("                       VERIFICAÇÃO CONCLUÍDA                         ")
    print("======================================================================")


if __name__ == "__main__":
    main()

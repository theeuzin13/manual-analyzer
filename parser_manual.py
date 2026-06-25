STMT_START_KEYWORDS = {
    'CPU', 'RUNCIRCUIT', 'RUNCOOLER',
    'SLOT', 'VOLTAGE', 'LED', 'LABEL',
    'MONITOR', 'EJECT',
}
STMT_START_TOKENS = {'KEYWORD': STMT_START_KEYWORDS, 'ID_FUNC': None, 'ID': None}


def _is_sync(tok):
    if tok is None or tok['token'] == 'EOF':
        return True
    if tok['token'] == 'KEYWORD':
        return tok['valor'] in STMT_START_KEYWORDS or tok['valor'] in ('POWER_ON', 'POWER_OFF', 'SHORTCIRCUIT', 'STOPCOOLER')
    if tok['token'] in ('RBRACE', 'LBRACE'):
        return True
    if tok['token'] == 'ID_FUNC':
        return True
    if tok['token'] == 'ID':
        return True
    return False


class ManualParser:
    def __init__(self, tokens: list[dict]):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def _peek(self) -> dict | None:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self) -> dict | None:
        if self.pos >= len(self.tokens):
            return None
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _check(self, token_type: str, valor: str | None = None) -> bool:
        tok = self._peek()
        if tok is None or tok['token'] == 'EOF':
            return False
        if tok['token'] != token_type:
            return False
        if valor is not None and tok['valor'] != valor:
            return False
        return True

    def _erro(self, line: int, col: int, msg: str):
        self.errors.append({
            'tipo': 'sintatico',
            'linha': line,
            'coluna': col,
            'mensagem': f"Erro Sintático [Linha {line}, Coluna {col}]: {msg}",
        })

    def _erro_eof(self, msg: str):
        tok = self.tokens[-2] if len(self.tokens) >= 2 else self.tokens[-1] if self.tokens else None
        line = tok['line'] if tok else 0
        col = tok['col'] if tok else 0
        self.errors.append({
            'tipo': 'sintatico',
            'linha': line,
            'coluna': col,
            'mensagem': f"Erro Sintático [Linha {line}, Coluna {col}]: {msg}",
        })

    def _sync_past_semicolon(self):
        while self._peek() is not None and self._peek()['token'] != 'EOF':
            tok = self._peek()
            if tok['token'] == 'SEMICOLON':
                self._advance()
                return
            if tok['token'] == 'RBRACE':
                return
            if tok['token'] == 'KEYWORD' and tok['valor'] in ('POWER_OFF', 'STOPCOOLER', 'SHORTCIRCUIT'):
                return
            self._advance()

    def _sync_to_stmt_start(self):
        while self._peek() is not None and self._peek()['token'] != 'EOF':
            if _is_sync(self._peek()):
                return
            self._advance()

    def _expect(self, token_type: str, valor: str | None = None) -> dict | None:
        tok = self._peek()
        if tok is None or tok['token'] == 'EOF':
            expected = f"'{valor}'" if valor else token_type
            self._erro_eof(f"Esperado {expected}, encontrado fim do arquivo.")
            return None
        if tok['token'] != token_type:
            self._erro(
                tok['line'], tok['col'],
                f"Esperado {token_type}, encontrado '{tok['valor']}'."
            )
            self._advance()
            return None
        if valor is not None and tok['valor'] != valor:
            self._erro(
                tok['line'], tok['col'],
                f"Esperado '{valor}', encontrado '{tok['valor']}'."
            )
            self._advance()
            return None
        return self._advance()

    def parse(self) -> list[dict]:
        self.errors = []
        self._parse_program()
        tok = self._peek()
        if tok is not None and tok['token'] != 'EOF':
            self._erro(
                tok['line'], tok['col'],
                f"Tokens inesperados após o fim do programa: '{tok['valor']}'."
            )
        return self.errors

    # ---- Program structure ----

    def _parse_program(self):
        # POWER_ON; / POWER_OFF; validation is handled by lexer's _check_structure
        # Parser only validates statement/expression syntax inside the body
        if self._check('KEYWORD', 'POWER_ON'):
            self._advance()
            if self._check('SEMICOLON', ';'):
                self._advance()

        while self._peek() is not None and self._peek()['token'] != 'EOF' and not (
            self._check('KEYWORD', 'POWER_OFF')
        ):
            self._parse_statement()

        if self._check('KEYWORD', 'POWER_OFF'):
            self._advance()
            if self._check('SEMICOLON', ';'):
                self._advance()

    # ---- Statements ----

    def _parse_statement(self):
        tok = self._peek()
        if tok is None or tok['token'] == 'EOF':
            return

        if tok['token'] == 'KEYWORD':
            if tok['valor'] == 'CPU':
                self._parse_function_def()
            elif tok['valor'] == 'RUNCIRCUIT':
                self._parse_if_stmt()
            elif tok['valor'] == 'RUNCOOLER':
                self._parse_for_stmt()
            elif tok['valor'] in ('SLOT', 'VOLTAGE', 'LED', 'LABEL'):
                self._parse_declaration()
            elif tok['valor'] == 'MONITOR':
                self._parse_monitor_stmt()
            elif tok['valor'] == 'EJECT':
                self._parse_eject_stmt()
            else:
                self._erro(
                    tok['line'], tok['col'],
                    f"Token inesperado '{tok['valor']}'."
                )
                self._advance()
        elif tok['token'] == 'ID_FUNC':
            self._parse_function_call()
        elif tok['token'] == 'ID':
            self._parse_assignment()
        else:
            self._erro(
                tok['line'], tok['col'],
                f"Token inesperado '{tok['valor']}' ({tok['token']})."
            )
            self._advance()

    def _parse_function_def(self):
        self._expect('KEYWORD', 'CPU')
        self._expect('ID_FUNC')
        self._expect('LPAREN', '(')
        if not self._check('RPAREN', ')'):
            self._parse_params()
        self._expect('RPAREN', ')')
        self._expect('LBRACE', '{')
        while self._peek() is not None and not (
            self._check('RBRACE', '}') or self._check('KEYWORD', 'POWER_OFF') or self._check('EOF', None)
        ):
            self._parse_statement()
        self._expect('RBRACE', '}')

    def _parse_params(self):
        self._parse_param()
        while self._check('COMMA', ','):
            self._advance()
            self._parse_param()

    def _parse_param(self):
        tok = self._peek()
        if tok is None or tok['token'] != 'KEYWORD' or tok['valor'] not in ('SLOT', 'VOLTAGE', 'LED', 'LABEL'):
            self._erro(
                tok['line'] if tok else 0, tok['col'] if tok else 0,
                f"Esperado tipo do parâmetro (SLOT, VOLTAGE, LED, LABEL), "
                f"encontrado '{tok['valor'] if tok else 'EOF'}'."
            )
            if tok is not None and tok['token'] != 'EOF':
                self._advance()
            return
        self._advance()
        self._expect('ID')

    def _parse_function_call(self):
        self._expect('ID_FUNC')
        self._expect('LPAREN', '(')
        if not self._check('RPAREN', ')'):
            self._parse_args()
        self._expect('RPAREN', ')')
        self._expect('SEMICOLON', ';')

    def _parse_args(self):
        self._parse_expression()
        while self._check('COMMA', ','):
            self._advance()
            self._parse_expression()

    def _parse_declaration(self):
        self._expect('KEYWORD')
        self._expect('ID')
        if self._check('OP_ATRIB'):
            self._advance()
            self._parse_expression()
        self._expect('SEMICOLON', ';')

    def _parse_assignment(self):
        self._expect('ID')
        if not self._check('OP_ATRIB'):
            tok = self._peek()
            self._erro(
                tok['line'] if tok else 0, tok['col'] if tok else 0,
                f"Esperado operador de atribuição, encontrado '{tok['valor'] if tok else 'EOF'}'."
            )
            self._sync_past_semicolon()
            return
        self._advance()
        self._parse_expression()
        self._expect('SEMICOLON', ';')

    def _parse_if_stmt(self):
        self._expect('KEYWORD', 'RUNCIRCUIT')
        self._expect('LPAREN', '(')
        self._parse_expression()
        self._expect('RPAREN', ')')
        self._expect('LBRACE', '{')
        while self._peek() is not None and not (
            self._check('RBRACE', '}') or self._check('KEYWORD', 'SHORTCIRCUIT')
            or self._check('KEYWORD', 'POWER_OFF') or self._check('EOF', None)
        ):
            self._parse_statement()
        self._expect('RBRACE', '}')
        if self._check('KEYWORD', 'SHORTCIRCUIT'):
            self._advance()
            self._expect('LBRACE', '{')
            while self._peek() is not None and not (
                self._check('RBRACE', '}') or self._check('KEYWORD', 'POWER_OFF') or self._check('EOF', None)
            ):
                self._parse_statement()
            self._expect('RBRACE', '}')

    def _parse_for_stmt(self):
        self._expect('KEYWORD', 'RUNCOOLER')
        self._expect('LPAREN', '(')
        self._parse_for_init()
        tok = self._peek()
        if tok is not None and tok['token'] != 'SEMICOLON' and tok['token'] != 'EOF':
            self._erro(
                tok['line'], tok['col'],
                f"Esperado ';' na inicialização do loop, encontrado '{tok['valor']}'."
            )
            self._sync_past_semicolon()
        else:
            self._expect('SEMICOLON', ';')
        self._parse_expression()
        tok = self._peek()
        if tok is not None and tok['token'] != 'SEMICOLON' and tok['token'] != 'EOF' and not self._check('RPAREN', ')'):
            self._erro(
                tok['line'], tok['col'],
                f"Esperado ';' na condição do loop, encontrado '{tok['valor']}'."
            )
            self._sync_past_semicolon()
        else:
            self._expect('SEMICOLON', ';')
        self._parse_for_update()
        self._expect('RPAREN', ')')
        self._expect('LBRACE', '{')
        while self._peek() is not None and not (
            self._check('RBRACE', '}') or self._check('KEYWORD', 'STOPCOOLER')
            or self._check('KEYWORD', 'POWER_OFF') or self._check('EOF', None)
        ):
            self._parse_statement()
        self._expect('RBRACE', '}')
        if self._check('KEYWORD', 'STOPCOOLER'):
            self._advance()
            self._expect('SEMICOLON', ';')
        else:
            tok = self._peek()
            if tok is not None and tok['token'] != 'EOF':
                self._erro(
                    tok['line'], tok['col'],
                    f"Esperado 'STOPCOOLER', encontrado '{tok['valor']}'."
                )
                self._sync_past_semicolon()

    def _parse_for_init(self):
        tok = self._peek()
        if tok is None:
            self._erro_eof("Esperado inicializador do loop.")
            return
        if tok['token'] == 'KEYWORD' and tok['valor'] in ('SLOT', 'VOLTAGE', 'LED', 'LABEL'):
            self._advance()
            self._expect('ID')
            if self._check('OP_ATRIB'):
                self._advance()
                self._parse_expression()
        elif tok['token'] == 'ID':
            self._advance()
            if self._check('OP_ATRIB'):
                self._advance()
                self._parse_expression()
            else:
                self._erro(
                    tok['line'], tok['col'],
                    "Esperado operador de atribuição na inicialização do loop."
                )
        else:
            self._erro(
                tok['line'], tok['col'],
                f"Esperado inicializador do loop (declaração ou atribuição), "
                f"encontrado '{tok['valor']}'."
            )
            self._advance()

    def _parse_for_update(self):
        tok = self._peek()
        if tok is None or tok['token'] != 'ID':
            self._erro(
                tok['line'] if tok else 0, tok['col'] if tok else 0,
                f"Esperado identificador na atualização do loop, "
                f"encontrado '{tok['valor'] if tok else 'EOF'}'."
            )
            if tok is not None and tok['token'] != 'EOF':
                self._advance()
            return
        self._advance()
        if self._check('OP_ATRIB'):
            self._advance()
            self._parse_expression()
        elif self._check('OP_ARIT'):
            op = self._peek()
            if op['valor'] in ('++', '--'):
                self._advance()
            else:
                self._erro(
                    op['line'], op['col'],
                    f"Esperado '++' ou '--' na atualização do loop, "
                    f"encontrado '{op['valor']}'."
                )
                self._advance()
        else:
            tok = self._peek()
            self._erro(
                tok['line'] if tok else 0, tok['col'] if tok else 0,
                "Esperado operador de atribuição ou '++'/'--' na atualização do loop."
            )

    def _parse_monitor_stmt(self):
        self._expect('KEYWORD', 'MONITOR')
        self._expect('LPAREN', '(')
        if not self._check('RPAREN', ')'):
            self._parse_args()
        if self._expect('RPAREN', ')') is None:
            self._sync_past_semicolon()
            return
        self._expect('SEMICOLON', ';')

    def _parse_eject_stmt(self):
        self._expect('KEYWORD', 'EJECT')
        self._parse_expression()
        self._expect('SEMICOLON', ';')

    # ---- Expression parsing (precedence climbing) ----

    def _parse_expression(self):
        self._parse_logical_or()

    def _parse_logical_or(self):
        self._parse_logical_and()
        while self._check('KEYWORD', 'OR'):
            self._advance()
            self._parse_logical_and()

    def _parse_logical_and(self):
        self._parse_comparison()
        while self._check('KEYWORD', 'AND'):
            self._advance()
            self._parse_comparison()

    def _parse_comparison(self):
        self._parse_addition()
        while self._check('OP_COMP'):
            self._advance()
            self._parse_addition()

    def _parse_addition(self):
        self._parse_term()
        while self._peek() is not None and self._peek()['token'] == 'OP_ARIT' and self._peek()['valor'] in ('+', '-'):
            self._advance()
            self._parse_term()

    def _parse_term(self):
        self._parse_unary()
        while self._peek() is not None and self._peek()['token'] == 'OP_ARIT' and self._peek()['valor'] in ('*', '/'):
            self._advance()
            self._parse_unary()

    def _parse_unary(self):
        tok = self._peek()
        if tok is None:
            self._erro_eof("Expressão incompleta.")
            return
        if tok['token'] == 'OP_COMP' and tok['valor'] == '!':
            self._advance()
            self._parse_unary()
        elif tok['token'] == 'OP_ARIT' and tok['valor'] == '-':
            self._advance()
            self._parse_unary()
        elif tok['token'] == 'KEYWORD' and tok['valor'] == 'NOT':
            self._advance()
            self._parse_unary()
        else:
            self._parse_primary()

    def _parse_primary(self):
        tok = self._peek()
        if tok is None:
            self._erro_eof("Expressão incompleta.")
            return

        if tok['token'] == 'NUMBER':
            self._advance()
        elif tok['token'] == 'STRING':
            self._advance()
        elif tok['token'] == 'ID':
            self._advance()
        elif tok['token'] == 'ID_FUNC':
            self._advance()
            self._expect('LPAREN', '(')
            if not self._check('RPAREN', ')'):
                self._parse_args()
            self._expect('RPAREN', ')')
        elif tok['token'] == 'KEYWORD' and tok['valor'] in ('GREENSCREEN', 'BLUESCREEN'):
            self._advance()
        elif tok['token'] == 'KEYWORD' and tok['valor'] == 'KEYBOARD':
            self._advance()
            self._expect('LPAREN', '(')
            self._expect('RPAREN', ')')
        elif tok['token'] == 'LPAREN':
            self._advance()
            self._parse_expression()
            self._expect('RPAREN', ')')
        else:
            self._erro(
                tok['line'], tok['col'],
                f"Expressão inválida: token inesperado '{tok['valor']}'."
            )
            self._advance()

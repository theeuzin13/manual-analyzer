class LexerError(Exception):
    pass


KEYWORDS = {
    'POWER_ON', 'POWER_OFF',
    'SLOT', 'VOLTAGE', 'LABEL', 'LED',
    'GREENSCREEN', 'BLUESCREEN',
    'RUNCIRCUIT', 'SHORTCIRCUIT',
    'RUNCOOLER', 'STOPCOOLER',
    'CPU', 'EJECT',
    'MONITOR', 'KEYBOARD',
    'AND', 'OR', 'NOT',
}

TOKEN_NAMES_PT = {
    'KEYWORD':    'PalavraReservada',
    'ID':         'Identificador',
    'ID_FUNC':    'Identificador',
    'NUMBER':     'Numero',
    'STRING':     'CadeiaCaracteres',
    'OP_ATRIB':   'OperadorAtribuicao',
    'OP_COMP':    'OperadorComparacao',
    'OP_ARIT':    'OperadorAritmetico',
    'LPAREN':     'AbreParenteses',
    'RPAREN':     'FechaParenteses',
    'LBRACE':     'AbreChaves',
    'RBRACE':     'FechaChaves',
    'COMMA':      'Virgula',
    'SEMICOLON':  'PontoVirgula',
}

MAX_ID_LEN  = 30
MAX_NUM_LEN = 15


class ManualLexer:
    def __init__(self, code: str):
        self.code   = code
        self.pos    = 0
        self.line   = 1
        self.col    = 1

    def _peek(self) -> str | None:
        if self.pos < len(self.code):
            return self.code[self.pos]
        return None

    def _peek2(self) -> str | None:
        if self.pos + 1 < len(self.code):
            return self.code[self.pos + 1]
        return None

    def _advance(self) -> str | None:
        if self.pos >= len(self.code):
            return None
        ch = self.code[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _is_letter(self, ch: str) -> bool:
        return ch.isalpha() or ch == '_'

    def _is_alnum(self, ch: str) -> bool:
        return ch.isalnum() or ch == '_'

    def tokenize(self) -> list[dict]:
        tokens = []

        while True:
            ch = self._peek()

            if ch is None:
                break

            if ch in (' ', '\t', '\r', '\n'):
                self._advance()
                continue

            if ch == '/' and self._peek2() == '/':
                self._advance()
                self._advance()
                while self._peek() is not None and self._peek() != '\n':
                    self._advance()
                continue

            if ch == '"':
                tok = self._read_string()
                tokens.append(tok)
                continue

            if ch == '$':
                tok = self._read_variable()
                tokens.append(tok)
                continue

            if ch == '!':
                tok = self._read_id_func()
                tokens.append(tok)
                continue

            if ch.isdigit():
                tok = self._read_number()
                tokens.append(tok)
                continue

            if self._is_letter(ch):
                tok = self._read_identifier()
                tokens.append(tok)
                continue

            start_line, start_col = self.line, self.col

            if ch == '=':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(self._tok('OP_COMP', '==', start_line, start_col))
                else:
                    tokens.append(self._tok('OP_ATRIB', '=', start_line, start_col))
                continue

            if ch == '!':
                self._advance()
                tokens.append(self._tok('OP_COMP', '!', start_line, start_col))
                continue

            if ch == '<':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(self._tok('OP_COMP', '<=', start_line, start_col))
                else:
                    tokens.append(self._tok('OP_COMP', '<', start_line, start_col))
                continue

            if ch == '>':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(self._tok('OP_COMP', '>=', start_line, start_col))
                else:
                    tokens.append(self._tok('OP_COMP', '>', start_line, start_col))
                continue

            if ch == '!':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(self._tok('OP_COMP', '!=', start_line, start_col))
                continue

            if ch == '+':
                self._advance()
                if self._peek() == '+':
                    self._advance()
                    tokens.append(self._tok('OP_ARIT', '++', start_line, start_col))
                elif self._peek() == '=':
                    self._advance()
                    tokens.append(self._tok('OP_ATRIB', '+=', start_line, start_col))
                else:
                    tokens.append(self._tok('OP_ARIT', '+', start_line, start_col))
                continue

            if ch == '-':
                self._advance()
                if self._peek() == '-':
                    self._advance()
                    tokens.append(self._tok('OP_ARIT', '--', start_line, start_col))
                elif self._peek() == '=':
                    self._advance()
                    tokens.append(self._tok('OP_ATRIB', '-=', start_line, start_col))
                else:
                    tokens.append(self._tok('OP_ARIT', '-', start_line, start_col))
                continue

            if ch == '*':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(self._tok('OP_ATRIB', '*=', start_line, start_col))
                else:
                    tokens.append(self._tok('OP_ARIT', '*', start_line, start_col))
                continue

            if ch == '/':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(self._tok('OP_ATRIB', '/=', start_line, start_col))
                else:
                    tokens.append(self._tok('OP_ARIT', '/', start_line, start_col))
                continue

            if ch == '(':
                self._advance()
                tokens.append(self._tok('LPAREN', '(', start_line, start_col))
                continue
            if ch == ')':
                self._advance()
                tokens.append(self._tok('RPAREN', ')', start_line, start_col))
                continue
            if ch == '{':
                self._advance()
                tokens.append(self._tok('LBRACE', '{', start_line, start_col))
                continue
            if ch == '}':
                self._advance()
                tokens.append(self._tok('RBRACE', '}', start_line, start_col))
                continue
            if ch == ',':
                self._advance()
                tokens.append(self._tok('COMMA', ',', start_line, start_col))
                continue
            if ch == ';':
                self._advance()
                tokens.append(self._tok('SEMICOLON', ';', start_line, start_col))
                continue

            self._advance()
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Símbolo não pertencente ao conjunto de símbolos terminais da linguagem: '{ch}'"
            )

        self._check_braces(tokens)
        self._check_structure(tokens)

        tokens.append({'token': 'EOF', 'valor': '', 'line': self.line, 'col': self.col})
        return tokens

    def _read_string(self) -> dict:
        start_line, start_col = self.line, self.col
        self._advance()
        buffer = '"'

        while True:
            ch = self._peek()
            if ch is None:
                raise LexerError(
                    f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                    f"Fim de arquivo inesperado — cadeia de caracteres não fechada: {buffer}"
                )
            if ch == '\n':
                raise LexerError(
                    f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                    f"Cadeia de caracteres mal formada (não fechada antes da quebra de linha): {buffer}"
                )
            if ch == '\\':
                buffer += self._advance()
                esc = self._peek()
                if esc is not None:
                    buffer += self._advance()
                continue
            if ch == '"':
                buffer += self._advance()
                break

            buffer += self._advance()

        return self._tok('STRING', buffer, start_line, start_col)

    def _read_variable(self) -> dict:
        start_line, start_col = self.line, self.col
        self._advance()
        buffer = ''

        ch = self._peek()
        if ch is None or not (ch.islower() or ch == '_'):
            mal = '$'
            while self._peek() is not None and self._is_alnum(self._peek()):
                mal += self._advance()
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Identificador/variável mal formado: '{mal}'"
            )

        while self._peek() is not None and self._is_alnum(self._peek()):
            buffer += self._advance()

        if len(buffer) > MAX_ID_LEN:
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Tamanho do identificador '${buffer}' excede o limite de {MAX_ID_LEN} caracteres."
            )

        return self._tok('ID', f'${buffer}', start_line, start_col)

    def _read_id_func(self) -> dict:
        start_line, start_col = self.line, self.col
        self._advance()
        buffer = ''

        ch = self._peek()
        if ch is None or not self._is_letter(ch):
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Identificador de função mal formado após '!'"
            )

        while self._peek() is not None and self._is_alnum(self._peek()):
            buffer += self._advance()

        if len(buffer) > MAX_ID_LEN:
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Tamanho do identificador '!{buffer}' excede o limite de {MAX_ID_LEN} caracteres."
            )

        return self._tok('ID_FUNC', f'!{buffer}', start_line, start_col)

    def _read_number(self) -> dict:
        start_line, start_col = self.line, self.col
        buffer = ''

        while self._peek() is not None and self._peek().isdigit():
            buffer += self._advance()

        if self._peek() == '.':
            buffer += self._advance()
            ch = self._peek()
            if ch is None or not ch.isdigit():
                mal = buffer
                while self._peek() is not None and (self._peek().isalnum() or self._peek() in '._'):
                    mal += self._advance()
                raise LexerError(
                    f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                    f"Número mal formado: '{mal}'"
                )
            while self._peek() is not None and self._peek().isdigit():
                buffer += self._advance()

        if self._peek() is not None and self._is_letter(self._peek()):
            mal = buffer
            while self._peek() is not None and self._is_alnum(self._peek()):
                mal += self._advance()
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Identificador/número mal formado: '{mal}'"
            )

        if len(buffer) > MAX_NUM_LEN:
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Tamanho excessivo do número '{buffer}' (máximo de {MAX_NUM_LEN} dígitos)."
            )

        return self._tok('NUMBER', buffer, start_line, start_col)

    def _read_identifier(self) -> dict:
        start_line, start_col = self.line, self.col
        buffer = ''

        while self._peek() is not None and self._is_alnum(self._peek()):
            buffer += self._advance()

        if buffer in KEYWORDS:
            return self._tok('KEYWORD', buffer, start_line, start_col)
        return self._tok('ID', buffer, start_line, start_col)

    @staticmethod
    def _check_braces(tokens: list[dict]):
        depth = 0
        last_open = None
        for t in tokens:
            if t['token'] == 'LBRACE':
                depth += 1
                if depth == 1:
                    last_open = t
            elif t['token'] == 'RBRACE':
                if depth == 0:
                    raise LexerError(
                        f"Erro Léxico [Linha {t['line']}, Coluna {t['col']}]: "
                        f"Bloco '}}' encontrado sem '{{' correspondente."
                    )
                depth -= 1
        if depth > 0 and last_open is not None:
            raise LexerError(
                f"Erro Léxico [Linha {last_open['line']}, Coluna {last_open['col']}]: "
                f"Fim de arquivo inesperado — bloco '{{' aberto não foi fechado com '}}'."
            )

    @staticmethod
    def _check_structure(tokens: list[dict]):
        """Valida que o programa começa com POWER_ON; e termina com POWER_OFF;"""
        # Filtra tokens relevantes (ignora comentários e espaços já ignorados)
        meaningful = [t for t in tokens if t['token'] != 'EOF']

        if not meaningful:
            raise LexerError(
                "Erro Estrutural: O programa está vazio. "
                "Todo programa BuildScript deve começar com 'POWER_ON;' e terminar com 'POWER_OFF;'."
            )

        # Verifica POWER_ON no início
        first = meaningful[0]
        if not (first['token'] == 'KEYWORD' and first['valor'] == 'POWER_ON'):
            raise LexerError(
                f"Erro Estrutural [Linha {first['line']}, Coluna {first['col']}]: "
                f"O programa deve começar obrigatoriamente com 'POWER_ON;'. "
                f"Token encontrado: '{first['valor']}'"
            )

        # Verifica que POWER_ON é seguido de ';'
        if len(meaningful) < 2 or not (meaningful[1]['token'] == 'SEMICOLON'):
            raise LexerError(
                f"Erro Estrutural [Linha {first['line']}, Coluna {first['col']}]: "
                f"'POWER_ON' deve ser seguido de ponto-e-vírgula ';'."
            )

        # Verifica POWER_OFF no final
        last = meaningful[-1]
        if not (last['token'] == 'SEMICOLON'):
            raise LexerError(
                f"Erro Estrutural [Linha {last['line']}, Coluna {last['col']}]: "
                f"O programa deve terminar com 'POWER_OFF;'. "
                f"Último token encontrado: '{last['valor']}'"
            )

        # Encontra o penúltimo token para verificar POWER_OFF
        second_last = meaningful[-2] if len(meaningful) >= 2 else None
        if second_last is None or not (second_last['token'] == 'KEYWORD' and second_last['valor'] == 'POWER_OFF'):
            found = second_last['valor'] if second_last else '(nenhum)'
            raise LexerError(
                f"Erro Estrutural [Linha {last['line']}, Coluna {last['col']}]: "
                f"O programa deve terminar obrigatoriamente com 'POWER_OFF;'. "
                f"Token encontrado antes do ';' final: '{found}'"
            )

    @staticmethod
    def _tok(kind: str, value: str, line: int, col: int) -> dict:
        return {'token': kind, 'valor': value, 'line': line, 'col': col}

    @staticmethod
    def format_tokens(tokens: list[dict]) -> str:
        lines = []
        for t in tokens:
            if t['token'] == 'EOF':
                continue
            name = TOKEN_NAMES_PT.get(t['token'], t['token'])
            lines.append(f"Linha: {t['line']} - Coluna {t['col']} - Token:<{name}, {t['valor']}>")
        return '\n'.join(lines)

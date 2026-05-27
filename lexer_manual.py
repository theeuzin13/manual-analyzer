"""
Analisador Léxico MANUAL - BuildScript (Tabela de Tokens Reduzida)
===================================================================
IMPLEMENTAÇÃO MANUAL: Nenhuma biblioteca de expressão regular (re) é usada.
O reconhecimento de cada token é feito caractere por caractere, simulando
um Autômato Finito Determinístico (DFA) implementado com while, if/elif/else.

Tabela de Tokens Reduzida:
---------------------------------------------------------------------------
| Token              | Lexema(s) de Exemplo      | Descrição              |
|--------------------|-----------------------------|------------------------|
| PalavraReservada   | POWER_ON, SLOT, CPU, ...    | Palavras-chave         |
| Identificador      | cpu_count, fan_speed        | Nome de variável/func  |
| Numero             | 8, 3.14, 650                | Literal numérico       |
| CadeiaCaracteres   | "hello world"               | Literal de texto       |
| OperadorAtribuicao | =, +=, -=, *=, /=          | Atribuição             |
| OperadorComparacao | ==, !=, >=, <=, >, <        | Comparação             |
| OperadorAritmetico | +, -, *, /                  | Aritmética             |
| AbreParenteses     | (                           | Abre parênteses        |
| FechaParenteses    | )                           | Fecha parênteses       |
| AbreChaves         | {                           | Abre bloco             |
| FechaChaves        | }                           | Fecha bloco            |
| Virgula            | ,                           | Separador              |
| PontoVirgula       | ;                           | Fim de instrução       |
---------------------------------------------------------------------------

Erros Léxicos Detectados (sem contexto semântico):
  - Símbolo inválido (@, %, #, ...)
  - Variável/identificador mal formado (iniciando com dígito: 1abc)
  - Tamanho de identificador excedido (> 30 caracteres)
  - Número mal formado (2.a3, 2.#)
  - Tamanho excessivo de número (> 15 dígitos)
  - String não fechada ("hello world sem aspas de fechamento)
  - Bloco de chaves não fechado (detectado via balanço de LBRACE/RBRACE)
"""


class LexerError(Exception):
    pass


# ─── Conjunto de palavras reservadas (chaves terminais) da linguagem ──────────
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

# ─── Mapeamento de tokens para nomes em português (formato professor) ─────────
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

MAX_ID_LEN  = 30   # Tamanho máximo de identificador/variável (excluindo prefixo)
MAX_NUM_LEN = 15   # Tamanho máximo de um número (em dígitos/caracteres)


class ManualLexer:
    """
    Analisador Léxico Manual — BuildScript.

    Itera por cada caractere da fonte usando ponteiro (self.pos) e
    reconhece os tokens através de transições de estado explícitas em
    if/elif/else e while — sem nenhum módulo externo.
    """

    def __init__(self, code: str):
        self.code   = code        # Código-fonte completo como string
        self.pos    = 0           # Posição atual no código (ponteiro do autômato)
        self.line   = 1           # Linha atual (para mensagens de erro)
        self.col    = 1           # Coluna atual (para mensagens de erro)

    # ── Helpers de leitura ───────────────────────────────────────────────────

    def _peek(self) -> str | None:
        """Retorna o caractere atual SEM avançar o ponteiro (lookahead)."""
        if self.pos < len(self.code):
            return self.code[self.pos]
        return None

    def _peek2(self) -> str | None:
        """Retorna o próximo caractere (pos+1) sem avançar o ponteiro."""
        if self.pos + 1 < len(self.code):
            return self.code[self.pos + 1]
        return None

    def _advance(self) -> str | None:
        """Consome o caractere atual e avança o ponteiro."""
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

    # ── Tokenizador principal (loop do autômato) ─────────────────────────────

    def tokenize(self) -> list[dict]:
        tokens = []

        while True:
            ch = self._peek()

            # ── Fim do arquivo ────────────────────────────────────────────────
            if ch is None:
                break

            # ── Estado: Ignorar espaços em branco e quebras de linha ──────────
            if ch in (' ', '\t', '\r', '\n'):
                self._advance()
                continue

            # ── Estado: Comentário de linha (//) ─────────────────────────────
            if ch == '/' and self._peek2() == '/':
                # Consome os dois traços '//'
                self._advance()
                self._advance()
                # Consome tudo até o fim da linha
                while self._peek() is not None and self._peek() != '\n':
                    self._advance()
                continue

            # ── Estado: String "..." ──────────────────────────────────────────
            if ch == '"':
                tok = self._read_string()
                tokens.append(tok)
                continue

            # ── Estado: Variável com prefixo $ (ex: $pente_um) ───────────────
            if ch == '$':
                tok = self._read_variable()
                tokens.append(tok)
                continue

            # ── Estado: Chamada de função com prefixo ! (ex: !calcular) ───────
            if ch == '!':
                tok = self._read_id_func()
                tokens.append(tok)
                continue

            # ── Estado: Número (inteiro ou decimal) ───────────────────────────
            if ch.isdigit():
                tok = self._read_number()
                tokens.append(tok)
                continue

            # ── Estado: Identificador ou Palavra Reservada ────────────────────
            if self._is_letter(ch):
                tok = self._read_identifier()
                tokens.append(tok)
                continue

            # ── Estado: Operadores e Pontuação ────────────────────────────────
            start_line, start_col = self.line, self.col

            if ch == '=':
                self._advance()
                if self._peek() == '=':             # ==
                    self._advance()
                    tokens.append(self._tok('OP_COMP', '==', start_line, start_col))
                else:                               # =
                    tokens.append(self._tok('OP_ATRIB', '=', start_line, start_col))
                continue

            if ch == '!':
                # Já tratado acima, mas por segurança:
                self._advance()
                tokens.append(self._tok('OP_COMP', '!', start_line, start_col))
                continue

            if ch == '<':
                self._advance()
                if self._peek() == '=':             # <=
                    self._advance()
                    tokens.append(self._tok('OP_COMP', '<=', start_line, start_col))
                else:                               # <
                    tokens.append(self._tok('OP_COMP', '<', start_line, start_col))
                continue

            if ch == '>':
                self._advance()
                if self._peek() == '=':             # >=
                    self._advance()
                    tokens.append(self._tok('OP_COMP', '>=', start_line, start_col))
                else:                               # >
                    tokens.append(self._tok('OP_COMP', '>', start_line, start_col))
                continue

            if ch == '!':
                self._advance()
                if self._peek() == '=':             # !=
                    self._advance()
                    tokens.append(self._tok('OP_COMP', '!=', start_line, start_col))
                continue

            if ch == '+':
                self._advance()
                if self._peek() == '+':             # ++
                    self._advance()
                    tokens.append(self._tok('OP_ARIT', '++', start_line, start_col))
                elif self._peek() == '=':           # +=
                    self._advance()
                    tokens.append(self._tok('OP_ATRIB', '+=', start_line, start_col))
                else:                               # +
                    tokens.append(self._tok('OP_ARIT', '+', start_line, start_col))
                continue

            if ch == '-':
                self._advance()
                if self._peek() == '-':             # --
                    self._advance()
                    tokens.append(self._tok('OP_ARIT', '--', start_line, start_col))
                elif self._peek() == '=':           # -=
                    self._advance()
                    tokens.append(self._tok('OP_ATRIB', '-=', start_line, start_col))
                else:                               # -
                    tokens.append(self._tok('OP_ARIT', '-', start_line, start_col))
                continue

            if ch == '*':
                self._advance()
                if self._peek() == '=':             # *=
                    self._advance()
                    tokens.append(self._tok('OP_ATRIB', '*=', start_line, start_col))
                else:                               # *
                    tokens.append(self._tok('OP_ARIT', '*', start_line, start_col))
                continue

            if ch == '/':
                self._advance()
                if self._peek() == '=':             # /=
                    self._advance()
                    tokens.append(self._tok('OP_ATRIB', '/=', start_line, start_col))
                else:                               # /
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

            # ── Erro: Símbolo inválido (não pertence ao alfabeto da linguagem) ─
            self._advance()
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Símbolo não pertencente ao conjunto de símbolos terminais da linguagem: '{ch}'"
            )

        # Verificação de blocos abertos (chaves desbalanceadas)
        self._check_braces(tokens)

        tokens.append({'token': 'EOF', 'valor': '', 'line': self.line, 'col': self.col})
        return tokens

    # ── Leitores de Tokens Específicos ───────────────────────────────────────

    def _read_string(self) -> dict:
        """Estado: dentro de uma string literal — reconhece até o fechamento de aspas."""
        start_line, start_col = self.line, self.col
        self._advance()  # Consome '"' de abertura
        buffer = '"'

        while True:
            ch = self._peek()

            # Fim de arquivo sem fechar string
            if ch is None:
                raise LexerError(
                    f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                    f"Fim de arquivo inesperado — cadeia de caracteres não fechada: {buffer}"
                )
            # Quebra de linha sem fechar string
            if ch == '\n':
                raise LexerError(
                    f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                    f"Cadeia de caracteres mal formada (não fechada antes da quebra de linha): {buffer}"
                )
            # Escape dentro da string (\n, \t, \", \\)
            if ch == '\\':
                buffer += self._advance()           # Consome '\'
                esc = self._peek()
                if esc is not None:
                    buffer += self._advance()       # Consome o caractere escapado
                continue
            # Aspas de fechamento — fim do estado de string
            if ch == '"':
                buffer += self._advance()
                break

            buffer += self._advance()

        return self._tok('STRING', buffer, start_line, start_col)

    def _read_variable(self) -> dict:
        """Estado: variável com prefixo $ — valida formato e tamanho."""
        start_line, start_col = self.line, self.col
        self._advance()  # Consome '$'
        buffer = ''

        ch = self._peek()

        # Erro: '$' deve ser seguido de letra minúscula ou '_' (não dígito nem maiúscula)
        if ch is None or not (ch.islower() or ch == '_'):
            # Captura o resto mal formado para compor a mensagem de erro
            mal = '$'
            while self._peek() is not None and self._is_alnum(self._peek()):
                mal += self._advance()
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Identificador/variável mal formado: '{mal}'"
            )

        # Consome o restante do nome da variável
        while self._peek() is not None and self._is_alnum(self._peek()):
            buffer += self._advance()

        # Validação de tamanho máximo
        if len(buffer) > MAX_ID_LEN:
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Tamanho do identificador '${buffer}' excede o limite de {MAX_ID_LEN} caracteres."
            )

        return self._tok('ID', f'${buffer}', start_line, start_col)

    def _read_id_func(self) -> dict:
        """Estado: chamada de função com prefixo ! — valida formato e tamanho."""
        start_line, start_col = self.line, self.col
        self._advance()  # Consome '!'
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
        """Estado: literal numérico — reconhece inteiro e float, rejeita mal formado."""
        start_line, start_col = self.line, self.col
        buffer = ''

        # Consome a parte inteira
        while self._peek() is not None and self._peek().isdigit():
            buffer += self._advance()

        # Parte decimal?
        if self._peek() == '.':
            buffer += self._advance()           # Consome '.'
            ch = self._peek()

            # Erro: ponto não seguido de dígito (ex: 2.a3, 2.)
            if ch is None or not ch.isdigit():
                mal = buffer
                while self._peek() is not None and (self._peek().isalnum() or self._peek() in '._'):
                    mal += self._advance()
                raise LexerError(
                    f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                    f"Número mal formado: '{mal}'"
                )

            # Consome os dígitos decimais
            while self._peek() is not None and self._peek().isdigit():
                buffer += self._advance()

        # Erro: número seguido direto de letra (ex: 2a3)
        if self._peek() is not None and self._is_letter(self._peek()):
            mal = buffer
            while self._peek() is not None and self._is_alnum(self._peek()):
                mal += self._advance()
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Identificador/número mal formado: '{mal}'"
            )

        # Validação de tamanho excessivo
        if len(buffer) > MAX_NUM_LEN:
            raise LexerError(
                f"Erro Léxico [Linha {start_line}, Coluna {start_col}]: "
                f"Tamanho excessivo do número '{buffer}' (máximo de {MAX_NUM_LEN} dígitos)."
            )

        return self._tok('NUMBER', buffer, start_line, start_col)

    def _read_identifier(self) -> dict:
        """Estado: identificador ou palavra reservada — letras, dígitos e '_'."""
        start_line, start_col = self.line, self.col
        buffer = ''

        while self._peek() is not None and self._is_alnum(self._peek()):
            buffer += self._advance()

        # Verifica se é palavra reservada ou identificador genérico
        if buffer in KEYWORDS:
            return self._tok('KEYWORD', buffer, start_line, start_col)
        return self._tok('ID', buffer, start_line, start_col)

    # ── Verificação pós-tokenização de blocos desbalanceados ─────────────────

    @staticmethod
    def _check_braces(tokens: list[dict]):
        """Percorre os tokens verificando balanceamento de { e }.
        
        depth acompanha quantos blocos estão abertos ao mesmo tempo.
        Cada '{' incrementa e cada '}' decrementa.
        Se '}' é encontrado com depth == 0, é um excesso.
        Se ao final depth > 0, há um bloco nunca fechado.
        """
        depth = 0
        last_open = None
        for t in tokens:
            if t['token'] == 'LBRACE':
                depth += 1
                if depth == 1:
                    last_open = t   # Salva apenas a abertura de nível mais externo
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

    # ── Construtor de Token ───────────────────────────────────────────────────

    @staticmethod
    def _tok(kind: str, value: str, line: int, col: int) -> dict:
        return {'token': kind, 'valor': value, 'line': line, 'col': col}

    # ── Formatação de Saída no padrão do professor ────────────────────────────

    @staticmethod
    def format_tokens(tokens: list[dict]) -> str:
        lines = []
        for t in tokens:
            if t['token'] == 'EOF':
                continue
            name = TOKEN_NAMES_PT.get(t['token'], t['token'])
            lines.append(f"Linha: {t['line']} - Coluna {t['col']} - Token:<{name}, {t['valor']}>")
        return '\n'.join(lines)

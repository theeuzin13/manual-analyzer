import http.server
import socketserver
import json
import sys
import io
import os

sys.path.insert(0, os.path.dirname(__file__))
from lexer_manual import ManualLexer, LexerError

PORT = 8001


class ManualIDEHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path in ('/', '/index_manual.html'):
            self._serve_file('index_manual.html', 'text/html; charset=utf-8')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/run_manual':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)

            try:
                req = json.loads(body.decode('utf-8'))
                code = req.get('code', '')
            except Exception as e:
                self._json_response(400, {'error': f'JSON inválido: {e}'})
                return

            tokens_fmt = ''
            error_msg = None

            try:
                lexer = ManualLexer(code)
                tokens = lexer.tokenize()
                tokens_fmt = ManualLexer.format_tokens(tokens)
            except LexerError as e:
                error_msg = str(e)
            except Exception as e:
                error_msg = f'Erro interno: {e}'

            self._json_response(200, {
                'success': error_msg is None,
                'tokens': tokens_fmt,
                'error': error_msg,
            })
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_file(self, filename: str, content_type: str):
        path = os.path.join(os.path.dirname(__file__), filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(f'Arquivo {filename} não encontrado.'.encode())

    def _json_response(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(body)


def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('', PORT), ManualIDEHandler) as httpd:
        print('==================================================')
        print('  IDE MANUAL DO BUILDSCRIPT INICIADA!')
        print(f'  Acesse: http://localhost:{PORT}')
        print('  Para encerrar: CTRL+C')
        print('==================================================')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor encerrado.')


if __name__ == '__main__':
    main()

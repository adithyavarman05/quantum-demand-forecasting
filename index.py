import os
import mimetypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def app(environ, start_response):
    path = environ.get('PATH_INFO', '/').lstrip('/')
    if not path or path == '':
        path = 'index.html'
    
    # Strip query parameters if any
    path = path.split('?')[0]
    
    # Sanitize path to prevent directory traversal
    filename = os.path.basename(path)
    file_path = os.path.join(BASE_DIR, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        if mime_type.startswith('text/'):
            mime_type += '; charset=utf-8'
            
        with open(file_path, 'rb') as f:
            content = f.read()
            
        start_response('200 OK', [
            ('Content-Type', mime_type),
            ('Content-Length', str(len(content)))
        ])
        return [content]
    
    # Default fallback to index.html
    html_path = os.path.join(BASE_DIR, 'index.html')
    if os.path.exists(html_path):
        with open(html_path, 'rb') as f:
            content = f.read()
        start_response('200 OK', [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(content)))
        ])
        return [content]

    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'File Not Found']

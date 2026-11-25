"""Quita del SVG exportado por Graphviz los textos de las relaciones.

En diagrama_er_v1.dot las relaciones tienen etiquetas transparentes: solo
sirven para que Graphviz distribuya las líneas. Este script elimina esos
<text> del SVG para que no queden textos ocultos en el archivo.

Uso, desde la carpeta que contiene manage.py:
    dot -Tsvg er/diagrama_er_v1.dot -o er/diagrama_er_v1.svg
    .\\.venv\\Scripts\\python.exe er/limpiar_svg.py er/diagrama_er_v1.svg
"""
import re
import sys
from pathlib import Path

GRUPO_RELACION = re.compile(r'(<g id="edge\d+" class="edge">.*?</g>)', re.S)
TEXTO = re.compile(r'\s*<text\b[^>]*>.*?</text>', re.S)


def limpiar(svg):
    return GRUPO_RELACION.sub(lambda m: TEXTO.sub('', m.group(1)), svg)


if __name__ == '__main__':
    ruta = Path(sys.argv[1] if len(sys.argv) > 1 else 'er/diagrama_er_v1.svg')
    ruta.write_text(limpiar(ruta.read_text(encoding='utf-8')), encoding='utf-8')
    print(f'Textos de relaciones eliminados de {ruta}')

#!/usr/bin/env python3
"""Genera pedido.html a partir de pedido.template.html.

El catálogo de estilos NO se mantiene a mano: se extrae de la galería
`#estilos` de petit_studio_v3.html (mismas imágenes base64, sin duplicar
ni recodificar) y se inyecta en la plantilla donde está el marcador
__CATALOG_JSON__.

Uso:  python3 build_pedido.py
"""
import re, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'petit_studio_v3.html')
TPL = os.path.join(HERE, 'pedido.template.html')
OUT = os.path.join(HERE, 'pedido.html')

PLACEHOLDER = '__CATALOG_JSON__'

# Cada gallery-item de #estilos: categoría + alt + src base64
PATTERN = re.compile(
    r'<div class="gallery-item[^>]*data-category="([^"]+)"[^>]*>\s*'
    r'<img alt="([^"]*)"[^>]*src="(data:image/jpeg;base64,[^"]+)"[^>]*/?>'
)


def main():
    source = open(SRC, encoding='utf-8').read()
    items = PATTERN.findall(source)

    # Comprobación de cordura: el número de items extraídos debe coincidir
    # con los `gallery-item` presentes en el fichero fuente. Si no cuadra,
    # el regex se ha desincronizado del marcado y hay que revisarlo.
    declared = source.count('class="gallery-item')
    if len(items) != declared:
        sys.exit(
            f'ERROR: extraídos {len(items)} items pero hay {declared} '
            f'`gallery-item` en {os.path.basename(SRC)}. El regex ya no '
            f'coincide con el marcado — revísalo antes de continuar.'
        )
    if not items:
        sys.exit('ERROR: no se ha extraído ninguna imagen del catálogo.')

    catalog = [{'category': c, 'alt': a, 'src': s} for c, a, s in items]

    template = open(TPL, encoding='utf-8').read()
    if PLACEHOLDER not in template:
        sys.exit(f'ERROR: falta el marcador {PLACEHOLDER} en la plantilla.')

    html = template.replace(PLACEHOLDER, json.dumps(catalog, ensure_ascii=False))
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)

    by_cat = {}
    for c, _, _ in items:
        by_cat[c] = by_cat.get(c, 0) + 1
    print(f'✓ {os.path.basename(OUT)} generado ({len(html):,} bytes)')
    print(f'  {len(items)} fotos: ' + ', '.join(f'{k} ({v})' for k, v in by_cat.items()))


if __name__ == '__main__':
    main()

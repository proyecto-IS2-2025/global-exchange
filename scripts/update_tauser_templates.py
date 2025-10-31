#!/usr/bin/env python
"""
Script para actualizar los templates de TAUSER y eliminar decimales en divisas.
Reemplaza floatformat:2 por currency (filtro personalizado sin decimales)
"""
import os
import re
from pathlib import Path

def update_template_file(file_path):
    """
    Actualiza un archivo de template reemplazando floatformat:2 con currency
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Patrón 1: {{ valor|floatformat:2 }} → {{ valor|currency }}
        pattern1 = r'\{\{\s*([^}|]+)\|floatformat:2\s*\}\}'
        matches1 = re.findall(pattern1, content)
        if matches1:
            content = re.sub(pattern1, r'{{ \1|currency }}', content)
            changes_made.append(f"Reemplazó {len(matches1)} ocurrencias de |floatformat:2 por |currency")
        
        # Patrón 2: {{ valor|floatformat:0|intcomma }} → {{ valor|currency }}
        # (Ya está sin decimales, pero aseguramos consistencia)
        pattern2 = r'\{\{\s*([^}|]+)\|floatformat:0\|intcomma\s*\}\}'
        matches2 = re.findall(pattern2, content)
        if matches2:
            content = re.sub(pattern2, r'{{ \1|currency }}', content)
            changes_made.append(f"Reemplazó {len(matches2)} ocurrencias de |floatformat:0|intcomma por |currency")
        
        # Patrón 3: Valores de denominación que ya usan floatformat:0 (dejarlos como currency también)
        pattern3 = r'\{\{\s*([^}|]*denominacion[^}|]*valor[^}|]*)\|floatformat:0\s*\}\}'
        matches3 = re.findall(pattern3, content)
        if matches3:
            content = re.sub(pattern3, r'{{ \1|currency }}', content)
            changes_made.append(f"Reemplazó {len(matches3)} valores de denominación a |currency")
        
        # Agregar carga de templatetags si no existe
        if 'currency' in content and '{% load tauser_filters %}' not in content:
            # Buscar después de {% load humanize %} o al inicio
            if '{% load humanize %}' in content:
                content = content.replace(
                    '{% load humanize %}',
                    '{% load humanize %}\n{% load tauser_filters %}'
                )
                changes_made.append("Agregó carga de tauser_filters después de humanize")
            elif '{% load static %}' in content:
                content = content.replace(
                    '{% load static %}',
                    '{% load static %}\n{% load tauser_filters %}'
                )
                changes_made.append("Agregó carga de tauser_filters después de static")
            else:
                # Agregar después de {% extends %}
                extends_pattern = r'(\{% extends [^%]+%\})'
                if re.search(extends_pattern, content):
                    content = re.sub(
                        extends_pattern,
                        r'\1\n{% load tauser_filters %}',
                        content,
                        count=1
                    )
                    changes_made.append("Agregó carga de tauser_filters después de extends")
        
        # Solo escribir si hubo cambios
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made
        
        return False, []
        
    except Exception as e:
        print(f"❌ Error procesando {file_path}: {e}")
        return False, []


def main():
    """
    Función principal que recorre todos los templates de TAUSER
    """
    # Ruta base del proyecto
    base_path = Path(__file__).resolve().parent.parent
    tauser_templates_path = base_path / 'tauser' / 'templates'
    
    if not tauser_templates_path.exists():
        print(f"❌ No se encontró la carpeta de templates: {tauser_templates_path}")
        return
    
    print(f"🔍 Buscando templates en: {tauser_templates_path}")
    print("=" * 80)
    
    # Buscar todos los archivos .html
    html_files = list(tauser_templates_path.rglob('*.html'))
    
    print(f"📄 Encontrados {len(html_files)} archivos HTML")
    print("=" * 80)
    
    updated_count = 0
    skipped_count = 0
    
    for html_file in html_files:
        relative_path = html_file.relative_to(tauser_templates_path)
        was_updated, changes = update_template_file(html_file)
        
        if was_updated:
            updated_count += 1
            print(f"\n✅ ACTUALIZADO: {relative_path}")
            for change in changes:
                print(f"   - {change}")
        else:
            skipped_count += 1
            print(f"⏭️  Sin cambios: {relative_path}")
    
    print("\n" + "=" * 80)
    print(f"📊 RESUMEN:")
    print(f"   ✅ Archivos actualizados: {updated_count}")
    print(f"   ⏭️  Archivos sin cambios: {skipped_count}")
    print(f"   📁 Total procesados: {len(html_files)}")
    print("=" * 80)
    print("\n✨ ¡Proceso completado!")
    print("\n📝 NOTA: Ahora todas las divisas en TAUSER se mostrarán SIN decimales.")
    print("   Ejemplo: 100.50 USD → 101 USD")
    print("            150.234 EUR → 150 EUR")
    print("            12.345.678 PYG → 12.345.678 PYG")


if __name__ == '__main__':
    main()

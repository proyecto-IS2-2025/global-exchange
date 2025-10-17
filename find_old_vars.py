"""
Script para encontrar templates que usan variables obsoletas.
"""
import os
import re

OBSOLETE_VARS = ['grupo_admin', 'grupo_operador', 'grupo_cliente']

def find_templates():
    """Encuentra todos los templates HTML."""
    templates = []
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                templates.append(os.path.join(root, file))
    return templates

def check_template(filepath):
    """Verifica si un template usa variables obsoletas."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        found = []
        for var in OBSOLETE_VARS:
            # Buscar en if, elif, y variables
            patterns = [
                rf'{{% if {var}',
                rf'{{% elif {var}',
                rf'{{{{ {var}',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Obtener número de línea
                    line_num = content[:match.start()].count('\n') + 1
                    found.append((var, line_num, match.group()))
        
        return found
    except Exception as e:
        return []

def main():
    print("=" * 80)
    print("🔍 BÚSQUEDA DE VARIABLES OBSOLETAS EN TEMPLATES")
    print("=" * 80)
    print()
    
    templates = find_templates()
    print(f"📁 Analizando {len(templates)} templates...\n")
    
    templates_con_problemas = {}
    
    for template in templates:
        found = check_template(template)
        if found:
            templates_con_problemas[template] = found
    
    if not templates_con_problemas:
        print("✅ ¡Excelente! No se encontraron variables obsoletas.\n")
        return
    
    print(f"⚠️  Encontrados {len(templates_con_problemas)} templates con variables obsoletas:\n")
    
    for template, issues in templates_con_problemas.items():
        print(f"📄 {template}")
        for var, line_num, code in issues:
            print(f"   Línea {line_num}: {var}")
            print(f"   → {code}")
        print()
    
    print("=" * 80)
    print("📋 RESUMEN")
    print("=" * 80)
    print(f"Total templates: {len(templates)}")
    print(f"Con variables obsoletas: {len(templates_con_problemas)}")
    print(f"Ya migrados: {len(templates) - len(templates_con_problemas)}")
    print()
    print("💡 SIGUIENTE PASO: Migrar los templates listados arriba")
    print()

if __name__ == '__main__':
    main()
"""
Script para encontrar qué variables de context processor se usan en templates.
"""
import os
import re

def find_template_files():
    """Encuentra todos los archivos de template."""
    templates = []
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                templates.append(os.path.join(root, file))
    return templates

def search_variables(filepath, variables):
    """Busca variables específicas en un template."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        found = {}
        for var in variables:
            # Buscar en if, for, variables
            patterns = [
                rf'{{% if {var}',
                rf'{{% elif {var}',
                rf'{{{{ {var}',
                rf"'{var}' in",
                rf'"{var}" in',
            ]
            
            for pattern in patterns:
                if re.search(pattern, content):
                    if var not in found:
                        found[var] = []
                    found[var].append(pattern)
        
        return found
    except Exception as e:
        return {}

def main():
    print("=" * 80)
    print("🔍 ANÁLISIS DE VARIABLES DE CONTEXT PROCESSOR EN TEMPLATES")
    print("=" * 80)
    print()
    
    # Variables a buscar
    variables_grupo_usuario = [
        'usuario_es_staff',
        'usuario_es_cliente',
        'tipo_usuario',
        'grupos_usuario',
        'grupo_admin',
        'grupo_operador',
        'grupo_cliente',
    ]
    
    variables_grupos_context = [
        'user_is_staff',
        'user_groups',
        'is_admin',
        'is_operador',
        'is_cliente',
    ]
    
    all_variables = variables_grupo_usuario + variables_grupos_context
    
    # Buscar en templates
    templates = find_template_files()
    print(f"📁 Encontrados {len(templates)} templates\n")
    
    usage_stats = {var: 0 for var in all_variables}
    templates_using = {var: [] for var in all_variables}
    
    for template in templates:
        found = search_variables(template, all_variables)
        
        for var, patterns in found.items():
            usage_stats[var] += 1
            templates_using[var].append(template)
    
    # Reporte
    print("📊 VARIABLES DE grupo_usuario:")
    print("-" * 80)
    for var in variables_grupo_usuario:
        count = usage_stats[var]
        status = "✅" if count > 0 else "○"
        print(f"{status} {var:25} → Usado en {count} template(s)")
        
        if count > 0 and count <= 5:
            for tpl in templates_using[var]:
                print(f"     • {tpl}")
    
    print("\n📊 VARIABLES DE grupos_context (posibles):")
    print("-" * 80)
    for var in variables_grupos_context:
        count = usage_stats[var]
        status = "✅" if count > 0 else "○"
        print(f"{status} {var:25} → Usado en {count} template(s)")
        
        if count > 0:
            for tpl in templates_using[var]:
                print(f"     • {tpl}")
    
    # Conclusiones
    print("\n" + "=" * 80)
    print("🎯 CONCLUSIONES:")
    print("=" * 80)
    
    grupo_usuario_usado = sum(1 for v in variables_grupo_usuario if usage_stats[v] > 0)
    grupos_context_usado = sum(1 for v in variables_grupos_context if usage_stats[v] > 0)
    
    print(f"\n✅ Variables de grupo_usuario en uso:    {grupo_usuario_usado}/{len(variables_grupo_usuario)}")
    print(f"⚠️  Variables de grupos_context en uso:  {grupos_context_usado}/{len(variables_grupos_context)}")
    
    if grupos_context_usado == 0:
        print("\n💡 RECOMENDACIÓN: Eliminar grupos_context (no se usa)")
    elif grupo_usuario_usado > 0 and grupos_context_usado > 0:
        print("\n⚠️  ADVERTENCIA: Ambos context processors en uso (duplicación)")
        print("   Considera fusionarlos en uno solo")

if __name__ == '__main__':
    main()
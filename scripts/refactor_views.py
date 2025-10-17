"""
Script helper para refactorizar vistas de is_staff/is_superuser a permisos.
NO reemplaza automáticamente, pero DETECTA qué cambiar.
"""
import os
import re

APPS_TO_CHECK = ['clientes', 'divisas', 'transacciones', 'medios_pago', 'roles', 'users']

# Patrones a buscar
PATTERNS = {
    'user_passes_test': r'@user_passes_test\(lambda u: u\.is_staff\)',
    'user_passes_test_super': r'@user_passes_test\(lambda u: u\.is_superuser\)',
    'is_admin_helper': r'@user_passes_test\(is_admin\)',
}

def scan_file(filepath):
    """Escanea un archivo en busca de decoradores obsoletos"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    issues = []
    
    for i, line in enumerate(lines, 1):
        for pattern_name, pattern in PATTERNS.items():
            if re.search(pattern, line):
                # Intentar encontrar el nombre de la función
                func_name = "desconocida"
                if i < len(lines):
                    next_line = lines[i]
                    func_match = re.search(r'def (\w+)\(', next_line)
                    if func_match:
                        func_name = func_match.group(1)
                
                issues.append({
                    'file': filepath,
                    'line': i,
                    'pattern': pattern_name,
                    'function': func_name,
                    'content': line.strip()
                })
    
    return issues

def main():
    all_issues = []
    
    for app in APPS_TO_CHECK:
        views_path = os.path.join(app, 'views')
        
        if not os.path.exists(views_path):
            views_file = os.path.join(app, 'views.py')
            if os.path.exists(views_file):
                all_issues.extend(scan_file(views_file))
        else:
            for filename in os.listdir(views_path):
                if filename.endswith('.py') and filename != '__init__.py':
                    filepath = os.path.join(views_path, filename)
                    all_issues.extend(scan_file(filepath))
    
    # Imprimir reporte
    print("=" * 80)
    print("REPORTE DE VISTAS QUE NECESITAN REFACTORIZACIÓN")
    print("=" * 80)
    
    if not all_issues:
        print("✓ ¡No se encontraron problemas!")
        return
    
    grouped = {}
    for issue in all_issues:
        app = issue['file'].split(os.sep)[0]
        if app not in grouped:
            grouped[app] = []
        grouped[app].append(issue)
    
    for app, issues in grouped.items():
        print(f"\n📁 {app.upper()}")
        print("-" * 80)
        for issue in issues:
            print(f"  Archivo: {issue['file']}")
            print(f"  Línea {issue['line']}: {issue['content']}")
            print(f"  Función: {issue['function']}")
            print(f"  → CAMBIAR A: @permission_required_custom('app.permiso')")
            print()
    
    print("=" * 80)
    print(f"TOTAL: {len(all_issues)} vistas necesitan actualización")
    print("=" * 80)

if __name__ == '__main__':
    main()
"""
Script para encontrar URLs rotas en templates.
"""
import os
import re

def find_broken_urls(directory):
    """Busca URLs en templates."""
    broken_urls = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Buscar {% url 'clientes:...' %}
                    urls = re.findall(r"{%\s*url\s+['\"]clientes:(\w+)['\"]", content)
                    
                    for url_name in urls:
                        # Lista de URLs válidas
                        valid_urls = [
                            'lista_clientes', 'crear_cliente', 'editar_cliente', 
                            'seleccionar_cliente', 'asociar_clientes_usuarios',
                            'listar_asociaciones', 'lista_descuentos', 'editar_descuento',
                            'historial_descuentos', 'limites_diarios', 'limites_mensuales',
                            'crear_limite_diario', 'crear_limite_mensual', 
                            'editar_limite_diario', 'editar_limite_mensual',
                            'medio_pago_list', 'medio_pago_dashboard', 'select_medio_pago',
                            'medio_pago_create_with_tipo', 'medio_pago_update',
                            'toggle_medio_pago', 'medio_pago_delete',
                            'seleccionar_medio_acreditacion', 'seleccionar_medio_pago',
                            'medio_pago_detail_ajax', 'verificar_duplicados_ajax',
                            'exportar_medios_pago'
                        ]
                        
                        if url_name not in valid_urls:
                            broken_urls.append({
                                'file': filepath,
                                'url': url_name
                            })
    
    return broken_urls

if __name__ == '__main__':
    templates_dir = 'C:/proyecto-is2/casa_de_cambios'
    broken = find_broken_urls(templates_dir)
    
    if broken:
        print("❌ URLs ROTAS encontradas:\n")
        for item in broken:
            print(f"Archivo: {item['file']}")
            print(f"URL rota: clientes:{item['url']}\n")
    else:
        print("✅ No se encontraron URLs rotas")
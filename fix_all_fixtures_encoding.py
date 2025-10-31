import os
import json
import glob

def convert_utf16_to_utf8(file_path):
    """Convierte un archivo JSON de UTF-16 a UTF-8"""
    try:
        # Leer con UTF-16
        with open(file_path, 'r', encoding='utf-16') as f:
            data = json.load(f)
        
        # Escribir con UTF-8
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

# Buscar todos los archivos JSON en fixtures
fixture_files = glob.glob('**/fixtures/*.json', recursive=True)

print(f"Encontrados {len(fixture_files)} archivos JSON en fixtures\n")

utf16_files = []
for file_path in fixture_files:
    try:
        with open(file_path, 'rb') as f:
            first_bytes = f.read(2)
            if first_bytes == b'\xff\xfe':  # BOM UTF-16 LE
                utf16_files.append(file_path)
    except:
        pass

if not utf16_files:
    print("✅ No se encontraron archivos con codificación UTF-16")
else:
    print(f"Encontrados {len(utf16_files)} archivos con UTF-16:\n")
    for file_path in utf16_files:
        print(f"📄 {file_path}")
        if convert_utf16_to_utf8(file_path):
            print(f"  ✅ Convertido exitosamente\n")
        else:
            print(f"  ❌ Error al convertir\n")
    
    print(f"\n✅ Conversión completada: {len(utf16_files)} archivos")

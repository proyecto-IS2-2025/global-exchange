import json

# Leer el archivo con codificación UTF-16
with open('medios_pago/fixtures/mediosfinancieros_data.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

# Escribir el archivo con codificación UTF-8 sin BOM
with open('medios_pago/fixtures/mediosfinancieros_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ Archivo convertido de UTF-16 a UTF-8 exitosamente")

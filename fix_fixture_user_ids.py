import json

# Leer el fixture
with open('clientes/fixtures/mediosfinancieroscliente_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Cambiar creado_por de 11 a 1 (admin)
for item in data:
    if item['fields'].get('creado_por') == 11:
        item['fields']['creado_por'] = 1
        print(f"✏️  Actualizando registro {item['pk']}: creado_por 11 → 1")

# Guardar el fixture actualizado
with open('clientes/fixtures/mediosfinancieroscliente_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n✅ Fixture actualizado exitosamente")

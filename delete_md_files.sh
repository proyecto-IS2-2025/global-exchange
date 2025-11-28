#!/bin/bash

################################################################################
# Script para Eliminar Archivos Markdown
# Elimina todos los archivos .md EXCEPTO README.md
################################################################################

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorio base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🗑️  Eliminando archivos Markdown${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Contar archivos .md (excluyendo README.md)
TOTAL=$(find "$BASE_DIR" -name "*.md" ! -name "README.md" -type f | wc -l)

if [ "$TOTAL" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No hay archivos .md para eliminar (excepto README.md)"
    exit 0
fi

echo -e "${YELLOW}Se encontraron $TOTAL archivos .md para eliminar${NC}"
echo ""

# Listar archivos que se van a eliminar
echo -e "${BLUE}Archivos que serán eliminados:${NC}"
find "$BASE_DIR" -name "*.md" ! -name "README.md" -type f -exec basename {} \; | sort

echo ""
read -p "¿Desea continuar con la eliminación? (s/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}⚠${NC} Operación cancelada"
    exit 0
fi

echo ""
echo -e "${BLUE}Eliminando archivos...${NC}"

# Eliminar archivos
DELETED=0
while IFS= read -r file; do
    if rm "$file"; then
        echo -e "${GREEN}✓${NC} Eliminado: $(basename "$file")"
        ((DELETED++))
    else
        echo -e "${RED}✗${NC} Error al eliminar: $(basename "$file")"
    fi
done < <(find "$BASE_DIR" -name "*.md" ! -name "README.md" -type f)

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Eliminados $DELETED de $TOTAL archivos${NC}"
echo -e "${GREEN}✓ README.md conservado${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

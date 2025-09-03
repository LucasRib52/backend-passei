#!/bin/bash

# Script para sincronização automática de produtos TheMembers
# Use este script em cron jobs para sincronização automática

# Configurações
PROJECT_DIR="/path/to/your/backend_passei"  # Altere para o caminho correto
LOG_FILE="/var/log/themembers_sync.log"
PYTHON_PATH="/usr/bin/python3"  # Altere se necessário

# Função de logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Verificar se o diretório do projeto existe
if [ ! -d "$PROJECT_DIR" ]; then
    log "ERRO: Diretório do projeto não encontrado: $PROJECT_DIR"
    exit 1
fi

# Navegar para o diretório do projeto
cd "$PROJECT_DIR" || {
    log "ERRO: Não foi possível navegar para o diretório do projeto"
    exit 1
}

# Verificar se o ambiente virtual existe (se usado)
if [ -d "venv" ]; then
    source venv/bin/activate
    log "Ambiente virtual ativado"
fi

# Executar sincronização
log "Iniciando sincronização TheMembers..."
$PYTHON_PATH manage.py sync_themembers_products --silent --log-file "$LOG_FILE"

# Verificar se a sincronização foi bem-sucedida
if [ $? -eq 0 ]; then
    log "Sincronização TheMembers concluída com sucesso"
else
    log "ERRO: Falha na sincronização TheMembers"
fi

# Desativar ambiente virtual se foi ativado
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
    log "Ambiente virtual desativado"
fi

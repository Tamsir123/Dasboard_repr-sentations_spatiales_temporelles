#!/bin/bash

# 🐳 Script de déploiement Docker - Dashboard Climatique Sénégal

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }

# Déploiement
echo -e "${BLUE}🐳 Dashboard Climatique - Déploiement Docker${NC}"

# Nettoyer et déployer
print_info "Nettoyage..."
docker-compose down --remove-orphans || true

print_info "Déploiement..."
docker-compose up -d --build

print_info "Attente du démarrage (15s)..."
sleep 15

print_info "Statut:"
docker-compose ps

print_success "Déploiement terminé !"
print_info "🌐 Dashboard: http://localhost:8501"
print_info "🔌 API: http://localhost:8000"
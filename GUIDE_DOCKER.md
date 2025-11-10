# 🐳 Guide de déploiement Docker complet

## 🚀 Commandes rapides

### A. Déploiement simple (recommandé pour débuter)
```bash
# 1. Builder et lancer
./deploy_docker.sh simple

# 2. Accéder aux services
# Dashboard: http://localhost:8501
# API: http://localhost:8000
# Docs API: http://localhost:8000/docs
```

### B. Déploiement avec Nginx (recommandé pour production)
```bash
# 1. Builder et lancer avec reverse proxy
./deploy_docker.sh nginx

# 2. Accéder aux services
# Application complète: http://localhost
# Dashboard: http://localhost (même port)
# API: http://localhost/api
```

### C. Mode développement (voir les logs)
```bash
./deploy_docker.sh dev
```

### D. Arrêter les services
```bash
./deploy_docker.sh stop
```

## 🌍 Exposition sur Internet

### Option 1: ngrok (rapide et gratuit)
```bash
# 1. Installer ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# 2. Créer compte gratuit sur https://ngrok.com
# 3. Configurer le token
ngrok config add-authtoken YOUR_TOKEN

# 4. Exposer le dashboard (mode simple)
ngrok http 8501

# Ou exposer l'application complète (mode nginx)
ngrok http 80
```

### Option 2: VPS avec Docker (production)
```bash
# 1. Sur votre VPS (Ubuntu/Debian)
sudo apt update
sudo apt install docker.io docker-compose git

# 2. Cloner le projet
git clone https://github.com/Tamsir123/votre-repo.git
cd votre-repo

# 3. Déployer
./deploy_docker.sh nginx

# 4. Configurer le firewall
sudo ufw allow 80
sudo ufw allow 443  # Pour SSL plus tard

# 5. Optionnel: SSL avec Let's Encrypt
sudo apt install certbot
# Configurer le certificat SSL
```

## 🔧 Commandes Docker utiles

### Gestion des conteneurs
```bash
# Voir les conteneurs actifs
docker ps

# Voir les logs d'un service
docker-compose logs backend
docker-compose logs frontend

# Redémarrer un service
docker-compose restart backend

# Reconstruire une image
docker-compose build --no-cache backend

# Entrer dans un conteneur
docker exec -it climate_api bash
docker exec -it climate_dashboard bash
```

### Nettoyage
```bash
# Supprimer les conteneurs et images
docker-compose down --rmi all --volumes

# Nettoyer complètement Docker
docker system prune -a --volumes
```

## 🐛 Dépannage

### Problème: Conteneur backend ne démarre pas
```bash
# Vérifier les logs
docker-compose logs backend

# Problèmes courants:
# - Fichiers NetCDF manquants → vérifier le montage de volume
# - Port 8000 occupé → docker-compose down puis relancer
```

### Problème: Frontend ne se connecte pas au backend
```bash
# Vérifier la connectivité réseau
docker exec climate_dashboard curl -f http://backend:8000/health

# Si échec, vérifier:
# - Les services sont sur le même réseau Docker
# - La variable API_BASE_URL est correcte
```

### Problème: Nginx ne fonctionne pas
```bash
# Vérifier la config Nginx
docker exec climate_proxy nginx -t

# Recharger la config
docker exec climate_proxy nginx -s reload
```

## 📊 Monitoring

### Health checks
```bash
# Vérifier la santé des services
docker-compose ps

# Tests manuels
curl http://localhost:8000/health        # Backend
curl http://localhost:8501/_stcore/health # Frontend
curl http://localhost/health             # Nginx
```

### Métriques Docker
```bash
# Utilisation des ressources
docker stats

# Espace disque utilisé
docker system df
```

## 🚀 Production avancée

### Avec SSL (Let's Encrypt)
1. Modifier `nginx.conf` pour ajouter SSL
2. Utiliser `certbot` pour générer les certificats
3. Redéployer avec les certificats montés

### Avec base de données
1. Ajouter un service PostgreSQL au `docker-compose.yml`
2. Modifier l'API pour utiliser la DB
3. Ajouter les variables d'environnement DB

### Avec monitoring
1. Ajouter Prometheus + Grafana au stack
2. Configurer les métriques dans FastAPI
3. Créer des dashboards de monitoring

## 📝 Variables d'environnement importantes

```bash
# Dans .env
DEPLOYMENT_MODE=docker          # Mode de déploiement
API_BASE_URL=http://backend:8000/api/v1/climate  # URL backend
DEBUG_MODE=false               # Mode debug
COMPOSE_PROJECT_NAME=climate_dashboard  # Nom du projet Docker
```
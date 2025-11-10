FROM nginx:alpine

# Copier la configuration personnalisée
COPY nginx.conf /etc/nginx/nginx.conf

# Exposer le port 80
EXPOSE 80

# Commande par défaut (héritée de l'image nginx)
CMD ["nginx", "-g", "daemon off;"]
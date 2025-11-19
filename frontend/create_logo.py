#!/usr/bin/env python3
"""
Créer le logo ClimaSéné pour le dashboard climatique
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_logo():
    # Dimensions
    width, height = 200, 200
    
    # Créer l'image avec fond transparent
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Couleurs
    primary_blue = (30, 60, 114)
    secondary_blue = (42, 82, 152)
    gold = (255, 215, 0)
    white = (255, 255, 255)
    
    # Fond circulaire avec gradient
    for i in range(80):
        color = (
            int(primary_blue[0] + (secondary_blue[0] - primary_blue[0]) * i / 80),
            int(primary_blue[1] + (secondary_blue[1] - primary_blue[1]) * i / 80),
            int(primary_blue[2] + (secondary_blue[2] - primary_blue[2]) * i / 80),
            200
        )
        draw.ellipse([10+i//2, 10+i//2, width-10-i//2, height-10-i//2], fill=color)
    
    # Soleil (température)
    sun_center = (60, 60)
    sun_radius = 20
    draw.ellipse([sun_center[0]-sun_radius, sun_center[1]-sun_radius, 
                  sun_center[0]+sun_radius, sun_center[1]+sun_radius], 
                 fill=gold)
    
    # Rayons du soleil
    for angle in range(0, 360, 45):
        import math
        x = sun_center[0] + math.cos(math.radians(angle)) * (sun_radius + 10)
        y = sun_center[1] + math.sin(math.radians(angle)) * (sun_radius + 10)
        x2 = sun_center[0] + math.cos(math.radians(angle)) * (sun_radius + 18)
        y2 = sun_center[1] + math.sin(math.radians(angle)) * (sun_radius + 18)
        draw.line([x, y, x2, y2], fill=gold, width=3)
    
    # Thermomètre
    therm_x = 140
    therm_y = 50
    # Corps du thermomètre
    draw.rectangle([therm_x, therm_y, therm_x+8, therm_y+40], fill=(220, 20, 60))
    # Bulbe
    draw.ellipse([therm_x-4, therm_y+35, therm_x+12, therm_y+50], fill=(220, 20, 60))
    # Graduations
    for i in range(5):
        y_grad = therm_y + 5 + i * 8
        draw.line([therm_x+8, y_grad, therm_x+12, y_grad], fill=white, width=1)
    
    # Graphique simple (données)
    graph_points = [(40, 130), (60, 120), (80, 135), (100, 115), (120, 125), (140, 110)]
    for i in range(len(graph_points)-1):
        draw.line([graph_points[i], graph_points[i+1]], fill=(79, 195, 247), width=3)
    
    # Points du graphique
    for point in graph_points:
        draw.ellipse([point[0]-3, point[1]-3, point[0]+3, point[1]+3], fill=(79, 195, 247))
    
    # Contour du Sénégal stylisé
    senegal_points = [(50, 150), (70, 145), (90, 148), (110, 155), (120, 170), (110, 180), (85, 175), (60, 172), (50, 160)]
    draw.polygon(senegal_points, fill=(129, 199, 132), outline=(76, 175, 80), width=2)
    
    # Points de villes
    cities = [(65, 160), (85, 155), (100, 165)]
    for city in cities:
        draw.ellipse([city[0]-2, city[1]-2, city[0]+2, city[1]+2], fill=gold)
    
    # Sauvegarder
    logo_path = os.path.join(os.path.dirname(__file__), 'logo_climasene.png')
    img.save(logo_path, 'PNG')
    print(f"Logo créé: {logo_path}")
    
    return logo_path

if __name__ == "__main__":
    create_logo()
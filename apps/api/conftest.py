"""Configuration pytest pour l'API SûrCheck AI."""

import sys
import os

# Ajouter le répertoire apps/api au chemin Python
sys.path.insert(0, os.path.dirname(__file__))
os.environ["TESTING"] = "1"

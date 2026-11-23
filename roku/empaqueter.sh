#!/bin/sh
# Prépare ameux-roku.zip, le fichier à envoyer à la TV (page web de la TV en mode développeur).
cd "$(dirname "$0")" && rm -f ../ameux-roku.zip && zip -qr ../ameux-roku.zip manifest source components images && echo "ameux-roku.zip prêt"

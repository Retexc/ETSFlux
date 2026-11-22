# AMÉUX sur la TV Roku

Économiseur d'écran « AMÉUX » : quand la TV est inactive sur l'accueil Roku, elle passe les annonces
d'AMÉUX Flux (Annonces → Écran du salon), dans le même design que l'écran web. N'importe quelle touche
de la télécommande ramène à la TV.

AMÉUX Flux dessine chaque diapositive en image (`/api/roku`) ; la Roku affiche les images et les
vidéos MP4, et écrit elle-même l'heure, le bandeau d'annonces et les alertes STM.

## Installer (une seule fois)

1. **Mode développeur de la TV** : sur la télécommande, appuie sur Accueil 3 fois, Haut 2 fois,
   Droite, Gauche, Droite, Gauche, Droite. Note l'adresse affichée (ex. `http://192.168.1.42`),
   accepte la licence, choisis un mot de passe (utilisateur : `rokudev`). La TV redémarre.
2. **Fichier de l'application** : `./roku/empaqueter.sh` crée `ameux-roku.zip`.
3. Sur un ordinateur **branché au même Wi-Fi que la TV**, ouvre l'adresse notée à l'étape 1,
   connecte-toi (`rokudev` + ton mot de passe), choisis `ameux-roku.zip`, puis **Install**.
   Si la page ne s'ouvre pas, le réseau empêche peut-être les appareils de se voir : connecte la TV
   et l'ordinateur au partage de connexion d'un téléphone le temps de l'installation.
4. La chaîne **AMÉUX** s'ouvre. Dans AMÉUX Flux : Annonces → Écran du salon → Connecter un écran,
   puis entre le code affiché avec la télécommande.
5. Sur la TV : **Paramètres → Thème → Économiseurs d'écran → AMÉUX**, puis le délai voulu.

## Ensuite

- Reconnecter avec un nouveau code : ouvrir la chaîne AMÉUX, touche `*`.
- Mettre à jour l'application : refaire les étapes 2 et 3 (la connexion est gardée).
- L'économiseur ne se lance pas sur une entrée HDMI ni sur la télé en direct (règle de Roku).
- Vidéos : MP4 seulement (les WebM ne passent pas sur la Roku).

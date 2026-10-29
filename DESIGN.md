# DESIGN

Principe : **l'information d'abord, le décor ensuite.** Chaque card se lit en moins de deux secondes ; le pixel art donne du caractère sans jamais passer devant le message.

## Contraintes de l'écran

| Contrainte | Conséquence |
|---|---|
| 240x240 LED | Texte lisible dès 8 px (labels), 16 à 24 px pour les valeurs, 40 px pour un héros. |
| GIF quantifié (64 à 128 couleurs) | Dégradés en bandes nettes, palettes courtes par zone. |
| Card visible environ 10 s par rotation | Un seul héros par card, le reste s'aligne autour. |
| Pixel perfect | Zoom entier, nearest neighbor, aucun anti-aliasing sur les sprites. |
| Mémoire (environ 3 Mo) | Cryptos 10 Ko, météo et horloge environ 200 Ko chacune. |

## Cards

- **Crypto** : pièce et nom petits et centrés, variation 24 h en héros, prix dessous, sparkline réelle en aire dégradée dans le fond, plus bas et plus haut du jour en bas avec contour sombre pour la lisibilité.
- **Météo** : scène plein cadre en perspective (ciel, décor, acteurs animés), icône, condition et température géante au centre avec contour. La scène dépend du jour (rotation), du moment, de la météo et de la saison.
- **Horloge** : style HTC Sense, tuiles noires brillantes à volets, date, météo animée. GIF non bouclé : effet d'entrée, retournement du chiffre qui change, reflet discret, puis image finale tenue.

## Animations

Toutes les boucles sont fermées (sinus, ping-pong, défilement modulo) pour éviter tout saut au redémarrage du GIF. Le firmware applique son propre fondu entre les images de l'album ; les effets d'entrée sont donc intégrés au GIF et réservés aux GIF non bouclés.

## Backoffice

Contexte produit dans `PRODUCT.md`. Cockpit sombre, Material 3 Expressive : formes très arrondies, teintes neutres tirées vers le bleu nuit, ambre en action principale, aperçu fidèle avant chaque envoi.

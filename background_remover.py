from PIL import Image
import os

def remove_background_from_image(image_path, output_path, target_color=(255, 255, 255), tolerance=30):
    """
    Tente de rendre transparent l'arrière-plan d'une image en se basant sur une couleur cible.
    Fonctionne mieux avec des arrière-plans uniformes.

    Args:
        image_path (str): Chemin d'accès à l'image d'entrée.
        output_path (str): Chemin d'accès où l'image traitée sera sauvegardée (format PNG).
        target_color (tuple): La couleur (R, G, B) de l'arrière-plan à rendre transparent. Par défaut, blanc (255, 255, 255).
        tolerance (int): La tolérance pour la correspondance des couleurs (0-255). Une valeur plus élevée
                         rendra transparentes plus de nuances autour de la couleur cible.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        datas = img.getdata()

        new_data = []
        for item in datas:
            # Vérifier si le pixel est proche de la couleur cible
            if all(abs(item[i] - target_color[i]) <= tolerance for i in range(3)):
                new_data.append((255, 255, 255, 0))  # Rendre transparent
            else:
                new_data.append(item)

        img.putdata(new_data)
        img.save(output_path, "PNG")
        print(f"Image traitée et sauvegardée avec succès : {output_path}")
        return True
    except Exception as e:
        print(f"Erreur lors du traitement de l'image {image_path}: {e}")
        return False

if __name__ == "__main__":
    # Exemple d'utilisation via la ligne de commande
    # python background_remover.py input.png output.png --color 255 255 255 --tolerance 30

    import argparse

    parser = argparse.ArgumentParser(description="Supprime l'arrière-plan d'une image en rendant une couleur cible transparente.")
    parser.add_argument("input_image", help="Chemin de l'image d'entrée.")
    parser.add_argument("output_image", help="Chemin de l'image de sortie (sera au format PNG).")
    parser.add_argument("--color", nargs=3, type=int, default=[255, 255, 255],
                        help="Couleur cible de l'arrière-plan en R G B (ex: --color 255 255 255 pour blanc).")
    parser.add_argument("--tolerance", type=int, default=30,
                        help="Tolérance de couleur (0-255). Plus la valeur est élevée, plus de nuances seront rendues transparentes.")

    args = parser.parse_args()

    # Convertir la couleur cible en tuple
    target_color_tuple = tuple(args.color)

    remove_background_from_image(args.input_image, args.output_image, target_color_tuple, args.tolerance)

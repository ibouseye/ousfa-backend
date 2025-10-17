import os
import sys
import shutil
import filecmp
import time
from tqdm import tqdm

def sync_dirs(src, dst):
    """
    Synchronise le répertoire de destination (dst) pour qu'il soit un miroir
    du répertoire source (src).
    """
    comparison = filecmp.dircmp(src, dst)

    # Copier les fichiers/dossiers qui sont dans src mais pas dans dst
    for name in tqdm(comparison.left_only, desc=f"COPIE vers {os.path.basename(dst)}", unit="fichier"):
        src_path = os.path.join(src, name)
        dst_path = os.path.join(dst, name)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)

    # Mettre à jour les fichiers qui sont différents
    for name in tqdm(comparison.diff_files, desc=f"MISE À JOUR dans {os.path.basename(dst)}", unit="fichier"):
        src_path = os.path.join(src, name)
        dst_path = os.path.join(dst, name)
        shutil.copy2(src_path, dst_path)

    # Supprimer les fichiers/dossiers qui sont dans dst mais pas dans src
    for name in tqdm(comparison.right_only, desc=f"SUPPRESSION dans {os.path.basename(dst)}", unit="fichier"):
        dst_path = os.path.join(dst, name)
        if os.path.isdir(dst_path):
            shutil.rmtree(dst_path)
        else:
            os.remove(dst_path)

    # Récursion dans les sous-dossiers communs
    for common_dir in comparison.common_dirs:
        new_src = os.path.join(src, common_dir)
        new_dst = os.path.join(dst, common_dir)
        sync_dirs(new_src, new_dst)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python sync_dirs.py <répertoire_source> <répertoire_destination>")
        sys.exit(1)

    source_dir = sys.argv[1]
    dest_dir = sys.argv[2]

    if not os.path.isdir(source_dir):
        print(f"Erreur : Le répertoire source n'existe pas : {source_dir}")
        sys.exit(1)

    if not os.path.isdir(dest_dir):
        print(f"Le répertoire de destination n'existe pas. Création de : {dest_dir}")
        os.makedirs(dest_dir)

    start_time = time.time()
    print(f"Démarrage de la synchronisation de '__{source_dir}__' vers '__{dest_dir}__'...")

    try:
        sync_dirs(source_dir, dest_dir)
        end_time = time.time()
        duration = end_time - start_time
        print(f"\nSynchronisation terminée avec succès en {duration:.2f} secondes.")
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"\nUne erreur est survenue durant la synchronisation (durée: {duration:.2f}s) : {e}")
        sys.exit(1)
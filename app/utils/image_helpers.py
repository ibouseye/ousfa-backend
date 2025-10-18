import os
import filetype
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import cloudinary
import cloudinary.uploader

def allowed_file(file, allowed_extensions):
    """Vérifie si le fichier a une extension autorisée et un type MIME d'image."""
    # Vérification de l'extension
    has_valid_extension = '.' in file.filename and \
                          file.filename.rsplit('.', 1)[1].lower() in allowed_extensions
    if not has_valid_extension:
        return False

    # Vérification du type MIME avec filetype
    file.seek(0)
    # filetype a besoin des 261 premiers octets pour fonctionner
    header = file.read(261)
    kind = filetype.guess(header)
    file.seek(0)

    if kind is None:
        return False

    return kind.mime.startswith('image/')

def save_image(file, upload_folder=None, image_size=(400, 400)):
    """Traite et sauvegarde une image uploadée sur Cloudinary avec un nom de fichier unique."""
    # Générer un nom de fichier unique pour Cloudinary
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    public_id = f"{uuid.uuid4()}"

    # Envoyer le fichier à Cloudinary
    # Le fichier doit être un objet de type fichier (file-like object)
    # Cloudinary peut lire directement depuis file.stream
    upload_result = cloudinary.uploader.upload(file.stream, 
                                                public_id=public_id, 
                                                folder="ousfa_ecommerce", # Dossier sur Cloudinary
                                                resource_type="image")
    
    # Retourner l'URL sécurisée de l'image sur Cloudinary
    return upload_result['secure_url']

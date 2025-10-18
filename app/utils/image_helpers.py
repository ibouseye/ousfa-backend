import os
import filetype
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import cloudinary
import cloudinary.uploader
import cloudinary.api

def allowed_file(file, allowed_extensions):
    """Vérifie si le fichier a une extension autorisée et un type MIME d'image."""
    # Vérification de l'extension
    has_valid_extension = '.' in file.filename and \
                          file.filename.rsplit('.', 1)[1].lower() in allowed_extensions
    if not has_valid_extension:
        return False

    # Vérification du type MIME avec filetype
    file.seek(0)
    header = file.read(261)
    kind = filetype.guess(header)
    file.seek(0)

    if kind is None:
        return False

    return kind.mime.startswith('image/')

def save_image(file, upload_folder=None, image_size=(400, 400)):
    """Traite et sauvegarde une image uploadée sur Cloudinary et retourne son URL."""
    public_id = f"{uuid.uuid4()}"
    upload_result = cloudinary.uploader.upload(file.stream, 
                                                public_id=public_id, 
                                                folder="ousfa_ecommerce",
                                                resource_type="image")
    return upload_result['secure_url']

def delete_image_from_cloudinary(image_url):
    """Supprime une image de Cloudinary en utilisant son URL."""
    if not image_url or 'cloudinary' not in image_url:
        return # Ce n'est pas une URL Cloudinary

    try:
        # Extrait le public_id de l'URL
        # Exemple: https://res.cloudinary.com/demo/image/upload/v12345/ousfa_ecommerce/public_id.jpg
        parts = image_url.split('/')
        upload_index = parts.index('upload')
        public_id_with_ext = '/'.join(parts[upload_index+2:])
        public_id = os.path.splitext(public_id_with_ext)[0]
        
        # Supprime l'image de Cloudinary
        cloudinary.api.delete_resources([public_id], resource_type="image")
    except Exception as e:
        # On ne veut pas que l'application plante si la suppression échoue
        print(f"Erreur lors de la suppression de l'image {image_url} sur Cloudinary: {e}")
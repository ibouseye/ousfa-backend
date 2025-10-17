import os
import filetype
import uuid
from werkzeug.utils import secure_filename
from PIL import Image

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

def save_image(file, upload_folder, image_size=(400, 400)):
    """Traite et sauvegarde une image uploadée avec un nom de fichier unique."""
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(upload_folder, unique_filename)

    img = Image.open(file)
    img.thumbnail(image_size)

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    img.save(filepath)
    return unique_filename
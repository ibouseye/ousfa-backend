import pytest
from app import db
from app.models import Product, ProductImage, Category

# Helper function to create a product with images for testing
def create_product_with_images(name="Test Product", num_images=3):
    """Helper to create a product with a category and a number of images."""
    category = Category.query.filter_by(name="Test Category").first()
    if not category:
        category = Category(name="Test Category")
        db.session.add(category)
        db.session.commit()

    product = Product(
        name=name,
        category_id=category.id,
        price=10.0,
        stock=100
    )
    db.session.add(product)
    db.session.commit()

    for i in range(num_images):
        filename = f"image_{i}.jpg"
        image = ProductImage(
            image_file=filename,
            product_id=product.id,
            position=i
        )
        db.session.add(image)
        if i == 0:
            product.image_file = filename
    
    db.session.commit()
    return product

def test_reorder_images(test_client, db):
    """
    GIVEN a product with multiple images
    WHEN the /reorder-images endpoint is called with a new order
    THEN the position of the images in the database should be updated
    """
    product = create_product_with_images(name="Reorder Product", num_images=3)
    images = sorted(product.images, key=lambda i: i.position)
    img0, img1, img2 = images

    new_order_payload = {
        "order": [
            {"id": img2.id, "position": 0},
            {"id": img0.id, "position": 1},
            {"id": img1.id, "position": 2},
        ]
    }
    response = test_client.post(
        f'/admin/product/{product.id}/reorder-images',
        json=new_order_payload
    )
    assert response.status_code == 200
    assert response.json['success'] is True

    db.session.refresh(img0)
    db.session.refresh(img1)
    db.session.refresh(img2)

    assert img2.position == 0
    assert img0.position == 1
    assert img1.position == 2

def test_set_main_image(test_client, db):
    """
    GIVEN a product with multiple images
    WHEN the /set-main-image endpoint is called for a different image
    THEN the product's main image file should be updated in the database
    """
    product = create_product_with_images(name="SetMain Product", num_images=2)
    images = sorted(product.images, key=lambda i: i.position)
    img0, img1 = images
    assert product.image_file == img0.image_file

    response = test_client.post(
        f'/admin/product/{product.id}/set-main-image/{img1.id}',
        follow_redirects=False
    )
    assert response.status_code == 302

    db.session.refresh(product)
    assert product.image_file == img1.image_file

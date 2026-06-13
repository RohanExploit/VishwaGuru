from PIL import Image, ImageOps, ExifTags
import io

def create_test_image_with_exif():
    # Create an image
    img = Image.new('RGB', (100, 50), color='red')

    # Add EXIF orientation tag (Orientation=6, Rotate 90 CW)
    exif = Image.Exif()
    exif[0x0112] = 6
    img.info['exif'] = exif.tobytes()

    return img

def test_resize_then_transpose():
    img = create_test_image_with_exif()
    print(f"Original size: {img.size}")

    # Resize
    img_resized = img.resize((50, 25))
    print(f"Resized size: {img_resized.size}")

    # Check if info is preserved
    if 'exif' in img_resized.info:
        print("EXIF preserved in resized image")
    else:
        print("EXIF LOST in resized image")
        return

    # Transpose
    img_transposed = ImageOps.exif_transpose(img_resized)
    print(f"Transposed size: {img_transposed.size}")

    if img_transposed.size == (25, 50):
        print("Success: Orientation applied correctly after resize")
    else:
        print(f"Failure: Expected (25, 50) but got {img_transposed.size}")

if __name__ == "__main__":
    test_resize_then_transpose()

from PIL import Image
import pytesseract

# Tell Python where Tesseract is installed
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Open the image (make sure it is in the same folder as this script)
img = Image.open("sample.png")

# Convert image to text
text = pytesseract.image_to_string(img)

# Print the result
print("---- OCR Result ----")
print(text)

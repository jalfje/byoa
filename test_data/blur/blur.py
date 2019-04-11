from PIL import Image, ImageFilter
import os

# The path where the source thumbnails are located
source_path = "/input/images/"
# The path where the filtered thumbnails are deposited
dump_path = "/output/"

def main():

    for filename in os.listdir(source_path):
        im = Image.open(source_path + filename)

        im = im.filter(ImageFilter.BLUR)

        im.save(dump_path + filename, "JPEG")

if __name__ == "__main__":
    main()

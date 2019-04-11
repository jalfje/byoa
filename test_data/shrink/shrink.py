from PIL import Image
import os

# The path where the source thumbnails are located
source_path = "/input/images/"
# The path where the shrunken thumbnails are deposited
dump_path = "/output/"

size = 100, 100

def main():

    for filename in os.listdir(source_path):
        im = Image.open(source_path + filename)

        im.thumbnail(size)

        im.save(dump_path + filename, "JPEG")

if __name__ == "__main__":
    main()

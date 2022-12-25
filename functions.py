from PIL import Image, ImageDraw, ImageChops, ImageQt
from bricks import ColourCodes, BrickNumbers, ColourPalettes
from numpy import asarray, all, ones, int8
import os


def get_palette_pics(palettes):
    for palette in palettes:
        # Initialize variables
        name = palette[0]
        colours = palette[1]
        colour_count = int(len(colours)/3)
        multiplier = int(256 / colour_count)
        # Create new flattend palette list using given colour_palette
        # every colour multiplied so often that the created palette list contains 768 entries -> 256 rgb values
        new_palette = sum([colours[i:i+3] * multiplier for i in range(0, len(colours), 3)], [])
        # Create new image with 256 pixels (size -> 16*16)
        palette_image = Image.new('P', (16, 16))
        palette_image.putpalette(new_palette)
        # Create RGB Colour list
        plist = palette_image.getpalette()
        clist = [plist[i:i+3] for i in range(0, 768, 3)]
        # Paint created image with palette colours
        counter = 0
        for w in range(16):
            for h in range(16):
                palette_image.putpixel((w, h), tuple(clist[counter]))
                counter += 1
        # Save Image used for converting later on
        palette_image = palette_image.rotate(270)
        palette_image.save(f'graphics/{name}.png')
        # Save preview image
        preview_image = palette_image.resize((260, 100))
        preview_image.save(f'graphics/{name}_preview.png')


def Create_Brick_Image(source_filename, palette_filename, brickpic_size):
    # Opening image files
    image = Image.open(source_filename)
    palette_image = Image.open(palette_filename)
    # Resizing
    width, height = brickpic_size
    image = image.resize(brickpic_size, resample=0)
    # Reducing image colors
    image = image.quantize(palette=palette_image, dither=0)
    # Creating preview image
    preview = image.resize((width * 16, height * 16), resample=0)
    # Creating dots image
    dot = Image.new('RGBA', (16, 16))
    draw = ImageDraw.Draw(dot)
    draw.rectangle((0, 0, 16, 16), fill=(255, 255, 255))
    draw.ellipse((3, 3, 12, 12), fill=(220, 220, 220))
    dots = Image.new('RGBA', (width * 16, height*16))
    for i in range(0, width * 16, 16):
        for j in range(0, height*16, 16):
            dots.paste(dot, (i, j))
    # Combining dots image with preview image and saving
    preview = ImageChops.multiply(preview.convert('RGB'), dots.convert('RGB'))
    preview.save('graphics/brickpic_preview.png')
    # Flipping the image horizontal and saving
    image = image.convert('RGB')
    image.save('graphics/brickpic.png')

    qim = ImageQt.ImageQt(preview)

    return qim


def get_array_from_image(source_filename):
    image = Image.open(source_filename)
    pixarray = asarray(image)
    image.close()
    return pixarray


def get_sliced_array(source, start, size):
    startr, startc = start
    return source[startr:startr+size[0], startc:startc+size[1]]


def get_max_block_list(array_size, array_list):
    r, c = array_size
    return [x for x in array_list if x[0] <= r and x[1] <= c]


def get_biggest_possible_array(arr, block_list):
    rows, cols, _ = arr.shape
    max_block_list = get_max_block_list((rows, cols), block_list)
    maxr = max(max_block_list, key=lambda item: item[0])[0]
    maxc = max(max_block_list, key=lambda item: item[1])[1]
    return arr[0:maxr, 0:maxc]


def set_part_bool_array_to_zero(bool_array, pos, block):
    bool_array[pos[0]:pos[0]+block[0], pos[1]:pos[1]+block[1]] = 0
    return bool_array


def get_biggest_block(part_array, block_list):
    blist = []
    for a in block_list:
        sliced = get_sliced_array(part_array, (0, 0), a)
        if all(sliced == sliced[0, 0]):
            blist.append(a)
    return sorted(blist, reverse=True)[0]


def get_steine_liste_mit_pos(arr, block_list):
    w, h, _ = arr.shape
    y = ones(shape=(w, h), dtype=int8)
    block_liste = []
    rows, cols = w, h
    for i in range(rows):
        for j in range(cols):
            if y[i, j] == 1:
                sliced = arr[i:rows, j:cols]
                bpa = get_biggest_possible_array(sliced, block_list)
                wi, he, _ = bpa.shape
                mbl = get_max_block_list((wi, he), block_list)
                bb = get_biggest_block(bpa, mbl)
                block_liste.append([(i, j), bb, tuple(bpa[0, 0])])
                y = set_part_bool_array_to_zero(y, (i, j), bb)
    return block_liste


def get_counted_duplicates_list(input_list):
    count_list = []
    for element in input_list:
        new_count = [input_list.count(element), element]
        if count_list.count(new_count) >= 1:
            continue
        else:
            count_list.append(new_count)
    result = [[e[0], e[1][0], e[1][1]] for e in count_list]
    return result


def get_shopping_list(brickliste):
    new_list = [[tuple(sorted(e[1])), e[2]] for e in brickliste]
    new_list = sorted(new_list, key=lambda e: (e[0], e[1]))
    new_list = get_counted_duplicates_list(new_list)
    return [[e[0], f'{e[1][0]}x{e[1][1]}', BrickNumbers[f'{e[1][0]}x{e[1][1]}'], ColourCodes[e[2]][0], ColourCodes[e[2]][2], ColourCodes[e[2]][1]] for e in new_list]


def SaveBrickPicAs(newname, picformat):
    brickpic = Image.open('graphics/brickpic_preview.png')
    root, fn = os.path.split(newname)
    fn = fn.split('.')[0]
    ext = picformat.split("*")[1][: 4]
    sfn = root+'/'+fn+ext
    pf = picformat[:4].strip()
    brickpic.save(sfn, format=pf)


def main():
    get_palette_pics(ColourPalettes)


if __name__ == '__main__':
    main()

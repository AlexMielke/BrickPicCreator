from PIL import Image, ImageDraw, ImageChops, ImageQt, ImageFont
from bricks import ColourCodes, BrickNumbers, ColourPalettes, ColourNumber2RGB
from numpy import asarray, all, ones, int8
from fpdf import FPDF
import os
from datetime import date


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
    #image = ImageOps.flip(image)
    image = image.convert('RGB')
    image.save('graphics/brickpic.png')
    return ImageQt.ImageQt(preview)


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


def get_biggest_block(part_array, block_list, bool_array_part):
    blist = []
    for a in block_list:
        sliced = get_sliced_array(part_array, (0, 0), a)
        boolsliced = get_sliced_array(bool_array_part, (0, 0), a)
        if all(sliced == sliced[0, 0]) and all(boolsliced == boolsliced[0, 0]):
            blist.append(a)
    bb = sorted(blist, reverse=True)[0]
    return bb


def get_steine_liste_mit_pos(arr, block_list):
    w, h, _ = arr.shape
    y = ones(shape=(w, h), dtype=int8)
    block_liste = []
    rows, cols = w, h
    for i in range(rows):
        for j in range(cols):
            if y[i, j] == 1:
                sliced = arr[i:rows, j:cols]
                boolsliced = y[i:rows, j:cols]
                bpa = get_biggest_possible_array(sliced, block_list)
                wi, he, _ = bpa.shape
                mbl = get_max_block_list((wi, he), block_list)
                bb = get_biggest_block(bpa, mbl, boolsliced)

                block_liste.append([(j, i), (bb[1], bb[0]), tuple(bpa[0, 0])])
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


def get_ManualImage(w, h, l):
    blocksize = 30
    im = Image.new(mode='RGB', size=(h*blocksize, w*blocksize), color=(255, 255, 255))
    font = ImageFont.truetype(r'fonts/OpenSans-Bold.ttf', 12)
    img = ImageDraw.Draw(im)
    for e in l:
        px, py, dx, dy = e[0][0], e[0][1], e[1][0], e[1][1]
        c = e[2]
        img.rectangle([px*blocksize + 2, py*blocksize + 2, px*blocksize + (blocksize*dx) - 2, py*blocksize + (blocksize*dy) - 2], fill=c, outline=(0, 0, 0))
        img.text((px*blocksize + (blocksize // 2), py*blocksize + (blocksize // 2)), str(e[3]), fill=(255-c[0], 255-c[1], 255-c[2]), font=font, anchor='mm')
    im.save('test.png')
    return ImageQt.ImageQt(im)


def ResizeImageKeepAspectRation(filename, width, resized_filename):
    img = Image.open(filename)
    aspectratio = (width / float(img.size[0]))
    height = int((float(img.size[1]) * float(aspectratio)))
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    img.save(resized_filename)
    img.close()


def SaveListAsPDF(l, filename, rastersize):
    cols = [20, 31, 49, 67, 81, 90, 140]
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_author('Alexander Mielke')
    pdf.set_title('BrickPicCreator - Benötigte Steine')
    pdf.set_creator('BrickPicCreator')
    today = date.today().strftime("%d.%m.%Y")
    # Create title page
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=44)
    pdf.set_text_color(0, 120, 150)
    pdf.text(45, 36, 'BrickPicCreator')
    pdf.set_font("Arial", style='', size=8)
    pdf.set_text_color(0, 120, 120)
    pdf.text(130, 40, '©2022 Alexander Mielke')
    pdf.set_font("Arial", style='', size=20)
    pdf.set_text_color(0, 0, 90)
    pdf.text(78, 200, 'Klemmsteinliste')
    pdf.set_font("Arial", style='', size=16)
    pdf.set_text_color(0, 0, 0)
    summe = sum([e[0] for e in l])
    anzahl_steinarten = len(set([e[1] for e in l]))
    anzahl_farben = len(set([e[3] for e in l]))
    pdf.text(20, 220, f'Klemmsteinbildgröße    : {rastersize}')
    pdf.text(20, 230, f'Anzahl der Klemmsteine : {summe}')
    pdf.text(20, 240, f'Anzahl versch. Steine  : {anzahl_steinarten}')
    pdf.text(20, 250, f'Anzahl versch. Farben  : {anzahl_farben}')
    pdf.text(20, 278, f'Erstelldatum : {today}')
    ResizeImageKeepAspectRation('graphics/brickpic_preview.png', 380, 'graphics/pdf_image.png')
    pdf.image('graphics/pdf_image.png', 36, 50)
    # Create Page(s) with Table/List
    margin = (4, 39)
    for zeile, e in enumerate(l):
        line = zeile % (margin[1]-margin[0])
        if line == 0:
            pdf.add_page()
            pdf.set_draw_color(0, 0, 0)
            pdf.set_fill_color(210, 210, 215)
            pdf.rect(15, 17, 180, 9, style='DF')
            pdf.set_font("Arial", size=12)
            pdf.set_text_color(0, 0, 0)
            pdf.text(cols[0]-3, 23, 'Anz.')
            pdf.text(cols[1], 23, 'Maße')
            pdf.text(cols[2]-2, 23, 'Art.-Nr.')
            pdf.text(cols[4]-2, 23, 'Nr.')
            pdf.text(cols[5], 23, 'Farbname Deutsch')
            pdf.text(cols[6], 23, 'Farbname Englisch')
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(0, 0, 200)
            pdf.text(180, 280, f'Seite {pdf.page_no()}')
        r, g, b = ColourNumber2RGB[e[3]]
        pdf.set_font("Arial", size=11)
        pdf.set_text_color(0, 0, 0)
        pdf.set_draw_color(0, 0, 0)
        pdf.set_fill_color(r=r, g=g, b=b)
        pdf.rect(cols[3], (line+margin[0])*7+1, 5, 5, style='DF')
        m = len(str(e[3]))
        pdf.text(cols[0], (line+margin[0])*7+5, f'{e[0]}')
        pdf.text(cols[1], (line+margin[0])*7+5, f'{e[1]}')
        pdf.text(cols[2], (line+margin[0])*7+5, f'{e[2]}')
        pdf.text(cols[4]-m, (line+margin[0])*7+5, f'{e[3]}')
        pdf.text(cols[5], (line+margin[0])*7+5, f'{e[4]}')
        pdf.text(cols[6], (line+margin[0])*7+5, f'{e[5]}')
    # Save created PDF file
    pdf.output(filename)


def SaveManualImage(pixmap, filename):
    image = Image.fromqpixmap(pixmap)
    image.save(filename)


def main():
    # get_palette_pics(ColourPalettes)
    # SaveListAsPDF(ml+ml, 'test.pdf')
    pass


if __name__ == '__main__':
    main()

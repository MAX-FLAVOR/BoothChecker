from PIL import Image, ImageFont, ImageDraw

# TODO: WHAT HAPPENED WHEN FONT FILE DOES NOT EXIST?!?!?!?!?
font = ImageFont.truetype('NanumSquareNeo-bRg.ttf', size=16)
font_color = 'rgb(255, 255, 255)'

def font_init(font_filename, size):
    global font
    font = ImageFont.truetype(font_filename, size)

def print_img(img, current_string):
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), current_string, font=font, fill=font_color)
    

def make_image(x, y):
    image = Image.new('RGB', (x, y), color = 'rgb(54, 57, 63)')
    return image


def get_offset(level, count):
    x_offset = 64 * level
    y_offset = 20 * count
    return (x_offset, y_offset)
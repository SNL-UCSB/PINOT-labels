import sys
import os
import argparse
import qrcode
from PIL import Image, ImageDraw, ImageFont

# Changeable variables
DEFAULT_FONT = "./resources/UbuntuMono-Regular.ttf"
IMG_GENERATION_SHAPE = 600, 600
IMG_RESULT_SHAPE = 590, 590
IMG_TEMPLATE = "./resources/US-10.png"  # Use US-10.png to fit the result and Empty for printing

WEB_URL = "pinot.cs.ucsb.edu"
WEB_URL_FONT_SIZE = 62
WEB_URL_SHAPE = 541, 90
WEB_URL_COORDS = 39, 411

PROJECT_NAME = "PINOT"
PROJECT_FONT_SIZE = 120
PROJECT_NAME_SHAPE = 300, 126
PROJECT_NAME_COORDS = 20, 20

LABEL_FONT_SIZE = 62
LABEL_SHAPE = 541, 90
LABEL_COORDS = 39, 473
LABEL2_COORDS = 39, 543

QR_CODE_TEMPLATE = "https://pinot.cs.ucsb.edu/devices/{}"
QR_SHAPE = 380, 380
QR_COORDS = 174, 25

ICO_FILE = "./resources/pinot_ico.png"
ICO_SHAPE = 80, 116
ICO_COORDS = 37, 327

FILL_COLOR = (0, 0, 0, 0)  # transparent
MAIN_COLOR = "black"  ##(0, 0, 0, 1)    # black
# End of changeable variables


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="""
        Label generator for PINOT project.
        The generator awaits a list of device identifiers and generate 
        a label for each device. The labels are generated for TownStix US-10 paper,
        designed to be 2 devices per one label. 
        
        """)

    parser.add_argument("-i", "--input", help="Input file with a label on each row", required=True)
    parser.add_argument("-o", "--output", help="Output folder", default="output")
    args = parser.parse_args(args)
    return args


def generate_qr_code(device_id: str) -> Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=0,
    )

    data = QR_CODE_TEMPLATE.format(device_id)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(
        fill_color=MAIN_COLOR,
        # see damn code of PilImage.new_image and how they set mode for new Image
        back_color="transparent" if FILL_COLOR == (0, 0, 0, 0) else FILL_COLOR
    )
    return img._img.resize(QR_SHAPE)


def generate_label(device_id: str) -> Image:
    # main canvas
    template = Image.new("RGBA", IMG_GENERATION_SHAPE, FILL_COLOR)

    # qr code
    qr_code = generate_qr_code(device_id)
    template.paste(qr_code, QR_COORDS, mask=qr_code)

    def text_generator(shape: tuple, text: str, font_size: int):
        img = Image.new("RGBA", shape, FILL_COLOR)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(DEFAULT_FONT, font_size)
        draw.text((0, 0), text, font=font, fill=MAIN_COLOR)
        return img

    # project name
    project_name_img = text_generator(PROJECT_NAME_SHAPE, PROJECT_NAME, PROJECT_FONT_SIZE)
    project_name_img = project_name_img.rotate(-90, expand=True)
    template.paste(project_name_img, PROJECT_NAME_COORDS, mask=project_name_img)

    # web url
    web_url_img = text_generator(WEB_URL_SHAPE, WEB_URL, WEB_URL_FONT_SIZE)
    template.paste(web_url_img, WEB_URL_COORDS, mask=web_url_img)

    # device id
    device_id_img = text_generator(LABEL_SHAPE, device_id, LABEL_FONT_SIZE)
    template.paste(device_id_img, LABEL_COORDS, mask=device_id_img)  # to be located on the cap
    template.paste(device_id_img, LABEL2_COORDS, mask=device_id_img)  # to be located on the device


    # ico image
    ico = Image.open(ICO_FILE)
    ico = ico.resize(ICO_SHAPE)
    ico = ico.rotate(-90, expand=True)
    template.paste(ico, ICO_COORDS, mask=ico)

    return template.resize(IMG_RESULT_SHAPE)


def generate_lists(labels: list[Image]) -> list[Image]:
    label_reference_points = [
        (655, 747),  (1896, 747),
        (655, 1348), (1896, 1348),
        (655, 1949), (1896, 1949),
        (655, 2550), (1896, 2550),
        (655, 3151), (1896, 3151),
    ]

    lists = [
        Image.open(IMG_TEMPLATE)
        for _ in range((len(labels) // 20) + (len(labels) % 20 != 0))
    ]

    flip = False
    for i, label in enumerate(labels):
        rotation = -90 if flip else 90
        shift = 0 if flip else -IMG_GENERATION_SHAPE[0]

        label = label.rotate(rotation, expand=True)
        reference_point = label_reference_points[(i // 2) % len(label_reference_points)]
        reference_point = (reference_point[0] + shift, reference_point[1] - IMG_GENERATION_SHAPE[1])
        lists[i // 20].paste(label, reference_point, mask=label)

        flip = not flip

    return lists


def save_lists(lists: list[Image], output_folder: str):
    for i, img in enumerate(lists):
        img.save(os.path.join(output_folder, "list_{}.png".format(i)))


def main():
    args = parse_args(sys.argv[1:])
    with open(args.input, "r") as f:
        dev_ids = f.readlines()
    dev_ids = [x.strip() for x in dev_ids if x.strip()]
    labels = [generate_label(x) for x in dev_ids]
    lists = generate_lists(labels)
    save_lists(lists, args.output)


if __name__ == '__main__':
    main()

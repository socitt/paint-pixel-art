"""
image -> Pixel Art Converter

Examples:

    python pixelate.py photo.jpg

    python pixelate.py photo.jpg --size 32

    python pixelate.py photo.jpg --size 32 --colors 16

    python pixelate.py photo.jpg --size 32 --colors 16 --output my_pixel_art.png

The script:
    1. Loads the input image.
    2. Reduces it to the requested pixel density.
    3. Reduces the image to the requested maximum number of colors.
    4. Enlarges it back up using nearest-neighbor scaling.
    5. Saves the pixel-art image.
    6. Creates a palette.txt file containing the colors used.
    7. Creates a palette.json file containing exact RGB/HEX values.
"""

import sys
import subprocess
import importlib.util


# ------------------------------------------------------------
# Automatically install Pillow if necessary
# ------------------------------------------------------------

def ensure_pillow():
    if importlib.util.find_spec("PIL") is not None:
        return

    print("Pillow is not installed.")
    print("Installing Pillow...")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "Pillow"]
        )
    except subprocess.CalledProcessError:
        print()
        print("Could not install Pillow automatically.")
        print("Try:")
        print()
        print("    python -m pip install Pillow")
        print()
        sys.exit(1)


ensure_pillow()

from PIL import Image


# ------------------------------------------------------------
# Named color database
# ------------------------------------------------------------

COLOR_NAMES = {
    "Black": (0, 0, 0),
    "White": (255, 255, 255),

    "Dark Gray": (64, 64, 64),
    "Gray": (128, 128, 128),
    "Light Gray": (192, 192, 192),

    "Dark Red": (128, 0, 0),
    "Red": (255, 0, 0),
    "Light Red": (255, 102, 102),

    "Dark Orange": (180, 80, 0),
    "Orange": (255, 165, 0),
    "Light Orange": (255, 200, 120),

    "Dark Yellow": (180, 160, 0),
    "Yellow": (255, 255, 0),
    "Light Yellow": (255, 255, 150),

    "Dark Green": (0, 100, 0),
    "Green": (0, 128, 0),
    "Light Green": (100, 200, 100),

    "Dark Cyan": (0, 128, 128),
    "Cyan": (0, 255, 255),
    "Light Cyan": (150, 255, 255),

    "Dark Blue": (0, 0, 128),
    "Blue": (0, 0, 255),
    "Light Blue": (100, 160, 255),

    "Dark Purple": (75, 0, 130),
    "Purple": (128, 0, 128),
    "Light Purple": (190, 130, 220),

    "Dark Pink": (180, 0, 90),
    "Pink": (255, 105, 180),
    "Light Pink": (255, 180, 210),

    "Dark Brown": (90, 45, 20),
    "Brown": (165, 100, 55),
    "Light Brown": (210, 160, 110),

    "Navy": (0, 0, 70),
    "Olive": (128, 128, 0),
    "Lime": (128, 255, 0),
    "Teal": (0, 128, 128),
    "Turquoise": (64, 224, 208),

    "Gold": (255, 215, 0),
    "Silver": (192, 192, 192),
    "Beige": (245, 245, 220),
    "Cream": (255, 253, 208),

    "Maroon": (128, 0, 0),
    "Violet": (238, 130, 238),
    "Indigo": (75, 0, 130),
}


# ------------------------------------------------------------
# Color utilities
# ------------------------------------------------------------

def color_distance(c1, c2):
    """
    Euclidean RGB distance.

    Good enough for assigning a human-readable name to
    a generated palette color.
    """

    r1, g1, b1 = c1
    r2, g2, b2 = c2

    return (
        (r1 - r2) ** 2
        + (g1 - g2) ** 2
        + (b1 - b2) ** 2
    )


def nearest_color_name(rgb):
    """
    Find the closest human-readable color name.
    """

    best_name = None
    best_distance = float("inf")

    for name, reference_rgb in COLOR_NAMES.items():
        distance = color_distance(rgb, reference_rgb)

        if distance < best_distance:
            best_distance = distance
            best_name = name

    return best_name


def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(
        rgb[0],
        rgb[1],
        rgb[2],
    )


# ------------------------------------------------------------
# Argument parsing
# ------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert an image into pixel art with a limited color palette."
    )

    parser.add_argument(
        "input",
        help="Input image file."
    )

    parser.add_argument(
        "--size",
        type=int,
        default=32,
        help=(
            "Pixel-art density. The longest dimension will be this many "
            "pixels while preserving aspect ratio. Default: 32"
        ),
    )

    parser.add_argument(
        "--colors",
        type=int,
        default=16,
        help=(
            "Maximum number of colors. Default: 16"
        ),
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Output PNG filename. Default: automatically generated."
    )

    parser.add_argument(
        "--scale",
        type=int,
        default=16,
        help=(
            "How large each final pixel should be. "
            "Default: 16"
        ),
    )

    return parser.parse_args()


# ------------------------------------------------------------
# Main conversion
# ------------------------------------------------------------

def create_pixel_art(input_path, pixel_size, max_colors, output_path, scale):
    input_path = Path(input_path)

    if not input_path.exists():
        print()
        print(f"ERROR: File not found: {input_path}")
        print()
        sys.exit(1)

    if pixel_size < 1:
        print("ERROR: --size must be at least 1.")
        sys.exit(1)

    if max_colors < 2:
        print("ERROR: --colors must be at least 2.")
        sys.exit(1)

    if max_colors > 256:
        print("ERROR: --colors cannot be greater than 256.")
        sys.exit(1)

    if scale < 1:
        print("ERROR: --scale must be at least 1.")
        sys.exit(1)

    print()
    print("Loading image...")

    try:
        image = Image.open(input_path)
    except Exception as exc:
        print()
        print(f"ERROR: Could not open image:")
        print(exc)
        sys.exit(1)

    # Convert everything to RGB.
    # This also handles PNGs with transparency.
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        background.alpha_composite(image.convert("RGBA"))
        image = background.convert("RGB")
    else:
        image = image.convert("RGB")

    original_width, original_height = image.size

    print(f"Original size: {original_width} x {original_height}")

    # --------------------------------------------------------
    # Determine pixel-art dimensions.
    #
    # The longest side becomes --size.
    # Aspect ratio is preserved.
    # --------------------------------------------------------

    if original_width >= original_height:
        small_width = pixel_size
        small_height = max(
            1,
            round(original_height * pixel_size / original_width)
        )
    else:
        small_height = pixel_size
        small_width = max(
            1,
            round(original_width * pixel_size / original_height)
        )

    print(f"Pixel-art size: {small_width} x {small_height}")

    # --------------------------------------------------------
    # Reduce image.
    #
    # LANCZOS gives us a representative average before
    # quantization. The final enlargement is nearest-neighbor.
    # --------------------------------------------------------

    print("Reducing image...")

    small = image.resize(
        (small_width, small_height),
        Image.Resampling.LANCZOS,
    )

    # --------------------------------------------------------
    # Quantize colors.
    #
    # Pillow's MEDIANCUT algorithm creates a palette based
    # on the actual colors in the image.
    # --------------------------------------------------------

    print(f"Reducing palette to at most {max_colors} colors...")

    quantized = small.quantize(
        colors=max_colors,
        method=Image.Quantize.MEDIANCUT,
    )

    small_rgb = quantized.convert("RGB")

    # --------------------------------------------------------
        # --------------------------------------------------------

    # Extract the exact colors actually used.

    # --------------------------------------------------------

    color_counts = {}

    for pixel in small_rgb.getdata():

        color_counts[pixel] = color_counts.get(pixel, 0) + 1

    # Sort colors by how many pixels use them.

    colors_sorted = sorted(

        color_counts.items(),

        key=lambda item: item[1],

        reverse=True,

    )

    # --------------------------------------------------------

    # Scale back up.

    #

    # NEAREST keeps every pixel perfectly square and sharp.

    # --------------------------------------------------------

    final_width = small_width * scale

    final_height = small_height * scale

    pixel_art = small_rgb.resize(

        (final_width, final_height),

        Image.Resampling.NEAREST,

    )

    # --------------------------------------------------------

    # Determine output filename.

    # --------------------------------------------------------

    if output_path is None:

        output_path = (

            input_path.parent

            / f"{input_path.stem}_{small_width}x{small_height}_{max_colors}colors.png"

        )

    else:

        output_path = Path(output_path)

    output_path.parent.mkdir(

        parents=True,

        exist_ok=True,

    )

    # --------------------------------------------------------

    # Save image.

    # --------------------------------------------------------

    pixel_art.save(

        output_path,

        "PNG",

    )

    # --------------------------------------------------------

    # Save palette files.

    # --------------------------------------------------------

    palette_base = output_path.with_suffix("")

    txt_path = Path(

        str(palette_base) + "_palette.txt"

    )

    json_path = Path(

        str(palette_base) + "_palette.json"

    )

    palette_data = []

    for index, (rgb, count) in enumerate(colors_sorted, start=1):

        name = nearest_color_name(rgb)

        hex_value = rgb_to_hex(rgb)

        percentage = (

            count / (small_width * small_height)

        ) * 100

        palette_data.append({

            "index": index,

            "name": name,

            "rgb": {

                "r": rgb[0],

                "g": rgb[1],

                "b": rgb[2],

            },

            "hex": hex_value,

            "pixels": count,

            "percentage": round(percentage, 2),

        })

    # --------------------------------------------------------

    # Human-readable palette.txt

    # --------------------------------------------------------

    with open(

        txt_path,

        "w",

        encoding="utf-8",

    ) as file:

        file.write("PIXEL ART PALETTE\n")

        file.write("=================\n\n")

        file.write(f"Source: {input_path.name}\n")

        file.write(

            f"Pixel dimensions: {small_width} x {small_height}\n"

        )

        file.write(

            f"Maximum colors: {max_colors}\n"

        )

        file.write(

            f"Actual colors: {len(colors_sorted)}\n"

        )

        file.write("\n")

        for item in palette_data:

            file.write(

                f"{item['index']:>2}. "

                f"{item['name']:<15} "

                f"{item['hex']}   "

                f"RGB({item['rgb']['r']}, "

                f"{item['rgb']['g']}, "

                f"{item['rgb']['b']})   "

                f"{item['percentage']:.2f}%\n"

            )

    # --------------------------------------------------------

    # Machine-readable JSON

    # --------------------------------------------------------

    json_data = {
        "source": input_path.name,
        "original_size": {
            "width": original_width,
            "height": original_height,
        },
        "pixel_art_size": {
            "width": small_width,
            "height": small_height,
        },
        "scale": scale,
        "maximum_colors": max_colors,
        "actual_colors": len(colors_sorted),
        "palette": palette_data,
    }

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            json_data,
            file,
            indent=4,
        )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)

    print()
    print(f"Pixel art:")
    print(f"  {output_path}")

    print()
    print(f"Palette:")
    print(f"  {txt_path}")

    print()
    print(f"Palette JSON:")
    print(f"  {json_path}")

    print()
    print(
        f"Actual colors used: {len(colors_sorted)}"
    )

    print()
    print("Colors:")

    for item in palette_data:
        print(
            f"  {item['index']:>2}. "
            f"{item['name']:<15} "
            f"{item['hex']}"
        )

    print()


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------

def main():
    args = parse_arguments()

    create_pixel_art(
        input_path=args.input,
        pixel_size=args.size,
        max_colors=args.colors,
        output_path=args.output,
        scale=args.scale,
    )


if __name__ == "__main__":
    main()


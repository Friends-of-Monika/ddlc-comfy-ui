################################################################################
#
# Copyright (c) 2020–2021 Dominus Iniquitatis <zerosaiko@gmail.com>
#
# See LICENSE file for the licensing information
#
################################################################################

################################################################################
# Configuration variables
################################################################################
release_mode = False

theme_dir  = "Themes"
source_dir = "Source"
build_dir  = "Build"

mod_dirs = [
    "common",

    # NOTE: uncomment for MAS support
    #"mas",
]

glitched_boxes = [
    "textbox_monika.png",
    "textbox_monika_d.png",
]

################################################################################
# Script itself
################################################################################
import json
import itertools
import os
import re
import shutil
from subprocess import Popen, PIPE, STDOUT

from PIL import Image
from hsluv import *

# Text file preprocessing
def clamp(value, lower, upper):
    return min(max(value, lower), upper)

def format_rgb_hex_string(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def format_rgba_hex_string(r, g, b, a):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}{int(a):02x}"

def modulate_rgb_color(r, g, b, h, s, l):
    r = float(r) / 255.0
    g = float(g) / 255.0
    b = float(b) / 255.0

    ch, cs, cl = rgb_to_hsluv((r, g, b))
    r, g, b = hsluv_to_rgb((clamp(h, 0.0, 360.0),
                            clamp(cs * s, 0.0, 100.0),
                            clamp(cl + l * 100.0, 0.0, 100.0)))

    return (int(r * 255.0),
            int(g * 255.0),
            int(b * 255.0))

def modulate_rgba_color(r, g, b, a, h, s, l):
    r = float(r) / 255.0
    g = float(b) / 255.0
    b = float(b) / 255.0
    a = float(a) / 255.0

    ch, cs, cl = rgb_to_hsluv((r, g, b))
    r, g, b = hsluv_to_rgb((clamp(h, 0.0, 360.0),
                            clamp(cs * s, 0.0, 100.0),
                            clamp(cl + l * 100.0, 0.0, 100.0)))

    return (int(r * 255.0),
            int(g * 255.0),
            int(b * 255.0),
            int(a * 255.0))

def modulate_colors(macro_args, method_args):
    h, s, l = method_args

    if len(macro_args) == 3:
        r, g, b = macro_args

        if h != None and s != None and l != None:
            r, g, b = modulate_rgb_color(int(r), int(g), int(b), float(h), float(s), float(l))

        return format_rgb_hex_string(r, g, b)

    elif len(macro_args) == 4:
        r, g, b, a = macro_args

        if h != None and s != None and l != None:
            r, g, b, a = modulate_rgba_color(int(r), int(g), int(b), int(a), float(h), float(s), float(l))

        return format_rgba_hex_string(r, g, b, a)

    return "#baadf00d"

def stringize(macro_args, method_args):
    return str(method_args)

def get_font_name(macro_args, method_args):
    # NOTE: it will work _only_ for fonts with file names matching "Name-Style.ext" pattern
    file_name = os.path.basename(method_args)
    font_name = re.match(r"(\w+)-\w+\.[ot]tf", file_name).group(1)
    return font_name

def parse_macro_args(match):
    if match.lastindex == None or match.lastindex == 0:
        # No arguments have been passed to the macro
        return []

    args_string = match.group(1)

    query = r""

    for i in range(4):
        query += r"\s*([\w\-.]+)\s*"
        result = re.findall(query, args_string)

        if len(result) > 0:
            return result

        query += r","

def preprocess_text_file(in_path, out_path, theme, scale):
    prm_color = theme["primary_color"]
    scd_color = theme["secondary_color"]

    macros = [
        # Name                       | Method         | Arguments
        [ "CUI_THEME_ID"             , stringize      , (("%s" if scale == 1 else "%s_hidpi") % theme["id"])     ],
        [ "CUI_THEME_NAME"           , stringize      , (("%s" if scale == 1 else "%s (HiDPI)") % theme["name"]) ],
        [ "CUI_BTN_ROUNDING"         , stringize      , (theme["button_rounding"])                               ],
        [ "CUI_FRM_ROUNDING"         , stringize      , (theme["frame_rounding"])                                ],
        [ "CUI_DLG_ROUNDING"         , stringize      , (theme["dialogue_rounding"])                             ],
        [ "CUI_MNU_PTSHAPE"          , stringize      , (theme["menu_pattern_shape"])                            ],
        [ "CUI_DLG_PTSHAPE"          , stringize      , (theme["dialogue_pattern_shape"])                        ],
        [ "CUI_MAIN_FONT_NAME"       , get_font_name  , (theme["main_font"]["regular"])                          ],
        [ "CUI_MAIN_FONT_REGULAR"    , stringize      , (theme["main_font"]["regular"])                          ],
        [ "CUI_MAIN_FONT_ITALIC"     , stringize      , (theme["main_font"]["italic"])                           ],
        [ "CUI_MAIN_FONT_BOLD"       , stringize      , (theme["main_font"]["bold"])                             ],
        [ "CUI_MAIN_FONT_BOLD_ITALIC", stringize      , (theme["main_font"]["bold_italic"])                      ],
        [ "CUI_MENU_FONT"            , stringize      , (theme["menu_font"])                                     ],
        [ "CUI_OPTION_FONT"          , stringize      , (theme["option_font"])                                   ],
        [ "CUI_MAIN_FONT_KERNING"    , stringize      , (theme["main_font_kerning"])                             ],
        [ "CUI_DLG_VERT_OFFSET"      , stringize      , (theme["dialogue_vertical_offset"])                      ],
        [ "CUI_DLG_LINE_SPACING"     , stringize      , (theme["dialogue_line_spacing"])                         ],
        [ "CUI_BTN_HEIGHT_ADJUSTMENT", stringize      , (theme["button_height_adjustment"])                      ],
        [ "CUI_PRM_COLOR"            , modulate_colors, (prm_color["h"], prm_color["s"], prm_color["l"])         ],
        [ "CUI_SCD_COLOR"            , modulate_colors, (scd_color["h"], scd_color["s"], scd_color["l"])         ],
        [ "CUI_SCALE"                , stringize      , (scale)                                                  ],
        [ "CUI_SCALE_INV"            , stringize      , (1.0 / scale)                                            ],
    ]

    with open(in_path, "r") as in_file, open(out_path, "w") as out_file:
        text = in_file.read()

        for macro_name, method, method_args in macros:
            query = macro_name + r"\(([\w\s\-.,]*)\)"
            text = re.sub(query, lambda match: method(parse_macro_args(match), method_args), text)

        out_file.write(text)

# Image rendering
def clear_alpha(p):
    return (p[0], p[1], p[2], 0)

def mix_pixel_glitched(l, r):
    a = min(max(int(l[3] * 0.25) + r[3],
                int(r[3] * 0.25) + l[3]), 255)
    return (r[0], r[1], r[2], a)

def shift_region(pixel_data, x, y, w, h, dx, dy):
    region_data = [[pixel_data[x + i, y + j] for j in range(h)] for i in range(w)]

    for i in range(w):
        for j in range(h):
            cx, cy = x + i, y + j
            pixel_data[cx, cy] = clear_alpha(pixel_data[cx, cy])

    for i in range(w):
        for j in range(h):
            cx, cy = x + dx + i, y + dy + j
            pixel_data[cx, cy] = mix_pixel_glitched(pixel_data[cx, cy], region_data[i][j])

def glitch(image_path, scale):
    regions = [
        # X  | Y  | W  | H  | DX | DY
        [  42,   5, 144,  15, -25,   0 ],
        [  42,  36,  41,  10,  25,   0 ],
        [  42,  62,  91,   5, -25,   0 ],
        [  42,  92,  87,   7, -25,   0 ],
        [  42, 108,  30,   4,  25,   0 ],
        [ 123, 115, 183,  20,  25,   0 ],
        [ 183,  77, 129,  22, -26,   0 ],
        [ 215,  86,  50,   1,   1,   0 ],
        [ 225,  40,  99,  20, -25,   0 ],
        [ 273,  15, 136,  11,  25,   0 ],
        [ 309,  86,  58,   1, -25,   0 ],
        [ 336,  87, 147,  28, -26,   0 ],
        [ 372,  54, 213,   4,  25,   0 ],
        [ 408,  20,  80,   3, -26,   0 ],
        [ 444,  72, 159,   6, -25,   0 ],
        [ 448, 127,  83,   9, -25,   0 ],
        [ 516,  35, 116,   6, -26,   0 ],
        [ 564,  93, 128,   3, -26,   0 ],
        [ 625,  36, 108,   8, -25,   0 ],
        [ 670, 101, 156,  12, -25,   0 ],
        [ 675,  67, 135,   9, -26,   0 ],
        [ 802,  45,  56,   2,  25,   0 ],
        [ 810,  64,  48,  15,  25,   0 ],
        [ 817,  19,  41,   2, -25,   0 ],
        [ 827,  43,  31,   6, -25,   0 ],
        [ 834, 122,  24,   7,  25,   0 ],
        [ 575, 103,  95,   1,  25,   0 ],
    ]

    with Image.open(image_path) as image:
        pixel_data = image.load()

        for region in regions:
            x, y, w, h, dx, dy = [i * scale for i in region]
            shift_region(pixel_data, x, y, w, h, dx, dy)

        image.save(image_path)

def install_fonts(fonts):
    proc = Popen("inkscape --actions=\"user-data-directory;\"", stdout = PIPE)
    stdout, _ = proc.communicate()
    proc.wait()

    inkscape_dir = stdout.decode().strip()
    inkscape_fonts_dir = os.path.join(inkscape_dir, "fonts")

    for font_path in fonts:
        shutil.copy2(font_path, inkscape_fonts_dir)

def batch_render(images, scale):
    proc = Popen("inkscape --shell", stdin = PIPE, stdout = PIPE, stderr = STDOUT, shell = True)

    cmd = ""

    for svg_path in images:
        png_path = f"{os.path.splitext(svg_path)[0]}.png"

        cmd += f"file-open:{svg_path};"
        cmd += f"export-dpi:{96 * scale};"
        cmd += f"export-filename:{png_path};"
        cmd += f"export-overwrite;"
        cmd += f"export-type:png;"
        cmd += f"export-do;"
        cmd += "\n"

    proc.communicate(input = cmd.encode(), timeout = 600)
    proc.wait()

    for svg_path in images:
        png_path = f"{os.path.splitext(svg_path)[0]}.png"

        if os.path.basename(png_path) in glitched_boxes:
            glitch(png_path, scale)

        os.remove(svg_path)

# Theme loading
def preload_themes():
    result = []

    for file_path in os.listdir(theme_dir):
        with open(os.path.join(theme_dir, file_path), "r") as theme_file:
            theme = json.load(theme_file)
            result.append(theme)

    return result

# Build chain
def log(message):
    print(f"BUILD: {message}")

def replicate_dir_structure(file_path, dst_path):
    file_dir = os.path.dirname(file_path)
    file_abs_dir = os.path.join(dst_path, file_dir)

    if not os.path.exists(file_abs_dir):
        log(f"Creating directory {file_abs_dir}...")
        os.makedirs(file_abs_dir)

def iterate_files_recursive(dir):
    for base_path, dirs, files in os.walk(dir):
        for file_path in files:
            yield os.path.join(base_path, file_path)

def copy_dir_contents(src_dir, dst_dir, theme = None, scale = None):
    fonts, images = [], []

    for file_path in iterate_files_recursive(src_dir):
        src_path = os.path.relpath(file_path, src_dir)
        dst_path = os.path.join(dst_dir, src_path)

        _, file_ext = os.path.splitext(src_path)

        replicate_dir_structure(src_path, dst_dir)

        if file_ext == ".svg" and theme and scale:
            log(f"Processing image {file_path}...")
            preprocess_text_file(file_path, dst_path, theme, scale)
            images.append(dst_path)

        elif file_ext == ".rpy" and theme and scale:
            log(f"Processing script {file_path}...")
            preprocess_text_file(file_path, dst_path, theme, scale)

        elif file_ext == ".json" and theme and scale:
            log(f"Processing JSON {file_path}...")
            preprocess_text_file(file_path, dst_path, theme, scale)

        elif file_ext in [".otf", ".ttf"]:
            log(f"Copying font {file_path}...")
            shutil.copyfile(file_path, dst_path)
            fonts.append(dst_path)

        else:
            log(f"Copying file {file_path}...")
            shutil.copyfile(file_path, dst_path)

    if len(fonts) > 0:
        log("Installing fonts...")
        install_fonts(fonts)

    if len(images) > 0:
        log("Rendering images...")
        batch_render(images, scale)

def make_archive(dir, archive_path, remove_dir = False):
    archive_name, _ = os.path.splitext(archive_path)
    shutil.make_archive(archive_name, "zip", dir)
    os.rename(f"{archive_name}.zip", archive_path)

    if remove_dir:
        shutil.rmtree(dir)

def build():
    # Clear previous build
    if os.path.exists(build_dir):
        log("Cleaning up previous build...")
        shutil.rmtree(build_dir)

    # Create build directory
    log("Creating build directory...")
    os.mkdir(build_dir)

    # Copy main files
    for mod_dir in mod_dirs:
        main_src_dir = os.path.join(source_dir, mod_dir, "main")
        copy_dir_contents(main_src_dir, build_dir)

    # Make themes
    themes = preload_themes()

    for theme, scale in itertools.product(themes, range(1, 3)):
        target_id = ("%s" if scale == 1 else "%s_hidpi") % theme["id"]
        target_dir = os.path.join(build_dir, "comfy_meta", target_id)

        for mod_dir in mod_dirs:
            theme_src_dir = os.path.join(source_dir, mod_dir, "theme")
            copy_dir_contents(theme_src_dir, target_dir, theme, scale)

        # Pack assets
        log(f"Creating archive for {target_id}...")
        make_archive(target_dir, f"{target_dir}.arc", True)

    # Create release archive if needed
    if release_mode:
        log("Creating release archive...")
        make_archive(build_dir, "Release.zip", True)

    log("Finished!")

preload_themes()
build()

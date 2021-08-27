from PIL import Image, ImageDraw, ImageFont
import os, os.path

easy_levels = 4
easy_levels_xp = 7000
xp_per_prestige = 96 * 5000 + easy_levels_xp
levels_per_prestige = 100
highest_prestige = 10
level_scale = {1: 500, 2: 1000, 3: 2500, 4: 3500}

def getXpForLevel(level):
    if level == 0:
        return 0

    respected_level = getLevelRespectingPrestige(level)

    if respected_level > easy_levels:
        return 5000
    elif respected_level == 1:
        return 500
    elif respected_level == 2:
        return 1000
    elif respected_level == 3:
        return 2000
    elif respected_level == 4:
        return 3500

def getLevelRespectingPrestige(level):
    if level > (highest_prestige * levels_per_prestige):
        return level - (highest_prestige * levels_per_prestige)
    else:
        return level % levels_per_prestige

def get_level_bedwars(xp):
    prestiges = int(xp / xp_per_prestige)
    level = prestiges * levels_per_prestige
    xp_without_prestige = xp - (prestiges * xp_per_prestige)

    for i in range(1, easy_levels + 1):
        xp_for_easy_level = getXpForLevel(i)
        if xp_without_prestige < xp_for_easy_level:
            break

        level = level + 1 
        xp_without_prestige -= xp_for_easy_level

    level_total = int(level + xp_without_prestige / 5000)
    if level_total % 100 > 4:
        xp_for_easy_level = 5000
    percentage = (level + xp_without_prestige / xp_for_easy_level) % 1.0
    return level_total, percentage

def get_level_skywars(xp):
    xps = [0, 20, 70, 150, 250, 500, 1000, 2000, 3500, 5000, 10000, 15000]
    easy_xp_skywars = 0
    for i in xps:
        easy_xp_skywars += i
    if xp >= 15000:
        level = (xp - 15000) / 10000 + 12
        percentage = level % 1.0
        return int(level), percentage
    else:
        for i in range(len(xps)):
            if xp < xps[i]:
                level = i + float(xp - xps[i-1]) / (xps[i] - xps[i-1])
                percentage = level % 1.0
                return int(level), percentage

def get_level_uhc(xp):
    pass

def create_xp_bar(size, xp, gamemode, path):
    try:
        stats_gamemode = globals()["get_level_" + str(gamemode.lower())]
        level, percentage = stats_gamemode(xp)
        im = Image.new('RGBA', size)
        draw_box = ImageDraw.Draw(im)

        x = int(size[0] / 7)
        y = int(size[1] - (size[1] / 21))
        thickness = int(size[1] / 216)
        spacing = int(size[1] / 54)
        green = "#40D433"

        y = y + spacing

        x_exp = x + ((size[0] - x * 2) * percentage)
        draw_box.line(((x, y - spacing * 0.5), (x + ((size[0] - x * 2)), y - spacing * 0.5)), fill="#9E9E9E", width=spacing)
        draw_box.line(((x, y - spacing * 0.5), (x_exp, y - spacing * 0.5)), fill=green, width=spacing)

        draw_box.line(((x, y), (size[0] - x, y)), fill=0, width=thickness)
        draw_box.line(((x, y - spacing), (size[0] - x, y - spacing)), fill=0, width=thickness)

        for i in range(0, 19):
            x_grid = x + i * ((size[0] - x * 2) / 18)
            draw_box.line(((x_grid, y), (x_grid, y - spacing)),fill=0, width=thickness)

        font_size = size[1] / 20
        font_file = [name for name in os.listdir(path + "fonts/level") if os.path.isfile(os.path.join(path + "fonts/level", name))]
        font = ImageFont.truetype(path + "fonts/level/" + font_file[0], int(font_size))
        x_text = size[0] / 2
        draw_box.text((x_text, y - spacing * 1.4), text=str(level), font=font, fill=green, anchor="mb")
    except:
        im = Image.new('RGBA', size)

    return im


from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import io
import random
import base64
from .level import create_xp_bar
import os, os.path
from itertools import zip_longest
import MinePI

async def create_img(statslist, name, datapath, uuid, gamemode, xp: int = 0, comparestats: list = [], header_color: tuple = (225,0,221), skin_b64: str = None):
    # define color of text
    COLOR_HEADER_PLAYER = tuple(header_color) if header_color != None else (225,0,221)
    COLOR_HEADER_STATS = (255,145,0)
    COLOR_BODY_STATS = (255,200,0)

    # convert b64 skin to PNG Pillow Image
    if skin_b64 != None:
        im_bytes = base64.b64decode(skin_b64)   # im_bytes is a binary image
        im_file = io.BytesIO(im_bytes)  # convert image to file-like object
        skin_image = Image.open(im_file)
    else:
        skin_image = None

    # fetch available backgrounds for randomize
    backgrounds_list = [name for name in os.listdir(datapath + "backgrounds") if os.path.isfile(os.path.join(datapath + "backgrounds", name))]

    # fetch fonts
    font_header_player_file = [name for name in os.listdir(datapath + "fonts/player_header") if os.path.isfile(os.path.join(datapath + "fonts/player_header", name))]
    font_header_stats_file = [name for name in os.listdir(datapath + "fonts/stats_header") if os.path.isfile(os.path.join(datapath + "fonts/stats_header", name))]
    font_body_stats_file = [name for name in os.listdir(datapath + "fonts/stats_body") if os.path.isfile(os.path.join(datapath + "fonts/stats_body", name))]

    # open background image and add alpha channel ('RGBA'), do some magic with brightness
    im = Image.open(datapath+"backgrounds/" + backgrounds_list[random.randint(0,len(backgrounds_list) - 1)])
    im = im.convert("RGBA")
    im = ImageEnhance.Brightness(im).enhance(0.3)

    # fetch background image size
    size_of_background = im.size

    # do some magic with blur
    im = im.filter(ImageFilter.GaussianBlur(size_of_background[0] / 300))

    # try to put a logo over the image
    try:
        logo = Image.open(datapath + "logos/logo_" + gamemode.lower() + ".png")
        logo = logo.convert("RGBA")
        size_of_logo = logo.size
        width_of_logo = size_of_background[0] / 8
        height_of_logo = width_of_logo * (size_of_logo[1] / size_of_logo[0])
        logo = logo.resize((int(width_of_logo), int(height_of_logo)), resample=Image.BOX)
        im.alpha_composite(logo,(int(size_of_background[0]-width_of_logo), int(size_of_background[1]-height_of_logo)))
    except:
        pass

    # returns the length of statslist and grabbing the half of it
    length_of_statslist = len(statslist)
    if length_of_statslist % 2 != 0:
        half_length_of_statslist = int(length_of_statslist/2)+1
    else:
        half_length_of_statslist = length_of_statslist/2

    # create font for name of the player
    FONT_SIZE_HEADER_PLAYER = int(size_of_background[1]/6.5)
    font_header_player = ImageFont.truetype((datapath+"fonts/player_header/"+font_header_player_file[0]), FONT_SIZE_HEADER_PLAYER)

    # fetch skin of player, resize it and put it over the background
    skin = await fetch_skin(uuid, skin_image)
    size_of_skin = skin.size
    height_of_skin = size_of_background[1]/1.4
    width_of_skin = height_of_skin * (size_of_skin[0] / size_of_skin[1])
    skin = skin.resize((int(width_of_skin),int(height_of_skin)),resample=Image.BOX)
    if length_of_statslist > 5:
        im.alpha_composite(skin,(int((size_of_background[0]/2)-(width_of_skin/2)),FONT_SIZE_HEADER_PLAYER+int(size_of_background[1]/200)))
    else:
        im.alpha_composite(skin,(int(size_of_background[0]-(width_of_skin*1.5)),FONT_SIZE_HEADER_PLAYER+int(size_of_background[1]/200)))

    # create draw element of the current image (background + skin)
    # you need it to write some text on it
    draw = ImageDraw.Draw(im)

    # find the longest word of the stats
    longest_word = ""
    for idx, item in statslist:
        if len(longest_word) < len(idx):
            longest_word = idx
    # returns the textsize of the longest word (just for the relations of height/width, so font_size doesnt matter)
    width_of_longestword, height_of_longestword = draw.textsize(longest_word, font=font_header_player)

    # calculating maximums of width and height
    if length_of_statslist > 5:
        max_width_of_stats = (size_of_background[0] - width_of_skin) / 2 - size_of_background[0]/200
    else:
        max_width_of_stats = size_of_background[0] - width_of_skin - size_of_background[0]/20
    max_height_of_stats = max_width_of_stats * (height_of_longestword / width_of_longestword)

    # calculating the box size of stats (header, body and space)
    if length_of_statslist > 5:
        stats_box_size = (size_of_background[1]-FONT_SIZE_HEADER_PLAYER-(size_of_background[1]/12)) / half_length_of_statslist
    else:
        stats_box_size = (size_of_background[1]-FONT_SIZE_HEADER_PLAYER-(size_of_background[1]/12)) / length_of_statslist

    # enter the relation of stats to space between stats
    relation_of_stats_to_space = 0.85
    space_stats = stats_box_size* (1 - relation_of_stats_to_space)

    # if font would be do big, resize it as often as necessary
    while max_height_of_stats + (max_height_of_stats * 0.9) + space_stats > stats_box_size:
        max_height_of_stats *= 0.95

    # create fonts and resize the space
    FONT_SIZE_HEADER_STATS = max_height_of_stats
    FONT_SIZE_BODY_STATS = max_height_of_stats * 0.9
    space_stats = stats_box_size - FONT_SIZE_HEADER_STATS - FONT_SIZE_BODY_STATS

    # create font for stats
    font_header_stats = ImageFont.truetype((datapath+"fonts/stats_header/"+font_header_stats_file[0]), int(FONT_SIZE_HEADER_STATS))
    font_body_stats = ImageFont.truetype((datapath+"fonts/stats_body/"+font_body_stats_file[0]), int(FONT_SIZE_BODY_STATS))

    # draw the player name on the image
    draw.text(((size_of_background[0]/2),size_of_background[1]/100),name,fill=COLOR_HEADER_PLAYER,font=font_header_player,anchor="mt")

    # hardcode a negative list for coloring the text
    negative_list = ['death', 'loss']

    # find longest word in left and right column
    if length_of_statslist <= 5:
        left_space = longest_word
    else:
        left_space = ""
        right_space = ""
        for idx, item in enumerate(statslist):
            if idx < half_length_of_statslist:
                if len(left_space) < len(str(item[0])):
                    left_space = str(item[0])
            else:
                if len(right_space) < len(str(item[0])):
                    right_space = str(item[0])
        else:
            left_space, _ = draw.textsize(left_space, font=font_header_stats)
            right_space, _ = draw.textsize(right_space, font=font_header_stats)
            

    # draw the stats on the image
    y = FONT_SIZE_HEADER_PLAYER + (space_stats / 2)
    x = size_of_background[0]/25
    anchor = "lt"
    compare_anchor = "rt"
    space = left_space

    for idx, (stats, compare) in enumerate(zip_longest(statslist, comparestats)):
        if (idx == half_length_of_statslist) and (length_of_statslist > 5):
            y = FONT_SIZE_HEADER_PLAYER + (space_stats / 2)
            anchor = "rt"
            compare_anchor = "lt"
            x = size_of_background[0]-(size_of_background[0]/25)
            space = -right_space
        if comparestats != []:
            cmp = str(round(compare[1], 2))
            COLOR_COMPARE_STATS = COLOR_BODY_STATS
            for entry in negative_list:
                if entry in compare[0]:
                    if compare[1] < 0:
                        COLOR_COMPARE_STATS = (0,255,0)
                        break
                    elif compare[1] > 0:
                        cmp = "+" + str(round(compare[1], 2))
                        COLOR_COMPARE_STATS = (255,0,0)
                        break
            else:
                if compare[1] > 0:
                    cmp = "+" + str(round(compare[1], 2))
                    COLOR_COMPARE_STATS = (0,255,0)
                elif compare[1] < 0:
                    COLOR_COMPARE_STATS = (255,0,0)

            draw.text(((x+space),(y+FONT_SIZE_HEADER_STATS)),cmp,fill=COLOR_COMPARE_STATS,font=font_body_stats,anchor=compare_anchor)

        draw.text((x,y),str(stats[0]),fill=COLOR_HEADER_STATS,font=font_header_stats,anchor=anchor)
        draw.text((x,y+FONT_SIZE_HEADER_STATS),str(stats[1]),fill=COLOR_BODY_STATS,font=font_body_stats,anchor=anchor)

        y += FONT_SIZE_HEADER_STATS + FONT_SIZE_BODY_STATS + space_stats

    # create a xp_bar with given experience and put it over the image
    xp_bar = create_xp_bar(size_of_background, xp, gamemode, datapath)
    im.alpha_composite(xp_bar,(0,0))

    return im

async def fetch_skin(uuid, skin):
    # list of positions for the skin renderer
    pos_list = [
        (-25, -25, 20, 5, -2, -20, 2),
        (-25, 25, 20, 5, -2, 20, -2),
        (-5, 25, 10, 5, -2, 5, -5),
        (-5, -25, 10, 5, -2, -5, 5),
        (0, 0, 0, 0, 0, 0, 0),
    ]

    # randomly take on position out of list
    pos = pos_list[random.randint(0, len(pos_list) - 1)]
    im = await MinePI.render_3d_skin(uuid, pos[0], pos[1], pos[2], pos[3], pos[4], pos[5], pos[6], ratio=100, display_hair=True, display_second_layer=True, aa=False, skin_image=skin)
    return im
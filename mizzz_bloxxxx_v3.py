import pygame
import random
import os
import sys
import numpy as np
import colorsys
import argparse
import logging
import textwrap
import time
import getpass

parser = argparse.ArgumentParser(description='Mizzz Bloxxxxx Game')
parser.add_argument('-nopixelshift', action='store_true', help='Disable smooth scaling')
parser.add_argument('-showborder', action='store_true', help='Show grid borders')
parser.add_argument('-about', action='store_true', help='Show about information')
parser.add_argument('-log', action='store_true', help='Enable logging to file')
args = parser.parse_args()

use_smooth_scaling = not args.nopixelshift
show_border = args.showborder

if args.about:
    print("mizzz bloxxxx by github.com/zeittresor")
    sys.exit()

if args.log:
    logging.basicConfig(
        filename='mizzz_bloxxxxx.log',
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s:%(message)s'
    )
    logging.debug('Logging enabled')
else:
    logging.basicConfig(level=logging.CRITICAL)

pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Mizzz Bloxxxxx")

clock = pygame.time.Clock()

GRID_SIZE = 10
MARGIN = 10
TITLE_HEIGHT = 100
COUNTER_HEIGHT = 50
SLIDER_WIDTH = 20
SLIDER_HEIGHT = 150
SLIDER_SPACING = 10

BUTTON_WIDTH = 100
BUTTON_HEIGHT = 40
BUTTON_SPACING = 10

font = pygame.font.SysFont(None, 48)
counter_font = pygame.font.SysFont(None, 36)
slider_font = pygame.font.SysFont(None, 24)
button_font = pygame.font.SysFont(None, 30)

slider_labels = ['Satuation', 'Brightness', 'Contrast', 'Colormap', 'BG Brightness', 'Transparence']
label_widths = [slider_font.size(lbl)[0] for lbl in slider_labels]
max_label_width = max(label_widths)
SLIDER_OFFSET_X = MARGIN + max_label_width + 5

BLOCK_SIZE = int(min(
    (SCREEN_WIDTH - 2*MARGIN - SLIDER_OFFSET_X - SLIDER_WIDTH - SLIDER_SPACING) / GRID_SIZE,
    (SCREEN_HEIGHT - TITLE_HEIGHT - COUNTER_HEIGHT - 2*MARGIN) / GRID_SIZE
))

BOARD_WIDTH = GRID_SIZE * BLOCK_SIZE
BOARD_HEIGHT = GRID_SIZE * BLOCK_SIZE
TOTAL_CONTENT_HEIGHT = TITLE_HEIGHT + BOARD_HEIGHT + COUNTER_HEIGHT + 2*MARGIN
BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_WIDTH) // 2
BOARD_OFFSET_Y = (SCREEN_HEIGHT - TOTAL_CONTENT_HEIGHT) // 2 + TITLE_HEIGHT + MARGIN
SLIDER_OFFSET_Y = BOARD_OFFSET_Y

BUTTON_OFFSET_X = SCREEN_WIDTH - MARGIN - BUTTON_WIDTH
BUTTON_OFFSET_Y = MARGIN

BACKGROUND_COLOR = (0, 0, 0)

COLORS = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 165, 0),
    (128, 0, 128),
    (0, 255, 255),
    (255, 192, 203)
]

DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logging.debug(f"Created directory: {DATA_DIR}")

TOP5_FILE = os.path.join(DATA_DIR, 'top5.txt')

def load_highscores():
    if not os.path.isfile(TOP5_FILE):
        return []
    highscores = []
    with open(TOP5_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            # Format: blocks ; date ; time ; spent ; user
            parts=line.split(';')
            if len(parts)==5:
                try:
                    blocks=int(parts[0].strip())
                    datum=parts[1].strip()
                    zeit=parts[2].strip()
                    spent=float(parts[3].strip())
                    user=parts[4].strip()
                    highscores.append((blocks, datum, zeit, spent, user))
                except:
                    pass
    # Sortiere nach blocks aufsteigend
    highscores.sort(key=lambda x: x[0])
    # Begrenze auf 5
    return highscores[:5]

def save_highscores(highscores):
    """Speichert die Highscore-Liste in top5.txt"""
    with open(TOP5_FILE, 'w', encoding='utf-8') as f:
        for entry in highscores:
            blocks, datum, zeit, spent, user=entry
            line=f"{blocks};{datum};{zeit};{spent:.2f};{user}\n"
            f.write(line)

def add_highscore(blocks_used, spent_time):
    hs=load_highscores()
    import datetime
    now=datetime.datetime.now()
    dat_str=now.strftime('%Y-%m-%d')
    tim_str=now.strftime('%H:%M:%S')
    user_name=getpass.getuser()  

    new_entry=(blocks_used, dat_str, tim_str, spent_time, user_name)
    hs.append(new_entry)
    hs.sort(key=lambda x: x[0])
    hs=hs[:5]  # nur 5
    save_highscores(hs)

block_images = []
images_available = True
for i in range(1, 9):
    path_img = os.path.join(DATA_DIR, f'block{i}.png')
    if os.path.isfile(path_img):
        try:
            img = pygame.image.load(path_img).convert_alpha()
            if use_smooth_scaling:
                img = pygame.transform.smoothscale(img, (BLOCK_SIZE, BLOCK_SIZE))
            else:
                img = pygame.transform.scale(img, (BLOCK_SIZE, BLOCK_SIZE))
            block_images.append(img)
            logging.debug(f'Loaded image: {path_img}')
        except Exception as e:
            logging.error(f'Error loading image {path_img}: {e}')
            images_available = False
            break
    else:
        logging.warning(f'Image file not found: {path_img}')
        images_available = False
        break
if not images_available or len(block_images) < 8:
    block_images = []

use_colors_with_images = os.path.isfile(os.path.join(DATA_DIR, 'farben.txt'))

def load_sound(sound_path):
    if os.path.isfile(sound_path):
        try:
            snd = pygame.mixer.Sound(sound_path)
            logging.debug(f'Loaded sound: {sound_path}')
            return snd
        except Exception as e:
            logging.error(f'Error loading sound {sound_path}: {e}')
            return None
    else:
        logging.warning(f'Sound file not found: {sound_path}')
        return None

match_sound = load_sound(os.path.join(DATA_DIR, 'sound1.wav'))
swap_fail_sound = load_sound(os.path.join(DATA_DIR, 'sound2.wav'))
four_match_sound = load_sound(os.path.join(DATA_DIR, 'sound3.wav'))
five_match_sound = load_sound(os.path.join(DATA_DIR, 'sound4.wav'))
hello_sound = load_sound(os.path.join(DATA_DIR, 'hello.wav'))
tschuess_sound = load_sound(os.path.join(DATA_DIR, 'tschuess.wav'))
help_sound = load_sound(os.path.join(DATA_DIR, 'hilfe.wav'))

music_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.mp3')]
music_files = [os.path.join(DATA_DIR, f) for f in music_files]
if music_files:
    logging.debug(f'Loaded music files: {music_files}')
else:
    logging.warning('No music files found')

current_music_index = 0
def play_next_music():
    global current_music_index
    if music_files:
        try:
            pygame.mixer.music.load(music_files[current_music_index])
            pygame.mixer.music.play()
            logging.debug(f'Playing music: {music_files[current_music_index]}')
            current_music_index = (current_music_index + 1) % len(music_files)
        except Exception as e:
            logging.error(f'Error playing music {music_files[current_music_index]}: {e}')

def skip_music():
    pygame.mixer.music.stop()
    play_next_music()

if music_files:
    play_next_music()

def check_music_end():
    if not pygame.mixer.music.get_busy():
        play_next_music()

clock = pygame.time.Clock()

background_image_path = os.path.join(DATA_DIR, 'background.png')
if os.path.isfile(background_image_path):
    try:
        background_image = pygame.image.load(background_image_path).convert()
        if use_smooth_scaling:
            background_image = pygame.transform.smoothscale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        logging.debug(f'Loaded background image: {background_image_path}')
    except Exception as e:
        logging.error(f'Error loading background image {background_image_path}: {e}')
        background_image = None
else:
    logging.warning(f'Background image not found: {background_image_path}')
    background_image = None

adjusted_background_image = background_image.copy() if background_image else None

shadow_offset = (3, 3)
text_surface = None
shadow_surface = None
text_rect = None

graphic_image_path = os.path.join(DATA_DIR, 'graphic.png')
if os.path.isfile(graphic_image_path):
    try:
        graphic_image = pygame.image.load(graphic_image_path).convert_alpha()
        gw = min(graphic_image.get_width(), SCREEN_WIDTH - 2*MARGIN)
        sf = gw / graphic_image.get_width()
        gh = int(graphic_image.get_height()*sf)
        if use_smooth_scaling:
            graphic_image = pygame.transform.smoothscale(graphic_image, (gw, gh))
        else:
            graphic_image = pygame.transform.scale(graphic_image, (gw, gh))
        graphic_rect = graphic_image.get_rect()
        graphic_rect.centerx = SCREEN_WIDTH // 2
        graphic_rect.bottom = BOARD_OFFSET_Y - 10
        logging.debug(f'Loaded graphic: {graphic_image_path}')
    except Exception as e:
        logging.error(f'Error loading graphic: {e}')
        graphic_image = None
else:
    graphic_image = None
    title_font = pygame.font.SysFont(None, 72)
    title_text = "Mizzz Bloxxxxx"
    text_surface = title_font.render(title_text, True, (255, 255, 255))
    shadow_surface = title_font.render(title_text, True, (0, 0, 0))

    text_rect = text_surface.get_rect()
    text_rect.centerx = SCREEN_WIDTH // 2
    text_rect.bottom = BOARD_OFFSET_Y - 10

grid = []
selected_block = None
blocks_cleared = 0
exit_prompt = False
sliders_visible = False
tip_highlight = None
showing_help = False
showing_top5 = False

saturation = 0.5
brightness = 0.5
contrast = 0.5
hue = 0.5
bg_brightness = 0.5
transparency_value = 0.5

adjusted_images_cache = {}

start_time = None

def create_grid():
    global grid, blocks_cleared
    grid = [[random.randint(0,7) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    blocks_cleared=0
    while not has_possible_moves(5):
        grid = [[random.randint(0,7) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def create_grid_lines_surface():
    global grid_lines_surface
    surf=pygame.Surface((BOARD_WIDTH,BOARD_HEIGHT),pygame.SRCALPHA)
    surf=surf.convert_alpha()
    if show_border:
        alpha_val=int(255*0.3)
        line_col=(0,0,0,alpha_val)
    else:
        alpha_val=int(255*0.1)
        line_col=(0,0,0,alpha_val)
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            rc=pygame.Rect(x*BLOCK_SIZE,y*BLOCK_SIZE,BLOCK_SIZE,BLOCK_SIZE)
            pygame.draw.rect(surf,line_col,rc,1)
    grid_lines_surface=surf

grid_lines_surface = None
create_grid_lines_surface()

def adjust_color(color):
    c=np.array(color,dtype=np.float32)/255.0
    c+=(brightness-0.5)*2
    c=np.clip(c,0,1)
    hsv=list(colorsys.rgb_to_hsv(*c))
    s_adj=(saturation-0.5)*2
    h_adj=(hue-0.5)*2
    hsv[1]+= s_adj
    hsv[1]=np.clip(hsv[1],0,1)
    hsv[0]+=h_adj
    hsv[0]%=1.0
    c=np.array(colorsys.hsv_to_rgb(*hsv))
    c_adj=(contrast-0.5)*2
    c=((c-0.5)*(c_adj+1))+0.5
    c=np.clip(c,0,1)
    return tuple((c*255).astype(int))

def adjust_image(image):
    arr=pygame.surfarray.array3d(image).astype(np.float32)/255.0
    arr+=(brightness-0.5)*2
    arr=np.clip(arr,0,1)
    r,g,b=arr[...,0],arr[...,1],arr[...,2]
    hsv=np.vectorize(colorsys.rgb_to_hsv)(r,g,b)
    h,s,v=hsv
    s+=(saturation-0.5)*2
    s=np.clip(s,0,1)
    h+=(hue-0.5)*2
    h%=1.0
    rgb=np.vectorize(colorsys.hsv_to_rgb)(h,s,v)
    arr[...,0],arr[...,1],arr[...,2]=rgb
    c_adj=(contrast-0.5)*2
    arr=((arr-0.5)*(c_adj+1))+0.5
    arr=np.clip(arr,0,1)
    new_surf=pygame.Surface(image.get_size(),pygame.SRCALPHA)
    pygame.surfarray.blit_array(new_surf,(arr*255).astype(np.uint8))
    alpha_arr=pygame.surfarray.array_alpha(image)
    pygame.surfarray.pixels_alpha(new_surf)[:]=alpha_arr
    return new_surf

def adjust_and_cache_images():
    adjusted_images_cache.clear()
    for idx, img in enumerate(block_images):
        adjusted_images_cache[idx] = adjust_image(img)

def adjust_background_image():
    global adjusted_background_image
    if background_image:
        arr=pygame.surfarray.array3d(background_image).astype(np.float32)/255.0
        arr+=(bg_brightness-0.5)*2
        arr=np.clip(arr,0,1)
        adjusted_background_image=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
        pygame.surfarray.blit_array(adjusted_background_image,(arr*255).astype(np.uint8))
    else:
        adjusted_background_image=None

def find_matches():
    matched=[]
    for y in range(GRID_SIZE):
        x=0
        while x<GRID_SIZE-2:
            mt=[(y,x)]
            bt=grid[y][x]
            if bt!=-1:
                for k in range(x+1,GRID_SIZE):
                    if grid[y][k]==bt:
                        mt.append((y,k))
                    else:
                        break
                if len(mt)>=3:
                    matched.extend(mt)
                x+=len(mt)
            else:
                x+=1
    for x in range(GRID_SIZE):
        y=0
        while y<GRID_SIZE-2:
            mt=[(y,x)]
            bt=grid[y][x]
            if bt!=-1:
                for k in range(y+1,GRID_SIZE):
                    if grid[k][x]==bt:
                        mt.append((k,x))
                    else:
                        break
                if len(mt)>=3:
                    matched.extend(mt)
                y+=len(mt)
            else:
                y+=1
    return list(set(matched))

def swap_blocks(pos1,pos2):
    y1,x1=pos1
    y2,x2=pos2
    grid[y1][x1],grid[y2][x2]=grid[y2][x2],grid[y1][x1]

def has_possible_moves(min_moves=1):
    count=0
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                ny,nx=y+dy,x+dx
                if 0<=ny<GRID_SIZE and 0<=nx<GRID_SIZE:
                    swap_blocks((y,x),(ny,nx))
                    if find_matches():
                        count+=1
                        swap_blocks((y,x),(ny,nx))
                        if count>=min_moves:
                            return True
                    else:
                        swap_blocks((y,x),(ny,nx))
    return False

def find_possible_move():
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                ny,nx=y+dy,x+dx
                if 0<=ny<GRID_SIZE and 0<=nx<GRID_SIZE:
                    swap_blocks((y,x),(ny,nx))
                    if find_matches():
                        swap_blocks((y,x),(ny,nx))
                        return [(y,x),(ny,nx)]
                    else:
                        swap_blocks((y,x),(ny,nx))
    return None

def animate_swap(pos1,pos2):
    y1,x1=pos1
    y2,x2=pos2
    xp1=BOARD_OFFSET_X+x1*BLOCK_SIZE
    yp1=BOARD_OFFSET_Y+y1*BLOCK_SIZE
    xp2=BOARD_OFFSET_X+x2*BLOCK_SIZE
    yp2=BOARD_OFFSET_Y+y2*BLOCK_SIZE

    steps=15
    swapped_positions=[pos1,pos2]
    swapped_positions_positions=[(xp1,yp1),(xp2,yp2)]
    swapped_positions_destinations=[(xp2,yp2),(xp1,yp1)]

    for i in range(steps+1):
        pr=i/steps
        draw_grid(
            swapped_positions=swapped_positions,
            swapped_positions_positions=swapped_positions_positions,
            swapped_positions_destinations=swapped_positions_destinations,
            swap_progress=pr
        )
        pygame.display.flip()
        clock.tick(60)

def animate_matches(matches):
    duration=1000
    st=pygame.time.get_ticks()
    blink_interval=duration//2
    last_blink_time=st
    blink=True

    while pygame.time.get_ticks()-st<duration:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
                sys.exit()
        now=pygame.time.get_ticks()
        if now-last_blink_time>=blink_interval:
            blink=not blink
            last_blink_time=now
        draw_grid(matched_positions=matches,blink=blink)
        pygame.display.flip()
        clock.tick(60)

def animate_falling(columns):
    falling=True
    velocities={}
    positions={}
    gravity=0.7
    while falling:
        falling=False

        if adjusted_background_image:
            screen.blit(adjusted_background_image,(0,0))
        else:
            screen.fill(BACKGROUND_COLOR)

        if graphic_image:
            screen.blit(graphic_image,graphic_rect)
        elif text_surface and shadow_surface and text_rect:
            sp=(text_rect.x+shadow_offset[0], text_rect.y+shadow_offset[1])
            screen.blit(shadow_surface,sp)
            screen.blit(text_surface,text_rect)

        c_text=f"Killed Xeno-Bug Blocks: {blocks_cleared}"
        c_s=counter_font.render(c_text,True,(255,255,255))
        sc_s=counter_font.render(c_text,True,(0,0,0))
        c_rect=c_s.get_rect()
        c_rect.centerx=SCREEN_WIDTH//2
        c_rect.top=BOARD_OFFSET_Y+BOARD_HEIGHT+10
        sofs=(2,2)
        sc_rect=c_rect.copy()
        sc_rect.x+=sofs[0]
        sc_rect.y+=sofs[1]
        screen.blit(sc_s,sc_rect)
        screen.blit(c_s,c_rect)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                bt=grid[y][x]
                if bt==-1:
                    continue
                key=(y,x)
                tx=BOARD_OFFSET_X+x*BLOCK_SIZE
                ty=BOARD_OFFSET_Y+y*BLOCK_SIZE

                if x in columns:
                    if key not in positions:
                        positions[key]=ty-BLOCK_SIZE
                        velocities[key]=0
                        falling=True
                    if positions[key]<ty:
                        velocities[key]+=gravity
                        positions[key]+= velocities[key]
                        if positions[key]>=ty:
                            positions[key]=ty
                        else:
                            falling=True
                        rect=pygame.Rect(tx,positions[key],BLOCK_SIZE,BLOCK_SIZE)
                    else:
                        rect=pygame.Rect(tx,ty,BLOCK_SIZE,BLOCK_SIZE)
                else:
                    rect=pygame.Rect(tx,ty,BLOCK_SIZE,BLOCK_SIZE)

                alpha=int(255*transparency_value)
                dark=pygame.Surface((BLOCK_SIZE,BLOCK_SIZE),pygame.SRCALPHA)
                dark.fill((0,0,0,alpha))
                screen.blit(dark,rect)

                if block_images:
                    if use_colors_with_images:
                        ac=adjust_color(COLORS[bt])
                        c_sf=pygame.Surface((BLOCK_SIZE,BLOCK_SIZE),pygame.SRCALPHA)
                        c_sf.fill(ac)
                        screen.blit(c_sf,rect)
                    adj=adjusted_images_cache.get(bt)
                    if adj:
                        screen.blit(adj,rect)
                    else:
                        screen.blit(block_images[bt],rect)
                else:
                    c=COLORS[bt]
                    ac=adjust_color(c)
                    c_sf=pygame.Surface((BLOCK_SIZE,BLOCK_SIZE),pygame.SRCALPHA)
                    c_sf.fill(ac)
                    screen.blit(c_sf,rect)

        screen.blit(grid_lines_surface,(BOARD_OFFSET_X,BOARD_OFFSET_Y))
        draw_buttons()
        if sliders_visible:
            draw_sliders()
        if showing_help:
            draw_help_panel()
        if showing_top5:
            draw_top5_panel()

        pygame.display.flip()
        clock.tick(60)

def collapse_grid():
    columns=set()
    for x in range(GRID_SIZE):
        column=[]
        for y in range(GRID_SIZE-1,-1,-1):
            if grid[y][x]!=-1:
                column.append(grid[y][x])
        missing=GRID_SIZE-len(column)
        new_blocks=[random.randint(0,7) for _ in range(missing)]
        column+=new_blocks
        column.reverse()
        for y in range(GRID_SIZE):
            grid[y][x]=column[y]
        if missing>0:
            columns.add(x)
    if columns:
        animate_falling(columns)

def no_more_moves():
    txt=font.render("Problem solved ! Another try ? (j/n)",True,(255,255,255))
    sh_txt=font.render("Problem solved ! Another try ? (j/n)",True,(0,0,0))
    retry_txt=font.render("",True,(255,255,255))  
    sh_retry=font.render("",True,(0,0,0))         

    t_rect=txt.get_rect()
    t_rect.centerx=SCREEN_WIDTH//2
    t_rect.centery=SCREEN_HEIGHT//2-50

    r_rect=retry_txt.get_rect()
    r_rect.centerx=SCREEN_WIDTH//2
    r_rect.centery=SCREEN_HEIGHT//2

    sofs=(2,2)
    s_txt_rect=t_rect.copy()
    s_txt_rect.x+=sofs[0]
    s_txt_rect.y+=sofs[1]
    s_r_rect=r_rect.copy()
    s_r_rect.x+=sofs[0]
    s_r_rect.y+=sofs[1]

    screen.blit(sh_txt,s_txt_rect)
    screen.blit(txt,t_rect)
    screen.blit(sh_retry,s_r_rect)
    screen.blit(retry_txt,r_rect)
    pygame.display.flip()

    end_time=time.time()
    spent_time=end_time - start_time
    add_highscore(blocks_cleared,spent_time)

    waiting=True
    while waiting:
        for event in pygame.event.get():
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_j:
                    create_grid()
                    waiting=False
                elif event.key==pygame.K_n:
                    fade_out_and_quit()
            elif event.type==pygame.QUIT:
                fade_out_and_quit()

def show_exit_prompt():
    ex_txt=font.render("EXit Game j/n",True,(255,255,255))
    sh_ex_txt=font.render("Exit Game j/n",True,(0,0,0))

    t_rect=ex_txt.get_rect()
    t_rect.centerx=SCREEN_WIDTH//2
    t_rect.centery=SCREEN_HEIGHT//2
    sofs=(2,2)
    sh_rect=t_rect.copy()
    sh_rect.x+=sofs[0]
    sh_rect.y+=sofs[1]

    screen.blit(sh_ex_txt,sh_rect)
    screen.blit(ex_txt,t_rect)
    pygame.display.flip()

def fade_out_and_quit():
    if tschuess_sound:
        tschuess_sound.play()
    pygame.mixer.music.fadeout(5000)
    fd_s=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    fd_s=fd_s.convert_alpha()
    for alpha in range(0,255,5):
        fd_s.fill((0,0,0,alpha))
        screen.blit(fd_s,(0,0))
        pygame.display.flip()
        pygame.time.delay(100)
    pygame.quit()
    sys.exit()

grafik_button_rect_global=None
tip_button_rect_global=None
hilfe_button_rect_global=None
musik_button_rect_global=None
top5_button_rect_global=None

def draw_buttons():
    global grafik_button_rect_global, tip_button_rect_global
    global hilfe_button_rect_global, musik_button_rect_global
    global top5_button_rect_global

    gf_rect=pygame.Rect(BUTTON_OFFSET_X,BUTTON_OFFSET_Y,BUTTON_WIDTH,BUTTON_HEIGHT)
    pygame.draw.rect(screen,(50,50,50),gf_rect)
    pygame.draw.rect(screen,(255,255,255),gf_rect,2)
    gf_txt=button_font.render("Graphic",True,(255,255,255))
    gf_txt_r=gf_txt.get_rect(center=gf_rect.center)
    screen.blit(gf_txt,gf_txt_r)

    tip_rect=pygame.Rect(BUTTON_OFFSET_X,BUTTON_OFFSET_Y+(BUTTON_HEIGHT+BUTTON_SPACING),
                         BUTTON_WIDTH,BUTTON_HEIGHT)
    pygame.draw.rect(screen,(50,50,50),tip_rect)
    pygame.draw.rect(screen,(255,255,255),tip_rect,2)
    tip_txt=button_font.render("Tip",True,(255,255,255))
    tip_txt_r=tip_txt.get_rect(center=tip_rect.center)
    screen.blit(tip_txt,tip_txt_r)

    hf_rect=pygame.Rect(BUTTON_OFFSET_X,BUTTON_OFFSET_Y+2*(BUTTON_HEIGHT+BUTTON_SPACING),
                        BUTTON_WIDTH,BUTTON_HEIGHT)
    pygame.draw.rect(screen,(50,50,50),hf_rect)
    pygame.draw.rect(screen,(255,255,255),hf_rect,2)
    hf_txt=button_font.render("Help",True,(255,255,255))
    hf_txt_r=hf_txt.get_rect(center=hf_rect.center)
    screen.blit(hf_txt,hf_txt_r)

    ms_rect=pygame.Rect(BUTTON_OFFSET_X,BUTTON_OFFSET_Y+3*(BUTTON_HEIGHT+BUTTON_SPACING),
                        BUTTON_WIDTH,BUTTON_HEIGHT)
    pygame.draw.rect(screen,(50,50,50),ms_rect)
    pygame.draw.rect(screen,(255,255,255),ms_rect,2)
    ms_txt=button_font.render("Music",True,(255,255,255))
    ms_txt_r=ms_txt.get_rect(center=ms_rect.center)
    screen.blit(ms_txt,ms_txt_r)

    # "Top5"
    top_rect=pygame.Rect(BUTTON_OFFSET_X,BUTTON_OFFSET_Y+4*(BUTTON_HEIGHT+BUTTON_SPACING),
                         BUTTON_WIDTH,BUTTON_HEIGHT)
    pygame.draw.rect(screen,(50,50,50),top_rect)
    pygame.draw.rect(screen,(255,255,255),top_rect,2)
    top_txt=button_font.render("Scores",True,(255,255,255))
    top_txt_r=top_txt.get_rect(center=top_rect.center)
    screen.blit(top_txt,top_txt_r)

    grafik_button_rect_global=gf_rect
    tip_button_rect_global=tip_rect
    hilfe_button_rect_global=hf_rect
    musik_button_rect_global=ms_rect
    top5_button_rect_global=top_rect

def draw_help_panel():
    help_file_path=os.path.join(DATA_DIR,'hilfe.txt')
    if os.path.isfile(help_file_path):
        try:
            with open(help_file_path,'r',encoding='utf-8') as f:
                help_text=f.read()
        except Exception as e:
            logging.error(f'Error reading hilfe.txt: {e}')
            help_text="github.com/zeittresor"
    else:
        help_text="github.com/zeittresor"

    panel_width=300
    panel_start_y=BUTTON_OFFSET_Y + 6*(BUTTON_HEIGHT+BUTTON_SPACING) + 10
    panel_height=SCREEN_HEIGHT - panel_start_y - MARGIN
    panel_x=SCREEN_WIDTH - panel_width - MARGIN
    panel_rect=pygame.Rect(panel_x,panel_start_y,panel_width,panel_height)

    panel_surf=pygame.Surface(panel_rect.size,pygame.SRCALPHA)
    panel_surf.fill((100,100,100,128))
    screen.blit(panel_surf,(panel_rect.x,panel_rect.y))

    lines=[]
    wrapper=textwrap.TextWrapper(width=40)
    raw_lines=help_text.split('\n')
    for raw_line in raw_lines:
        if raw_line.strip()=='':
            lines.append('')
        else:
            for wrapped_line in wrapper.wrap(raw_line):
                lines.append(wrapped_line)

    help_font=pygame.font.SysFont(None,24)
    x_ofs=10
    y_ofs=10
    curr_y=panel_start_y+y_ofs

    for line in lines:
        if line=='':
            curr_y+=help_font.get_height()
            continue
        ts=help_font.render(line,True,(255,255,255))
        shadow=help_font.render(line,True,(0,0,0))
        text_rect=ts.get_rect()
        text_rect.x=panel_x+x_ofs
        text_rect.y=curr_y
        sh_rect=text_rect.copy()
        sh_rect.x+=2
        sh_rect.y+=2
        screen.blit(shadow,sh_rect)
        screen.blit(ts,text_rect)
        curr_y+=ts.get_height()+3

def draw_top5_panel():
    highscores=load_highscores()
    panel_width=300
    panel_start_y=BUTTON_OFFSET_Y+5*(BUTTON_HEIGHT+BUTTON_SPACING)+10
    panel_height=SCREEN_HEIGHT - panel_start_y - MARGIN
    panel_x=SCREEN_WIDTH - panel_width - MARGIN
    panel_rect=pygame.Rect(panel_x,panel_start_y,panel_width,panel_height)

    panel_surf=pygame.Surface(panel_rect.size,pygame.SRCALPHA)
    panel_surf.fill((100,100,100,128))
    screen.blit(panel_surf,(panel_rect.x,panel_rect.y))

    help_font=pygame.font.SysFont(None,24)
    x_ofs=10
    y_ofs=10
    curr_y=panel_start_y+y_ofs

    title_s=help_font.render("Top 5 Games",True,(255,255,255))
    shadow=help_font.render("Top 5 Games",True,(0,0,0))
    t_rect=title_s.get_rect()
    t_rect.x=panel_x+x_ofs
    t_rect.y=curr_y
    sh_rect=t_rect.copy()
    sh_rect.x+=2
    sh_rect.y+=2
    screen.blit(shadow,sh_rect)
    screen.blit(title_s,t_rect)
    curr_y+=t_rect.height+10

    if not highscores:
        no_s=help_font.render("No entries yet.",True,(255,255,255))
        no_shadow=help_font.render("No entries yet.",True,(0,0,0))
        nr=no_s.get_rect()
        nr.x=panel_x+x_ofs
        nr.y=curr_y
        sr=nr.copy()
        sr.x+=2
        sr.y+=2
        screen.blit(no_shadow,sr)
        screen.blit(no_s,nr)
        return
    place=1
    for entry in highscores:
        blocks, datum, zeit, spent, user=entry
        line_platz=f"Platz {place}"
        line_blocks=f"Benötigte Blöcke: {blocks}"
        line_date=f"Datum: {datum} {zeit}"
        line_spent=f"Dauer: {spent:.2f}s"
        line_user=f"Benutzer: {user}"

        lines=[line_platz, line_blocks, line_date, line_spent, line_user, ""]
        for l in lines:
            ts=help_font.render(l,True,(255,255,255))
            sh=help_font.render(l,True,(0,0,0))
            tr=ts.get_rect()
            tr.x=panel_x+x_ofs
            tr.y=curr_y
            shr=tr.copy()
            shr.x+=2
            shr.y+=2
            screen.blit(sh,shr)
            screen.blit(ts,tr)
            curr_y+=ts.get_height()+3
        place+=1

def draw_sliders():
    s_x=SLIDER_OFFSET_X
    s_y=SLIDER_OFFSET_Y

    total_slider_height=6*SLIDER_HEIGHT+5*SLIDER_SPACING
    panel_w=SLIDER_WIDTH+max_label_width+10
    panel_h=total_slider_height
    panel_x=s_x-max_label_width-5
    panel_y=s_y
    surf=pygame.Surface((panel_w,panel_h),pygame.SRCALPHA)
    surf.fill((100,100,100,128))
    screen.blit(surf,(panel_x,panel_y))

    sliders=[
        ('Saturation',saturation),
        ('Brightness',brightness),
        ('Contrast',contrast),
        ('Color Tone',hue),
        ('BG Brightness',bg_brightness),
        ('Transparency',transparency_value)
    ]

    for lbl,val in sliders:
        lbl_s=slider_font.render(lbl,True,(255,255,255))
        lbl_r=lbl_s.get_rect()
        lbl_r.right=s_x-5
        lbl_r.centery=s_y+SLIDER_HEIGHT//2
        screen.blit(lbl_s,lbl_r)

        bar_rect=pygame.Rect(s_x,s_y,SLIDER_WIDTH,SLIDER_HEIGHT)
        pygame.draw.rect(screen,(200,200,200),bar_rect)

        knob_y=s_y+(1-val)*(SLIDER_HEIGHT-20)
        knob_rect=pygame.Rect(s_x,knob_y,SLIDER_WIDTH,20)
        pygame.draw.rect(screen,(100,100,100),knob_rect)

        s_y+=(SLIDER_HEIGHT+SLIDER_SPACING)

def handle_slider_click(pos):
    global saturation, brightness, contrast, hue, bg_brightness, transparency_value
    x, y=pos
    s_x=SLIDER_OFFSET_X
    s_y=SLIDER_OFFSET_Y

    sls=[
        ('saturation', s_y),
        ('brightness', s_y+SLIDER_HEIGHT+SLIDER_SPACING),
        ('contrast',   s_y+2*(SLIDER_HEIGHT+SLIDER_SPACING)),
        ('hue',        s_y+3*(SLIDER_HEIGHT+SLIDER_SPACING)),
        ('bg_brightness', s_y+4*(SLIDER_HEIGHT+SLIDER_SPACING)),
        ('transparency',  s_y+5*(SLIDER_HEIGHT+SLIDER_SPACING))
    ]

    for name, sy in sls:
        rect=pygame.Rect(s_x, sy, SLIDER_WIDTH, SLIDER_HEIGHT)
        if rect.collidepoint(x,y):
            rel_y=y-sy
            val=1-(rel_y/(SLIDER_HEIGHT-20))
            val=max(0.0, min(1.0, val))
            if name=='saturation':
                saturation=val
            elif name=='brightness':
                brightness=val
            elif name=='contrast':
                contrast=val
            elif name=='hue':
                hue=val
            elif name=='bg_brightness':
                bg_brightness=val
                adjust_background_image()
            elif name=='transparency':
                transparency_value=val

            if block_images and name not in ('bg_brightness','transparency'):
                adjust_and_cache_images()
            break

def handle_button_click(pos):
    global sliders_visible, tip_highlight, showing_help, showing_top5
    x, y = pos

    if grafik_button_rect_global and grafik_button_rect_global.collidepoint(x,y):
        sliders_visible=not sliders_visible
        return

    if tip_button_rect_global and tip_button_rect_global.collidepoint(x,y):
        tip_highlight=find_possible_move()
        if tip_highlight:
            highlight_duration=1000
            st=pygame.time.get_ticks()
            while pygame.time.get_ticks()-st<highlight_duration:
                draw_grid()
                pygame.display.flip()
                clock.tick(60)
            tip_highlight=None
        return

    if hilfe_button_rect_global and hilfe_button_rect_global.collidepoint(x,y):
        if showing_help:
            showing_help=False
            if help_sound:
                help_sound.stop()
        else:
            showing_help=True
            if help_sound:
                help_sound.play()
        return

    if musik_button_rect_global and musik_button_rect_global.collidepoint(x,y):
        skip_music()
        return

    # "Top5 HiScore"
    if top5_button_rect_global and top5_button_rect_global.collidepoint(x,y):
        showing_top5=not showing_top5
        return

def draw_grid(selected_positions=None, matched_positions=None, blink=False,
              swapped_positions=None, swap_progress=0,
              swapped_positions_positions=None, swapped_positions_destinations=None):
    if adjusted_background_image:
        screen.blit(adjusted_background_image,(0,0))
    else:
        screen.fill(BACKGROUND_COLOR)

    if graphic_image:
        screen.blit(graphic_image,graphic_rect)
    elif text_surface and shadow_surface and text_rect:
        sh_pos=(text_rect.x+shadow_offset[0], text_rect.y+shadow_offset[1])
        screen.blit(shadow_surface,sh_pos)
        screen.blit(text_surface,text_rect)

    c_txt=f"Killed Xenobug Blocks: {blocks_cleared}"
    c_s=counter_font.render(c_txt,True,(255,255,255))
    sc_s=counter_font.render(c_txt,True,(0,0,0))
    c_rect=c_s.get_rect()
    c_rect.centerx=SCREEN_WIDTH//2
    c_rect.top=BOARD_OFFSET_Y+BOARD_HEIGHT+10
    sofs=(2,2)
    sc_rect=c_rect.copy()
    sc_rect.x+=sofs[0]
    sc_rect.y+=sofs[1]
    screen.blit(sc_s,sc_rect)
    screen.blit(c_s,c_rect)

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            bt=grid[y][x]
            if bt==-1:
                continue
            rect=pygame.Rect(BOARD_OFFSET_X+x*BLOCK_SIZE, BOARD_OFFSET_Y+y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)

            if swapped_positions and (y,x) in swapped_positions:
                idx=swapped_positions.index((y,x))
                st=swapped_positions_positions[idx]
                ed=swapped_positions_destinations[idx]
                dx=ed[0]-st[0]
                dy=ed[1]-st[1]
                cx=st[0]+dx*swap_progress
                cy=st[1]+dy*swap_progress
                rect.topleft=(cx,cy)

            if matched_positions and (y,x) in matched_positions and not blink:
                continue

            alpha=int(255*transparency_value)
            dark=pygame.Surface((BLOCK_SIZE,BLOCK_SIZE),pygame.SRCALPHA)
            dark.fill((0,0,0,alpha))
            screen.blit(dark,rect)

            if block_images:
                if use_colors_with_images:
                    ac=adjust_color(COLORS[bt])
                    c_sf=pygame.Surface((BLOCK_SIZE,BLOCK_SIZE),pygame.SRCALPHA)
                    c_sf.fill(ac)
                    screen.blit(c_sf,rect)
                adj=adjusted_images_cache.get(bt)
                if adj:
                    screen.blit(adj,rect)
                else:
                    screen.blit(block_images[bt],rect)
            else:
                c=COLORS[bt]
                ac=adjust_color(c)
                c_sf=pygame.Surface((BLOCK_SIZE,BLOCK_SIZE),pygame.SRCALPHA)
                c_sf.fill(ac)
                screen.blit(c_sf,rect)

            if selected_positions and (y,x) in selected_positions:
                pygame.draw.rect(screen,(255,255,0),rect,3)
            elif matched_positions and (y,x) in matched_positions:
                pygame.draw.rect(screen,(0,255,0),rect,3)
            elif tip_highlight and (y,x) in tip_highlight:
                pygame.draw.rect(screen,(255,0,0),rect,3)

    screen.blit(grid_lines_surface,(BOARD_OFFSET_X,BOARD_OFFSET_Y))

    draw_buttons()
    if sliders_visible:
        draw_sliders()

    if showing_help:
        draw_help_panel()

    if showing_top5:
        draw_top5_panel()

def no_more_moves():
    txt=font.render("No more moves possible ! Another try ? (j/n)",True,(255,255,255))
    sh_txt=font.render("No more moves possible ! Another try ? (j/n)",True,(0,0,0))
    retry_txt=font.render("",True,(255,255,255))  
    sh_retry=font.render("",True,(0,0,0))         

    t_rect=txt.get_rect()
    t_rect.centerx=SCREEN_WIDTH//2
    t_rect.centery=SCREEN_HEIGHT//2-50

    r_rect=retry_txt.get_rect()
    r_rect.centerx=SCREEN_WIDTH//2
    r_rect.centery=SCREEN_HEIGHT//2

    sofs=(2,2)
    s_txt_rect=t_rect.copy()
    s_txt_rect.x+=sofs[0]
    s_txt_rect.y+=sofs[1]
    s_r_rect=r_rect.copy()
    s_r_rect.x+=sofs[0]
    s_r_rect.y+=sofs[1]

    screen.blit(sh_txt,s_txt_rect)
    screen.blit(txt,t_rect)
    screen.blit(sh_retry,s_r_rect)
    screen.blit(retry_txt,r_rect)
    pygame.display.flip()

    end_time=time.time()
    spent_time=end_time - start_time
    add_highscore(blocks_cleared,spent_time)

    waiting=True
    while waiting:
        for event in pygame.event.get():
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_j:
                    create_grid()
                    waiting=False
                elif event.key==pygame.K_n:
                    fade_out_and_quit()
            elif event.type==pygame.QUIT:
                fade_out_and_quit()

def show_exit_prompt():
    ex_txt=font.render("Exit Game j/n",True,(255,255,255))
    sh_ex_txt=font.render("Exit Game j/n",True,(0,0,0))

    t_rect=ex_txt.get_rect()
    t_rect.centerx=SCREEN_WIDTH//2
    t_rect.centery=SCREEN_HEIGHT//2
    sofs=(2,2)
    sh_rect=t_rect.copy()
    sh_rect.x+=sofs[0]
    sh_rect.y+=sofs[1]

    screen.blit(sh_ex_txt,sh_rect)
    screen.blit(ex_txt,t_rect)
    pygame.display.flip()

def fade_out_and_quit():
    if tschuess_sound:
        tschuess_sound.play()
    pygame.mixer.music.fadeout(5000)
    fd_s=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    fd_s=fd_s.convert_alpha()
    for alpha in range(0,255,5):
        fd_s.fill((0,0,0,alpha))
        screen.blit(fd_s,(0,0))
        pygame.display.flip()
        pygame.time.delay(100)
    pygame.quit()
    sys.exit()

def main():
    global start_time
    start_time=time.time()

    create_grid()
    if block_images:
        adjust_and_cache_images()
    adjust_background_image()

    running=True
    global selected_block,blocks_cleared,exit_prompt
    global sliders_visible, showing_help, showing_top5

    if hello_sound:
        hello_sound.play()

    while running:
        clock.tick(60)
        check_music_end()

        if exit_prompt:
            draw_grid()
            show_exit_prompt()
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_j:
                        fade_out_and_quit()
                    elif event.key==pygame.K_n:
                        exit_prompt=False
                elif event.type==pygame.QUIT:
                    fade_out_and_quit()
        else:
            draw_grid(selected_positions=[selected_block] if selected_block else None)
            pygame.display.flip()

            if not has_possible_moves():
                no_more_moves()
                continue

            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    fade_out_and_quit()
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE:
                        exit_prompt=True
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    x,y=event.pos
                    # Zuerst Buttonklick prüfen
                    handle_button_click((x,y))

                    # Falls Slider offen => Klick in slider?
                    if sliders_visible:
                        total_slider_height=6*SLIDER_HEIGHT+5*SLIDER_SPACING
                        slider_panel_rect=pygame.Rect(
                            SLIDER_OFFSET_X-max_label_width-5,
                            SLIDER_OFFSET_Y,
                            SLIDER_WIDTH+max_label_width+10,
                            total_slider_height
                        )
                        if slider_panel_rect.collidepoint(x,y):
                            handle_slider_click((x,y))
                            continue

                    # Schließe Menüs, falls Klick NICHT in Buttons/Panels
                    if not (grafik_button_rect_global and grafik_button_rect_global.collidepoint(x,y)) \
                       and not (tip_button_rect_global and tip_button_rect_global.collidepoint(x,y)) \
                       and not (hilfe_button_rect_global and hilfe_button_rect_global.collidepoint(x,y)) \
                       and not (musik_button_rect_global and musik_button_rect_global.collidepoint(x,y)) \
                       and not (top5_button_rect_global and top5_button_rect_global.collidepoint(x,y)):

                        if sliders_visible and not slider_panel_rect.collidepoint(x,y):
                            sliders_visible=False

                        if showing_help:
                            panel_width=300
                            panel_start_y=BUTTON_OFFSET_Y+6*(BUTTON_HEIGHT+BUTTON_SPACING)+10
                            panel_height=SCREEN_HEIGHT - panel_start_y - MARGIN
                            panel_x=SCREEN_WIDTH - panel_width - MARGIN
                            help_rect=pygame.Rect(panel_x,panel_start_y,panel_width,panel_height)
                            if not help_rect.collidepoint(x,y):
                                showing_help=False
                                if help_sound:
                                    help_sound.stop()

                        if showing_top5:
                            panel_width=300
                            panel_start_y=BUTTON_OFFSET_Y+5*(BUTTON_HEIGHT+BUTTON_SPACING)+10
                            panel_height=SCREEN_HEIGHT - panel_start_y - MARGIN
                            panel_x=SCREEN_WIDTH - panel_width - MARGIN
                            top5_rect=pygame.Rect(panel_x,panel_start_y,panel_width,panel_height)
                            if not top5_rect.collidepoint(x,y):
                                showing_top5=False

                    # Board-Klick => Move
                    grid_x=(x-BOARD_OFFSET_X)//BLOCK_SIZE
                    grid_y=(y-BOARD_OFFSET_Y)//BLOCK_SIZE
                    if 0<=grid_x<GRID_SIZE and 0<=grid_y<GRID_SIZE:
                        if selected_block:
                            y1,x1=selected_block
                            if abs(y1-grid_y)+abs(x1-grid_x)==1:
                                animate_swap(selected_block,(grid_y,grid_x))
                                swap_blocks(selected_block,(grid_y,grid_x))
                                matches=find_matches()
                                if matches:
                                    while True:
                                        matches=find_matches()
                                        if not matches:
                                            break
                                        match_length=len(set(matches))
                                        if match_length>=5 and five_match_sound:
                                            five_match_sound.play()
                                        elif match_length==4 and four_match_sound:
                                            four_match_sound.play()
                                        elif match_sound:
                                            match_sound.play()
                                        blocks_cleared+=match_length
                                        animate_matches(matches)
                                        for y_m,x_m in matches:
                                            grid[y_m][x_m]=-1
                                        collapse_grid()
                                else:
                                    animate_swap(selected_block,(grid_y,grid_x))
                                    swap_blocks(selected_block,(grid_y,grid_x))
                                    if swap_fail_sound:
                                        swap_fail_sound.play()
                                selected_block=None
                            else:
                                selected_block=(grid_y,grid_x)
                        else:
                            selected_block=(grid_y,grid_x)

            draw_grid(selected_positions=[selected_block] if selected_block else None)
            pygame.display.flip()
    pygame.quit()

if __name__=="__main__":
    main()

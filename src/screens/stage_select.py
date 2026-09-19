"""One illustrated world, with native plaques, status markers and hotspots."""
from functools import lru_cache
from pathlib import Path
import math
import pygame

from src.data.stage_map import STAGE_MAP_NODES, stage_map_node
from src.data.stages import get_stage
from src.systems.stage_selection import stage_available, stage_status, stage_unlocked
from src.systems.audio import handle_music_shortcut
from src.ui.text_layout import fit_text, draw_text_block
from src.ui.theme import title_font, ui_font

ART_PATH = Path("assets/images/backgrounds/stage_select_world_reference.png")
ART_SIZE = (1374, 1145)
GOLD = (220, 185, 115)
INK = (46, 32, 22)
PARCHMENT = (216, 191, 147)
TEXT = (247, 234, 207)


def map_to_screen(point, map_rect):
    return (round(map_rect.x + point[0] * map_rect.w),
            round(map_rect.y + point[1] * map_rect.h))


def screen_to_map(point, map_rect):
    if not map_rect.collidepoint(point):
        return None
    return ((point[0] - map_rect.x) / map_rect.w,
            (point[1] - map_rect.y) / map_rect.h)


def stage_select_layout(size):
    w, h = size
    s = min(w / 1280, h / 720)
    margin = round(16 * s)
    available_h = h - round(64 * s)
    scale = min((w - margin * 2) / ART_SIZE[0], available_h / ART_SIZE[1])
    map_rect = pygame.Rect(0, 0, round(ART_SIZE[0] * scale), round(ART_SIZE[1] * scale))
    map_rect.midtop = (w // 2, margin)
    plaques = []
    for node in STAGE_MAP_NODES:
        rect = pygame.Rect(0, 0, round(235 * s), round(58 * s))
        rect.center = map_to_screen(node["plaque"], map_rect)
        plaques.append(rect)
    markers = []
    for node, plaque in zip(STAGE_MAP_NODES, plaques):
        x, y = map_to_screen(node["marker"], map_rect)
        markers.append((x, max(y, plaque.bottom + round(19*s))))
    # Expand the illustration's parchment into the side gutter on wide screens.
    panel = pygame.Rect(0, 0, round(300 * s), max(round(362 * s), round(map_rect.h * .435)))
    panel.topleft = map_to_screen((.797, .269), map_rect)
    panel.right = min(panel.right, w - margin)
    panel.bottom = min(panel.bottom, map_rect.bottom)
    back = pygame.Rect(margin, h - round(48 * s), round(120 * s), round(34 * s))
    enter = pygame.Rect(panel.x + round(18*s), panel.bottom - round(53*s),
                        panel.w - round(36*s), round(35*s))
    return {"scale": s, "map": map_rect, "plaques": plaques, "markers": markers,
            "panel": panel, "enter": enter, "back": back}


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    previous = polygon[-1]
    for current in polygon:
        ax, ay = previous
        bx, by = current
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
        previous = current
    return inside


def hotspot_at(point, layout):
    if layout["panel"].collidepoint(point) or layout["back"].collidepoint(point):
        return None
    for index, rect in enumerate(layout["plaques"]):
        if rect.collidepoint(point):
            return index
        if math.dist(point, layout["markers"][index]) <= 24 * layout["scale"]:
            return index
    normalized = screen_to_map(point, layout["map"])
    if normalized is not None:
        for index, node in enumerate(STAGE_MAP_NODES):
            if point_in_polygon(normalized, node["region"]):
                return index
    return None


@lru_cache(maxsize=1)
def _original_art():
    return pygame.image.load(str(ART_PATH)).convert()


@lru_cache(maxsize=6)
def atlas_background(size):
    layout = stage_select_layout(size)
    w, h = size
    source = _original_art()
    # Carry the forest/sea colors across the entire viewport. The tiny
    # intermediate texture makes a soft atmospheric backdrop without
    # repeating readable labels from the illustration.
    landscape = source.subsurface(pygame.Rect(
        round(source.get_width() * .03), round(source.get_height() * .22),
        round(source.get_width() * .74), round(source.get_height() * .76)))
    mist = pygame.transform.smoothscale(landscape, (32, 24))
    result = pygame.transform.smoothscale(mist, size)
    tint = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(h):
        alpha = round(110 + 45 * abs(y / max(1, h) - .45))
        pygame.draw.line(tint, (9, 20, 28, alpha), (0, y), (w, y))
    result.blit(tint, (0, 0))
    # Contain the full illustration, without cropping or stretching landmarks.
    atlas = pygame.transform.smoothscale(source, layout["map"].size).convert_alpha()
    # Feather only the outer edge into the surrounding mist; the map and
    # all hit coordinates keep their original aspect and dimensions.
    fade = max(1, round(20 * layout["scale"]))
    mask = pygame.Surface(atlas.get_size(), pygame.SRCALPHA)
    mask.fill((255, 255, 255, 255))
    for offset in range(fade):
        alpha = round(255 * offset / fade)
        pygame.draw.rect(mask, (255, 255, 255, alpha), mask.get_rect().inflate(-offset*2, -offset*2), 1)
    atlas.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    result.blit(atlas, layout["map"])
    # A quiet antique frame makes the surrounding space part of the atlas.
    inset = max(6, round(10 * layout["scale"]))
    frame = result.get_rect().inflate(-inset*2, -inset*2)
    pygame.draw.rect(result, (93, 85, 62), frame, 1)
    arm = round(28 * layout["scale"])
    for x, y, dx, dy in ((frame.left, frame.top, 1, 1),
                         (frame.right-1, frame.top, -1, 1),
                         (frame.left, frame.bottom-1, 1, -1),
                         (frame.right-1, frame.bottom-1, -1, -1)):
        pygame.draw.lines(result, GOLD, False, [(x+dx*arm, y), (x, y), (x, y+dy*arm)], 2)
    return result


def draw_atlas_ambience(screen, layout, time_seconds):
    """Slow drifting dust in the margins, away from text and landmarks."""
    w, h = screen.get_size()
    s = layout["scale"]
    particles = pygame.Surface((w, h), pygame.SRCALPHA)
    for index in range(30):
        x = round(((index * .6180339) % 1) * w + math.sin(time_seconds*.18+index)*12*s)
        y = round(((index*.381966 - time_seconds*.012) % 1) * h)
        if layout["map"].inflate(12, 12).collidepoint(x, y) or layout["panel"].collidepoint(x, y):
            continue
        alpha = round(55 + 45*(1+math.sin(time_seconds*.8+index))/2)
        pygame.draw.circle(particles, (238, 203, 132, alpha), (x, y), max(1, round(s)))
    screen.blit(particles, (0, 0))


@lru_cache(maxsize=24)
def _region_glow(size, color, alpha):
    glow = pygame.Surface(size, pygame.SRCALPHA)
    w, h = size
    for step in range(32):
        fraction = 1 - step / 40
        rect = pygame.Rect(0, 0, max(1, round(w*fraction)), max(1, round(h*fraction)))
        rect.center = (w//2, h//2)
        pygame.draw.ellipse(glow, (*color, round(alpha * (step/31))), rect)
    return glow


def _plaque(screen, rect, fill, border, width=1):
    cut = max(4, round(min(rect.h * .13, rect.w * .035)))
    points = [(rect.left+cut, rect.top), (rect.right-cut, rect.top),
              (rect.right, rect.top+cut), (rect.right, rect.bottom-cut),
              (rect.right-cut, rect.bottom), (rect.left+cut, rect.bottom),
              (rect.left, rect.bottom-cut), (rect.left, rect.top+cut)]
    pygame.draw.polygon(screen, fill, points)
    pygame.draw.polygon(screen, border, points, width)


def draw_stage_select(screen, state, selected=0, developer_access=False,
                      mouse=(-1, -1), time_seconds=0):
    layout = stage_select_layout(screen.get_size())
    s, map_rect = layout["scale"], layout["map"]
    screen.blit(atlas_background(screen.get_size()), (0, 0))
    draw_atlas_ambience(screen, layout, time_seconds)

    def label(text, rect, size, color=TEXT, heading=False, center=False):
        font = title_font(round(size*s)) if heading else ui_font(round(size*s))
        image = fit_text(font, text, color, rect.size)
        screen.blit(image, image.get_rect(center=rect.center) if center else image.get_rect(midleft=rect.midleft))

    old_clip = screen.get_clip()
    current_id = get_stage(state.get("stage"))["id"]
    screen.set_clip(map_rect)
    for index, node in enumerate(STAGE_MAP_NODES):
        cx, cy, width, height = node["glow"]
        glow_size = (round(width*map_rect.w), round(height*map_rect.h))
        center = map_to_screen((cx, cy), map_rect)
        if not stage_unlocked(node["id"], state, developer_access):
            glow = _region_glow(glow_size, (0, 0, 0), 90)
            screen.blit(glow, glow.get_rect(center=center))
        if index == selected:
            glow = _region_glow(glow_size, (245, 210, 131), 28)
            screen.blit(glow, glow.get_rect(center=center))
    screen.set_clip(old_clip)

    for index, node in enumerate(STAGE_MAP_NODES):
        rect = layout["plaques"][index]
        status = stage_status(node["id"], state, developer_access)
        focused = index == selected
        _plaque(screen, rect.move(0, round(3*s)), (12, 11, 10), (12, 11, 10))
        _plaque(screen, rect, (41, 29, 22), GOLD if focused else (136, 109, 70), max(1, round(2*s)))
        inset = rect.inflate(-round(10*s), -round(8*s))
        label(f"STAGE {node['number']}", pygame.Rect(inset.x, inset.y, inset.w, round(21*s)), 17, GOLD, heading=True, center=True)
        label(node["name"], pygame.Rect(inset.x, inset.y + round(22*s), inset.w, round(22*s)), 17, center=True)

        x, y = layout["markers"][index]
        radius = round(16*s)
        # Opaque seals replace the locks/waypoint baked into the supplied art.
        pygame.draw.circle(screen, (37, 31, 24), (x, y), radius + round(3*s))
        tint = (129, 235, 172) if status in ("CURRENT", "COMPLETED", "AVAILABLE") else GOLD
        pulse = (1 + math.sin(time_seconds * 3)) / 2
        if node["id"] == current_id or focused:
            pygame.draw.circle(screen, tint, (x, y), radius + round((4 + pulse*3)*s), max(1, round(s)))
        pygame.draw.circle(screen, tint, (x, y), radius, max(1, round(s)))
        if status == "COMPLETED":
            pygame.draw.lines(screen, tint, False, [(x-round(7*s), y), (x-round(2*s), y+round(5*s)), (x+round(8*s), y-round(6*s))], max(2, round(2*s)))
        elif status in ("LOCKED", "COMING SOON"):
            shackle = pygame.Rect(x-round(5*s), y-round(10*s), round(10*s), round(13*s))
            pygame.draw.ellipse(screen, tint, shackle, max(2, round(2*s)))
            pygame.draw.rect(screen, tint, (x-round(8*s), y-round(2*s), round(16*s), round(12*s)), border_radius=max(1, round(2*s)))
            pygame.draw.circle(screen, INK, (x, y+round(3*s)), max(1, round(2*s)))
        else:
            pygame.draw.polygon(screen, tint, [(x, y-round(8*s)), (x+round(6*s), y), (x, y+round(9*s)), (x-round(6*s), y)])

    panel = layout["panel"]
    _plaque(screen, panel.move(round(4*s), round(5*s)), (13, 13, 14), (13, 13, 14))
    _plaque(screen, panel, PARCHMENT, (123, 88, 46), max(2, round(3*s)))
    pygame.draw.rect(screen, (160, 126, 79), panel.inflate(-round(12*s), -round(14*s)), 1, border_radius=3)
    node = STAGE_MAP_NODES[selected]
    status = stage_status(node["id"], state, developer_access)
    left, width = panel.x + round(20*s), panel.w - round(40*s)
    label(f"CHAPTER {node['number']}  /  {status}", pygame.Rect(left, panel.y+round(17*s), width, round(23*s)), 14, INK)
    draw_text_block(screen, node["name"], title_font(round(18*s)), INK,
                    pygame.Rect(left, panel.y+round(46*s), width, round(63*s)))
    pygame.draw.line(screen, (152, 115, 65), (left, panel.y+round(114*s)), (left+width, panel.y+round(114*s)))
    draw_text_block(screen, node["description"], ui_font(round(12*s)), INK,
                    pygame.Rect(left, panel.y+round(125*s), width, round(86*s)))
    label(node["content"], pygame.Rect(left, panel.y+round(216*s), width, round(22*s)), 14, INK)
    note = node["map_note"]
    if not stage_unlocked(node["id"], state, developer_access):
        prior = stage_map_node(node["unlock_after"])
        note = f"Complete Stage {prior['number']} to unlock. " + note
    draw_text_block(screen, note, ui_font(round(11*s)), (86, 62, 38),
                    pygame.Rect(left, panel.y+round(246*s), width, round(52*s)))
    available = stage_available(node["id"], state, developer_access)
    if available:
        button = layout["enter"]
        _plaque(screen, button, (62, 52, 29) if button.collidepoint(mouse) else (45, 39, 26), (133, 97, 45))
        label("ENTER STAGE", button.inflate(-12, -8), 17, TEXT, center=True)
    else:
        label("LOCKED" if status == "LOCKED" else "MAP COMING SOON", layout["enter"], 16, (97, 75, 50), center=True)
    _plaque(screen, layout["back"], (42, 32, 24), GOLD)
    label("BACK", layout["back"], 16, center=True)
    footer = pygame.Rect(layout["back"].right+round(22*s), layout["back"].y,
                         screen.get_width()-layout["back"].right-round(38*s), layout["back"].h)
    label("Developer access  /  Select a landmark" if developer_access else
          "Select a landmark   /   Arrow keys to explore   /   Enter to travel   /   Esc to return",
          footer, 14, (204, 193, 171))
    return layout


def open_stage_select(screen, state, developer_access=False):
    stage_ids = tuple(node["id"] for node in STAGE_MAP_NODES)
    current = get_stage(state.get("stage"))["id"]
    selected = stage_ids.index(current) if current in stage_ids else 0
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        layout = stage_select_layout(screen.get_size())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.event.post(event)
                return None
            if handle_music_shortcut(event):
                continue
            activate = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_g):
                    return None
                if event.key in (pygame.K_RIGHT, pygame.K_UP, pygame.K_TAB):
                    selected = (selected + 1) % len(stage_ids)
                elif event.key in (pygame.K_LEFT, pygame.K_DOWN):
                    selected = (selected - 1) % len(stage_ids)
                activate = event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
            elif event.type == pygame.MOUSEMOTION:
                hovered = hotspot_at(event.pos, layout)
                if hovered is not None:
                    selected = hovered
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if layout["back"].collidepoint(event.pos):
                    return None
                hovered = hotspot_at(event.pos, layout)
                if hovered is not None:
                    selected = hovered
                activate = layout["enter"].collidepoint(event.pos)
            if activate and stage_available(stage_ids[selected], state, developer_access):
                return stage_ids[selected]
        draw_stage_select(screen, state, selected, developer_access,
                          pygame.mouse.get_pos(), pygame.time.get_ticks()/1000)
        pygame.display.flip()

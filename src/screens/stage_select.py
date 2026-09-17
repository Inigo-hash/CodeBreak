"""Illustrated campaign atlas with native, resolution-independent controls."""
from functools import lru_cache
from pathlib import Path
import pygame

from src.data.stages import STAGES, get_stage
from src.systems.stage_selection import stage_available
from src.systems.audio import handle_music_shortcut
from src.ui.text_layout import fit_text, draw_text_block
from src.ui.theme import title_font, ui_font

ART_PATH = Path("assets/images/backgrounds/stage_select_world.png")
GOLD = (224, 184, 102)
TEXT = (241, 235, 219)
MUTED = (170, 188, 195)
STAGE_COPY = {
    "island": ("BEGINNER EXPEDITION", "The Island",
               "Follow torch-lit trails, learn Python's foundations, and face the Kapre at the Corrupted Core.",
               "9 lessons   /   9 keys   /   Kapre boss"),
    "castle": ("INTERMEDIATE FRONTIER", "The Castle",
               "Explore the grand staircase and quiet stone halls. The lobby is open; its lesson route is still being built.",
               "Castle lobby   /   Exploration preview"),
}


def stage_select_layout(size):
    w, h = size
    scale = min(w / 1280, h / 720)
    width = min(w - round(80 * scale), round(1160 * scale))
    left = (w - width) // 2
    gap = round(24 * scale)
    card_w = (width - gap) // 2
    cards = [pygame.Rect(left + i * (card_w + gap), round(h * .57),
                         card_w, round(h * .27)) for i in range(2)]
    return {
        "scale": scale, "cards": cards,
        "back": pygame.Rect(left, h - round(76 * scale), round(130 * scale), round(44 * scale)),
        "enter": pygame.Rect(left + width - round(254 * scale), h - round(76 * scale), round(254 * scale), round(44 * scale)),
        "header": pygame.Rect(left, round(38 * scale), width, round(120 * scale)),
    }


@lru_cache(maxsize=6)
def atlas_background(size):
    source = pygame.image.load(str(ART_PATH)).convert()
    w, h = size
    # Cover preserves artwork proportions on wide and tall displays.
    scale = max(w / source.get_width(), h / source.get_height())
    art = pygame.transform.smoothscale(source, (round(source.get_width() * scale), round(source.get_height() * scale)))
    result = pygame.Surface(size)
    result.blit(art, ((w - art.get_width()) // 2, (h - art.get_height()) // 2))
    shade = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(h):
        edge = max(0, 1 - y / (h * .32)) * 165
        bottom = max(0, (y / h - .48) / .52) * 220
        pygame.draw.line(shade, (5, 12, 21, round(max(edge, bottom))), (0, y), (w, y))
    result.blit(shade, (0, 0))
    return result


def draw_stage_select(screen, state, selected=0, developer_access=False, mouse=(-1, -1)):
    layout = stage_select_layout(screen.get_size())
    s = layout["scale"]
    screen.blit(atlas_background(screen.get_size()), (0, 0))
    header = layout["header"]

    def label(text, rect, size, color=TEXT, heading=False):
        font = title_font(round(size * s)) if heading else ui_font(round(size * s))
        image = fit_text(font, text, color, rect.size)
        screen.blit(image, image.get_rect(midleft=rect.midleft))

    label("CODEBREAK  /  EXPEDITION ATLAS", pygame.Rect(header.x, header.y, header.w, round(24*s)), 16, GOLD)
    label("Choose your next chapter", pygame.Rect(header.x, header.y + round(28*s), header.w, round(52*s)), 40, heading=True)
    label("Every trail has something to teach you.", pygame.Rect(header.x, header.y + round(84*s), header.w, round(28*s)), 18, MUTED)
    current = get_stage(state.get("stage"))["id"]
    for index, (stage_id, rect) in enumerate(zip(STAGE_COPY, layout["cards"])):
        available = stage_available(stage_id, state, developer_access)
        focused = index == selected
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((9, 22, 32, 237 if focused else 222))
        screen.blit(panel, rect)
        pygame.draw.rect(screen, GOLD if focused else (72, 93, 104), rect, 2 if focused else 1, border_radius=8)
        pad = round(22*s)
        area = rect.inflate(-pad * 2, 0)
        kicker, name, description, facts = STAGE_COPY[stage_id]
        status = ("LOCKED" if not available else "CURRENT" if current == stage_id
                  else "COMPLETED" if stage_id in state.get("completed_stages", ()) else "AVAILABLE")
        label(f"0{index+1}  /  {kicker}", pygame.Rect(area.x, rect.y + round(13*s), area.w * .72, round(22*s)), 13, GOLD)
        badge = pygame.Rect(rect.right - round(128*s), rect.y + round(13*s), round(108*s), round(22*s))
        label(status, badge, 12, (119, 220, 179) if available else MUTED)
        label(name, pygame.Rect(area.x, rect.y + round(40*s), area.w, round(39*s)), 29, heading=True)
        body = pygame.Rect(area.x, rect.y + round(87*s), area.w, round(55*s))
        draw_text_block(screen, description, ui_font(round(16*s)), MUTED, body)
        label(facts if available else "Complete the Island to unlock this chapter.",
              pygame.Rect(area.x, rect.bottom - round(37*s), area.w, round(24*s)), 14, GOLD if available else MUTED)
    stage_id = tuple(STAGE_COPY)[selected]
    available = stage_available(stage_id, state, developer_access)
    for key, text in (("back", "BACK"), ("enter", "RESUME CHAPTER" if current == stage_id else "ENTER CHAPTER")):
        rect = layout[key]
        enabled = key == "back" or available
        hovered = rect.collidepoint(mouse)
        pygame.draw.rect(screen, (205, 166, 86) if key == "enter" and enabled else (15, 29, 42), rect, border_radius=6)
        pygame.draw.rect(screen, TEXT if hovered else GOLD if enabled else (65, 78, 89), rect, 1, border_radius=6)
        image = fit_text(ui_font(round(17*s)), text if enabled else "CHAPTER LOCKED",
                         (15, 25, 32) if key == "enter" and enabled else TEXT, (rect.w - 20, rect.h - 10))
        screen.blit(image, image.get_rect(center=rect.center))
    hint = "ARROWS  Select     ENTER  Travel     ESC  Back"
    if developer_access:
        hint = "DEVELOPER ACCESS  /  Available maps unlocked"
    label(hint, pygame.Rect(layout["back"].right + round(25*s), layout["back"].y,
                           layout["enter"].left - layout["back"].right - round(50*s), layout["back"].h), 13, MUTED)
    return layout


def open_stage_select(screen, state, developer_access=False):
    stage_ids = tuple(STAGE_COPY)
    current = get_stage(state.get("stage"))["id"]
    selected = stage_ids.index(current) if current in stage_ids else 0
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        layout = draw_stage_select(screen, state, selected, developer_access, pygame.mouse.get_pos())
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.event.post(event)
                return None
            if handle_music_shortcut(event):
                continue
            activate = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_TAB):
                    selected = (selected + 1) % len(stage_ids)
                activate = event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if layout["back"].collidepoint(event.pos):
                    return None
                for index, rect in enumerate(layout["cards"]):
                    if rect.collidepoint(event.pos):
                        selected = index
                activate = layout["enter"].collidepoint(event.pos)
            if activate and stage_available(stage_ids[selected], state, developer_access):
                return stage_ids[selected]

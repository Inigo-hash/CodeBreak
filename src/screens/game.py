from pytmx.util_pygame import load_pygame
import pygame
import sys
from pytmx.util_pygame import load_pygame

def game_screen(screen):
    clock = pygame.time.Clock()

    # --- Load Map ---
    tmx_data = load_pygame("assets/map/tmx/basic.tmx")
    TILE_SIZE = tmx_data.tilewidth  # e.g. 16 or 32

    map_width  = tmx_data.width  * TILE_SIZE
    map_height = tmx_data.height * TILE_SIZE

    # --- Build collision rects from tile custom properties ---
    collision_rects = []
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            for x, y, gid in layer:
                if gid == 0:
                    continue
                props = tmx_data.get_tile_properties_by_gid(gid)
                if props and props.get('collidable'):
                    collision_rects.append(
                        pygame.Rect(
                            x * TILE_SIZE,
                            y * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE
                        )
                    )

    # --- Player Setup ---
    SCREEN_W, SCREEN_H = screen.get_size()
    player_size = TILE_SIZE
    player_rect = pygame.Rect(
        map_width  // 2,
        map_height // 2,
        player_size,
        player_size
    )
    player_speed = 3
    player_color = (255, 50, 50)  # red placeholder until you have a sprite

    # --- Camera ---
    camera_x = 0
    camera_y = 0

    def update_camera():
        camera_x = player_rect.centerx - SCREEN_W // 2
        camera_y = player_rect.centery - SCREEN_H // 2
        camera_x = max(0, min(camera_x, map_width  - SCREEN_W))
        camera_y = max(0, min(camera_y, map_height - SCREEN_H))
        return camera_x, camera_y

    # --- Pre-render map layers to surfaces for performance ---
    def render_map_surface():
        surf = pygame.Surface((map_width, map_height))
        for layer in tmx_data.visible_layers:
            if hasattr(layer, 'data'):
                for x, y, gid in layer:
                    if gid == 0:
                        continue
                    tile = tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        surf.blit(tile, (x * TILE_SIZE, y * TILE_SIZE))
        return surf

    map_surface = render_map_surface()

    running = True
    while running:
        clock.tick(60)

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return  # Go back to main menu

        # --- Movement ---
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -player_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy =  player_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -player_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx =  player_speed

        # --- Collision (horizontal) ---
        player_rect.x += dx
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                if dx > 0:
                    player_rect.right = rect.left
                elif dx < 0:
                    player_rect.left  = rect.right

        # --- Collision (vertical) ---
        player_rect.y += dy
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                if dy > 0:
                    player_rect.bottom = rect.top
                elif dy < 0:
                    player_rect.top    = rect.bottom

        # --- Keep player inside map bounds ---
        player_rect.clamp_ip(pygame.Rect(0, 0, map_width, map_height))

        # --- Camera ---
        camera_x, camera_y = update_camera()

        # --- Draw ---
        screen.blit(map_surface, (-camera_x, -camera_y))

        # Draw player (red square placeholder)
        pygame.draw.rect(
            screen,
            player_color,
            pygame.Rect(
                player_rect.x - camera_x,
                player_rect.y - camera_y,
                player_rect.width,
                player_rect.height
            )
        )

        # ESC hint
        font = pygame.font.SysFont("consolas", 18)
        hint = font.render("ESC = Back to Menu", True, (255, 255, 255))
        screen.blit(hint, (10, 10))

        pygame.display.flip()
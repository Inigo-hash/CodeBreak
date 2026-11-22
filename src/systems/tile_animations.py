"""Runtime support for Tiled animated tile layers.

PyTMX loads each animation's frame GIDs and durations into tile properties,
but get_tile_image_by_gid() returns only one image. This renderer advances
those frames and patches only the affected cells in the pre-scaled map.
"""

import pygame


def _normalise_frames(raw_frames):
    """Return (frame_gid, duration_ms) pairs from PyTMX AnimationFrames."""
    frames = []
    for frame in raw_frames or ():
        gid = getattr(frame, "gid", None)
        duration = getattr(frame, "duration", None)
        if gid is None or duration is None:
            try:
                gid, duration = frame
            except (TypeError, ValueError):
                continue
        frames.append((int(gid), max(1, int(duration))))
    return tuple(frames)


def _frame_index(frames, elapsed_ms):
    """Choose the animation frame for elapsed milliseconds in its cycle."""
    cycle_ms = sum(duration for _gid, duration in frames)
    if not frames or cycle_ms <= 0:
        return 0

    position = int(elapsed_ms) % cycle_ms
    for index, (_gid, duration) in enumerate(frames):
        if position < duration:
            return index
        position -= duration
    return len(frames) - 1


class AnimatedTileRenderer:
    """Animate placed Tiled tile-layer cells on an existing scaled map surface."""

    def __init__(self, tmx_data, tile_size, zoom):
        self.tmx_data = tmx_data
        self.tile_size = int(tile_size)
        self.zoom = float(zoom)

        self.animations = {
            int(gid): frames
            for gid, properties in getattr(tmx_data, "tile_properties", {}).items()
            if (frames := _normalise_frames(properties.get("frames")))
        }

        # Preserve the visible tile-layer order for each cell. When an
        # animated tile changes, redraw the complete stack at this cell so
        # transparent pixels still reveal the correct lower layers.
        self.cell_layers = {}
        self.cells_by_gid = {}
        for layer in tmx_data.visible_layers:
            if not hasattr(layer, "data"):
                continue
            for x, y, gid in layer:
                gid = int(gid)
                if not gid:
                    continue
                cell = (int(x), int(y))
                self.cell_layers.setdefault(cell, []).append(gid)
                if gid in self.animations:
                    self.cells_by_gid.setdefault(gid, set()).add(cell)

        self.started_at_ms = None
        self.frame_indices = {}
        self.scaled_images = {}
        # Track painted frames so off-screen cells can catch up when visible.
        self.cell_animation_state = {}
        # Cache each fully composited animated cell/frame combination. The
        # Stage 3 lava field has many repeated cells; composing the layer
        # stack on every animation tick causes visible gameplay stalls.
        self.composed_cells = {}
        self.animated_cells = {
            cell: tuple(gid for gid in layers if gid in self.animations)
            for cell, layers in self.cell_layers.items()
            if any(gid in self.animations for gid in layers)
        }

    @property
    def has_animations(self):
        return bool(self.cells_by_gid)

    def _scaled_image(self, gid, size):
        key = (gid, size)
        image = self.scaled_images.get(key)
        if image is None:
            source = self.tmx_data.get_tile_image_by_gid(gid)
            if source is None:
                return None
            image = pygame.transform.scale(source, size)
            self.scaled_images[key] = image
        return image

    def update(self, map_surface, now_ms, viewport=None):
        """Advance animations, repainting only animated cells in the visible area.

        viewport is an optional (x, y, width, height) rectangle in scaled
        map-surface coordinates. Omitting it updates every animated cell.
        """
        if not self.has_animations:
            return 0

        if self.started_at_ms is None:
            self.started_at_ms = int(now_ms)

        elapsed_ms = max(0, int(now_ms) - self.started_at_ms)
        for gid, frames in self.animations.items():
            if gid in self.cells_by_gid:
                self.frame_indices[gid] = _frame_index(frames, elapsed_ms)

        if viewport is None:
            cells = self.animated_cells.keys()
        else:
            view_x, view_y, view_w, view_h = viewport
            tile_pixels = self.tile_size * self.zoom
            left = max(0, int(view_x // tile_pixels))
            top = max(0, int(view_y // tile_pixels))
            right = min(self.tmx_data.width, int((view_x + view_w + tile_pixels - 1) // tile_pixels))
            bottom = min(self.tmx_data.height, int((view_y + view_h + tile_pixels - 1) // tile_pixels))
            cells = (
                (x, y)
                for y in range(top, bottom)
                for x in range(left, right)
                if (x, y) in self.animated_cells
            )

        changed_cells = 0
        for cell in cells:
            animation_gids = self.animated_cells[cell]
            state = tuple((gid, self.frame_indices.get(gid, 0)) for gid in animation_gids)
            if self.cell_animation_state.get(cell) == state:
                continue

            x, y = cell
            left = round(x * self.tile_size * self.zoom)
            top = round(y * self.tile_size * self.zoom)
            right = round((x + 1) * self.tile_size * self.zoom)
            bottom = round((y + 1) * self.tile_size * self.zoom)
            size = (max(1, right - left), max(1, bottom - top))
            destination = (left, top)
            cell_rect = pygame.Rect(left, top, *size)

            # Compose the full layer stack once for this cell/frame state.
            # Blitting one cached surface per changed cell avoids repeated
            # per-layer work during the large Stage 3 lava animation.
            cache_key = (cell, state)
            composed = self.composed_cells.get(cache_key)
            if composed is None:
                composed = pygame.Surface(size, pygame.SRCALPHA)
                for base_gid in self.cell_layers[cell]:
                    frames = self.animations.get(base_gid)
                    draw_gid = frames[self.frame_indices.get(base_gid, 0)][0] if frames else base_gid
                    image = self._scaled_image(draw_gid, size)
                    if image is not None:
                        composed.blit(image, (0, 0))
                self.composed_cells[cache_key] = composed

            # Clear the previous frame before drawing the complete stack,
            # matching the renderer's original repaint behavior.
            map_surface.fill((0, 0, 0), cell_rect)
            map_surface.blit(composed, destination)
            self.cell_animation_state[cell] = state
            changed_cells += 1

        return changed_cells

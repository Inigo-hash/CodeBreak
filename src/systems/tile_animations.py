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
        # Cells whose animation frame changed but which were outside the
        # camera viewport. Keep them pending until they become visible.
        self.pending_cells = set()

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
        """Advance animations and redraw changed cells visible to the camera.

        viewport is (left, top, width, height) in scaled map-surface pixels.
        Off-screen cells remain pending until the camera brings them into
        view. Omitting viewport redraws all changed cells.
        """
        if not self.has_animations:
            return 0

        if self.started_at_ms is None:
            self.started_at_ms = int(now_ms)

        elapsed_ms = max(0, int(now_ms) - self.started_at_ms)
        changed_gids = set()

        for gid, frames in self.animations.items():
            if gid not in self.cells_by_gid:
                continue
            index = _frame_index(frames, elapsed_ms)
            if self.frame_indices.get(gid) != index:
                self.frame_indices[gid] = index
                changed_gids.add(gid)

        # Preserve off-screen changes until those cells enter the viewport.
        for gid in changed_gids:
            self.pending_cells.update(self.cells_by_gid[gid])

        if not self.pending_cells:
            return 0

        if viewport is None:
            visible_cells = self.pending_cells
        else:
            view_left, view_top, view_width, view_height = viewport
            view_right = view_left + view_width
            view_bottom = view_top + view_height
            scaled_tile = self.tile_size * self.zoom
            first_x = max(0, int(view_left // scaled_tile))
            last_x = int((view_right - 1e-9) // scaled_tile)
            first_y = max(0, int(view_top // scaled_tile))
            last_y = int((view_bottom - 1e-9) // scaled_tile)
            visible_cells = {
                (x, y)
                for x in range(first_x, last_x + 1)
                for y in range(first_y, last_y + 1)
                if (x, y) in self.pending_cells
            }

        for x, y in visible_cells:
            left = round(x * self.tile_size * self.zoom)
            top = round(y * self.tile_size * self.zoom)
            right = round((x + 1) * self.tile_size * self.zoom)
            bottom = round((y + 1) * self.tile_size * self.zoom)
            size = (max(1, right - left), max(1, bottom - top))
            destination = (left, top)
            cell_rect = pygame.Rect(left, top, *size)

            # Keep the original complete layer-stack composition for each cell.
            map_surface.fill((0, 0, 0), cell_rect)
            for base_gid in self.cell_layers[(x, y)]:
                draw_gid = base_gid
                frames = self.animations.get(base_gid)
                if frames:
                    frame_index = self.frame_indices.get(base_gid, 0)
                    draw_gid = frames[frame_index][0]

                image = self._scaled_image(draw_gid, size)
                if image is not None:
                    map_surface.blit(image, destination)

        self.pending_cells.difference_update(visible_cells)
        return len(visible_cells)

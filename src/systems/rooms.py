"""Room selection, independent map checkpoints, and hold interaction state."""
from copy import deepcopy
from src.data.rooms import ROOM_STAGES

# Keys/time/topics/inventory belong to the stage or player, not a room.
ROOM_CHECKPOINT_FIELDS = ('map_position', 'map_layout_version', 'stage_progress')


def room_for(stage_id, state):
    config = ROOM_STAGES.get(stage_id)
    if not config:
        return None, None
    room_id = state.get('room_id') or config['default']
    if room_id not in config['rooms']:
        room_id = config['default']
    return room_id, config['rooms'][room_id]


def world_for_room(stage_id, world, state):
    room_id, room = room_for(stage_id, state)
    result = dict(world)
    if room:
        result.update(map=room['map'], room_spawn=room['spawn'],
                      zoom=ROOM_STAGES[stage_id]['zoom'],
                      follow_edges=ROOM_STAGES[stage_id]['follow_edges'])
        if room_id != ROOM_STAGES[stage_id]['default']:
            result.update(zones=[{'name': room['name'], 'rect': (0, 0, 1, 1)}],
                          encounters=(), path_layer=None, path_gids=frozenset(),
                          map_layout_version=1, legacy_shift_tiles=(0, 0))
    return result


def transition_room(state, stage_id, route_id, tile_size=16):
    current_id, current = room_for(stage_id, state)
    if not current:
        raise ValueError('This stage has no room routes.')
    route = next((r for r in current['routes'] if r['id'] == route_id), None)
    if route is None:
        raise ValueError('Unknown room passage.')
    target_id = route['target']
    target = ROOM_STAGES[stage_id]['rooms'][target_id]
    result = deepcopy(state)
    checkpoints = result.get('room_checkpoints') or {}
    result['room_checkpoints'] = checkpoints
    checkpoints[current_id] = {key: deepcopy(state.get(key)) for key in ROOM_CHECKPOINT_FIELDS}
    target_checkpoint = checkpoints.get(target_id, {})
    result.update(room_id=target_id, stage_progress=deepcopy(target_checkpoint.get('stage_progress') or {}),
                  map_layout_version=target_checkpoint.get('map_layout_version') or 1)
    # Use this passage's arrival, rather than a stale saved position elsewhere.
    result['map_position'] = [v * tile_size for v in target['arrivals'][route['arrival']]]
    return result


class PassageHold:
    """Release E once after loading; leaving/releasing cancels partial progress."""
    def __init__(self, duration=1.0):
        self.duration = max(0.1, float(duration))
        self.ready = False
        self.route_id = None
        self.elapsed = 0.0

    @property
    def progress(self):
        return min(1.0, self.elapsed / self.duration)

    def update(self, route_id, held, dt, blocked=False):
        if not held:
            self.ready = True
        if blocked:
            self.ready = False
        if not self.ready or not held or not route_id or blocked:
            self.route_id = None
            self.elapsed = 0.0
            return False
        if self.route_id != route_id:
            self.route_id = route_id
            self.elapsed = 0.0
        self.elapsed += max(0.0, dt)
        if self.elapsed >= self.duration:
            self.ready = False
            return True
        return False

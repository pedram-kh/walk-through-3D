"""Stop 04, the creative cycle (landing section 13) (Blender 4.5 LTS, CPU render).

The cycle ring on the left of the frame (a thin ring with a faint disc), the four
stage spheres (Strategy top, Testing right, Iteration bottom, Scale left), the signal
sphere and its trail arc, and the Catalyst mark in the centre (extruded from core.svg,
the landing's CycleCore outline) with its glowing core square. All text is HTML (title,
the four rows on the right, the four stage labels). No particles (the flat version has no current).
Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python stops/04-cycle/build.py
Outputs beside this file:
  poster.jpg, stop.blend     preview render (also the fallback poster) and editable scene
  stop.glb                   the mark, and the disc (for the route's clearance check)
  stop.json                  contract: rest camera, brief, ring
"""
import bpy, json, math, random, struct, sys
from pathlib import Path
from mathutils import Vector, Matrix, Euler

OUT = Path(__file__).resolve().parent
SEED = 41

# What was agreed for this stop (the five content questions), kept in stop.json.
BRIEF = {
    'status': 'approved 2026-10-05',
    'route': "Landing section 13 'Creative cycle' is stop 04; landing sections 03-12 are skipped for now "
             '(may be added later).',
    'text': "HTML: the title 'Creative cycle' and the four rows (01 Strategy. 02 Testing. 03 Iteration. "
            "04 Scale.). 3D: the four stage labels on the ring (they follow the turning ring, facing the camera) "
            "and the list's lines and underlines (changed 2026-10-04: only the text goes up with the curtain). "
            "No section label (no '13 — Creative cycle'). The whole section fits one viewport: ring on the "
            "left, list on the right.",
    'buttons': 'The four list rows (HTML). The stage spheres on the ring are not buttons.',
    'button_behaviour': "As the landing page: the active row's text turns white and moves 12 px right, its "
                        'number turns teal, and a violet-blue-teal underline grows across it. Hover or click '
                        'moves the signal to that stage and holds it there; leaving lets the cycle carry on. '
                        'As the camera arrives and leaves: like the hero (HTML on the section, which scrolls '
                        'with the curtain).',
    'scene_behaviour': 'The ring turns slowly on its vertical axis (one turn in 30 s; changed 2026-10-04). '
                       'Idle: the signal sphere and its trail go round the ring clockwise like the landing '
                       '(1.8 s per stage, eased settle at each stage); the stage it reaches lights in its colour '
                       '(#9B6BC4, #6F9CC6, #3FA9B8, #2FC4BA) with a glow. Cursor: only the Catalyst mark tilts '
                       'and lifts a little; the ring does not. The current parts around the cursor (same at '
                       'every stop). Arrives frozen and black and white; colour and motion once live.',
    'current': 'Arrives from below, goes around the outside of the ring and leaves through the left of the screen.',
    'media': "The Catalyst mark from the site (the landing's CycleCore SVG) in 3D, with its violet-blue-cyan "
             'glowing core. Ring, stage dots (spheres), signal, trail and glows built in 3D.',
    'transition_in': 'tilt up, same move as before (half circle radius 8, 60 degrees, travel 8)',
}
CAMERA_AT = (0.0, -11.0, 0.0)
CAMERA_LENS = 28
FRAME = (1616, 875)
REST_DEPTH = 11.0

# ---- The ring (landing: CreativeCycleEngine, 1 px ring at 14% white, 16 px stage dots,
# 8 px signal, a 140-degree trail behind it, the mark at 21% of the ring's width) ----------
RING_CENTRE = (0.285, 0.5)     # in the frame (0..1 from the top-left)
RING_RADIUS = 0.29             # as a share of the frame height
STAGES = ['Strategy', 'Testing', 'Iteration', 'Scale']   # clockwise from the top
STAGE_COLORS = ['#9B6BC4', '#6F9CC6', '#3FA9B8', '#2FC4BA']
STAGE_PX, SIGNAL_PX, RING_PX = 16, 8, 1.5                # landing sizes in px (ring height 508 px)
TRAIL_DEG = 140
SIGNAL_DEG = 10                # where the signal rests in the poster (degrees clockwise from the top)
MARK_SHARE = 0.21              # mark width / ring diameter
MARK_DEPTH = 0.12              # extrusion, as a share of the mark's width
CORE_SHARE = 136.34 / 603.5    # glowing core square / mark width (from the SVG)

# Poster colours (linear): the browser draws these with its own shaders (stop.js)
COLORS = {'Ring': (0.0168,) * 3, 'Disc': (0.0012, 0.0008, 0.002), 'Stage': (0.03, 0.03, 0.03), 'Signal': (1.0, 1.0, 1.0),
          'Trail': (0.16, 0.48, 0.46), 'Mark': (0.68, 0.68, 0.68), 'Core': (0.12, 0.08, 0.3), 'Active': (0.33, 0.15, 0.55)}


def hex_rgb(h):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb)


def y_up(v):
    return [round(v[0], 5), round(v[2], 5), round(-v[1], 5)]


# ---- Scene and camera ----------------------------------------------------------
random.seed(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = FRAME
cam_data = bpy.data.cameras.new('Stop camera')
cam_data.lens = CAMERA_LENS
camera = bpy.data.objects.new('Stop camera', cam_data)
scene.collection.objects.link(camera)
camera.location = CAMERA_AT
target = Vector((0, 0, 0))
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera
bpy.context.view_layer.update()
_frame = [Vector(c) / -c[2] for c in cam_data.view_frame(scene=scene)]   # frame corners at depth 1
FRAME_LEFT, FRAME_RIGHT = min(c.x for c in _frame), max(c.x for c in _frame)
FRAME_TOP, FRAME_BOTTOM = max(c.y for c in _frame), min(c.y for c in _frame)
FRAME_W, FRAME_H = FRAME_RIGHT - FRAME_LEFT, FRAME_TOP - FRAME_BOTTOM      # frame size at depth 1


def screen_point(x, y, depth):
    """World point that lands at (x, y) in the frame (0..1 from top-left), depth units ahead."""
    local = Vector((FRAME_LEFT + x * FRAME_W, FRAME_TOP - y * FRAME_H, -1)) * depth
    return camera.matrix_world @ local


def emission(name, color, strength=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    em, out = nodes.new('ShaderNodeEmission'), nodes.new('ShaderNodeOutputMaterial')
    em.inputs['Color'].default_value = (*color, 1)
    em.inputs['Strength'].default_value = strength
    mat.node_tree.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return mat


def plane(name, width, height, material):
    hw, hh = width / 2, height / 2
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(-hw, 0, -hh), (hw, 0, -hh), (hw, 0, hh), (-hw, 0, hh)], [], [(0, 1, 2, 3)])
    uv = mesh.uv_layers.new(name='UVMap')
    for loop, co in zip(uv.data, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        loop.uv = co
    mesh.materials.append(material)
    ob = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(ob)
    return ob



# ---- Ring geometry (all in the plane depth 11 ahead of the camera) ------------------------
px = FRAME_H * REST_DEPTH / FRAME[1]                       # one frame pixel, in scene units
centre = screen_point(*RING_CENTRE, REST_DEPTH)
radius = RING_RADIUS * FRAME_H * REST_DEPTH
mats = {name: emission(name, rgb) for name, rgb in COLORS.items()}
objects = []


def on_ring(deg, r=None):
    """Point on the ring, degrees clockwise from the top as seen from the camera."""
    a = math.radians(deg)
    return centre + Vector((math.sin(a), 0, math.cos(a))) * (radius if r is None else r)


def torus(name, major, minor, material, arc_deg=360.0, start_deg=0.0, segments=256, sides=12):
    """Ring (or arc) around `centre` in the camera-facing plane; arcs run clockwise from start_deg."""
    verts, faces = [], []
    steps = max(8, int(segments * arc_deg / 360))
    closed = arc_deg >= 360
    rings = steps if closed else steps + 1
    for i in range(rings):
        deg = start_deg + arc_deg * i / steps
        a = math.radians(deg)
        out = Vector((math.sin(a), 0, math.cos(a)))
        for j in range(sides):
            b = 2 * math.pi * j / sides
            verts.append(centre + out * (major + minor * math.cos(b)) + Vector((0, minor * math.sin(b), 0)))
    for i in range(steps):
        for j in range(sides):
            a0, a1 = i * sides + j, i * sides + (j + 1) % sides
            b0, b1 = ((i + 1) % rings) * sides + j, ((i + 1) % rings) * sides + (j + 1) % sides
            faces.append((a0, a1, b1, b0))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for v in verts], [], faces)
    mesh.materials.append(material)
    ob = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(ob)
    return ob


def sphere(name, location, r, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r, location=location)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return ob


objects.append(torus('Ring', radius, RING_PX * px / 2, mats['Ring']))
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=radius, fill_type='TRIFAN', location=centre + Vector((0, 0.02, 0)),
                                  rotation=(math.radians(90), 0, 0))
disc = bpy.context.active_object
disc.name = 'Disc'
disc.data.materials.append(mats['Disc'])
objects.append(disc)
stages = []
for i, label in enumerate(STAGES):
    p = on_ring(i * 90)
    objects.append(sphere(f'Stage_{i}', p, STAGE_PX * px / 2, mats['Active' if i == 0 else 'Stage']))
    stages.append({'label': label, 'deg': i * 90, 'color': STAGE_COLORS[i], 'centre': y_up(p)})
objects.append(sphere('Signal', on_ring(SIGNAL_DEG), SIGNAL_PX * px / 2, mats['Signal']))
objects.append(torus('Trail', radius, RING_PX * px * 0.9, mats['Trail'], arc_deg=TRAIL_DEG, start_deg=SIGNAL_DEG - TRAIL_DEG))

# The mark: core.svg's outline, extruded, facing the camera; the glowing core square inside it.
for addon in ('io_curve_svg',):
    try:
        bpy.ops.preferences.addon_enable(module=addon)
    except Exception:
        pass
before = set(bpy.data.objects)
bpy.ops.import_curve.svg(filepath=str(OUT / 'core.svg'))
curves = [o for o in bpy.data.objects if o not in before and o.type == 'CURVE']
mark = curves[0]
for o in curves[1:]:
    bpy.data.objects.remove(o)
bpy.context.view_layer.objects.active = mark
mark.select_set(True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
width_now = mark.dimensions.x
mark_w = MARK_SHARE * 2 * radius
scale = mark_w / width_now
mark.data.extrude = MARK_DEPTH * mark_w / scale / 2
mark.data.dimensions = '2D'
mark.data.fill_mode = 'BOTH'
mark.data.resolution_u = 5                                 # enough for the mark's rounded corners
mark.scale = (scale, scale, scale)
mark.rotation_euler = (math.radians(90), 0, 0)             # SVG plane (XY) -> facing the camera (XZ)
mark.location = centre
bpy.ops.object.convert(target='MESH')
mark.name = 'Mark'
mark.data.materials.clear()
mark.data.materials.append(mats['Mark'])
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
objects.append(mark)
core = plane('Core', CORE_SHARE * mark_w, CORE_SHARE * mark_w, mats['Core'])
core.location = centre + Vector((0, MARK_DEPTH * mark_w * 0.1, 0))
objects.append(core)

ring = {'centre': y_up(centre), 'radius': round(radius, 4), 'px': round(px, 6), 'frame_centre': list(RING_CENTRE),
        'radius_share_of_height': RING_RADIUS, 'stages': stages, 'signal_deg': SIGNAL_DEG, 'trail_deg': TRAIL_DEG,
        'stage_seconds': 1.8, 'mark_width': round(mark_w, 4), 'mark_depth': round(MARK_DEPTH * mark_w, 4),
        'core_width': round(CORE_SHARE * mark_w, 4)}

# ---- Render -----------------------------------------------------------------------
world = bpy.data.worlds.new('Black')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.00061, 0.00061, 0.00121, 1)
scene.world = world
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.cycles.max_bounces = 1
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 85
scene.render.filepath = str(OUT / 'poster.jpg')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'stop.blend'))
bpy.ops.render.render(write_still=True)

# ---- Browser export ---------------------------------------------------------------
bpy.ops.object.select_all(action='DESELECT')
for ob in (mark, disc):            # the browser builds the ring, spheres and glows from stop.json
    ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT / 'stop.glb'), export_format='GLB', use_selection=True,
                          export_materials='NONE', export_animations=False)

Y_UP = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))
q = (Y_UP @ camera.matrix_world.to_3x3()).to_quaternion()
(OUT / 'stop.json').write_text(json.dumps({
    'id': '04-cycle',
    'blender': bpy.app.version_string,
    'rest': {'position': y_up(camera.location), 'quaternion': [round(v, 6) for v in (q.x, q.y, q.z, q.w)],
             'horizontal_fov_deg': round(math.degrees(2 * math.atan(cam_data.sensor_width / 2 / cam_data.lens)), 3),
             'design_aspect': round(FRAME[0] / FRAME[1], 4)},
    'brief': BRIEF,
    'ring': ring,
}, indent=1))
print(f'STOP_DONE 04-cycle objects={len(objects)}')

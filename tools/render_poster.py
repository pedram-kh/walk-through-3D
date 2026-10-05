"""Re-render a stop's poster from its saved scene (Blender 4.5 LTS, CPU render).

Opens stops/<id>/stop.blend, removes the particle objects (dust and current: this flat
version has none), saves the .blend and renders poster.jpg next to it. Nothing else in the
scene changes, so the approved layout stays exactly as it is.

  Blender --background stops/<id>/stop.blend --python tools/render_poster.py
"""
import bpy
from pathlib import Path

PARTICLES = {'Galaxy_dust', 'Galaxy_current', 'Current'}

folder = Path(bpy.data.filepath).parent
for ob in [o for o in bpy.data.objects if o.name in PARTICLES]:
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)

scene = bpy.context.scene
scene.render.filepath = str(folder / 'poster.jpg')
bpy.ops.wm.save_as_mainfile(filepath=str(folder / 'stop.blend'))
bpy.ops.render.render(write_still=True)
print('POSTER_DONE', folder.name)

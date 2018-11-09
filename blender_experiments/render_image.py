import bpy
import mathutils
import os
import sys
sys.path.append('/home/user1/GitHubRepos/pix2scene/blender_experiments')

from render_image_functions import *
from render_image_params import opt

start = time.time()

# Fix the image size
bpy.context.scene.render.resolution_x = opt.width
bpy.context.scene.render.resolution_y = opt.height
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.image_settings.compression = 0

scene = bpy.data.scenes["Scene"]

# Delete all objects in scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ADD PLANES
plane_size = 2
# XY
bpy.ops.mesh.primitive_plane_add(radius=plane_size, location=(plane_size, plane_size, 0))
# YZ
bpy.ops.mesh.primitive_plane_add(radius=plane_size, location=(0, 0, 0))
bpy.ops.transform.rotate(value=-np.pi/2, axis=(0, 1, 0))
bpy.ops.transform.translate(value=(0, plane_size, plane_size))
# ZX
bpy.ops.mesh.primitive_plane_add(radius=plane_size, location=(0, 0, 0))
bpy.ops.transform.rotate(value=-np.pi/2, axis=(1, 0, 0))
bpy.ops.transform.translate(value=(plane_size, 0, plane_size))


# ADD OBJECT

# Import obj
imported_object = bpy.ops.import_scene.obj(filepath=opt.obj_filepath)

# Select the object
# obj_object = bpy.context.selected_objects[0]
for key in bpy.data.objects.keys():
    if 'Camera' not in bpy.data.objects[key] and 'Point' not in bpy.data.objects[key]:
        break

bpy.data.objects[key].select = True

# Find objects centre
def find_center(o):
    vcos = [ o.matrix_world * v.co for v in o.data.vertices ]
    findCenter = lambda l: ( max(l) + min(l) ) / 2
    x,y,z  = [ [ v[i] for v in vcos ] for i in range(3) ]
    return [ findCenter(axis) for axis in [x,y,z] ]

o = bpy.data.objects[key]
obj_center = find_center(o)

# Translate obj to origin
bpy.ops.transform.translate(value=list(-np.array(obj_center)))

# Flip it wrt X
bpy.ops.transform.rotate(value=np.pi, axis=(1, 0, 0))

# Find its max dimension
# max_dimension = max(bpy.context.selected_objects[0].dimensions)
max_dimension = max(bpy.data.objects[key].dimensions)

# Resize obj with a scale
bpy.ops.transform.resize(value=(opt.new_max_dimension/max_dimension, opt.new_max_dimension/max_dimension, opt.new_max_dimension/max_dimension))

# Rotate obj
rot_angle = np.random.random(opt.batch_size)*2*np.pi
bpy.ops.transform.rotate(value=rot_angle[i], axis=(0, 0, 1))

# Recenter it
o = bpy.data.objects[key]
obj_center = find_center(o)
bpy.ops.transform.translate(value=list(-np.array(obj_center)))

# Translate obj, or set it to a location
bpy.ops.transform.translate(value=(opt.new_max_dimension/2, opt.new_max_dimension/2, opt.new_max_dimension/2))
# bpy.context.selected_objects[0].location = (opt.new_max_dimension/2, opt.new_max_dimension/2, opt.new_max_dimension/2)

def obj_random_rot(rot_angle=None):
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    # Select our object
    bpy.data.objects[key].select = True
    # Find its center
    obj_center = find_center(o)
    # Translate to origin
    bpy.ops.transform.translate(value=list(-np.array(obj_center)))
    # Rotate about Z axis by random value
    if rot_angle is None:
        rot_angle = np.random.random()*2*np.pi
    bpy.ops.transform.rotate(value=rot_angle, axis=(0, 0, 1))
    # Translate back to good place
    bpy.ops.transform.translate(value=(opt.new_max_dimension/2, opt.new_max_dimension/2, opt.new_max_dimension/2))


# i = 0
i = 0

# LAMPS
# Generate batch_size # of light positions
light_eps = 0.15
light_pos1 = np.random.rand(opt.batch_size, 3)*opt.cam_dist + light_eps
light_pos2 = np.random.rand(opt.batch_size, 3)*opt.cam_dist + light_eps
light_pos3 = (3, 3, 10)
# Add lamps
bpy.ops.object.lamp_add(type='POINT', location=light_pos1[i])
bpy.ops.object.lamp_add(type='POINT', location=light_pos2[i])
bpy.ops.object.lamp_add(type='POINT', location=light_pos3)
# bpy.ops.object.lamp_add(type='AREA', radius=0.5, location=(0, 0, 10))

# CAMERA
# Generate batch_size # of camera positions
cam_pos = uniform_sample_sphere(radius=opt.cam_dist, num_samples=opt.batch_size, theta_range=np.deg2rad(opt.theta_range), phi_range=np.deg2rad(opt.phi_range))
look_at = mathutils.Vector(opt.lookat)
# Add camera
bpy.ops.object.camera_add(location=cam_pos[i], rotation=(0, 0, 0))
# Set field of view
bpy.context.object.data.angle = np.deg2rad(opt.fovy)
# Set focal length
# bpy.context.object.data.lens = opt.focal_length
# bpy.data.cameras[-1].lens = opt.focal_length
# Look at
camera = bpy.data.objects['Camera']
looking_direction = camera.location - look_at
rot_quat = looking_direction.to_track_quat('Z', 'Y')
camera.rotation_euler = rot_quat.to_euler()


# RENDER
# Make this camera the camera of the scene
bpy.data.scenes[0].camera = bpy.data.objects['Camera']
# Render settings
bpy.data.scenes[0].render.image_settings.file_format = 'PNG'
bpy.data.scenes[0].render.filepath = os.path.join(opt.save_dir, "blender_image_{0:03d}".format(i))
# Don't render shadows
bpy.context.scene.render.use_shadows = False
# Render
if opt.save_image:
    bpy.ops.render.render(write_still=True)

# Delete selected object
# bpy.ops.object.delete(use_global=False)

# If batch_size > 1:
for i in range(1, opt.batch_size):
    # Randomly rotate object
    obj_random_rot(rot_angle[i])
    # Translate camera
    bpy.data.scenes[0].camera.location = cam_pos[i]
    # Make it look at lookat
    looking_direction = camera.location - look_at
    rot_quat = looking_direction.to_track_quat('Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    # Render settings
    bpy.data.scenes[0].render.filepath = os.path.join(opt.save_dir, "blender_image_{0:03d}".format(i))
    # Render image
    if opt.save_image:
        bpy.ops.render.render(write_still=True)

duration = time.time() - start

print("Total: {0:.02f} secs".format(duration))
print("Total per image: {0:.02f} secs".format(duration/opt.batch_size))


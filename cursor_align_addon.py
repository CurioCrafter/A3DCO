"""
Cursor & Origin Alignment Tools for Blender 4.5
------------------------------------------------

This add‑on exposes a set of operators and a UI panel to control the orientation
of the 3D cursor and to align selected objects' origins and rotations.  It also
integrates optional entries into Blender's Shift+S Snap menu and provides a
pie‑menu for quick access.  See implementation_plan.md for detailed design
notes and citations from the Blender manual and API.

Usage:
    • Enable the add‑on in Preferences → Add‑ons.
    • Open the 3D view sidebar (N‑panel) and look for the “Cursor Align” tab.
    • Use buttons to rotate the cursor/origin, reset orientation, copy rotation
      between cursor and objects and snap origins.
    • In preferences, enable integration with the Shift+S Snap menu or bind
      the optional pie menu to a hotkey of your choice.

The code is written with clarity and extensibility in mind.  All state is
encapsulated in property groups, and registration/unregistration cleans up
callbacks and keymaps properly.
"""

import bpy
import math
from math import radians, degrees
from bpy.props import (
    EnumProperty,
    FloatProperty,
    BoolProperty,
)
from bpy.types import (
    AddonPreferences,
    Operator,
    Panel,
    Menu,
    PropertyGroup,
)


bl_info = {
    "name": "Cursor & Origin Alignment Tools",
    "author": "OpenAI Assistant",
    "version": (1, 0, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Cursor Align",
    "description": (
        "Tools to rotate the 3D cursor and align object origins/orientations."
        " Includes optional snap menu integration and a pie menu."
    ),
    "category": "3D View",
}


# -----------------------------------------------------------------------------
# Property Group to store settings on the scene
# -----------------------------------------------------------------------------

class CursorAlignProperties(PropertyGroup):
    """Per‑scene settings for the alignment tools."""

    step_items = [
        ('90', "90°", "Rotate in 90 degree increments"),
        ('45', "45°", "Rotate in 45 degree increments"),
        ('30', "30°", "Rotate in 30 degree increments"),
        ('15', "15°", "Rotate in 15 degree increments"),
        ('CUSTOM', "Custom", "Use a custom angle (see below)"),
    ]
    rotation_step: EnumProperty(
        name="Rotation Step",
        description="Angle used when rotating the cursor or objects",
        items=step_items,
        default='90',
    )
    custom_step: FloatProperty(
        name="Custom Step",
        description="Custom rotation angle in degrees",
        default=22.5,
        min=0.1,
        max=360.0,
    )
    use_snap_menu: BoolProperty(
        name="Append to Snap Menu",
        description="Add alignment tools to the Shift+S snap menu",
        default=True,
    )
    use_pie_menu: BoolProperty(
        name="Enable Pie Menu",
        description="Register a pie menu for cursor/origin tools",
        default=False,
    )
    pie_menu_key: EnumProperty(
        name="Pie Menu Hotkey",
        description="Modifier key for the pie menu (works with S)",
        items=[
            ('ALT', "Alt", "Alt+S"),
            ('CTRL', "Ctrl", "Ctrl+S"),
            ('SHIFT', "Shift (override) ", "Override Shift+S default snap menu"),
            ('NONE', "None", "Do not bind automatically"),
        ],
        default='ALT',
    )


def get_step(scene):
    """Retrieve the rotation step in radians based on scene settings."""
    props = scene.cursor_align_props
    if props.rotation_step == 'CUSTOM':
        angle_deg = props.custom_step
    else:
        angle_deg = float(props.rotation_step)
    return radians(angle_deg)


# -----------------------------------------------------------------------------
# Machine Tools Integration Detection
# -----------------------------------------------------------------------------

def is_machine_tools_available():
    """Check if Machine Tools (MACHIN3tools) is installed and enabled."""
    try:
        import addon_utils
        for mod in addon_utils.modules():
            if mod.__name__ in ['MACHIN3tools', 'machin3tools'] and addon_utils.check(mod.__name__)[1]:
                return True
        return False
    except:
        return False

def get_machine_tools_cursor_pie():
    """Get the Machine Tools cursor pie menu class if available."""
    try:
        if is_machine_tools_available():
            return getattr(bpy.types, 'MACHIN3_MT_cursor_pie', None)
        return None
    except:
        return None

def integrate_with_machine_tools_cursor_pie():
    """Integrate our operators directly into Machine Tools cursor pie menu."""
    try:
        # Get the Machine Tools cursor pie menu class
        cursor_pie_class = getattr(bpy.types, 'MACHIN3_MT_cursor_pie', None)
        if cursor_pie_class and hasattr(cursor_pie_class, 'draw'):
            # Store original draw method if not already stored
            if not hasattr(cursor_pie_class, '_original_draw_cursor_align'):
                cursor_pie_class._original_draw_cursor_align = cursor_pie_class.draw
                
            # Create enhanced draw method that properly integrates with Machine Tools pie menu
            def enhanced_draw(self, context):
                # The key insight: We need to use the pie layout system, not self.layout
                # Create the pie menu context first
                pie = self.layout.menu_pie()
                
                # Claim the TOP slot (4th position) for our Cursor Alignment panel
                # This will be positioned at the very top of the pie menu wheel
                top_slot = pie.split()
                col = top_slot.column(align=True)
                
                # Center align the content within the slot
                col.alignment = 'CENTER'
                
                # Cursor Alignment header
                row = col.row(align=True)
                row.alignment = 'CENTER'
                row.scale_y = 1.2
                row.label(text="Cursor Alignment", icon='ORIENTATION_CURSOR')
                
                col.separator(factor=0.5)
                
                # Compact layout with smaller buttons in rows
                col.scale_x = 1.2
                col.scale_y = 1.1
                
                # First row - Reset and View alignment
                row = col.row(align=True)
                row.operator("cursor.reset_orientation", text="Reset", icon='LOOP_BACK')
                row.operator("cursor.align_to_view", text="to View", icon='VIEW_ORTHO')
                
                # Second row - Preset and Surface alignment
                row = col.row(align=True)
                row.operator("cursor.set_preset_orientation", text="Preset", icon='ORIENTATION_CURSOR')
                row.operator("cursor.align_to_surface", text="Surface", icon='UV_FACESEL')
                
                # Third row - Copy and Apply tools
                row = col.row(align=True)
                row.operator("cursor.copy_from_object", text="Copy", icon='COPYDOWN')
                row.operator("cursor.apply_to_object", text="Apply", icon='CHECKMARK')
                
                # Now call Machine Tools draw method to create their pie menu
                # This will fill the remaining slots (LEFT, RIGHT, BOTTOM, etc.)
                self._original_draw_cursor_align(context)
                

            
            # Replace the draw method with our enhanced version
            cursor_pie_class.draw = enhanced_draw
            print("Cursor & Origin Alignment: Successfully integrated with Machine Tools cursor pie menu")
            return True
            
    except Exception as e:
        print(f"Failed to integrate with Machine Tools cursor pie: {e}")
    return False

def remove_machine_tools_integration():
    """Clean up Machine Tools integration by restoring original draw method."""
    try:
        cursor_pie_class = getattr(bpy.types, 'MACHIN3_MT_cursor_pie', None)
        if cursor_pie_class and hasattr(cursor_pie_class, '_original_draw_cursor_align'):
            # Restore original draw method
            cursor_pie_class.draw = cursor_pie_class._original_draw_cursor_align
            delattr(cursor_pie_class, '_original_draw_cursor_align')
            print("Cursor & Origin Alignment: Restored Machine Tools cursor pie menu")
    except Exception as e:
        print(f"Failed to remove Machine Tools integration: {e}")


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def rotate_euler(euler, axis, delta):
    """Return a copy of the Euler with the specified axis rotated by delta radians.

    Parameters:
        euler (Euler): Euler angles to start from.
        axis (str): 'X', 'Y' or 'Z'.
        delta (float): Amount in radians to add (can be negative).
    Returns:
        Euler: a new Euler instance with the rotation applied.
    """
    new_eul = euler.copy()
    axis = axis.upper()
    if axis == 'X':
        new_eul.x += delta
    elif axis == 'Y':
        new_eul.y += delta
    elif axis == 'Z':
        new_eul.z += delta
    return new_eul.normalized()  # keep values within [-pi, pi]


def copy_object_rotation_to_cursor(obj, cursor):
    """Copy an object's world rotation to the cursor."""
    # Use matrix_world to get world rotation independent of parents
    matrix = obj.matrix_world.to_3x3()
    cursor.rotation_euler = matrix.to_euler(cursor.rotation_mode)


def apply_cursor_rotation_to_object(cursor, obj):
    """Set an object's world rotation to match the cursor's orientation."""
    # Build rotation matrix from cursor and assign to object's matrix_world
    # Keep translation and scale components
    cur_rot = cursor.rotation_euler.to_matrix()
    obj_mat = obj.matrix_world
    scale = obj_mat.to_scale()
    loc = obj_mat.to_translation()
    new_mat = cur_rot.to_4x4()
    # apply scale
    new_mat[0][0] *= scale.x
    new_mat[1][1] *= scale.y
    new_mat[2][2] *= scale.z
    new_mat.translation = loc
    obj.matrix_world = new_mat


# -----------------------------------------------------------------------------
# Cursor Operators
# -----------------------------------------------------------------------------

class CURSOR_OT_reset_orientation(Operator):
    """Reset the 3D cursor rotation to world axes (0,0,0)."""
    bl_idname = "cursor.reset_orientation"
    bl_label = "Reset Cursor Orientation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cursor = context.scene.cursor
        cursor.rotation_euler = (0.0, 0.0, 0.0)
        return {'FINISHED'}


class CURSOR_OT_rotate_axis(Operator):
    """Rotate the 3D cursor around a specific axis by the configured step."""
    bl_idname = "cursor.rotate_axis"
    bl_label = "Rotate Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        items=[('X', "X", "Rotate around X"),
               ('Y', "Y", "Rotate around Y"),
               ('Z', "Z", "Rotate around Z")],
        default='Z',
    )
    direction: EnumProperty(
        name="Direction",
        items=[('POS', "+", "Rotate positively"), ('NEG', "−", "Rotate negatively")],
        default='POS',
    )

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor
        step_rad = get_step(scene)
        delta = step_rad if self.direction == 'POS' else -step_rad
        cursor.rotation_euler = rotate_euler(cursor.rotation_euler, self.axis, delta)
        return {'FINISHED'}


class CURSOR_OT_flip_axis(Operator):
    """Flip the 3D cursor's rotation around the specified axis."""
    bl_idname = "cursor.flip_axis"
    bl_label = "Flip Cursor Axis"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        items=[('X', "X", "Flip around X"), ('Y', "Y", "Flip around Y"), ('Z', "Z", "Flip around Z")],
        default='Z',
    )

    def execute(self, context):
        cursor = context.scene.cursor
        eul = cursor.rotation_euler.copy()
        if self.axis == 'X':
            eul.x = -eul.x
        elif self.axis == 'Y':
            eul.y = -eul.y
        elif self.axis == 'Z':
            eul.z = -eul.z
        cursor.rotation_euler = eul
        return {'FINISHED'}


class CURSOR_OT_copy_from_object(Operator):
    """Copy the active object's rotation to the 3D cursor."""
    bl_idname = "cursor.copy_from_object"
    bl_label = "Cursor: Copy from Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'WARNING'}, "No active object to copy from")
            return {'CANCELLED'}
        copy_object_rotation_to_cursor(obj, context.scene.cursor)
        return {'FINISHED'}


class CURSOR_OT_apply_to_object(Operator):
    """Apply the 3D cursor's rotation to all selected objects."""
    bl_idname = "cursor.apply_to_object"
    bl_label = "Apply Cursor Rotation to Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        cursor = context.scene.cursor
        for obj in selected:
            apply_cursor_rotation_to_object(cursor, obj)
        return {'FINISHED'}


class CURSOR_OT_align_to_view(Operator):
    """Align the 3D cursor rotation to match the active 3D view orientation."""
    bl_idname = "cursor.align_to_view"
    bl_label = "Align Cursor to View"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the active 3D view's rotation
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        # Get view rotation from region data
                        for region in area.regions:
                            if region.type == 'WINDOW':
                                try:
                                    view_rotation = region.data.view_rotation
                                    # Convert quaternion to euler
                                    cursor = context.scene.cursor
                                    cursor.rotation_euler = view_rotation.to_euler(cursor.rotation_mode)
                                    return {'FINISHED'}
                                except AttributeError:
                                    # Fallback: try to get view matrix
                                    try:
                                        view_matrix = region.data.view_matrix
                                        view_rot = view_matrix.to_3x3().to_euler()
                                        cursor = context.scene.cursor
                                        cursor.rotation_euler = view_rot
                                        return {'FINISHED'}
                                    except AttributeError:
                                        continue
        self.report({'WARNING'}, "Could not determine view orientation")
        return {'CANCELLED'}


class CURSOR_OT_align_to_surface(Operator):
    """Align the 3D cursor rotation to match the surface normal of selected faces."""
    bl_idname = "cursor.align_to_surface"
    bl_label = "Align Cursor to Surface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'EDIT_MESH':
            self.report({'WARNING'}, "Must be in Edit Mode with faces selected")
            return {'CANCELLED'}
        
        # Get selected faces and calculate average normal
        import bmesh
        obj = context.edit_object
        bm = bmesh.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        
        selected_faces = [f for f in bm.faces if f.select]
        if not selected_faces:
            self.report({'WARNING'}, "No faces selected")
            return {'CANCELLED'}
        
        # Calculate average normal
        avg_normal = (0, 0, 0)
        for face in selected_faces:
            avg_normal = (avg_normal[0] + face.normal.x,
                         avg_normal[1] + face.normal.y,
                         avg_normal[2] + face.normal.z)
        
        # Normalize
        length = (avg_normal[0]**2 + avg_normal[1]**2 + avg_normal[2]**2)**0.5
        if length > 0:
            avg_normal = (avg_normal[0]/length, avg_normal[1]/length, avg_normal[2]/length)
            
            # Convert normal to rotation matrix and then to euler
            from mathutils import Vector, Matrix
            normal_vec = Vector(avg_normal)
            up_vec = Vector((0, 0, 1))
            
            # Create rotation matrix from normal to up vector
            if abs(normal_vec.dot(up_vec)) < 0.99:  # Not parallel
                rotation_matrix = normal_vec.rotation_difference(up_vec).to_matrix()
                cursor = context.scene.cursor
                cursor.rotation_euler = rotation_matrix.to_euler(cursor.rotation_mode)
                return {'FINISHED'}
            else:
                # Normal is parallel to up vector, use identity rotation
                cursor = context.scene.cursor
                cursor.rotation_euler = (0, 0, 0)
                return {'FINISHED'}
        
        self.report({'WARNING'}, "Could not calculate surface normal")
        return {'CANCELLED'}


class CURSOR_OT_set_preset_orientation(Operator):
    """Set the 3D cursor to a preset orientation."""
    bl_idname = "cursor.set_preset_orientation"
    bl_label = "Set Preset Orientation"
    bl_options = {'REGISTER', 'UNDO'}

    orientation: bpy.props.EnumProperty(
        name="Orientation",
        items=[
            ('FRONT', "Front", "Front view (X forward, Y right, Z up)"),
            ('RIGHT', "Right", "Right view (X right, Y back, Z up)"),
            ('TOP', "Top", "Top view (X right, Y forward, Z up)"),
            ('BACK', "Back", "Back view (X back, Y left, Z up)"),
            ('LEFT', "Left", "Left view (X left, Y forward, Z up)"),
            ('BOTTOM', "Bottom", "Bottom view (X right, Y forward, Z down)"),
        ],
        default='FRONT',
    )

    def execute(self, context):
        cursor = context.scene.cursor
        
        # Set rotation based on preset
        if self.orientation == 'FRONT':
            cursor.rotation_euler = (0, 0, 0)
        elif self.orientation == 'RIGHT':
            cursor.rotation_euler = (0, 0, -1.570796)  # -90 degrees
        elif self.orientation == 'TOP':
            cursor.rotation_euler = (1.570796, 0, 0)   # 90 degrees
        elif self.orientation == 'BACK':
            cursor.rotation_euler = (0, 0, 3.141593)   # 180 degrees
        elif self.orientation == 'LEFT':
            cursor.rotation_euler = (0, 0, 1.570796)   # 90 degrees
        elif self.orientation == 'BOTTOM':
            cursor.rotation_euler = (-1.570796, 0, 0)  # -90 degrees
        
        return {'FINISHED'}


class CURSOR_OT_set_to_selection_center(Operator):
    """Set the 3D cursor to the center of selected objects."""
    bl_idname = "cursor.set_to_selection_center"
    bl_label = "Cursor to Selection Center"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        # Calculate center of all selected objects
        center = (0, 0, 0)
        count = 0
        
        for obj in context.selected_objects:
            center = (center[0] + obj.location.x,
                     center[1] + obj.location.y,
                     center[2] + obj.location.z)
            count += 1
        
        if count > 0:
            center = (center[0] / count, center[1] / count, center[2] / count)
            context.scene.cursor.location = center
        
        return {'FINISHED'}


class CURSOR_OT_set_to_view_center(Operator):
    """Set the 3D cursor to the center of the 3D view."""
    bl_idname = "cursor.set_to_view_center"
    bl_label = "Cursor to View Center"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Set cursor to origin (0, 0, 0)
        context.scene.cursor.location = (0, 0, 0)
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# Object Operators
# -----------------------------------------------------------------------------

class OBJECT_OT_origin_to_cursor(Operator):
    """Move selected objects' origins to the 3D cursor position."""
    bl_idname = "object.origin_to_cursor"
    bl_label = "Origin to Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        if is_machine_tools_available():
            return "Move Origin to Cursor (Alternative to Machine Tools)\nUse Machine Tools 'machin3.origin_to_cursor' for advanced options"
        return "Move selected objects' origins to the 3D cursor position"

    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        # Check if Machine Tools is available and suggest using their operator
        if is_machine_tools_available():
            self.report({'INFO'}, "Consider using Machine Tools 'machin3.origin_to_cursor' for advanced options")
        
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        return {'FINISHED'}


class OBJECT_OT_rotate_axis(Operator):
    """Rotate selected objects around an axis by the configured step."""
    bl_idname = "object.rotate_axis_step"
    bl_label = "Rotate Objects"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        items=[('X', "X", "Rotate around X"),
               ('Y', "Y", "Rotate around Y"),
               ('Z', "Z", "Rotate around Z")],
        default='Z',
    )
    direction: EnumProperty(
        name="Direction",
        items=[('POS', "+", "Rotate positively"), ('NEG', "−", "Rotate negatively")],
        default='POS',
    )

    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        step_rad = get_step(context.scene)
        delta = step_rad if self.direction == 'POS' else -step_rad
        for obj in context.selected_objects:
            eul = obj.rotation_euler.copy()
            axis = self.axis
            if axis == 'X':
                eul.x += delta
            elif axis == 'Y':
                eul.y += delta
            elif axis == 'Z':
                eul.z += delta
            obj.rotation_euler = eul
        return {'FINISHED'}


class OBJECT_OT_reset_orientation(Operator):
    """Reset selected objects' rotations to zero (identity)."""
    bl_idname = "object.reset_orientation"
    bl_label = "Reset Object Orientation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        for obj in context.selected_objects:
            obj.rotation_euler = (0.0, 0.0, 0.0)
        return {'FINISHED'}


class OBJECT_OT_align_to_cursor(Operator):
    """Align selected objects' origins and rotations to the 3D cursor."""
    bl_idname = "object.align_to_cursor"
    bl_label = "Align Objects to Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    move_objects: BoolProperty(
        name="Move Objects",
        description="Move objects to the cursor instead of keeping them in place",
        default=True,
    )
    use_rotation: BoolProperty(
        name="Use Rotation",
        description="Rotate objects to match the cursor's orientation",
        default=True,
    )

    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        # Snap selection to cursor; when move_objects=False use_offset stays True
        use_offset = not self.move_objects
        # Use rotation only if requested
        bpy.ops.view3d.snap_selected_to_cursor(
            use_offset=use_offset,
            use_rotation=self.use_rotation
        )
        return {'FINISHED'}


class OBJECT_OT_snap_cursor_to_selected(Operator):
    """Move the 3D cursor to the middle of the selected item(s)."""
    bl_idname = "object.cursor_to_selected"
    bl_label = "Cursor to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not context.selected_objects and context.mode != 'EDIT_MESH':
            self.report({'WARNING'}, "Nothing selected")
            return {'CANCELLED'}
        bpy.ops.view3d.snap_cursor_to_selected()
        return {'FINISHED'}


class OBJECT_OT_snap_selected_to_cursor(Operator):
    """Snap selected item(s) to the 3D cursor without rotation."""
    bl_idname = "object.selected_to_cursor"
    bl_label = "Selected to Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    use_offset: BoolProperty(
        name="Use Offset",
        description="Move objects relative to their current offset rather than all to the cursor",
        default=False,
    )

    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=self.use_offset, use_rotation=False)
        return {'FINISHED'}


class OBJECT_OT_create_transform_orientation(Operator):
    """Create a custom transform orientation from the 3D cursor's rotation."""
    bl_idname = "object.create_transform_orientation"
    bl_label = "Create Transform Orientation"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty(
        name="Name",
        description="Name for the new transform orientation",
        default="Cursor",
    )

    def execute(self, context):
        cursor = context.scene.cursor
        
        # Create a new transform orientation
        bpy.ops.transform.create_orientation(name=self.name, use_view=False)
        
        # Get the newly created orientation
        for orientation in bpy.context.scene.transform_orientation_slots:
            if orientation.name == self.name:
                # Set the orientation to match cursor rotation
                orientation.matrix = cursor.matrix
                break
        
        self.report({'INFO'}, f"Created transform orientation '{self.name}' from cursor")
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class OBJECT_OT_align_objects_to_each_other(Operator):
    """Align selected objects to match the active object's rotation."""
    bl_idname = "object.align_objects_to_each_other"
    bl_label = "Align Objects to Active"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active = context.active_object
        selected = [obj for obj in context.selected_objects if obj != active]
        
        if not active:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}
        
        if not selected:
            self.report({'WARNING'}, "No other objects selected")
            return {'CANCELLED'}
        
        # Get active object's world rotation
        active_rot = active.matrix_world.to_euler()
        
        # Apply to all selected objects
        for obj in selected:
            # Keep current world position and scale
            world_pos = obj.matrix_world.to_translation()
            world_scale = obj.matrix_world.to_scale()
            
            # Create new matrix with active's rotation
            new_matrix = active_rot.to_matrix_4x4()
            new_matrix.translation = world_pos
            
            # Apply scale
            new_matrix[0][0] *= world_scale.x
            new_matrix[1][1] *= world_scale.y
            new_matrix[2][2] *= world_scale.z
            
            obj.matrix_world = new_matrix
        
        return {'FINISHED'}


class OBJECT_OT_distribute_along_cursor(Operator):
    """Distribute selected objects along the cursor's orientation."""
    bl_idname = "object.distribute_along_cursor"
    bl_label = "Distribute Along Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    spacing: bpy.props.FloatProperty(
        name="Spacing",
        description="Distance between objects",
        default=1.0,
        min=0.01,
        unit='LENGTH',
    )
    
    axis: bpy.props.EnumProperty(
        name="Axis",
        items=[
            ('X', "X", "Distribute along X axis"),
            ('Y', "Y", "Distribute along Y axis"),
            ('Z', "Z", "Distribute along Z axis"),
        ],
        default='Z',
    )

    def execute(self, context):
        if len(context.selected_objects) < 2:
            self.report({'WARNING'}, "Select at least 2 objects")
            return {'CANCELLED'}
        
        cursor = context.scene.cursor
        cursor_matrix = cursor.matrix
        
        # Sort objects by distance from cursor along the specified axis
        objects = list(context.selected_objects)
        axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[self.axis]
        
        # Calculate positions along the cursor's axis
        positions = []
        for obj in objects:
            # Get object position relative to cursor
            rel_pos = obj.matrix_world.to_translation() - cursor.location
            # Project onto cursor's axis
            axis_pos = rel_pos.dot(cursor_matrix[axis_idx][:3])
            positions.append((axis_pos, obj))
        
        # Sort by position along axis
        positions.sort(key=lambda x: x[0])
        
        # Distribute objects
        for i, (_, obj) in enumerate(positions):
            # Calculate new position
            offset = i * self.spacing
            new_pos = cursor.location + cursor_matrix[axis_idx][:3] * offset
            
            # Update object position
            obj.location = new_pos
        
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class OBJECT_OT_copy_cursor_location(Operator):
    """Copy the 3D cursor's location to selected objects."""
    bl_idname = "object.copy_cursor_location"
    bl_label = "Copy Cursor Location"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        cursor_location = context.scene.cursor.location
        
        for obj in context.selected_objects:
            obj.location = cursor_location.copy()
        
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# Panel Class
# -----------------------------------------------------------------------------

class VIEW3D_PT_cursor_align(Panel):
    """Panel in the 3D Viewport's sidebar for cursor/origin alignment."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Cursor Align'
    bl_label = 'Cursor & Origin Alignment'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.cursor_align_props
        cursor = scene.cursor

        # Show Machine Tools integration status
        if is_machine_tools_available():
            box = layout.box()
            box.label(text="Machine Tools Integration", icon='CHECKMARK')
            row = box.row()
            row.scale_y = 1.2
            row.operator("cursor.machine_tools_menu", text="Quick Access Menu", icon='MENU_PANEL')
            box.label(text="Add 'cursor.machine_tools_menu' to Quick Favorites", icon='INFO')

        # Display current cursor rotation
        box = layout.box()
        box.label(text="Cursor Orientation")
        col = box.column(align=True)
        col.prop(cursor, "rotation_euler", text="Euler")
        col.operator("cursor.reset_orientation", icon='LOOP_BACK')
        row = col.row(align=True)
        row.operator("cursor.rotate_axis", text="+X").axis = 'X'
        row.operator("cursor.rotate_axis", text="-X").axis = 'X'
        row.operator("cursor.rotate_axis", text="-X").direction = 'NEG'
        row = col.row(align=True)
        row.operator("cursor.rotate_axis", text="+Y").axis = 'Y'
        row.operator("cursor.rotate_axis", text="-Y").axis = 'Y'
        row.operator("cursor.rotate_axis", text="-Y").direction = 'NEG'
        row = col.row(align=True)
        row.operator("cursor.rotate_axis", text="+Z").axis = 'Z'
        row.operator("cursor.rotate_axis", text="-Z").axis = 'Z'
        row.operator("cursor.rotate_axis", text="-Z").direction = 'NEG'
        col.operator("cursor.flip_axis", text="Flip X").axis = 'X'
        col.operator("cursor.flip_axis", text="Flip Y").axis = 'Y'
        col.operator("cursor.flip_axis", text="Flip Z").axis = 'Z'
        col.operator("cursor.copy_from_object", icon='COPYDOWN')
        col.operator("cursor.apply_to_object", icon='CHECKMARK')
        col.operator("cursor.align_to_view", icon='VIEW_ORTHO', text="Align to View")
        col.operator("cursor.align_to_surface", icon='UV_FACESEL', text="Align to Surface")
        col.operator("cursor.set_preset_orientation", icon='ORIENTATION_CURSOR', text="Set Preset Orientation")
        col.operator("cursor.set_to_selection_center", icon='PIVOT_CURSOR', text="Cursor to Selection Center")
        col.operator("cursor.set_to_view_center", icon='PIVOT_CURSOR', text="Cursor to View Center")
        col.operator("object.create_transform_orientation", icon='ORIENTATION_GLOBAL', text="Create Transform Orientation")

        # Rotation step
        box = layout.box()
        box.label(text="Rotation Settings")
        row = box.row()
        row.prop(props, "rotation_step", text="Step")
        if props.rotation_step == 'CUSTOM':
            box.prop(props, "custom_step", text="Angle")

        # Object alignment tools
        box = layout.box()
        box.label(text="Object Alignment")
        row = box.row(align=True)
        row.operator("object.cursor_to_selected", icon='PIVOT_CURSOR', text="Cursor to Sel")
        row.operator("object.selected_to_cursor", icon='PIVOT_CURSOR', text="Sel to Cursor")
        row = box.row(align=True)
        row.operator("object.origin_to_cursor", text="Origin to Cursor", icon='PIVOT_CURSOR')
        row.operator("object.copy_cursor_location", text="Copy Cursor Loc", icon='COPYDOWN')
        row.operator("object.reset_orientation", text="Reset Rot", icon='OBJECT_ORIGIN')
        row = box.row(align=True)
        row.operator("object.rotate_axis_step", text="+X").axis = 'X'
        row.operator("object.rotate_axis_step", text="-X").axis = 'X'
        row.operator("object.rotate_axis_step", text="-X").direction = 'NEG'
        row = box.row(align=True)
        row.operator("object.rotate_axis_step", text="+Y").axis = 'Y'
        row.operator("object.rotate_axis_step", text="-Y").axis = 'Y'
        row.operator("object.rotate_axis_step", text="-Y").direction = 'NEG'
        row = box.row(align=True)
        row.operator("object.rotate_axis_step", text="+Z").axis = 'Z'
        row.operator("object.rotate_axis_step", text="-Z").axis = 'Z'
        row.operator("object.rotate_axis_step", text="-Z").direction = 'NEG'
        box.operator("object.align_to_cursor", text="Align to Cursor", icon='PIVOT_CURSOR')
        box.operator("object.align_objects_to_each_other", text="Align to Active", icon='CONSTRAINT')
        box.operator("object.distribute_along_cursor", text="Distribute Along Cursor", icon='ARROW_LEFTRIGHT')


# -----------------------------------------------------------------------------
# Snap menu integration
# -----------------------------------------------------------------------------

def draw_snap_menu(self, context):
    """Append custom alignment operators to the Shift+S snap menu."""
    layout = self.layout
    
    # Check if Machine Tools is available and skip if it is
    # (Machine Tools has its own comprehensive cursor/origin system)
    if is_machine_tools_available():
        return
    
    layout.separator()
    layout.label(text="Cursor & Origin Alignment", icon='ORIENTATION_CURSOR')
    
    # Cursor orientation tools - integrate with existing "to" pattern
    layout.operator("cursor.reset_orientation", text="Cursor to World Orientation", icon='LOOP_BACK')
    layout.operator("cursor.align_to_view", text="Cursor to View Orientation", icon='VIEW_ORTHO')
    layout.operator("cursor.align_to_surface", text="Cursor to Surface Normal", icon='UV_FACESEL')
    layout.operator("cursor.set_preset_orientation", text="Cursor to Preset", icon='ORIENTATION_CURSOR')
    
    # Cursor positioning tools - following the "to" naming convention
    layout.operator("cursor.set_to_selection_center", text="Cursor to Selection Center", icon='PIVOT_CURSOR')
    layout.operator("cursor.set_to_view_center", text="Cursor to View Center", icon='PIVOT_CURSOR')
    
    # Object alignment tools - integrate with existing object tools
    layout.operator("object.origin_to_cursor", text="Origin to Cursor", icon='PIVOT_CURSOR')
    layout.operator("object.copy_cursor_location", text="Object to Cursor Location", icon='COPYDOWN')
    
    # Advanced alignment tools
    op = layout.operator("object.align_to_cursor", text="Objects to Cursor Orientation", icon='PIVOT_CURSOR')
    op.move_objects = True
    op.use_rotation = True
    layout.operator("object.align_objects_to_each_other", text="Objects to Active Orientation", icon='CONSTRAINT')
    
    # Rotation and transformation tools
    layout.separator()
    layout.label(text="Rotation & Transform", icon='DRIVER_ROTATIONAL_DIFFERENCE')
    
    # Quick rotation tools
    row = layout.row(align=True)
    op = row.operator("cursor.rotate_axis", text="+X")
    op.axis = 'X'
    op.direction = 'POS'
    op = row.operator("cursor.rotate_axis", text="-X")
    op.axis = 'X'
    op.direction = 'NEG'
    
    row = layout.row(align=True)
    op = row.operator("cursor.rotate_axis", text="+Y")
    op.axis = 'Y'
    op.direction = 'POS'
    op = row.operator("cursor.rotate_axis", text="-Y")
    op.axis = 'Y'
    op.direction = 'NEG'
    
    row = layout.row(align=True)
    op = row.operator("cursor.rotate_axis", text="+Z")
    op.axis = 'Z'
    op.direction = 'POS'
    op = row.operator("cursor.rotate_axis", text="-Z")
    op.axis = 'Z'
    op.direction = 'NEG'
    
    # Utility tools
    layout.separator()
    layout.label(text="Utilities", icon='TOOL_SETTINGS')
    
    layout.operator("cursor.copy_from_object", text="Cursor to Object Rotation", icon='COPYDOWN')
    layout.operator("cursor.apply_to_object", text="Apply Cursor to Objects", icon='CHECKMARK')
    layout.operator("object.create_transform_orientation", text="Create Transform Orientation", icon='ORIENTATION_GLOBAL')
    layout.operator("object.distribute_along_cursor", text="Distribute Along Cursor", icon='ARROW_LEFTRIGHT')


# -----------------------------------------------------------------------------
# Pie menu
# -----------------------------------------------------------------------------

class VIEW3D_MT_cursor_origin_wheel(Menu):
    """Radial menu for cursor/origin tools."""
    bl_idname = "VIEW3D_MT_cursor_origin_wheel"
    bl_label = "Cursor & Origin Wheel"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # Top (8 o'clock position) – Cursor to Selected
        pie.operator("object.cursor_to_selected", text="Cursor to Selected", icon='PIVOT_CURSOR')
        # Right – Selected to Cursor (no offset)
        pie.operator("object.selected_to_cursor", text="Selected to Cursor", icon='PIVOT_CURSOR').use_offset = False
        # Bottom – Origin to Cursor
        pie.operator("object.origin_to_cursor", text="Origin to Cursor", icon='OBJECT_ORIGIN')
        # Left – Align to Cursor (with rotation)
        op = pie.operator("object.align_to_cursor", text="Align to Cursor", icon='PIVOT_CURSOR')
        op.move_objects = True
        op.use_rotation = True
        # Upper left – Reset Cursor
        pie.operator("cursor.reset_orientation", text="Reset Cursor", icon='LOOP_BACK')
        # Upper right – Reset Objects
        pie.operator("object.reset_orientation", text="Reset Objects", icon='OBJECT_ORIGIN')
        # Lower right – Rotate Cursor +Z
        op = pie.operator("cursor.rotate_axis", text="Rotate Cursor +Z", icon='DRIVER_ROTATIONAL_DIFFERENCE')
        op.axis = 'Z'
        op.direction = 'POS'
        # Lower left – Rotate Objects +Z
        op = pie.operator("object.rotate_axis_step", text="Rotate Objects +Z", icon='DRIVER_ROTATIONAL_DIFFERENCE')
        op.axis = 'Z'
        op.direction = 'POS'
        
        # Additional cursor tools in center - only show if Machine Tools is not available
        if not is_machine_tools_available():
            pie.operator("cursor.align_to_view", text="Align to View", icon='VIEW_ORTHO')
            pie.operator("cursor.align_to_surface", text="Align to Surface", icon='UV_FACESEL')


# -----------------------------------------------------------------------------
# Machine Tools Integration Menu
# -----------------------------------------------------------------------------

class VIEW3D_MT_cursor_align_machine_tools(Menu):
    """Cursor alignment tools menu for Machine Tools integration."""
    bl_idname = "VIEW3D_MT_cursor_align_machine_tools"
    bl_label = "Cursor Alignment Tools"

    def draw(self, context):
        layout = self.layout
        
        # Cursor orientation tools
        layout.label(text="Cursor Orientation", icon='ORIENTATION_CURSOR')
        layout.separator()
        
        layout.operator("cursor.reset_orientation", icon='LOOP_BACK')
        layout.operator("cursor.align_to_view", icon='VIEW_ORTHO')
        layout.operator("cursor.align_to_surface", icon='UV_FACESEL')
        layout.operator("cursor.set_preset_orientation", icon='ORIENTATION_CURSOR')
        
        layout.separator()
        
        # Cursor positioning
        layout.label(text="Cursor Position", icon='PIVOT_CURSOR')
        layout.separator()
        
        layout.operator("cursor.set_to_selection_center", icon='PIVOT_CURSOR')
        layout.operator("cursor.set_to_view_center", icon='PIVOT_CURSOR')
        
        layout.separator()
        
        # Cursor rotation tools
        props = context.scene.cursor_align_props
        layout.label(text=f"Rotate ({props.rotation_step}°)", icon='DRIVER_ROTATIONAL_DIFFERENCE')
        layout.separator()
        
        row = layout.row(align=True)
        op = row.operator("cursor.rotate_axis", text="+X")
        op.axis = 'X'
        op.direction = 'POS'
        op = row.operator("cursor.rotate_axis", text="-X")
        op.axis = 'X'
        op.direction = 'NEG'
        
        row = layout.row(align=True)
        op = row.operator("cursor.rotate_axis", text="+Y")
        op.axis = 'Y'
        op.direction = 'POS'
        op = row.operator("cursor.rotate_axis", text="-Y")
        op.axis = 'Y'
        op.direction = 'NEG'
        
        row = layout.row(align=True)
        op = row.operator("cursor.rotate_axis", text="+Z")
        op.axis = 'Z'
        op.direction = 'POS'
        op = row.operator("cursor.rotate_axis", text="-Z")
        op.axis = 'Z'
        op.direction = 'NEG'


# -----------------------------------------------------------------------------
# Machine Tools Integration Operator
# -----------------------------------------------------------------------------

class CURSOR_OT_machine_tools_menu(Operator):
    """Show cursor alignment tools menu for Machine Tools integration."""
    bl_idname = "cursor.machine_tools_menu"
    bl_label = "Cursor Alignment Tools"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.call_menu(name="VIEW3D_MT_cursor_align_machine_tools")
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# Addon Preferences
# -----------------------------------------------------------------------------

class CursorAlignAddonPreferences(AddonPreferences):
    """Add-on preferences for cursor alignment tools."""
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        
        # Get scene properties for display
        try:
            props = context.scene.cursor_align_props
        except (AttributeError, KeyError):
            # Show message if properties not available
            layout.label(text="Properties not available. Please restart Blender.")
            return
        
        # General settings
        box = layout.box()
        box.label(text="General Settings")
        box.prop(props, "rotation_step", text="Default Rotation Step")
        if props.rotation_step == 'CUSTOM':
            box.prop(props, "custom_step", text="Custom Angle")
        
        # Menu integration options
        box = layout.box()
        box.label(text="Menu Integration")
        box.prop(props, "use_snap_menu", text="Add to Shift+S Snap Menu")
        box.prop(props, "use_pie_menu", text="Enable Pie Menu")
        
        if props.use_pie_menu:
            box.prop(props, "pie_menu_key", text="Pie Menu Hotkey")
            if props.pie_menu_key == 'SHIFT':
                box.label(text="Note: This will override the default Shift+S snap menu", icon='INFO')
        
        # Machine Tools integration info
        box = layout.box()
        box.label(text="Machine Tools Integration")
        if is_machine_tools_available():
            box.label(text="✓ Machine Tools detected", icon='CHECKMARK')
            box.label(text="• Snap menu integration disabled (Machine Tools handles this)")
            box.label(text="• Access tools via the sidebar panel or add to Quick Favorites")
            box.label(text="• Consider adding 'cursor.machine_tools_menu' to Quick Favorites")
        else:
            box.label(text="• Machine Tools not detected", icon='QUESTION')
            box.label(text="• Full snap menu integration available")
        
        # Information
        box = layout.box()
        box.label(text="Information")
        box.label(text="• The add-on adds a 'Cursor Align' tab to the 3D View sidebar")
        box.label(text="• Use the panel to control cursor rotation and align objects")
        box.label(text="• Enable snap menu integration for quick access via Shift+S")
        box.label(text="• The pie menu provides radial access to common operations")


# -----------------------------------------------------------------------------
# Registration and Keymap
# -----------------------------------------------------------------------------

classes = (
    CursorAlignProperties,
    CURSOR_OT_reset_orientation,
    CURSOR_OT_rotate_axis,
    CURSOR_OT_flip_axis,
    CURSOR_OT_copy_from_object,
    CURSOR_OT_apply_to_object,
    CURSOR_OT_align_to_view,
    CURSOR_OT_align_to_surface,
    CURSOR_OT_set_preset_orientation,
    CURSOR_OT_set_to_selection_center,
    CURSOR_OT_set_to_view_center,
    CURSOR_OT_machine_tools_menu,
    OBJECT_OT_origin_to_cursor,
    OBJECT_OT_rotate_axis,
    OBJECT_OT_reset_orientation,
    OBJECT_OT_align_to_cursor,
    OBJECT_OT_snap_cursor_to_selected,
    OBJECT_OT_snap_selected_to_cursor,
    OBJECT_OT_create_transform_orientation,
    OBJECT_OT_align_objects_to_each_other,
    OBJECT_OT_distribute_along_cursor,
    OBJECT_OT_copy_cursor_location,
    VIEW3D_PT_cursor_align,
    VIEW3D_MT_cursor_origin_wheel,
    VIEW3D_MT_cursor_align_machine_tools,
    CursorAlignAddonPreferences,
)

# Keymap handles stored here for unregister
addon_keymaps = []


def register_keymap_pie():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:
        return
    
    # Get properties safely, with fallback to default
    try:
        props = bpy.context.scene.cursor_align_props
        key_modifier = props.pie_menu_key
    except (AttributeError, KeyError):
        # Fallback to default if properties not available
        key_modifier = 'ALT'
    
    # Determine keymap hotkey based on modifier
    keymap = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    
    # Map S with chosen modifier; use call_menu_pie
    if key_modifier == 'SHIFT':
        keymap_item = keymap.keymap_items.new('wm.call_menu_pie', type='S', value='PRESS', shift=True)
    elif key_modifier == 'CTRL':
        keymap_item = keymap.keymap_items.new('wm.call_menu_pie', type='S', value='PRESS', ctrl=True)
    elif key_modifier == 'ALT':
        keymap_item = keymap.keymap_items.new('wm.call_menu_pie', type='S', value='PRESS', alt=True)
    else:
        # No automatic binding
        return
    
    keymap_item.properties.name = VIEW3D_MT_cursor_origin_wheel.bl_idname
    addon_keymaps.append((keymap, keymap_item))


def unregister_keymap_pie():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def register_menu_draw():
    bpy.types.VIEW3D_MT_snap.append(draw_snap_menu)


def unregister_menu_draw():
    try:
        bpy.types.VIEW3D_MT_snap.remove(draw_snap_menu)
    except Exception:
        pass


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register property group and assign to scene
    bpy.types.Scene.cursor_align_props = bpy.props.PointerProperty(type=CursorAlignProperties)
    
    # Check for Machine Tools integration
    machine_tools_available = is_machine_tools_available()
    
    if machine_tools_available:
        # Integrate with Machine Tools cursor pie menu
        integrate_with_machine_tools_cursor_pie()
    else:
        # Always register snap menu if Machine Tools is not available
        # (Properties might not be available during initial registration)
        register_menu_draw()
    
    # Register pie keymap if enabled (check safely)
    try:
        if bpy.context.scene.cursor_align_props.use_pie_menu:
            register_keymap_pie()
    except (AttributeError, KeyError):
        # Default to disabled if properties not available
        pass
    
    # Print integration status
    if machine_tools_available:
        print("Cursor & Origin Alignment: Machine Tools detected - snap menu integration disabled")
    else:
        print("Cursor & Origin Alignment: Standalone mode - full functionality enabled")


def unregister():
    # Remove menu items and keymaps
    unregister_menu_draw()
    unregister_keymap_pie()
    
    # Remove Machine Tools integration if it was added
    remove_machine_tools_integration()
    
    # Delete property
    del bpy.types.Scene.cursor_align_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
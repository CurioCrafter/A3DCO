# Align3DCursorAndOrigin Add-on for Blender 4.5+

A comprehensive Blender add-on that provides advanced 3D cursor rotation control and object origin manipulation tools, with seamless integration into existing workflows.

## ✨ Features

### 🎯 3D Cursor Rotation Control
- **Reset Orientation** - Reset cursor rotation to world coordinates
- **Align to View** - Align cursor to current viewport orientation
- **Align to Surface** - Align cursor to selected surface normal
- **Set Preset Orientations** - Quick access to Front, Right, Top, Back, Left, Bottom views
- **Rotate by Increments** - Rotate cursor in 90° steps along any axis
- **Copy from Objects** - Copy rotation from selected objects to cursor

### 🔧 Object Origin Tools
- **Origin to Cursor** - Move object origins to 3D cursor location/rotation
- **Copy Cursor Location** - Move objects to cursor location
- **Align Objects to Cursor** - Align object rotations to cursor orientation
- **Create Transform Orientations** - Generate custom transform orientations from cursor
- **Distribute Along Cursor** - Distribute objects along cursor's forward axis

### 🎨 Advanced Features
- **Cursor to Selection Center** - Position cursor at center of selected objects
- **Cursor to View Center** - Position cursor at viewport center
- **Object Alignment Tools** - Align objects to each other using cursor as reference
- **Preset System** - Save and recall custom cursor orientations

## 🔄 Shift+S Integration

The add-on intelligently integrates with Blender's **Shift+S** snap menu system:

### 📦 **With MACHIN3tools Installed**
When MACHIN3tools is detected, the add-on seamlessly integrates with Machine Tools' cursor pie menu:

- **Access**: Press **Shift+S** to open Machine Tools' cursor pie
- **Location**: Cursor alignment tools appear **above** existing content, perfectly centered
- **Integration**: Follows Machine Tools' UI design patterns for consistent experience
- **Layout**: Compact 3-row layout with organized tool groups:
  - **Row 1**: Reset + to View
  - **Row 2**: Preset + Surface  
  - **Row 3**: Copy + Apply

### ⚡ **Without MACHIN3tools (Standard Blender)**
When MACHIN3tools is not installed, the add-on extends Blender's default snap menu:

- **Access**: Press **Shift+S** to open standard Blender snap menu
- **Location**: Cursor alignment tools appear as organized sections at the bottom
- **Sections**:
  - **Cursor & Origin Alignment** - Basic positioning tools
  - **Rotation & Transform** - Rotation and orientation controls
  - **Utilities** - Advanced features and custom tools

## 🎛️ Additional Access Methods

### 📋 N-Panel (Sidebar)
- **Location**: 3D View → N-Panel → "Cursor Align" tab
- **Features**: Full access to all tools with detailed controls
- **Settings**: Angle presets, pie menu toggle, snap menu preferences

### 🥧 Pie Menu (Optional)
- **Hotkey**: Configurable (default: disabled)
- **Content**: Quick access wheel with most-used tools
- **Toggle**: Enable/disable in add-on preferences

## 🛠️ Installation

1. Download the `cursor_align_addon.py` file
2. In Blender: **Edit** → **Preferences** → **Add-ons** → **Install**
3. Select the downloaded file and click **Install Add-on**
4. Enable "Align3DCursorAndOrigin" in the add-ons list
5. The tools will automatically integrate with your Shift+S workflow

## ⚙️ Settings & Preferences

### Add-on Preferences
- **Use Pie Menu** - Enable custom pie menu with configurable hotkey
- **Use Snap Menu Integration** - Toggle Shift+S integration (auto-managed)
- **Custom Angle Presets** - Define your own rotation increments

### N-Panel Properties
- **Rotation Angle** - Set custom rotation increment (default: 90°)
- **Preset Orientations** - Quick buttons for common view angles
- **Machine Tools Detection** - Shows integration status

## 🔗 Compatibility

- **Blender Version**: 4.5+ required
- **MACHIN3tools**: Automatic detection and integration
- **Other Add-ons**: Non-intrusive, works alongside existing tools
- **Safe Integration**: Preserves all original functionality when integrating

## 📖 Usage Examples

### Basic Cursor Alignment
1. Press **Shift+S**
2. Click **"Reset Orientation"** to align cursor to world
3. Click **"to View"** to align cursor to current viewport
4. Use **"Preset"** for quick standard orientations

### Object Origin Workflow  
1. Select objects you want to align
2. Position and orient 3D cursor as desired
3. Press **Shift+S** → **"Origin to Cursor"**
4. Objects' origins now match cursor position/rotation

### Advanced Surface Alignment
1. Select a face on your mesh
2. Press **Shift+S** → **"Surface"**  
3. Cursor aligns to the face normal
4. Use cursor as reference for placing new objects

## 🎯 Design Philosophy

This add-on follows the principle of **enhancing existing workflows** rather than replacing them:

- **Non-Intrusive**: Integrates seamlessly without disrupting established patterns
- **Context-Aware**: Automatically adapts to your installed add-ons
- **Workflow-Focused**: Tools appear exactly where and when you need them
- **Reversible**: Can be disabled without affecting other functionality

## 🤝 Integration Details

### MACHIN3tools Integration
The add-on detects MACHIN3tools and:
- Hooks into the existing `MACHIN3_MT_cursor_pie` menu
- Preserves original functionality completely
- Adds cursor alignment tools in a dedicated section above existing content
- Follows Machine Tools' established UI patterns and design language
- Automatically removes integration when disabled

### Fallback Behavior
When MACHIN3tools is not available:
- Extends Blender's default `VIEW3D_MT_snap` menu (Shift+S)
- Organizes tools into logical sections with clear labeling
- Maintains consistent functionality across different setups

## 📝 Notes

- All tools respect Blender's undo system
- Cursor transformations work in both Object and Edit modes where applicable
- Integration is dynamic - install/remove MACHIN3tools anytime
- No external dependencies beyond Blender 4.5+

---

**Made with ❤️ for the Blender community**

*Enhancing 3D cursor workflows through intelligent integration and thoughtful design.*

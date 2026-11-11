[app]
title = DesktopTodo
project_dir = .
input_file = main.py
exec_directory = dist
project_file =
icon = src/desktop_todo/assets/icon.ico

[python]
python_path =
packages = Nuitka==4.2.1

[qt]
qml_files =
excluded_qml_plugins =
modules = Core,Gui,Widgets,Network,Svg
plugins =

[android]
wheel_pyside =
wheel_shiboken =
plugins =

[nuitka]
macos.permissions =
mode = onefile
extra_args = --quiet --mingw64 --noinclude-qt-translations --windows-console-mode=disable --assume-yes-for-downloads --include-data-dir=src/desktop_todo/assets=desktop_todo/assets --product-name=DesktopTodo --file-description=DesktopTodo --file-version=0.1.0.0 --product-version=0.1.0.0

[buildozer]
mode = debug
recipe_dir =
jars_dir =
ndk_path =
sdk_path =
local_libs =
arch =

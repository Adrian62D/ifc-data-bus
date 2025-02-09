# Blender Client

To run this client you need to install Python [mqtt-client](../mqtt-client/README.md) for Blender : 

* Clone `ifc-data-bus` repo in your Blender addons installation path
* Install dependencies with Blender's Python binary
* Start Blender, Open the file editor, load `ifcbus.py`, run the script
* In the Object Panel, clic on the `connect` button in  `IfcBus`

## Linux

Clone source

```bash
cd blender/4.3/scripts/addons_core
git clone https://github.com/Adrian62D/ifc-data-bus
```

Install pip

```bash
cd blender/4.3/python/bin
./python3.11 -m pip install -U pip
```
Install Python client with pip

```bash
./python3.11 -m pip install -U ../../scripts/addons_core/ifc-data-bus
```





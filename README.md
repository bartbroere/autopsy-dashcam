# BlackVue dashcam geolocation (Autopsy Module)
Extract and parse the geolocation data from BlackVue dashcams

## Installing
Unzip a release of the project into the folder that opens if you click Tools > Python Plugins.
Restart Autopsy to allow it to find the newly added module.

## Using
During a regular "ingest" run in Autopsy, select the module "Geolocation BlackVue dashcam".
This tool will attempt to process any file ending in ``.mp4``.

## Building
The tool automatically builds on pushes to the repository.
Alternatively, follow the commands described in ``.github/workflows/compile.yml`` to build
a copy manually.

## Contributing
Please take a look at the list of issues if you would like to contribute.
This is not an exhaustive list. Any other features will be considered as well.

Although Autopsy Modules are written in Python 2 (Jython specifically), this tool bridges to
a Python 3 runtime by packing ``parse_mp4.py`` into a standalone executable using PyInstaller.

## Acknowledgements
The research into the file format has mostly been done by ``gandy92`` in the ``blackclue`` repository.
The NMEA records are parsed using ``pynmea2``

## License
This project is MIT Licensed

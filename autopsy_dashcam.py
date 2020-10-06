import inspect
import platform
import subprocess
import json

if platform.system() == 'Java':  # Jython runtime imports
    from java.util.logging import Level
    from org.sleuthkit.autopsy.coreutils import Logger
    from org.sleuthkit.autopsy.ingest import FileIngestModule
    from org.sleuthkit.datamodel import BlackboardArtifact
    from org.sleuthkit.datamodel import BlackboardAttribute
    from org.sleuthkit.datamodel import TskData
    from org.sleuthkit.autopsy.ingest import IngestMessage
    from org.sleuthkit.autopsy.ingest import IngestModule
    from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
    from org.sleuthkit.autopsy.ingest import ModuleDataEvent
    from org.sleuthkit.autopsy.ingest import IngestServices
    from org.sleuthkit.datamodel import ReadContentInputStream
    from org.sleuthkit.datamodel import TskData


    class GeolocationBlackvue(IngestModuleFactoryAdapter):
        moduleName = "Geolocation from BlackVue dashcam recordings"

        def getModuleDisplayName(self):
            return self.moduleName

        # TODO: Give it a description
        def getModuleDescription(self):
            return "Get geolocation data from Blackvue dashcam recordings"

        def getModuleVersionNumber(self):
            return "2020.10.6"

        # Return true if module wants to get called for each file
        def isFileIngestModuleFactory(self):
            return True

        # can return null if isFileIngestModuleFactory returns false
        def createFileIngestModule(self, ingestOptions):
            return SampleJythonFileIngestModule()


    class SampleJythonFileIngestModule(FileIngestModule):
        _logger = Logger.getLogger(GeolocationBlackvue.moduleName)

        def log(self, level, msg):
            self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

        def startUp(self, context):
            self.platform = ''
            pass

        def process(self, file):
            # Skip non-files
            if ((file.getType() == TskData.TSK_DB_FILES_TYPE_ENUM.UNALLOC_BLOCKS) or
                    (file.getType() == TskData.TSK_DB_FILES_TYPE_ENUM.UNUSED_BLOCKS) or
                    (not file.isFile())):
                return IngestModule.ProcessResult.OK

            if file.getName().lower().endswith(".mp4"):
                self.log(Level.INFO, "Found a mp4 file, possibly a BlackVue dashcam recording: " + file.getName())
                platform_suffix = '.exe' if hasattr(platform, 'win32_ver') else ''
                # call our "binary" and pipe our inputstream into it
                locations = json.loads(
                    subprocess.check_output('./bin/autopsy_dashcam' + platform_suffix,
                                            stdin=ReadContentInputStream(file))
                )

                for location in locations:
                    art = file.newArtifact(BlackboardArtifact.ARTIFACT_TYPE.TSK_GPS_TRACK)
                    # TODO fill in appropriate attributes for geolocations
                    art.addAttribute(BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_SET_NAME.getTypeID(),
                                                         GeolocationBlackvue.moduleName,
                                                         "Dashcam Location"))

                    # Fire an event to notify the UI and others that there is a new artifact
                    IngestServices.getInstance().fireModuleDataEvent(
                        ModuleDataEvent(GeolocationBlackvue.moduleName,
                                        BlackboardArtifact.ARTIFACT_TYPE.TSK_GPS_TRACK, None)
                    )

            return IngestModule.ProcessResult.OK

        def shutDown(self):
            message = IngestMessage.createMessage(
                IngestMessage.MessageType.DATA, GeolocationBlackvue.moduleName,
                self.platform)
            ingestServices = IngestServices.getInstance().postMessage(message)

# Python 3 code from here on
if __name__ == '__main__':
    from pymp4 import parser
    import re
    import pynmea2

    # TODO open from stdin
    with open('C:\\Users\TEMP\Downloads\\vid.mp4', 'rb') as f:
        while True:
            mp4 = parser.Box.parse_stream(f)
            if mp4.type == b'free':
                try:
                    data = dict(mp4.__getstate__())['data']
                    gps_data = data[data.find(b'gps [') + 4:data.find(b'\n\n\x00')]
                    gps_data = gps_data.split(b'\n\n')
                    gps_out = []
                    previous_unix_ms = 0
                    for line in gps_data:
                        line = line.decode('utf8')
                        unix_ms = re.findall(r'(?!\[)[0-9]*(?=\])', line)[0]
                        try:
                            parsed_nmea = pynmea2.parse(line.split(']')[-1])
                            if hasattr(parsed_nmea, 'latitude'):
                                if unix_ms != previous_unix_ms:
                                    lat = parsed_nmea.latitude
                                    lon = parsed_nmea.longitude
                                    gps_out.append([int(unix_ms), lat, lon])
                                    previous_unix_ms = unix_ms
                        except:
                            continue
                    print(json.dumps(gps_out))
                    quit(0)
                except:
                    continue

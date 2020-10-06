import inspect
import platform

if platform.system() == 'Java':  # Jython runtime imports
    from java.util.logging import Level
    from org.sleuthkit.autopsy.coreutils import Logger
    from org.sleuthkit.autopsy.ingest import FileIngestModule
    from org.sleuthkit.autopsy.ingest import IngestMessage
    from org.sleuthkit.autopsy.ingest import IngestModule
    from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
    from org.sleuthkit.autopsy.ingest import IngestServices
    from org.sleuthkit.datamodel import ReadContentInputStream
    from org.sleuthkit.datamodel import TskData


    class SampleJythonFileIngestModuleFactory(IngestModuleFactoryAdapter):
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
        _logger = Logger.getLogger(SampleJythonFileIngestModuleFactory.moduleName)

        def log(self, level, msg):
            self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

        def startUp(self, context):
            self.platform = ''
            pass

        def process(self, file):
            # Skip non-files
            if ((file.getType() == TskData.TSK_DB_FILES_TYPE_ENUM.UNALLOC_BLOCKS) or
                    (file.getType() == TskData.TSK_DB_FILES_TYPE_ENUM.UNUSED_BLOCKS) or
                    (file.isFile() == False)):
                return IngestModule.ProcessResult.OK

            if file.getName().lower().endswith(".mp4"):
                inputStream = ReadContentInputStream(file)
                self.log(Level.INFO, "Found a mp4 file, possibly a BlackVue dashcam recording: " + file.getName())
                if hasattr(platform, 'win32_ver'):
                    self.log(Level.INFO, 'On Windows')
                    # TODO call our "binary" and pipe our inputstream into it
                else:  # for now we hope we're on Linux, but anything's possible of course
                    self.log(Level.INFO, 'Not on Windows, assuming / hoping Linux amd64')

            return IngestModule.ProcessResult.OK

        def shutDown(self):
            message = IngestMessage.createMessage(
                IngestMessage.MessageType.DATA, SampleJythonFileIngestModuleFactory.moduleName,
                self.platform)
            ingestServices = IngestServices.getInstance().postMessage(message)


# Python 3 code from here on
if __name__ == '__main__':
    from pymp4 import parser
    import re
    import pynmea2
    import json

    with open('C:\\Users\TEMP\Downloads\\vid.mp4', 'rb') as f:
        while True:
            mp4 = parser.Box.parse_stream(f)
            if mp4.type == b'free':
                try:
                    data = dict(mp4.__getstate__())['data']
                    gps_data = data[data.find(b'gps ['):data.find(b'\n\n\x00')]
                    gps_data = gps_data.split(b'\n\n')
                    gps_out = []
                    for line in gps_data:
                        unix_ms = re.findall(r'(?!\[)[0-9]*(?=\])', line)[0]
                        try:
                            parsed_nmea = pynmea2.parse(line.split(']')[-1])
                            if hasattr(parsed_nmea, 'latitude'):
                                if unix_ms != previous_unix_ms:
                                    lat = parsed_nmea.latitude
                                    lon = parsed_nmea.longitude
                                    gps_out.append([unix_ms, lat, lon])
                                    previous_unix_ms = unix_ms
                        except:
                            continue
                    print(json.dumps(gps_out))
                except:
                    continue
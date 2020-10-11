import inspect
import json
import os
import platform
import subprocess
import tempfile
import traceback

import jarray
from java.util.logging import Level
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.ingest import FileIngestModule
from org.sleuthkit.autopsy.ingest import IngestMessage
from org.sleuthkit.autopsy.ingest import IngestModule
from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.autopsy.ingest import ModuleDataEvent
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
from org.sleuthkit.datamodel import TskData


class GeolocationBlackvue(IngestModuleFactoryAdapter):
    moduleName = "Geolocation BlackVue dashcam"

    def getModuleDisplayName(self):
        return self.moduleName

    # TODO: Give it a description
    def getModuleDescription(self):
        return "Get geolocation data from Blackvue dashcam recordings"

    def getModuleVersionNumber(self):
        return "2020.10.11"

    # Return true if module wants to get called for each file
    def isFileIngestModuleFactory(self):
        return True

    # can return null if isFileIngestModuleFactory returns false
    def createFileIngestModule(self, ingestOptions):
        return SampleJythonFileIngestModule()


class BlackVueFileIngest(FileIngestModule):
    _logger = Logger.getLogger(GeolocationBlackvue.moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    def startUp(self, context):
        pass

    def process(self, file):
        # Skip non-files
        if ((file.getType() == TskData.TSK_DB_FILES_TYPE_ENUM.UNALLOC_BLOCKS) or
                (file.getType() == TskData.TSK_DB_FILES_TYPE_ENUM.UNUSED_BLOCKS) or
                (not file.isFile())):
            return IngestModule.ProcessResult.OK

        def getBlackboardAtt(label, value):
            return BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.fromLabel(label).getTypeID(),
                                       GeolocationBlackvue.moduleName, value)

        if file.getName().lower().endswith(".mp4"):
            self.log(Level.INFO, "Found a mp4 file, possibly a BlackVue dashcam recording: " + file.getName())
            platform_suffix = '.exe' if hasattr(platform, 'win32_ver') else ''

            # get an input buffer
            filesize = file.getSize()
            buffer = jarray.zeros(filesize, 'b')
            file.read(buffer, 0, filesize)
            file.close()

            temporary = tempfile.NamedTemporaryFile()
            temporary.write(buffer)

            # call our "binary" and supply our temporary file
            # TODO pipe our file in instead of making a temporary copy
            output = subprocess.check_output(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    'dist',
                    'parse_mp4'
                ) + platform_suffix + ' ' + temporary.name
            )
            locations = json.loads(output)

            for unix, lat, lon in locations:
                art = file.newArtifact(BlackboardArtifact.ARTIFACT_TYPE.TSK_GPS_TRACKPOINT)
                lat = getBlackboardAtt("TSK_GEO_LATITUDE", lat)
                lon = getBlackboardAtt("TSK_GEO_LONGITUDE", lon)
                loc = getBlackboardAtt("TSK_DATETIME", unix)
                art.addAttributes([lat, lon, loc])

            IngestServices.getInstance().fireModuleDataEvent(
                ModuleDataEvent(GeolocationBlackvue.moduleName,
                                BlackboardArtifact.ARTIFACT_TYPE.TSK_GPS_TRACKPOINT, None)
            )

        return IngestModule.ProcessResult.OK

    def shutDown(self):
        message = IngestMessage.createMessage(
            IngestMessage.MessageType.DATA, GeolocationBlackvue.moduleName,
            "Done processing BlackVue mp4 files")
        ingestServices = IngestServices.getInstance().postMessage(message)

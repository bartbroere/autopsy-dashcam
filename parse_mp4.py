import json
import re
import sys

import construct
import pynmea2
from pymp4 import parser


if __name__ == '__main__':
    # TODO read from stdin
    with open(sys.argv[1], 'rb') as f:
        while True:
            try:
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
            except construct.core.ConstError:
                break

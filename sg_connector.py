from shotgun_api3 import Shotgun

sgURL = 'https://dev.shotgunstudio.com'
sgScriptName = 'api'
sgScriptKey = 'njcvtq6#yrrPavifadbhpedqc'


sg = Shotgun(sgURL, sgScriptName, sgScriptKey)
sg.config.no_ssl_validation = True
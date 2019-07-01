import os
import json 
import time 
import uuid 
import logging
import multiprocessing
from sg_connector import sg 


log = logging.getLogger()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(module)s.%(funcName)s.%(lineno)d: %(message)s", "%Y-%m-%d %H:%M:%S")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)

DIR = os.path.dirname(os.path.realpath(__file__))
API_USER_ID = 60
INTERVAL = 30


def queryEvents(event_id): 
    fields = ['meta', 'user', 'event_type']
    filters = [['id', 'greater_than', event_id], 
            ['user', 'is_not', {'type': 'ApiUser', 'id': API_USER_ID}]]

    return sg.find('EventLogEntry', filters, fields)

def assembleJsonFilepath():
    return os.path.join(DIR, 'event_id.json')

def queryLatestEventId():
    fields = []
    filters = [['user', 'is_not', {'type': 'ApiUser', 'id': API_USER_ID}]]

    sort = [{'field_name':'id','direction':'desc'}]
    result = sg.find_one('EventLogEntry', filters, fields, sort)

    if not isinstance(result, dict):
        raise Exception('failed to get the latest event')
    if not isinstance(result.get('id'), int):
        raise Exception('latest event has no id %s' % str(result))    
    return result.get('id')


def writeToJson(dictionary, filepath):
    _dict = dict()
    for key in dictionary:
        if key in ['assets']:
            _dict[key] = dictionary[key]
        else:
            _dict[key] = json.dumps(dictionary[key])

    with open(filepath, 'w') as _file:
        json.dump(_dict, _file)
    log.info('last event id has been saved as %s' % dictionary )


def saveLastEventId(event_id):
    writeToJson(dictionary={'LAST_EVENT_ID': int(event_id)}, 
                filepath=assembleJsonFilepath())
    log.info('event %s has been saved.' % event_id)

def readJson(filepath):
    with open(filepath) as file:  
        loaded = json.loads(file.read())          

    result = dict()
    for key in loaded:
        if isinstance(key, unicode):
            key = str(key)

        value = loaded[key]
        if isinstance(value, unicode):
            result[key] = eval(value)
        else:
            result[key] = value
    return result


def getLastEventId():
    try:
        return int(readJson(assembleJsonFilepath())['LAST_EVENT_ID'])
    except:
        event_id = queryLatestEventId()
        saveLastEventId(event_id = event_id)
        return event_id


def dispatch():
    try:
        last_id = getLastEventId()    
        events = queryEvents(event_id = last_id)
        log.info('total events since last event %s: %s' % (last_id, len(events)))
        for i, event in enumerate(events):
            saveLastEventId(event_id=event['id'])
    except Exception, e:
        log.warning(e)   


def startServer():
    while True:
        try:
            proc = multiprocessing.Process(target=dispatch, name=str(uuid.uuid4())) 
            proc.start()
            log.info('%s seconds till query. proc: %s' % (INTERVAL, proc.name))
            time.sleep(INTERVAL)
            
            if proc.is_alive():
                log.warning('...timeout is reached. main proc %s is being terminated' % proc.name)
                proc.terminate()
                time.sleep(0.1)
                
        except KeyboardInterrupt, e:
            try: proc.terminate()
            except: pass 
            log.error(e)


if __name__ == '__main__':
    startServer()


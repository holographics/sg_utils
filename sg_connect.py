import os
import sys
import multiprocessing, logging
logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.INFO)

from shotgun_api3 import Shotgun

sgURL = 'https://dev.shotgunstudio.com'
sgScriptName = 'api'
sgScriptKey = 'njcvtq6#yrrPavifadbhpedqc'


sg = Shotgun(sgURL, sgScriptName, sgScriptKey)
sg.config.no_ssl_validation = True

logger.info('sg connected: %s' % sg)

PLACE = 'C:/Users/Administrator/Downloads/Evermotion/download'


class Asset(dict):
    def __init__(self, **kwargs):
        super(Asset, self).__init__(**kwargs)
        self.item = None

    def getItem(self):
        if not self.item:
            self.item = models.File(code=self['code'], 
                                    gender=self['sg_gender'], 
                                    bitype=self['sg_bitype'], 
                                    category=self['sg_category'])

        return self.item if self.item else dict()


def collect_images(place = PLACE):
    result = list()
    
    for category in os.listdir(place):
        if category != 'architectural_elements':
            continue 
        category_dirname  = os.path.join(place, category)
        if not os.path.isdir(category_dirname):
            continue 

        for subcat in os.listdir(category_dirname):
            subcategory_dirname  = os.path.join(category_dirname, subcat)
            if not os.path.isdir(subcategory_dirname):
                continue 

            for folder_name in os.listdir(subcategory_dirname):
                folder_dirname = os.path.join(subcategory_dirname, folder_name)
                if not os.path.isdir(folder_dirname):
                    continue 

                for basename in os.listdir(folder_dirname):
                    filepath = os.path.join(folder_dirname, basename )
                    if not filepath.endswith('.jpg'):
                        continue 

                    result.append(filepath.replace('\\', '/'))

    return result

def upload_thumbnail(entity_type, entity_id, thumb_path):         
    counter=0  
    while True:
        counter+=1
        try:
            sg.upload_thumbnail(entity_type, entity_id, thumb_path)
            break 
        except Exception as e:
            logger.info(e)                
            if counter > 5:
                break


def create_asset(rel_path):
    dirname = os.path.dirname(rel_path)
    basename = os.path.basename(rel_path)
    file_uuid, ext = os.path.splitext(basename)

    data = dict(sg_filepath = rel_path,
                sg_uuid = file_uuid,
                project = {'type': 'Project', 'id': 89},
                sg_status_list = 'cmpt')

    result = sg.create('PublishedFile', data)

    upload_thumbnail(entity_type = 'PublishedFile', 
                        entity_id = result['id'], 
                        thumb_path = os.path.join(PLACE, rel_path))



    return result['id']


def create_assets(filepaths):
    for i, path in enumerate(filepaths):
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        file_uuid, ext = os.path.splitext(basename)
        rel_dirname = dirname[len(PLACE)+1:]
        rel_path = os.path.join(rel_dirname, basename).replace('\\','/')
        create_asset(rel_path = rel_path)
        logger.info('%s of %s : %s' % (i, len(filepaths), rel_path))







if __name__ == '__main__':
    filepaths = collect_images()
    logger.info('found files: %s' % len(filepaths))
    create_assets(filepaths)

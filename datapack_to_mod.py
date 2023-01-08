from os.path import isdir, join
import shutil
from sys import api_version, argv
import os
import zipfile
from tempfile import gettempdir

from common import safe_del, make_dirname, read_json, write_text

temp = os.path.join(gettempdir(), 'package_datapack_to_mod')

import unicodedata
import re

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '_', value).strip('_')



forge = """modLoader = "javafml"
loaderVersion = "[25,)"
license = "Unknow"
showAsResourcePack = true

[[mods]]
modId = "{id}_pdpm"
version = "1-mcmeta-{mcmeta}"
displayName = "{name}"
description = "{description}"
logoFile = "{id}_pack.png"
credits = "Generated by MC-utility-tools"
authors = "un-pogaz"
"""

forge_class = [
    b"\xca\xfe\xba\xbe\x00\x00\x004\x00\x14\x01\x00%net/pdpm/",
    b"/pdpmWrapper\x07\x00\x01\x01\x00\x10java/lang/Object\x07\x00\x03\x01\x00\x14pdpmWrapper.java\x01\x00#Lnet/minecraftforge/fml/common/Mod;\x01\x00\x05value\x01\x00\x0b",
    b"_pdpm\x01\x00\x06<init>\x01\x00\x03()V\x0c\x00\t\x00\n\n\x00\x04\x00\x0b\x01\x00\x04this\x01\x00'Lcom/pdpm/wrappera/pdpmWrapper;\x01\x00\x04Code\x01\x00\x0fLineNumberTable\x01\x00\x12LocalVariableTable\x01\x00\nSourceFile\x01\x00\x19RuntimeVisibleAnnotations\x00!\x00\x02\x00\x04\x00\x00\x00\x00\x00\x01\x00\x01\x00\t\x00\n\x00\x01\x00\x0f\x00\x00\x00/\x00\x01\x00\x01\x00\x00\x00\x05*\xb7\x00\x0c\xb1\x00\x00\x00\x02\x00\x10\x00\x00\x00\x06\x00\x01\x00\x00\x00\x06\x00\x11\x00\x00\x00\x0c\x00\x01\x00\x00\x00\x05\x00\r\x00\x0e\x00\x00\x00\x02\x00\x12\x00\x00\x00\x02\x00\x05\x00\x13\x00\x00\x00\x0b\x00\x01\x00\x06\x00\x01\x00\x07s\x00\x08",
]

fabric = """{{"schemaVersion":1,"id":"{id}_pdpm","version":"1-mcmeta-{mcmeta}","name":"{name}","description":"{description}","license":"Unknow","icon":"{id}_pack.png","environment":"*","depends":{{"fabric-resource-loader-v0":"*"}}}}"""

quilt = """{{"schema_version":1,"quilt_loader":{{"group": "net.pdpm","id":"{id}_pdpm","version":"1-mcmeta-{mcmeta}","metadata":{{"name":"{name}","description":"{description}","icon":"{id}_pack.png"}},"intermediate_mappings":"net.fabricmc:intermediary","depends":[{{"id":"quilt_resource_loader","versions":"*","unless":"fabric-resource-loader-v0"}}]}}}}"""

def package_datapack(path):
    safe_del(temp)
    safe_del(temp+'.zip')
    os.makedirs(temp, exist_ok=True)
    path = os.path.abspath(path)
    
    if zipfile.is_zipfile(path):
        print('Extracting Datapack...')
        with zipfile.ZipFile(path, mode='r') as zip:
            zip.extractall(temp)
        work = temp
        name = os.path.splitext(os.path.basename(path))[0]
    else:
        work = path
        name = os.path.basename(path)
    
    if work == temp:
        new_path = os.path.splitext(path)[0]+'.jar'
    else:
        new_path = os.path.abspath(path)+'.jar'
    
    if os.path.exists(new_path):
        print('Error: packaged Datapack already exist {}'.format(os.path.basename(new_path)))
        return None
    
    id = slugify(name)
    id = re.sub(r'^([0-9])',r'n\1', id)
    id = re.sub(r'^([^a-z])',r'a\1', id)
    
    if not os.path.isdir(work):
        print(f'Error: the target path is not a folder or a ZIP "{path}"')
        return None
    
    print('Writing metadata...')
    try:
        j = read_json(os.path.join(work, 'pack.mcmeta'))
        mcmeta = j['pack']['pack_format']
        description = j['pack'].get('description', '')
        if isinstance(description, list):
            for i in range(len(description)):
                if isinstance(description[i], dict):
                    description[i] = description[i].get('text', '')
            
            description = ''.join(description).replace('\r\n','\n')
        
    except:
        print(f'Error: invalide Datapack')
        return None
    
    map = {'id': id, 'mcmeta':mcmeta, 'name':name, 'description':description.replace('\n', '\\n').replace('"', '\\"')}
    
    shutil.make_archive(temp, 'zip', root_dir=work)
    with zipfile.ZipFile(temp+'.zip', mode='a') as zip:
        icon = os.path.join(work, 'pack.png')
        if os.path.exists(icon):
            zip.write(icon, f"{id}_pack.png")
        zip.writestr('META-INF/mods.toml', forge.format_map(map))
        zip.writestr('fabric.mod.json', fabric.format_map(map))
        zip.writestr('quilt.mod.json', quilt.format_map(map))
        fc = id.encode('utf-8').join(forge_class)
        zip.writestr(f'net/pdpm/{id}/pdpmWrapper.class', fc)
    
    shutil.move(temp+'.zip', new_path)
    
    safe_del(temp)
    safe_del(temp+'.zip')


if __name__ == "__main__":
    print('{|[ Package Datapack to mod ]|}')
    args = argv[1:]
    if args:
        for a in args:
            print('>> '+os.path.basename(a))
            package_datapack(a)
            print()
    
    else:
        while True:
            print('Enter a Datapack (folder or zip) to package:')
            print('(Enter empty value to quit)')
            a = input().strip().strip('"')
            if not a:
                exit()
            package_datapack(a)
            print()

# todo: разобраться с self.force_http
# todo: разобраться с make_valid_url

# TODO : сделать нумерацию если она идёт не по умолчанию

# more about download resource: https://docs.nextgis.ru/docs_ngweb_dev/doc/developer/misc.html

import argparse
import re
import os
import zipfile
import base64
import requests
from transliterate import translit

import xml.etree.ElementTree as ET

# from qgis.core import *

from urllib.parse import urlparse
from avral.operation import AvralOperation, OperationException
from avral.io.types import FileType, StringType

import qgis_proj_generator


def get_args():
    epilog = '''Sample: '''
    epilog +=  ''' '''
    p = argparse.ArgumentParser(description=" ", epilog=epilog)

    p.add_argument('webgis_addr', help='')
    p.add_argument('id_map', help='')
    p.add_argument('--login', help='')
    p.add_argument('--password', help='')

    args = p.parse_args()

    return args


def ngw_request(url, creds):

    if creds != None:
        headers = {
            'Accept': '*/*',
            'Authorization': 'Basic' + ' ' + base64.b64encode(creds.encode("utf-8")).decode("utf-8")
        }
    else:
        headers = {
            'Accept': '*/*',
        }

    response = requests.get(url, headers=headers)

    return response


def getting_webmap_resources(webgis_addr, creds, id_webmap):

    '''
    Получение ресурсов из веб-карты NGW
    more: https://docs.nextgis.ru/docs_ngweb_dev/doc/developer/resource.html
    '''

    layer_position = 0

    url = f"{webgis_addr}/api/resource/{id_webmap}"

    response = ngw_request(url, creds)

    if response.status_code == 200:
        data = response.json()
    else:
        raise OperationException("Error in webgis addr or login/password")

    if data['resource']['cls'] != 'webmap':
        raise OperationException("Resource ID is not ID og webmap")

    webmap_dict = {
        'name': data['resource']['display_name'],
        'creation_date': data['resource']['creation_date'],
        'extent_left': data['webmap']['extent_left'],
        'extent_right': data['webmap']['extent_right'],
        'extent_bottom': data['webmap']['extent_bottom'],
        'extent_top': data['webmap']['extent_top']
    }

    layer_list = []

    for idx, item in enumerate(data['webmap']['root_item']['children']):
        if item['item_type'] == 'layer':
            layer_info = {
                "item_type": item['item_type'],
                # "display_name": item['display_name'],
                "layer_enabled": '0' if item['layer_enabled'] == 'false' else '1',
                "layer_identifiable": '0' if item['layer_identifiable'] == 'false' else '1',
                "layer_transparency": '0' if item['layer_transparency'] == 'null' else item['layer_transparency'],
                "layer_style_id": item['layer_style_id'],
                "style_parent_id": item['style_parent_id'],
                "layer_min_scale_denom": item['layer_min_scale_denom'] or 100000,
                "layer_max_scale_denom": item['layer_max_scale_denom'] or 0,
                "layer_adapter": item['layer_adapter'],
                "draw_order_position": item['draw_order_position'] or (idx + 1),  # fixme: а порядок с нуля или одного?
                "geometry_type": '',
                "display_name": '',
                "srs": '',
                "file_format": '',
                "fields": {},
            }
            layer_list.append(layer_info)
        else:
            continue  # todo : а что ещё может быть?

    layer_list.reverse()

    # TODO : СДЕЛАТЬ ДЛЯ БЭЙЗМАПА

    return webmap_dict, layer_list



def download_resource(webgis_addr, creds, layer_list, folder_path):

    for item in layer_list:

        resource_id = item['style_parent_id']
        style_id = item['layer_style_id']

        # if item[]
        url_vector_download = f"{webgis_addr}/api/resource/{resource_id}/export?format=GPKG&srs=4326&zipped=False&fid=ngw_id&encoding=UTF-8"
        # url_raster_download = f"put your url here"
        url_qml_download = f"{webgis_addr}/api/resource/{style_id}/qml"

        url_layer_info = f"{webgis_addr}/api/resource/{resource_id}"
        url_qml_info = f"{webgis_addr}/api/resource/search/?id={style_id}"


        response_vector_download = ngw_request(url_vector_download, creds)
        # response_raster_download = ngw_request(url_raster_download, creds)

        if response_vector_download.status_code == 200:

            response_qml_download = ngw_request(url_qml_download, creds)

            vector_content = response_vector_download.content

            vector_info = ngw_request(url_layer_info, creds).json()
            qml_info = ngw_request(url_qml_info, creds).json()

            for qml in qml_info:
                if qml['resource']['cls'] == 'qgis_vector_style':
                    response_qml_download = ngw_request(url_qml_download, creds)
                    qml_content = response_qml_download.content
                    qml_filename = f"{vector_info['resource']['display_name']}_style_{qml_info[0]['resource']['display_name']}.qml"
                    qml_file_path = os.path.join(folder_path, qml_filename)
                    with open(qml_file_path, 'wb') as qml_file:
                        qml_file.write(qml_content)

            filename = f"{vector_info['resource']['display_name']}.gpkg"

            ru_display_name = vector_info['resource']['display_name']
            # display_name = translit(ru_display_name, 'ru', reversed=True)
            display_name = ru_display_name

            item['geometry_type'] = f"{vector_info['vector_layer']['geometry_type']}"
            item['display_name'] = display_name
            item['srs'] = f"{vector_info['vector_layer']['srs']['id']}"
            item['file_format'] = 'gpkg'

            vector_file_path = os.path.join(folder_path, filename)

            with open(vector_file_path, 'wb') as vector_file:
                vector_file.write(vector_content)  # подмать

        # elif response_raster_download.status_code == 200:
        #     continue  # todo: описать загрузку растровых данных
        else:
            continue  # заглушка


def __make_valid_url(url):
    # beautify url taken from
    # https://github.com/nextgis/ngw_external_api_python/blob/master/qgis/ngw_connection_edit_dialog.py#L167

    url = url.strip()

    # Always remove trailing slashes (this is only a base url which will not be
    # used standalone anywhere).
    while url.endswith('/'):
        url = url[:-1]

    # Replace common ending when user copy-pastes from browser URL.
    url = re.sub('/resource/[0-9]+', '', url)

    o = urlparse(url)
    hostname = o.hostname

    # Select https if protocol has not been defined by user.
    if hostname is None:
        hostname = 'http://' if self.force_http else 'https://'
        return hostname + url

    # Force https regardless of what user has selected, but only for cloud connections.
    if url.startswith('http://') and url.endswith('.nextgis.com') and not self.force_http:
        return url.replace('http://', 'https://')

    return url


args = get_args()
webgis_addr = args.webgis_addr
username = args.username
password = args.password
id_map = args.id_map  # todo : прописать парсинг в случае если подётся ссылка

self.force_http = False
if webgis_addr.startswith('http://'): self.force_http = True
webgis_addr = __make_valid_url(webgis_addr)

if None in (webgis_addr, username, password, mode):
    raise OperationException("Internal error: Wrong number of arguments")

zip_path = 'result.zip'

with zipfile.ZipFile(zip_path, 'w') as zip_file:
    pass

creds = f"{username}:{password}"

webmap_dict, layer_list = getting_webmap_resources(webgis_addr, creds, id_map)

folder_path = f'{id_map}_qgis_project'

if not os.path.isdir(folder_path):
    os.mkdir(folder_path)

download_resource(webgis_addr, creds, layer_list, folder_path)

qgis_proj_generator.create_qgis_project(webgis_addr, username, folder_path, webmap_dict, layer_list)


setOutput("result", )
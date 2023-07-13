# todo: разобраться с self.force_http
# todo: разобраться с make_valid_url

# more about download resource: https://docs.nextgis.ru/docs_ngweb_dev/doc/developer/misc.html

import pandas as pd
import argparse
import re
import os
import zipfile
import json
import base64
import requests

import xml.etree.ElementTree as ET

# from qgis.core import *

from urllib.parse import urlparse
from avral.operation import AvralOperation, OperationException
from avral.io.types import FileType, StringType


def get_args():
    epilog = '''Sample: '''
    epilog +=  ''' '''
    p = argparse.ArgumentParser(description=" ", epilog=epilog)

    p.add_argument('webgis_addr', help='')
    p.add_argument('--login', help='')
    p.add_argument('--password', help='')
    p.add_argument('--id_map', help='')

    args = p.parse_args()

    return args


def ngw_request(url, creds):

    headers = {
        'Accept': '*/*',
        'Authorization': 'Basic' + ' ' + base64.b64encode(creds.encode("utf-8")).decode("utf-8")
    }

    response = requests.get(url, headers=headers)

    return response


# подсчёт количества ресурсов в Web GIS
# def resource_counter(webgis_addr, creds):
#
#     vector_id_list = []
#     raster_id_list = []
#     qgsstyle_id_list = []
#
#     url = f"{webgis_addr}/api/resource/search/"
#
#     response = ngw_request(url, creds)
#
#     if response.status_code == 200:
#         dataframe = response.json()
#     else:
#         raise OperationException("Error in webgis addr or login/password")
#
#     # for item in dataframe:
#     #     if 'resource' in item:
#     #         count += 1
#
#     for item in dataframe:
#
#         if 'resource' in item:
#
#             resource_cls = item['resource']['cls']
#             id_value = item['resource']['id']
#
#             if resource_cls == 'vector_layer':
#                 vector_id_list.append(id_value)
#             elif resource_cls == 'raster_layer':
#                 raster_id_list.append(id_value)
#             elif resource_cls == 'qgis_vector_style':
#                 parent_id = item['resource']['parent']['id']
#                 qgsstyle_id_list.append([id_value][parent_id])
#
#     return vector_id_list, raster_id_list, qgsstyle_id_list


def getting_webmap_resources(webgis_addr, creds, id_webmap):

    '''
    Получение ресурсов из веб-карты NGW
    '''

    # more: https://docs.nextgis.ru/docs_ngweb_dev/doc/developer/resource.html

    layer_position = 0

    webmap_dict = {}
    layer_list = []

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

    for item in data:

        layer_position += 1

        if item['webmap']['children']['item_type'] == 'layer':

            layer_info = {}

            if item['webmap']['children']['draw_order_position'] != 0:
                draw_position = item['webmap']['children']['draw_order_position']
            else:
                draw_position = layer_position + 1
            layer_info['draw_position'] = draw_position
            layer_info['id'] = item['webmap']['children']['style_parent_id'] # fixme : работает?
            layer_info['style_id'] = item['webmap']['children']['layer_style_id']
            layer_info['display_name'] = item['webmap']['children']['display_name'] # fixme : разобраться с именем стиля
            layer_info['transparency'] = item['webmap']['children']['layer_transparency']
            layer_info['min_scale_denom']  = item['webmap']['children']['layer_min_scale_denom']
            layer_info['max_scale_denom'] = item['webmap']['children']['layer_max_scale_denom']
            layer_info['layer_adapter'] = item['webmap']['children']['layer_adapter']

            layer_list.append(layer_info)

        layer_list.reverse()

    return webmap_dict, layer_list




# загрузка ресурсов
# def download_vector_resource(webgis_addr, creds, vector_list, zip_path): # todo: переделать под списки
#
#     # vector_quantity = len(vector_list)
#
#     for item in vector_list:
#
#         resource_id = vector_list[item]
#
#         url = f"{webgis_addr}/api/resource/{resource_id}/export?format=GPKG&srs=4326&zipped=False&fid=ngw_id&encoding=UTF-8"
#
#         response = ngw_request(url, creds)
#
#         if response.status_code != 200:
#             # todo : придумать ошибку
#
#         gpkg_content = response.content
#         parsed_url = urlparse(url)
#         filename = os.path.basename(parsed_url.path)
#
#         with zipfile.ZipFile(zip_path, 'a') as zip_file:
#             zip_file.writestr(filename, gpkg_content)
#
#
# def download_qgis_styles(webgis_addr, creds, qgs_list, zip_path):
#
#     for item in qgs_list:
#
#         resource_id = qgs_list[item][0]
#
#         url = f"{webgis_addr}/api/resource/{resource_id}/qml"
#
#         response = ngw_request(url, creds)
#
#         if response.status_code != 200:
#             # todo : придумать ошибку
#
#         qml_content = response.content
#         parsed_url = urlparse(url)
#         filename = os.path.basename(parsed_url.path)
#
#         with zipfile.ZipFile(zip_path, 'a') as zip_file:
#             zip_file.writestr(filename, qml_content)
#
#         # TODO : объединить с векторными слоями
#
#
# def download_tms(webgis_addr, creds, raster_list, zip_path):
#
#     for item in raster_list:


def download_resource(webgis_addr, creds, layer_list, folder_path):

    for item in layer_list:

        resource_id = item['id']
        style_id = item['style_id']

        url_vector_download = f"{webgis_addr}/api/resource/{resource_id}/export?format=GPKG&srs=4326&zipped=False&fid=ngw_id&encoding=UTF-8"
        url_raster_download = f"put your {url} here"
        url_qml_download = f"{webgis_addr}/api/resource/{style_id}/qml"

        url_layer_info = f"{webgis_addr}/api/resource/search/?id={resource_id}"
        url_qml_info = f"{webgis_addr}/api/resource/search/?id={style_id}"


        response_vector_download = ngw_request(url_vector_download, creds)
        response_raster_download = ngw_request(url_vector_download, creds)

        if response_vector_download.status_code == 200:

            response_qml_download = ngw_request(url_qml_download, creds)

            vector_content = response_vector_download.content
            qml_content = response_qml_download.content

            vector_info = ngw_request(url_layer_info, creds).json()
            qml_info = ngw_request(url_qml_info, creds).json()

            filename = f"{vector_info['resource']['display_name']}"
            qml_filename = f"{vector_info['resource']['display_name']}_style_{qml_info['resource']['display_name']}"

            vector_file_path = os.path.join(folder_path, filename)
            qml_file_path = os.path.join(folder_path, qml_filename)

            with open(vector_file_path, 'w') as vector_file, open(qml_file_path, 'w') as qml_file:
                vector_file.write(vector_content)
                qml_file.write(qml_content)

        elif response_raster_download.status_code == 200:
            continue  # todo: описать загрузку растровых данных
        else:
            continue

def create_qgis_project(webgis_addr, login, folder_path, style_dict):

    # put your code here




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
id_map = args.id_map # todo : прописать парсинг в случае если подётся ссылка

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

folder_path = f'{webgis_addr}_qgis_project'

if not os.path.isdir(folder_path):
    os.mkdir(folder_path)

# download_vector_resource(webgis_addr, creds, vector_id_list, zip_file)
# download_qgis_styles(webgis_addr, creds, qgsstyle_id_list, zip_file)
# download_tms(webgis_addr, creds, raster_id_list, zip_file)

# download_resource(webgis_addr, creds, vector_id_list, folder_path, 'vector')
# download_resource(webgis_addr, creds, qgsstyle_id_list, folder_path, 'qgis_style')
# download_resource(webgis_addr, creds, raster_id_list, folder_path, 'raster')

# тут написатт про загрузку ресурсов

qgsstyle_id_dict = dict(qgsstyle_id_list)

# qgis_element = ET.Element('qgis')
# qgis_element.set('version', '3.0')
# title_element = ET.SubElement(qgis_element, 'title')
# title_element.text = f'{webgis_addr}'
#
# canvas_element = ET.SubElement(qgis_element, 'layer-tree-canvas')




setOutput("result", ) # todo: допилить
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
    p.add_argument('--mode', help='')

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
def resource_counter(webgis_addr, creds):

    vector_id_list = []
    raster_id_list = []
    qgsstyle_id_list = []

    url = f"{webgis_addr}/api/resource/search /"

    response = ngw_request(url, creds)

    if response.status_code == 200:
        dataframe = response.json()
    else:
        raise OperationException("Error in webgis addr or login/password")

    # for item in dataframe:
    #     if 'resource' in item:
    #         count += 1

    for item in dataframe:

        if 'resource' in item:

            resource_cls = item['resource']['cls']
            id_value = item['resource']['id']

            if resource_cls == 'vector_layer':
                vector_id_list.append(id_value)
            elif resource_cls == 'raster_layer':
                raster_id_list.append(id_value)
            elif resource_cls == 'qgis_vector_style':
                parent_id = item['resource']['parent']['id']
                qgsstyle_id_list.append([id_value][parent_id])

    return vector_id_list, raster_id_list, qgsstyle_id_list


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
# def download_tms(webgis_addr, creds, raster_list, zip_path):  # todo: допилить
#
#     for item in raster_list:


def download_resource(webgis_addr, creds, resource_list, folder_path, resource_type):

    for item in resource_list:

        if resource_type == 'vector':
            resource_id = resource_list[item]
            url = f"{webgis_addr}/api/resource/{resource_id}/export?format=GPKG&srs=4326&zipped=False&fid=ngw_id&encoding=UTF-8"
        elif resource_type == 'qgis_style':
            resource_id = resource_list[item][0]
            url = f"{webgis_addr}/api/resource/{resource_id}/qml"
        elif resource_type == 'raster':
            resource_id = resource_list[item]
            url = f"{webgis_addr}/api/resource/{resource_id}/qml"
        else:
            raise ValueError("Invalid format type")

        response = ngw_request(url, creds)

        if response.status_code != 200:
            raise OperationException("Error in webgis addr or login/password")

        content = response.content

        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        file_path = os.path.join(folder_path, filename)

        with open(file_path, 'w') as file:
            file.write(content)

        # with zipfile.ZipFile(zip_path, 'a') as zip_file:
        #     zip_file.writestr(filename, content)

def create_qgis_project(webgis_addr, folder_path, style_dict):

    qgis_project = ET.Element('qgis')
    qgis_project.set('version', '3.16.16-Hannover')

    title_element = ET.SubElement(qgis_project, 'title')
    title_element.text = f'{webgis_addr}'

    crc_element = ET.SubElement(qgis_project, )

    vector_layers = ET.SubElement(qgis_project, 'vector_layers')
    for filename in os.listdir(folder_path):
        if filename.endswith('.gpkg'):
            file_id = int(filename.split('_')[0])




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
mode = args.mode

self.force_http = False
if webgis_addr.startswith('http://'): self.force_http = True
webgis_addr = __make_valid_url(webgis_addr)

if None in (webgis_addr, username, password, mode):
    raise OperationException("Internal error: Wrong number of arguments")

zip_path = 'result.zip'

with zipfile.ZipFile(zip_path, 'w') as zip_file:
    pass

creds = f"{username}:{password}"

vector_id_list, raster_id_list, qgsstyle_id_list = resource_counter(webgis_addr, creds)

folder_path = f'{webgis_addr}_qgis_project'

if not os.path.isdir(folder_path):
    os.mkdir(folder_path)

# download_vector_resource(webgis_addr, creds, vector_id_list, zip_file)
# download_qgis_styles(webgis_addr, creds, qgsstyle_id_list, zip_file)
# download_tms(webgis_addr, creds, raster_id_list, zip_file)

download_resource(webgis_addr, creds, vector_id_list, folder_path, 'vector')
download_resource(webgis_addr, creds, qgsstyle_id_list, folder_path, 'qgis_style')
download_resource(webgis_addr, creds, raster_id_list, folder_path, 'raster')

qgsstyle_id_dict = dict(qgsstyle_id_list)

# qgis_element = ET.Element('qgis')
# qgis_element.set('version', '3.0')
# title_element = ET.SubElement(qgis_element, 'title')
# title_element.text = f'{webgis_addr}'
#
# canvas_element = ET.SubElement(qgis_element, 'layer-tree-canvas')




setOutput("result", ) # todo: допилить
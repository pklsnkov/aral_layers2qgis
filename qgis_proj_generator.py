import xml.etree.ElementTree as ET

webgis_addr = 'test'
login = 'chel'
folder_path = "C:\\Users\\AntanWind\\PycharmProjects\\aral_layers2qgis\\test_folder"
webmap_dict = {
    'name': 'My Web Map',
    'creation_date': '2023-07-20',
    "extent_left": '-180',
    "extent_right": '180',
    "extent_bottom": '-90',
    "extent_top": '90',
}

layer_list = [
    {
        "item_type": "layer",
        "display_name": "Terrain",
        "layer_enabled": True,
        "layer_identifiable": False,
        "layer_transparency": None,
        "layer_style_id": 10,
        "style_parent_id": 5,
        "layer_min_scale_denom": 1000,
        "layer_max_scale_denom": 5000,
        "layer_adapter": "terrain_data",
        "draw_order_position": 1,
        "legend_symbols": ["Mountains", "Hills", "Plains"],
        "payload": None,
        'geometry_type': 'MULTIPOLYGON',
        'layername': '2',
        file
    },
    {
        "item_type": "layer",
        "display_name": "Cities",
        "layer_enabled": True,
        "layer_identifiable": True,
        "layer_transparency": 0.5,
        "layer_style_id": 8,
        "style_parent_id": 5,
        "layer_min_scale_denom": 5000,
        "layer_max_scale_denom": 20000,
        "layer_adapter": "point",
        "draw_order_position": 2,
        "legend_symbols": ["City Center", "Suburbs"],
        "payload": None
    },
]

def create_qgis_project(webgis_addr, login, folder_path, webmap_dict, layer_list: list):

    qgis_tree = ET.parse('base_project.qgs')
    root = qgis_tree.getroot()

    root_dict = {
        'version': '3.16.16-Hannover',
        'saveUser': str(login.split('@')[0]),
        'saveUserFull': str(login.split('@')[0]),
        'projectname': f"QGIS project from {webmap_dict['name']}"
    }
    for key, value in root_dict.items():
        root.set(key, value)

    root.find('.//title').text = f'QGIS project from {webgis_addr}'

    layer_tree_group = root.find('layer-tree-group')

    vector_list = []
    raster_list = []
    style_list = []
    for layer in layer_list:
        if layer['file_format'] == 'gpkg':
            vector_list.append(layer)
        elif layer['file_format'] == 'jpeg':
            raster_list.append(layer)

    for vector_layer in vector_list:  # todo : сделать для растров
        layer_element = ET.SubElement(layer_tree_group, 'layer-tree-layer')
        layer_element.set('legend_split_behavior', "0")
        layer_element.set('name', f"{vector_layer['display_name']}")
        layer_element.set('patch_size', "0,0")
        layer_element.set('checked', "Qt::Checked")
        layer_element.set('id', f"{vector_layer['display_name']}_{vector_layer['style_parent_id']}")
        layer_element.set('expanded', "1")
        layer_element.set('providerKey', "ogr")
        layer_element.set('source', f"./{folder_path}/{vector_layer['display_name']}.gpkg|"
                                    f"layername={vector_layer['display_name']}|"
                                    f"geometrytype={vector_layer['geometry_type']}")
        custom_properties = ET.SubElement(layer_element, "customproperties")
        option_elem = ET.SubElement(custom_properties, 'Option')

    custom_order = layer_tree_group.find('custom-order')  # todo : тут подумать в случае особого порядка
    for vector_layer in vector_list:
        ET.SubElement(custom_order, 'item').text = f"{vector_layer['display_name']}_{vector_layer['style_parent_id']}"


    snapping_settings = root.find('snapping-settings')
    individual_layer_settings = snapping_settings.find('individual-layer-settings')
    for vector_layer in vector_list:
        layer_setting = ET.SubElement(individual_layer_settings, 'layer-setting')
        layer_setting_dict = {
            'enabled': f"{vector_layer['layer_enabled']}",
            'tolerance': '12',
            'units': '1',
            'id': f"{vector_layer['display_name']}_{vector_layer['style_parent_id']}",
            'maxScale': f"{vector_layer['layer_max_scale_denom']}",
            'minScale': f"{vector_layer['layer_max_scale_denom']}",
            'type': '1',
        }
        for key, value in layer_setting_dict.items():
            layer_setting.set(key, value)


    legend = root.find('legend')
    for vector_layer in vector_list:
        legendlayer = ET.SubElement(legend, 'legendlayer')

        legendlayer_dict = {
            'open': 'true',
            'name': f"{vector_layer['display_name']}",
            'checked': "Qt::Checked",
            'showFeatureCount': "0",
            'drawingOrder': "-1",
        }
        for key, value in legendlayer_dict.items():
            legendlayer.set(key, value)

        filegroup = ET.SubElement(legendlayer, 'filegroup')
        filegroup_dict = {
            'hidden': 'false',
            'open': 'true'
        }
        for key, value in filegroup_dict.items():
            filegroup.set(key, value)

        legendlayerfile = ET.SubElement(filegroup, 'legendlayerfile')
        legendlayerfile_dict = {
            'isInOverview': "0",
            'layerid': f"{vector_layer['display_name']}_{vector_layer['style_parent_id']}",
            'visible': "1",
        }
        for key, value in legendlayerfile_dict.items():
            legendlayerfile.set(key, value)


    # todo : main-annotation-layer


    # todo : projectlayers


    layerorder = root.find('layerorder')
    for vector_layer in vector_list:
        layer = ET.SubElement(layerorder, 'layer')
        layer.set('id', f"{vector_layer['display_name']}_{vector_layer['style_parent_id']}")


    projectMetadata = root.find('projectMetadata')
    projectMetadata.find('title').text = f'QGIS project from {webgis_addr}'
    projectMetadata.find('author').text = ''
    projectMetadata.find('creation').text = ''

    qgis_tree.write(f'QGIS project from {webgis_addr}.qgs')

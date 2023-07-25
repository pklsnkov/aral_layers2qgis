import xml.etree.ElementTree as ET
import os


def create_qgis_project(webgis_addr, login, folder_path, webmap_dict: dict, layer_list: list):

    # заполнение основной информации о файле qgs
    qgis_tree = ET.parse('default_files\\base_project.qgs')
    root = qgis_tree.getroot()
    root_dict = {
        'saveDateTime':'',
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

    for file in os.listdir(folder_path):
        if file.endswith('qml'):
            style_list.append(file)

    for vector_layer in vector_list:  # todo : сделать для растров
        layer_element = ET.SubElement(layer_tree_group, 'layer-tree-layer')
        layer_element.set('legend_split_behavior', "0")
        layer_element.set('name', f"{vector_layer['display_name']}")
        layer_element.set('patch_size', "0,0")
        layer_element.set('checked', "Qt::Checked")
        layer_element.set('id', f"{vector_layer['display_name']}_{vector_layer['style_parent_id']}")
        layer_element.set('expanded', "1")
        layer_element.set('providerKey', "ogr")
        layer_element.set('source', f"./{vector_layer['display_name']}.gpkg|"
                                    f"layername={vector_layer['display_name']}|"
                                    f"geometrytype={vector_layer['geometry_type']}")
        # layer_element.set('source', f"{vector_layer['display_name']}.gpkg")
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


    # создание и заполнение элемента projectlayers
    projectlayers = root.find('projectlayers')
    for vector_layer in vector_list:
        maplayer = ET.SubElement(projectlayers, 'maplayer')
        maplayer_dict = {
            'simplifyLocal': '1',
            'simplifyMaxScale': '1',
            'maxScale': f"{vector_layer['layer_max_scale_denom']}",
            'type': 'vector',
            'legendPlaceholderImage': '',
            'minScale': f"{vector_layer['layer_min_scale_denom']}",
            'autoRefreshTime': '0',
            'styleCategories': 'AllStyleCategories',
            'refreshOnNotifyEnabled': '0',
            'autoRefreshEnabled': '0',
            'simplifyDrawingHints': '0' if vector_layer['geometry_type'] == 'POINT' else '1',
            'geometry': f"{vector_layer['geometry_type']}".casefold().capitalize(),
            'readOnly': '0',
            'symbologyReferenceScale': '-1',
            'labelsEnabled': '1',
            'hasScaleBasedVisibilityFlag': '1',
            'refreshOnNotifyMessage': '',
            'simplifyAlgorithm': '1',
        }
        for key, value in maplayer_dict.items():
            maplayer.set(key, value)

        extent = ET.SubElement(maplayer, 'extent')
        ET.SubElement(extent, 'xmin').text = ''
        ET.SubElement(extent, 'ymin').text = ''
        ET.SubElement(extent, 'xmax').text = ''
        ET.SubElement(extent, 'ymax').text = ''

        ET.SubElement(maplayer, 'id').text = f"{vector_layer['display_name']}_{vector_layer['style_parent_id']}"

        ET.SubElement(maplayer, 'datasource').text = f"./{vector_layer['display_name']}.gpkg"

        ET.SubElement(maplayer, 'layername').text = f"{vector_layer['display_name']}"

        srs = ET.SubElement(maplayer, 'srs')
        spatialrefsys_elem = ET.SubElement(srs, 'spatialrefsys')
        ET.SubElement(spatialrefsys_elem, 'wkt').text = "GEOGCRS['WGS 84'," \
                                                        "DATUM['World Geodetic System 1984'," \
                                                        "ELLIPSOID['WGS 84',6378137,298.257223563," \
                                                        "LENGTHUNIT['metre',1]]]," \
                                                        "PRIMEM['Greenwich',0," \
                                                        "ANGLEUNIT['degree',0.0174532925199433]]," \
                                                        "CS[ellipsoidal,2]," \
                                                        "AXIS['geodetic latitude (Lat)',north,ORDER[1]," \
                                                        "ANGLEUNIT['degree',0.0174532925199433]]," \
                                                        "AXIS['geodetic longitude (Lon)',east,ORDER[2]," \
                                                        "ANGLEUNIT['degree',0.0174532925199433]]," \
                                                        "USAGE[SCOPE['unknown']," \
                                                        "AREA['World']," \
                                                        "BBOX[-90,-180,90,180]]," \
                                                        "ID['EPSG',4326]]"
        ET.SubElement(spatialrefsys_elem, 'proj4').text = "+proj=longlat +datum=WGS84 +no_defs"
        ET.SubElement(spatialrefsys_elem, 'srsid').text = '3452'
        ET.SubElement(spatialrefsys_elem, 'srid').text = '4326'
        ET.SubElement(spatialrefsys_elem, 'authid').text = 'EPSG:4326'
        ET.SubElement(spatialrefsys_elem, 'projectionacronym').text = 'longlat'
        ET.SubElement(spatialrefsys_elem, 'ellipsoidacronym').text = 'EPSG:7030'
        ET.SubElement(spatialrefsys_elem, 'geographicflag').text = 'true'

        provider = ET.SubElement(maplayer, 'provider')
        provider.set('encoding', 'utf-8')
        provider.text = 'ogr'
        ET.SubElement(maplayer, 'vectorjoins')
        ET.SubElement(maplayer, 'layerDependencies')
        ET.SubElement(maplayer, 'dataDependencies')
        ET.SubElement(maplayer, 'expressionfields')

        map_layer_style_manager = ET.SubElement(maplayer, 'map-layer-style-manager')
        for style in style_list:
            if vector_layer['display_name'] in style:
                map_layer_style_manager.set('current', f"{style.split('_style_')[0]}")
                ET.SubElement(map_layer_style_manager, 'map_layer_style').set('name', f"{style.split('_style_')[0]}")
            else:
                map_layer_style_manager.set('current', 'по умолчанию')
                ET.SubElement(map_layer_style_manager, 'map_layer_style').set('name', 'по умолчанию')

        ET.SubElement(maplayer, 'auxiliaryLayer')

        flags = ET.SubElement(maplayer, 'flags')
        ET.SubElement(flags, 'Identifiable').text = '1'
        ET.SubElement(flags, 'Removable').text = '1'
        ET.SubElement(flags, 'Searchable').text = '1'

        temporal = ET.SubElement(maplayer, 'temporal')
        temporal_dict = {
            'fixedDuration': '0',
            'accumulate': '0',
            'endExpression': '',
            'mode': '0',
            'enabled': '0',
            'durationField': '',
            'endField': '',
            'startField': '',
            'durationUnit': 'min',
        }
        for key, value in temporal_dict.items():
            temporal.set(key, value)

        fixedRange = ET.SubElement(temporal, 'fixedRange')
        ET.SubElement(fixedRange, 'start')
        ET.SubElement(fixedRange, 'finish')

        # renderer_v2 = ET.SubElement(maplayer, 'renderer-v2')
        # renderer_v2_dict = {
        #     'forceraster': '0',
        #     'symbollevels': '0',
        #     'enableorderby': '0',
        #     'type': 'singleSymbol',
        # }
        # for key, value in renderer_v2_dict.items():
        #     renderer_v2.set(key, value)

        try:
            for style in style_list:
                if vector_layer['display_name'] == style.split('_style_')[0]:
                    qml_path = os.path.join(folder_path, f'{style}')
                    qml_tree = ET.parse(qml_path)
                    qml_root = qml_tree.getroot()
                    renderer_v2 = qml_root.find('renderer-v2')
                    maplayer.append(renderer_v2)
                    # customproperties = qml_root.find('customproperties')
                    # maplayer.append(customproperties)
                    # labelattributes = qml_root.find('labelattributes')
                    # maplayer.append(labelattributes)

                    # todo : информация о подписях не копируется так просто
                    # todo : файл со стилем не отображается в qgis'е, без стиля всё работает




        except:
            default_style = 'default.qml'
            qml_path = os.path.join('default_files', default_style)
            qml_tree = ET.parse(qml_path)
            qml_root = qml_tree.getroot()
            renderer_v2 = qml_root.find('renderer-v2')
            maplayer.append(renderer_v2)


        ET.SubElement(maplayer, 'blendMode').text = '0'
        ET.SubElement(maplayer, 'featureBlendMode').text = '0'
        ET.SubElement(maplayer, 'layerOpacity').text = '1'
        ET.SubElement(maplayer, 'SingleCategoryDiagramRenderer').text = '0'


    layerorder = root.find('layerorder')
    for vector_layer in vector_list:
        layer = ET.SubElement(layerorder, 'layer')
        layer.set('id', f"{vector_layer['display_name']}_{vector_layer['style_parent_id']}")


    projectMetadata = root.find('projectMetadata')
    projectMetadata.find('title').text = f'QGIS project from {webgis_addr}'
    projectMetadata.find('author').text = ''
    projectMetadata.find('creation').text = ''

    ET.indent(qgis_tree, space='  ', level=0)

    return qgis_tree.write(f'{folder_path}\\QGIS project.qgs', encoding='UTF-8')

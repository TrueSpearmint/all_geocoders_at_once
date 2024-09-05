from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using Yandex service
def geocode_yandex(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()

    query = QUrlQuery()
    query.addQueryItem('geocode', str(value))
    query.addQueryItem('apikey', user_api_key)
    query.addQueryItem('format', 'json')
    query.addQueryItem('results', '1') 

    url = QUrl('https://geocode-maps.yandex.ru/1.x')
    url.setQuery(query)

    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.UserAgentHeader, 'QGIS Plugin "All Geocoders At Once"')

    nam = QgsNetworkAccessManager()
    response = nam.blockingGet(request)

    if response:
        status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            response_json = json.loads(bytes(response.content()))
            geo_object_collection = response_json['response'].get('GeoObjectCollection', {})
            feature_members = geo_object_collection.get('featureMember', [])
            if len(feature_members) > 0:
                first_feature = feature_members[0].get('GeoObject', {})
                point = first_feature.get('Point', {})
                coordinates_str = point.get('pos', '')
                if coordinates_str:
                    coordinates = list(map(float, coordinates_str.split()))
                    if len(coordinates) == 2:
                        lon = coordinates[0]
                        lat = coordinates[1]
                        address_geocoded = first_feature.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('text', 'No address')

                        point_out = QgsPointXY(lon, lat)
                        feature = QgsFeature()
                        feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                        feature.setAttributes([value, address_geocoded, lon, lat])

                        return feature
        else:
            error_response = json.loads(bytes(response.content()))
            error_message = error_response.get("message", "No error message provided")
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_message}')
    return None
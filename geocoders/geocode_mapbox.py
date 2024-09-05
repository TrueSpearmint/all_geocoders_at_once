from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using Mapbox service
def geocode_mapbox(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()

    query = QUrlQuery()
    query.addQueryItem('q', str(value))
    query.addQueryItem('access_token', user_api_key)
    query.addQueryItem('limit', '1') 

    url = QUrl('https://api.mapbox.com/search/geocode/v6/forward')
    url.setQuery(query)

    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.UserAgentHeader, 'QGIS Plugin "All Geocoders At Once"')

    nam = QgsNetworkAccessManager()
    response = nam.blockingGet(request)

    if response:
        status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            response_json = json.loads(bytes(response.content()))
            if 'features' in response_json and len(response_json['features']) > 0:
                first_feature = response_json['features'][0]
                geometry = first_feature.get('geometry', {})
                coordinates = geometry.get('coordinates', [])
                if len(coordinates) == 2:
                    lon = float(coordinates[0])
                    lat = float(coordinates[1])
                    properties = first_feature.get('properties', {})
                    address_geocoded = properties.get('full_address', 'No address')

                    point_out = QgsPointXY(lon, lat)
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                    feature.setAttributes([value, address_geocoded, lon, lat])

                    return feature
            else:
                context.dlg.plainTextEdit_results.appendPlainText('No features found in response')
        else:
            error_response = json.loads(bytes(response.content()))
            error_message = error_response.get("message", "No error message provided")
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_message}')
    return None
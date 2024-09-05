from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using Azure (ex. Bing Maps) service
def geocode_azure(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()

    query = QUrlQuery()
    query.addQueryItem('api-version', '2023-06-01')
    query.addQueryItem('query', str(value)) 
    query.addQueryItem('subscription-key', user_api_key)
    query.addQueryItem('top', '1')

    url = QUrl('https://atlas.microsoft.com/geocode')
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
                first_result = response_json['features'][0]
                geometry = first_result.get('geometry', {})
                coordinates = geometry.get('coordinates', [])
                if len(coordinates) == 2:
                    lon = float(coordinates[0])
                    lat = float(coordinates[1]) 
                    address_geocoded = first_result.get('properties', {}).get('address', {}).get('formattedAddress', 'No address')

                    point_out = QgsPointXY(lon, lat)
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                    feature.setAttributes([value, address_geocoded, lon, lat])

                    return feature
        else:
            error_response = json.loads(bytes(response.content()))
            error_body = error_response.get("error", {})
            error_message = error_body.get("message", "No error message provided")
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_message}')
    return None

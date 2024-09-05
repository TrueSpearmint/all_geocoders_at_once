from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using Geoapify service
def geocode_geoapify(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()
    query = QUrlQuery()
    query.addQueryItem('text', str(value))
    query.addQueryItem('apiKey', user_api_key)
    query.addQueryItem('limit', '1')
    query.addQueryItem('format', 'json')

    url = QUrl('https://api.geoapify.com/v1/geocode/search')
    url.setQuery(query)

    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.UserAgentHeader, 'QGIS Plugin "All Geocoders At Once"')

    nam = QgsNetworkAccessManager()
    response = nam.blockingGet(request)

    if response:
        status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            response_json = json.loads(bytes(response.content()))
            if 'results' in response_json and len(response_json['results']) > 0:
                first_result = response_json['results'][0]
                lat = float(first_result.get('lat', 0))
                lon = float(first_result.get('lon', 0))
                address_geocoded = first_result.get('formatted', 'No address')

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
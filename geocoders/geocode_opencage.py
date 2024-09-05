from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using OpenCage service
def geocode_opencage(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()

    query = QUrlQuery()
    query.addQueryItem('q', str(value)) 
    query.addQueryItem('key', user_api_key)
    query.addQueryItem('limit', '1') 

    url = QUrl('https://api.opencagedata.com/geocode/v1/json')
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
                geometry = first_result.get('geometry', {})
                if 'lat' in geometry and 'lng' in geometry:
                    lat = float(geometry['lat'])
                    lon = float(geometry['lng'])
                    address_geocoded = first_result.get('formatted', 'No address')

                    point_out = QgsPointXY(lon, lat)
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                    feature.setAttributes([value, address_geocoded, lon, lat])

                    return feature
        else:
            error_response = json.loads(bytes(response.content()))
            error_body = error_response.get("status", {})
            error_message = error_body.get("message", "No error message provided")
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_message}')
    return None

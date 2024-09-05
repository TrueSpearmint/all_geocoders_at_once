from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using Here service
def geocode_here(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()

    query = QUrlQuery()
    query.addQueryItem('q', str(value))
    query.addQueryItem('apikey', user_api_key)
    query.addQueryItem('limit', '1')

    url = QUrl('https://geocode.search.hereapi.com/v1/geocode')
    url.setQuery(query)

    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.UserAgentHeader, 'QGIS Plugin "All Geocoders At Once"')

    nam = QgsNetworkAccessManager()
    response = nam.blockingGet(request)

    if response:
        status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            response_json = json.loads(bytes(response.content()))
            if 'items' in response_json and len(response_json['items']) > 0:
                first_item = response_json['items'][0]
                position = first_item.get('position', {})
                if 'lat' in position and 'lng' in position:
                    lat = float(position['lat'])
                    lon = float(position['lng'])
                    address_geocoded = first_item.get('address', {}).get('label', 'No address')

                    point_out = QgsPointXY(lon, lat)
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                    feature.setAttributes([value, address_geocoded, lon, lat])

                    return feature
        else:
            error_response = json.loads(bytes(response.content()))
            error_message = error_response.get("error_description", "No error message provided")
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_message}')
    return None

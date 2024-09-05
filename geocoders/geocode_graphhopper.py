from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using GraphHopper service
def geocode_graphhopper(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()
    query = QUrlQuery()
    query.addQueryItem('q', str(value))
    query.addQueryItem('key', user_api_key)
    query.addQueryItem('limit', '1')

    url = QUrl('https://graphhopper.com/api/1/geocode')
    url.setQuery(query)

    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.UserAgentHeader, 'QGIS Plugin "All Geocoders At Once"')

    nam = QgsNetworkAccessManager()
    response = nam.blockingGet(request)

    if response:
        status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            response_json = json.loads(bytes(response.content()))
            if 'hits' in response_json and len(response_json['hits']) > 0:
                first_result = response_json['hits'][0]
                point = first_result.get('point', {})
                lat = float(point.get('lat', 0))
                lon = float(point.get('lng', 0))

                country = first_result.get('country', '')
                city = first_result.get('city', '')
                state = first_result.get('state', '')
                street = first_result.get('street', '')
                housenumber = first_result.get('housenumber', '')
                address_geocoded = f"{country}, {state}, {city}, {street}, {housenumber}" if city or state or street or housenumber else 'No address'

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
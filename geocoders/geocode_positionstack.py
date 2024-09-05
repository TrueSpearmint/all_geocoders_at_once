from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using Positionstack service
def geocode_positionstack(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()
    query = QUrlQuery()
    query.addQueryItem('query', str(value))
    query.addQueryItem('access_key', user_api_key)
    query.addQueryItem('limit', '1')

    url = QUrl('https://api.positionstack.com/v1/forward')
    url.setQuery(query)

    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.UserAgentHeader, 'QGIS Plugin "All Geocoders At Once"')

    nam = QgsNetworkAccessManager()
    response = nam.blockingGet(request)

    if response:
        status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            response_json = json.loads(bytes(response.content()))
            if 'data' in response_json and len(response_json['data']) > 0:
                first_result = response_json['data'][0]
                lat = float(first_result.get('latitude', 0))
                lon = float(first_result.get('longitude', 0))

                country = first_result.get('country', '') if first_result.get('country') is not None else ''
                region = first_result.get('region', '') if first_result.get('region') is not None else ''
                street = first_result.get('street', '') if first_result.get('street') is not None else ''
                housenumber = first_result.get('number', '') if first_result.get('number') is not None else ''
                address_geocoded = f"{country}, {region}, {street}, {housenumber}" if country or region or street or housenumber else 'No address'
                address_geocoded = ", ".join(filter(None, [country, region, street, housenumber]))

                point_out = QgsPointXY(lon, lat)
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                feature.setAttributes([value, address_geocoded, lon, lat])

                return feature
        else:
            error_response = json.loads(bytes(response.content()))
            error_body = error_response.get("error", "No error body provided")
            error_message = error_body.get("message", "No error message provided")
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_message}')
    return None
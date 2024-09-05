from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using MapQuest service
def geocode_mapquest(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()

    query = QUrlQuery()
    query.addQueryItem('location', str(value))
    query.addQueryItem('key', user_api_key)
    query.addQueryItem('maxResults', '1')
    query.addQueryItem('outFormat', 'json')

    url = QUrl('https://www.mapquestapi.com/geocoding/v1/address')
    url.setQuery(query)

    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.UserAgentHeader, 'QGIS Plugin "All Geocoders At Once"')

    nam = QgsNetworkAccessManager()
    response = nam.blockingGet(request)

    if response:
        status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code == 200:
            response_json = json.loads(bytes(response.content()))
            results = response_json['results'][0]
            if 'locations' in results and len(results['locations']) > 0:
                location = results['locations'][0]
                latLng = location.get('latLng', {})
                lat = float(latLng.get('lat', 0))
                lon = float(latLng.get('lng', 0))

                country = location.get('adminArea1', '')
                state = location.get('adminArea3', '')
                county = location.get('adminArea4', '')
                city = location.get('adminArea5', '')
                street = location.get('street', '')
                address_geocoded = f"{country}, {state}, {county}, {city}, {street}" if country or state or county or city or street else 'No address'

                point_out = QgsPointXY(lon, lat)
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                feature.setAttributes([value, address_geocoded, lon, lat])

                return feature
        elif status_code == 401:
            error_response = response.content()
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_response}')
        else:
            error_response = response.content()
            error_message = error_response.get("info", "No error info provided").get("message", "No error message provided")
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_message}')
    return None
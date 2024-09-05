from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using TomTom service
def geocode_tomtom(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()
    
    query = QUrlQuery()
    query.addQueryItem('key', user_api_key) 
    query.addQueryItem('limit', '1')

    url = QUrl(f'https://api.tomtom.com/search/2/geocode/{QUrl.toPercentEncoding(value)}.json')
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
                position = first_result.get('position', {})
                if 'lat' in position and 'lon' in position:
                    lat = float(position['lat'])
                    lon = float(position['lon'])
                    address = first_result.get('address', {})
                    country = address.get('country', '')
                    countrySecondarySubdivision = address.get('countrySecondarySubdivision', '')
                    freeformAddress = address.get('freeformAddress', '')
                    address_geocoded = f'{freeformAddress}, {country}, {countrySecondarySubdivision}'

                    point_out = QgsPointXY(lon, lat)
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                    feature.setAttributes([value, address_geocoded, lon, lat])

                    return feature
        else:
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: No error message provided')
    return None

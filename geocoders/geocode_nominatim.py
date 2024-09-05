from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using Nominatim service
def geocode_nominatim(value, context):
    # Forming a request
    query = QUrlQuery()
    query.addQueryItem('q', str(value))
    query.addQueryItem('limit', '1')
    query.addQueryItem('format', 'json')

    url = QUrl('https://nominatim.openstreetmap.org/search')
    url.setQuery(query)

    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.UserAgentHeader, 'QGIS Plugin "All Geocoders At Once"')

    nam = QgsNetworkAccessManager()
    response = nam.blockingGet(request)

    # Processing the request response
    if response:
        status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        # If the request was successful 
        if status_code == 200:
            response_json = json.loads(bytes(response.content()))
            if isinstance(response_json, list) and response_json:
                # Process the first result in the response (if any)
                first_result = response_json[0]
                lon = float(first_result.get('lon', 0))
                lat = float(first_result.get('lat', 0))
                address_geocoded = first_result.get('display_name', 'No address')

                # Creating a feature
                point_out = QgsPointXY(lon, lat)
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                feature.setAttributes([value, address_geocoded, lon, lat])

                return feature
        else:
            # Handling code responses other than 200
            error_response = json.loads(bytes(response.content()))
            error_body = error_response.get("error", "No error body provided")
            error_message = error_body.get("message", "No error message provided")
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_message}')
    return None
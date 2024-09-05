from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json

# Geocoding function using Esri (ArcGIS) service
def geocode_esri(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()

    query = QUrlQuery()
    query.addQueryItem('SingleLine', str(value))
    query.addQueryItem('token', user_api_key)
    query.addQueryItem('f', 'json')
    query.addQueryItem('maxLocations', '1')

    url = QUrl('https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates')
    url.setQuery(query)

    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.UserAgentHeader, 'QGIS Plugin "All Geocoders At Once"')

    nam = QgsNetworkAccessManager()
    response = nam.blockingGet(request)

    # Processing of the response from Esri is different from other services, as an error is returned in the response with code 200
    if response:
        response_json = json.loads(bytes(response.content()))
        if "error" in response_json:
            status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            error_body = response_json.get("error", "No error body provided")
            error_message = error_body.get("message", "No error message provided")
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_message}')
        else:
            if 'candidates' in response_json and len(response_json['candidates']) > 0:
                first_candidate = response_json['candidates'][0]
                location = first_candidate.get('location', {})
                if location:
                    lon = float(location.get('x'))
                    lat = float(location.get('y'))
                    address_geocoded = first_candidate.get('address', 'No address')

                    point_out = QgsPointXY(lon, lat)
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                    feature.setAttributes([value, address_geocoded, lon, lat])

                    return feature
            else:
                context.dlg.plainTextEdit_results.appendPlainText('No candidates found in response')
    else:
        context.dlg.plainTextEdit_results.appendPlainText('No response received')
    return None

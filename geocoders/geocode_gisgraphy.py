from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json
import re

# Geocoding function using Gisgraphy service hosted by Gisgraphy
def geocode_gisgraphy(value, context):
    user_api_key = context.dlg.lineEdit_enterApiKey.text()
    
    query = QUrlQuery()
    query.addQueryItem('address', str(value))
    query.addQueryItem('apikey', user_api_key)
    query.addQueryItem('format', 'json')

    url = QUrl('https://services.gisgraphy.com/geocoding')
    url.setQuery(query)

    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.UserAgentHeader, 'QGIS Plugin "All Geocoders At Once"')

    nam = QgsNetworkAccessManager()
    response = nam.blockingGet(request)

    if response:
        status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        content = bytes(response.content())
        if status_code == 200:
            response_json = json.loads(content())
            if 'result' in response_json and len(response_json['result']) > 0:
                first_result = response_json['result'][0]
                if 'lat' in first_result and 'lng' in first_result:
                    lat = float(first_result['lat'])
                    lon = float(first_result['lng'])
                    country = first_result.get('country', '')
                    formattedFull = first_result.get('formattedFull', 'No address')
                    address_geocoded = f'{formattedFull},{country}'

                    point_out = QgsPointXY(lon, lat)
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                    feature.setAttributes([value, address_geocoded, lon, lat])

                    return feature
        elif status_code == 401:
            if b"Too much requests" in content:
                error_body = content.decode('utf-8')
                # A regular expression to extract the desired parts
                pattern = re.compile(r'<li>(.*?)</li>|<br/>\s*(.*?)\s*</br>|([^<>]*)<a[^>]*>(.*?)</a>', re.S)
                # Text extraction
                matches = pattern.findall(error_body)
                # Merge all found parts on a new line
                error_details = '\n'.join(filter(None, [match[0] or match[1] or match[2].strip() + match[3] for match in matches]))
                context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: 401. Error message: Too much requests. Error details:\n{error_details}')
            else:
                error_body = content.decode('utf-8')
                context.dlg.plainTextEdit_results.appendPlainText(f'Error body: {error_body}')
        else:
            error_body = content.decode('utf-8')
            context.dlg.plainTextEdit_results.appendPlainText(f'Error body: {error_body}')
    return None
from qgis.core import QgsNetworkAccessManager, QgsPointXY, QgsFeature, QgsGeometry
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QUrlQuery
import json
import subprocess

# Geocoding function using DaData service
# The function is different from other services because it does not support get-request
def geocode_dadata(value, context):
    # Calling a function that verifies that curl is installed on the user's system
    if not context.is_curl_installed():
        context.dlg.plainTextEdit_results.appendPlainText(
            "Error: curl is not installed on this system. "
            "Please install curl to use this feature.\n"
            "Windows: Download from https://curl.se/windows/\n"
            "Linux: Install via package manager (e.g., sudo apt install curl)\n"
            "macOS: curl is typically pre-installed or use Homebrew to install it."
        )
        return None

    # API key processing
    dadata_key = context.dlg.lineEdit_enterApiKey.text() 
    if ';' not in dadata_key:
        context.dlg.plainTextEdit_results.appendPlainText("Error: Invalid API key format. It should contain both API and Secret keys separated by a semicolon.")
        return None
    user_api_key = dadata_key.split(';')[0]
    user_secret_key = dadata_key.split(';')[1]
    
    # Data for the request
    query = [str(value)]
    # Forming the curl command
    curl_command = [
        'curl', '-X', 'POST',
        '-H', 'Content-Type: application/json',
        '-H', 'Accept: application/json',
        '-H', f'Authorization: Token {user_api_key}',
        '-H', f'X-Secret: {user_secret_key}',
        '-d', json.dumps(query), 
        'https://cleaner.dadata.ru/api/v1/clean/address'
    ]
    
    try:
        # Executing the curl command
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        # Checking the status of command execution
        if result.returncode != 0:
            context.dlg.plainTextEdit_results.appendPlainText(f"Error: curl command failed with return code {result.returncode}.")
            return None
        # Receive and process a response
        response_text = result.stdout
        response_json = json.loads(response_text)
        if isinstance(response_json, list) and len(response_json) > 0:
            first_result = response_json[0]
            lon = first_result.get('geo_lon')
            lat = first_result.get('geo_lat')
            address_geocoded = first_result.get('result', 'No address')
            if lon is not None and lat is not None:
                point_out = QgsPointXY(float(lon), float(lat))
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPointXY(point_out))
                feature.setAttributes([value, address_geocoded, lon, lat])
                return feature
            else:
                context.dlg.plainTextEdit_results.appendPlainText("Error: No coordinates found in the response")
        else:
            status_code = response_json.get("status", "No error status provided")
            error_message = response_json.get("message", "No error message provided")
            context.dlg.plainTextEdit_results.appendPlainText(f'HTTP error code: {status_code}. Error message: {error_message}')
    except subprocess.CalledProcessError as e:
        if e.returncode == 60:
            context.dlg.plainTextEdit_results.appendPlainText(
                "Error: SSL certificate verification failed.\n"
                "You can try to add the '--insecure' parameter to the curl_command before the URL.\n"
                "Open AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/all_geocoders_at_once/geocoders/geocode_dadata.py\n"
            )
        else:
            context.dlg.plainTextEdit_results.appendPlainText(f"Error: curl command failed with error: {e}")
    except json.JSONDecodeError:
        context.dlg.plainTextEdit_results.appendPlainText("Error: Failed to decode JSON response.")
    except Exception as e:
        context.dlg.plainTextEdit_results.appendPlainText(f"An unexpected error occurred: {e}")
    return None
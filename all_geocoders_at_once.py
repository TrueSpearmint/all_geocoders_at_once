# -*- coding: utf-8 -*-
# Библиотеки для функционирования плагина
from qgis.PyQt.QtCore import QSettings, QCoreApplication # QSettings - для сохранения настроек плагина (размеры и расположение окон, опции и т.д.), QCoreApplication - предоставляет основную инфраструктуру для любого приложения.
from qgis.PyQt.QtGui import QIcon # класс для работы с иконками.
from qgis.PyQt.QtWidgets import QAction # класс для создания действий в интерфейсе пользователя.

from .resources import * #импорт из модуля resources, который изначально создан в директории модуля. В нём хранится иконка, её взаимосвязи и различные статические ресурсы, используемые плагином.
from .all_geocoders_at_once_dialog import AllGeocodersAtOnceDialog # импорт диалогового окна (окна с которым взаимодействует пользователь) плагина.
import os.path # импорт модуля для работы с путями к файлам и директориям (например выбор файлов).
from .terms_of_use_dialog import TermsOfUseDialog # импорт диалогового окна со справкой.

# Библиотеки для работы основных скриптов (в def run)
from PyQt5.QtCore import QThread, pyqtSignal # библиотеки для многопоточности, чтобы процесс можно было остановить.
from qgis.core import QgsNetworkAccessManager, QgsProject, QgsVectorLayer
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl
import subprocess
# Импорт модулей геокодеров
from .geocoders import geocode_nominatim,geocode_photon,geocode_esri,geocode_mapbox,geocode_tomtom,geocode_yandex,geocode_graphhopper,geocode_geoapify,geocode_locationiq,geocode_nettoolkit,geocode_geocodio,geocode_opencage,geocode_google,geocode_here,geocode_azure,geocode_mapquest,geocode_positionstack,geocode_pelias,geocode_gisgraphy,geocode_dadata

# Класс в рамках которого происходит процесс геокодирования. Вынесен отдельно для возможности остановки процесса
class GeocodeThread(QThread):
    progress_updated = pyqtSignal(int)  # сигнал для обновления прогресс-бара.
    geocoding_finished = pyqtSignal(list, int, int, list)  # сигнал для завершения геокодирования.
    message_signal = pyqtSignal(str)  # сигнал для передачи текстовых сообщений. Использование сигнала необходимо, для передачи сообщения в основной класс (то есть поток) и отображения ответов без задержек. 

    def __init__(self, geocode_function, features, field_index, user_api_key, dlg):
        QThread.__init__(self)
        self.geocode_function = geocode_function
        self.features = features
        self.field_index = field_index
        self.user_api_key = user_api_key
        self.dlg = dlg
        self.stop_geocoding = False

    # Проверка наличия curl для геокодера DaData
    def is_curl_installed(self):
        try:
            result = subprocess.run(['curl', '--version'], capture_output=True, text=True, check=True)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False

    def run(self):
        # Инициализация счетчиков
        geocoded_features = []
        geocoded_count = 0
        not_geocoded_count = 0
        not_geocoded_addresses = []

        # Получение значений поля для всех объектов в слое и их подсчёт
        for i, feature in enumerate(self.features):
            if self.stop_geocoding:
                break

            value = feature.attributes()[self.field_index]
            geocoded_feature = self.geocode_function(value, self)

            # Проверка результата геокодирования
            if geocoded_feature:
                geocoded_features.append(geocoded_feature)
                geocoded_count += 1
            else:
                not_geocoded_count += 1
                not_geocoded_addresses.append(value)

            # Обновление прогресс-бара
            self.progress_updated.emit(i + 1)

            # Отправка сообщения о текущем статусе геокодирования
            self.message_signal.emit('')

        # Эмитируем сигнал завершения геокодирования
        self.geocoding_finished.emit(geocoded_features, geocoded_count, not_geocoded_count, not_geocoded_addresses)

class AllGeocodersAtOnce:
    ''' Функционал необходимый для работы любого плагина '''
    def __init__(self, iface): # создание конструктора (шаблона объектов) для класса AllGeocodersAtOnce. Обязательные атрибуты объектов (в данном случае одного плагина): сам объект (self) и iface.
        self.iface = iface # iface — это объект, предоставляемый QGIS, который используется для взаимодействия с интерфейсом QGIS (например, для добавления кнопок на панель инструментов, взаимодействия с картой и т.д.).

        # Опциональные атрибуты. Эти параметры не передаются в конструктор, так как они зависят от внутренней логики работы плагина, а не от параметров, переданных извне.
        self.plugin_dir = os.path.dirname(__file__) # атрибут plugin_dir, который передаёт директорию этого скрипта.
        self.actions = [] # список, в котором будут храниться объекты действий (QActions) плагина: кнопки на панели инструментов, пункты меню и т.д. Используется для хранения всех этих объектов, чтобы позже их можно было удалить при деактивации плагина.
        self.menu = '&All Geocoders At Once' # строка, которая задает название меню плагина.
        self.first_start = None # атрибут для проверки, был ли плагин запущен впервые в текущей сессии QGIS. Может быть полезно, например, для приветственного окна.

    # Метод add_action (произвольное название) добавляет действия (иконку с плагином) в интерфейс QGIS: на панель инструментов и в меню
    def add_action( # список постоянных, используемых в методе.
        self,
        icon_path,
        text, 
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path) # посредством класса QIcon создаётся объект иконки
        action = QAction(icon, text, parent) # создаёт действие (кнопку или пункт меню) с иконкой, текстом и родительским виджетом.
        action.triggered.connect(callback) # привязывает функцию callback к событию активации (например, нажатия на кнопку).
        action.setEnabled(enabled_flag) # устанавливает доступность действия, например, на него можно нажать.

        if status_tip is not None: 
        # Появление всплывающей подсказки (popup) при наведении на кнопку модуля
            action.setStatusTip(status_tip)

        if whats_this is not None: 
        # Отображение текста в строке состояния (status bar) при наведении на кнопку модуля
            action.setWhatsThis(whats_this)

        if add_to_toolbar: 
        # Добавление кнопки плагина (действия=QActions) на панель инструментов (plugins toolbar)
            self.iface.addToolBarIcon(action)

        if add_to_menu: 
        # Добавление кнопки плагина (действия=QActions) в меню
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action) # добавляет действие в список self.actions.

        return action # возвращает созданное действие. То есть плагин можно будет использовать сразу после создания.

    def initGui(self): # произвольное распространённое название
        # Метод initGui предназначен для инициализации графического интерфейса пользователя (GUI) в QGIS. Он создает пункты меню и иконки на панели инструментов, чтобы пользователь мог взаимодействовать с вашим плагином

        icon_path = ':/plugins/all_geocoders_at_once/icon.png' # путь к иконке.
        self.add_action(
            icon_path,
            text='Geocode by any service', # текст при наведении на иконку.
            callback=self.run, # функция, которая будет вызвана при активации действия, в данном случае это метод run.
            parent=self.iface.mainWindow()) # родительский виджет, в данном случае главное окно QGIS.

        self.first_start = True # изменения параметра first_start на True

    def unload(self):
        # Метод unload отвечает за удаление элементов меню и иконок панели инструментов, добавленных плагином в интерфейс QGIS. Необходим при отключении или удалении модуля
        for action in self.actions: # проходит по всем действиям, сохраненным в списке self.actions.
            self.iface.removePluginMenu( # удаление действий из меню. В качестве параметров передаются название меню и само действие.
                '&All Geocoders At Once', 
                action)
            self.iface.removeToolBarIcon(action) # удаление иконки с панели инструментов

    def show_terms_of_use(self):
        # Открыть диалоговое окно со справкой
        dialog = TermsOfUseDialog(self.dlg)
        dialog.exec_()  

    ''' Функционал необходимый для работы данного плагина '''
    def run(self):
        # Проверяем, если окно уже создано
        if hasattr(self, 'dlg') and self.dlg is not None:
            # Если окно уже создано, показываем его
            self.dlg.show()
            self.dlg.raise_()
            self.dlg.activateWindow()
        else:
            # Инициализация диалогового окна при первом запуске
            self.first_start = False
            self.dlg = AllGeocodersAtOnceDialog()
            
            # Получение имён слоёв, загруженных в QGIS
            layer_list = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
            
            self.dlg.comboBox_selectService.addItem("–– Geocoders without API key ––")
            self.dlg.comboBox_selectService.addItems(['Nominatim','Photon','Esri (ArcGis)'])

            self.dlg.comboBox_selectService.addItem("–– Geocoders with API key ––")
            self.dlg.comboBox_selectService.addItems(['Mapbox','TomTom','Yandex','GraphHopper','Geoapify','LocationIQ','NetToolKit','Geocodio','OpenCage'])

            self.dlg.comboBox_selectService.addItem("–– Geocoders with API key with card binding ––")
            self.dlg.comboBox_selectService.addItems(['Google','Here','Azure (ex. Bing Maps)','MapQuest','Positionstack'])
            
            self.dlg.comboBox_selectService.addItem("–– Geocoders with API key and fully paid ––")
            self.dlg.comboBox_selectService.addItems(['Pelias (hosted by Geocode Earth)','Gisgraphy (hosted by Gisgraphy)','DaData'])

            self.dlg.comboBox_selectTable.currentIndexChanged.connect(self.update_attributes) # соединение сигнала изменения выбранного элемента с обновлением списка атрибутов. 
            self.dlg.comboBox_selectService.currentIndexChanged.connect(self.update_api_key_visibility) # соединение сигнала изменения выбора с обновлением видимости поля ключа API.
            self.dlg.comboBox_selectService.currentIndexChanged.connect(self.reset_api_key_label) # вызов функции при изменении в списке comboBox_selectService (выбора сервиса)
            
            self.update_attributes() # вызов функции update_attributes при первой инициализации окна.
            self.update_api_key_visibility() # вызов функции update_api_key_visibility при первой инициализации окна.
            
            self.dlg.pushButton_geocode.clicked.connect(self.geocode_button_clicked) # запуск процесса гекодирования по кнопке "Geocode".
            self.dlg.pushButton_stop.clicked.connect(self.stop_geocoding_process)  # остановка процесса гекодирования по кнопке "Stop".
            self.dlg.pushButton_clearResults.clicked.connect(lambda: (self.dlg.plainTextEdit_results.clear(), self.dlg.progressBar.setValue(0))) # очистка окна вывода и сброс прогресс-бара по кнопке "Clear Results".
            self.dlg.pushButton_termsOfUse.clicked.connect(self.show_terms_of_use) # открытие диалогового окна со справкой по кнопке "Geocoders Terms of Use".
            self.dlg.pushButton_close.clicked.connect(self.dlg.close) # закрытие диалогового окна по кнопке "Close".

        # Обновление списка слоев
        self.update_layer_list()
        
        # Отобразить диалоговое окно
        self.dlg.show()
        # Метод exec_ не позволяет взаимодействовать с другими окнами приложения, пока выполняется вызванная операция (геокодирование).
        result = self.dlg.exec_()
        if result: # если нажата кнопка, которая возвращает положительный результат ("Geocode"), то выполнить код.
            pass
    
    # Получение имён слоёв, загруженных в QGIS
    def update_layer_list(self):
        layer_list = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
        self.dlg.comboBox_selectTable.clear()  # очистка списка слоёв.
        self.dlg.comboBox_selectTable.addItems(layer_list)  # добавление списка слоёв.
        self.update_attributes()  # обновление списка атрибутов для нового списка слоев.

    # Функция передачи слоя по его имени
    def get_layer_by_name(self, layer_name):
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == layer_name:
                return layer
        return None
    
    # Функция передачи атрибутов слоя
    def update_attributes(self):
        selected_layer_name = self.dlg.comboBox_selectTable.currentText()
        selected_layer = self.get_layer_by_name(selected_layer_name)
        if selected_layer and isinstance(selected_layer, QgsVectorLayer): # проверка, чтобы атрибуты считывались только с векторных слоёв.
            self.dlg.comboBox_selectAttribute.clear() # очистка списка атрибутов.
            attributes_list = [field.name() for field in selected_layer.fields()] # получение списка атрибутов слоя.
            self.dlg.comboBox_selectAttribute.addItems(attributes_list) # добавление атрибутов в comboBox_selectAttribute.

    # Функция проверки необходимости ключа API для выбранного сервиса
    def update_api_key_visibility(self):
        selected_service = self.dlg.comboBox_selectService.currentText()
        if selected_service in ['Mapbox','TomTom','Yandex','GraphHopper','Geoapify','LocationIQ','NetToolKit','Geocodio','OpenCage','Google','Here','Azure (ex. Bing Maps)','MapQuest','Positionstack','Pelias (hosted by Geocode Earth)','Gisgraphy (hosted by Gisgraphy)']:
            self.dlg.lineEdit_enterApiKey.setDisabled(False)  # делает поле доступным.
            self.dlg.lineEdit_enterApiKey.setPlaceholderText('')
            self.dlg.label_enterApiKey.setText('Enter API key')
        elif selected_service in ['Esri (ArcGis)']:
            self.dlg.lineEdit_enterApiKey.setDisabled(False)  # делает поле доступным.
            self.dlg.lineEdit_enterApiKey.setPlaceholderText('')
            self.dlg.label_enterApiKey.setText('Enter API key if necessary')
        elif selected_service in ['DaData']:
            self.dlg.lineEdit_enterApiKey.setDisabled(False)  # делает поле доступным.
            self.dlg.lineEdit_enterApiKey.setPlaceholderText('API-key;secret-key')
            self.dlg.label_enterApiKey.setText('Enter API key')
        else:
            self.dlg.lineEdit_enterApiKey.setDisabled(True)  # делает поле недоступным.
            self.dlg.lineEdit_enterApiKey.setText('')
            self.dlg.lineEdit_enterApiKey.setPlaceholderText('')
            self.dlg.label_enterApiKey.setText('API Key is not needed')

    # Сброс текста в поле ввода API ключа
    def reset_api_key_label(self):
        self.dlg.lineEdit_enterApiKey.setText("")

    # Проверка наличия интернет-соединения
    def internet_is_available(self):
        url = QUrl('https://google.com')

        request = QNetworkRequest(url)
        nam = QgsNetworkAccessManager()
        response = nam.blockingGet(request)

        if response:
            status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            if status_code == 200:
                return True
        return False
    
    # Функция остановки процесса геокодирования
    def stop_geocoding_process(self):
        if hasattr(self, 'geocode_thread') and self.geocode_thread.isRunning():  # проверка на наличие потока геокодирования и его активность.
                self.geocode_thread.stop_geocoding = True  # установка флага для остановки процесса в потоке.
                self.dlg.plainTextEdit_results.appendPlainText('Geocoding process stopped by user.')


    # Основная функция, выполняемая при нажатии на кнопку "Goecode". Сбор данных слоя, отправка объектов сервису и обработка результатов 
    def geocode_button_clicked(self):
        # Сбор данных слоя и выбранного сервиса
        selected_layer_name = self.dlg.comboBox_selectTable.currentText()
        selected_attribute_name = self.dlg.comboBox_selectAttribute.currentText()
        selected_service_name = self.dlg.comboBox_selectService.currentText()

        # Проверка наличия слоя
        selected_layer = self.get_layer_by_name(selected_layer_name)
        if not selected_layer:
            self.dlg.plainTextEdit_results.appendPlainText('Layer is not selected')
            return

        # Проверка наличия поля атрибутов
        field_index = selected_layer.fields().indexOf(selected_attribute_name)
        if field_index == -1:
            self.dlg.plainTextEdit_results.appendPlainText('Address field is not selected')
            return
        
        # Проверка наличия интернет-соединения
        if not self.internet_is_available():
            self.dlg.plainTextEdit_results.appendPlainText(f'No internet connection')
            return

        # Выбор сервиса геокодирования и проверка его наличия. Сами функции подключаются из отдельного файла
        geocode_function = {
            'Nominatim': geocode_nominatim,
            'Photon': geocode_photon,
            'Esri (ArcGis)': geocode_esri,
            'Mapbox': geocode_mapbox,
            'TomTom': geocode_tomtom,
            'Yandex': geocode_yandex,
            'GraphHopper': geocode_graphhopper,
            'Geoapify': geocode_geoapify,
            'LocationIQ': geocode_locationiq,
            'NetToolKit': geocode_nettoolkit,
            'Geocodio': geocode_geocodio,
            'OpenCage': geocode_opencage,
            'Google': geocode_google,
            'Here': geocode_here,
            'Azure (ex. Bing Maps)': geocode_azure,
            'MapQuest': geocode_mapquest,
            'Positionstack': geocode_positionstack,
            'Pelias (hosted by Geocode Earth)': geocode_pelias,
            'Gisgraphy (hosted by Gisgraphy)': geocode_gisgraphy,
            'DaData': geocode_dadata,
        }.get(selected_service_name)
        if not geocode_function:
            self.dlg.plainTextEdit_results.appendPlainText('Geocoding service is not selected')
            return
        
        # Инициализируем переменную user_api_key
        user_api_key = None
        # Проверка наличия API ключа перед геокодированием
        if selected_service_name in ['Mapbox','TomTom','Yandex','GraphHopper','Geoapify','LocationIQ','NetToolKit','Geocodio','OpenCage','Google','Here','Azure (ex. Bing Maps)','MapQuest','Positionstack','Pelias (hosted by Geocode Earth)','Gisgraphy (hosted by Gisgraphy)','DaData']:
            user_api_key = self.dlg.lineEdit_enterApiKey.text()
            if not user_api_key:
                self.dlg.plainTextEdit_results.appendPlainText('API key is missing')
                return
            
        # Установка максимального и минимального значения для прогресс-бара
        features = list(selected_layer.getFeatures())
        total_features = len(features)
        self.dlg.progressBar.setMinimum(0)
        self.dlg.progressBar.setMaximum(total_features)

        # Создание потока для геокодирования и соединение его с функциями обновления прогресс-бара и вывода результатов
        self.geocode_thread = GeocodeThread(geocode_function, features, field_index, user_api_key, self.dlg)
        self.geocode_thread.progress_updated.connect(self.update_progress_bar)
        self.geocode_thread.geocoding_finished.connect(self.geocoding_finished)
        self.geocode_thread.message_signal.connect(self.append_text_to_results)

        # Активация (включение) кнопки "Stop" для возможности прерывания процесса
        self.dlg.pushButton_stop.setEnabled(True) 
        # Запуск потока геокодирования 
        self.geocode_thread.start()  

    # Функция обновления значения прогресс-бара
    def update_progress_bar(self, value):
        self.dlg.progressBar.setValue(value)

    # Функция вывода ответа геокодера (не в одну строчку, чтобы избавиться от пустой строки)
    def append_text_to_results(self, text):
        current_text = self.dlg.plainTextEdit_results.toPlainText()
        updated_text = current_text + text
        self.dlg.plainTextEdit_results.setPlainText(updated_text)

    # Функция вывода сообщений по результатам геокодирования
    def geocoding_finished(self, geocoded_features, geocoded_count, not_geocoded_count, not_geocoded_addresses):
        self.dlg.pushButton_stop.setEnabled(False)
        total_features = self.dlg.progressBar.maximum()
        self.dlg.progressBar.setValue(total_features) # в любом случае заполнить прогресс-бар.
        
        # Создание выходного слоя
        selected_service_name_unified = self.dlg.comboBox_selectService.currentText().split()[0].lower()
        layer_out_name = f"{selected_service_name_unified}_geocoded"
        layer_out = QgsVectorLayer("Point?crs=EPSG:4326&field=address_source:string&field=address_geocoded:string&field=lon:double&field=lat:double",
                                   layer_out_name, "memory")

        # Вывод текста о результатах операции геокодирования
        if geocoded_count > 0:
            # Добавить объекты в слой и на карту
            layer_out.dataProvider().addFeatures(geocoded_features)
            layer_out.updateExtents()
            project = QgsProject.instance()
            project.addMapLayer(layer_out)

            # Формирование сообщения о негеокодированных адресах
            if not_geocoded_addresses:
                self.dlg.plainTextEdit_results.appendPlainText("Not geocoded addresses: ")
                for address in not_geocoded_addresses:
                    self.dlg.plainTextEdit_results.appendPlainText(address)
            
            # Добавить сообщение о завершении процесса
            self.dlg.plainTextEdit_results.appendPlainText('')
            self.dlg.plainTextEdit_results.appendPlainText(f'Successfully geocoded: {geocoded_count}')
            self.dlg.plainTextEdit_results.appendPlainText(f'Not geocoded: {not_geocoded_count}')
            self.dlg.plainTextEdit_results.appendPlainText('Geocoding is complete!')
        else:
            self.dlg.plainTextEdit_results.appendPlainText('Geocoding was not successful')
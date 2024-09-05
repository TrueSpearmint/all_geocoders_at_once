# -*- coding: utf-8 -*-

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

class TermsOfUseDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(TermsOfUseDialog, self).__init__(parent)
        ui_file_path = os.path.join(os.path.dirname(__file__), 'terms_of_use_dialog.ui')
        uic.loadUi(ui_file_path, self)
        self.setWindowTitle("Geocoders Terms of Use")
#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import platform
import traceback
import urllib
import webbrowser

from PyQt5.QtCore import QObject
import PyQt5.QtCore as QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *

from electrum.i18n import _
import sys
from lib import ELECTRUM_VERSION

issue_template = """Traceback
=========
```
{traceback}
```
Additional information
======================
- Electrum version: {electrum_version}
- Operating system: {os}
- Wallet type: {wallet_type}
"""


class Exception_Window(QWidget):
    _active_window = None

    def __init__(self, main_window, exctype, value, tb):
        self.exc_args = (exctype, value, tb)
        self.main_window = main_window
        QWidget.__init__(self)
        self.setWindowTitle('Electrum - ' + _('An Error Occured'))
        self.setMinimumSize(600, 300)

        main_box = QVBoxLayout()

        heading = QLabel('<h2>' + _('Sorry!') + '</h2>')
        main_box.addWidget(heading)
        main_box.addWidget(QLabel(_('Something went wrong while executing Electrum.')))

        main_box.addWidget(QLabel(
            _('To help us diagnose and fix the problem, you can send us a bug report with the following information:')))

        info_textfield = QTextEdit()
        info_textfield.setReadOnly(True)
        info_textfield.setText(self.get_report_string())
        main_box.addWidget(info_textfield)

        report_button = QPushButton(_('Send Bug Report'))
        report_button.clicked.connect(self.send_report)
        report_button.setIcon(QIcon(":icons/github_mark.png"))
        main_box.addWidget(report_button, 1, QtCore.Qt.AlignLeft)

        close_button = QPushButton(_('Close'))
        close_button.clicked.connect(self.close)
        main_box.addWidget(close_button, 1, QtCore.Qt.AlignRight)

        self.setLayout(main_box)
        self.show()

    def send_report(self):
        url = 'https://github.com/spesmilo/electrum/issues/new?body={}'.format(
            urllib.parse.quote(self.get_report_string()))
        webbrowser.open(url, new=2)

    def on_close(self):
        sys.__excepthook__(*self.exc_args)
        self.close()

    def closeEvent(self, event):
        self.on_close()
        event.accept()

    def get_report_string(self):
        args = {
            "traceback": "".join(traceback.format_exception(*self.exc_args)),
            "electrum_version": ELECTRUM_VERSION,
            "os": platform.platform(),
            "wallet_type": "unknown"
        }
        try:
            args["wallet_type"] = self.main_window.wallet.wallet_type
        except:
            # Maybe the wallet isn't loaded yet
            pass
        return issue_template.format(**args)


def _show_window(*args):
    Exception_Window._active_window = Exception_Window(*args)

class Exception_Hook(QObject):
    _report_exception = QtCore.pyqtSignal(object, object, object, object)

    def __init__(self, main_window, *args, **kwargs):
        super(Exception_Hook, self).__init__(*args, **kwargs)
        self.main_window = main_window
        sys.excepthook = self.handler
        self._report_exception.connect(_show_window)

    def handler(self, *args):
        self._report_exception.emit(self.main_window, *args)
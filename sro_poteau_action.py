# -*- coding: utf-8 -*-


import os

from PyQt5.QtGui import QIcon
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from PyQt5.QtWidgets import *
from qgis.core import *
import processing


class SROPoteauAction(QtWidgets.QDialog):
    def __init__(self, section, co, pt, iface, t_actions_result, parent=None):
        """Constructor."""
        super(SROPoteauAction, self).__init__(parent)
        self.setWindowTitle("SRO Print - Ajout Action")
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.setWindowIcon(QIcon(scriptDir + os.path.sep + 'icon.png'))

        self.btannul = QPushButton("Annuler", self)
        self.btok = QPushButton("OK", self)
        self.t_actions_result = t_actions_result
        self.t_actions = []
        self.exec(section, co, pt, iface)


    def exec(self, section, co, pt, iface):
        layers = []

        for layer in QgsProject.instance().mapLayers().values():
            layers.append(layer)

        for i in layers:
            if co == i.name() and co != "":
                co = i
            if pt == i.name() and pt != "":
                pt = i

        co.selectByExpression("SECTION=" + section)

        co_temp = processing.run("native:saveselectedfeatures", {'INPUT': co, 'OUTPUT': 'memory:'})[
            'OUTPUT']
        co.removeSelection()

        ptt = None

        for co_feat in co_temp.getFeatures():
            co_geo = co_feat.geometry()
            for pt_feat in pt.getFeatures():
                pt_geo = pt_feat.geometry()
                intersect = co_geo.intersects(pt_geo)
                if intersect is True:
                    if ptt is None:
                        ptt = [pt_feat["CODE_ID"]]
                    else:
                        ptt.append(pt_feat["CODE_ID"])

        listep = []
        i2 = 6
        i3 = 3
        i4 = 0
        if self.get_boolean_table() is True:
            for feat in pt.getFeatures():
                for pt in ptt:
                    if feat["CODE_ID"] == pt and feat["REMPLA_APP"] == "OUI":
                        if feat["NOM"] not in listep:
                            self.t_actions.append([feat["NOM"], QLabel(feat["NOM"], self), QLineEdit("", self),""])
            for i in self.t_actions:
                i[1].move(5, i2)
                i[2].move(100, i3)
                i2 += 30
                i3 += 30
        else:
            for feat in pt.getFeatures():
                for pt in ptt:
                    if feat["CODE_ID"] == pt and feat["REMPLA_APP"] == "OUI":
                        if feat["NOM"] not in listep:
                            self.t_actions.append([feat["NOM"], QLabel(feat["NOM"], self), QLineEdit(self.t_actions_result[i4][3], self),""])
                            i4+= 1
            for i in self.t_actions:
                i[1].move(5, i2)
                i[2].move(100, i3)
                i2 += 30
                i3 += 30

        self.btannul.move(125, i2 + 10)
        self.btok.move(40, i2 + 10)

    def get_table(self):
        for i in self.t_actions:
            i[3] = i[2].text()

        return self.t_actions

    def get_boolean_table(self):
        if len(self.t_actions_result) > 0:
            return False
        else:
            return True

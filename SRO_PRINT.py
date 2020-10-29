# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import *
from qgis.utils import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import (
    QAction,
    QFileDialog,
    QProgressBar
)
from qgis.PyQt.QtPrintSupport import QPrinter
from datetime import date
from qgis.core import *
from qgis.PyQt.QtGui import (
    QPolygonF,
    QColor
)
from qgis.PyQt.QtCore import *
from .resources import *
from .sro_menu import SROPrintDialog
from .sro_poteau_action import SROPoteauAction

import os.path
import processing

import time

class SROPrint:

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SROPrint_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&SRO PRINT')

        self.first_start = None

        self.t_actions = []
    def tr(self, message):
        return QCoreApplication.translate('SROPrint', message)

    def ajout_action(self, section, co, pt, iface):
        if len(self.t_actions) > 0:
            self.pa = SROPoteauAction(section, co, pt, iface, self.t_actions)
        else:
            self.pa = SROPoteauAction(section, co, pt, iface, [])
        self.pa.show()

        self.pa.btannul.clicked.connect(lambda: self.pa.close())
        self.pa.btok.clicked.connect(lambda: self.ajout_action_finale())

    def ajout_action_finale(self):
        self.dlg.pushButton_action.setText("[...]")
        self.t_actions = self.pa.get_table()
        self.pa.close()

    def clean_action(self):
        self.dlg.pushButton_action.setText("...")
        self.t_actions = []
    def add_action(
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

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):

        icon_path = ':/plugins/SRO_PRINT/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'SRO PRINT'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SRO PRINT'),
                action)
            self.iface.removeToolBarIcon(action)

    def select_output_file(self):
      filename,  _filter  =  QFileDialog.getSaveFileName(
        self.dlg,"Sélectionner le fichier de sortie","",'*.pdf' )
      self.dlg.lineEdit.setText(filename)

    def polygon4(self,p1,p2,p3,p4,layout):
        py = QPolygonF()
        py.append(QPointF(p4, p2))
        py.append(QPointF(p1, p2))
        py.append(QPointF(p1, p3))
        py.append(QPointF(p4, p3))

        polygonItem = QgsLayoutItemPolygon(py, layout)
        layout.addItem(polygonItem)

    def polygon5(self,p1,p2,p3,p4,p5,layout):
        py = QPolygonF()

        py.append(QPointF(p3, p5))
        py.append(QPointF(p3, p4))
        py.append(QPointF(p2, p4))
        py.append(QPointF(p2, p5))
        py.append(QPointF(p1, p5))
        py.append(QPointF(p1, p4))
        py.append(QPointF(p2, p4))
        py.append(QPointF(p2, p5))
        py.append(QPointF(p3, p5))


        polygonItem = QgsLayoutItemPolygon(py, layout)
        layout.addItem(polygonItem)

    def polygon6(self,p1,p2,p3,p4,p5,p6,layout):
        py = QPolygonF()


        py.append(QPointF(p6, p1))
        py.append(QPointF(p6, p2))
        py.append(QPointF(p5, p2))
        py.append(QPointF(p5, p1))
        py.append(QPointF(p4, p1))
        py.append(QPointF(p4, p2))
        py.append(QPointF(p3, p2))
        py.append(QPointF(p3, p1))
        py.append(QPointF(p4, p1))
        py.append(QPointF(p4, p2))
        py.append(QPointF(p5, p2))
        py.append(QPointF(p5, p1))
        py.append(QPointF(p6, p1))



        polygonItem = QgsLayoutItemPolygon(py, layout)
        layout.addItem(polygonItem)

    def libeltext(self,text,taille,police,p1,p2,color,layout):
        libel = QgsLayoutItemLabel(layout)
        libel.setText(text)

        if taille is not None:
             libel.setFont(QFont(police, taille))

        libel.adjustSizeToText()
        libel.attemptMove(QgsLayoutPoint(p1, p2))
        libel.setFontColor(color)
        layout.addItem(libel)


    def refresh(self):
        list = None
        verif = True
        ly = None
        layers = []

        for layer in QgsProject.instance().mapLayers().values():
            layers.append(layer)

        for i in layers:
            if self.dlg.co.text() in i.name() and self.dlg.co.text() != "":
                ly = i

        if ly is not None:
            self.dlg.comboBox.clear()
            features = ly.getFeatures()
            for feat in features:
                sect = feat["SECTION"]
                if list is None:
                    list = [sect]
                for i in list:
                    if sect == i:
                        verif = False
                if verif is True:
                    list.append(sect)
                else:
                    verif = True

            self.dlg.comboBox.addItems(list)

        pterror = True
        for i in layers:
            if self.dlg.pt.text() == i.name() and self.dlg.pt.text() != "":
                pt = i
                pterror = False
        if pterror is False:
            self.dlg.pushButton_action.setEnabled(True)

    def run(self):




        list = None
        verif = True

        layers = []

        co = None
        pt = None
        bo = None

        for layer in QgsProject.instance().mapLayers().values():
            layers.append(layer)


        for i in layers:
            if "CABLE_OPTIQUE" in i.name():
                co = i
            if "POINT_TECHNIQUE" in i.name():
                pt = i
            if "BOITE_OPTIQUE" in i.name():
                bo = i




        if co is not None:
            features = co.getFeatures()

            for feat in features:
                sect = feat["SECTION"]

                if list is None:
                    list = [sect]
                for i in list:
                    if sect == i:
                        verif = False
                if verif is True:
                    list.append(sect)
                else:
                    verif = True

        if self.first_start == True:
            self.first_start = False
            self.dlg = SROPrintDialog()
            self.dlg.pushButton.clicked.connect(self.select_output_file)
            self.dlg.pushButton_2.clicked.connect(self.refresh)
            self.dlg.pushButton_action.clicked.connect(lambda: self.ajout_action(self.dlg.comboBox.currentText(), self.dlg.co.text(), self.dlg.pt.text(),self.iface))
            self.dlg.comboBox.activated.connect(self.clean_action)
        if co is not None:
            self.dlg.comboBox.clear()
            self.dlg.comboBox.addItems(list)
            self.dlg.co.setText(co.name())
            self.dlg.co.setEnabled(False)
        if pt is not None:
            self.dlg.pushButton_action.setEnabled(True)
            self.dlg.pt.setText(pt.name())
            self.dlg.pt.setEnabled(False)
        if bo is not None:
            self.dlg.bo.setText(bo.name())
            self.dlg.bo.setEnabled(False)

        self.dlg.lineEdit.setEnabled(False)



        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            coerror = True
            boerror = True
            pterror = True
            fileerror = False
            filename = self.dlg.lineEdit.text()
            for i in layers:
                if self.dlg.co.text() == i.name() and self.dlg.co.text() != "":
                    co = i
                    coerror = False
                if self.dlg.bo.text() == i.name() and self.dlg.bo.text() != "":
                    bo = i
                    boerror = False
                if self.dlg.pt.text() == i.name() and self.dlg.pt.text() != "":
                    pt = i
                    pterror = False

            if filename == "":
                fileerror = True

            if coerror is True:
                iface.messageBar().pushMessage("Ooops", "Couche CABLE_OPTIQUE manquante", level=Qgis.Critical, duration=3)
            if boerror is True:
                iface.messageBar().pushMessage("Ooops", "Couche BOITE_OPTIQUE manquante", level=Qgis.Critical, duration=3)
            if pterror is True:
                iface.messageBar().pushMessage("Ooops", "Couche POINT_TECHNIQUE manquante", level=Qgis.Critical, duration=3)
            if fileerror is True:
                iface.messageBar().pushMessage("Ooops", "Lien du fichier manquant", level=Qgis.Critical, duration=3)


            if coerror is False and boerror is False and pterror is False and fileerror is False:
                progressMessageBar = iface.messageBar().createMessage("Création en cours veuillez patienter...")
                progress = QProgressBar()
                progress.setMaximum(10)
                progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
                progressMessageBar.layout().addWidget(progress)
                iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)

                lien = filename.split("/")
                project = QgsProject()
                layout = QgsPrintLayout(project)
                layout.initializeDefaults()

                co.selectByExpression("SECTION="+self.dlg.comboBox.currentText())
                co_temp = processing.run("native:saveselectedfeatures", {'INPUT': co, 'OUTPUT': 'memory:'})[
                    'OUTPUT']
                co_temp.setName('Cable Optique')


                labeling = co.labeling().clone()
                settings = labeling.settings()
                format = settings.format()
                format.setSizeUnit(QgsUnitTypes.RenderPoints)
                settings.setFormat(format)
                labeling.setSettings(settings)
                co_temp.setLabeling(labeling)
                co_temp.setLabelsEnabled(True)

                renderer = co.renderer().clone()
                ctx = QgsRenderContext()

                renderer.startRender(ctx, QgsFields())
                for feature in co_temp.getFeatures():
                    ctx.expressionContext().setFeature(feature)
                    if renderer.willRenderFeature(feature, ctx):
                        symbol = renderer.symbolForFeature(feature, ctx).clone()
                renderer = QgsSingleSymbolRenderer(symbol)
                co_temp.setRenderer(renderer)
                co_temp.triggerRepaint()




                ptt = None
                bot = None
                verif = False

                pt.selectByExpression("NOM=table_vide")
                pt_temp = processing.run("native:saveselectedfeatures", {'INPUT': pt, 'OUTPUT': 'memory:'})[
                    'OUTPUT']
                pt.removeSelection()
                pt_temp.setName('Point Technique')

                pt_temp.startEditing()
                for co_feat in co_temp.getFeatures():
                    co_geo = co_feat.geometry()
                    for pt_feat in pt.getFeatures():
                        pt_geo = pt_feat.geometry()
                        intersect = co_geo.intersects(pt_geo)
                        if intersect is True:
                            if ptt is None:
                                ptt = [pt_feat["CODE_ID"]]
                                pt_temp.addFeatures([pt_feat])
                                verif = True
                            else:
                                for i in ptt:
                                    if i == pt_feat["CODE_ID"]:

                                        verif = True
                            if verif is False:
                                ptt.append(pt_feat["CODE_ID"])
                                pt_temp.addFeatures([pt_feat])
                            else:
                                verif = False
                pt_temp.commitChanges()
                pt.selectByExpression("NOM=table_vide")

                renderer = pt.renderer().clone()
                renderer2 = pt.renderer().clone()
                renderer3 = pt.renderer().clone()
                renderer2.deleteAllCategories()
                renderer3.deleteAllCategories()
                pt_temp.setRenderer(renderer)
                ctx = QgsRenderContext()
                table = []
                table2 = []

                for feature in pt_temp.getFeatures():
                    for i in renderer.categories():
                        renderer3.addCategory(i)
                        #####################################
                        renderer3.startRender(ctx, QgsFields())
                        ctx.expressionContext().setFeature(feature)
                        #####################################
                        if renderer3.willRenderFeature(feature, ctx):
                            if i.label() not in table and i.label() != "":
                                table.append(i.label())
                                table2.append(i)
                        #####################################
                        renderer3.stopRender(ctx)
                        #####################################
                        renderer3.deleteAllCategories()

                for i in table2:
                    i.setLabel(i.label().lower())
                    renderer2.addCategory(i)

                pt_temp.setRenderer(renderer2)
                pt_temp.triggerRepaint()


                bo_temp = processing.run("native:saveselectedfeatures", {'INPUT': bo, 'OUTPUT': 'memory:'})[
                    'OUTPUT']
                bo_temp.setName('Boite Optique')

                labeling = bo.labeling().clone()
                settings = labeling.settings()
                format = settings.format()
                format.setSizeUnit(QgsUnitTypes.RenderPoints)
                settings.setFormat(format)
                labeling.setSettings(settings)
                bo_temp.setLabeling(labeling)
                bo_temp.setLabelsEnabled(True)



                bo_temp.startEditing()
                for co_feat in co_temp.getFeatures():
                    co_geo = co_feat.geometry()
                    for bo_feat in bo.getFeatures():
                        bo_geo = bo_feat.geometry()
                        intersect = co_geo.intersects(bo_geo)
                        if intersect is True:
                            if bot is None:
                                bot = [bo_feat["id"]]
                                bo_temp.addFeatures([bo_feat])
                                verif = True
                            else:
                                for i in bot:
                                    if i == bo_feat["id"]:
                                        verif = True
                            if verif is False:
                                bot.append(bo_feat)
                                bo_temp.addFeatures([bo_feat])
                            else:
                                verif = False
                bo_temp.commitChanges()
                bo.removeSelection()

                renderer = bo.renderer().clone()
                renderer2 = bo.renderer().clone()
                renderer3 = bo.renderer().clone()
                renderer2.deleteAllCategories()
                renderer3.deleteAllCategories()
                bo_temp.setRenderer(renderer)
                ctx = QgsRenderContext()
                table = []
                table2 = []

                for feature in bo_temp.getFeatures():
                    for i in renderer.categories():
                        renderer3.addCategory(i)
                        #####################################
                        renderer3.startRender(ctx, QgsFields())
                        ctx.expressionContext().setFeature(feature)
                        #####################################
                        if renderer3.willRenderFeature(feature, ctx):
                            if i.label() not in table and i.label() != "":
                                table.append(i.label())
                                table2.append(i)
                        #####################################
                        renderer3.stopRender(ctx)
                        #####################################
                        renderer3.deleteAllCategories()


                for i in table2:
                    i.setLabel(i.label().lower())
                    renderer2.addCategory(i)

                bo_temp.setRenderer(renderer2)
                bo_temp.triggerRepaint()

                urlWithParams = 'type=xyz&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0&crs=EPSG3857'
                maplayer = QgsRasterLayer(urlWithParams, 'OpenStreetMap', 'wms')

                s = QgsMapSettings()
                s.setLayers([bo_temp, pt_temp, co_temp, maplayer])
                layout = QgsLayout(QgsProject.instance())
                layout.initializeDefaults()
                ##RENDER 1

                s = QgsMapSettings()
                s.setLayers([bo_temp, pt_temp, co_temp, maplayer])

                geo = co_temp.extent()
                map = QgsLayoutItemMap(layout)
                map.setRect(QRectF(20, 20, 200, 100))
                map.setFrameEnabled(True)
                map.setLayers([bo_temp, pt_temp, co_temp, maplayer])
                map.setCrs(co_temp.crs())
                map.setExtent(QgsRectangle(geo.xMinimum() - 50, geo.yMinimum() - 25, geo.xMaximum() + 25,
                                           geo.yMaximum() + 25).buffered(40))
                map.setExtent(QgsRectangle(geo.xMinimum(), geo.yMinimum(), geo.xMaximum() + 100,
                                           geo.yMaximum() +100).buffered(130))
                layout.addLayoutItem(map)

                map.attemptMove(QgsLayoutPoint(68, 1))
                map.attemptResize(QgsLayoutSize(228, 207.8, QgsUnitTypes.LayoutMillimeters))

                ##
                ##RENDER 2

                co_temp.selectAll()

                co_temp2 = processing.run("native:saveselectedfeatures", {'INPUT': co_temp, 'OUTPUT': 'memory:'})[
                    'OUTPUT']
                co_temp.removeSelection()

                renderer = co.renderer().clone()
                renderer2 = co.renderer().clone()
                renderer3 = co.renderer().clone()
                renderer2.deleteAllCategories()
                renderer3.deleteAllCategories()
                co_temp.setRenderer(renderer)
                ctx = QgsRenderContext()
                table = []
                table2 = []

                for feature in co_temp.getFeatures():
                    for i in renderer.categories():
                        renderer3.addCategory(i)
                        #####################################
                        renderer3.startRender(ctx, QgsFields())
                        ctx.expressionContext().setFeature(feature)
                        #####################################
                        if renderer3.willRenderFeature(feature, ctx):
                            if i.label() not in table and i.label() != "":
                                table.append(i.label())
                                table2.append(i)
                        #####################################
                        renderer3.stopRender(ctx)
                        #####################################
                        renderer3.deleteAllCategories()

                for i in table2:
                    i.setLabel(i.label().lower())
                    renderer2.addCategory(i)

                co_temp.setRenderer(renderer2)
                renderer3 = renderer2.clone()
                co_temp2.setRenderer(renderer3)
                co_temp.triggerRepaint()
                co_temp2.triggerRepaint()

                map2 = QgsLayoutItemMap(layout)
                map2.attemptSetSceneRect(QRectF(0, 0, 64, 104))
                map2.attemptMove(QgsLayoutPoint(2, 62))
                map2.setFrameEnabled(True)
                map2.setLayers([co_temp2, maplayer])
                map2.setCrs(co_temp.crs())
                layout.addLayoutItem(map2)
                map2.setExtent(co_temp.extent().buffered(250))

                ##

                item = QgsLayoutItemScaleBar(layout)


                features = co.getFeatures()
                i=0
                carto= 0
                cables = []


                for feat in features:
                    if feat["SECTION"] == self.dlg.comboBox.currentText():
                        cables.append(str(feat["id"])+"`"+feat["NOM"]+"`"+str(feat["CAPACITE"]))
                        carto = carto + float(feat["LGR_CARTO"])
                        if i == 0:
                            sro = feat["RATTACH"]
                            cap = feat["CAPACITE"]
                            i=1

                listep = []
                verif = True


                for feat in pt_temp.getFeatures():
                    for pt in ptt:
                        if feat["CODE_ID"] == pt and feat["REMPLA_APP"] == "OUI":
                            listep.append(feat["NOM"])

                self.polygon4(10,6,56,60,layout)

                logo = QgsLayoutItemPicture(layout)

                logo.setPicturePath(QgsApplication.qgisSettingsDirPath()+"python/plugins/sro_print/logo.png")
                logo.attemptSetSceneRect(QRectF(0, 0, 20, 20))
                logo.attemptMove(QgsLayoutPoint(25, 12))

                layout.addItem(logo)
                h = None
                b = None
                t = None
                numAction = 0


                if listep is not None:
                    while len(self.t_actions) < len(listep):
                        self.t_actions.append([" ", " ", " "," "])


                    for i in listep:
                        if h is None:
                            h = 1
                        else:
                            h = h + 5
                        if b is None:
                            b = 6
                        else:
                            b = b + 5

                        self.polygon5(68,92,120,b,h,layout)

                        if t is None:
                            self.libeltext("Nom poteau",None,None,68.5,1,QColor(81,137,172),layout)
                            self.libeltext("Action",None,None,93,1,QColor(81,137,172),layout)
                            t = 7
                            b = b + 5
                            h = h + 5
                            self.polygon5(68,92,120,b,h,layout)
                            self.libeltext(i,8,'Arial',68.5,t,QColor(0,0,0),layout)
                            self.libeltext(self.t_actions[numAction][3],8,'Arial', 93, t, QColor(0,0,0), layout)
                            t = t + 5
                        else:
                            self.libeltext(i,8,'Arial',68.5,t,QColor(0,0,0),layout)
                            self.libeltext(self.t_actions[numAction][3], 8, 'Arial', 93, t, QColor(0,0,0), layout)

                            t = t + 5
                        numAction += 1
                h = None
                b = None
                t = None

                for i in cables :
                    if i.split('`')[0] == "NULL":
                        i.split('`')[0] = 0
                    if h is None:
                        h = 1
                    else:
                        h = h + 5
                    if b is None:
                        b = 6
                    else:
                        b = b + 5

                    self.polygon6(b,h,240,250,280,296,layout)

                    if t is None:
                        self.libeltext("Ref",None,None,242,1,QColor(81,137,172),layout)
                        self.libeltext("Info Cable",None,None,257,1,QColor(81,137,172),layout)
                        self.libeltext("Capacité",None,None,281.5,1,QColor(81,137,172),layout)
                        t = 7
                        b = b + 5
                        h = h + 5
                        self.polygon6(b,h,240,250,280,296,layout)
                        self.libeltext(i.split('`')[0],8,'Arial',244,t,QColor(0,0,0),layout)
                        self.libeltext(i.split('`')[1],8,'Arial',251.5,t,QColor(0,0,0),layout)
                        self.libeltext(i.split('`')[2],8,'Arial',286,t,QColor(0,0,0),layout)
                        t = t + 5
                    else:
                        if i.split('`')[0] == "NULL":
                            self.libeltext("0",8,'Arial',244,t,QColor(0,0,0),layout)
                        else:
                            self.libeltext(i.split('`')[0],8,'Arial',244,t,QColor(0,0,0),layout)
                        self.libeltext(i.split('`')[1],8,'Arial',251.5,t,QColor(0,0,0),layout)
                        self.libeltext(i.split('`')[2],8,'Arial',286,t,QColor(0,0,0),layout)
                        t = t + 5



                self.libeltext("SRO "+ sro.replace("SRO-", ""),None,None,20,25,QColor(0,0,0),layout)
                self.libeltext("SECTION N° "+ self.dlg.comboBox.currentText(),None,None,20,32,QColor(0,0,0),layout)
                self.libeltext("CAPACITE "+ cap + " FO",None,None,20,39,QColor(0,0,0),layout)
                self.libeltext("CARTO "+str(int(carto))+" m",None,None,20,46,QColor(0,0,0),layout)

                legend = QgsLayoutItemLegend(layout)
                legend.setTitle('Légende')
                legend.setAutoUpdateModel(False)
                group = legend.model().rootGroup()
                group.clear()
                for i in [bo_temp,pt_temp,co_temp]:
                    group.addLayer(i)
                layout.addItem(legend)
                legend.adjustBoxSize()
                legend.setLegendFilterOutAtlas(True)
                legend.refresh()
                legend.attemptMove(QgsLayoutPoint(1, 13.5, QgsUnitTypes.LayoutCentimeters))
                item.attemptMove(QgsLayoutPoint(1.4, 1.8, QgsUnitTypes.LayoutCentimeters))
                item.attemptResize(QgsLayoutSize(2.8, 2.2, QgsUnitTypes.LayoutCentimeters))
                map.setFrameEnabled(True)
                map2.setFrameEnabled(True)
                legend.setFrameEnabled(True)

                pdf_path = os.path.join(filename.replace(lien[len(lien)-1], ""), lien[len(lien)-1])

                progress.setValue(9)
                exporter = QgsLayoutExporter(layout)
                exporter.exportToPdf(pdf_path, QgsLayoutExporter.PdfExportSettings())
                progress.setValue(10)
                iface.messageBar().clearWidgets()
                iface.messageBar().pushMessage("Succès", "Fichier créer - "+filename, level=Qgis.Success, duration=8)
                pass


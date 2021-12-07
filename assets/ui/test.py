# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainScreen.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 720)
        MainWindow.setMinimumSize(QtCore.QSize(1280, 720))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("#centralwidget{\n"
"background-color:#FFFFFF;\n"
"}\n"
"#leftSlideMenu{\n"
"background-color:#b5b5b5;\n"
"}\n"
"#dashboardButton, #setupButton, #debugButton{\n"
"background-color:transparent;\n"
"border-top-left-radius:15px;\n"
"font-size:16px;\n"
"padding:5px;\n"
"text-align:left;\n"
"}")
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.leftSlideMenu = QtWidgets.QWidget(self.centralwidget)
        self.leftSlideMenu.setMinimumSize(QtCore.QSize(0, 0))
        self.leftSlideMenu.setMaximumSize(QtCore.QSize(200, 16777215))
        self.leftSlideMenu.setStyleSheet("")
        self.leftSlideMenu.setObjectName("leftSlideMenu")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.leftSlideMenu)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.frame = QtWidgets.QFrame(self.leftSlideMenu)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.logoFrame = QtWidgets.QFrame(self.frame)
        self.logoFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.logoFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.logoFrame.setObjectName("logoFrame")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.logoFrame)
        self.horizontalLayout_2.setContentsMargins(10, 10, 10, 50)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.logoFrame)
        self.label_2.setMinimumSize(QtCore.QSize(180, 67))
        self.label_2.setMaximumSize(QtCore.QSize(500, 67))
        font = QtGui.QFont()
        font.setFamily("Candara")
        font.setPointSize(30)
        self.label_2.setFont(font)
        self.label_2.setText("")
        self.label_2.setPixmap(QtGui.QPixmap(":/brand/logos/innopark.png"))
        self.label_2.setScaledContents(True)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2, 0, QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.verticalLayout_3.addWidget(self.logoFrame)
        self.frame_3 = QtWidgets.QFrame(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy)
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.menuOptionsFrame = QtWidgets.QFrame(self.frame_3)
        self.menuOptionsFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.menuOptionsFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.menuOptionsFrame.setObjectName("menuOptionsFrame")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.menuOptionsFrame)
        self.verticalLayout_5.setContentsMargins(5, 0, 0, 0)
        self.verticalLayout_5.setSpacing(10)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.dashboardButton = QtWidgets.QPushButton(self.menuOptionsFrame)
        self.dashboardButton.setStyleSheet("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/black/icons/home.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.dashboardButton.setIcon(icon)
        self.dashboardButton.setObjectName("dashboardButton")
        self.verticalLayout_5.addWidget(self.dashboardButton)
        self.setupButton = QtWidgets.QPushButton(self.menuOptionsFrame)
        self.setupButton.setStyleSheet("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/black/icons/sliders.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setupButton.setIcon(icon1)
        self.setupButton.setObjectName("setupButton")
        self.verticalLayout_5.addWidget(self.setupButton)
        self.violationReviewButton = QtWidgets.QPushButton(self.menuOptionsFrame)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.violationReviewButton.setFont(font)
        self.violationReviewButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.violationReviewButton.setAutoFillBackground(False)
        self.violationReviewButton.setStyleSheet("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/black/icons/rotate-cw.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.violationReviewButton.setIcon(icon2)
        self.violationReviewButton.setObjectName("violationReviewButton")
        self.verticalLayout_5.addWidget(self.violationReviewButton)
        self.debugButton = QtWidgets.QPushButton(self.menuOptionsFrame)
        self.debugButton.setStyleSheet("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/black/icons/info.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.debugButton.setIcon(icon3)
        self.debugButton.setObjectName("debugButton")
        self.verticalLayout_5.addWidget(self.debugButton)
        self.verticalLayout_6.addWidget(self.menuOptionsFrame, 0, QtCore.Qt.AlignTop)
        self.verticalLayout_3.addWidget(self.frame_3)
        self.verticalLayout_2.addWidget(self.frame)
        self.horizontalLayout.addWidget(self.leftSlideMenu)
        self.screen = QtWidgets.QWidget(self.centralwidget)
        self.screen.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.screen.sizePolicy().hasHeightForWidth())
        self.screen.setSizePolicy(sizePolicy)
        self.screen.setMinimumSize(QtCore.QSize(500, 0))
        self.screen.setStyleSheet("#screen{\n"
"background-color:#FFFFFF;\n"
"}")
        self.screen.setObjectName("screen")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.screen)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(0, 5, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.top_bar = QtWidgets.QHBoxLayout()
        self.top_bar.setObjectName("top_bar")
        self.menuButton = QtWidgets.QPushButton(self.screen)
        self.menuButton.setStyleSheet("#menuButton{\n"
"background-color:transparent;\n"
"border:0px\n"
"}")
        self.menuButton.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/black/icons/menu.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.menuButton.setIcon(icon4)
        self.menuButton.setIconSize(QtCore.QSize(32, 32))
        self.menuButton.setObjectName("menuButton")
        self.top_bar.addWidget(self.menuButton)
        self.screenPageLabel = QtWidgets.QLabel(self.screen)
        font = QtGui.QFont()
        font.setFamily("Candara")
        font.setPointSize(16)
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(75)
        font.setStrikeOut(False)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.screenPageLabel.setFont(font)
        self.screenPageLabel.setObjectName("screenPageLabel")
        self.top_bar.addWidget(self.screenPageLabel)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.top_bar.addItem(spacerItem)
        self.verticalLayout.addLayout(self.top_bar)
        self.screenStackedWidget = QtWidgets.QStackedWidget(self.screen)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.screenStackedWidget.sizePolicy().hasHeightForWidth())
        self.screenStackedWidget.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setStrikeOut(False)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.screenStackedWidget.setFont(font)
        self.screenStackedWidget.setObjectName("screenStackedWidget")
        self.dashboardPage = QtWidgets.QWidget()
        self.dashboardPage.setObjectName("dashboardPage")
        self.startSystemButton = QtWidgets.QPushButton(self.dashboardPage)
        self.startSystemButton.setGeometry(QtCore.QRect(520, 0, 71, 61))
        font = QtGui.QFont()
        font.setPointSize(50)
        self.startSystemButton.setFont(font)
        self.startSystemButton.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/black/icons/power.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.startSystemButton.setIcon(icon5)
        self.startSystemButton.setIconSize(QtCore.QSize(32, 32))
        self.startSystemButton.setObjectName("startSystemButton")
        self.screenStackedWidget.addWidget(self.dashboardPage)
        self.setupPage = QtWidgets.QWidget()
        self.setupPage.setObjectName("setupPage")
        self.screenStackedWidget.addWidget(self.setupPage)
        self.debugPage = QtWidgets.QWidget()
        self.debugPage.setObjectName("debugPage")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.debugPage)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.frame_2 = QtWidgets.QFrame(self.debugPage)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout_7.setContentsMargins(9, 14, 0, 0)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.label = QtWidgets.QLabel(self.frame_2)
        font = QtGui.QFont()
        font.setPointSize(21)
        font.setUnderline(False)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout_7.addWidget(self.label)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(10, 16, -1, -1)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.debugOtCb = QtWidgets.QCheckBox(self.frame_2)
        self.debugOtCb.setObjectName("debugOtCb")
        self.horizontalLayout_3.addWidget(self.debugOtCb)
        self.debugPtmCb = QtWidgets.QCheckBox(self.frame_2)
        self.debugPtmCb.setObjectName("debugPtmCb")
        self.horizontalLayout_3.addWidget(self.debugPtmCb)
        self.checkBox = QtWidgets.QCheckBox(self.frame_2)
        self.checkBox.setObjectName("checkBox")
        self.horizontalLayout_3.addWidget(self.checkBox)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.verticalLayout_7.addLayout(self.horizontalLayout_3)
        self.debugFrames = QtWidgets.QHBoxLayout()
        self.debugFrames.setObjectName("debugFrames")
        self.verticalLayout_7.addLayout(self.debugFrames)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_7.addItem(spacerItem2)
        self.verticalLayout_4.addWidget(self.frame_2)
        self.screenStackedWidget.addWidget(self.debugPage)
        self.violationReviewPage = QtWidgets.QWidget()
        self.violationReviewPage.setObjectName("violationReviewPage")
        self.frame_4 = QtWidgets.QFrame(self.violationReviewPage)
        self.frame_4.setGeometry(QtCore.QRect(0, 0, 1081, 671))
        self.frame_4.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_4.setObjectName("frame_4")
        self.screenStackedWidget.addWidget(self.violationReviewPage)
        self.verticalLayout.addWidget(self.screenStackedWidget)
        self.horizontalLayout.addWidget(self.screen)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Innopark Desktop"))
        self.dashboardButton.setText(_translate("MainWindow", "Dashboard"))
        self.setupButton.setText(_translate("MainWindow", "Setup"))
        self.violationReviewButton.setText(_translate("MainWindow", "Violation Review"))
        self.debugButton.setText(_translate("MainWindow", "Debug"))
        self.screenPageLabel.setText(_translate("MainWindow", "Dashboard"))
        self.label.setText(_translate("MainWindow", "Options:"))
        self.debugOtCb.setText(_translate("MainWindow", "Object Tracking"))
        self.debugPtmCb.setText(_translate("MainWindow", "Parking Tariff Management"))
        self.checkBox.setText(_translate("MainWindow", "Parking Violation Management"))
import icons_rc
import logos_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
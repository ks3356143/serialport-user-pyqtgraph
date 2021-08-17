from PyQt5 import QtCore,QtWidgets,QtGui
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import random
import sys
'''
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.login_widget = LoginWidget(self)
        self.login_widget.button.clicked.connect(self.plotter)
        self.central_widget.addWidget(self.login_widget)

        self.curve = self.login_widget.it1
        self.curve2 =self.login_widget.it2

    def plotter(self):
        self.data =[0]
        self.data2 = [0]
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updater)
        self.timer.start(0)

    def updater(self):
        self.data.append(self.data[-1]+10*(0.5-random.random())) 
        self.curve.setData(self.data, pen=pg.mkPen('b', width=1))
        self.data2.append(self.data2[-1]+0.1*(0.5-random.random()))
        self.curve2.setData(self.data2, pen=pg.mkPen('r', width=1))

class LoginWidget(QWidget):
    def __init__(self, parent=None):
        super(LoginWidget, self).__init__(parent)
        layout = QVBoxLayout()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.button = QPushButton('Start Plotting')
        layout.addWidget(self.button)
        self.plot = pg.PlotWidget(title='Force and Extension vs. Time')
        layout.addWidget(self.plot)
        self.setLayout(layout)

        p1 = self.plot.plotItem
        p2 = pg.ViewBox()
        p1.showAxis('right')
        p1.scene().addItem(p2)
        p1.getAxis('right').linkToView(p2)
        p2.setXLink(p1)

        self.plot.getAxis('bottom').setLabel('Time', units='s')
        self.plot.getAxis('left').setLabel('Force', units='lbf', color="#0000ff")
        p1.getAxis('right').setLabel('Extension', units='in.', color="#ff0000")

        def updateViews():
            p2.setGeometry(p1.vb.sceneBoundingRect())
            p2.linkedViewChanged(p1.vb, p2.XAxis)

        updateViews()
        p1.vb.sigResized.connect(updateViews)

        self.it1 = p1.plot()
        self.it2 = pg.PlotCurveItem()
        p2.addItem(self.it2)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
'''
# for i in range(3):
#     locals()['p'+str(i)]=i
#     print ('p'+ str(i))
# print(p0)
# print(p1)
# print(p2)

#12个复选框
# class body():

#     self.createVar = locals(); 为了生成多个变量
#     for i in range(12):
#         k='p' + str(i);
#         self.createVar[k]=QCheckBox('节点'+str(i+1), self);
#         self.createVar[k].stateChanged.connect(self.stateClicked)
#         self.QHBox_whole.addWidget(self.createVar[k]);
# i = 0
# print('p'+str(i))
for i in range(4):
    locals()['list'+str(i)] = [0] #定义用户选择数量的数组
print(list0)

# -*- coding: utf-8 -*-
import sys
import os
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtGui import QColor
from chuankou import Ui_MainWindow
from queue import Queue
import pyqtgraph as pg
import numpy as np
from numpy import array
import time
from tool import Tool
from PyQt5.QtCore import pyqtSignal,QTimer
from PyQt5.QtWidgets import *
import threading
from serial.serialutil import *
import utils
import help
import pyqtgraph as pg
import random
import json
import csv
import binascii
from typing import List
import axisCtrlTemplate_pyqt5

class MyWidget(QtWidgets.QWidget,help.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

class MyMainWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    #自定义信号和槽来显示接收数据
    signal_recv_data = pyqtSignal(str)
    save_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        #实例化帮助窗口
        self.w_help = MyWidget() #然后调用show方法就可以显示了,注意现在w_help已经是主界面的子类了可以直接调用
         
        #实例化信号接收变量初始化dict
        self.recived_dict = {} #实例化接收信号函数带来的东西
        #~~~~~~~~~主线程全局变量~~~~~~~~~（1）
        self.is_uart_start = 0  #定义标志位检测串口是否启动
        self.show_mode = 0 #0为ASCII形式，1为Hex形式
        self.enable_auto_line = 0 #0代表不自动换行，1代表自动换行
        self.enable_show_time = 0 #0代表不显示，1代表显示
        self.enable_recv_file = 0 #0代表不保存，1代表保存
        self.send_mode = 0 #0为默认ASCII形式发送，1为Hex形式发送
        self.enable_repeat_send = 0 #0代表不重复发送，1代表重复发送
        self.enable_recv_pause = 0 #0代表不停止接收，1代表停止接收
        self.user_para_addr = ["0c060f80","0c06119c","0c061168","0c0611d0"]
        #self.user_para_addr = [] #初始化用户选择的数据变量地址信息'0c67AE6A'4字节列表
        self.user_para_dict = {} #初始化用户选择的数据变量地址信息以及其变量名
        self.user_send_length = 4
        #self.user_send_length = 0 #~~~~~~~~~~~~~~~~

        self.user_send_message = '' #用int数组展示

        self.table1.setColumnCount(2)#信息列数固定为2
        self.table1.setHorizontalHeaderLabels(["变量名","数值"])
        #最后一列自动拉伸
        self.table1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        QHeaderView.Stretch #自适应宽度


        #加载初始化文件,这里也有全局变量~~~~前全局类变量
        self.uart_para_dict = {"port":"COM1","baud":115200, "databits":EIGHTBITS, "stopbits":STOPBITS_ONE, "parity":PARITY_NONE, "flow_rts":False, "flow_xon":False}

        self.settings = QtCore.QSettings("config.ini", QtCore.QSettings.IniFormat)
        self.settings.setIniCodec("UTF-8")
        self.uart_para_dict["baud"] = self.settings.value("SETUP/UART_BAUD", 0, type=int)
        print("波特率(int) is %d" % self.uart_para_dict["baud"])
        self.uart_para_dict["databits"] = self.settings.value("SETUP/UART_DATABIT", 0, type=int)
        print("数据位(int) is %d" % self.uart_para_dict["databits"])
        self.uart_para_dict["stopbits"] = self.settings.value("SETUP/UART_STOPBIT", 0, type=float)
        print("停止位(int) is %d" % self.uart_para_dict["stopbits"])
        parity_value = self.settings.value("SETUP/UART_PARITY")
        if ("无" == parity_value):
            self.uart_para_dict["parity"] = PARITY_NONE
        elif ("偶校验" == parity_value):
            self.uart_para_dict["parity"] = PARITY_EVEN
        elif ("奇校验" == parity_value):
            self.uart_para_dict["parity"] = PARITY_ODD
        elif ("置1" == parity_value):
            self.uart_para_dict["parity"] = PARITY_MARK
        elif ("置0" == parity_value):
            self.uart_para_dict["parity"] = PARITY_SPACE
        print("uart parity(int) is %s" % self.uart_para_dict["parity"])

        flow_value = self.settings.value("SETUP/UART_FLOW")
        if ("RTS/CTS" == flow_value):
            self.uart_para_dict["flow_rts"] = True
            self.uart_para_dict['flow_xon'] = False
        elif ("XON/XOFF" == flow_value):
            self.uart_para_dict["flow_rts"] = False
            self.uart_para_dict['flow_xon'] = True
        elif ("无" == flow_value):
            self.uart_para_dict["flow_rts"] = False
            self.uart_para_dict['flow_xon'] = False

        print("uart flow is %s" % flow_value)
        #~~~~~~~~~初始化主界面定时器或者线程~~~~~~~~
        self.timer_repeat = QTimer(self)
        self.timer_repeat.timeout.connect(self.timer_repeat_cb)

        #~~~~~~~~~绑定信号与槽~~~~~~~~~~
        self.comboBox_com_select.currentTextChanged.connect(self.comboBox_com_select_uart_cb) #当COM口改变时
        self.comboBox_com_select_3.currentTextChanged.connect(self.comboBox_com_select_databits_cb) #当数据位改变时候
        self.comboBox_com_select_5.currentTextChanged.connect(self.comboBox_com_select_stopbit_cb) #当停止位改变时候
        self.comboBox_com_select_2.currentIndexChanged.connect(self.comboBox_baud_cb) #当波特率改变进行回调
        self.comboBox_com_select_4.currentIndexChanged.connect(self.comboBox_polarity_cb) #当用户选择校验位改变时
        self.comboBox_com_select_6.currentIndexChanged.connect(self.comboBox_flow_cb) #当用户选择其他流控
        
        self.btn_send.clicked.connect(self.btn_send_cb) #点击发送按钮链接
        self.action_Start.triggered.connect(self.action_start_cb) #这4个action连接
        self.action_pause.triggered.connect(self.action_pause_cb)
        self.action_stop.triggered.connect(self.action_stop_cb)
        self.action_clean.triggered.connect(self.action_clean_cb)
        self.action_about.triggered.connect(self.action_about_cb) #点击关于按钮
        self.action_huitu.triggered.connect(self.action_huitu_cb) #点击实时监控按钮

        self.radioButton_recive_select.toggled.connect(self.radioButton_recive_select_cb) #当选择ascii接收时候
        self.radioButton_recive_select_2.toggled.connect(self.radioButton_recive_select_cb_2) #当选择hex接收
        self.radioButton.toggled.connect(self.radioButton_send_select_cb_3) #当选择ascii发送
        self.radioButton_2.toggled.connect(self.radioButton_send_select_cb_4) #当选择hex发送
        self.checkBox_recive_select.toggled.connect(self.checkbox_auto_line_cb) #当选择自动换行
        self.checkBox_recive_select_2.toggled.connect(self.checkbox_display_cb) #选择了接收数据到文件
        self.checkBox_recive_select_3.toggled.connect(self.checkbox_displaytime_cb) #当选择显示时间
        self.checkBox_send_select.toggled.connect(self.checkbox_repeat_send_cb) #当选择重复发送
        self.spinBox_send_select.valueChanged.connect(self.dingshi_changed_cb) #当定时发送改变时候,这个value设置为全局变量

        self.pushButton_del.clicked.connect(self.list_remove_item) #点击按钮删除选中项
        self.pushButton_cle.clicked.connect(self.list_clear_cb) #点击清空列表
        self.pushButton_map.clicked.connect(self.mapparser_cb) #点击选中文件，得到文件路径存到全类变量self.map_file_name
        self.pushButton_bin.clicked.connect(self.bin_file_cb) #点击选中文件获得全类变量绝对路径self.map_file_name
        self.pushButton_send_bin.clicked.connect(self.send_bin_cb) #点击发送bin文件
        self.pushButton_create.clicked.connect(self.map_create_cb) #点击生成参数列表
        self.pushButton_order.clicked.connect(self.create_order) #生成获取参数的指令
        self.pushButton_raise.clicked.connect(self.create_order_send) #发送生产的指令
        self.pushButton.clicked.connect(self.save_file) #点击开启保存数据 
        self.pushButton_2.clicked.connect(self.closethread) #点击关闭绘图线程
        self.pushButton_3.clicked.connect(self.begin_huoqu) #点击开启绘图线程
        self.pushButton_4.clicked.connect(self.create_huaban) #点击创建画板
        #~~~~~~~~自定义的信号与槽~~~~~~~~~
        self.signal_recv_data.connect(self.textBrowser_show_data_cb) #第一个自定义信号连接

        #检测串口,这个是线程函数,用来一直看串口更新（线程连接函数）
        def check_valid_uart():
            ports_value = []
            ports_list = serial.tools.list_ports.comports()
            for i in range(len(ports_list)):
                ports_value.append(ports_list[i][0])
            #print("串口值有 ", ports_value)

            if (0 == len(ports_value)):
                print("无法找到串口")
                self.comboBox_com_select.clear()
                self.comboBox_com_select.setCurrentIndex(-1)
            else:
                for i in range(len(ports_value)):
                    index = self.comboBox_com_select.findText(ports_value[i], QtCore.Qt.MatchFixedString)
                    if (index < 0):
                        self.comboBox_com_select.addItem(ports_value[i])
                    # else:
                    #     print("curent port is ", self.comboBox_uart.currentText())
            # get current port
            self.uart_para_dict["port"] = self.comboBox_com_select.currentText()

        #开启监听线程
        def gui_status_thread():
            print("开启监听线程")
            while True:
                check_valid_uart()
                time.sleep(2)

        #上面2个函数由下面这个驱动
        th2 = threading.Thread(target=gui_status_thread,daemon=True)
        th2.start()

        #~~~~~~~~~主界面初始化~~~~~~~~~~
        self.statusbar.showMessage("欢迎进入串口工具")  #进入主界面显示statusbar
        self.radioButton_recive_select.setChecked(True) #这4个为hex和ascii接收发送初始化
        self.radioButton_recive_select_2.setChecked(False)
        self.radioButton.setChecked(True)
        self.radioButton_2.setChecked(False)
        self.spinBox_send_select.setRange(100,30000) #设置时间范围，定时发送
        self.spinBox_send_select.setValue(1000) #设置默认1s
        self.spinBox_send_select.setSingleStep(100) #设置部署为100ms
        self.spinBox_send_select.setWrapping(True) #设置减到最小循环或增到最大变为最小
        self.comboBox_com_select_2.setCurrentText(str(self.uart_para_dict["baud"])) #通过配置文件设置的波特率值
        self.comboBox_com_select_3.setCurrentText(str(self.uart_para_dict["databits"])) #通过配置文件设置的波特率值
        self.comboBox_com_select_5.setCurrentText(str(self.uart_para_dict["stopbits"])) #通过配置文件设置的波特率值
        self.comboBox_com_select_4.setCurrentText(parity_value)
        self.comboBox_com_select_6.setCurrentText(flow_value)
        #~~~~~~~~~主线程全局变量~~~~~~~~~（2）
        self.dingshivalue = self.spinBox_send_select.value()
        #新建action，获取QStyleFactory的style
        for style in QtWidgets.QStyleFactory.keys():
            print(style)
            action = QtWidgets.QAction(self,text=style)
            action.triggered.connect(self.actionstyle_show)
            self.menu_show.addAction(action)
            action.setData(style) #把每个action绑定一个数据！！

    def actionstyle_show(self):
        name = self.sender() #当我们点击action，就获取到setData（data）中data数据
        style = QtWidgets.QStyleFactory.create(name.data()) #self.sender获取 action.setData传过来的数据
        QtWidgets.QApplication.setStyle(style)
        
    #~~~~~~~~~~~~被信号连接的函数~~~~~~~~~~
    def comboBox_com_select_uart_cb(self): #设置COM号,区别于其他设置这是端口检测->用户选择->录入dict
        content = self.comboBox_com_select.currentText()
        text = "串口选择为%s" % content
        print(text)
        self.config_uart_port = content
        
    def comboBox_baud_cb(self): #设置波特率，用户设置
        content = self.comboBox_com_select_2.currentText()
        text = "波特率选择为%s" % content
        print(text)
        self.uart_para_dict['baud'] = int(content)
        self.settings.setValue("SETUP/UART_BAUD",self.uart_para_dict["baud"])

    def comboBox_com_select_databits_cb(self): #设置数据位
        content = self.comboBox_com_select_3.currentText()
        text = "数据位选择为%s" % content
        print(text)
        self.uart_para_dict["databits"] = int(content)
        self.settings.setValue("SETUP/UART_DATABIT",self.uart_para_dict["databits"])

    def comboBox_com_select_stopbit_cb(self): #设置停止位
        content = self.comboBox_com_select_5.currentText()
        text = "停止位选择为%s" % content
        print(text)
        self.uart_para_dict["stopbits"] = int(content) #注意停止位转换为int
        self.settings.setValue("SETUP/UART_STOPBIT",self.uart_para_dict["stopbits"])

    def comboBox_polarity_cb(self): #当用户设置校验位，先获取选择的值，然后放入ini文件，如果串口已启动，直接设置川酷
        val = self.comboBox_com_select_4.currentText()
        if ("无" == val):
            print("无校验")
        elif ("奇校验" == val):
            self.uart_para_dict["parity"] = PARITY_ODD
        elif ("偶校验" == val):
            self.uart_para_dict["parity"] = PARITY_EVEN
        elif ("置1" == val):
            self.uart_para_dict["parity"] = PARITY_MARK
        elif ("置0" == val):
            self.uart_para_dict["parity"] = PARITY_SPACE
        self.settings.setValue("SETUP/UART_PARITY", val)
        if (1 == self.is_uart_start):
            self.tool.uart.ser.parity = self.uart_para_dict["parity"]
    
    def comboBox_flow_cb(self): #当选择流控
        val = self.comboBox_com_select_6.currentText()
        if ("RTS/CTS" == val):
            self.uart_para_dict["flow_rts"] = True
            self.uart_para_dict['flow_xon'] = False
        elif ("XON/XOFF" == val):
            self.uart_para_dict["flow_rts"] = False
            self.uart_para_dict['flow_xon'] = True
        elif ("无" == val):
            self.uart_para_dict["flow_rts"] = False
            self.uart_para_dict['flow_xon'] = False
        self.settings.setValue("SETUP/UART_FLOW", val)
        if (1 == self.is_uart_start):
            self.tool.uart.ser.xonxoff = self.uart_para_dict["flow_xon"]
            self.tool.uart.ser.rtscts = self.uart_para_dict["flow_rts"]

    def btn_send_cb(self):  #当发送按钮被点击,用户点击进入该函数,然后函数调用中间层,找到底层
        print('用户点击了发送按钮')
        if(1 == self.is_uart_start): #模式是ascii码，直接发送，如果是hex转换后发送
            if self.send_mode == 0: #ascii码
                send_data = self.textEdit_send_display.toPlainText() #默认是ascii码的方式
            else:
                list_data = []
                data = self.textEdit_send_display.toPlainText()
                for i in range(0,len(data),3):
                    temp = data[i:i+2]
                    list_data.append(chr(int(temp, 16)))
                send_data = ''.join(list_data)
            self.tool.uart.send_uart_data(send_data)

        else:
            QtWidgets.QMessageBox.information(self,"串口未打开","请先打开串口，才能发送数据")
            print('点击了发送按钮，但是串口未打开')

    def action_start_cb(self): #action开始连接后
        print('点击了开始!!!')
        if not self.comboBox_com_select.currentText():
            QMessageBox.critical(self,"没有选择串口","请选择串口后再点击打开")
            #实例化Tool（实例化中间逻辑层，这里实例化就要实例化Uart，Uart初始化就要打开）
        else:
            self.tool = Tool(self)  #注意这里把主界面当作父类传给了self.tool
            self.is_uart_start = 1 #标志位变为1
            self.statusbar.showMessage("串口已打开")
            self.statusbar.setStyleSheet("color:green;")
            if not os.path.exists('./data'):
                os.mkdir('./data')
            if not os.path.exists('./data/datafile'):
                os.mkdir('./data/datafile')
            try:
                self.csv_file_1 = open('./data/datafile/datas.csv','a+',newline='')
                self.writer_1 = csv.writer(self.csv_file_1)
            except Exception as e:
                QMessageBox.warning(self,"打开文件错误","打开文件错误，请检查")
        

    def action_pause_cb(self): #action暂停连接后~~后续完善
        print('点击了暂停!!!')
        if self.enable_recv_pause == 0:
            self.enable_recv_pause = 1
            self.statusbar.showMessage("串口已关闭")
            self.statusbar.setStyleSheet("color:red;")
        else:
            self.enable_recv_pause = 0
            self.statusbar.showMessage("串口已打开")
            self.statusbar.setStyleSheet("color:green;")

    def action_stop_cb(self): #action停止连接后
        print('点击了停止!!!')
        #先关闭当前串口，把数据处理对象删除掉
        if self.is_uart_start == 1:
            self.is_uart_start = 0
            self.recived_sure = 0
            self.tool.uart.uart_close() #调用最下层关闭串口
            del self.tool #删除tool对象
            self.statusbar.showMessage("串口已关闭")
            self.statusbar.setStyleSheet("color:red;")
            try:
                self.csv_file_1.close()
            except:
                print("没有打开csv文件，所以没法关闭")
            finally:
                pass
            
    def action_clean_cb(self): #action清除连接后
        print('点击了清除!!!')
        self.textBrowser_recive_display.clear()

    def radioButton_recive_select_cb(self): #当选择ascii接收
        if self.radioButton_recive_select.isChecked():
            print('选择了ascii接收')
            if self.show_mode == 1:
                self.show_mode = 0
                #data数据 FF FF FF FF FF FF FF FF FF FF FF
                list_data = []
                data = self.textBrowser_recive_display.toPlainText()
                for i in range(0,len(data),3):
                    temp = data[i:i+2]
                    list_data.append(chr(int(temp, 16))) 
                res = ''.join(list_data)
                self.textBrowser_recive_display.setText(res)
        

    def radioButton_recive_select_cb_2(self): #当选择hex接收
        if self.radioButton_recive_select_2.isChecked():
            print('选择了Hex接收')
            if self.show_mode == 0:
                self.show_mode = 1
                data = self.textBrowser_recive_display.toPlainText()
                hexstring = self.hextostring(data)
                self.textBrowser_recive_display.setText(hexstring)

    def radioButton_send_select_cb_3(self): #当选择ascii发送
        if self.radioButton.isChecked():
            print('选择了ascii发送')
            if self.send_mode == 1:
                self.send_mode = 0
                #data数据 FF FF FF FF FF FF FF FF FF FF FF
                list_data = []
                data = self.textEdit_send_display.toPlainText()
                for i in range(0,len(data),3):
                    temp = data[i:i+2]
                    list_data.append(chr(int(temp, 16)))
                res = ''.join(list_data)
                self.textEdit_send_display.setText(res)

    def radioButton_send_select_cb_4(self): #当选择hex发送
        if self.radioButton_2.isChecked():
            print('选择了Hex发送')
            if self.send_mode == 0:
                self.send_mode = 1
                data = self.textEdit_send_display.toPlainText()
                hexstring2 = self.hextostring(data)
                self.textEdit_send_display.setText(hexstring2)

    def checkbox_auto_line_cb(self): #当选择自动换行checkbox~~当取消选择，同时获取checkbox状态
        print("用户选择勾选了自动换行")
        res_auto_line = self.checkBox_recive_select.isChecked()
        print("接收结果自动换行是 %d" % res_auto_line)
        self.enable_auto_line = res_auto_line


    def checkbox_display_cb(self): #当选择文件储存checkbox
        res = self.checkBox_recive_select_2.isChecked()
        print('选择了接收数据到文件储存',res)
        # if True == res:
        #     self.enable_show_time = 1
        # else:
        #     self.enable_show_time = 0
        #如果当前目录没有debug文件夹，新创建一个
        if res == True:
            self.enable_recv_file = 1
            path = os.getcwd() #获取当前工作目录
            list_files = os.listdir(path) #获取文件列表
            if "debug" not in list_files:
                os.system("mkdir debug") #os.system相当于CMD
            file_name = "debug/RecvToFile-" + utils.get_current_name() + ".txt"
            self.file = open(file_name, "w+")
            QtWidgets.QMessageBox.information(self,"文件输出名称",file_name)
        else:
            if (1 == self.enable_recv_file):
                self.enable_recv_file = 0
                self.file.close()
            

    def checkbox_displaytime_cb(self): #当选择显示时间checkbox
        res = self.checkBox_recive_select_3.isChecked()
        print('选择了显示时间',res)
        if True == res:
            self.enable_show_time = 1
        else:
            self.enable_show_time = 0
        

    def checkbox_repeat_send_cb(self): #当选择重复发送时
        res = self.checkBox_send_select.isChecked()
        if True == res:
            #启动PYQT定时器，定时器的函数中访问spinBox中设置的发送时间，然后调用发送函数
            self.enable_repeat_send = 1
            if self.spinBox_send_select.value() <= 0:
                QtWidgets.QMessageBox.warning(self,"警告","设置时间必须大于0！")
            else:
                self.timer_repeat.start(self.spinBox_send_select.value())
        else:
            #关闭定时发送的定时器
            print('取消选择了重复发送，关闭定时器')
            self.timer_repeat.stop()
            self.enable_repeat_send = 0

    def dingshi_changed_cb(self,value): 
        print('现在定时发送的时间 %d'% value)
        self.dingshivalue = value
        print('现在定时发送时间全局变量为%d' %self.dingshivalue)

    def action_about_cb(self): #点击关于按钮
        self.w_help.show()

    def action_huitu_cb(self): #点击绘图按钮
        self.w_chart.show()

    def mapparser_cb(self):
        self.map_file_name = QFileDialog.getOpenFileName(self,"打开map文件",'C:\\',"Map files(*.map)")
        print(self.map_file_name) #返回了文件绝对路径file_name[0]为绝对路径，即C:\XXXX\XXX\XXX.map
        self.mapConfig,self.mapDict = self.mapToJson(self.map_file_name[0])
        print(self.mapConfig,self.mapDict)

    def map_create_cb(self):   #呈现到leftwidget
        my_dict = self.mapDict
        for value in my_dict.values():
            item = QListWidgetItem()
            item.setText(value)
            curRow = self.leftWidget.currentRow() #当前行，目前没有用
            self.leftWidget.addItem(item)

    def create_order(self):
        QMessageBox.warning(self,"每次生成指令","都要清空user_para_dict以及self_para_addr但全局变量生成的指令不会清空")
        if self.listWidget.count() >= 1:
            para_list = []
            for i in range(self.listWidget.count()):
                aItem = self.listWidget.item(i)
                print(aItem.text()) #打印了AVMBlob_initAVMInterval_emptyinit
                para_list.append(aItem.text())
            #para_list为['AVMInterval_emptyinit', 'AVMInterval_assign']用户选择的参数字符串
            #现在要去找对应的地址
            self.user_para_dict = {}
            self.user_para_addr = []

            for i in para_list:
                addr = list(self.mapDict.keys())[list(self.mapDict.values()).index(i)]
                #现在找到了用户选择的参数的地址,也就是dict中的key，现在要把地址组装
                self.user_para_addr.append(addr)
                self.user_para_dict[addr] = i
            print('用户选择的地址列表为：',self.user_para_addr)
            print('用户选择的参数dict为：',self.user_para_dict)
            #然后把指令显示['0c061108', '0c068498'],帧头（2字节）+有效长度（1字节）+命令字（1字节）+地址1（4字节）+长度（1字节）
            #+地址2（4字节）+长度（1）字节,长度是固定'04'【传输显示04】
            frame_tou = 'E116' # 帧头固定的，那么有小长度占1字节，组装（'E116220c06110800010c068498'）
            frame_type = '22' # 固定的命令字
            frame_sigle_lang = '01' #固定每个参数宽度,不一定是4~~~~~~@@,给DSP的地址长度
            frame_datas = ''  #变量位加上它自己的sigle长度位
            for i in range(len(self.user_para_addr)):
                one_datazhen = self.user_para_addr[i] + frame_sigle_lang #注意这里固定了一个参数带的数据的字节数为1@@@@
                frame_datas = frame_datas + one_datazhen  #这里5个字节了@@@@@
            print('数据位+自己的single长度字符显示',frame_datas)
            temp1 = str(hex(len(self.user_para_addr) * 5)) #用户选择n个变量，那么长度位就是5*n,@@#temp=有效长度位
            print(temp1)
            #我要把0xa转换为'0A'
            if len(self.user_para_addr) * 5 < 16:
                frame_changdu = '0'+ temp1.replace('0x','')
            else:
                frame_changdu = temp1.replace('0x','')
            print('长度位大小字符显示：',frame_changdu) #打印长度位情况
            print('长度位大小int显示：',int(frame_changdu,16))
            #下面是除开校验位checksum以外的str表达的帧
            frame_exceptchecksum = frame_tou + frame_changdu + frame_type + frame_datas
            print(frame_exceptchecksum) #OK现在除开校验位正确了
            
            #下面就是生产校验位了
            if frame_exceptchecksum:
                checksum = 0
                for i,j in zip(frame_exceptchecksum[8::2],frame_exceptchecksum[9::2]):
                    checksum += int('0x' + (i + j),16)
                print('发送的校验和未取第2字节:',checksum)
                check_num = ('{:04x}'.format(checksum & 0xFFFF)).upper() #【更变！】~~~~~
                send_code = frame_exceptchecksum + ('00'*(240-len(self.user_para_addr)*5-2-1-1-2)) +check_num
                self.lineEdit_2.setText(send_code)
                self.lineEdit_2.setReadOnly(True)
                #生产指令完毕
            else:
                QMessageBox.warning(self,"无法生产指令","程序没有收到选择参数")
        else:
            QMessageBox.warning(self,"请选择参数","请选择想要获取的参数")

    #校验和，输入一个十六进制str(比如PyQt界面上用户输入的十六进制字符串无空格)，输出为校验和十六进制str
    #使用了int.from_byte(str)

    def create_order_send(self):
        if self.is_uart_start == 1:
            if self.lineEdit_2.text():
                print("发送的指令为：",self.lineEdit_2.text()) #调试打印的指令
                sendddd = self.lineEdit_2.text().upper()
                self.tool.uart.send_uart_data(sendddd)
                print(sendddd)
                self.user_send_message = sendddd
                self.user_send_length = len(self.user_para_addr)
            else:
                QMessageBox.warning(self,"暂未生产指令！","请先生产指令")
        else:
            QMessageBox.warning(self,"请先打开串口","请先打开串口")
        self.table1.setRowCount(5)
        
    #上面函数调用的dict找key函数,其他地方有用再写
    def valueTokey(self,dict_values):
        pass


    def bin_file_cb(self):
        self.bin_file_name = QFileDialog.getOpenFileName(self,"打开bin文件",'C:\\',"Bin files(*.*)")
        print(self.bin_file_name) #返回了文件绝对路径file_name[0]为绝对路径
        self.lineEdit.setText(str(self.bin_file_name[0]))

    def send_bin_cb(self): #点击发送按钮发送bin二进制文件
        if self.is_uart_start == 1:
            if self.bin_file_name[0]:
                ZT1 = 0xEB
                ZT2 = 0x90
                MLZ = 0x44
                #先发送重构bin文件指令，先获取bin文件字节长度，
                self.file_bin = open(self.bin_file_name[0],"rb")
                bin_length = len(self.file_bin.read())
                print("发送bin文件长度位：",bin_length)

                index = 0
                for i in range(240):
                    c = self.file_bin.read(1)
                    print("C的值为：",c)
                    #将字节转16进制字符
                    ssss = str(binascii.b2a_hex(c))[2:-1]
                    print("16进制字符转为",ssss)
                    print("@@@@@@@@@",bytes().fromhex(ssss))
                    #write(bytes().fromhex(ssss))
                    break





                print("发送bin文件长度",index)
                print('正在发送bin文件')
                self.tool.uart.send_bin_data(send_data)
                QMessageBox.information(self,"发送状态","发送完成")
        else:
            QtWidgets.QMessageBox.warning(self,"串口通信",'串口未打开')
        pass
    
    def closethread(self): #点击关闭绘图线程
        self.thread1.terminate()
            

    #~~~~~~~~~~~~定时器连接函数~~~~~~~~~~~~
    def timer_repeat_cb(self):
        print("重复发送定时器启动")
        if(1 == self.is_uart_start): #模式是ascii码，直接发送，如果是hex转换后发送
            if self.send_mode == 0: #ascii码
                send_data = self.textEdit_send_display.toPlainText() #默认是ascii码的方式
            else:
                list_data = []
                data = self.textEdit_send_display.toPlainText()
                for i in range(0,len(data),3):
                    temp = data[i:i+2]
                    list_data.append(chr(int(temp, 16)))
                send_data = ''.join(list_data)
            self.tool.uart.send_uart_data(send_data)
        else:
            self.checkBox_send_select.setChecked(False)
            self.timer_repeat.stop()
            self.enable_repeat_send = 0
            QtWidgets.QMessageBox.information(self,"串口未打开","请先打开串口，才能发送数据")
            print('重复发送打开，但是串口未打开')
    
    def list_remove_item(self):
        row = self.listWidget.currentRow()
        self.listWidget.takeItem(row)
    
    def list_clear_cb(self):
        self.listWidget.clear()

    #~~~~~~~~~~~~非被信号连接的函数，是函数连接的函数~~~~~~~~~~
    def mapToJson(self,name):#解析map文件函数，返回一个变量列表，一个变量dict
        map_config = []
        map_dict = {}
        filename = name
        if filename:
            QMessageBox.warning(self,"找到MAP文件","找到map文件")
        else:
            QMessageBox.warning(self,"没有找到文件","没有找到相对应的map文件")

        with open(filename, 'r') as f:  #这里要改
            read = f.readlines()
            start_index = 0
            end_index = len(read)
            try: #直接在这里
                start_index = list.index(read, 'GLOBAL SYMBOLS: SORTED ALPHABETICALLY BY Name \n') + 4
                end_index = list.index(read, 'GLOBAL SYMBOLS: SORTED BY Symbol Address \n') - 3
            except Exception as e:
                print('未找到匹配的地址信息,解析过程可能稍慢，请耐心等待。')
            read = read[start_index:end_index]
            if start_index > 0:  # 匹配到开始结束位时，直接读取整个列表添加到数组中
                for t in read:
                    t = t.strip('\n')
                    t = t.split(' ')
                    if t[0][-4:] not in map_dict.keys():
                        map_dict[t[0][-8:]] = t[-1]
                        map_config.append({'value': t[0][-8:], 'desc': t[-1]})
            else:  # 未匹配到开始结束位时，就把列表循环。一般不会出现这种情况
                for t in read:
                    t = t.strip('\n')
        return map_config, map_dict

    def hextostring(self,data):
        hexstr_str = ""
        databytes = bytes(data,"UTF-8") #原来是utf-8换为bytes类型
        for i in range(len(data)):
            hexstr_str = hexstr_str + ("%02x" % databytes[i]) + " " #对每个字节处理
            hexstring1 = hexstr_str.upper()
        return hexstring1 #这个就将接收数据窗口的变成了16进制显示，#('%02x' %10) 输出两位十六进制，字母小写空缺补零！！！

    #~~~~~~~~~~~~被自定义信号连接的函数~~~~~~~~~~~信号带参数，槽函数也带参数~~~~绘图数据获取
    def textBrowser_show_data_cb(self,data):
        if self.is_uart_start == 1:
            if(1 == self.tool.uart.uart_mode): #显示一定要判断模式是否为1
                data_dict = json.loads(data) #解析Json为dict，不然温度和湿度都是str，原来代码为json.loads(data)
                if bool(data_dict):  #判断dict是否为空
                #现在要把值显示出去
                    self.save_signal.emit(data_dict)
                    self.recived_dict = data_dict #将收到的dict放入全类变量
                    #测试信息，后面删除
                    #self.user_send_length = 4
                    #self.user_para_addr = ["0c060f80","0c06119c","0c061168","0c0611d0"]

                    #循环显示keys,放入listWidget
                    for j in range(2):
                        for i in range(self.user_send_length):
                            if j == 0:
                                self.table1.setItem(i,j,QTableWidgetItem(self.user_para_addr[i]))
                            elif j == 1:
                                self.table1.setItem(i,j,QTableWidgetItem(data_dict[self.user_para_addr[i]]))



            #如果传过来数据,模式为0页就是普通模式
            elif  self.enable_recv_pause == 0:
                if (1 == self.enable_recv_file):
                    self.file.write(data)
                if (1 == self.enable_auto_line):
                    data = data + "\r"  #!!!!!!!注意设备返回数据本来就带字节流和\r注意注意attention
                #我们需要解决数据显示之前就处理为hex
                if (self.show_mode == 0):
                    self.textBrowser_recive_display.insertPlainText(data)
                    #获取到text光标
                    textCursor = self.textBrowser_recive_display.textCursor()
                    #滚动到最底部
                    textCursor.movePosition(textCursor.End)
                    #设置光标到text中去
                    self.textBrowser_recive_display.setTextCursor(textCursor)
                elif (self.show_mode == 1):
                    hexstring = self.hextostring(data)  #确定mode然后显示，用hextostring()函数
                    self.textBrowser_recive_display.insertPlainText(hexstring)
                    #获取到text光标
                    textCursor = self.textBrowser_recive_display.textCursor()
                    #滚动到最底部
                    textCursor.movePosition(textCursor.End)
                    #设置光标到text中去
                    self.textBrowser_recive_display.setTextCursor(textCursor)

    #绘图函数，先用信号来展示
    def plot_graph(self,dict_perfect):
        for i in range(self.user_send_length):
            list_perfect = dict_perfect[i]
            eval('self.p'+str(i)+'_curvel').setData(list_perfect,pen=self.pen1)

    
    def closeEvent(self,event):
        print("关闭主界面！！！")
        try:
            self.csv_file_1.close() #关闭csv文件
        except Exception as e:
            print("没有打开串口，故没有可关闭的CSV文件")
        finally:
            pass
        if self.enable_recv_file == 1:
            self.file.close()
        event.accept() #接收窗口退出事件

    #开启获取数据进程，并且创建绘图窗口并show出来
    def begin_huoqu(self):
        if self.is_uart_start == 1:
            if not self.p0_curvel:
                QMessageBox.warning(self,"未创建画板","请创建画板后进行绘图")
            else:
                self.thread1 = RunThread2(self)
                self.thread1.plot_signal.connect(self.plot_graph)
                self.thread1.start()
        else:
            QMessageBox.warning(self,"串口未打开","清先打开串口发送指令后再点击绘图!")

    #开始保存文件数据线程
    def save_file(self):
        if self.is_uart_start == 1:
            if self.tool.uart.uart_mode == 1:
                self.save_signal.connect(self.save_file_ok)
            else:
                QMessageBox.warning(self,"模式错误","请切换到模式1来获取数据!")
        else:
            QMessageBox.warning(self,"串口未打开","清先打开串口发送指令后再点击保存数据!")

    def save_file_ok(self,dataDict):
        for key,value in dataDict.items():
                self.writer_1.writerow([utils.get_current_time(),key,value])

    def create_huaban(self):
        #实例化实时绘图窗口
        #init chart初始化图像-Tab3页面展示
        pg.setConfigOption('background','w')
        pg.setConfigOptions(antialias=False, foreground=QtGui.QColor(0, 0, 0))
        self.wid = pg.GraphicsLayoutWidget() #创建wid为GraphicsLayoutWidget
        self.verticalLayout_6.addWidget(self.wid) #将其嵌入
        #创建self.user_send_length个画板,现在有self.user_para_addr个地址变量
        len_user = self.user_send_length
        #下面for循环阐释了python的精髓,一定要记住，根据用户动态确立了画图的所有属性
        for i in range(len_user): 
            setattr(self,'p'+ str(i),self.wid.addPlot(title=self.user_para_addr[i]))
            eval('self.'+'p'+str(i)).setClipToView(True)
            eval('self.'+'p'+str(i)).setDownsampling(mode = 'peak')
            eval('self.'+'p'+str(i)).setMouseEnabled(x=False, y=False)
            eval('self.'+'p'+str(i)).showGrid(x=True,y=True)
            eval('self.'+'p'+str(i)).setRange(xRange=[0, 100])
            eval('self.'+'p'+str(i)).setLimits(xMax=0)
            setattr(self,'p'+str(i)+'_curvel',eval('self.'+'p'+str(i)).plot())
            if i > 1:
                self.wid.nextRow() #现在生成的是p0,p1,p2,限制最多生成9个       
        #定义画笔
        self.pen1 = pg.mkPen({'color': (255, 0, 0), 'width': 2}) 

        
        

class RunThread1(QtCore.QThread):
    def __init__(self,parent):
        super().__init__()
        self.parent = parent #将主界面信息传过来
    
    def run(self): #接收主线程送来的信号进行保存
        #将结果存入csv
        while True:
            for key,value in self.parent.data_dict.items():
                self.parent.writer_1.writerow([utils.get_current_time(),key,value])
            time.sleep(0.1)
    def stop(self):
        self.terminate()

    

class RunThread2(QtCore.QThread): #run是0.1秒
    plot_signal = pyqtSignal(dict) #给别人信号
    def __init__(self,parent):
        super().__init__()
        self.parent = parent #将主界面信息传过来
        
    def run(self):
        dict_perfect = {}
        for i in range(self.parent.user_send_length):
            locals()['list' + str(i)] = []
        while True:
            for i in range(self.parent.user_send_length):
                if len(eval('list' + str(i))) <= 100:
                    eval('list' + str(i)).append(int(self.parent.recived_dict[self.parent.user_para_addr[i]],16))
                else:
                    locals()['list' + str(i)][:-1] = locals()['list' + str(i)][1:]
                    locals()['list' + str(i)][-1] = int(self.parent.recived_dict[self.parent.user_para_addr[i]],16)
                dict_perfect[i] = eval('list' + str(i))
            self.plot_signal.emit(dict_perfect) #传了4个列表过去
            #self.plot_signal.emit(self.list1,self.list2,self.list3,self.list4)
            time.sleep(0.2) 
    def stop(self):
        self.terminate()
        
        

if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    win = MyMainWindow()
    win.show()
    sys.exit(app.exec_())
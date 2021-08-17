# -*- coding: utf-8 -*-
#中间层-逻辑处理层
import sys
import threading
from time import sleep
from uart import Uart
import utils
import csv

class Tool(object):
    def __init__(self,parent):  #这里parent就是要获取父类的数据！！！这样我们可以调用UI层的全部类全局变量!!!
        self.err = 0            #什么意思呢，就是UI层实例化Tool把自己传进去，然后tool就可以用全部的类全局变量了
        self.parent = parent    #调用方式！！！！！，然后调用类全局变量就要self.parent.XXXX
        print('中间层：tool实例化成功')
        self.uart = Uart(self,self.parent.config_uart_port,self.parent.uart_para_dict) 
        #打开线程一致监听
        # self.uart = uart(self)
        self.start_listen_uart()

    #承上启下，是否收到数据，如果收到数据反馈给UI层

    #设置启动线程函数
    def start_listen_uart(self):
        th1 = threading.Thread(target=self.listen_uart_data_thread,daemon=True)  
        th1.start()

    #线程函数
    def listen_uart_data_thread(self):
        print("开始监听线程.....")
        while True:
            # print('正在监听串口数据')
            # sleep(1)
            #调用自定义信号,携带不同参数
            if not self.uart.is_queue_recv_is_empty():
                recv_data = self.uart.get_queue_recv()
                if (self.parent.enable_show_time == 1):
                    recv_data = utils.get_current_time() + recv_data #把时间和data全传过去，如果用户选择了时间
                #调用自定义信号
                self.parent.signal_recv_data.emit(recv_data)
       
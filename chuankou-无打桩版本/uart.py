# -*- coding: utf-8 -*-
#纯python脚本-对串口的收发,最低层
#所以encode和decode必须用在网络传输
import sys
import serial
import threading
import time
from queue import Queue
import json
import binascii

class Uart(object):
    def __init__(self,parent1,port,uart_para_dict):
        self.err = 0 #类全局变量标志位
        self.queue_recv = Queue(maxsize=240)
        #继承父类
        self.parent1 = parent1
        #判断串口类型
        self.uart_mode = 1 #0的时候是接收所有串口数据，1的时候给曲线图显示的通信协议数据数据
        #打开串口
        try:
            print("uart打开的参数为：",port,uart_para_dict['baud'],uart_para_dict["databits"],uart_para_dict["parity"],uart_para_dict["stopbits"])
            self.ser = serial.Serial(port,uart_para_dict['baud'],uart_para_dict["databits"],uart_para_dict["parity"],uart_para_dict["stopbits"])
            #默认顺序：port、baudrate、bytesize、parity、stopbits、timeout=None、xonxoff=False、rtscts=False、write_timeout=None
            #默认顺序继续：dsrdtr=False、inter_byte_timeout=None
            print("打开串口成功success")
        except:
            print("打开串口失败failed")
            self.err = -1

        self.start_recv_thread()
        
    def start_recv_thread(self):
        xiancheng = threading.Thread(target=self.uart_recv_thread,daemon=True) #这里注意daemon是守护线程，如果主线程消失，
                                                                               #它也拜拜，也就是说xiancheng变量没了，
                                                                               #self。uart_recv_thread也小时
        xiancheng.start()

    #使用队列可以解决发送数据很快时候的丢包问题，模式0接收
    def uart_recv_thread(self):
        data_dict = {} #定义一个dict来放入数据
        print('接收数据函数')
        #为了较好处理数据位，构造数据类型
        #这部分是每行都接收全部，然后全部decode，放入队列中
        while(True):
            try:
                if self.uart_mode == 0:
                    recv_data_raw = self.ser.readline()
                    data = recv_data_raw.decode("utf-8")
                    if self.queue_recv.full():
                        self.queue_recv.get()
                    self.queue_recv.put(data)
                    data = "DEVICE---->PC MODE0:" + data
                    print(data)
                elif self.uart_mode == 1: #当模式为1的时候
                    length_user = self.parent1.parent.user_send_length
                    recv_data = self.uart_recv_mode_1() 
                    if recv_data:
                        #将recv_data转化为字符串列表并且拼接，和user_send_
                        recv_data_str =''.join(map(lambda x: hex(x).split('x')[1].zfill(2), recv_data))
                        index_changdu = '' #创建一个index_changdu循环获取我们要的数据的长度位长度
                        index_len = 0 #创建一个index_len来等于转化数据里面长度位字符为int，需要乘以2哦！
                        index = 0 #从获取的数据开头，通过循环标记下一个数据的开头
                        #去掉前面4字节以及后面4个字节，对于str就是4*2=8
                        recv_data_str = recv_data_str[8:-4] #去掉16个字符，剩下500-12 = 488个字符
                        for wusuowei in range(length_user): #这句话要用的哦
                        #for wusuowei in range(2):    #测试用
                            index_changdu = recv_data_str[index + 8:index + 10] #数据长度获取，因为地址8个字符长度位2个字符固定
                            index_len = int(index_changdu,16)
                            #去地址8个字符，通过index来取
                            data_dict[recv_data_str[index :index + 8]] = recv_data_str[index + 10:index + 10 + index_len*2]
                            index = index + 10 + index_len*2
                            
                        if self.queue_recv.full():
                            self.queue_recv.get()
                        print("uart层取出来数据为：",data_dict)
                        self.queue_recv.put(json.dumps(data_dict)) #由于我们信号是发送str需要转换为str,将字典转换为str(json)
                        #self.queue_recv.put(data_dict)
            except:
                print('接收失败！')
                break

    def uart_recv_mode_1(self): #协议是uart_mode = 1
        #协议1：表4 DSP软件变量信息下发
        '''
        帧头：0xE1 0X16
        长度：1字节(数值未知)
        信息类别：0x22 
        地址：4字节
        长度：1字节
        数据：XXXX
        校验和：重新计算
        固定240个字节
        '''
        STX1 = 0xE1 #不需要b
        STX2 = 0x16 #定义协议中帧头2字节
        XXL1 = 0x22 #类型编码
        length = 0 #数据长度，最大0xFA
        CHECK_SUM = 0  #是否是CRC
        while True: #这里没有判断ser.isWaiting
            byte = self.ser.read(1) #取第一个~~~~~~~~~~~~~~~~~~~~~这个字节转换还是没理解透~~~~~~~~~~~~~~~~~~
            if(byte[0] == STX1):
                byte = self.ser.read(1) #取第二个，串口有点像队列
                if(byte[0] == STX2):
                    byte = self.ser.read(1) #取第三个,长度字节最大0xFA - 帧头长度位（2+1）
                    length = byte[0] #将长度位给到length，这个长度是（信息类别+数据位（地址、长度、数据））
                    byte = self.ser.read(1) #取第四个，信息类别0x22
                    if(byte[0] == XXL1):
                        recv_msg = [] #将存储所有数据
                        recv_msg.append(STX1) #将帧头第一个字节存入局部变量
                        recv_msg.append(STX2) #将帧头第二个字节存入局部变量
                        recv_msg.append(length) #将长度位加进去
                        recv_msg.append(XXL1) #将类型位加入进去
                        data = self.ser.read(length) #接收数据位length长度,其中包括地址4字节+自己长度1字节+数据N字节（即5+N）
                        for i in range(length):#左边可以取到右边取不到
                            recv_msg.append(data[i]) 
                        byte = self.ser.read(234-length)  #将000000取出来,不做处理
                        byte = self.ser.read(1) #再取一位,校验位第一位
                        recv_msg.append(byte[0])
                        byte = self.ser.read(1) #再取一位，校验位第二位
                        recv_msg.append(byte[0]) 
                        #检查数据完整性和正确性(后面校验)
                        if(len(recv_msg) == (length + 6)): #得到数据长度应该是：length + 5
                            if (True == self.uart_jiaoyan_mode_1(recv_msg)):#校验位校验
                                return recv_msg
                        return None

    def uart_jiaoyan_mode_1(self,recv_msg): #校验规则,注意验证
        #根据协议说明MODE_1
        #校验说明：校验位之前所有和加起来等于校验位，注意取低八位
        length = recv_msg[2]
        check_sum = 0
        for i in range(4, length + 4): #lenth加上帧头2字节和长度位1字节
            check_sum += recv_msg[i]
        check_sum &= 0xFFFF
        if recv_msg[-2] < 16:
            a1 = '0' + str(hex(recv_msg[-2])).replace('0x','')
        else:
            a1 = str(hex(recv_msg[-2])).replace('0x','')
        if recv_msg[-1] < 16:
            b1 = '0' + str(hex(recv_msg[-1])).replace('0x','')
        else:
            b1 = str(hex(recv_msg[-1])).replace('0x','')
        c = a1 + b1
        
        summaryc = int(c,16)
        if (check_sum == summaryc): #是否和传入的校验和一致
            return True
        return False
        
    def send_uart_data(self,data):
        self.ser.write(data.encode('utf-8'))

    def send_bin_data(self,data):
        if self.ser.is_open:
            print("准备发送bin文件")
            send_data = data
            self.ser.write(send_data)
            print("发送完毕")
            
            

    def uart_close(self):
        self.ser.close()

    #清空队列
    def flush_queue_recv(self):
        while not self.queue_recv.empty():
            self.queue_recv.get()
    #判断队列空情况
    def is_queue_recv_is_empty(self):
        return self.queue_recv.empty()

    #获取队列数据
    def get_queue_recv(self):
        return self.queue_recv.get()

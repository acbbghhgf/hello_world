#coding:utf-8

import Queue
import threading
import time
import socket
import os
import struct
import  sys
import time
import datetime

global exitMusic
global current_file
exitMusic = 0 # 0表示下一轮关闭录音,1表示下一轮开启录音
global music_index
music_index = 0 # 音频播放列号
global real_time #录音的时间
real_time = str(datetime.datetime.now().year)+str(datetime.datetime.now().month)+str(datetime.datetime.now().day)
# 每做一件事，方法内独立把queue住满，再清空
# 每做一件事，方法内独立把queue住满，再清空
clients = set()
ready_clients = set()
service_find_prot = 8888
client_request = 'request for recorder master'

class play_server():

    def __init__(self):
        #self.HOST = '0.0.0.0'
        self.HOST = '192.168.0.235'
        self.PORT = 8000
        os.popen('sudo fuser -k -n tcp 8000') #关闭端口占用
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 网络通信，TCP
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 释放端口占用
        self.soc.bind((self.HOST,self.PORT))  # 套接字绑定的IP与端口
        self.soc.listen(10)  # 开始TCP监听


    def run(self,deviceCount):
        self.deviceCount = deviceCount
        for i in xrange(int(deviceCount)):
            workQueue.put(True)

        for i in xrange(int(deviceCount)):
            conn, addr = self.soc.accept()  # 接受TCP连接，并返回新的套接字与IP地址
            t = threading.Thread(target=self.work,args=(conn,addr,))
            t.start()


    def work(self,conn,addr):
        #deviceName = conn.recv(1024)
        fileinfo_size = struct.calcsize('i')  # 定义文件信息。128s表示文件名为128bytes长，l表示一个int或log文件类型，在此为文件大小,如果计算机位数不一样，需要设l为i
        buf = conn.recv(fileinfo_size)
        deviceName = struct.unpack('i', buf)[0]
        print deviceName,' Connected by', addr  # 输出客户端的IP地址
        conn.sendall('ok')
        self.ready(conn,deviceName)

    def ready(self,conn,deviceName):
        data = conn.recv(1024)
        if data == 'ready':
            queueLock.acquire()
            workQueue.get()
            workQueue.task_done()
            queueLock.release()
            workQueue.join() # 阻塞直到为空
            self.while_start(conn,deviceName)
           # time.sleep(0.05)
        else:
            print data
            print deviceName,' 连接异常'

    def while_start(self,conn,deviceName):
        while 1:
            self.startRecord(conn,deviceName)  # 发起开启录音请求

    def startRecord(self,conn,deviceName):
        queueLock.acquire()
        workQueue.put(True)
        queueLock.release()
        while not workQueue.full:
            # 不满等待
            pass
        conn.sendall('start_record')
        #while 1:
        data = conn.recv(1024)
             #if data == 'start_record':
                 #break
        if data == 'start_record':
            queueLock.acquire()
            workQueue.get()
            workQueue.task_done()
            print deviceName,'_开启录音'
            queueLock.release()
        else:
            print data
            print len(data)
            raise Exception(deviceName + '_开启录音异常')

        startQueue.get()
        startQueue.task_done()
        startQueue.join()
        workQueue.join()
        self.stopRecord(conn,deviceName)

    def stopRecord(self,conn,deviceName):
        workQueue.get()
        workQueue.task_done()
        workQueue.join()
        #time.sleep(0.05)
        
        conn.sendall('stop_record')
        if conn.recv(1024) == 'stop_record':
            print  deviceName,"_关闭录音"
            self.downLoad(conn,deviceName)
        else:
            raise Exception(str(deviceName) + ' 关闭录音异常')

    def downLoad(self,conn,deviceName):
        file_name = stopQueue.get()
        conn.sendall('down_load')
        data = conn.recv(1024)
        if data == 'down_load':
            conn.sendall('do')
            self.file(conn,deviceName, file_name)
        else:
            print data
            print len(data)
            raise Exception(str(deviceName) + ' 回传录音异常')
        stopQueue.task_done()
        stopQueue.join()

    def file(self,conn,deviceName, music_name):
        #fileinfo_size = struct.calcsize('1024si')  # 定义文件信息。128s表示文件名为128bytes长，l表示一个int或log文件类型，在此为文件大小,如果计算机位数不一样，需要设l为i
        fileinfo_size = struct.calcsize('i')  # 定义文件信息。128s表示文件名为128bytes长，l表示一个int或log文件类型，在此为文件大小,如果计算机位数不一样，需要设l为i
        buf = conn.recv(fileinfo_size)
        filesize = struct.unpack('i', buf)[0]
        print filesize
        conn.sendall('ready_downLoad')
        if filesize:  # 如果不加这个if，第一个文件传输完成后会自动走到下一句
            path = './auto_record_file/'+str(deviceName)+"/"
            #filename, filesize = struct.unpack('1024si', buf)
            filenewname = path + music_name
            recvd_size = 0  # 定义接收了的文件大小
            print deviceName, '_机器传回的音频文件', str(filesize), filenewname
            isExists = os.path.exists(path)

            if not isExists:
                os.makedirs(path)
            if os.path.exists(filenewname):
                raise Exception(str(deviceName) + 'duplicate file')
            file_wav = open(filenewname.split('\0')[0], 'wb')
            while not recvd_size == filesize:
                if filesize - recvd_size > 1024:
                    rdata = conn.recv(1024)
                else:
                    rdata = conn.recv(filesize - recvd_size)
                recvd_size += len(rdata)
                file_wav.write(rdata)
            file_wav.close()
            conn.sendall('do')
            do = conn.recv(1024)
            if do == 'file_success':
                print deviceName,"_机器录音保存成功"
            else:
                print do
                raise Exception(str(deviceName) + ' _机器录音保存异常')
        else:
            raise Exception(str(deviceName) + 'empty file')

def playMusic(music_addr):
    # global music_index
    # global exitMusic
    music_name = music_addr.split('/')[-1].split(' ')[0]
    print '正在播放',music_name
    os.popen('sh aplay.sh %s'%music_addr)
    # exitMusic = 1 #0表示下一轮关闭录音,1表示下一轮开启录音
    # print '第 ',str(music_index + 1),' 播放结束'
    # play_flag = 1
    
def client_close(cli):
    ready_clients.remove(cli)
    clients.add(cli)

class client(object):
    def __init__(self, addr, dev_id):
        self.__addr = addr
        print("dev_id", str(dev_id))
        self.__did = dev_id

    def __str__(self):
        return self.__addr

    def assign(self, id_buf, socket):
        if id_buf != self.__did:
    	    print("id_buf",id_buf,"__did",self.__did)
            return False
        else:
            self.__socket = socket
            self.addr = '%s:%d' % socket.getpeername()
            return True

    def start(self, current_file):
        self.send_string('1%s' % current_file)
        recv_buf = cli.recv_string()
        if(recv_buf):
            print(cli.addr + ': ' + recv_buf)
    
    def stop(self):
        self.send_string('2')
        recv_buf = cli.recv_string()
        if(recv_buf):
            print(cli.addr + ': ' + recv_buf)

    def join(self):
        self.send_string('3')
        time.sleep(1)
        self.close_socket()

    def send_string(self, string):
        try:
            self.__socket.sendall(struct.pack('B', len(string)))
            self.__socket.sendall(string)
        except socket.error, e:
            self.close_socket()
    def recv_string(self):
        try:
            len_bytes = self.__socket.recv(1)
            content_len, = struct.unpack('B', len_bytes)
            return self.__socket.recv(content_len)
        except socket.error, e:
            self.close_socket()
	    return None
    def close_socket(self):
        self.__socket.close()
        # client_close(self)


class server(object):
    def __init__(self, addr, port):
        self.__serv_addr = (addr, port)
        self.__fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.__fd.bind(self.__serv_addr)

    def serve(self, handler):
        print(self.__fd.listen(10))
        global run
        while run:
            cli_sock, addr = self.__fd.accept()
	    try:
	        id_buf = cli_sock.recv(12)
		print("xxx",id_buf)
	    except socket.error, e:
		break
            handler(cli_sock, id_buf)
        return self

    def close(self):
        close(self.__fd)

def wait_clients_join(n, port, ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', 8888))
    for i in range(n):
        while True:
            data, addr = s.recvfrom(1024)
            print(data)
            msg = data.split(":")
            print(msg[0])
            if msg[0] == client_request:
                print(msg[1])
                content = bytearray(struct.pack('B', 0x88))
                content.extend('%s:%d' % (ip, port))
                s.sendto(content, 0, addr)
                clients.add(client(addr[0], msg[1]))
                print('%s[%d,%s]: Join' % (addr[0], addr[1], msg[1]))
                break
    s.close()

def client_handler(socket, id_buf):
    for cli in clients:
        if cli.assign(id_buf, socket):
            clients.remove(cli)
            ready_clients.add(cli)
            break

def do_serve(opt):
    server('0.0.0.0', opt.port).serve(client_handler)
    sleep(360)
    server('0.0.0.0', opt.port).close

def run(opt):
    th = threading.Thread(target=do_serve,args=(opt,))
    th.start()
    wait_clients_join(opt.num, opt.port, opt.ip)

if __name__ == "__main__":
    import optparse
    global play_flag
    parser = optparse.OptionParser()
    parser.add_option('-n', '--num', dest='num', type='int', default=1)
    parser.add_option('-p', '--port', dest='port', type='int', default=19088)
    parser.add_option('-i', '--ip', dest='ip', type='string', default='192.168.0.160')
    parser.add_option('-f', '--fn', dest='fn', type='string', default='1.t')
    (opt, _) = parser.parse_args()
    print "请输入录音设备数量:"
    deviceCount = int(raw_input())
    opt.num = deviceCount
    run(opt)
    print "请输入播放的分贝值dbc:格式(70)"
    playdbc = str(raw_input())

    list_wav = []
    with open(opt.fn, 'rb') as f:
        for line in f.readlines():
            list_wav.append(line.strip('\n'))
    list_len = len(list_wav)
    print "list_len:",list_len
    while music_index < list_len:
        current_file = 'auto-qdm-'+real_time+'-'+playdbc+'dbc-'+list_wav[music_index].split('/')[-1].split('.')[0] +'.pcm'
        play = threading.Thread(target=playMusic,args=(list_wav[music_index],))
        for cli in ready_clients:
            cli.start(current_file)
            print("开始时间为%d" % int(time.time()))
	    print("正在录音，录音文件名为%s" %current_file)
        play.start()
        
        print '正在播放第 ',str(music_index + 1),' 首音乐 '
        play.join()
        print '第 ',str(music_index + 1),' 播放结束'
        for cli in ready_clients:
            cli.stop()
            print("停止录音时间为%d" % int(time.time()))
        music_index = music_index + 1
    print '音乐列表播放完毕'
    try:
        th.join()
    except:
        pass
    for cli in ready_clients:
        cli.join()
    print("与录音机断开链接%d" % int(time.time()))

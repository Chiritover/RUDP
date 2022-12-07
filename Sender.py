import sys
import getopt
import threading
import time

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''


class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        if sackMode:
            raise NotImplementedError  # remove this line when you implement SACK
        self.windowSize = 5
        self.base = 0
        self.nextSeqNum = 1
        self.sackMode = sackMode
        self.bufferSize = 1460
        self.timer = [None, None, None, None, None]
        self.TimeoutInterval = 0.5
        # 保存窗口内的包
        self.data = [None, None, None, None, None]
        self.lock = threading.Lock()

    # Main sending loop.
    def start(self):
        if self.sackMode:
            start_packet = self.make_packet("start", 0, "")
            self.send(start_packet)
            self.log("send start: %s" % start_packet)
            self.data[0] = start_packet
            self.timer[0] = threading.Timer(self.TimeoutInterval, self.handle_timeout)
            self.timer[0].start()
            # wait for ack
            while True:
                ack, _ = self.receive()
                if Checksum.validate_checksum(ack):
                    ack = self.split_packet(ack)
                    if ack[0] == "sack" and ack[1] == "1;":
                        self.log("receive ack: %s" % ack)
                        break
            self.log("start sending")
            while
            return

        # first send the start packet
        start_packet = self.make_packet('start', 0, '')
        self.send(start_packet)
        self.data[0] = start_packet
        self.timer[0] = threading.Timer(self.TimeoutInterval, self.handle_timeout)
        self.timer[0].start()
        self.log("sent: %s" % start_packet)
        # wait for the ack
        ack = self.receive().decode()
        # print("recv: %s" % ack)
        if ack is None:
            self.log("didn't receive ack for start packet")
            return
        msg_type, seqno, data, checksum = self.split_packet(ack)
        self.base = int(seqno)
        self.nextSeqNum = int(seqno)
        if msg_type != 'ack':
            self.log("received non-ack for start packet")
            return
        if not Checksum.validate_checksum(ack):
            self.log("received corrupt ack for start packet")
            return
        msg_type = 'data'
        msg = self.infile.read(self.bufferSize)
        # print(msg)
        while msg_type != 'end':
            #         将在base之后窗口内数据包发送
            while self.nextSeqNum <= self.base + self.windowSize and msg_type != 'end':
                next_msg = self.infile.read(self.bufferSize)
                msg_type = 'data'
                # 如果读入的数据包长度小于bufferSize，说明已经读完了，将msg_type改为end
                if len(next_msg) < self.bufferSize:
                    msg_type = 'end'
                packet = self.make_packet('data', self.nextSeqNum, msg)
                self.data[self.nextSeqNum % self.windowSize] = packet
                self.send(packet)
                self.log("sent: %s" % packet)
                self.timer[self.nextSeqNum % self.windowSize] = threading.Timer(self.TimeoutInterval,
                                                                                self.handle_timeout)
                self.timer[self.nextSeqNum % self.windowSize].start()
                self.nextSeqNum += 1
                msg = next_msg
            while True:
                ack = self.receive().decode()
                ack_msg_type, seqno, data, checksum = self.split_packet(ack)
                # check if the ack is corrupted
                if not Checksum.validate_checksum(ack):
                    self.log("received corrupt ack: %s" % ack)
                    continue
                if ack_msg_type == 'ack':
                    self.handle_new_ack(int(seqno))
                break
        #     send end packet
        end_packet = self.make_packet('end', self.nextSeqNum, msg)
        self.send(end_packet)
        self.data[self.nextSeqNum % self.windowSize] = end_packet
        self.timer[self.nextSeqNum % self.windowSize] = threading.Timer(self.TimeoutInterval, self.handle_timeout)
        self.timer[self.nextSeqNum % self.windowSize].start()
        self.log("sent: %s" % end_packet)
        # 接受剩余的ack
        while self.base < self.nextSeqNum:
            ack = self.receive().decode()
            ack_msg_type, seqno, data, checksum = self.split_packet(ack)
            # check if the ack is corrupted
            if not Checksum.validate_checksum(ack):
                self.log("received corrupt ack: %s" % ack)
                continue
            if ack_msg_type == 'ack':
                self.handle_new_ack(int(seqno))
        self.log("done sending")

    def handle_timeout(self):
        if self.sackMode:  # 选择重传
            raise NotImplementedError
        else:  # go back n
            #         重新设置时间，重传base到nextSeqNum的包
            for i in range(self.base % self.windowSize, self.nextSeqNum % self.windowSize):
                self.timer[i].cancel()
                self.timer[i] = threading.Timer(self.TimeoutInterval, self.handle_timeout)
                self.timer[i].start()
                packet = self.data[i]
                self.send(packet)
                self.log("resend: %s" % packet)

    def handle_new_ack(self, ack):
        if self.sackMode:  # Selective Acknowledgements
            raise NotImplementedError
        else:  # go back n
            # 1.	如果接收端收到了一个sequence number不为N的数据包，它会发送“ack|N”
            # 2.	如果接收端收到了一个sequence number为N的数据包，它会检查
            # 自己已按序收到的数据包中序号最大的数据包，假设该数据包的sequence number为M，
            # 那么接收端会发送“ack|M+1”
            if self.base < ack <= self.nextSeqNum:
                self.base = ack
                for i in range(self.base, self.nextSeqNum):
                    self.timer[i % self.windowSize].cancel()
                self.log("receive ack: %s" % ack)

    def handle_dup_ack(self, ack):
        raise NotImplementedError

    def log(self, msg):
        if self.debug:
            print(msg)


'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print("RUDP Sender")
        print("-f FILE | --file=FILE The file to transfer; if empty reads from STDIN")
        print("-p PORT | --port=PORT The destination port, defaults to 33122")
        print("-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost")
        print("-d | --debug Print debug messages")
        print("-h | --help Print this usage message")
        print("-k | --sack Enable selective acknowledgement mode")


    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False
    sackMode = False

    for o, a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest, port, filename, debug, sackMode)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()

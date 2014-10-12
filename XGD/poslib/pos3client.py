#-*- coding: utf-8 -*-

import PosMsg
import socket
import binascii
from robot.api import logger

TCP_PROTOCOL = 'tcp'
UDP_PROTOCOL = 'udp'

class Pos3Client(object):
   """
   """   
   def __init__(self):
      self.sk = None
      self.defaulttimeout = 20
      self.serveraddr = None
      self.protocol = None
   
   def connect_to_server(self, serverip, port, protocol = TCP_PROTOCOL):
      if self.sk:
         self.close_connection()
      if protocol.lower() not in [TCP_PROTOCOL, UDP_PROTOCOL]:
         raise AssertionError("Protocol type not supported! %s" % protocol)
      self.protocol = protocol.lower()
      self.__getattribute__('_%s_connect' % self.protocol)(serverip, port)
   
   def _udp_connect(self, serverip, port):
      self.sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      self.sk.settimeout(self.defaulttimeout)
      self.serveraddr = (serverip, int(port))
   
   def _tcp_connect(self, serverip, port):
      self.serveraddr = (serverip, int(port))
      self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sk.connect(self.serveraddr)
      self.sk.settimeout(self.defaulttimeout)
   
   def _udp_send(self, msg):
      self.sk.sendto(self.pack_msg(msg), self.serveraddr)
   
   def _tcp_send(self, msg):
      self.sk.send(self.pack_msg(msg))
   
   def _udp_receive(self):
      data = ''
      recv, ADDR = self.sk.recvfrom(2)
      data += recv
      #print self.unpack_msg(data)
      length = int(self.unpack_msg(data), 16)
      recv, ADDR = self.sk.recvfrom(length)
      data += recv
      
      data = self.unpack_msg(data)
      return data
   
   def _tcp_receive(self):
      data = ''
      data += self.sk.recv(2)
      #print self.unpack_msg(data)
      length = int(self.unpack_msg(data), 16)
      data += self.sk.recv(length)
      
      data = self.unpack_msg(data)
      return data
   
   def send_packet(self, msg):
      if not self.sk:
         raise RuntimeError("Please connect to server first!")
      logger.info("Sending Message: %s" % msg, True)
      self.__getattribute__('_%s_send' % self.protocol)(msg)
   
   def receive_packet(self, parser=None):
      if not self.sk:
         raise RuntimeError("Please connect to server first!")
      data = self.__getattribute__('_%s_receive' % self.protocol)()
      logger.info("Received Message: %s" % data, True)
      if parser:
         return parser(data)
      else:
         return data
   
   def send_receive(self, msg, parser=None):
      self.send_packet(msg)
      return self.receive_packet(parser)
   
   def close_connection(self):
      if self.sk:
         self.sk.close()
      self.sk = None
   
   def pack_msg(self, msg):
      return binascii.a2b_hex(msg)
   
   def unpack_msg(self, msg):
      return binascii.b2a_hex(msg)
      

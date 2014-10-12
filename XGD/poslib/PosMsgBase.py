#-*- coding: utf-8 -*-
"""

(C) Copyright 2004 wei_cloud@126.com

"""
from test.test_float import toHex

__author__ =  'wei_cloud@126.com'
__version__=  '1.0'
__licence__ = 'GPL V3'

from Utils import *
from robot.api import logger

class FieldNonExistError(RuntimeError):
   pass

class Pos3MsgBase(object):
   """
   符号约定
   N  ：数值，定长右靠左补零，若表示金额，则最右两位为角分。
   AN ：字母/数字，定长，左靠右补空格。
   VAR：可变长数据。
   HEX：以十六进制表示的数据。
   ASC：按照ASCII码表示的数据。
   BCD：按照ASCII码数据顺序，以十六进制表示。
   M  ：必须存在的数据域。
   M  ：必须原值返回的数据域
   """
   
   fields = fixdict()
   fieldlength = 0
      
   def __init__(self, msg="", debug=False):
      """
      """
      self.DEBUG = debug
      self.fieldlength = len(self.fields)
      self.msg = ''
      if not self.__hasattribute__('msgType'):
         self.msgType = '87'
      if msg != "":
         self.setContent(msg)
      else:
         self.initFields()
   
   def initFields(self):
      for i in self.fields.keys():
         self.__setattr__(self.getName(i), '0')
   
   def getName(self, fieldId):
      return self.fields[fieldId][1]
   
   def getAttr(self, fieldId):
      return self.fields[fieldId][2]
   
   def getType(self, fieldId):
      return self.fields[fieldId][3]
   
   def getLength(self, fieldId):
      return int(self.fields[fieldId][4])*2
   
   def getShowFlag(self, fieldId):
      """
      should overwrite this in child class
      """
      return True
      
   def setField(self, fieldId, value):
      try:
         fieldId = int(fieldId)
         self.__setattr__(self.getName(fieldId), value)
      except ValueError, e:
         if not self.nameInField(fieldId):
            raise FieldNonExistError("This field (%s) is not defined, please check your input!" % fieldId)
         self.__setattr__(fieldId, value)
         
   def setFields(self, fieldDict={}):
      if not fieldDict:
         return 
      for k, v in fieldDict.items():
         self.setField(k, v)
   
   def getField(self, fieldId):
      try:
         fieldId = int(fieldId)
         return self.__getattribute__(self.getName(fieldId))
      except ValueError, e:
         if not self.nameInField(fieldId):
            raise FieldNonExistError("This field (%s) is not defined, please check your input!" % fieldId)
         return self.__getattribute__(fieldId)
   
   def nameInField(self, name):
      for i in self.fields.keys():
         if self.getName(i) == name:
            return True
      return False
   
   def setContent(self, msg):
      offset = self.readFromString(msg)  
      self.msg = msg[:offset]    
      return offset
      
   def __hasattribute__(self, name):
      try:
         self.__getattribute__(name)
         return True
      except AttributeError:
         return False
   
   def readFromString(self, strcontent):
      offset = 0
      for i in self.fields.keys():
         length = 0         
         if not self.getShowFlag(i):
            continue
         logger.debug(self.getName(i)+':'+ strcontent[offset:])
         if self.__hasattribute__('read_'+self.getName(i)):
            length = self.__getattribute__('read_'+self.getName(i))(strcontent[offset:])
            #self.setField(self.getName(i), value)
            logger.debug('===:'+self.getName(i)+ str(self.getField(self.getName(i)))+ ':'+ strcontent[offset:])         
         elif not isinstance(self.getAttr(i), basestring) and self.getAttr(i) != None:
            value = self.getAttr(i)(strcontent[offset:])
            self.setField(self.getName(i), value)
            length = len(value)            
            logger.debug('===:'+self.getName(i) + ':' + str(self.getField(self.getName(i)))+ ':'+ strcontent[offset:])
         elif self.getAttr(i) in ['N', 'AN']:
            length = self.getLength(i)
            value = strcontent[offset:offset+length]
            self.setField(self.getName(i), value)
         elif self.getAttr(i).endswith('VAR'):
            length = self.getLength(i)
            datalen = strcontent[offset:offset+length]
            length = length + int(datalen, 16)*2
            value = strcontent[offset+self.getLength(i):offset+length]
            self.setField(self.getName(i), value)
         elif self.getAttr(i).endswith('LIST'):
            length = self.read_record_list(i, strcontent[offset:])
         else:
            raise RuntimeError("This data (%s) is not implemented!" % self.getAttr(i))
         
         offset += length         
      return offset
         
   def fieldFill(self, filedId, value):
      ret = ''
      datalen = self.getLength(filedId)
      if self.getAttr(filedId) == 'AN':
         if self.getType(filedId) == 'ASC':
            ret = value + '32'*((datalen-len(value))/2)
         else:
            ret = value + '0'*(datalen-len(value))
      if self.getAttr(filedId) == 'N':
         if self.getType(filedId) == 'ASC':
            ret = '32'*((datalen-len(value))/2) + value
         else:
            ret = value.zfill(datalen)
      return ret

   def constructMsg(self, force=False):
      msg = ''
      for i in self.fields.keys():
         if not self.getShowFlag(i):
            continue
         datavalue = self.getField(i)
         if self.getName(i) in ['msgLength', 'parityBit']:
            continue
         if self.__hasattribute__('construct_'+self.getName(i)):
            value = self.__getattribute__('construct_'+self.getName(i))()
            msg += str(value)
         elif not isinstance(self.getAttr(i), basestring) and self.getAttr(i) != None:
            if isinstance(datavalue, basestring):
               msg += datavalue
            else:
               msg += datavalue.constructMsg()
         elif self.getAttr(i) in ["AN", "N"]:
            msg += self.fieldFill(i, datavalue)
         elif self.getAttr(i).endswith('VAR'):
            if not isinstance(datavalue, basestring):
               datavalue = datavalue.constructMsg(force)
            validlen = hex(len(datavalue)/2)[2:]    
            msg += validlen.zfill(self.getLength(i))
            alignmentType = self.getAttr(i).replace('VAR', '')
            if len(datavalue) % 2 == 0:
               msg += datavalue
            else:
               if alignmentType == 'AN':
                  msg += datavalue + '0'
               if alignmentType == 'N':
                  msg += '0' + datavalue     
         elif self.getAttr(i).endswith('LIST'):
            msg += self.construct_record_list(i)
      
      self.msg = msg
      return msg      
   
   def read_record_list(self, fieldId, strcontent):
      offset = 0
      recordlist = []
      countlen = self.getLength(fieldId)
      count = int(strcontent[offset:offset+countlen], 16)
      offset += countlen
      for i in range(count):
         datatype = self.getType(fieldId)
         data = datatype(strcontent[offset:])
         recordlist.append(data)
         offset += len(data)
      self.setField(fieldId, recordlist)
      logger.debug("===:%s:%s:%s" % (self.getName(fieldId), len(recordlist), map(str, recordlist)))
      return offset
   
   def construct_record_list(self, fieldId):
      msg = ''
      recordlist = self.getField(fieldId)
      count = len(recordlist)
      msg += toHexstr(count).zfill(self.getLength(fieldId))
      for rec in recordlist:
         msg += rec.constructMsg()
      
      return msg   
         
   def getMsg(self, force=False):
      if force:
         return self.msg
      return self.constructMsg()
      
   def printFields(self):
      for i in self.fields.keys():
         print(self.getName(i) + ' : ' + str(self.getField(i)))
         
   def __str__(self):
      return self.getMsg()
   
   def __unicode__(self):
      return self.__str__()
      
   def __len__(self):
      return len(self.msg)
   
class Pos3DirectiveMsg(Pos3MsgBase):
   def constructMsg(self, force=False):
      msg = Pos3MsgBase.constructMsg(self, force)
      if self.getName(self.fields.keys()[0]) == 'validLength':
         datalen = self.getLength(self.fields.keys()[0])
         msg = msg[datalen:]
         msg = hex(len(msg)/2)[2:].zfill(datalen) + msg
      return msg
   
   def readFromString(self, strcontent):
      
      offset = Pos3MsgBase.readFromString(self, strcontent)
      #In case some field is not implemented yet.
      if self.getName(self.fields.keys()[0]) == 'validLength':
         datalen = self.getLength(self.fields.keys()[0])
         offset = datalen + int(self.getField('validLength'), 16)*2
      return offset


class TLVField(Pos3DirectiveMsg):
   id = 00
   fields = fixdict()
   
   fields[1] = ['1', 'tag', 'N', 'ASC', '2']
   fields[2] = ['2', 'value', 'NVAR', 'HEX', '1']

class _terminalPara(Pos3DirectiveMsg):
   id = 00
   fields = fixdict()
   
   fields[1] = ['1', 'index', 'N', 'HEX', '1']
   fields[2] = ['2', 'paraData', 'NVAR', 'HEX', '1']

class updateTerminalParameter(Pos3DirectiveMsg):
   """
   输入数据格式：
序号   字段名称   属性   类型   备 注
1   有效数据长度   N2   HEX   指明以下有效数据字节数
2   参数记录数   N1   HEX   指明以下记录条数
3   参数记录号   N1   HEX   终端中记录号（参见5.终端参数管理）
4   参数有效数据长度   N1   HEX   
5   参数有效数据   An   ASC   

   """
   id = 22
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'paraList', 'NLIST', _terminalPara, '1']
   
class updateWorkingKey(Pos3DirectiveMsg):
   """
    序号   字段名称   属性   类型   备 注
1   有效数据长度   N1   HEX   指明以下有效数据字节数
2   主密钥索引   N1   HEX   用于解密工作密钥的主密钥存放位置
3   PIN密钥记录号   N1   HEX   记录PIN密钥存放位置   0x41
4   PIN密钥长度   N1   HEX   长度8的倍数
5   PIN密钥   VAR   HEX   
6   PIN密钥CV   N4   HEX   PIN密钥校验值
7   MAC密钥记录号   N1   HEX   记录MAC密钥存放位置   0x42
8   MAC密钥长度   N1   HEX   长度8的倍数
9   MAC密钥   VAR   HEX   
10   MAC密钥CV   N4   HEX   MAC密钥校验值
11   磁道密钥记录号   N1   HEX   记录磁道密钥存放位置   0x43
12   磁道密钥长度   N1   HEX   长度8的倍数
13   磁道密钥   VAR   HEX   
14   磁道密钥CV   N4   HEX   磁道密钥校验值

   """
   id = 57
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '1']
   fields[2] = ['2', 'primaryKeyIndex', 'N', 'HEX', '1']
   fields[3] = ['3', 'pinKeyRcordNumber', 'N', 'HEX', '1']
   fields[4] = ['4', 'pinKey', 'NVAR', 'HEX', '1']
   fields[5] = ['5', 'pinKeyCV', 'N', 'HEX', '4']
   fields[6] = ['6', 'macKeyRecordNumber', 'N', 'HEX', '1']
   fields[7] = ['7', 'macKey', 'NVAR', 'HEX', '1']
   fields[8] = ['8', 'macKeyCV', 'N', 'HEX', '4']
   fields[9] = ['9', 'trackKeyRcordNumber', 'N', 'HEX', '1']
   fields[10] = ['10', 'trackKey', 'NVAR', 'HEX', '1']
   fields[11] = ['11', 'trackKeyCV', 'N', 'HEX', '4']
   
class updateICTag(Pos3DirectiveMsg):
   """
   序号   字段名称   属性   类型   备注
1   有效数据长度   N   HEX2   
2   标签总数   N   HEX1   01表示IC卡数据处理;
02表示磁条卡数据处理
3   标签索引   T      tag标签索引
4   标签数据属性   N   HEX   0-   结构化
1-   ANS
2-   CN3-   B
5   标签数据格式   N   HEX   0-   DECIMAL(12，0)
1-   DECIMAL(12，1)
2-   DECIMAL(12，2)
3-   DECIMAL(12，3)
4-   DECIMAL(12，4)
5-   DECIMAL(12，5)
6-   YYMMDD
7-   CCYYMMDD
8-   HHMMSS
6   标签长度类型   N   HEX   0-   定长
1-   VAR
2-   LVAR
3-   LLVAR
4-   LLLVAR
7   标签长度   N   HEX2   若标签长度类型0，则表示固定长度。
若标签长度类型其他，则表示最大长度

   """
   id = 85
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'tagCount', 'N', 'HEX', '1']
   fields[3] = ['3', 'tagIndex', 'N', 'HEX', '1']
   fields[4] = ['4', 'tagDataProperty', 'N', 'HEX', '1']
   fields[5] = ['5', 'tagDataFormat', 'N', 'HEX', '1']
   fields[6] = ['6', 'tagDataType', 'N', 'HEX', '1']
   fields[7] = ['7', 'tagDatalength', 'N', 'HEX', '1']
   
   
class updateMerchantInfo(Pos3DirectiveMsg):
   """
   序号   字段名称   属性   类型   备注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   商户信息版本号   N   HEX4   
3   商户信息组索引号   N   HEX1   更新成功后，更新原版本号
4   商户信息记录长度   N   HEX1   商户信息的长度
5   商户信息记录内容   VAR   ASC   本域采用TLV （tag-length-value ）的表示方式，即每个子域由 tag 标签索引(T)，子域取值的长度(L)和子域取值(V) 构成。

商户信息TAG表
1   通道号   N      EF01
2   商户号   N      1F07
3   商户名称   N      1F08
4   终端号   N      1F09

   """
   id = 80
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'merchantVersion', 'N', 'HEX', '4']
   fields[3] = ['3', 'merchantGroupIndex', 'N', 'HEX', '1']
   fields[4] = ['4', 'merchantInfo', 'NVAR', 'ASC', '1']

class updateICOfflinePrintList(Pos3DirectiveMsg):
   """
 序号   字段名称   属性   类型   备注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   脱机打印版本号   A   ASC4   脱机打印版本号
3   脱机打印列表索引   N   HEX1   指定脱机交易使用的脱机打印列表
4   打印信息长度   N   HEX2   打印信息的长度
5   凭单特征标识   N   HEX1   用于标识凭单特征：
1－交易凭条　
2－结算单　
3－非存储的打印凭条
6   打印份数   N1   ASC   需要打印的份数
7   IC卡标志   N   HEX1   是否为IC卡打印。0x00—非IC卡交易打印，0x01—IC卡交易打印
8   打印信息   VAR      

   """
   id = 79
   fields = fixdict()
   
   def __init__(self):   
      raise RuntimeError("This Message is not implemented yet!")

class updateBlacklist(Pos3DirectiveMsg):
   """
 序号   字段名称   属性   类型   备注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   黑名单版本号   A   HEX4   黑名单的版本号。通过结束位来判断是否需要还有后续包。如果没有后续包则保存黑名单版本号。
3   黑名单记录数   N   HEX1   指明以下黑名单记录条数
4   黑名单卡号长度   N   HEX1   
5   黑名单卡号数据   VAR   ASC   

   """
   id = 78
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'blacklistVersion', 'AN', 'HEX', '4']
   fields[3] = ['3', 'blacklistCount', 'N', 'HEX', '1']
   fields[4] = ['4', 'blacklistData', 'NVAR', 'ASC', '1']

class updateCAPK(Pos3DirectiveMsg):
   """
 序号   字段名称   属性   类型   备注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   CAPK版本号   A   HEX4   CAPK版本号。通过结束位来判断是否需要还有后续包。如果没有后续包则保存CAPK版本号。
3   CAPK组索引号   N   HEX1   CAPK组的索引号
4   CAPK记录数   N   HEX1   CAPK记录数
5   CAPK记录长度   N   HEX2   CAPK记录长度
6   CAPK记录内容   AVR   ASC   本域采用TLV （tag-length-value ）的表示方式，即每个子域由 tag 标签索引(T)，子域取值的长度(L)和子域取值(V) 构成。

CAPK记录相关TAG:
序号   字段名称   属性   类型   备注
1   RID   N      9F06
2   认证中心公钥索引   N      9F22
3   认证中心公钥有效期   N      DF05
4   认证中心公钥哈什算法标识   N      DF06
5   认证中心公钥算法标识   N      DF07
6   认证中心公钥模   N      DF02
7   认证中心公钥指数   N      DF04
8   认证中心公钥校验值   N      DF03

   """
   id = 77
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'CAPKVersion', 'N', 'HEX', '4']
   fields[3] = ['3', 'CAPKIndexGroup', 'N', 'HEX', '1']
   fields[4] = ['4', 'CAPKRecordNumber', 'N', 'HEX', '1']   
   fields[5] = ['5', 'CAPKContent', 'NVAR', 'ASC', '2']
   
   #TODO: 2   CAPK版本号   A   HEX4   CAPK版本号。通过结束位来判断是否需要还有后续包。如果没有后续包则保存CAPK版本号。
   

class updateAID(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   AID版本号   A   HEX4   AID的版本号。通过结束位来判断是否需要还有后续包。如果没有后续包则保存AID版本号。
3   AID组索引号   N   HEX1   AID组的索引号
4   AID记录数   N   HEX1   指明以下AID记录条数
5   AID记录长度   N   HEX2   AID记录的长度
6   AID记录内容   VAR   ASC   本域采用TLV （tag-length-value ）的表示方式，即每个子域由 tag 标签索引(T)，子域取值的长度(L)和子域取值(V) 构成。

AID记录相关TAG:
序号   字段名称   属性   类型   备注
1   AID   B      Tag:9F06 
2   应用选择指示符   B      Tag:DF01 
3   应用版本号   B      Tag:9F08
4   TAC-缺省   B      Tag:DF11
5   TAC-联机   B      Tag:DF12
6   TAC-脱机   B      Tag:DF13
7   终端最低限额   B      Tag:9F1B
8   偏置随记选择的阈值   B      Tag:DF15
9   偏置随机选择的最大目标百分数   CN      Tag:DF16
10   随机选择的目标百分数   CN      Tag:DF17
11   缺省DDOL   B      Tag:DF14
12   终端联机PIN支持能力   B      Tag:DF18
13   终端电子现金交易限额   CN      Tag:9F7B
14   读写器持卡人验证方法（CVM）所需限制   CN      Tag:DF21
15   非接触读写器交易限额   CN      Tag:DF20
16   非接触读写器脱机最低限额   CN      Tag:DF19

   """
   id = 76
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'AIDVersion', 'N', 'HEX', '4']
   fields[3] = ['3', 'AIDIndexGroup', 'N', 'HEX', '1']
   fields[4] = ['4', 'AIDRecordNumber', 'N', 'HEX', '1']   
   fields[5] = ['5', 'AIDContent', 'NVAR', 'ASC', '2']

   #TODO: 2   AID版本号   A   HEX4   AID的版本号。通过结束位来判断是否需要还有后续包。如果没有后续包则保存AID版本号。


class readSpecialICTradeResult(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备注
1   特殊交易数据长度   N   HEX2   脱机交易有效数据长度
2   特殊交易类型   N   HEX1   0x01:ARPC错但卡片仍然承兑
0x02:脱机成功
0x03:脱机失败
3   交易读卡方式   N   HEX1   0x01:IC卡 
0x02:非接
4   交易流水号   N   BCD3   特殊交易交易流水号
5   交易代码   N   HEX3   特殊交易交易代码
6   特殊交易内容   VAR      本域采用TLV （tag-length-value ）的表示方式，即每个子域由 tag 标签索引(T)，子域取值的长度(L)和子域取值(V) 构成。

   """
   id = 75
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'tradeType', 'N', 'HEX', '1']
   fields[3] = ['3', 'cardType', 'N', 'HEX', '1']
   fields[4] = ['4', 'tradeSeq', 'N', 'BCD', '3']   
   fields[5] = ['5', 'tradeCode', 'N', 'HEX', '3']
   fields[6] = ['6', 'tradeInfo', 'NVAR', 'HEX', '2']
   
   #TODO: read and construct tradeInfo
   
   def read_tradeInfo(self, strcontent):
      #TODO: implement this
      raise RuntimeError("TODO: implement this")
      pass

   def construct_tradeInfo(self):
      #TODO: implement this
      raise RuntimeError("TODO: implement this")
      pass

class readICTradeResult(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备注
1   有效数据长度   N   HEX2   有效数据长度
2   原交易流水号   AN   BCD3   原交易流水号
3   原交易MAC   AN   BCD8   发生异常交易的上行MAC值
4   TC，脚本结果、TVR内容   VAR      本域采用TLV （tag-length-value ）的表示方式，即每个子域由 tag 标签索引(T)，子域取值的长度(L)和子域取值(V) 构成。

   """
   id = 74
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'tradeSeq', 'AN', 'BCD', '3']
   fields[3] = ['3', 'tradeMAC', 'AN', 'BCD', '8']
   fields[4] = ['4', 'tradeInfo', 'NVAR', 'HEX', '2']
   
   #TODO: read and construct tradeInfo
   
   def read_tradeInfo(self, strcontent):
      #TODO: implement this
      raise RuntimeError("TODO: implement this")
      pass

   def construct_tradeInfo(self):
      #TODO: implement this
      raise RuntimeError("TODO: implement this")
      pass
   
class ICPrintDataOrder(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备注
1   打印信息长度   N   HEX2   打印信息的长度
2   打印份数   N   HEX1   需要打印的份数
3   打印信息   VAR   ASC   打印记录信息
打印记录格式：
序号   字段名称   属性   类型   备注
1   打印控制符   AN3   ASC   %Bn表示第 n 份标题（第一行居中）； 
%FF 为正文； 
%En 表示第n 份落款（最后一行居中）； 
2   模板记录号   N1   HEX   指明使用的模板记录号(0x01 －0XFF) ，打印时，取出该号码对应记录号的打印信息内容替换
3   打印信息   VAR      打印信息若为“FFFF”，表示使用菜单显示内容替换
打印信息若为“EEEE”,则使用指定Tag内容替换。

   """
   id = 73
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   #fields[2] = ['2', 'printNumber', 'N', 'HEX', '1']
   fields[2] = ['2', 'printInfo', 'NVAR', 'ASC', '1']
   
   def read_printInfo(self, strcontent):
      #TODO: implement this
      raise RuntimeError("TODO: implement this")
      pass

   def construct_printInfo(self):
      #TODO: implement this
      raise RuntimeError("TODO: implement this")
      pass
   
class ICOnlineDataHandle(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备注
1   交易类型标识   N   HEX1   01表示IC卡数据处理;
02表示磁条卡数据处理
2   应答码   AN2   ASC   中心返回的处理代码
3   IC有效数据长度   N   HEX2   IC卡有效数据长度
4   IC有效数据内容   VAR      本域采用TLV （tag-length-value ）的表示方式，即每个子域由 tag 标签索引(T)，子域取值的长度(L)和子域取值(V) 构成。

   """
   id = 72
   fields = fixdict()
   
   fields[1] = ['1', 'tradeType', 'N', 'HEX', '1']
   fields[2] = ['2', 'retCode', 'AN', 'ASC', '2']
   fields[3] = ['3', 'validData', 'NVAR', 'ASC', '2']
   
class ICOnlineDataHandleResult(Pos3DirectiveMsg):
   """
序号   字段名称   属性   类型   备注
1   交易类型标识   N   HEX1   01表示IC卡数据处理;
02表示磁条卡数据处理
2   有效数据长度   N   HEX2   IC卡有效数据长度，磁条卡数据长度为0。
3   有效数据内容   VAR      本域采用TLV （tag-length-value ）的表示方式，即每个子域由 tag 标签索引(T)，子域取值的长度(L)和子域取值(V) 构成。

   """
   id = 72
   fields = fixdict()
   
   fields[1] = ['1', 'tradeType', 'N', 'HEX', '1']
   fields[2] = ['2', 'validData', 'NVAR', 'HEX', '2']
   
class ICSimplifyResult(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备注
1   交易类型标识   N   HEX1   01表示IC卡数据处理;
02表示磁条卡数据处理
2   有效数据长度   N   HEX2   指明以下有效数据字节数
3   有效数据   VAR      1.磁条卡交易：8个字节的密码密文
2.IC卡交易: IC卡相关有效数据本域采用TLV （tag-length-value ）的表示方式，即每个子域由 tag 标签索引(T)，子域取值的长度(L)和子域取值(V) 构成。当有密码时，需要通过99tag把密码密文上送

   """
   id = 69
   fields = fixdict()
   
   fields[1] = ['1', 'tradeType', 'N', 'HEX', '1']
   fields[2] = ['2', 'validData', 'NVAR', 'HEX', '2']
   

class ICExpandResult(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备注
1   交易类型标识   N   HEX1   01表示IC卡数据处理;
02表示磁条卡数据处理
2   有效数据长度   N   HEX2   指明以下有效数据字节数
3   有效数据   VAR      1.磁条卡交易：8个字节的密码密文
2.IC卡交易: IC卡相关有效数据本域采用TLV （tag-length-value ）的表示方式，即每个子域由 tag 标签索引(T)，子域取值的长度(L)和子域取值(V) 构成。

   """
   id = 68
   fields = fixdict()
   
   fields[1] = ['1', 'tradeType', 'N', 'HEX', '1']
   fields[2] = ['2', 'validData', 'NVAR', 'HEX', '2']
   

class cardReadOrderResult(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备注
1   读卡操作标识   N   HEX2   根据操作的情况填写
2   交易类型标识   N   HEX1   01表示IC卡数据处理;
02表示磁条卡数据处理
03 表示手输卡号
3   有效数据长度   N   HEX2   指明以下有效数据字节数
4   有效数据内容   VAR      1.若为IC卡交易,该有效数据为空。
2.若为刷卡,该有效数据为磁道数据，相当于04号指令。
3.若为手输，该有效数据为手输内容，相当于08号指令。

   """
   id = 67
   fields = fixdict()
   
   fields[1] = ['1', 'readOperationID', 'N', 'HEX', '2']
   fields[2] = ['2', 'tradeType', 'N', 'HEX', '1']
   fields[3] = ['3', 'validData', 'NVAR', 'HEX', '2']
   
class _terminalControlData(Pos3DirectiveMsg):
   id = 00
   fields = fixdict()
   
   fields[1] = ['1', 'controlType', 'N', 'HEX', '1']
   fields[2] = ['2', 'controlMethod', 'N', 'HEX', '1']
   fields[3] = ['3', 'controlData', 'NVAR', 'HEX', '1']

class terminalConsoleOrder(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备注
1   有效数据长度   N   HEX2   有效数据长度
2   控制条数   N   HEX1   控制类别条数
3   控制类别   N   HEX1   终端控制类别
4   控制方式   N   HEX1   控制方式
5   控制数据长度   N1   HEX1   控制数据长度
6   控制数据   VAR      控制数据

   """
   id = 64
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'controlList', 'NLIST', _terminalControlData, '1']
   
class downloadSalessplitTemplate(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备 注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   模板个数   N   HEX1   指明以下模板数
3

   模板ID   N   BCD4   指明打印模板ID
   有效数据长度   N   HEX2   指明有效信息内容字节数
   有效数据   VAR      
4   校验值         
有效数据内容：
序号   字段名称   属性   类型   备 注
1   IC卡标志   N   HEX1   指明当前指令是否需要打印在IC卡交易打印单上。0x00—所有打印单，0x01—只打印在IC卡打印单上。
2   指令   N   HEX1   用于打印的指令
3   指令输入数据   VAR      参照附录D

   """
   id = 62
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'templateNumber', 'N', 'HEX', '1']
   fields[3] = ['3', 'templateID', 'N', 'BCD', '4']
   fields[4] = ['4', 'validData', 'NVAR', 'HEX', '2']
   fields[5] = ['5', 'parityBit', 'N', 'HEX', '1']
   
class uploadBasestationMsg(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备注
1   有效数据长度   N2   HEX   指明以下有效数据字节数
2   基站总数   N   HEX   附近基站的总个数,若为0，则表示没有基站信息
3   基站详细信息   N   HEX   

基站详细信息如下：
序号   字段名称   属性   类型   备注
1   基站序号   N   HEX1    
2   信息长度   N   HEX1   此条基站信息的长度
3   本地区域号(Lac)   N   HEX2    
4   小区号(cell_id)   N   HEX2    
5   基站识别码(bsic)   N   HEX2    
6   国家代码(mcc)   N   HEX2    
7   移动网号(mnc)   N   HEX1    
8   载波号(bcch)   N   HEX2    
9   csq   N   HEX1   可以根据这个值来算出信号强度

   """
   id = 60
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'basestationInfo', 'NVAR', 'HEX', '1']
   
   #TODO: read basestation info to list
   def read_basestationInfo(self, strcontent):
      #TODO: implement this
      raise RuntimeError("TODO: implement this")
      pass
   
   def construct_basestationInfo(self):
      #TODO: implement this
      raise RuntimeError("TODO: implement this")
      pass
   
class updateErrMsg(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备 注
1   有效数据长度   N2   HEX   指明以下有效数据字节数
2   信息记录数   N1   HEX   指明以下记录条数
3   提示信息索引   N1   HEX   指明提示信息的记录位置
4   信息操作标志   N1   ASC   0表示不可用，1表示可用
5   提示信息长度   N1   HEX   指明有效提示信息字节数
6   信息内容模板   an   ASC   
信息内容模板格式：
序号   字段名称   属性   类型   备 注
1   模板数   N1   HEX   指明以下记录数（1－3）注1
2   信息显示格式   N2   BCD1   参照0x1A指令注2
3   信息内容长度   N1   HEX   
4   信息内容   VAR      参照0x1A指令注3

   """
   id = 59
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'recordNumber', 'N', 'HEX', '1']
   fields[3] = ['3', 'recordIndex', 'N', 'HEX', '1']
   fields[4] = ['4', 'recordOPFlag', 'N', 'ASC', '1']
   fields[5] = ['5', 'templateInof', 'NVAR', 'HEX', '1']
   
class dynamicTradeMenu(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备 注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   标题   N   ASC   菜单标题/选择标题
3   分隔符   N   HEX1   用以分隔数据，取值为0xff
4   总项数      HEX1   菜单总项数/选择总项数
5   分隔符      HEX1   用以分隔数据，取值为0xff
6   选项1      ASC   菜单1/选项1
7   分隔符      HEX1   用以分隔数据，取值为0xff
8   ……         ………
9   分隔符      HEX1   用以分隔数据，取值为0xff
10   选项N      ASC   菜单N/选项N
11   分隔符      HEX1   用以分隔数据，取值为0xff

   """
   id = 58
   fields = fixdict()
   
   fields[1] = ['1', 'validLength', 'N', 'HEX', '2']
   fields[2] = ['2', 'menuTitle', 'N', 'ASC', '10']
   fields[3] = ['3', 'menuData', 'NVAR', 'ASC', '1']
   
   def read_menuData(self, strcontent):
      #TODO: implement this
      raise RuntimeError("TODO: implement this")
      pass
   
   def construct_menuData(self):
      #TODO: implement this
      raise RuntimeError("TODO: implement this")
      pass
   
class searchOriginalTrade(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备 注
2   输入数据类型   N1   BCD   01流水号，02授权码，（根据下发顺序表示）
3   最小长度   N1   HEX   限制输入数据的最小长度
4   最大长度   N1   HEX   限制输入数据的最大长度

   """
   id = 55
   fields = fixdict()
   
   fields[1] = ['1', 'dataType', 'N', 'BCD', '1']
   fields[2] = ['2', 'minLength', 'N', 'HEX', '1']
   fields[3] = ['3', 'maxLength', 'N', 'HEX', '1']

class searchOriginalTradeResult(Pos3DirectiveMsg):
   """
      输出数据格式：返回码（1个字节HEX，0x00查询成功，0x01查询失败） + 1个字节输入数据长度+ 输入数据
   """
   id = 55
   fields = fixdict()
   
   fields[1] = ['1', 'resultCode', 'N', 'HEX', '1']
   fields[2] = ['2', 'searchResult', 'NVAR', 'HEX', '1']
   
class singleSelectOptions(Pos3DirectiveMsg):
   """
    序号   字段名称   属性   类型   备 注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   标题内容长度   N   HEX1   标题内容长度
3   标题内容   VAR      标题
4   总项数   N   HEX1   总项数/选择总项数
5   选项1内容长度   N   HEX1   选项1内容长度
6   选项1内容   VAR      选项1内容
7   选项2内容长度   N   HEX1   选项2内容长度
8   选项2内容   VAR      选项2内容
9   选项3内容长度   N   HEX1   选项3内容长度
10   选项3内容   VAR      选项3内容
   …         
1   选项内容长度   N   HEX1   选项内容长度
2   选项内容   VAR      选项内容

   """
   id = 54
   fields = fixdict()
   
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'titleContent', 'NVAR', 'HEX', '1']
   fields[3] = ['3', 'options', 'NVAR', 'HEX', '1']
   
   def read_options(self, strcontent):
      offset = 0
      optioncount = int(strcontent[offset:offset+2], 16)
      offset += 2
      options = []
      for i in range(optioncount):
         length, value = self._read_option(strcontent[offset:])
         offset += length
         options.append(value)
      
      self.setField("options", options)
      
      return offset

   def _read_option(self, strcontent):
      offset = 0
      length = 2
      datalen = int(strcontent[offset:offset+2], 16)*2
      value = strcontent[offset+length:offset+length+datalen]
      return length+datalen, value

   def construct_options(self):
      options = self.getField('options')      
      msg = toHex(len(options)).zfill(2)
      for option in options:
         msg += self._construct_option(option)
      
      return msg
      
   def _construct_option(self, datavalue):
      msg = ''
      datalen = 2
      validlen = hex(len(datavalue)+1/2)[2:]
      msg += validlen.zfill(datalen)
      if len(datavalue) % 2 == 0:
         msg += datavalue
      else:
         msg += '0' + datavalue
      return msg
     

class terminalBalance(Pos3DirectiveMsg):
   """
      序号   字段名称   属性   类型   备 注
1   内卡借计金额   N   BCD6   结算内容
2   内卡借计笔数   N2   HEX   
3   内卡贷计金额   N   BCD6   
4   内卡贷计笔数   N2   HEX   
5   外卡借计金额   N   BCD6   
6   外卡借计笔数   N2   HEX   
7   外卡贷计金额   N   BCD6   
8   外卡贷计笔数   N2   HEX


   """
   id = 53
   fields = fixdict()
   
   fields[1] = ['1', 'innerDebitAmount', 'N', 'BCD', '6']
   fields[2] = ['2', 'innerDebitCount', 'N', 'HEX', '2']
   fields[3] = ['3', 'innerCreditAmount', 'N', 'BCD', '6']
   fields[4] = ['4', 'innerCreditCount', 'N', 'HEX', '2']
   fields[5] = ['5', 'outerDebitAmount', 'N', 'BCD', '6']
   fields[6] = ['6', 'outerDebitCount', 'N', 'HEX', '2']
   fields[7] = ['7', 'outerCreditAmount', 'N', 'BCD', '6']
   fields[8] = ['8', 'outerCreditCount', 'N', 'HEX', '2']

class _tradeDetail(Pos3DirectiveMsg):
   id = 00
   fields = fixdict()
   
   fields[1] = ['1', 'tradeType', 'N', 'HEX', '1']
   fields[2] = ['2', 'cardType', 'N', 'HEX', '1']
   fields[3] = ['3', 'cancelFlag', 'N', 'HEX', '1']
   fields[4] = ['4', 'tradeName', 'NVAR', 'ASC', '1']
   fields[5] = ['5', 'cardNumber', 'N', 'BCD', '10']
   fields[6] = ['6', 'sequenceNumber', 'N', 'BCD', '3']
   fields[7] = ['7', 'authNumber', 'N', 'ASC', '6']
   fields[8] = ['8', 'systemRefNumber', 'N', 'ASC', '12']
   fields[9] = ['9', 'tradeAmount', 'N', 'BCD', '6']
   fields[10] = ['10', 'tradeTime', 'N', 'BCD', '7']
   fields[11] = ['11', 'tradeInfo', 'NVAR', 'ASC', '1']

class saveTradeDetail(Pos3DirectiveMsg):
   """
    序号   字段名称   属性   类型   备 注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   明细记录数   N   HEX1   指明以下记录条数
3   借贷标志   N   HEX1   0：非借非贷 
1：借（消费） 
2：贷（撤消）
4   外卡标志   N   HEX1   0：未知 1：内卡 2：外卡
5   是否可撤销   N   HEX   0x00-可撤销，0x01-已撤销，0x02-通知类交易不可撤销
6   交易名称长度   N   HEX1   
7   交易名称   An   ASC   
8   主账号   N   BCD10   压缩BCD码，右补F
9   流水号   N   BCD3   
10   授权码   N   ASC6   
11   系统参考号   N   ASC12   
12   金额   N   BCD6   前补0
13   时间   N   BCD7   YYYYMMDDHHNNSS
14   信息长度   N   HEX1   
15   信息内容   N   ASC   

   """
   id = 52
   fields = fixdict()
   
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'recordList', 'NLIST', _tradeDetail, '1']
   
   #TODO: Cardnumber read and write
   #TODO: this is a record list
   
#    def read_cardNumber(self, strcontent):
#       pass
#      
#    def construct_cardNumber(self):
#       pass

class updateTerminalAppVersion(Pos3DirectiveMsg):
   """
   序号   字段名称   属性   类型   备 注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   版本号更新数量   N   HEX1   指明以下记录条数
3   版本号类型   N   HEX1   0-   应用版本号
1-   IC版本号
4   版本号内容长度   N   HEX1   版本号内容长度
5   版本号内容   VAR   HEX   

   """
   id = 51
   fields = fixdict()
   
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'recordNumber', 'N', 'HEX', '1']
   fields[3] = ['3', 'versionType', 'N', 'HEX', '1']
   fields[4] = ['4', 'version', 'NVAR', 'HEX', '1']
   
class updateMenuLevel(Pos3DirectiveMsg):
   """
   序号   字段名称   属性   类型   备 注
1   有效数据长度   N   HEX2   指明以下有效数据字节数
2   菜单记录数   N   HEX2   指明以下记录条数
3   菜单级别   AN   HEX2   注2 
4   交易代码   AN   BCD3   终端不作处理，交易时提交中心
5   是否加入缺省交易列表   N   HEX1   0x00-不加入，0x01-加入

   """
   id = 51
   fields = fixdict()
   
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'recordNumber', 'N', 'HEX', '2']
   fields[3] = ['3', 'menuLevel', 'AN', 'HEX', '2']
   fields[4] = ['4', 'tradeCode', 'AN', 'BCD', '3']
   fields[5] = ['5', 'defaultListFlag', 'N', 'HEX', '1']
   
class comCommunication(Pos3DirectiveMsg):
   """
    序号   字段名称   属性   类型   备 注
1   超时时长   N1   HEX   超时时长不为0时，终端等待串口返回，直到超时。如无数据返回，输出数据为0，如超时时长为0，此指令无输出数据。
2   有效数据长度   N2   HEX2   
3   有效数据内容   VAR   ASC   

   """
   id = 47
   fields = fixdict()
   
   fields[1] = ['1', 'timeout', 'N', 'HEX', '1']
   fields[2] = ['2', 'validDate', 'NVAR', 'ASC', '2']

class comCommunicationResult(Pos3DirectiveMsg):
   """
    序号   字段名称   属性   类型   备 注
1   超时时长   N1   HEX   超时时长不为0时，终端等待串口返回，直到超时。如无数据返回，输出数据为0，如超时时长为0，此指令无输出数据。
2   有效数据长度   N2   HEX2   
3   有效数据内容   VAR   ASC   

   """
   id = 47
   fields = fixdict()
   
   fields[1] = ['1', 'timeout', 'N', 'HEX', '1']
   fields[2] = ['2', 'validDate', 'NVAR', 'ASC', '2']
   
class onlineTradeConfirm(Pos3DirectiveMsg):
   """
    序号   字段名称   属性   类型   备 注
1   有效数据长度   N2   HEX   
2   时间控制   N1   HEX   00—无限等待确认键，\x01-FF—等待时限
3   信息内容长度   N2   HEX   指明以下有效数据字节数
4   信息内容   VAR   ASC   

   """
   id = 44
   fields = fixdict()
   
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'timeout', 'N', 'HEX', '1']
   fields[3] = ['3', 'tradeInfo', 'NVAR', 'HEX', '2']
   

#####
class trackCipherText (Pos3DirectiveMsg):
   """
   1字节HEX长度值（最大88）＋ 二、三磁道密文数据+加密参数（4字节）。[加密参数为随机数]
   """
   id = 4
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'NVAR', 'BCD', '1']
         
class tradeAmountFormat(Pos3DirectiveMsg):
   """
   1   操作标识   N   HEX1   0-可以更改　　1-只读
   2   小数点位数   N   HEX1   指明小数点后的位数
   3   回显数值   N   BCD6   初始回显数值
   4   最小数值   N   BCD6   输入的最小数值
   5   最大数值   N   BCD6   输入的最大数值
   6   输密码是否回显金额   N   HEX1   输密码时是否在PINPAD上回显金额，1-回显　0-不回显
   7   是否填充9F02   N   HEX1   输入是否填充TAG 9F02 1：填充 0：不填充
   """
   id = 7
   fields = fixdict()
   fields[1] = ['1', 'operateId', 'N', 'HEX', '1'] 
   fields[2] = ['2', 'radixPoint', 'N', 'HEX', '1']
   fields[3] = ['3', 'echoNum', 'N', 'BCD', '6']
   fields[4] = ['4', 'maxNum', 'N', 'BCD', '6']
   fields[5] = ['5', 'minNum', 'N', 'BCD', '6']
   fields[6] = ['6', 'ifEcho', 'N', 'HEX', '1']
   fields[7] = ['7', 'if9F02', 'N', 'HEX', '1']

class bankAppNumber(Pos3DirectiveMsg):
   """
   1字节HEX长度＋有效数据（最长40字节）
   """
   id = 8
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'NVAR', 'BCD', '1']
   
class businessAppNumber(Pos3DirectiveMsg):
   """
   1字节HEX长度＋有效数据
   """
   id = 9
   fields = fixdict()
   fields[1] = ['1', 'readBusiness', 'NVAR', 'HEX', '1']
   
class customFormat(Pos3DirectiveMsg):
   """
   1   有效数据长度   N   HEX2   指明以下有效数据长度
   2   操作标识   N   HEX1   0-可以更改　　1-只读
   3   最小长度   N   HEX1   指明最小输入数据长度
   4   最大长度   N   HEX1   指明最大输入数据长度
   5   输入法类型   N   HEX1   1—数字，2-数字+字母+特殊字符，3—全部输入法
   6   默认输入法   N   HEX   1--数字、2--小写字母、3--大写字母、4--T9拼音、5--特殊字符、6--笔画输入法、7--区位码、
   7   回显数据长度   N   HEX1   
   8   回显数据   VAR   ASC   
   """
   id = 12
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'operateId', 'N', 'HEX', '1']
   fields[3] = ['3', 'minLen', 'N', 'HEX', '1']
   fields[4] = ['4', 'maxLen', 'N', 'HEX', '1']
   fields[5] = ['5', 'typewriting', 'N', 'HEX', '1']
   fields[6] = ['6', 'defaultTypewriting', 'N', 'HEX', '1']
   fields[7] = ['7', 'echoLen', 'NVAR', 'ASC', '1']
   
class customData(Pos3DirectiveMsg):
   """
   1字节HEX长度＋有效数据
   """
   id = 12
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'NVAR', 'HEX', '1']
   
   
class correctionMsg(Pos3DirectiveMsg):
   """
   1   有效数据长度   N1   HEX   
   2   交易流水   N3   BCD3   流水号
   3   交易MAC   N8   HEX   
   4   TAG记录内容   VAR      本域采用TLV （tag-length-value ）的表示方式。若为发卡行认证失败的冲正则要上送95和9F10。 若为一般冲正，该域为空。
   """
   id = 15
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '1']
   fields[2] = ['2', 'tradeList', 'N', 'BCD', '3']
   fields[3] = ['3', 'tradeMAC', 'N', 'HEX', '8']
   
class terminalAppVersion(Pos3DirectiveMsg):
   """
   1   版本号类型   N   HEX1   0-应用版本号　　1-IC卡应用版本号
   2   版本号内容长度   N   HEX1   
   3   版本号内容   VAR   BCD
   """
   id = 17
   fields = fixdict()
   fields[1] = ['1', 'versionType', 'N', 'HEX', '1']
   fields[2] = ['2', 'versionLen', 'NVAR', 'BCD', '1']
   
class updateElecSignature(Pos3DirectiveMsg):
   """
   1   原交易流水号   BCD3   BCD   电子签名压缩图片名为流水号
   2   原交易MAC   N8   HEX   交易MAC 
   3   电子签名数据长度   N2   HEX   电子签名数据长度
   4   电子签名数据   VAR      电子签名压缩数据  见注1 
   """
   id = 19
   fields = fixdict()
   fields[1] = ['1', 'originalSerial', 'N', 'BCD', '3'] 
   fields[2] = ['2', 'originalMAC', 'N', 'HEX', '8'] 
   fields[3] = ['3', 'SignatureLen', 'NVAR', 'HEX', '2'] 
   
class getElecSignature(Pos3DirectiveMsg):
   """
   1   电子签名数据长度   N2   HEX   电子签名数据长度
   2   电子签名数据   VAR      电子签名压缩数据
   """
   id = 21
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'NVAR', 'HEX', '1']

class updatePasswordKeywork(Pos3DirectiveMsg):
   """
   1   有效数据长度   N2   HEX   指明以下有效数据字节数
   2   参数记录数   N1   HEX   指明以下记录条数
   3   参数记录号   N1   HEX   密码键盘中记录号 01－32
   4   参数有效数据长度   N1   HEX   
   5   参数有效数据   An   ASC
   """
   id = 23
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']   
   fields[2] = ['2', 'parameList', 'N', 'HEX', '1']
   fields[3] = ['3', 'paramNum', 'N', 'HEX', '1']
   fields[4] = ['4', 'paramDataLen', 'ANVAR', 'ASC', '1']
   
class updateMenuParameter(Pos3DirectiveMsg):   
   """
   1   有效数据长度   N   HEX2   指明以下有效数据字节数
   2   处理模式   N   ASC1   注1
   3   菜单记录数   N   HEX1   指明以下记录条数
   4   菜单操作标志   N   ASC1   0表示不可用，1表示可用
   5   交易代码   AN   BCD3   终端不作处理，交易时提交中心
   6   冲正标识   N   ASC1   注3
   7   功能提示索引   N   HEX1   0表示无提示，其他指明提示信息位置
   8   中心号码序号   N   ASC1   
   9   流程代码长度   N   HEX1   参见第9节：流程代码说明
   10   流程代码   VAR      
   11   有效数据长度   N   HEX2   （终端暂定有效数据最大长度为512） 
   12   有效数据   VAR      
   13   显示内容长度   N   HEX1   
   14   显示内容   An   ASC   
   """
   id = 24
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'porcessingMode', 'N', 'ASC', '1']
   fields[3] = ['3', 'menuNum', 'N', 'HEX', '1']
   fields[4] = ['4', 'menuOperate', 'N', 'ASC', '1']
   fields[5] = ['5', 'tradeNum', 'N', 'BCD', '3']
   fields[6] = ['6', 'correction', 'N', 'ASC', '1']
   fields[7] = ['7', 'funcPoint', 'N', 'HEX', '1']
   fields[8] = ['8', 'centerNum', 'N', 'ASC', '1']
   fields[9] = ['9', 'flowLen', 'NVAR', 'ASC', '1']
   fields[10] = ['10', 'validDataLen', 'NVAR', 'ASC', '2']
   fields[11] = ['11', 'printData', 'ANVAR', 'ASC', '1']

class updateFuncPromptMsg(Pos3DirectiveMsg):
   """
   1   有效数据长度   N   HEX2   指明以下有效数据字节数
   2   信息记录数   N   HEX1   指明以下记录条数
   3   提示信息索引   N   HEX1   指明提示信息的记录位置
   4   信息操作标志   N   ASC1   0表示不可用，1表示可用
   5   信息内容长度   N   HEX1   指明有效信息内容字节数
   6   信息内容模板   VAR      
   """
   id = 25
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'msgNum', 'N', 'HEX', '1']
   fields[3] = ['3', 'msgIndex', 'N', 'HEX', '1']
   fields[4] = ['4', 'msgOperate', 'N', 'ASC', '1']
   fields[5] = ['5', 'templateMsg', 'NVAR', 'HEX', '1']
   #TODO: read the template info
   #fields[6] = ['6', 'msgContentTemplate', msgContentTemplate, '', '']
   
# class msgContentTemplate(Pos3DirectiveMsg):
#    """
#    1   模板数   N1   HEX   指明以下记录数（1－3）注1
#    2   信息显示格式   N2   BCD1   注2
#    3   信息内容长度   N1   HEX   
#    4   信息内容   VAR      
#    """
#    id = 25
#    fields = fixdict()
#    fields[1] = ['1', 'templateNum', 'N', 'HEX', '1']
#    fields[2] = ['2', 'msgFormat', 'N', 'BCD', '1']
#    fields[3] = ['3', 'msgLen', 'NVAR', 'HEX', '1']

class updateOperationMsg(Pos3DirectiveMsg):
   """
   1   有效数据长度   N2   HEX   指明以下有效数据字节数
   2   信息记录数   N1   HEX   指明以下记录条数
   3   提示信息索引   N1   HEX   指明提示信息的记录位置
   4   信息操作标志   N1   ASC   0表示不可用，1表示可用
   5   提示信息长度   N1   HEX   指明有效提示信息字节数
   6   信息内容模板   An   ASC   
   """
   id = 26
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'msgNum', 'N', 'HEX', '1']
   fields[3] = ['3', 'msgIndex', 'N', 'HEX', '1']
   fields[4] = ['4', 'msgOperate', 'N', 'ASC', '1']
   fields[5] = ['5', 'templateMsg', 'NVAR', 'HEX', '1']
   #TODO: read template info
   #fields[6] = ['6', 'updateMsgContentTemplate', updateMsgContentTemplate, '', '']
   
# class updateMsgContentTemplate(Pos3DirectiveMsg):
#    """
#    1   模板数   N1   HEX   指明以下记录数（1－3）注1
#    2   信息显示格式   N2   BCD1   注2
#    3   信息内容长度   N1   HEX   
#    4   信息内容   VAR      
#    """
#    id = 26
#    fields = fixdict()
#    fields[1] = ['1', 'templateNum', 'N', 'HEX', '1']
#    fields[2] = ['2', 'msgFormat', 'N', 'BCD', '1']
#    fields[3] = ['3', 'msgLen', 'NVAR', 'HEX', '1']   
   
class updateHomePage(Pos3DirectiveMsg):
   """
   1   有效数据长度   N2   HEX   指明以下有效数据字节数
   2   有效信息内容   An   ASC    
   """
   id = 27
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'ANVAR', 'ASC', '1']   
   
class updatePrintTemplate(Pos3DirectiveMsg):
   """
   1   有效数据长度   N2   HEX   指明以下有效数据字节数
   2   模板记录数   N1   HEX   指明以下记录条数
   3   记录编号   N1   HEX   打印记录编号(0x01-0XFF)，0X00表示用菜单显示内容替换 注1
   4   打印信息长度   N1   HEX   
   5   打印信息内容   An   ASC   
   """
   id = 28
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'formatNum', 'N', 'HEX', '1']
   fields[3] = ['3', 'recordNum', 'N', 'HEX', '1']
   fields[4] = ['4', 'printLen', 'ANVAR', 'ASC', '1']
   
class readSigninName(Pos3DirectiveMsg):
   """
   1字节HEX长度＋有效数据
   """
   id = 30
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'NVAR', 'HEX', '1']         
   
class searchExchangeRate(Pos3DirectiveMsg):
   """
   1   有效数据长度   N   HEX2
   2   币种标识1长度   N   HEX
   3   币种标识1   Ans   ASC
   4   币种标识2长度   N   HEX
   5   币种标识2   Ans   ASC
   """
   id = 31
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'currency', 'N', 'HEX', '1']
   fields[3] = ['3', 'currency2', 'ANVAR', 'ASC', '1']   
   
class searchExchangeRateResult(Pos3DirectiveMsg):
   """
   1   有效数据长度   N   HEX2
   2   币种标识1长度   N   HEX
   3   币种标识1   Ans   ASC
   4   币种标识2长度   N   HEX
   5   币种标识2   Ans   ASC
   """
   id = 31
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'currency', 'N', 'HEX', '1']
   fields[3] = ['3', 'currency2', 'ANVAR', 'ASC', '1']   
   
class updateSaleSlip(Pos3DirectiveMsg):
   """
   1   原交易流水   BCD3   BCD    原交易流水
   2   原交易MAC   N8   HEX   原交易MAC
   3   签购单信息域长度   N2   HEX2   签购单信息域长度
   4   签购单信息   VAR      本域采用TLV （tag-length-value ）的表示方式。具体包括的TAG见附录D中的IC卡TAG记录。        见注2
   """
   id = 32
   fields = fixdict()
   fields[1] = ['1', 'trade', 'N', 'BCD', '3']
   fields[2] = ['2', 'tradeMAC', 'N', 'HEX', '8']
   fields[3] = ['3', 'dataLen', 'N', 'HEX', '2']   
   
class printDate(Pos3DirectiveMsg):
   """
   1      打印信息长度   N   HEX2   指明打印信息的字节数
   2      凭单特征标识   N   HEX1   用于标识凭单特征：
   0x01－交易凭条　
   0x02－结算单　
   0x03－非存储的打印凭条
   3      打印份数   N   ASC1   
   4      打印信息   VAR      注1
   """
   id = 33
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'print', 'N', 'HEX', '1']
   fields[3] = ['3', 'printNum', 'NVAR', 'ASC', '1']
   
class showReultMsg(Pos3DirectiveMsg):
   """
   1      有效数据长度   N2   HEX   以下所有有效数据长度字节数
   2      刷新方式   N1   ASC   指明自动返回待机状态或等待接收下一报文时屏幕的刷新方式，0表示不刷新不显示首页信息，1表示刷新后显示首页信息或提示信息。
   3      显示时间   N1   HEX   控制超时，时间到了自动执行下一条指令。0表示无限等待确认，1-FF表示显示等待确认时间，单位：秒。
   4      应答码   AN2   ASC   中心返回的处理代码
   5      应答信息长度   N1   HEX   指明应答信息的字节数
   6      应答信息   VAR   ASC   
   7      PINPAD显示信息1长度   N1   HEX   指明PINPAD的显示信息1的字节数
   8      PINPAD显示信息1   VAR   ASC   
   9   主机 显示信息2长度   N1   HEX   指明主机 的显示信息2的字节数
   10   主机 显示信息2   VAR   ASC   
   """
   id = 34
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'refreshMode', 'N', 'ASC', '1']
   fields[3] = ['3', 'showTime', 'N', 'HEX', '1']
   fields[4] = ['4', 'responseCode', 'N', 'ASC', '2']
   fields[5] = ['5', 'responseMsg', 'NVAR', 'ASC', '1']
   fields[6] = ['6', 'PINPADShowMsg', 'NVAR', 'ASC', '1']
   fields[7] = ['7', 'hostShowMsg', 'NVAR', 'ASC', '2']
   
class checkMAC(Pos3DirectiveMsg):
   """
   """
   #TODO: this field is not defined in the document
   id = 40
   fields = fixdict()
   fields[1] = ['1', 'msgContent', 'NVAR', 'HEX', '1']
   
   
class printSalesslipTemplate(Pos3DirectiveMsg):
   """
   1      打印信息长度   N   HEX2   指明打印信息的字节数
   2      打印模板编号   N   BCD4   指明使用的模板编号
   3      凭单特征标识   N   HEX1   用于标识凭单特征：
   0x01－交易凭条　
   0x02－结算单　
   0x03－非存储的打印凭条
   4      打印份数   N   ASC1   指明打印的份数
   5      打印联数顺序   VAR   ASC   长度跟打印份数保持一致，顺序由后台统一指定。
   6      IC卡标志   N   HEX1   是否为IC卡打印。0x00—非IC卡交易打印，0x01—IC卡交易打印
   7      TLV个数   N   HEX1   
   8      打印TLV数据   VAR      TLV数据 
   """
   id = 41
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'templateNum', 'N', 'BCD', '4']
   fields[3] = ['3', 'salesId', 'N', 'HEX', '1']
   fields[4] = ['4', 'printSeq', 'N', 'HEX', '1']
   fields[5] = ['5', 'copyNum', 'NVAR', 'ASC', '1']
   fields[6] = ['6', 'ifIC', 'N', 'HEX', '1']
   fields[7] = ['7', 'TLVList', 'NLIST', TLVField, '1']   

class checkIdentifyingCode(Pos3DirectiveMsg):
   """
   序号   字段名称   属性   类型   备 注
1   有效数据长度   N   HEX2   
2   输入超时时间   N   HEX1   等待输入的超时时间
3   验证次数   N   HEX1   输入允许次数
4   小数点位数   N   HEX1   指明小数点后的位数
5   输入法类型   N   HEX1   1—金额（短信认证），2-数字+字母+特殊字符，3—全部输入法
6   默认输入法   N   HEX   1--数字、2--小写字母、3--大写字母、4--T9拼音、5--特殊字符、6--笔画输入法、7--区位码、
7   最小输入长度   N   HEX1   输入的最小数值
8   最大输入长度   N   HEX1   输入的最大数值
9   验证数据长度   N   HEX1   待校验密文数据长度
10   验证数据密文   VAR   ASC   TDK加密后的待校验密文数据

   """
   id = 43
   fields = fixdict()
   fields[1] = ['1', 'validLegth', 'N', 'HEX', '2']
   fields[2] = ['2', 'timeout', 'N', 'HEX', '1']
   fields[3] = ['3', 'verifyCount', 'N', 'HEX', '1']
   fields[4] = ['4', 'decimalPoint', 'N', 'HEX', '1']
   fields[5] = ['5', 'inputType', 'N', 'HEX', '1']
   fields[6] = ['6', 'defaultInputType', 'N', 'HEX', '1']      
   fields[7] = ['7', 'minLength', 'N', 'HEX', '1']      
   fields[8] = ['8', 'maxLength', 'N', 'HEX', '1']   
   fields[9] = ['9', 'verifyData', 'NVAR', 'ASC', '1']   


if __name__ == '__main__':
   data = '009200000001010100000c0f5204d6d0b9fa0f510f3834393434303335333131363033310f530838303031343039390f600230311f2108c5a9d2b5d2f8d0d09f010830313033303030301f120b3242454243304531422f530f150530392f33301f1304cffbb7d11f170c3132333435363738393031321f1513323031342f31302f31312031353a30303a30301f180535352e353500113002303009bdbbd2d7b3c9b9a620000000000c030100000c00000d00020101f9eca75906294c1005'
   ret = printSalesslipTemplate(data)
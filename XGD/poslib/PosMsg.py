#-*- coding: utf-8 -*-
"""

(C) Copyright 2004 wei_cloud@126.com

"""

from PosMsgBase import *

class Pos3Msg(Pos3MsgBase):
   fields = fixdict()
   
   #序号， 名称， 属性， 类型， 长度，请求，应答， 备注
   fields[1] = ['1', 'msgLength', 'N', 'HEX', '2', True, True, '数据长度']
   fields[2] = ['2', 'TPDU', 'AN', 'HEX', '5', True, True, '该域，不作为报文有效数据']
   fields[3] = ['3', 'msgType', 'AN', 'HEX', '1', True, True, '0X87为终端发送 0X84为中心发送']
   fields[4] = ['4', 'transactionRandId', 'AN', 'HEX', '4', True, True, '由请求方随机产生，在整个会话过程中保持不变']
   fields[5] = ['5', 'syncSerialNumber', 'N', 'HEX', '1', True, True, '请求方第一个请求报文为1，响应方原样回送，再次请求时按步长为1递增']
   fields[6] = ['6', 'merchantId', 'AN', 'ASC', '15', True, True, '商户唯一标识']
   fields[7] = ['7', 'terminalId', 'AN', 'ASC', '8', True, True, '终端唯一标识']
   fields[8] = ['8', 'reserved', 'N', 'AN', '2', True, True, '']
   fields[9] = ['9', 'failedTimes', 'N', 'HEX', '1', True, True, '上一次建链成功到这次建链成功，中间建链失败次数']
   fields[10] = ['10', 'terminalProperty', 'N', 'N', '1', True, True, '前0-3位表示通信方式（1-有线、2-无线、3-网络），第4位表示打印方式（0-针打、1-热敏）']
   fields[11] = ['11', 'ICVersion', 'N', 'N', '4', True, True, '']
   #fields[12] = ['12', '消息内容长度', 'N', 'HEX', '2', True, True, '']
   fields[12] = ['13', 'content', 'NVAR', 'HEX', '2', True, True, '']
   fields[13] = ['14', 'parityBit', 'AN', 'HEX', '1', True, True, '基于通讯协议的校验算法']
   
   def setField(self, fieldId, value):
      try:
         Pos3MsgBase.setField(self, fieldId, value)
      except FieldNonExistError:
         if type(self.content) != str:
            self.content.setField(fieldId, value)
         else:
            raise
   
   def readFromString(self, strcontent):
      offset = Pos3MsgBase.readFromString(self, strcontent)
      logger.debug("===content before parse:"+ self.content)
      self.content = PosTradeMSG(self.msgType, self.content, debug=self.DEBUG)   
      
      return offset
   
   def constructMsg(self, force=False):
      Pos3MsgBase.constructMsg(self, force)
       #Add parityBit
      if self.fields and self.getName(self.fields.keys()[-1]) == 'parityBit':       
         datalen = self.getLength(self.fields.keys()[-1])  
         self.msg += toHexstr(calcParityBit(self.msg[self.getLength(2):])).zfill(datalen)
            
      #Add Length
      if self.fields and self.getName(self.fields.keys()[0]) == 'msgLength':
         datalen = self.getLength(self.fields.keys()[0])
         datavalue = self.getField(self.fields.keys()[0])
         if not force:
            datavalue = hex(len(self.msg)/2)[2:]
         self.msg = datavalue.zfill(datalen) + self.msg
      
      return self.msg
      
   def getField(self, fieldId):
      try:
         return Pos3MsgBase.getField(self, fieldId)
      except FieldNonExistError:
         if type(self.content) != str:
            return self.content.getField(fieldId)
         else:
            raise   
   
   def getShowFlag(self, fieldId):
      if self.msgType == '87':
         return self.fields[fieldId][5]
      else:
         return self.fields[fieldId][6]
   
class PosTradeMSG(Pos3MsgBase):
   
   fields = fixdict()
   
   #序号， 名称， 属性， 类型， 长度，终端，中心， 备注
   fields[1] = ['1', 'contentType', 'AN', 'HEX', '1', True, True, '']
   fields[2] = ['2', 'endFlag', 'N', 'HEX', '1', True, True, '结束标志（同一交易代码）0表示结束，n表示后续数据包数量']
   fields[3] = ['3', 'version', 'N', 'BCD', '2', True, False, '0x30 0x01']
   fields[4] = ['4', 'appVersion', 'N', 'BCD', '4', True, False, '终端保存的版本号原样上送']
   fields[5] = ['5', 'date', 'N', 'BCD', '4', False, True, '终端收到中心应答的系统日期和时间后，使用该值更新终端日期时间（更新方法可根据终端当时状态确定）']
   fields[6] = ['6', 'time', 'N', 'BCD', '3', False, True, '终端收到中心应答的系统日期和时间后，使用该值更新终端日期时间（更新方法可根据终端当时状态确定）']
   fields[7] = ['7', 'batchNo', 'N', 'BCD', '3', True, True, '中心根据判断程序版本是否大于“\x31\x02”（包含\x31\x02）来确定是否有“7.交易批次号”和“8.预留”两项，']
   fields[8] = ['8', 'tradeReserved', 'AN', 'BCD', '20', True, True, '中心根据判断程序版本是否大于“\x31\x02”（包含\x31\x02）来确定是否有“7.交易批次号”和“8.预留”两项，']
   fields[9] = ['9', 'voucherNo', 'N', 'BCD', '3', True, True, '当MAC值不为“0X00”时，终端应检查应答与请求是否一致']
   fields[10] = ['10', 'tradeCode', 'AN', 'ASC', '3', True, True, '若为初始请求，则填写终端中保存的交易代码；若为收到中心应答后的再次提交，则填写从中心返回的交易代码']
   fields[11] = ['11', 'operationCode', 'NVAR', 'HEX', '1', True, True, '由多个操作码组成']
   #msgfields[11] = ['11', '有效数据长度', 'AN', 'HEX', '2', True, True, '有效数据长度包括（有效数据域+MAC）的总长度']
   fields[12] = ['12', 'operationData', 'ANVAR', 'HEX', '2', True, True, '根据指令代码集确定']
   fields[13] = ['13', 'MAC', 'AN', 'BCD', '8', True, True, '不包含在有效数据长度内（与规范实现不一致）']
   
   def __init__(self, msgType, msg='', debug=False):
      """
      msgType = '87' or '84'
      """
      self.msgType = msgType
      Pos3MsgBase.__init__(self, msg, debug)
      
   
   def getShowFlag(self, fieldId):
      if self.msgType == '87':
         return self.fields[fieldId][5]
      else:
         return self.fields[fieldId][6]
      
   def read_operationCode(self, strcontent):
      codemsg = OperationCodeBits(self.DEBUG)
      codemsg.read_from_msg(strcontent)
      self.setField('operationCode', codemsg)
      return len(codemsg)
      
   def construct_operationCode(self):
      if isinstance(self.operationCode, basestring):
         return self.operationCode
      else:
         return self.operationCode.construct_operation_msg()
      
   def read_operationData(self, strcontent):
      logger.debug("===Read OperationData"+self.msgType+ str(self.getField('operationCode'))+ strcontent)
      data = OperationData(self.msgType, self.getField('operationCode'), strcontent, self.DEBUG)
      self.setField('operationData', data)
      return len(data)
   
   def construct_operationData(self):
      if isinstance(self.operationData, basestring):
         return self.operationData
      else:
         return self.operationData.constructMsg()
   
   def getField(self, fieldId):
      try:
         return Pos3MsgBase.getField(self, fieldId)
      except FieldNonExistError:
         if fieldId.count('.') > 0:
            fids = fieldId.split('.')
            target = self
            for fid in fids:
               target = target.getField(fid)
            return target
         else:
            raise     
   
   def setField(self, fieldId, value):
      try:
         Pos3MsgBase.setField(self, fieldId, value)
         if fieldId in ['operationData', 12] and isinstance(value, basestring):
            self.read_operationCode(value)
      except FieldNonExistError:
         if fieldId.count('.') > 0:
            fids = fieldId.split('.')
            target = self
            for i in range(0, len(fids)-1):
               target = target.getField(fids[i])
            target.setField(fids[-1], value)
         elif type(self.operationData) != str:
            self.operationData.setField(fieldId, value)
         else:
            raise
         
   def insert_bit(self, index, value):
      #TODO: implement this
      pass
   
   def remove_bit(self, index):
      #TODO: implement this
      pass
   
   def alter_bit(self, codenumber, value):
      #TODO: implement this
      #index = self.get_bit_index(codenumber)
      
      pass
   
      
   
class OperationCodeBits(object):
   def __init__(self, debug=False):
      self.opcodes = []
      self.length = 0
      self.msg = ''
      self.DEBUG = debug
   
   def read_from_msg(self, msg):
      logger.debug("=====Read Code: " + msg)
      length = len(msg)
      count = int(msg[:2], 16)
      self.msg += msg[:2]
      msg = msg[2:]
      #print '===opcode:', count
      while count:
         count -= 1
         opcode = OperationCode()
         msg = opcode.read_code(msg)
         self.opcodes.append(opcode)
         self.msg += str(opcode)
      self.length = length - len(msg)
      logger.debug('=====Operation codes:'+ str([i.codenumber for i in self.opcodes]))
      return msg
   
   def construct_operation_msg(self):
      msg = hex(len(self.opcodes))[2:].zfill(2)
      for o in self.opcodes:
         msg += o.construct_code_msg()
      self.length = len(msg)
      self.msg = msg
      return msg
   
   def get_bit_index(self, codenumber):
      for i in range(len(self.opcodes)):
         if self.opcodes[i].codenumber == int(codenumber):
            return i
         
      raise IndexError("bit not found: %s" % codenumber)
   
   def get_bit_value(self):
      pass
   
   def __len__(self):
      return self.length
   
   def __str__(self):
      if not self.msg:
         self.construct_operation_msg()
      return self.msg
   
   def __unicode__(self):
      return self.__str__()
   
class OperationCode(object):
   def __init__(self):
      self.codetype = None
      self.codenumber = None
      self.hintindex = None
      self.encrypttype = None
      self.cactype = None
      self.encryptflag = None
      self.cacflag = None
      self.reserved = None
      self.newcodetype = None
      self.msg = ''
      
   def read_code(self, srcmsg):
      firstbit = int(srcmsg[:2], 16)
      msg = srcmsg[2:]
      self.codetype = firstbit >> 6
      if self.codetype == 1:
         #code 2
         self.newcodetype = firstbit >> 2 & 0b11
         self.codenumber = (firstbit & 0b11) << 8
         if self.newcodetype in [0, 2, 3]:
            secondbit = int(msg[:2], 16)
            msg = msg[2:]
            self.codenumber += secondbit
         if self.newcodetype in [0, 3]:
            self.hintindex = msg[:2]
            msg = msg[2:]
         if self.codetype == 3:
            lastbit = int(msg[:2], 16)
            msg = msg[2:]
            self.encryptflag = lastbit >> 7
            self.encrypttype = lastbit >> 5 & 0b11
            self.cacflag = lastbit >> 4 & 0b1
            self.cactype = lastbit >> 1 & 0b11
            self.reserved = lastbit & 0b1
      else:
         #code 1
         self.codenumber = firstbit & 0b111111
         if self.codetype in [0, 3]:
            self.hintindex = msg[:2]
            msg = msg[2:]
         if self.codetype == 3:
            thirdbit = int(msg[:2], 16)
            msg = msg[2:]
            self.encryptflag = thirdbit >> 7
            self.encrypttype = thirdbit >> 5 & 0b11
            self.cacflag = thirdbit >> 4 & 0b1
            self.cactype = thirdbit >> 1 & 0b11
            self.reserved = thirdbit & 0b1
      self.msg = srcmsg[:len(srcmsg)-len(msg)]
      #print '===Code:', self.msg
      return msg
         
   def construct_code_msg(self):
      if self.codetype == 1:
         #code 2
         firstbit = (self.codetype << 6) + (self.newcodetype << 2) + (self.codenumber >> 8)
         msg = hex(firstbit)[2:]
         msg += hex(self.codenumber & 0xFF)[2:]
         if self.codetype in [0, 3]:
            msg += self.hintindex
         if self.codetype == 3:
            lastbit = (self.encryptflag <<7) + (self.encrypttype <<5) + \
                       (self.cacflag <<4) + (self.cactype <<1) + self.reserved
            msg += hex(lastbit)[2:]
      else:
         #code 1
         firstbit = (self.codetype <<6) + self.codenumber
         msg = hex(firstbit)[2:]
         if self.codetype in [0, 3]:
            msg += self.hintindex
         if self.codetype == 3:
            thirdbit = (self.encryptflag <<7) + (self.encrypttype <<5) + \
                       (self.cacflag <<4) + (self.cactype <<1) + self.reserved
            msg += hex(thirdbit)[2:]
      self.msg = msg
      return msg
         
   def __str__(self):
      if not self.msg:
         self.construct_code_msg()
      return self.msg
   
   def __unicode(self):
      return self.__str__()
     
class OperationData(Pos3MsgBase):
   
   datafields = fixdict()
   
   #seq, inputname, inputattr, inputtype, inputlen, outputname, outputattr, outputtype, outputlen
   datafields[2]=['02', None, None, None, None, "keyboardSerial", 'N', 'ASC', '16']
   datafields[3]=['03', None, None, None, None, "m1cardNumber", 'N', 'BCD', '11']
   datafields[4]=['04', None, None, None, None, "trackCipherText",trackCipherText , '', '']
   datafields[5]=['05', 'passwdFormat', 'N', 'HEX', '3', "passwdCipherText", 'N', 'HEX', '12']
   datafields[6]=['06', 'tradeNumberFormat', 'N', 'BCD', '19', "tradeNumber", 'N', 'BCD', '6']
   datafields[7]=['07', 'tradeAmountFormat', tradeAmountFormat, '', '22', "tradeAmount", 'N', 'BCD', '6']
   datafields[8]=['08', None, None, None, None, "bankAppNumber", bankAppNumber, '', '']
   datafields[9]=['09', None, None, None, None, "businessAppNumber", businessAppNumber, '', '']
   datafields[10]=['0A', None, None, None, None, "readDate", 'N', 'BCD', '4']
   datafields[11]=['0B', None, None, None, None, "readYearMonth", 'N', 'BCD', '3']
   datafields[12]=['0C', 'customFormat', customFormat, '', '', "customData", customData, '', '']
   #datafields[13]=['0D', None, None, None, None, "identificationCode", 'N', 'BCD', '8']
   #TODO: This is not the same as standard doc
   datafields[13]=['0D', None, None, None, None, None, None, None, None]
   datafields[14]=['0E', None, None, None, None, "printconfirmMsg", 'N', 'BCD', '11']   
   datafields[15]=['0F', None, None, None, None, "correctionMsg", correctionMsg, '', '']
   datafields[16]=['10', None, None, None, None, "terminalSystemVersion", 'N', 'BCD', '2']
   datafields[17]=['11', "appVersionType", "N", "HEX", "1", "terminalAppVersion", terminalAppVersion, '', '']
   datafields[18]=['12', None, None, None, None, "terminalSerialNumber", 'N', 'BCD', '10']
   datafields[19]=['13', None, None, None, None, "updateElecSignature", updateElecSignature, '', '']
   datafields[20]=['14', "elecSignature", 'N', "HEX", '8', None, None, None, None]
   datafields[21]=['15', "getElecSignature", getElecSignature, "", '', "terminalRelult", 'N', 'ASC', '2']
   datafields[22]=['16', "updateTerminalParameter", updateTerminalParameter, '', '',"updateTerminalParameterResult", 'N', 'ASC', '2']
   datafields[23]=['17', "updatePasswordKeywork", updatePasswordKeywork, '', '', "updatePasswordKeyworkResult", 'N', 'ASC', '2']
   datafields[24]=['18', "updateMenuParameter", updateMenuParameter, '', '', "updateMenuParameterResult", 'N', 'ASC', '2']
   datafields[25]=['19', "updateFuncPromptMsg", updateFuncPromptMsg, '', '', "updateFuncPromptMsgResult", 'N', 'ASC', '2']
   datafields[26]=['1A', "updateOperationMsg", updateOperationMsg, '', '', "updateOperationMsgResult", 'N', 'ASC', '2']
   datafields[27]=['1B', "updateHomePage", updateHomePage, '', '', "updateHomePageResult", 'N', 'ASC', '2']
   datafields[28]=['1C', "updatePrintTemplate", updatePrintTemplate, '', '', "updatePrintTemplateResult", 'N', 'ASC', '2']
   datafields[29]=['1D']#预留
   datafields[30]=['1E', None, None, None, None, "readSigninName", readSigninName, '', '']
   datafields[31]=['1F', "searchExchangeRate", searchExchangeRate, '', '', "searchExchangeRateResult", searchExchangeRateResult, '', '']
   datafields[32]=['20', None, None, None, None, "updateSaleSlip", updateSaleSlip, '', '']
   datafields[33]=['21', "printData", printDate, '', '', None, None, None, None]
   datafields[34]=['22', "showReultMsg", showReultMsg, '', '', None, None, None, None]
   datafields[35]=['23', None, None, None, None, None, None, None, None]
   datafields[36]=['24', None, None, None, None, None, None, None, None]
   datafields[37]=['25', None, None, None, None, None, None, None, None]
   datafields[38]=['26', None, None, None, None, None, None, None, None]
   datafields[39]=['27', None, None, None, None, None, None, None, None]
   #datafields[40]=['28', "checkMAC", checkMAC, 'BCD', '8', None, None, None, None]
   #TODO: This is not the same as standard doc
   datafields[40]=['28', None, None, None, None, None, None, None, None]
   datafields[41]=['29', "printSalesslipTemplate", printSalesslipTemplate, '', '', None, None, None, None]
   datafields[42]=['2A', None, None, None, None, None, None, None, None]
   datafields[43]=['2B', "checkIdentifyingCode", checkIdentifyingCode, '', '', "checkIdentifyingCodeResult", 'N', 'ASC', '2']
   datafields[44]=['2C', "onlineTradeConfirm", onlineTradeConfirm, '', '', "onlineTradeConfirmResult", 'N', 'ASC', '2']
   datafields[45]=['2D']#预留
   datafields[46]=['2E', "comCommunication", comCommunication, '', '', "comCommunicationResult", comCommunicationResult, '', '']
   datafields[47]=['2F', "temperaryOperateMsg", 'ANVAR', 'ASC', '2', None, None, None, None]
   datafields[48]=['30', None, None, None, None, "getControlCode", 'N', 'ASC', '1']
   datafields[49]=['31', "updateMenuLevel", updateMenuLevel, '', '', "updateMenuLevelResult", 'N', 'ASC', '2']
   datafields[50]=['32']#预留
   datafields[51]=['33', "updateTerminalVersion", updateTerminalAppVersion, '', '', "updateTerminalVersion", 'N', 'ASC', '2']
   datafields[52]=['34', "saveTradeList", saveTradeDetail, '', '', None, None, None, None]
   datafields[53]=['35', None, None, None, None, "terminalBalance", terminalBalance, '', '']
   datafields[54]=['36', "singleSelectOptions", singleSelectOptions, '', '', "singleSelectOptionsResult", 'NVAR', 'HEX', '1']
   datafields[55]=['37', "searchOriginalTrade", searchOriginalTrade, '', '', "searchOriginalTradeResult", searchOriginalTradeResult, '', '']
   datafields[56]=['38', None, None, None, None, None, None, None, None]
   datafields[57]=['39', 'updateWorkingKey', updateWorkingKey, None, None, "updateWorkingKeyStatus", 'N', 'ASC', '2']
   datafields[58]=['3A', "dynamicTradeMenu", dynamicTradeMenu, '', '', "dynamicTradeMenuResult", 'N', 'HEX', '1']
   datafields[59]=['3B', "updateErrMsg", updateErrMsg, '', '', "updateErrMsgResult", 'N', 'ASC', '2']
   datafields[60]=['3C', None, None, None, None, "uploadBasestationMsg", uploadBasestationMsg, '', '']
   datafields[61]=['3D', None, None, None, None, None, None, None, None]
   datafields[62]=['3E', "downloadSalessplitTemplate", downloadSalessplitTemplate, '', '', "downloadSalessplitTemplateResult", 'N', 'ASC', '2']
   datafields[63]=['3F']#预留
   datafields[64]=['40', "terminalConsoleOrder", terminalConsoleOrder, '', '', None, None, None, None]
   datafields[65]=['41']#预留
   datafields[66]=['42', "ICInitialise", 'N', 'HEX', '7', None, None, None, None]
   datafields[67]=['43', "cardReadOrder", 'N', 'HEX', '3', "cardReadOrderResult", cardReadOrderResult, '', '']
   datafields[68]=['44', "ICExpand", 'N', 'HEX', '5', "ICExpandSelect", ICExpandResult, '', '']
   datafields[69]=['45', "ICSimplify", 'N', 'HEX', '2', "ICSimplifyResult", ICSimplifyResult, '', '']
   datafields[70]=['46', None, None, None, None, None, None, None, None]
   datafields[71]=['47', None, None, None, None, None, None, None, None]
   datafields[72]=['48', "ICOnlineDataHandle", ICOnlineDataHandle, '', '', "ICOnlineDataHandleResult", ICOnlineDataHandleResult, '', '']
   datafields[73]=['49', "ICPrintDataOrder", ICPrintDataOrder, '', '', "ICPrintDataOrderResult", 'N', 'ASC', '2']
   datafields[74]=['4A', None, None, None, None, "readICTradeResult", readICTradeResult, '', '']
   datafields[75]=['4B', None, None, None, None, "readSpecialICTradeResult", readSpecialICTradeResult, '', '']
   datafields[76]=['4C', "updateAID", updateAID, '', '', "updateAIDResult", 'N', 'ASC', '2']
   datafields[77]=['4D', "updateCAPK", updateCAPK, '', '', "updateCAPKResult", 'N', 'ASC', '2']
   datafields[78]=['4E', 'updateBlacklist', updateBlacklist, None, None, "updateBlacklistResult", 'N', 'ASC', '2']
   datafields[79]=['4F', 'updateICOfflinePrintList', updateICOfflinePrintList, None, None, "updateICOfflinePrintListResult", 'N', 'ASC', '2']
   datafields[80]=['50', 'updateMerchantInfo', updateMerchantInfo, None, None, "updateMerchantInfoResult", 'N', 'ASC', '2']
   datafields[81]=['51', 'ICSetupLink', 'N', 'HEX', '1', None, None, None, None]
   datafields[82]=['52', 'ICSendData', 'N', 'HEX', '1', None, None, None, None]
   datafields[83]=['53', 'ICReceiveData', 'N', 'HEX', '1', None, None, None, None]
   datafields[84]=['54', 'ICJumpCommand', 'N', 'HEX', '2', None, None, None, None]
   datafields[85]=['55', 'updateICTag', updateICTag, None, None, "updateICTagResult", 'N', 'ASC', '2']
   
   
   fields = fixdict()
   
   
   def __init__(self, msgType, opbits, msg="", debug=False):
      """
      msgType:
         '87'   terminal ---> server   output message
         '84'   server   ---> terminal input message
      opbits:
         来自 OperationCodeBits 类
         
      //TODO update datafields
      """
      self.msgType = msgType
      self.bits = opbits
      self.mac = ''
      self.fields = fixdict()
      for opcode in self.bits.opcodes:
         self.fields[opcode.codenumber] = self.datafields[opcode.codenumber]
      Pos3MsgBase.__init__(self, msg, debug)
   
   def getName(self, fieldId):
      if self.msgType == '87':
         return self.fields[fieldId][5]
      else:
         return self.fields[fieldId][1]
   
   def getAttr(self, fieldId):
      if self.msgType == '87':
         return self.fields[fieldId][6]
      else:
         return self.fields[fieldId][2]
   
   def getType(self, fieldId):
      if self.msgType == '87':
         return self.fields[fieldId][7]
      else:
         return self.fields[fieldId][3]
   
   def getLength(self, fieldId):
      if self.msgType == '87':
         return int(self.fields[fieldId][8])*2
      else:
         return int(self.fields[fieldId][4])*2
   
   def getShowFlag(self, fieldId):
      return self.getName(fieldId) != None
 
   def readFromString(self, strcontent):
      offset = 0
      length = int(strcontent[offset:offset+4], 16)
      offset += 4
      offset += Pos3MsgBase.readFromString(self, strcontent[offset:])
      #MAC 实现与规范不一致
      #self.mac = strcontent[offset:offset+16]
      #offset += 16
      
      #if offset != len(strcontent):
         #print("**WARNING** Message length is not the same as expected.", strcontent)
      return offset
      
   def constructMsg(self, force=False):
      msg = Pos3MsgBase.constructMsg(self, force)
      #MAC 实现与规范不一致
      #msg += self.mac.zfill(16)
      msg = hex(len(msg)/2)[2:].zfill(4) + msg
      
      self.msg = msg
      return msg      
      
   def read_terminalAppVersion(self, strcontent):
      offset = 0
      self.setField("appVersionType", strcontent[offset:offset+2])
      offset += 2
      versionlength = int(strcontent[offset:offset+2], 16)
      offset += 2
      self.setField('terminalAppVersion', strcontent[offset:offset+versionlength])
      return versionlength + offset
   
   def construct_terminalAppVersion(self):
      msg = self.getField('terminalAppVersion')
      msg = hex(len(msg)/2)[2:].zfill(2) + msg
      msg = self.getField('appVersionType').zfill(2) + msg
      return msg

   
if __name__ == '__main__':
   msg = """006e60000300008728f5b40f013834393434303335333131363033313830303134303939000000302013018400410200310400050062ffffff0000000000000000000000000000000000000000000013303531018200100000000000000000000000000000000026777401aa376dc1d4"""
   msg = "006360000300008728f5b40f033834393434303335333131363033313830303134303939000000302013018400360200310400050062ffffff000000000000000000000000000000000000000000001430353102b9960004303030300355f1f86e6d797274"
   msg = '00d660000000038428f5b40f023834393434303335333131363033313830303134303939000000000000000000a9020020141009105527ffffff000000000000000000000000000000000000000000001330353104b996240225030072430041106620ee3b51e0281ae8f329d0f9b96f1c74a570b14210737e11a2300c4a6ca1913dec2ed63b684aedde2f43103ed1bde81884983844e9a9de001c5046b216a00a002c050a000b000c00291e2000000000000000000000000000000000000000000000000000000000002d03ffffff00000000000000005a'
   msg = '00a66000030000879cf202f00138343934343033353331313630333138303031343039390000003020130184007902003104000500620002410000000000000000000000000000000000000000317927323032079e48438ab78748458d004002303180000200186226160600005000358dc1f7680229b594235c5e3b66cad0201410111500000006323538373331000000003333020008ffffffffffffffff3606c03da787946e82'
   #msg = '006b600003000087fb9a2b760138343934343033353331313630333138303031343039390000003020130184003e0200310400050062ffffff0000000000000000000000000000000000000000316156303034028f8d000c0b316155bb28a475e46fdb60e48595074e3c0ade45'
   #msg = '00956000030000876ff806890138343934343033353331313630333138303031343039390000003020130184006802003104000500620000020000000000000000000000000000000000000000315912313031059e87484348448d00310230310000000066668000020018080683da000acf238edc0d50c2b2c8fa176a0291d6678ddd020008ffffffffffffffff8c02597de5db8941ea'
   #msg = '00956000030000876c306b0f013834393434303335333131363033313830303134303939000000302013018400680200310400050062ffffff0000000000000000000000000000000000000000000036313031059e87484348448d00310230310000000055558000020018cdd528b75fb5f40c358dc1f7680229b594235c5e3b66cad0020008ffffffffffffffff6581679178130b25c8'
   #msg = '017d600000000384b4efa1ca02383439343430333533313136303331383030313430393900000000000000000150020020141010161130000002000000000000000000000000000000000000000000003631303107a6a84848b4a9a2484001160230300000005a0101010028cffbb7d10000000000000000000000000000000000000000000000000000000000000000000000002bebc0e1bfffffffffffffffff0000000000003132333435363738393031320000000055552014101115000000009200000001010100000c0f5204d6d0b9fa0f510f3834393434303335333131363033310f530838303031343039390f600230311f2108c5a9d2b5d2f8d0d09f010830313033303030301f120b3242454243304531422f530f150530392f33301f1304cffbb7d11f170c3132333435363738393031321f1513323031342f31302f31312031353a30303a30301f180535352e353500113002303009bdbbd2d7b3c9b9a620000000000c030100000c00000d00020101f9eca75906294c1005'
   p = Pos3Msg(msg, debug = True)
   #p.setContent(msg)
   p.printFields()
   print('============================')
   
   p.constructMsg()
   print msg
   print(p.msg)
   print(p.msg == msg)
      
   print('============================')

   msgtype = p.msgType
   iso = str(p.content)
   print iso
   p = PosTradeMSG(msgtype, debug = True)
   p.setContent(iso)
   p.printFields()
   
   op = OperationCodeBits()
   op.read_from_msg(str(p.operationCode))


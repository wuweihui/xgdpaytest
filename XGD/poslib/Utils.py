#-*- coding: utf-8 -*-

def calcParityBit(base):
   """
   POS报文校验位校验算法
   """
   ret = 0x0
   while(base):
      ret += int(base[:2], 16)
      base = base[2:]
   ret &= 0xFF
   return (256-ret) & 0xFF

def toHexstr(intbase):
   return hex(intbase)[2:]

def calcCardNumber(base):
   """
   POS平台终端规范5.0。1 算法1 - 数字校验算法
   """
   ret = 0
   base = str(base)
   while len(base) > 1:
      i, j = int(base[:1]), int(base[1:2])
      ret += i + (j*2)/10 + (j*2)%10
      base = base[2:]
      
   if base:
      ret += int(base)
      
   return ret%10 != 0 and 10 - ret%10 or 0

def intToBCD(base):
   return ''.join(['3'+i for i in str(base).split()])

def BCDToIntstr(base):
   return base[1::2]
      
class fixdict(dict):
   """
   字典的Key顺序将按照初始化的顺序排列，用于保存操作码的顺序
   """
   def __init__(self):
      dict.__init__(self)
      self._keys = []
   
   def __setitem__(self, i, v):
      dict.__setitem__(self, i, v)
      if i not in self._keys:
         self._keys.append(i)
   
   def keys(self):
      return self._keys
   
   def items(self):
      return [(k, self[k]) for k in self._keys]
   
   def values(self):
      return [self[k] for k in self._keys]
   
   def update(self, dc):
      for k, v in dc.items():
         self[k] = v
         
   def pop(self, key):
      dict.pop(self, key)
      self._keys.remove(key)
      
   def insert(self, i, k, v):
      dict.__setitem__(self, k, v)
      if k not in self._keys:
         self._keys.insert(i, k)
   

if __name__ == '__main__':
   msg = '009960000000038419b380b30238343934343033353331313630333138303031343039390000000000000000006c020020140924130747ffffff000000000000000000000000000000000000000031615531303103a2a648400037002a303c463022bdbbd2d7caa7b0dca3bacfb5cdb3d2ecb3a3a3acc7ebc1aacfb5ceacbba4c8cbd4b10000000009020c00000d0002010100000000000000005e'
   base = msg[14:-2]
   print hex(calcParityBit(base))
   
   print calcCardNumber(4992739871)
   
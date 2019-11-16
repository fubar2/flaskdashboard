#!/usr/bin/python3
# for raspberry pi
# works with 4 HX711/loadcells on a pi zero at 30 second sampling
# will need more grunt and optimising for rapid sampling
#
# note NEED SCALE (reference unit) AS FLOAT for decent accuracy - using an int leads to systematic error
#
# uses paramiko to append data to remote files to avoid writing frequently to rpi ssd
# 
# multiple HX711 version - separate data/clock port pair for each
# uses curses so we can read keystrokes and ignore them while running
# x exits and c calibrates during operation while latest values are continuously written
# to the curses window
# some fancy footwork to go back to normal console for calibration...
# check that reading a requested dataport repeatedly does not give zeros
# as that means probably no hx711/scale connected - ignore config if so
# october 2019
#
# sampler for a pi hx711/loadcell combination
# ross lazarus me fecit May 2019
# based on the hx711py example.py code.
# Keep hx711 powered down when not in use - seems to keep the loadcell cooler
# so less thermal drift - also connect it to the 3.7v supply, not the 5v supply
# as that also seems to induce less drift
#
# added rename of old log file - I just wrote 19 hours over. Sad face.
# changed to just append. deal with zeros and discontinuities later

import datetime
import time
from paramiko import Transport, SFTPClient, RSAKey
import sys
import os
import RPi.GPIO as GPIO
from hx711 import HX711

from config import BaseConfig

SHORTSLEEP=BaseConfig.SHORTSLEEP
SAMPINT = BaseConfig.SAMPINT
RUNCOOL = BaseConfig.RUNCOOL


class SftpClient:

	_connection = None

	def __init__(self, host, port, username, password, key):
		self.host = host
		self.port = port
		self.username = username
		self.password = password
		self.key = key
		self.create_connection(self.host, self.port,
							   self.username, self.password, self.key)

	@classmethod
	def create_connection(cls, host, port, username, password, key):
		transport = Transport(sock=(host, port))
		transport.connect(username=username, pkey = key)
		cls._connection = SFTPClient.from_transport(transport)

	@classmethod
	def appendrows(self, rows, remote_path):

		f = self._connection.file(remote_path,'a')
		f.write(rows)
		f.close()
		return len(rows)

	@classmethod
	def dirch(self,d):
		self._connection.chdir(d)

	@classmethod
	def dirlist(self,d):
		return self._connection.listdir(d)
		
	def file_exists(self, remote_path):

		try:
			print('remote path : ', remote_path)
			self._connection.stat(remote_path)
		except IOError as e:
			if e.errno == errno.ENOENT:
				return False
			raise
		else:
			return True

	def download(self, remote_path, local_path, retry=5):

		if self.file_exists(remote_path) or retry == 0:
			self._connection.get(remote_path, local_path,
								 callback=None)
		elif retry > 0:
			time.sleep(5)
			retry = retry - 1
			self.download(remote_path, local_path, retry=retry)
			
	def close(self):
		self._connection.close()
		





class hxboard():
	""" encapsulate a single hx711/load cell
	"""
	def __init__(self,port,logfname,nscale):
		"""
		"""
		if not port:
			logging.warning('## hxboard __init__ requires a clock/data port (as [5,6] eg) please')
			return
		self.logdat = False
		self.recording = False
		self.outfile = None
		self.nscale = nscale
		self.lastval = 0.0
		self.configfile = 'scale%d.config' % nscale
		self.scale = 1.0
		self.offset = 0
		self.port = port
		self.lasttime = datetime.datetime.now()
		if os.path.isfile(self.configfile):
			s = open(self.configfile,'r').read()
			sc,offs = s.split(',')
			self.scale = float(sc)
			self.offset = int(offs)
			self.calibrated = True
		else:
			self.calibrated = False
		hxnew = HX711(self.port[0],self.port[1])
		hxnew.set_reading_format("MSB", "MSB")
		hxnew.set_reference_unit(self.scale)
		hxnew.set_offset(self.offset)
		self.hx = hxnew
		scale_ready = self.do_Ready()
		if not scale_ready:
			# timeout
			logging.warning("!!! Scale ready timeout - is scale %d @ port %s connected? Not calibrating" % (self.nscale,self.port))
		else:
			if not self.calibrated:
				self.do_Calibrate()
			
	def do_Ready(self):
		# arbitrary check that scale is attached
		# if all zeros for a series of values, probably not.
		scale_ready = False
		if RUNCOOL:
			self.hx.power_up()
		time.sleep(SHORTSLEEP)
		vals = [self.hx.read_average(times=1) for x in range(10)]
		if max(vals) != 0.0 and min(vals) != 0.0:
			scale_ready = True
		if RUNCOOL:
			self.hx.power_down() # reduce heat load on chip
		return scale_ready


	def cleanUp(self):
		logging.debug("Cleaning up")
		if self.outfile:
			self.outfile.close()
		self.hx.power_down()

	def do_Show(self):
		"""return some html for flask
		"""
		recnote = ""
		if self.recording:
			recnote = 'Recording to file %s' % self.logfname
		#s = '<tr><td>Scale #%d</td><td>last value %.2fg</td><td>%s @ %s</td></tr>\n' % (self.nscale,self.lastval,recnote,self.lasttime.ctime())
		s = 'Scale #%d last value %.2fg %s @ %s\n' % (self.nscale,self.lastval,recnote,self.lasttime.ctime())
		return s

	def do_Read(self):
		"""
		"""
		if RUNCOOL:
			self.hx.power_up()
		time.sleep(SHORTSLEEP)
		val = (self.hx.read_average(times=7) - self.offset)/self.scale
		if RUNCOOL:
			self.hx.power_down() # reduce heat load on chip
		self.lastval = val
		self.lasttime = datetime.datetime.now()
		return val

	def do_Calibrate(self):
		"""
		"""
		readyCheck = input("Remove any items from scale #%d. Press any key when ready." % self.nscale)
		self.hx.power_up()
		self.hx.set_reference_unit(1)
		time.sleep(1)
		self.hx.tare()
		# hx.set_reference_unit(1) # not needed if use read_average
		offset = self.hx.read_average(10)
		print("Value at zero (offset): {}".format(offset))
		self.hx.set_offset(offset)
		self.offset = offset
		print("Please place an item of known weight on scale #%d." % self.nscale)
		readyCheck = input("Press <Enter> to continue when ready.")
		rval = self.hx.read_average(times=10)
		val = (rval - offset)
		status = "Scale #%d read=%f offset=%d val=%f." % (self.nscale,rval, offset,val)
		print(status)
		logging.debug(status)
		item_weight = input("Please enter the item's weight in grams.\n>")
		iwf = float(item_weight)
		scale = val/iwf
		self.hx.set_reference_unit(int(scale))
		status = "Scale #%d adjusted for %d grams = %d\n" % (self.nscale,iwf,scale)
		print(status)
		logging.debug(status)
		self.scale = scale
		if os.path.exists(self.configfile):
			ps = open(self.configfile,'r').readline()
			status = 'Replacing old configfile %s with %.2f,%d' % (ps,scale,offset)
			print(status)
			logging.debug(status)
		input("Press <Enter> to continue")
		cf = open(self.configfile,'w')
		s = '%.2f,%d\n' % (scale,offset)
		cf.write(s)
		cf.close()
		if RUNCOOL:
			self.hx.power_down()
		self.calibrated = True
		print("Please replace the %.f mass with the item to be recorded on scale #%d." % (iwf,self.nscale))
		readyCheck = input("Press <Enter> to continue when ready.")

class hxboards():
	"""
	encapsulate a collection of hx711/load cell inputs - have 4 kits!
	"""
		
	def __init__(self,portlist=[[5,6],]):
		self.hxs = []
		self.upload_remote_path = BaseConfig.REMPATH
		sftpkey = RSAKey.from_private_key_file(BaseConfig.SFTPKEYFILENAME)
		self.client = SftpClient(BaseConfig.FILEHOST, BaseConfig.SFTPPORT, BaseConfig.REMLOGINUSER, BaseConfig.SFTPPASSWORD, sftpkey)
		for i in range(len(portlist)):
			hx = hxboard(portlist[i],'scale%d.xls' % i,i)
			if hx.do_Ready():
				self.hxs.append(hx)
			else:
				status = 'Getting zeros from scale %d ports %s so not using' % (i,portlist[i])
				print(status)
				logging.debug(status)                
				dummy = input('Press <Enter> to continue')
	

	def getStatus(self):
		s = ''
		for hx in self.hxs:
			s += hx.do_Show()
		return s

	def getVals(self):
		for hx in self.hxs:
			val = hx.do_Read()
			uprempath = BaseConfig.UPREMPATHSKEL % hx.nscale
			dur = int(time.time()) # seconds is enough for us
			s = '%d\t%.2f\n' % (dur,val)
			self.client.appendrows(s,uprempath)

	def cleanUp(self):
		for hx in self.hxs:
			hx.cleanUp()
		GPIO.cleanup()
		logging.shutdown()


	def do_Calibrate(self):
		lhs = len(self.hxs)
		if lhs > 1:
			print('Which scale would you like to recalibrate - enter one of %s' % ' '.join(map(str,range(lhs))))
			doscale = input('>')
			if int(doscale) in range(lhs):
				self.hxs[int(doscale)].do_Calibrate()
			else:
				status = '!!! No scale %d - cancelled Press <Enter> to continue'
				print(status)
				logging.debug(status)                
				input('>')
		elif lhs == 1:
			self.hxs[0].do_Calibrate()
			

if __name__ == "__main__":
	hxb = hxboards([[5, 6], [7, 8], [9, 10], [11, 12]])
	# unconnected ports will fail if read_average always zero
	running = True
	lastupdate = 0
	while running:
		if (time.time() - lastupdate) > SAMPINT:
			hxb.getVals()
			scalestats = hxb.getStatus()
			print(scalestats)
			lastupdate = time.time()
		time.sleep(5)

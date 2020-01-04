#!/home/ross/rossgit/loadcellflask/venv/bin/python
# distribution of slopes of weight discontinuity segments
# for each series
# nov 15 why guess when we can 
# use watercron.log as authoritative segmenter

from config import BaseConfig
from loadcelldata import loadCellDataMulti
from sftp import SftpClient
from pandas import Timedelta
import datetime
from paramiko import Transport, SFTPClient, RSAKey
import bisect
import copy
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import pandas as pd
import numpy as np
import peakutils
from peakutils.plot import plot as pplot
from matplotlib import pyplot
from sftp import SftpClient
from config import BaseConfig
from loadcelldata import loadCellDataMulti
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

#%matplotlib inline

DELTAUP = BaseConfig.DELTAUP
DELTADOWN = BaseConfig.DELTADOWN
# Increasing or falling from t at t+1 and t+2 data points = watering - next segment starts at last rising time
MINDURATION = BaseConfig.MINDURATION
# sometimes very short spikes - ignore...
SEGTABFNAME = BaseConfig.SEGTABFNAME

def getWCronlog(fname):
	"""
	Cronjobs write a log so use that to figure out when watering actually occurred rather
	than trying to guess
	
ross@nuc:~/rossgit/pyCronPlug$ head watercron.log 
### Wed Oct 30 12:01:02 2019: watering cron job has turned plug on for 42.857143 seconds
<ChuangmiPlugStatus power=True, usb_power=None, temperature=44, load_power=None, wifi_led=None>
### Wed Oct 30 12:01:45 2019: watering cron job has turned plug off
<ChuangmiPlugStatus power=False, usb_power=None, temperature=45, load_power=None, wifi_led=None>
### Wed Oct 30 13:01:01 2019: watering cron job has turned plug on for 35.294118 seconds
	"""
	wlog = open(fname,'r').readlines() 
	# 4 lines per event. ok, ok. Sorry. Send code.
	wlogt = [x for x in wlog if ('has turned plug on' in x)]
	evnts = []
	ctf = '%a %b %d %H %M %S %Y'
	for evnt in wlogt:
		sev = evnt.replace(':',' ').split()[1:8]
		sevs = ' '.join(sev)
		cdt = datetime.datetime.strptime(sevs,ctf)
		csec = cdt.timestamp()
		on4 = float(evnt.split('on for ')[1].split(' seconds')[0])
		evnts.append((csec,on4,cdt))
	return(evnts)


def findDisc(vals,startx,ntest):
	""" find last point of transpiration before water increases mass
	"""
	allbigger = []
	xval = vals[startx]
	for i in range(ntest):
		isBigger = vals[startx+i+1] - xval >= DELTAUP
		if not isBigger:
			break # cannot be true
		allbigger.append(isBigger)
	nbigger = sum(allbigger)
	return (nbigger == ntest)
	

def findNextUporend(vals,xstart,lastRow,sd,ntest):
	"""
	"""
	i = xstart
	upfound = False
	foundAt = None
	endy = None
	while (not upfound) and (i < lastRow):
		xval = vals[i]
		if ((i == 0) or (vals[i-1] > xval)): # is falling
			i += 1
			continue
		if findDisc(vals,i,ntest): # discontinuity - save segment start and update when next discontinuity or end data
			upfound = True
			foundAt = i
			endy = vals[foundAt]
		else:
			i += 1
	if foundAt == None:
		foundAt = i
		endy = vals[i]
	return(foundAt,endy)


def getDerivs(timex,y):
	"""https://math.stackexchange.com/questions/2875173/numerical-second-derivative-of-time-series-data
	"""
	yderiv = [float('nan') for x in range(len(y))]
	y2deriv = [float('nan') for x in range(len(y))]
	for i,t in enumerate(timex[1:(len(timex)-1)]):
		yderiv[i] = (y[i+1] - y[i-1])/2.0
		y2deriv[i] = (y[i+2] + y[i-2] - 2*y[i])/4.0
	return yderiv,y2deriv
	
	

def segMents(df,n):
	""" data driven version - does not use water cron log
	header only when n=0
	"""
	segs = []
	header = ['scale','tstart','tend','mstart','mend','duration','delta','rate\n']
	if n >= 1:
		segd = []
	else:
		segd = [header,] # for xls	
	vals = df.iloc[:,-1].rolling(5).median()
	dft = [x.timestamp() for x in df.iloc[:,0]]
	# yderiv,y2deriv = getDerivs(dft,vals) # use smoothed...
	# if n == 0:
		# f = open('deriv.xls','w')
		# f.write('scale\tt\td1\td2\t\n')
	# else:
		# f = open('deriv.xls','a')
	# outl = ['%d\t%s\t%f\t%f\n' % (n,dft[x],yderiv[x],y2deriv[x]) for x in range(len(dft))]
	# f.write(''.join(outl))
	# f.close()
	# meen = df.iloc[:,-1].mean()
	sd = df.iloc[:,-1].std()
	startx = 0
	ntest = 10
	lastRow = df.shape[0] - ntest
	while startx < lastRow:
		# ignore watering periods of ascending weight 
		xval = vals[startx]
		foundAt = None
		if findDisc(vals,startx,ntest):
			startx += 1
			starty = vals[startx] # 
			(foundAt,endy) = findNextUporend(vals,startx,lastRow,sd,ntest)
			if foundAt:
				stillup = True
				j = foundAt
				while stillup and (j < lastRow):
					# ignore watering periods of ascending weight 
					xval = vals[j]
					d1 = (vals[j+1]-vals[j])/xval > DELTAUP
					d2 = (vals[j+2]-vals[j+1])/xval > DELTAUP
					j += 1
					if not (d1 and d2):
						stillup = False
					# print('foundAt',foundAt,'stillup=',stillup,'startx=',startx, 'j=',j,'lastRow=',lastRow,'d1=',d1,'d2=',d2)
				foundAt = j
				diff = (endy-starty)
				td = df.iloc[foundAt,0] - df.iloc[startx,0]
				dur = td.total_seconds()/60.0
				if dur > MINDURATION:
					rate = diff/dur
					s = [df.iloc[startx,0].ctime(),df.iloc[foundAt,0].ctime(),'%.2f' % starty,'%.2f' % endy, '%.2fmin' % dur,'%.2fg' % diff, 
					'%.2fg/min' % rate]
					d = ['%d' % n,df.iloc[startx,0].ctime(),df.iloc[foundAt,0].ctime(),'%.2f' % starty,'%.2f' % endy, '%.2f' % dur,'%.2f' % diff, 
					'%.2f\n' % rate]
					segs.append(s)
					segd.append(d)
				else:
					#pass
					print('## Ignoring diff=',diff,'because dur=',td,'. Change config MINDURATION to control')
				startx = foundAt
		else:
			startx += 1
	return(segs,segd)
		
def segMentsLog(df,evnts):
	"""
	uses water cron log as definitive source of watering times
	"""
	header = ['scale','tstart','tend','mstart','mend','duration','delta','rate','watered\n']
	seqd = [header,] # for xls	
	dft = [x.timestamp() for x in df.iloc[:,0]]
	eventt = [int(x[0]) for x in evnts]
	eventdt = [x[2] for x in evnts]
	seqs = [] # decorated 
	vals = df.iloc[:,-1].rolling(5).median()
	sd = vals.std()
	startx = 0
	lastRow = df.shape[0]
	lastRow -= 2
	for starte,tsec in enumerate(eventt[:-1]):
		durat = evnts[starte][1] # water duration
		# look for rise then fall after watering
		# use next watering as limit for period
		wend = (tsec+durat) 
		startx = bisect.bisect_left(dft,wend)
		nextwatert = eventt[starte+1]
		nextwaterx = bisect.bisect_left(dft,nextwatert)
		nextwaterx = min(lastRow,nextwaterx)
		i = startx
		riseFound = False
		while not riseFound and i < nextwaterx: 
			d1 = (vals[i+1] - vals[i])/sd > DELTAUP
			d2 = (vals[i+2] - vals[i+1])/sd > DELTAUP
			if d1 and d2:
				riseFound = True
			else:
				i += 1
				continue
		startx = i
		fallFound = False
		while not fallFound and i < nextwaterx: 
			d1 = (vals[i] - vals[i+1])/sd > DELTADOWN
			d2 = (vals[i+1] - vals[i+2])/sd > DELTADOWN
			if d1 and d2:
				fallFound = True				
			else:
				i += 1
				continue
		startx = i
		starty = vals[startx]
		endx = nextwaterx # safe assumption?
		endy = vals[endx]
		diff = (endy-starty)
		td = df.iloc[endx,0] - df.iloc[startx,0]
		dur = td.total_seconds()/60.0
		if dur > MINDURATION:
			rate = diff/dur
			s = [df.iloc[startx,0].ctime(),df.iloc[endx,0].ctime(),'%.2f' % starty,'%.2f' % endy, '%.2fmin' % dur,'%.2fg' % diff, 
			'%.2fg/min' % rate,'Water @ %s' % eventdt[starte].ctime()]
			d = [df.iloc[startx,0].ctime(),df.iloc[endx,0].ctime(),'%.2f' % starty,'%.2f' % endy, '%.2f' % dur,'%.2f' % diff, 
			'%.2f' % rate,'%s\n' % eventdt[starte].ctime()]
			seqs.append(s)
			seqd.append(d)
		else:
			pass
			#print('## Ignoring diff=',diff,'because dur=',td,'. Change config MINDURATION to control')

	return(seqs,seqd)
		

def runSeg():
	evnts = getWCronlog(BaseConfig.CRONLOG)
	# print(evnts)	
	upload_remote_path = BaseConfig.REMOTEDATAPATH
	sftpkey = RSAKey.from_private_key_file(BaseConfig.SFTPKEYFILENAME)
	sftp = SftpClient(BaseConfig.REMOTEDATAHOST,BaseConfig.SFTPPORT,BaseConfig.SFTPLOGINUSER,BaseConfig.SFTPPASSWORD,sftpkey)
	sftp.dirch(BaseConfig.REMOTEDATAPATH)
	fl = sftp.dirlist(upload_remote_path)
	fl.sort()
	fl = [x for x in fl if (len(x.split('.')) > 1 and x.split('.')[1]=='xls')]
	if fl != None:
		lcd = loadCellDataMulti(BaseConfig.NSD,fl)
		datal = []
		for i, df in enumerate(lcd.dfs):
			nr = df.shape[0]
			print('###i=',i)
			if nr > 0:
				#segmints,segtab = segMentsLog(df,evnts)
				segmints,segtab = segMents(df,i)
				segments = ['\t'.join(x) for x in segmints]
				print(lcd.names[i],'segments=\n','\n'.join(segments))
				segtabs = ['\t'.join(x) for x in segtab]
				if i == 0:
					f = open(SEGTABFNAME,'w')
				else:
					f = open(SEGTABFNAME,'a')
				f.write(''.join(segtabs))
				f.close()



def getpeaks():
	""" use scikit signal peak finding
	
	"""


	nobs = 60*2*24*7 # size of sample 
	upload_remote_path = BaseConfig.REMOTEDATAPATH
	sftpkey = RSAKey.from_private_key_file(BaseConfig.SFTPKEYFILENAME)
	sftp = SftpClient(BaseConfig.REMOTEDATAHOST,BaseConfig.SFTPPORT,BaseConfig.SFTPLOGINUSER,BaseConfig.SFTPPASSWORD,sftpkey)
	sftp.dirch(BaseConfig.REMOTEDATAPATH)
	fl = sftp.dirlist(upload_remote_path)
	fl.sort()
	fl = [x for x in fl if (len(x.split('.')) > 1 and x.split('.')[1]=='xls')]
	if fl != None:
		lcd = loadCellDataMulti(BaseConfig.NSD,fl)
		datal = []
		for i, df in enumerate(lcd.dfs):
			nd0 = df.shape[0]
			print('###i=',i)
			if nd0 > 0:
				print(nd0,nobs)
				dat = df.iloc[(nd0-nobs):nd0,]
				nd0 = dat.shape[0]
				dat0y = dat['mass'].rolling(5).median() # low pass filter helps
				dat0x = dat.iloc[:,0]

				peaks, pp = find_peaks(dat0y, height=20,width=30,distance=60)
				#peaks= find_peaks_cwt(dat0y,np.arange(100,960,10)) # doesn't work well with irregular waveforms I guess..
				peakx = [dat0x[x] for x in peaks ]
				dpeaks = pd.DataFrame(peakx)
				dpeaks['scale'] = i
				if i == 0:
					allPeaks = dpeaks
				elif i != 3:
					allPeaks = allPeaks.append(dpeaks)
				# peakutils doesn't work as well with this data
				#peaks = peakutils.indexes(dat0y, thres=0.6, min_dist=40)
				#peaks = peakutils.interpolate(dat0x.index,dat0x,peaks1)
				#print(indexes)
				#print(x[indexes], y[indexes])
				fig = plt.figure(figsize=(12,4))
				pplot(dat0x,dat0y,peaks)
				fig.show()
				#axs[scl].title.set_text('Scale %d' % scl)
				#axs[scl].plot(peaks, dat0x[peaks] ,'x')
				#axs[scl].plot(np.zeros_like(dat0x), "--", color="gray")
	fig = plt.figure(figsize=(12,4))
	plt.plot(allPeaks.iloc[:,0],allPeaks.scale,'x')            
	plt.title('Times of peaks for each scale')
	fig.show()

if __name__== "__main__":
	runSeg()
	

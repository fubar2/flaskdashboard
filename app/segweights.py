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

DELTAUP = BaseConfig.DELTAUP
DELTADOWN = BaseConfig.DELTADOWN
# Increasing or falling from t at t+1 and t+2 data points = watering - next segment starts at last rising time
MINDURATION = BaseConfig.MINDURATION
# sometimes very short spikes - ignore...

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
	return evnts
		

def findNextUporend(vals,xstart,lastRow,meen):
	"""
	"""
	i = xstart
	upfound = False
	foundAt = None
	endy = None
	while (not upfound) and (i < lastRow):
		x = vals[i]
		if ((vals[i-1] >= x)) or (i == 0): # is falling
			i += 1
			continue
		d1 = (vals[i+1] - x)/meen > DELTA
		d2 = (vals[i+2] - vals[i+1])/meen > DELTA
		if d1 and d2: # discontinuity - save segment start and update when next discontinuity or end data
			upfound = True
			foundAt = i
			endy = vals[foundAt]
		else:
			i += 1
	return(foundAt,endy)


def segMents(df):
	""" data driven version - does not use water cron log
	"""
	seqs = []
	vals = df.iloc[:,-1].rolling(10).median()
	meen = vals.mean()
	startx = 0
	lastRow = df.shape[0]
	lastRow -= 2
	while startx < lastRow:
		# ignore watering periods of ascending weight 
		xval = vals[startx]
		d1 = (vals[startx+1]-xval)/meen > DELTA
		d2 = (vals[startx+2]-xval)/meen > DELTA
		if d1 and d2:
			startx += 1
			continue
		starty = vals[startx]
		(foundAt,endy) = findNextUporend(vals,startx,lastRow,meen)
		if foundAt:
			stillup = True
			j = foundAt + 1
			while stillup and j < lastRow:
				# ignore watering periods of ascending weight 
				# print('stillup,i=',i, 'j=',j)
				xval = vals[j]
				d1 = (vals[j+1]-xval)/meen > DELTA
				d2 = (vals[j+2]-xval)/meen > DELTA
				if d1 and d2:
					j += 1
					continue
				else:
					stillup = False
			foundAt = j
			diff = (endy-starty)
			td = df.iloc[foundAt,0] - df.iloc[startx,0]
			dur = td.total_seconds()/60.0
			if dur > MINDURATION:
				rate = diff/dur
				s = (df.iloc[startx,0].ctime(),df.iloc[foundAt,0].ctime(),'%.2f' % starty,'%.2f' % endy, '%.2fmin' % dur,'%.2fg' % diff, '%.2fg/min' % rate)
				seqs.append(s)
			startx = foundAt
		else:
			startx = lastRow 	
	return(seqs)
		
def segMentsLog(df,evnts):
	"""
	uses water cron log as definitive source of watering times
	"""
	dft = [x.timestamp() for x in df.iloc[:,0]]
	eventt = [int(x[0]) for x in evnts]
	eventdt = [x[2] for x in evnts]
	seqs = []
	vals = df.iloc[:,-1].rolling(10).median()
	sd = vals.std()
	startx = 0
	lastRow = df.shape[0]
	lastRow -= 2
	for starte,tsec in enumerate(eventt[:-1]):
		durat = evnts[starte][1]
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
			s = (df.iloc[startx,0].ctime(),df.iloc[endx,0].ctime(),'%.2f' % starty,'%.2f' % endy, '%.2fmin' % dur,'%.2fg' % diff, 
			'%.2fg/min' % rate,'Water @ %s' % eventdt[starte].ctime())

			seqs.append(s)
		else:
			pass
			#print('## Ignoring diff=',diff,'because dur=',td,'. Change config MINDURATION to control')

	return(seqs)
		
		



if __name__== "__main__":
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
				if nr > 0:
					segmints = segMentsLog(df,evnts)
					segments = ['\t'.join(x) for x in segmints]
					print(lcd.names[i],'segments=\n','\n'.join(segments))


#!/home/ross/rossgit/loadcellflask/venv/bin/python
# distribution of slopes of weight discontinuity segments
# for each series

from config import BaseConfig
from loadcelldata import loadCellDataMulti
from sftp import SftpClient
from pandas import Timedelta

from paramiko import Transport, SFTPClient, RSAKey

DELTA = BaseConfig.DELTA
# 1% increase from t at t+1 and t+2 data points = watering - next segment starts at last rising time



def findNextUporend(vals,xstart,lastRow,meen):
	"""
	"""
	i = xstart
	upfound = False
	foundAt = None
	endy = None
	while not upfound and i < lastRow:
		x = vals[i]
		if ((vals[i-1] >= x)) or (i == 0): # is falling
			i += 1
			continue
		d1 = (vals[i+1] - x)/meen > DELTA
		d2 = (vals[i+2] - x)/meen > DELTA
		if d1 and d2: # discontinuity - save segment start and update when next discontinuity or end data
			upfound = True
			foundAt = i
			endy = vals[foundAt]
		else:
			i += 1
	return(foundAt,endy)


def segMents(df):
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
			#print('diff=',diff,'dur=',td)
			rate = diff/dur
			s = (df.iloc[startx,0].ctime(),df.iloc[foundAt,0].ctime(),'%.2f' % starty,'%.2f' % endy, '%.2fmin' % dur,'%.2fg' % diff, '%.2fg/min' % rate)

			seqs.append(s)
			startx = foundAt
		else:
			startx = lastRow 	
	return(seqs)
		
		



if __name__== "__main__":
	
		upload_remote_path = BaseConfig.REMOTEDATAPATH
		sftpkey = RSAKey.from_private_key_file(BaseConfig.SFTPKEYFILENAME)
		sftp = SftpClient(BaseConfig.REMOTEDATAHOST,BaseConfig.SFTPPORT,BaseConfig.SFTPLOGINUSER,BaseConfig.SFTPPASSWORD,sftpkey)
		sftp.dirch(BaseConfig.REMOTEDATAPATH)
		fl = sftp.dirlist(upload_remote_path)
		fl.sort()
		print('fl=',fl)
		fl = [x for x in fl if (len(x.split('.')) > 1 and x.split('.')[1]=='xls')]
		if fl != None:
			lcd = loadCellDataMulti(BaseConfig.NSD,fl)
			datal = []
			for i, df in enumerate(lcd.dfs):
				nr = df.shape[0]
				if nr > 0:
					segmints = segMents(df)
					segments = ['\t'.join(x) for x in segmints]
					print(lcd.names[i],'segments=\n','\n'.join(segments))


# class encapsulating a loader for pi loadcell data
# ross lazarus 7 june 2019

import pandas as pd

import matplotlib as mpl
mpl.use('Agg') # headless!
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import time
import sys
import os
from dateutil import tz
from tzlocal import get_localzone
from paramiko import Transport, SFTPClient, RSAKey
tzl = get_localzone().zone
mdates.rcParams['timezone'] = tzl
NSD = 2.0
from config import BaseConfig


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
    def getfobj(self,fpath):
        return self._connection.file(fpath,'r')
        
    @classmethod
    def dirch(self,d):
        self._connection.chdir(d)
        
    @classmethod
    def dirlist(self,d):
        dlist = self._connection.listdir(d)
        l = [self._connection.normalize(x) for x in dlist]
        return l

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
        




class loadCellData():

    def __init__(self,nsd,infi):
        self.started = time.time()
        self.tzl = tzl
        self.nsd = nsd
        self.have_cache = False
        if infi:
            self.infile = infi
        else:
            self.infile = '/home/ross/rossgit/dashInFlask/data/loadcellsample55k.xls'
        df = pd.read_csv(self.infile,sep='\t')
        try:
            df['date'] = pd.to_datetime(df.iloc[:,0],unit='s')
        except:
            try:
                df['date'] = pd.to_datetime(df.iloc[:,0],format='%Y%m%d_%H%M%S')
            except:
                print('~~~~ cannot figure out date format')
        df.set_index(df['date'],inplace=True)
        df = df.tz_localize(tz=self.tzl)
        self.df = df.sort_index()
        ms = 2
        nrow = self.df.shape[0]
        if nrow > 1000:
            ms = 1
        if nrow > 10000:
            ms = 0.5
        if nrow > 100000:
            ms = 0.2
        self.ms = ms
        self.nrow = nrow
        self.trimcl()
 
    def trimcl(self):
        """ trim +/-nsd SD and ignore first IGSEC data as load cell settles a bit
        """
        firstone = float(self.df.iloc[0,0])
        firsttime = time.strftime('%H:%M:%S %d/%m/%Y',time.localtime(firstone))
        lastone = float(self.df.iloc[-1,0]) # easier to use the original epoch rather than the internal datetimes!
        lasttime = time.strftime('%H:%M:%S %d/%m/%Y',time.localtime(lastone))
        self.fstamp = time.strftime('%Y%m%d_%H%M%S',time.localtime(lastone))
        self.firsttime = firsttime
        self.lasttime = lasttime  
        if self.nsd:
            mene = self.df.iloc[:,1].mean()
            ci = self.df.iloc[:,1].std()*self.nsd
            ucl = mene + ci
            lcl = mene - ci
            notbig = self.df.iloc[:,1] < ucl
            df2 = self.df[notbig]
            notsmall = df2.iloc[:,1] > lcl
            df2 = df2[notsmall]
            nhi = sum(notbig==False)
            nlo = sum(notsmall==False)
            s = 'Trim +/- %.1f SD removed %d above %.2f and %d below %.2f\n' % (self.nsd,nhi,ucl,nlo,lcl)
            s2 = '##Before trim:\n %s\nAfter trim:\n %s' % (self.df.describe(),df2.describe())
            self.df = df2.sort_index()
        else:
            s = 'Raw untrimmed data'
            s2 = '##Raw:\n%s' % (self.df.describe())
        self.note = s2
        self.subt = s

class loadCellDataMulti():

    def __init__(self,nsd,fpath):
        print('fpath=%s' % fpath)
        self.started = time.time()
        tzl = get_localzone().zone
        print('####tzl=',tzl)
        self.tzl = tzl
        self.nsd = nsd
        self.have_cache = False
        self.upload_remote_path = BaseConfig.REMOTEDATAPATH
        sftpkey = RSAKey.from_private_key_file(BaseConfig.SFTPKEYFILENAME)
        self.sftp = SftpClient(BaseConfig.REMOTEDATAHOST,BaseConfig.SFTPPORT,BaseConfig.SFTPLOGINUSER,BaseConfig.SFTPPASSWORD,sftpkey)
        self.sftp.dirch(self.upload_remote_path)
        if fpath != None:
            self.infiles = fpath
        else:
            self.infiles = ['/home/ross/rossgit/dashInFlask/data/loadcellsample55k.xls',]
        self.dfs = []
        self.nrows = []
        self.mss = []
        for fname in self.infiles:
            with self.sftp.getfobj(fname) as f:
                df = pd.read_csv(f,sep='\t',header=None,names=['date','mass'])
            df['date'] = pd.to_datetime(df['date'],unit='s',utc=True).dt.tz_convert(tz=self.tzl)
            df.set_index(df['date'],inplace=True)
            dfsorted = df.sort_index()
            ms = 2
            nrow = df.shape[0]
            if nrow > 1000:
                ms = 1
            if nrow > 10000:
                ms = 0.5
            if nrow > 100000:
                ms = 0.2
            self.mss.append(ms)
            self.nrows.append(nrow)
            self.dfs.append(dfsorted)
 

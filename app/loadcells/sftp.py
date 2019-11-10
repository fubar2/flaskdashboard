from paramiko import Transport, SFTPClient, RSAKey
from config import BaseConfig


class SftpClient:
	"""
		to avoid writing anything to local rpi storage use remote file server
		A few hard failed sd cards lead me to this position :)
		Use with a public key certificate in the caller's ~/.ssh directory
		eg:
		
		def fileChooser(returnv = False):
    
			upload_remote_path = BaseConfig.REMOTEDATAPATH
			sftpkey = RSAKey.from_private_key_file(BaseConfig.SFTPKEYFILENAME)
			sftp = SftpClient(BaseConfig.REMOTEDATAHOST,BaseConfig.SFTPPORT,BaseConfig.SFTPLOGINUSER,BaseConfig.SFTPPASSWORD,sftpkey)
			sftp.dirch(upload_remote_path)
			fl = sftp.dirlist(upload_remote_path)
			fl.sort()
			fl = [x for x in fl if (x.split('.')[-1]=='xls')]
			ddl = []
			vals = []
			for fn in fl:
				ddl.append({'label':os.path.split(fn)[-1],'value': fn})
				vals.append(fn)
			if returnv:
				return vals
			else:
				return ddl



	"""

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
	def appendrows(cls, rows, remote_path):
		f = cls._connection.file(remote_path,'a')
		f.write(rows)
		f.close()
		return len(rows)

	@classmethod
	def dirch(cls,d):
		cls._connection.chdir(d)

	@classmethod
	def dirlist(cls,d):
		return cls._connection.listdir(d)

	@classmethod
	def getfobj(cls,fpath):
		return cls._connection.file(fpath,'r')
				
	def file_exists(self, remote_path):

		try:
			# print('remote path : ', remote_path)
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
			
	@classmethod
	def close(cls):
		cls._connection.close()
		




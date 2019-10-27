
class BaseConfig(self):
	
	SHORTSLEEP = 0.01
	SAMPINT = 30
	RUNCOOL = True

	USER = 'pi'
	REMLOGINUSER = 'ross'
	REMPATH = '/home/ross'
	UPREMPATHSKEL = '/home/ross/loadcelldata/scale%d.xls'
	FILEHOST = '192.168.1.9'
	SFTPPORT = 22
	SFTPPASSWORD = ''
	SFTPKEYFILENAME = '/home/%s/.ssh/id_rsa' % USER


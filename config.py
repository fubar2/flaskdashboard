import os
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig():
	SQLALCHEMY_DATABASE_URI = 'sqlite:////home/ross/rossgit/dashonflask.db'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	DEBUG = True
	SECRET_KEY = "fobarbaz and 0 spel1ng fuio-=dkjk"
	TESTING = True

	# Flask-User settings
	USER_APP_NAME = "Ross testing"      # Shown in and email templates and page footers
	USER_ENABLE_EMAIL = False      # Disable email authentication
	USER_ENABLE_USERNAME = True    # Enable username authentication
	USER_REQUIRE_RETYPE_PASSWORD = False    # Simplify register form
	REMOTEDATAHOST="192.168.1.9"
	REMOTEDATAPATH="/home/ross/loadcelldata/"


	USER = 'ross'
	SFTPLOGINUSER = 'ross'
	REMPATH = '/home/ross'
	SFTPLOGINUSER = 'ross'
	SFTPPORT = 22
	SFTPPASSWORD = ''
	SFTPKEYFILENAME = '/home/%s/.ssh/id_rsa' % USER
	DELTADOWN = 0.005
	DELTAUP = 0.05
	MINDURATION = 5 # minutes - ignore shorter events as unlikely to be informative
	NSD = 2 # sig digits
	ALWAYSKEEPN = 50 # always add last 50 to plot so can see what's happening lately when seeking watering events!
	CRONLOG='/home/ross/rossgit/pyCronPlug/watercron.log'

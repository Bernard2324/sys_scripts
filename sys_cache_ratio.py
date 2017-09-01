#!/usr/bin/env python

'''
Author: Maurice Green
Purpose: System Cache Hit Ratio
'''
import sys, os, re
import threading


class Proc(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		uname = os.uname()
		if uname[0] == 'Linux':
			self.proc = "/proc"
		else:
			print "OS: %s NOT Supported" % uname[0]
	
	
	def paths(self, *args):
		return os.path.join(self.proc, *(str(x) for x in args))
	
	def name(self, target_file):
		try:
			with open(target_file, 'r') as f:
				proc_name = f.readline()
			f.close()
			return proc_name
		except:
			pass

def get_pids():
	pids = []
	for inode in os.listdir('/proc'):
		if inode.isdigit():
			pids.append(inode)
		else:
			continue
	
	for pid in pids:
		get_hits(pid)
		

def get_hits(pid):
	byte_access = {
		'rchar:': 0,
		'syscr:': 0,
		'wchar:': 0,
		'syscw:': 0,
		'read_bytes:': 0,
		'write_bytes:': 0,
		'cancelled_write_bytes:': 0
	}
	proc = Proc()
	io_file = proc.paths(pid, 'io')
	pc_name = proc.name(proc.paths(pid,'comm'))
	with open(io_file, 'r') as ioholder: # Open /proc/<pid>/io 
		bytes_info = ioholder.read().split()
		ioholder.close()
	for label in bytes_info: # loop throug dictionary above, find label match in file, get corresponding value
		if label in byte_access.keys():
			byte_position = bytes_info.index(label)
			byte_access[label] = bytes_info[byte_position + 1]
	for bytelabel, value in byte_access.iteritems(): # calculate 
		if bytelabel == 'read_bytes:':
			miss_ratio_n = (100 * int(value))
		if bytelabel == 'rchar:':
			miss_ratio_d = int(value)
	try:
		miss_ratio = (float(miss_ratio_n)/float(miss_ratio_d))
		cache_hit_ratio = float(100 - miss_ratio)
		print
		print "=" * 100
		print "Process: %s\n" % pc_name
		print
		print "Cache Hit Ratio: %.2f%%" % float(cache_hit_ratio)
		print "Miss Hit Ratio: %.2f%%" % float(miss_ratio)
		print "=" * 100
	except:
		pass
	
if __name__ == "__main__":
	get_pids()

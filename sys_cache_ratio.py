#!/usr/bin/env python

from __future__ import print_function
import os
import re
import sys
import six
import threading

__author__ = 'Maurice Green'
__purpose__ = 'System Cahce Hit Ratio'


class Proc(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		uname = os.uname()
		if uname[0] == 'Linux':
			self.proc = "/proc"
		else:
			print("OS: {} NOT Supported".format(uname[0]))
	
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

proc = Proc()

def get_pids():
	pids = [inode for inode in os.listdir('/proc') if inode.isdigit()]
	return map(get_hits, pids)

def get_hits(pid):
	byte_access = dict()
	
	io_file = proc.paths(pid, 'io')
	pc_name = proc.name(proc.paths(pid,'comm'))

	with open(io_file, 'r') as ioholder:
		dtx = ioholder.read().split()
		for idx, sts in enumerate(dtx[::2]):
			byte_access[sts] = dtx[idx] if dtx[idx].isdigit() else dtx[idx+1]
		ioholder.close()

	miss_ratio_n = (100 * int(byte_access.get('read_bytes:')))
	miss_ratio_d = (int(byte_access.get('rchar:')))

	try:
		miss_ratio = (float(miss_ratio_n)/float(miss_ratio_d))
		cache_hit_ratio = float(100 - miss_ratio)
		
		print("=" * 100)
		print("Process: {}\n".format(pc_name))
		print("")
		print("Cache Hit Ratio: %.2f%%" % float(cache_hit_ratio))
		print("Miss Hit Ratio: %.2f%%" % float(miss_ratio))
		print("=" * 100)
	except ZeroDivisionError:
		pass


if __name__ == "__main__":
	get_pids()

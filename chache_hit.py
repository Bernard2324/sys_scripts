#!/usr/bin/env python

'''
Author: Maurice Green JR
License GPLv3
'''
import os, sys, re
import subprocess
from ConfigParser import *
# Get Agent PID
def get_pid(process):
	try: # check_output only works on python 2.7+
		pid_t = subprocess.check_output(['pidof', process]).split()[1]
		return pid_t
	except:
		ps = subprocess.Popen(['pidof', process], stdout=subprocess.PIPE).communicate()[0]
		pid_t = ps.split()[1]
		return pid_t

# Get All Agents
def get_process():
	global agents
	agents = []
	config = RawConfigParser()
	try:
		config.read('/path/to/file.ini')
	except:
		pass
	for ag in config.sections():
		if ag[:1].isdigit():
			if ag.endswith('_ignore_string'):
				continue
			new_agent = re.sub(r'\d+-', "", ag)
			agents.append(new_agent)
# Calc HIT Ratio
# Cache HIT Ratio = Cache Hits/Total Attempts (Hits + Misses)
def get_hits():
	byte_access = {
		'rchar:': 0,
		'syscr:': 0,
		'wchar:': 0,
		'syscw:': 0,
		'read_bytes:': 0,
		'write_bytes:': 0,
		'cancelled_write_bytes:': 0
	}
	# Get agentNames
	get_process()
	for agent in agents:
		pid = get_pid(agent)
		io_file = os.path.join('/proc',pid,'io')
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
		miss_ratio = (float(miss_ratio_n)/float(miss_ratio_d))
		cache_hit_ratio = float(100 - miss_ratio)
		print
		print "=" * 100
		print "Agent: %s\n" % agent
		print
		print "Cache Hit Ratio: %.2f%%" % float(cache_hit_ratio)
		print "Miss Hit Ratio: %.2f%%" % float(miss_ratio)
		print "=" * 100
			
if __name__ == "__main__":
	subprocess.call('clear', shell=True)
	get_hits()

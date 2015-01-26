#!/usr/bin/env python
import dosa
from subprocess import call
import random
import string
import urllib2
import fileinput
import shutil
import os
import sys
import time

CLUSTER_SIZE = 3
API_KEY = 'ad64ddd15bf37aa7157b30b3eada5d0d254936ae11d30e6c8ae386c9d2803d1c'
# dosa.set_debug()  # enables debug logs
client = dosa.Client(api_key=API_KEY)
HOME = os.environ['HOME']

# Remove the old config file if exists and copy new one
if os.path.isfile('./cloud-config'): os.remove('./cloud-config')
shutil.copyfile('./cloud-config.tmpl', './cloud-config')
# Generate and replace cluster id
cluster_id = urllib2.urlopen("https://discovery.etcd.io/new").read()
for line in fileinput.input("cloud-config", inplace=True):
	print(line.replace("https://discovery.etcd.io/b827b6e8fa78993a03e04944d834db45", cluster_id))
# Push cloud-config with new cluster id
call(["git", "add", "cloud-config"])
call(["git", "commit", "-m", "'cloud-config updated.'"])
call(["git", "push"])


# Create new droplets
x = 1
while x <= CLUSTER_SIZE:
	vm_gen_num = random.randint(11,99)
	vm_gen_let = random.choice(string.ascii_lowercase)
	status, result = client.droplets.create(name='Dmitry.CoreOS.test' + str(vm_gen_num) + str(vm_gen_let), region='nyc3',\
		size='4gb', image='coreos-stable', private_networking='true', ssh_keys=['534374'])
	new_droplet_id = result['droplet']['id']
	new_droplet = client.Droplet(new_droplet_id)
	# Wait for IP address allocation
	time.sleep(10)
	# Get public IP address of droplet
	pub_ip = new_droplet.ip_addresses()[1]
	# Clean ssh key fingerprint
	call(["ssh-keygen", "-R", pub_ip])
	# Configure droplet for DEIS cluster
	# call(["/usr/bin/ssh", "-o StrictHostKeyChecking=no", "-o PasswordAuthentication=no", "core@" + pub_ip, "sudo /usr/bin/coreos-cloudinit --from-url=https://raw.githubusercontent.com/freeminder/deis_cluster_automation/master/cloud-config"])
	call(["/usr/bin/scp", "-o StrictHostKeyChecking=no", "-o PasswordAuthentication=no", "cloud-config", "core@" + pub_ip + ":~/"])
	call(["/usr/bin/ssh", "-o StrictHostKeyChecking=no", "-o PasswordAuthentication=no", "core@" + pub_ip, "sudo /usr/bin/coreos-cloudinit --from-file=cloud-config"])
	x += 1


# Tag the master
call(["/usr/bin/scp", "-o StrictHostKeyChecking=no", "-o PasswordAuthentication=no", "fleet.conf", "core@" + pub_ip + ":~/"])
call(["/usr/bin/ssh", "-o StrictHostKeyChecking=no", "-o PasswordAuthentication=no", "core@" + pub_ip, "sudo mkdir -p /etc/fleet && sudo mv fleet.conf /etc/fleet/ && sudo systemctl restart fleet"])
# DEIS installation
call(["ssh-agent", "-s"])
call(["ssh-add", HOME + "/.ssh/id_rsa"])

os.environ['DEISCTL_TUNNEL'] = pub_ip
call(["deisctl", "config", "platform", "set", "sshPrivateKey=" + HOME + "/.ssh/id_rsa"])
call(["deisctl", "config", "platform", "set", "domain=deis." + pub_ip + ".xip.io"])
call(["deisctl", "install", "platform"])
call(["deisctl", "start", "platform"])

call(["deis", "register", "http://deis." + pub_ip + ".xip.io"])
call(["deis", "keys:add"])

os.chdir("../btsync_local_test2/")
call(["deis", "create"])
call(["deis", "tags:set", "environ=prod,master=true"])
call(["git", "push", "deis", "master"])

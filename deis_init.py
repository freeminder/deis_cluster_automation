#!/usr/bin/env python
import dosa
from subprocess import call
import urllib2
import fileinput
import shutil
import os

API_KEY = 'ad64ddd15bf37aa7157b30b3eada5d0d254936ae11d30e6c8ae386c9d2803d1c'
dosa.set_debug()  # enables debug logs
client = dosa.Client(api_key=API_KEY)


# Remove the old config file if exists and copy new one
if os.path.isfile('./cloud-config'): os.remove('./cloud-config')
shutil.copyfile('./cloud-config.tmpl', './cloud-config')

# Generate, replace and push new cluster id
cluster_id = urllib2.urlopen("https://discovery.etcd.io/new").read()
for line in fileinput.input("cloud-config", inplace=True):
    print(line.replace("https://discovery.etcd.io/b827b6e8fa78993a03e04944d834db45", cluster_id))

call(["git", "add", "cloud-config"])
call(["git", "commit", "-m", "'cloud-config updated.'"])
call(["git", "push"])


# Create new droplet
vm_gen_num = randint(2,99)
status, result = client.droplets.create(name='Dmitry.CoreOS.test' + vm_gen_num, region='nyc3',\
    size='4gb', image='coreos-stable', private_networking='true', ssh_keys=['534374'])
new_droplet_id = result['droplet']['id']
new_droplet = client.Droplet(new_droplet_id)
pub_ip = new_droplet.ip_addresses()[1]
call(["/usr/bin/ssh", "core@" + pub_ip, "sudo /usr/bin/coreos-cloudinit --from-url=https://raw.githubusercontent.com/freeminder/deis_cluster_automation/master/cloud-config"])

# Configure DEIS cluster
new_droplet = client.Droplet(new_droplet_id)
pub_ip = new_droplet.ip_addresses()[1]
call(["/usr/bin/ssh", "core@" + pub_ip, "sudo /usr/bin/coreos-cloudinit --from-url=https://raw.githubusercontent.com/freeminder/deis_cluster_automation/master/cloud-config"])















# SSH Keys
# pub_key = open('~/.ssh/id_rsa.pub').read()
# client.keys.create(name='RSA key', public_key=pub_key)
# client.keys.list()

# Images
# client.images.list()

## shortcuts
# new_droplet.status()
# client.droplets.list()
# print(new_droplet.info())
# client.droplets.delete(new_droplet_id)

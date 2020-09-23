"""This profile sets up a simple NFS server and a network of clients. The NFS server uses
a long term dataset that is persistent across experiments. In order to use this profile,
you will need to create your own dataset and use that instead of the demonstration 
dataset below. If you do not need persistant storage, we have another profile that
uses temporary storage (removed when your experiment ends) that you can use. 

Instructions:
Click on any node in the topology and choose the `shell` menu item. Your shared NFS directory is mounted at `/nfs` on all nodes."""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Import the Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal context.
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Only Ubuntu images supported.
imageList = [
    ('urn:publicid:IDN+clemson.cloudlab.us+image+cops-PG0:lrb_omr.nfs', 'WEBCACHESIM_SNAPSHOT'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD', 'UBUNTU 18.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU16-64-STD', 'UBUNTU 16.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU14-64-STD', 'UBUNTU 14.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD', 'CENTOS 7'),
]

# Do not change these unless you change the setup scripts too.
nfsServerName = "nfs"
nfsLanName    = "nfsLan"
nfsDirectory  = "/nfs"

# Number of NFS clients (there is always a server)
pc.defineParameter("clientCount", "Number of NFS clients",
                   portal.ParameterType.INTEGER, 2)

pc.defineParameter("osImage", "Select OS image",
                   portal.ParameterType.IMAGE,
                   imageList[0], imageList)

pc.defineParameter("DATASET", "URN of your dataset", 
                   portal.ParameterType.STRING,
                   "urn:publicid:IDN+clemson.cloudlab.us:lrbplus-pg0+ltdataset+cacheDataset")

pc.defineParameter("DATASET2", "URN of your dataset2", 
                   portal.ParameterType.STRING,
                   "urn:publicid:IDN+clemson.cloudlab.us:cops-pg0+ltdataset+lrb-256-6")

# Always need this when using parameters
params = pc.bindParameters()

# The NFS network. All these options are required.
nfsLan = request.LAN(nfsLanName)
nfsLan.best_effort       = True
nfsLan.vlan_tagging      = True
nfsLan.link_multiplexing = True

# The NFS server.
nfsServer = request.RawPC(nfsServerName)
nfsServer.disk_image = params.osImage
# Attach server to lan.
nfsLan.addInterface(nfsServer.addInterface())
# Initialization script for the server
nfsServer.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-server.sh"))
nfsServer.addService(pg.Execute(shell="sh", command="sudo /bin/echo ServerAliveInterval 60 >> /users/yangdsh/.ssh/config"))

# Special node that represents the ISCSI device where the dataset resides
dsnode = request.RemoteBlockstore("dsnode", "/nfs")
dsnode.dataset = params.DATASET

# Link between the nfsServer and the ISCSI device that holds the dataset
dslink = request.Link("dslink")
dslink.addInterface(dsnode.interface)
dslink.addInterface(nfsServer.addInterface())
# Special attributes for this link that we must use.
dslink.best_effort = True
dslink.vlan_tagging = True
dslink.link_multiplexing = True

if len(params.DATASET2) > 1:
    # Special node that represents the ISCSI device where the dataset resides
    dsnode2 = request.RemoteBlockstore("dsnode2", "/nfs2")
    dsnode2.dataset = params.DATASET2

    # Link between the nfsServer and the ISCSI device that holds the dataset
    dslink2 = request.Link("dslink2")
    dslink2.addInterface(dsnode2.interface)
    dslink2.addInterface(nfsServer.addInterface())
    # Special attributes for this link that we must use.
    dslink2.best_effort = True
    dslink2.vlan_tagging = True
    dslink2.link_multiplexing = True

# The NFS clients, also attached to the NFS lan.
for i in range(1, params.clientCount+1):
    node = request.RawPC("node%d" % i)
#    node.hardware_type = "d710"
    node.disk_image = params.osImage
    nfsLan.addInterface(node.addInterface())
    # Initialization script for the clients
    node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-client.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo /bin/cp /local/repository/.bashrc /users/yangdsh/"))
    node.addService(pg.Execute(shell="sh", command="sudo /bin/cat /local/repository/id_rsa.pub >> /users/yangdsh/.ssh/authorized_keys"))
    node.addService(pg.Execute(shell="sh", command="sudo /bin/echo ServerAliveInterval 60 >> /users/yangdsh/.ssh/config"))
    pass

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)

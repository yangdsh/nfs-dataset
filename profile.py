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
    ('urn:publicid:IDN+clemson.cloudlab.us+image+lrbplus-PG0:cachelib_new', 'UBUNTU 18.04 ML'),
    ('urn:publicid:IDN+clemson.cloudlab.us+image+cops-PG0:webcachesim_ubuntu18', 'UBUNTU 18.04'),
    ('urn:publicid:IDN+clemson.cloudlab.us+image+lrbplus-PG0:ubuntu18-cachelib', 'UBUNTU 18.04 new')
]

# Do not change these unless you change the setup scripts too.
nfsServerName = "nfs"
nfsLanName    = "nfsLan"
nfsDirectory  = "/nfs"

# Number of NFS clients (there is always a server)
pc.defineParameter("clientCount", "Number of NFS clients",
                   portal.ParameterType.INTEGER, 2)

pc.defineParameter("rwclone", "Dataset clone mode flag",
                   portal.ParameterType.INTEGER, 0)

pc.defineParameter("osImage", "Select OS image",
                   portal.ParameterType.STRING,
                   "urn:publicid:IDN+clemson.cloudlab.us+image+lrbplus-PG0:cachelib2023")

pc.defineParameter("DATASET", "URN of your dataset", 
                   portal.ParameterType.STRING,
                   "urn:publicid:IDN+clemson.cloudlab.us:lrbplus-pg0+ltdataset+cacheDataset")

pc.defineParameter("Hardware", "hardware", 
                   portal.ParameterType.STRING,
                   "r6525")

pc.defineParameter("Hardware_nfs", "hardware_nfs", 
                   portal.ParameterType.STRING,
                   "c6320")

# Always need this when using parameters
params = pc.bindParameters()

# The NFS network. All these options are required.
nfsLan = request.LAN(nfsLanName)
nfsLan.best_effort       = True
nfsLan.vlan_tagging      = True
nfsLan.link_multiplexing = True

# The NFS server.
nfsServer = request.RawPC(nfsServerName)
nfsServer.hardware_type = params.Hardware_nfs
nfsServer.disk_image = params.osImage
bs = nfsServer.Blockstore("bs0", "/nfs2")
bs.size = "50GB"
# Attach server to lan.
nfsLan.addInterface(nfsServer.addInterface())
# Initialization script for the server
nfsServer.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-server.sh"))
nfsServer.addService(pg.Execute(shell="sh", command="sudo /bin/cp /local/repository/.bashrc /users/yangdsh/"))

if len(params.DATASET) > 1:
    # Special node that represents the ISCSI device where the dataset resides
    dsnode = request.RemoteBlockstore("dsnode", "/nfs")
    dsnode.dataset = params.DATASET
    dsnode.rwclone = params.rwclone
    
    # Link between the nfsServer and the ISCSI device that holds the dataset
    dslink = request.Link("dslink")
    dslink.addInterface(dsnode.interface)
    dslink.addInterface(nfsServer.addInterface())
    # Special attributes for this link that we must use.
    dslink.best_effort = True
    dslink.vlan_tagging = True
    dslink.link_multiplexing = True

# The NFS clients, also attached to the NFS lan.
for i in range(1, params.clientCount+1):
    node = request.RawPC("node%d" % i)
    node.hardware_type = params.Hardware
    node.disk_image = params.osImage
    bs = node.Blockstore("bs"+str(i), "/nfs2")
    bs.size = "50GB"
    nfsLan.addInterface(node.addInterface())
    # Initialization script for the clients
    node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-client.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo /bin/cp /local/repository/.bashrc /users/yangdsh/"))
    pass

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)

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
    ('urn:publicid:IDN+utah.cloudlab.us+image+lrbplus-PG0:cachelib-http', 'UBUNTU 18.04'),
]

# Do not change these unless you change the setup scripts too.
nfsServerName = "nfs"
nfsLanName    = "nfsLan"
nfsDirectory  = "/nfs"

# Number of NFS clients (there is always a server)
pc.defineParameter("clientCount", "Number of NFS clients",
                   portal.ParameterType.INTEGER, 2)

pc.defineParameter("phystype",  "Optional physical node type",
                   portal.ParameterType.STRING, "c6525-25g",
                   longDescription="Specify a physical node type (pc3000,d710,etc) " +
                   "instead of letting the resource mapper choose for you.")

pc.defineParameter("osImage", "Select OS image",
                   portal.ParameterType.IMAGE,
                   imageList[0], imageList)

pc.defineParameter("DATASET", "URN of your dataset", 
                   portal.ParameterType.STRING,
                   "urn:publicid:IDN+utah.cloudlab.us:lrbplus-pg0+ltdataset+cache_traces")

pc.defineParameter("DATASET2", "URN of your dataset2", 
                   portal.ParameterType.STRING,
                   "")

# Always need this when using parameters
params = pc.bindParameters()

# The NFS network. All these options are required.
nfsLan = request.LAN(nfsLanName)
nfsLan.best_effort       = True
nfsLan.vlan_tagging      = True
nfsLan.link_multiplexing = True

cachelan = request.LAN('cacheLan')

# The NFS server.
nfsServer = request.RawPC(nfsServerName)
nfsServer.disk_image = params.osImage
nfsServer.hardware_type = params.phystype
# Attach server to lan.
nfsLan.addInterface(nfsServer.addInterface())

iface = nfsServer.addInterface("eth2", pg.IPv4Address('192.168.1.1','255.255.255.0'))
cachelan.addInterface(iface)
# Initialization script for the server
nfsServer.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-server.sh"))
nfsServer.addService(pg.Execute(shell="sh", command="sudo /bin/cp /local/repository/.bashrc /users/yangdsh/"))
nfsServer.addService(pg.Execute(shell="sh", command="sudo cp /proj/lrbplus-PG0/workspaces/yangdsh/id_rsa /users/yangdsh/.ssh/"))
nfsServer.addService(pg.Execute(shell="sh", command="sudo chown yangdsh /users/yangdsh/.ssh/id_rsa"))

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

# The NFS clients, also attached to the NFS lan.
for i in range(1, params.clientCount+1):
    node = request.RawPC("node%d" % i)
    node.hardware_type = params.phystype
    node.disk_image = params.osImage
    nfsLan.addInterface(node.addInterface())
    iface = node.addInterface("eth2", pg.IPv4Address('192.168.1.%d' % (i+1),'255.255.255.0'))
    cachelan.addInterface(iface)
    # Initialization script for the clients
    node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-client.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo /bin/cp /local/repository/.bashrc /users/yangdsh/"))
    nfsServer.addService(pg.Execute(shell="sh", command="sudo cp /proj/lrbplus-PG0/workspaces/yangdsh/id_rsa /users/yangdsh/.ssh/"))
    nfsServer.addService(pg.Execute(shell="sh", command="sudo chown yangdsh /users/yangdsh/.ssh/id_rsa"))
    pass

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)

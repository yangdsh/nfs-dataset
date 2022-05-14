"""Variable number of nodes in a lan. You have the option of picking from one
of several standard images we provide, or just use the default (typically a recent
version of Ubuntu). You may also optionally pick the specific hardware type for
all the nodes in the lan. 
Instructions:
Wait for the experiment to start, and then log into one or more of the nodes
by clicking on them in the toplogy, and choosing the `shell` menu option.
Use `sudo` to run root commands. 
"""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal context, needed to defined parameters
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Variable number of nodes.
pc.defineParameter("nodeCount", "Number of Nodes", portal.ParameterType.INTEGER, 2,
                   longDescription="If you specify more then one node, " +
                   "we will create a lan for you.")

pc.defineParameter("osImage", "Select OS image",
                   portal.ParameterType.STRING,
                   "urn:publicid:IDN+utah.cloudlab.us+image+cops-PG0:lrb")

# Optional physical type for all nodes.
pc.defineParameter("phystype",  "Optional physical node type",
                   portal.ParameterType.STRING, "c6525-25g",
                   longDescription="Specify a physical node type (pc3000,d710,etc) " +
                   "instead of letting the resource mapper choose for you.")

# remote dataset
pc.defineParameter("DATASET", "URN of your dataset dataset", 
                   portal.ParameterType.STRING,
                   "urn:publicid:IDN+utah.cloudlab.us:cops-pg0+ltdataset+lrb")

pc.defineParameter("firstNodeRWDataset",  "Mount dataset in rw instead of rwclone on the first node",
                   portal.ParameterType.BOOLEAN, False)


# Optionally create XEN VMs instead of allocating bare metal nodes.
pc.defineParameter("useVMs",  "Use XEN VMs",
                   portal.ParameterType.BOOLEAN, False,
                   longDescription="Create XEN VMs instead of allocating bare metal nodes.")

# Optional link speed, normally the resource mapper will choose for you based on node availability
pc.defineParameter("linkSpeed", "Link Speed",portal.ParameterType.INTEGER, 0,
                   [(0,"Any"),(100000,"100Mb/s"),(1000000,"1Gb/s"),(10000000,"10Gb/s"),(25000000,"25Gb/s"),(100000000,"100Gb/s")],
                   longDescription="A specific link speed to use for your lan. Normally the resource " +
                   "mapper will choose for you based on node availability and the optional physical type.")
                   
# For very large lans you might to tell the resource mapper to override the bandwidth constraints
# and treat it a "best-effort"
pc.defineParameter("bestEffort",  "Best Effort", portal.ParameterType.BOOLEAN, False,
                    longDescription="For very large lans, you might get an error saying 'not enough bandwidth.' " +
                    "This options tells the resource mapper to ignore bandwidth and assume you know what you " +
                    "are doing, just give me the lan I ask for (if enough nodes are available).")

# Optional ephemeral blockstore
pc.defineParameter("tempFileSystemSize", "Temporary Filesystem Size",
                   portal.ParameterType.INTEGER, 0,
                   longDescription="The size in GB of a temporary file system to mount on each of your " +
                   "nodes. Temporary means that they are deleted when your experiment is terminated. " +
                   "The images provided by the system have small root partitions, so use this option " +
                   "if you expect you will need more space to build your software packages or store " +
                   "temporary files.")
                   
# Instead of a size, ask for all available space. 
pc.defineParameter("tempFileSystemMax",  "Temp Filesystem Max Space",
                    portal.ParameterType.BOOLEAN, False,
                    longDescription="Instead of specifying a size for your temporary filesystem, " +
                    "check this box to allocate all available disk space. Leave the size above as zero.")

pc.defineParameter("tempFileSystemMount", "Temporary Filesystem Mount Point",
                   portal.ParameterType.STRING,"/mydata",
                   longDescription="Mount the temporary file system at this mount point; in general you " +
                   "you do not need to change this, but we provide the option just in case your software " +
                   "is finicky.")

# Optional number of network interfaces
pc.defineParameter("numNetworkInterface", "Number of Network Interface Except the Control Interface",
                   portal.ParameterType.INTEGER, 1,
                  longDescription="Number of Network Interface Except the Control Interface. On machine i interface j, the ip will be 192.168.{j+1}.{i}")

# Only Ubuntu images supported.
imageList = [
    ('urn:publicid:IDN+clemson.cloudlab.us+image+lrbplus-PG0:cachelib_new', 'UBUNTU 18.04 ML'),
    ('urn:publicid:IDN+clemson.cloudlab.us+image+cops-PG0:webcachesim_ubuntu18', 'UBUNTU 18.04'),
    ('urn:publicid:IDN+clemson.cloudlab.us+image+lrbplus-PG0:ubuntu18-cachelib', 'UBUNTU 18.04 new')
]

pc.defineParameter("osImage", "Select OS image",
                   portal.ParameterType.IMAGE,
                   "urn:publicid:IDN+utah.cloudlab.us+image+lrbplus-PG0:cachelib-http")

pc.defineParameter("DATASET", "URN of your dataset", 
                   portal.ParameterType.STRING,
                   "urn:publicid:IDN+utah.cloudlab.us:lrbplus-pg0+ltdataset+cache_traces")

# Always need this when using parameters
params = pc.bindParameters()

pc.verifyParameters()
nodes = []

lans = []
# Create link/lan.
for j in range(params.numNetworkInterface):
  if params.nodeCount > 1:
      if params.nodeCount == 2:
          lan = request.Link()
      else:
          lan = request.LAN()
      # if params.bestEffort:
      #     lan.best_effort = True
      # if params.linkSpeed > 0:
      #     lan.bandwidth = params.linkSpeed
      lans.append(lan)

# Process nodes, adding to link or lan.
for i in range(params.nodeCount):
    # Create a node and add it to the request
    if params.useVMs:
        name = "vm" + str(i)
        node = request.XenVM(name)
    else:
        name = "node" + str(i)
        node = request.RawPC(name)
        nodes.append(node)

    if params.osImage and params.osImage != "default":
        node.disk_image = params.osImage
    if params.nodeCount > 1:
        for j in range(params.numNetworkInterface):
          iface = node.addInterface("eth%d" % (j+1), pg.IPv4Address('192.168.%d.%d' % (j, i + 1),'255.255.255.0'))
          lans[j].addInterface(iface)
    # Optional hardware type.
    if params.phystype != "":
        node.hardware_type = params.phystype
    # Optional Blockstore
    if params.tempFileSystemSize > 0 or params.tempFileSystemMax:
        bs = node.Blockstore(name + "-bs", params.tempFileSystemMount)
        if params.tempFileSystemMax:
            bs.size = "0GB"
        else:
            bs.size = str(params.tempFileSystemSize) + "GB"
        bs.placement = "any"
    # Link between the nfsServer and the ISCSI device that holds the dataset
    if params.DATASET != "":
      # We need a link to talk to the remote file system, so make an interface.
      iface = node.addInterface()

      # The remote file system is represented by special node.
      fsnode = request.RemoteBlockstore("fsnode" + str(i), "/nfs")
      # This URN is displayed in the web interfaace for your dataset.
      fsnode.dataset = params.DATASET
      #
      # The "rwclone" attribute allows you to map a writable copy of the
      # indicated SAN-based dataset. In this way, multiple nodes can map
      # the same dataset simultaneously. In many situations, this is more
      # useful than a "readonly" mapping. For example, a dataset
      # containing a Linux source tree could be mapped into multiple
      # nodes, each of which could do its own independent,
      # non-conflicting configure and build in their respective copies.
      # Currently, rwclones are "ephemeral" in that any changes made are
      # lost when the experiment mapping the clone is terminated.
      if (i > 0) or (not params.firstNodeRWDataset):
        fsnode.rwclone = True

      # Now we add the link between the node and the special node
      fslink = request.Link("fslink" + str(i))
      fslink.addInterface(iface)
      fslink.addInterface(fsnode.interface)
      
      # Special attributes for this link that we must use.
      fslink.best_effort = True
      fslink.vlan_tagging = True
      # Initialization script for the clients
      node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-client.sh"))
      node.addService(pg.Execute(shell="sh", command="sudo /bin/cp /local/repository/.bashrc /users/yangdsh/"))
      node.addService(pg.Execute(shell="sh", command="sudo cp /proj/lrbplus-PG0/workspaces/yangdsh/webcachesim/passwd /etc/passwd"))
      node.addService(pg.Execute(shell="sh", command="sudo cp /proj/lrbplus-PG0/workspaces/yangdsh/webcachesim/id_rsa /users/yangdsh/.ssh/"))
      node.addService(pg.Execute(shell="sh", command="sudo chown yangdsh /users/yangdsh/.ssh/id_rsa"))

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)

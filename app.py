from base import base
from tabulate import tabulate
from os import system, name
from git import Repo
from shutil import copyfile
import json
def run():
  conn = base.connect().create_connection() 
  externalNetworks = getExternalNetworks(conn)
  stacks = getStacks(conn)
  keys = getKeys(conn)
  images = getImages(conn)
  routers = getRouters(conn)
  flavors = getFlavors(conn)
  ports = getPorts(conn)
  generateEnvFile(externalNetworks,stacks,keys,images,routers,flavors, ports)
  
def getFlavors(conn):
  flavors = conn.compute.flavors()
  return flavors

def getPorts(conn):
  ports = conn.network.ports()
  return ports

def getExternalNetworks(conn):
  externalNetworks = conn.network.networks(is_router_external=True)
  return externalNetworks

def getStacks(conn):
  stacks = conn.orchestration.stacks()
  return stacks

def getKeys(conn):
  keys = conn.compute.keypairs()
  return keys

def getImages(conn):
  images = conn.image.images(visibility="public")
  return images

def getRouters(conn):
  routers = conn.network.routers()
  return routers

def ListGen(obj):
  returnObject = []
  setupHeaders = []
  setupHeaders.append("ID")
  setupHeaders.append("Name")
  setupHeaders.append("GUID")
  returnObject.append(setupHeaders)
  id = 1
  for item in obj:
    tempList = []
    tempList.append(id)
    tempList.append(item.name)
    tempList.append(item.id)
    returnObject.append(tempList)
    id += 1
  return returnObject

def printItem(obj):
  print(tabulate(obj,headers="firstrow"))

def printIntro():
  clear()
  print("#### UKCloud Loadbalancer Heat Template Generator app ####")
  print("This application will help you to generate a template file that can be used with UKCloud HaProxy on OpenStack heat templates")
  print("The HaProxy on OpenStack heat templates deploy a pair of servers running haproxy and keepalived, these can be used to provide loadbalancing services")
  print("It will create a new front end network for the loadbalancers to sit on, this will need to be connected to a router, which has a connection to both the external network you wish to serve, and the backend network that the target servers exist on. Alternativly you can use the template to build a new netwok and deploy both your loadbalancers and back end servers to the same network.")
  print("You can also provide a haproxy config file, and this will be auto uploaded to the new instnces")
  print("Caching information")
  run()

def clear():
  print(chr(27)+'[2j')
  print('\033c')
  print('\x1bc')

def generateEnvFile(externalNetworks,stacks,keys,images,routers,flavors, ports):
  externalNetworkList = ListGen(externalNetworks)
  keyPairList = ListGen(keys)
  imageList = ListGen(images)
  flavorList = ListGen(flavors)
  rooterList = ListGen(routers)
  stackName = input("Please enter the name for the stack: ")
  printItem(externalNetworkList)
  externalNetworkSelection = int(input("Please select an external network that this loadbalancer will service: "))
  printItem(rooterList)
  routerSelection = int(input("Please select router you want to connect your new network to: "))
  printItem(imageList)
  imageSelection = int(input("Please select which image you wish to use (Only Centos is currently supported): "))
  printItem(flavorList)
  flavorSelection = int(input("Please select which flavor you wish to use (t1.small is usuall enough for most applications): "))
  printItem(keyPairList)
  keypairSlection = int(input("Please select which keypair you wish to use: "))
  serverNames = input("What do you wish your servers to be called (E.G. blog-balancers): ")
  networkName = input("Please enter the name of the new network you wish to create: ")
  netowrkCIDR = input("Please enter the network CIDR you wish the network to use (E.G. 10.0.0.0/24): ") 
  DNS = input("Please enter the DNS servers you wish your loadbalancers to use (E.G. 8.8.8.8): ")
  haProxyConfig = input("Please enter the location for your custom haproxy config (full path), leave blank to use the default (This will need to be customised to work): ")
  haProxyPorts = input("Please enter the ports you will access your services on, or leave blank for 80 and 443 (Enter as comma delimited: ")

  selectedExternalNetwork = externalNetworkList[externalNetworkSelection][2]
  selectedRooter = rooterList[routerSelection][2]
  selectedImage = imageList[imageSelection][2]
  selectedFlavor = flavorList[flavorSelection][2]
  selectedKeyPair = keyPairList[keypairSlection][2]
  cloneHaProxyRepo(stackName)
  writeEnvfile(stackName,serverNames,networkName,netowrkCIDR,DNS,haProxyConfig,selectedExternalNetwork,selectedRooter,selectedImage,selectedFlavor,selectedKeyPair,haProxyPorts)

def cloneHaProxyRepo(stackName):
  data = Repo.clone_from("https://github.com/UKCloud/haproxy-on-openstack.git", stackName)
  data.git.checkout('hotfix/updating_to_work_with_newton')

def copyHaProxyConfig(stackName,haProxyConfigLocation):
  copyfile(haProxyConfigLocation, stackName + "/files/haproxy.cfg")

def writeEnvfile(stackName,serverNames,networkName,netowrkCIDR,DNS,haProxyConfig,selectedExternalNetwork,selectedRooter,selectedImage,selectedFlavor,selectedKeyPair,haProxyPorts):
  f = open(stackName + "/" + stackName + "_enviroment.yaml", "a")
  f.write("parameters:"  + "\n")
  f.write("  key_name: " + selectedKeyPair +"\n")
  f.write("  flavor: " + selectedFlavor + "\n")
  f.write("  image: " + selectedImage + "\n")
  f.write("  router: " + selectedRooter + "\n")
  f.write("  external_network: " + selectedExternalNetwork + "\n")
  f.write("  vrrp_subnet_cidr: " + netowrkCIDR + "\n")
  f.write("  vrrp_subnet_dns: " + DNS + "\n")
  f.write("  haproxy_ports: " + "'" + haProxyPorts + "'" + "\n")
  f.write("  server_name: " + serverNames + "\n")
  f.write("  frontend_network_name: " + networkName + "\n")
  if haProxyConfig:
    copyHaProxyConfig(stackName,haProxyConfig)
  print("Now run: openstack stack create -t " + stackName + "/haproxy.yaml -e " + stackName + "/" + stackName + "_enviroment.yaml" + " --wait " + stackName)
   

if __name__ == "__main__":
  printIntro()

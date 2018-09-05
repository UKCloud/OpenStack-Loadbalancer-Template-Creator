from base import base
from tabulate import tabulate
from git import Repo
from shutil import copyfile

def run():
    conn = base.connect().create_connection()
    external_networks = get_external_networks(conn)
    keys = get_keys(conn)
    images = get_images(conn)
    routers = get_routers(conn)
    flavors = get_flavors(conn)
    generateEnvFile(external_networks, keys, images, routers, flavors)

def get_flavors(conn):
    flavors = conn.compute.flavors()
    return flavors

def get_external_networks(conn):
    external_networks = conn.network.networks(is_router_external=True)
    return external_networks


def get_keys(conn):
    keys = conn.compute.keypairs()
    return keys

def get_images(conn):
    images = conn.image.images(visibility="public")
    return images

def get_routers(conn):
    routers = conn.network.routers()
    return routers

def list_gen(obj):
    return_object = []
    setup_headers = []
    setup_headers.append("ID")
    setup_headers.append("Name")
    setup_headers.append("GUID")
    return_object.append(setup_headers)
    id = 1
    for item in obj:
        temp_list = []
        temp_list.append(id)
        temp_list.append(item.name)
        temp_list.append(item.id)
        return_object.append(temp_list)
        id += 1
    return return_object

def print_item(obj):
    print(tabulate(obj, headers="firstrow"))

def print_intro():
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

def generateEnvFile(external_networks, keys, images, routers, flavors):
    external_network_list = list_gen(external_networks)
    key_pair_list = list_gen(keys)
    imgae_list = list_gen(images)
    flavor_list = list_gen(flavors)
    rooter_list = list_gen(routers)
    stack_name = input("Please enter the name for the stack: ")
    print_item(external_network_list)
    external_network_selection = int(input("Please select an external network that this loadbalancer will service: "))
    print_item(rooter_list)
    rooter_selection = int(input("Please select router you want to connect your new network to: "))
    print_item(imgae_list)
    image_selection = int(input("Please select which image you wish to use (Only Centos is currently supported): "))
    print_item(flavor_list)
    flavor_selection = int(input("Please select which flavor you wish to use (t1.small is usuall enough for most applications): "))
    print_item(key_pair_list)
    key_pair_selection = int(input("Please select which keypair you wish to use: "))
    server_names = input("What do you wish your servers to be called (E.G. blog-balancers): ")
    network_name = input("Please enter the name of the new network you wish to create: ")
    netowrk_cidr = input("Please enter the network CIDR you wish the network to use (E.G. 10.0.0.0/24): ")
    dns = input("Please enter the dns servers you wish your loadbalancers to use (E.G. 8.8.8.8): ")
    ha_proxy_config = input("Please enter the location for your custom haproxy config (full path), leave blank to use the default (This will need to be customised to work): ")
    ha_proxy_ports = input("Please enter the ports you will access your services on, or leave blank for 80 and 443 (Enter as comma delimited: ")

    selected_external_network = external_network_list[external_network_selection][2]
    selected_rooter = rooter_list[rooter_selection][2]
    selected_image = imgae_list[image_selection][2]
    selected_flavor = flavor_list[flavor_selection][2]
    selected_key_pair = key_pair_list[key_pair_selection][2]
    clone_ha_proxy_repo(stack_name)
    write_env_file(stack_name, server_names, network_name, netowrk_cidr, dns, ha_proxy_config, selected_external_network, selected_rooter, selected_image, selected_flavor, selected_key_pair, ha_proxy_ports)

def clone_ha_proxy_repo(stack_name):
    data = Repo.clone_from("https://github.com/UKCloud/haproxy-on-openstack.git", stack_name)
    data.git.checkout('hotfix/updating_to_work_with_newton')

def copy_ha_proxy_config(stack_name, ha_proxy_config_location):
    copyfile(ha_proxy_config_location, stack_name + "/files/haproxy.cfg")

def write_env_file(stack_name, server_names, network_name, netowrk_cidr, dns, ha_proxy_config, selected_external_network, selected_rooter, selected_image, selected_flavor, selected_key_pair, ha_proxy_ports):
    f = open(stack_name + "/" + stack_name + "_enviroment.yaml", "a")
    f.write("parameters:"  + "\n")
    f.write("  key_name: " + selected_key_pair +"\n")
    f.write("  flavor: " + selected_flavor + "\n")
    f.write("  image: " + selected_image + "\n")
    f.write("  router: " + selected_rooter + "\n")
    f.write("  external_network: " + selected_external_network + "\n")
    f.write("  vrrp_subnet_cidr: " + netowrk_cidr + "\n")
    f.write("  vrrp_subnet_dns: " + dns + "\n")
    f.write("  haproxy_ports: " + "'" + ha_proxy_ports + "'" + "\n")
    f.write("  server_name: " + server_names + "\n")
    f.write("  frontend_network_name: " + network_name + "\n")
    if ha_proxy_config:
        copy_ha_proxy_config(stack_name, ha_proxy_config)
    print("Now run: openstack stack create -t " + stack_name + "/haproxy.yaml -e " + stack_name + "/" + stack_name + "_enviroment.yaml" + " --wait " + stack_name)


if __name__ == "__main__":
    print_intro()

import os
from openstack import utils
from openstack import connection
from openstack import profile
from openstack import version as os_ver


class connect:
    """Connection related class

    Class to collate all operations related to connecting to OpenStack.
    """
    def create_connection(self):
        """Creates a connection

        Method creates a connection and returns it for use in other methods.

        Returns:
            connection: a connection object
        """
        ver_tmp = os_ver.__version__
        major_tmp, minor_tmp, rel_tmp = ver_tmp.split(".")

        major_version = int(major_tmp)
        minor_version = int(minor_tmp)
        rel_version = int(rel_tmp)

        prof = profile.Profile()
        prof.set_region(profile.Profile.ALL, os.environ['OS_REGION_NAME'])
        prof.set_interface('identity', 'admin')
        prof.set_version('identity', 'v3')
        prof.set_version('image', 'v2')
        """
        Between v2 and v3 OS_TENANT_NAME is changed to OS_PROJECT_NAME
        This switch ensures we dont care what version you are using
        """
        if os.environ['OS_TENANT_NAME'] is None:
            projectSelect = os.environ['OS_PROJECT_NAME']
        else:
            projectSelect = os.environ['OS_TENANT_NAME']

        if major_version >= 0 and minor_version >= 13 and rel_version >= 0:
            # Newer version of OpenStackSDK
            return connection.Connection(
                                region_name='regionOne',
                                auth=dict(
                                    auth_url=os.environ['OS_AUTH_URL'],
                                    username=os.environ['OS_USERNAME'],
                                    password=os.environ['OS_PASSWORD'],
                                    project_name=projectSelect),
                                identity_interface='public')
        else:
            # Older version of OpenStackSDK
            return connection.Connection(
                                 profile=prof,
                                 user_agent='examples',
                                 auth_url=os.environ['OS_AUTH_URL'],
                                 project_name=projectSelect,
                                 username=os.environ['OS_USERNAME'],
                                 password=os.environ['OS_PASSWORD'])


class orphanFinder:
    """Orphan resource related class

    Class to collate all operations related to finding orphan resources.
    """
    def findOrphans(self, resources, projIdList):
        """Find orphan resources

        Method takes a list of resources, and a list of project IDs then finds
        the resources that don't relate to a valid project.

        Args:
            resources (list): List of resources to filter.
            projIdList (list): List of valid project IDs.

        Returns:
            list: list of resources not owned by a valid project
        """
        orphans = []
        for resource in resources:
            if hasattr(resource, 'project_id'):
                if resource.project_id not in projIdList:
                    orphans.append(resource)
            elif hasattr(resource, 'owner'):
                if resource.owner not in projIdList:
                    orphans.append(resource)
        return orphans


import charms.reactive as reactive
import charmhelpers.core.hookenv as hookenv

# This charm's library contains all of the handler code associated with
# aodh
import charm.openstack.aodh as aodh


# Minimal inferfaces required for operation
MINIMAL_INTERFACES = [
    'shared-db.available',
    'identity-service.available',
    'amqp.available',
]


# use a synthetic state to ensure that it get it to be installed independent of
# the install hook.
@reactive.when_not('charm.installed')
def install_packages():
    aodh.install()
    reactive.set_state('charm.installed')


@reactive.when('amqp.connected')
def setup_amqp_req(amqp):
    """Use the amqp interface to request access to the amqp broker using our
    local configuration.
    """
    amqp.request_access(username='aodh',
                        vhost='openstack')
    aodh.assess_status()


@reactive.when('shared-db.connected')
def setup_database(database):
    """On receiving database credentials, configure the database on the
    interface.
    """
    database.configure('aodh', 'aodh', hookenv.unit_private_ip())
    aodh.assess_status()


@reactive.when('identity-service.connected')
def setup_endpoint(keystone):
    aodh.setup_endpoint(keystone)
    aodh.assess_status()


def render(*args):
    aodh.render_configs(args)
    reactive.set_state('config.complete')
    aodh.assess_status()


@reactive.when_not('cluster.available')
@reactive.when(*MINIMAL_INTERFACES)
def render_unclustered(*args):
    render(*args)


@reactive.when('cluster.available',
               *MINIMAL_INTERFACES)
def render_clustered(*args):
    render(*args)


@reactive.when('config.complete')
@reactive.when_not('db.synced')
def run_db_migration():
    aodh.db_sync()
    aodh.restart_all()
    reactive.set_state('db.synced')
    aodh.assess_status()


@reactive.when('ha.connected')
def cluster_connected(hacluster):
    aodh.configure_ha_resources(hacluster)


@reactive.hook('upgrade-charm')
def upgrade_charm():
    aodh.install()

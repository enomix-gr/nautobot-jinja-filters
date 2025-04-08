""" Jinja2 filters to be used with Computed Fields """ 
# from django.conf import settings

from django_jinja import library

from nautobot.dcim.models import Site, Device, DeviceRole, RearPort, FrontPort
from nautobot.extras.models import Relationship

ROLE_ACCESS_CABLE = DeviceRole.objects.get(slug="access-cable")

RELATIONSHIP_HAS_DBB = Relationship.objects.get(slug='has_dbb')
RELATIONSHIP_BEP_FRONTPORT = Relationship.objects.get(slug='bep_frontport')


def get_dbb(bep: Site) -> Site:
    dbb_assoc = bep.destination_for_associations.filter(relationship=RELATIONSHIP_HAS_DBB).first()
    if dbb_assoc is None:
        return None
    return dbb_assoc.source

def get_tray_ports(bep: Site) -> list[RearPort]:
    dbb = get_dbb(bep)
    access_cable = Device.objects.get(device_role=ROLE_ACCESS_CABLE, site__in=[bep, dbb])

    if dbb is None or 'p' in bep.cf['spliterbep']: # Not dbb through
        return [a.get_cable_peer() for a in access_cable.rearports.exclude(cable=None)]

    # DBB through
    f_port_assoc = bep.source_for_associations.filter(relationship=RELATIONSHIP_BEP_FRONTPORT)
    return [f.destination.rear_port.get_cable_peer() for f in f_port_assoc]

def get_fdc_splitter_ports(bep: Site) -> list[FrontPort]:
    tray4_r_ports = get_tray_ports(bep)
    fdc_ports = []
    for r in tray4_r_ports:
        front_ports = r.frontports.all()
        for f in front_ports:
            fdc_ports.append(f.get_cable_peer())

    return fdc_ports


def get_bep_or_dbb_from_tray4(port: RearPort) -> Site:
    """ Given a tray4 Rearport return the bep or dbb it corresponds """

    access_cable_r_port = port.get_cable_peer()
    
    # No DBB
    if access_cable_r_port.device.site.cf.get('site_type') == "BEP":
        return access_cable_r_port.device.site
    
    access_cable_f_port = access_cable_r_port.frontports.first()
    dbb_splitter_r_port = access_cable_f_port.get_cable_peer()

    # Normal DBB (not through) already connected
    if (dbb_splitter_r_port is not None
        and 'splitter' in dbb_splitter_r_port.device.device_type.slug
        ) :
        return dbb_splitter_r_port.device.site

    # DBB through already connected
    if (dbb_splitter_r_port is not None
        and 'splice' in dbb_splitter_r_port.device.device_type.slug
        ) :
        return dbb_splitter_r_port.frontports.first().get_cable_peer().device.site

    # DBB through not connected
    bep_assoc = access_cable_f_port.destination_for_associations.first()
    if (dbb_splitter_r_port is None
        and bep_assoc is not None
        ) :
        return bep_assoc.source
    
    # return DBB
    return access_cable_r_port.device.site


def get_bep_or_dbb_from_fdcsplitter(port: FrontPort) -> Site:
    """ Given an FDC splitter Frontport return the bep or dbb it corresponds """
    tray4_f_port = port.get_cable_peer()

    return get_bep_or_dbb_from_tray4(tray4_f_port.rear_port)


@library.filter
def trace_to_tray4(bep: Site) -> str:
    """ Tray 4 ports BEP is connected to """

    tray4_ports = get_tray_ports(bep)
    return ', '.join([r.name for r in tray4_ports])

@library.filter
def trace_to_fdc_splitter(bep: Site) -> str:
    """ FDC splitter ports BEP is connected to """

    fdc_splitter_ports = get_fdc_splitter_ports(bep)

    return fdc_splitter_ports[0].device.name + ': ' + ', '.join([r.name for r in fdc_splitter_ports])


@library.filter
def trace_to_bep_or_dbb(port) -> str:
    """ Bep or DBB to utilize this port """

    if port.cable is None:
        return ""

    if type(port) == RearPort and port.device.device_role.slug == "fdc_ds_pp":
        site = get_bep_or_dbb_from_tray4(port)
        return site.name

    if type(port) == FrontPort and port.device.device_role.slug == "fdc-splitter":
        site = get_bep_or_dbb_from_fdcsplitter(port)
        return site.name

    return ""
    # raise Exception("Field not applicable")

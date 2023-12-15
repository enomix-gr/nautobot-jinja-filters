""" Jinja2 filters to be used with Computed Fields """ 
# from django.conf import settings

from django_jinja import library

from nautobot.dcim.models import Device, RearPort, FrontPort
from nautobot.extras.models import Relationship


@library.filter
def trace_to_tray4(msg):
    """ Tray 4 ports BEP is connected to """

    return "Wow! s"
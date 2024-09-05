# -*- coding: utf-8 -*-

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load AllGeocodersAtOnce class from file AllGeocodersAtOnce."""
    from .all_geocoders_at_once import AllGeocodersAtOnce
    return AllGeocodersAtOnce(iface)
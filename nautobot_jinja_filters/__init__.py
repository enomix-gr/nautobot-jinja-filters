from nautobot.apps import NautobotAppConfig

class NautobotJinjaFiltersConfig(NautobotAppConfig):
    name = 'nautobot_jinja_filters'
    verbose_name = 'Custom Jinja filters for Nautobot'
    description = 'Arbitrary jinja filters for Nautobot'
    version = '0.1'
    author = 'Alexis Panagiotopoulos'
    author_email = 'apanagio@enomix.gr'
    base_url = 'jinja-filters'
    required_settings = []

config = NautobotJinjaFiltersConfig

from django.apps import AppConfig

MODULE_NAME = "notice"

DEFAULT_CFG = {
    "gql_query_notices_perms": ["112001"],  # Permission to query notices
    "gql_query_notice_admins_perms": [],    # Permissions for admins (if any)
    "gql_mutation_create_notices_perms": ["112002"],  # Permission to create notices
    "gql_mutation_update_notices_perms": ["112003"],  # Permission to update notices
    "gql_mutation_delete_notices_perms": ["112004"],  # Permission to delete notices
    "gql_mutation_toggle_notice_status_perms": ["112005"],  # Permission to toggle notice status
    "gql_mutation_send_notice_email_perms": ["112006"],     # Permission to send email
    "gql_mutation_send_notice_sms_perms": ["112007"],       # Permission to send SMS
    "notice_max_length_title": 100,         # Max length for notice title
    "notice_max_length_description": 1000,  # Max length for notice description
    "notice_priority_options": ["Low", "Medium", "High"],  # Allowed priority values
    "notice_default_priority": "Low",       # Default priority if not specified
    "notice_max_restore": None,             # Max number of times a notice can be restored (if applicable)
    "notice_email_enabled": True,           # Enable/disable email sending
    "notice_sms_enabled": True,             # Enable/disable SMS sending
    "notice_attachments_root_path": None,   # Root path for notice attachments (if any)
    "allowed_domains_attachments": [],      # Allowed domains for attachments
}


class NoticeConfig(AppConfig):
    name = MODULE_NAME

    gql_query_notices_perms = []
    gql_query_notice_admins_perms = []
    gql_mutation_create_notices_perms = []
    gql_mutation_update_notices_perms = []
    gql_mutation_delete_notices_perms = []
    gql_mutation_toggle_notice_status_perms = []
    gql_mutation_send_notice_email_perms = []
    gql_mutation_send_notice_sms_perms = []
    notice_max_length_title = None
    notice_max_length_description = None
    notice_priority_options = []
    notice_default_priority = None
    notice_max_restore = None
    notice_email_enabled = None
    notice_sms_enabled = None
    notice_attachments_root_path = None
    allowed_domains_attachments = None

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(NoticeConfig, field):
                setattr(NoticeConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)
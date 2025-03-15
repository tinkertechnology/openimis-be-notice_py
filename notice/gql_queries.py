import graphene
from core import prefix_filterset, ExtendedConnection
from graphene_django import DjangoObjectType
from django.utils.translation import gettext as _
import graphene
from graphene_django import DjangoObjectType
from location.schema import HealthFacilityGQLType

from .models import Notice, NoticeAttachment


class NoticePriority(graphene.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @property
    def description(self):
        if self == NoticePriority.LOW:
            return _("Low priority")
        elif self == NoticePriority.MEDIUM:
            return _("Medium priority")
        elif self == NoticePriority.HIGH:
            return _("High priority")
        return ""

class NoticeGQLType(DjangoObjectType):
    attachment_count = graphene.Int()
    class Meta:
        model = Notice
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "uuid": ["exact"],
            "id": ["exact"],
            "title": ["icontains"],
            "description": ["icontains"],
            "priority": ["exact"],
            "created_at": ["exact", "lt", "lte", "gt", "gte"],
            **prefix_filterset("health_facility__", HealthFacilityGQLType._meta.filter_fields),

        }
        connection_class = ExtendedConnection 
    
    def resolve_attachment_count(self, info):
    # Count the number of attachments related to this notice
        return self.attachments.count()


class NoticeAttachmentGQLType(DjangoObjectType):
    doc = graphene.String(source='document')
    class Meta:
        model = NoticeAttachment
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        filter_fields = {
            "id": ["exact"],
            "general_type": ["exact", "icontains"],
            "type": ["exact", "icontains"],
            "title": ["exact", "icontains"],
            "date": ["exact", "lt", "lte", "gt", "gte"],
            "filename": ["exact", "icontains"],
            "mime": ["exact", "icontains"],
            "url": ["exact", "icontains"],
            **prefix_filterset("notice__", NoticeGQLType._meta.filter_fields),
        }
        connection_class = ExtendedConnection
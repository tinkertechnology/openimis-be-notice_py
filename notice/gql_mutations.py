import logging
import graphene
from .models import Notice, NoticeAttachment
from core.schema import  OpenIMISMutation
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext as _
from location.models import HealthFacility
from django.core.mail import send_mail
import requests
import os

logger = logging.getLogger(__name__)

# Mutations
class CreateNoticeMutation(OpenIMISMutation):
    _mutation_module = "notice"
    _mutation_class = "CreateNoticeMutation"

    class Input(OpenIMISMutation.Input):
        title = graphene.String(required=True)
        description = graphene.String(required=True)
        priority = graphene.String(required=True)
        health_facility_id = graphene.Int(required=True)  
        schedule_publish = graphene.Boolean(required=False)  # New field
        publish_start_date = graphene.DateTime(required=False)  # New field

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if isinstance(user, AnonymousUser) or not user.id:
                raise ValidationError("Authentication required")
            if not user.has_perms(["notice.add_notice"]):
                raise PermissionDenied("Unauthorized")

            health_facility = HealthFacility.objects.get(id=data["health_facility_id"])
            notice = Notice(
                title=data["title"],
                description=data["description"],
                priority=data["priority"],
                health_facility=health_facility,
                schedule_publish=data.get("schedule_publish", False),  # Default to False if not provided
                publish_start_date=data.get("publish_start_date"),  # Can be None if not provided
            )
            notice.save()
            return None  # Success, no errors
        except Exception as exc:
            return [{
                "message": "Failed to create notice",
                "detail": str(exc)
            }]

class UpdateNoticeMutation(OpenIMISMutation):
    _mutation_module = "notice"
    _mutation_class = "UpdateNoticeMutation"

    class Input(OpenIMISMutation.Input):
        uuid = graphene.UUID(required=True)
        title = graphene.String()
        description = graphene.String()
        priority = graphene.String()
        health_facility_id = graphene.Int()

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if isinstance(user, AnonymousUser) or not user.id:
                raise ValidationError("Authentication required")
            if not user.has_perms(["notice.change_notice"]):
                raise PermissionDenied("Unauthorized")

            notice = Notice.objects.get(uuid=data["uuid"], is_active=True)
            if "title" in data:
                notice.title = data["title"]
            if "description" in data:
                notice.description = data["description"]
            if "priority" in data:
                notice.priority = data["priority"]
            if "health_facility_id" in data:
                notice.health_facility = HealthFacility.objects.get(id=data["health_facility_id"])
            notice.save()
            return None  # Success, no errors
        except Notice.DoesNotExist:
            return [{"message": "Notice not found", "detail": str(data["uuid"])}]
        except Exception as exc:
            return [{"message": "Failed to update notice", "detail": str(exc)}]

class DeleteNoticeMutation(OpenIMISMutation):
    _mutation_module = "notice"
    _mutation_class = "DeleteNoticeMutation"

    class Input(OpenIMISMutation.Input):
        uuids = graphene.List(graphene.UUID, required=True)  # Support bulk deletion

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if isinstance(user, AnonymousUser) or not user.id:
                raise ValidationError("Authentication required")
            if not user.has_perms(["notice.delete_notice"]):
                raise PermissionDenied("Unauthorized")

            errors = []
            for uuid in data["uuids"]:
                try:
                    notice = Notice.objects.get(uuid=uuid, is_active=True)
                    notice.is_active = False  # Soft delete
                    notice.save()
                except Notice.DoesNotExist:
                    errors.append({"message": "Notice not found", "detail": str(uuid)})
            
            if errors:
                return errors
            return None  # Success, no errors
        except Exception as exc:
            return [{"message": "Failed to delete notices", "detail": str(exc)}]


class ToggleNoticeStatusMutation(OpenIMISMutation):
    _mutation_module = "notice"
    _mutation_class = "ToggleNoticeStatusMutation"

    class Input(OpenIMISMutation.Input):
        uuid = graphene.UUID(required=True)
        is_active = graphene.Boolean(required=True)

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if isinstance(user, AnonymousUser) or not user.id:
                raise ValidationError("Authentication required")
            if not user.has_perms(["notice.change_notice"]):  
                raise PermissionDenied("Unauthorized")

            notice = Notice.objects.get(uuid=data["uuid"])
            notice.is_active = data["is_active"]
            notice.save()
            return None
        except Notice.DoesNotExist:
            return [{"message": "Notice not found", "detail": str(data["uuid"])}]
        except Exception as exc:
            return [{"message": "Failed to toggle notice status", "detail": str(exc)}]

class SendNoticeEmailMutation(OpenIMISMutation):
    _mutation_module = "notice"
    _mutation_class = "SendNoticeEmailMutation"

    class Input(OpenIMISMutation.Input):
        uuid = graphene.UUID(required=True)

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if isinstance(user, AnonymousUser) or not user.id:
                raise ValidationError("Authentication required")
            if not user.has_perms(["notice.send_email"]):  #
                raise PermissionDenied("Unauthorized")
            notice = Notice.objects.get(uuid=data["uuid"])
            recipient = notice.health_facility.email
            send_mail(
                subject=f"Notice: {notice.title}",
                message=notice.description,
                from_email="no-reply@openimis.org",
                recipient_list=[recipient],
                fail_silently=False,
            )
            return None
        except Notice.DoesNotExist:
            return [{"message": "Notice not found", "detail": str(data["uuid"])}]
        except Exception as exc:
            return [{"message": "Failed to send email", "detail": str(exc)}]

class SendNoticeSMSMutation(OpenIMISMutation):
    _mutation_module = "notice"
    _mutation_class = "SendNoticeSMSMutation"

    class Input(OpenIMISMutation.Input):
        uuid = graphene.UUID(required=True)

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if isinstance(user, AnonymousUser) or not user.id:
                raise ValidationError("Authentication required")
            if not user.has_perms(["notice.send_sms"]):
                raise PermissionDenied("Unauthorized")

            notice = Notice.objects.get(uuid=data["uuid"])
            # Custom SMS Gateway configuration
            sms_gateway_url = os.getenv("SMS_GATEWAY_URL", "https://api.smsgateway.example.com/send")
            sms_gateway_api_key = os.getenv("SMS_GATEWAY_API_KEY", "your-api-key")
            recipient_phone = "+1234567890"  # Replace with actual logic, e.g., notice.health_facility.contact_phone

            # Example payload for a custom SMS gateway (adjust based on your provider's API)
            payload = {
                "api_key": sms_gateway_api_key,
                "to": recipient_phone,
                "message": notice.description,
                "from": os.getenv("SMS_GATEWAY_SENDER_ID", "OpenIMIS")  # Optional sender ID
            }

            # Send SMS via HTTP POST request
            response = requests.post(sms_gateway_url, json=payload, timeout=10)
            if response.status_code != 200:
                raise Exception(f"SMS gateway returned status {response.status_code}: {response.text}")

            # Optionally, parse the response to confirm success
            response_data = response.json()
            if not response_data.get("success", False):  # Adjust based on your gateway's response format
                raise Exception(f"SMS gateway error: {response_data.get('error', 'Unknown error')}")

            return None
        except Notice.DoesNotExist:
            return [{"message": "Notice not found", "detail": str(data["uuid"])}]
        except Exception as exc:
            return [{"message": "Failed to send SMS", "detail": str(exc)}]




class CreateNoticeAttachmentMutation(OpenIMISMutation):
    _mutation_module = "notice"
    _mutation_class = "CreateNoticeAttachmentMutation"

    class Input(OpenIMISMutation.Input):
        notice_uuid = graphene.String(required=True)
        general_type = graphene.String(required=False)
        type = graphene.String()
        title = graphene.String()
        date = graphene.Date()
        filename = graphene.String()
        mime = graphene.String()
        url = graphene.String()
        document = graphene.String()

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if isinstance(user, AnonymousUser) or not user.id:
                raise ValidationError("Authentication required")
            if not user.has_perms(["notice.add_notice_attachment"]):
                raise PermissionDenied("Unauthorized")
            notice = Notice.objects.get(uuid=data["notice_uuid"])
            from datetime import datetime
            attachment = NoticeAttachment(
                notice=notice,
                general_type=data.get("general_type") if data.get("general_type") else "test" ,
                type=data.get("type"),
                title=data.get("title"),
                date=data.get("date") if data.get('date') else datetime.now().today(),
                filename=data.get("filename"),
                mime=data.get("mime"),
                url=data.get("url"),
                document=data.get("document"),
            )
            attachment.save()
            return None  # Success, no errors
        except Exception as exc:
            
            return [{
                "message": "Failed to create notice attachment",
                "detail": str(exc)
            }]

class UpdateNoticeAttachmentMutation(OpenIMISMutation):
    _mutation_module = "notice"
    _mutation_class = "UpdateNoticeAttachmentMutation"

    class Input(OpenIMISMutation.Input):
        uuid = graphene.String(required=True)
        general_type = graphene.String(required=True)
        type = graphene.String()
        title = graphene.String()
        date = graphene.Date()
        filename = graphene.String()
        mime = graphene.String()
        url = graphene.String()
        document = graphene.String()

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if isinstance(user, AnonymousUser) or not user.id:
                raise ValidationError("Authentication required")
            if not user.has_perms(["notice.change_notice_attachment"]):
                raise PermissionDenied("Unauthorized")

            attachment = NoticeAttachment.objects.get(uuid=data["uuid"])
            attachment.general_type = data["general_type"]
            attachment.type = data.get("type")
            attachment.title = data.get("title")
            attachment.date = data.get("date")
            attachment.filename = data.get("filename")
            attachment.mime = data.get("mime")
            attachment.url = data.get("url")
            attachment.document = data.get("document")
            attachment.save()
            return None  # Success, no errors
        except Exception as exc:
            return [{
                "message": "Failed to update notice attachment",
                "detail": str(exc)
            }]

class DeleteNoticeAttachmentMutation(OpenIMISMutation):
    _mutation_module = "notice"
    _mutation_class = "DeleteNoticeAttachmentMutation"

    class Input(OpenIMISMutation.Input):
        id = graphene.String(required=True)

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if isinstance(user, AnonymousUser) or not user.id:
                raise ValidationError("Authentication required")
            if not user.has_perms(["notice.delete_notice_attachment"]):
                raise PermissionDenied("Unauthorized")
            if "client_mutation_id" in data:
                data.pop('client_mutation_id')
            if "client_mutation_label" in data:
                data.pop('client_mutation_label')   
            import pdb;pdb.set_trace()         
            attachment = NoticeAttachment.objects.get(id=data["id"])
            attachment.delete()
            return None  # Success, no errors
        except Exception as exc:
            return [{
                "message": "Failed to delete notice attachment",
                "detail": str(exc)
            }]


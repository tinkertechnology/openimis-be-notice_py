# openIMIS Backend Notice Reference Module

## Overview
This repository contains the backend implementation of the openIMIS Notice reference module. It provides database models, GraphQL APIs, services, and configurations for managing notices and their attachments.

## Code Climate (develop branch)
TBD: Add Code Climate badge or status once integrated (e.g., maintainability, test coverage).

## ORM Mapping

### Notice
- **uuid**: `UUIDField` (primary_key=True, default=uuid.uuid4, editable=False) - Unique identifier for the notice.
- **title**: `TextField` (blank=False, null=False) - Title of the notice.
- **created_at**: `DateField` (default=TimeUtils.now, blank=True) - Creation date of the notice.
- **priority**: `CharField` (max_length=10, choices=NOTICE_PRIORITY_LEVELS, default="LOW") - Priority level (e.g., Low, Medium, High).
- **health_facility**: `ForeignKey` (to=location.HealthFacility, on_delete=models.CASCADE) - Associated health facility.
- **description**: `TextField` (blank=False, null=False) - Detailed description of the notice.
- **is_active**: `BooleanField` (default=True) - Indicates if the notice is active.
- Inherited from `core.UUIDModel` and `core.UUIDVersionedModel` (assumed to provide uuid and versioning fields).

### NoticeAttachment
- **uuid**: `UUIDField` (primary_key=True, default=uuid.uuid4, editable=False) - Unique identifier for the attachment.
- **notice**: `ForeignKey` (to=Notice, on_delete=models.CASCADE, related_name="attachments") - Reference to the parent notice.
- **general_type**: `CharField` (max_length=4, choices=[("FILE", "File"), ("URL", "URL")], default="FILE") - Type of attachment (File or URL).
- **type**: `TextField` (blank=True, null=True) - Custom type description.
- **title**: `TextField` (blank=True, null=True) - Title or name of the attachment.
- **date**: `DateField` (blank=True, default=TimeUtils.now) - Date of the attachment.
- **filename**: `TextField` (blank=True, null=True) - Original filename of the uploaded file.
- **mime**: `TextField` (blank=True, null=True) - MIME type (e.g., "application/pdf").
- **module**: `TextField` (blank=False, null=True, default="notice") - Module identifier.
- **url**: `TextField` (blank=True, null=True) - URL link if `general_type` is "URL".
- **document**: `TextField` (blank=True, null=True) - Base64-encoded file content if `general_type` is "FILE".
- Inherited from `core.UUIDModel` and `core.UUIDVersionedModel`.

## Listened Django Signals

### `django.db.models.signals.post_save`
- Listened on `Notice` to trigger updates (e.g., caching or notifications).
- Listened on `NoticeAttachment` to log attachment creation.

### `django.db.models.signals.post_delete`
- Listened on `NoticeAttachment` to clean up related data (e.g., remove Base64 content from storage).

## Services

### NoticeService
- `create_notice(data)`: Creates a new notice with the provided data.
- `update_notice(notice_uuid, data)`: Updates an existing notice.
- `delete_notice(notice_uuid)`: Deletes a notice and its attachments.
- `fetch_notices(filters)`: Retrieves a filtered list of notices.

### NoticeAttachmentService
- `create_attachment(notice_uuid, data)`: Adds an attachment to a notice.
- `update_attachment(attachment_uuid, data)`: Updates an attachment.
- `delete_attachment(attachment_uuid)`: Removes an attachment from a notice.
- `download_attachment(attachment_uuid)`: Retrieves attachment content (e.g., Base64 or URL redirect).

## GraphQL Queries

### `notices`
- **Description**: Retrieves a paginated list of notices.
- **Arguments**: `uuid`, `title`, `priority`, `health_facility_uuid`, `is_active`, `first`, `after`, `last`, `before`.
- **Returns**: `[NoticeType]` (includes fields: `uuid`, `title`, `createdAt`, `priority`, `healthFacility`, `description`, `isActive`, `attachments`).

### `notice`
- **Description**: Retrieves a single notice by UUID.
- **Arguments**: `uuid` (required).
- **Returns**: `NoticeType`.

### `noticeAttachments`
- **Description**: Retrieves attachments for a specific notice.
- **Arguments**: `notice_uuid` (required), `general_type`.
- **Returns**: `[NoticeAttachmentType]` (includes fields: `uuid`, `generalType`, `type`, `title`, `date`, `filename`, `mime`, `url`, `document`).

## GraphQL Mutations
- `createNotice`: Creates a new notice.
- `updateNotice`: Updates an existing notice.
- `deleteNotice`: Deletes a notice.
- `createNoticeAttachment`: Adds an attachment to a notice.
- `updateNoticeAttachment`: Updates an attachment.
- `deleteNoticeAttachment`: Deletes an attachment.

### NoticeSummaryReport
- **Template**: `notice_summary.html`
- **Description**: Summarizes active notices by health facility and priority.
- **Parameters**: `date_range`, `health_facility_uuid`


## Configuration Options

Configurable via `core.ModuleConfiguration`:
- `notice.max_attachments_per_notice`: Maximum number of attachments per notice (Default: `10`).
- `notice.allowed_mime_types`: List of allowed MIME types for attachments (Default: `['application/pdf', 'image/jpeg', 'image/jpg']`).
- `notice.priority_levels`: Customizable priority levels (Default: `[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')]`).
- `notice.default_is_active`: Default value for `is_active` on notice creation (Default: `true`).

## openIMIS Modules Dependencies
- `openimis-be-core_py`: For base models (`UUIDModel`, `UUIDVersionedModel`), signals, and GraphQL utilities.
- `openimis-be-location_py`: For `HealthFacility` model and picker integration.


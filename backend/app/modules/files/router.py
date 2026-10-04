from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.core.pagination import Page
from app.modules.auth.dependencies import Configuration, CurrentUser, Database
from app.modules.files import service
from app.modules.files.schemas import AttachmentFilters, AttachmentRead, OwnerReference
from app.modules.files.storage import LocalStorage

router = APIRouter(prefix="/files", tags=["files"])


def storage(settings: Configuration) -> LocalStorage:
    return LocalStorage(settings.storage_directory)


@router.get("", response_model=Page[AttachmentRead])
def list_files(
    session: Database,
    user: CurrentUser,
    filters: Annotated[AttachmentFilters, Query()],
) -> object:
    return service.list_files(session, user, filters)


@router.post("", response_model=AttachmentRead, status_code=201)
def upload_file(
    session: Database,
    user: CurrentUser,
    settings: Configuration,
    upload: Annotated[UploadFile, File()],
    project_id: Annotated[UUID | None, Form()] = None,
    task_id: Annotated[UUID | None, Form()] = None,
    setup_id: Annotated[UUID | None, Form()] = None,
    component_id: Annotated[UUID | None, Form()] = None,
    test_id: Annotated[UUID | None, Form()] = None,
    firmware_revision_id: Annotated[UUID | None, Form()] = None,
    branch_id: Annotated[UUID | None, Form()] = None,
    product_id: Annotated[UUID | None, Form()] = None,
    product_revision_id: Annotated[UUID | None, Form()] = None,
    firmware_release_id: Annotated[UUID | None, Form()] = None,
    stage_execution_id: Annotated[UUID | None, Form()] = None,
) -> object:
    owner = OwnerReference(
        project_id=project_id,
        task_id=task_id,
        setup_id=setup_id,
        component_id=component_id,
        test_id=test_id,
        firmware_revision_id=firmware_revision_id,
        branch_id=branch_id,
        product_id=product_id,
        product_revision_id=product_revision_id,
        firmware_release_id=firmware_release_id,
        stage_execution_id=stage_execution_id,
    )
    try:
        return service.create_file(
            session,
            user,
            owner,
            upload.filename,
            upload.content_type,
            upload.file,
            storage(settings),
            settings.max_upload_bytes,
        )
    finally:
        upload.file.close()


@router.get("/{attachment_id}/download")
def download_file(
    attachment_id: UUID, session: Database, user: CurrentUser, settings: Configuration
) -> StreamingResponse:
    attachment = service.get_file(session, attachment_id, user)
    stream = storage(settings).open(attachment.storage_path)
    encoded = quote(attachment.original_filename, safe="")
    return StreamingResponse(
        service.stream_file(stream),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=download; filename*=UTF-8''{encoded}",
            "Content-Length": str(attachment.size),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete("/{attachment_id}", status_code=204)
def delete_file(
    attachment_id: UUID, session: Database, user: CurrentUser, settings: Configuration
) -> None:
    service.delete_file(session, attachment_id, user, storage(settings))

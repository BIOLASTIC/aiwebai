from backend.app.db.models import UploadedFile


def test_uploaded_file_model_fields():
    file = UploadedFile(
        file_id="file_test",
        filename="ref.png",
        mime_type="image/png",
        size_bytes=123,
        storage_path="/tmp/ref.png",
        purpose="reference",
        owner_user_id=1,
    )
    assert file.file_id == "file_test"
    assert file.filename
    assert file.mime_type
    assert file.size_bytes is not None
    assert file.storage_path
    assert file.purpose
    assert file.owner_user_id is not None

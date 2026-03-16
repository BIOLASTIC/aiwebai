from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.models import Base, UploadedFile
from datetime import datetime


def test_uploaded_file_model():
    # Create an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Create an UploadedFile instance
    uploaded_file = UploadedFile(
        file_id="file_test123", filename="test.png", mime_type="image/png", size=1024, purpose="fine-tune", user_id=1
    )

    # Add to session and commit
    session.add(uploaded_file)
    session.commit()

    # Retrieve from database
    retrieved_file = session.query(UploadedFile).filter(UploadedFile.file_id == "file_test123").first()

    # Verify attributes
    assert retrieved_file is not None
    assert retrieved_file.file_id == "file_test123"
    assert retrieved_file.filename == "test.png"
    assert retrieved_file.mime_type == "image/png"
    assert retrieved_file.size == 1024
    assert retrieved_file.purpose == "fine-tune"
    assert retrieved_file.user_id == 1

    session.close()


if __name__ == "__main__":
    test_uploaded_file_model()
    print("UploadedFile model test passed!")

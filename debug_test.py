import hashlib
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Issue(Base):
    __tablename__ = "issues"
    id = Column(Integer, primary_key=True)
    description = Column(Text)
    category = Column(String)
    integrity_hash = Column(String)
    previous_integrity_hash = Column(String)

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

# Mocking the test logic
hash1_content = "First issue|Road|"
hash1 = hashlib.sha256(hash1_content.encode()).hexdigest()
issue1 = Issue(description="First issue", category="Road", integrity_hash=hash1)
db.add(issue1)
db.commit()
db.refresh(issue1)

issue_id = issue1.id
current_issue = db.query(Issue.id, Issue.description, Issue.category, Issue.integrity_hash, Issue.previous_integrity_hash).filter(Issue.id == issue_id).first()

prev_issue_hash = db.query(Issue.integrity_hash).filter(Issue.id < issue_id).order_by(Issue.id.desc()).first()
actual_prev_hash = prev_issue_hash[0] if prev_issue_hash and prev_issue_hash[0] else ""

print(f"current_issue: {current_issue}")
print(f"prev_issue_hash: {prev_issue_hash}")
print(f"actual_prev_hash: '{actual_prev_hash}'")

hash_content = f"{current_issue.description}|{current_issue.category}|{actual_prev_hash}"
computed_hash = hashlib.sha256(hash_content.encode()).hexdigest()
print(f"hash_content: '{hash_content}'")
print(f"computed_hash: {computed_hash}")
print(f"current_issue.integrity_hash: {current_issue.integrity_hash}")
print(f"Match: {computed_hash == current_issue.integrity_hash}")

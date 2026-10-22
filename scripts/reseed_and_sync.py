import sys
from pathlib import Path
import shutil

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.database.seed import seed_database
from app.documents.ingestion import ingest_sample_documents
from app.database.repository import repo

print("Seeding database...")
seed_database(force=True)

sample_dir = Path(__file__).resolve().parent.parent / "data" / "sample_documents"
print(f"Ingesting samples from {sample_dir}...")
ingest_sample_documents(sample_dir)

src = (Path(__file__).resolve().parent.parent / "data" / "buddy.db").resolve()
dst = (backend_dir / "data" / "buddy.db").resolve()
print(f"Syncing {src} -> {dst}...")
shutil.copy2(src, dst)

with repo.get_connection() as conn:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM document_chunks WHERE content LIKE '%Nalawade%'")
    nal_chunks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM faculty WHERE name LIKE '%Nalawade%'")
    nal_fac = c.fetchone()[0]
    print(f"Nalawade matches in chunks: {nal_chunks}, in faculty: {nal_fac}")
    
    print("\n--- Current Academic Departments & HODs ---")
    c.execute("SELECT name, hod, contact_email FROM departments")
    for row in c.fetchall():
        print(f"  {row[0]} -> HOD: {row[1]} ({row[2]})")

    print("\n--- Key Faculty ---")
    c.execute("SELECT name, department, designation, cabin FROM faculty")
    for row in c.fetchall():
        print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}")

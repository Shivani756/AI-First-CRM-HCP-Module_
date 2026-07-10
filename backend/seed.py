"""
Seed the database with sample HCPs and materials for demo purposes.
Run from the backend/ directory: python seed.py
"""
import asyncio
from app.database import AsyncSessionLocal, async_engine, Base  # noqa
from app import models  # noqa – registers all models
from app.models.hcp import HCP
from app.models.material import Material
from sqlalchemy import select

SAMPLE_HCPS = [
    {"name": "Dr. Rajan Sharma",  "specialty": "Oncology",        "email": "rajan.sharma@apollo.com",   "phone": "+91-9876543210", "organization": "Apollo Hospital"},
    {"name": "Dr. Priya Mehta",   "specialty": "Cardiology",      "email": "priya.mehta@fortis.com",    "phone": "+91-9876543211", "organization": "Fortis Medical Center"},
    {"name": "Dr. Arjun Nair",    "specialty": "Endocrinology",   "email": "arjun.nair@clinic.com",     "phone": "+91-9876543212", "organization": "City Endocrinology Clinic"},
    {"name": "Dr. Sunita Patel",  "specialty": "Neurology",       "email": "sunita.patel@neuro.com",    "phone": "+91-9876543213", "organization": "Neurocare Institute"},
    {"name": "Dr. Vikram Singh",  "specialty": "General Medicine","email": "vikram.singh@genmed.com",   "phone": "+91-9876543214", "organization": "Singh General Hospital"},
    {"name": "Dr. Anjali Gupta",  "specialty": "Rheumatology",    "email": "anjali.gupta@rheum.com",    "phone": "+91-9876543215", "organization": "Rheumatology Associates"},
    {"name": "Dr. Kavitha Reddy", "specialty": "Pulmonology",     "email": "kavitha.reddy@lung.com",    "phone": "+91-9876543216", "organization": "Lung Health Center"},
    {"name": "Dr. Suresh Iyer",   "specialty": "Gastroenterology","email": "suresh.iyer@gastro.com",    "phone": "+91-9876543217", "organization": "GI Specialists Clinic"},
    {"name": "Dr. Meena Krishnan","specialty": "Dermatology",     "email": "meena.k@skin.com",          "phone": "+91-9876543218", "organization": "SkinCare Clinic"},
    {"name": "Dr. Anil Verma",    "specialty": "Nephrology",      "email": "anil.verma@kidney.com",     "phone": "+91-9876543219", "organization": "Kidney Care Center"},
]

SAMPLE_MATERIALS = [
    {"name": "OncoBoost Phase III Clinical Trial Results",  "type": "PDF",      "url": "/materials/oncoboost-phase3.pdf"},
    {"name": "CardioGuard Product Brochure",                "type": "Brochure", "url": "/materials/cardioguard-brochure.pdf"},
    {"name": "Diabetes Management Guide 2025",             "type": "PDF",      "url": "/materials/diabetes-guide-2025.pdf"},
    {"name": "NeuroShield Safety Data Sheet",               "type": "PDF",      "url": "/materials/neuroshield-sds.pdf"},
    {"name": "Product Efficacy Comparison Chart",           "type": "Chart",    "url": "/materials/efficacy-comparison.pdf"},
    {"name": "Patient Testimonials Booklet",                "type": "Brochure", "url": "/materials/patient-testimonials.pdf"},
    {"name": "RheumaClear Prescribing Information",         "type": "PDF",      "url": "/materials/rheumaclear-pi.pdf"},
    {"name": "Lung Health Clinical Study Summary",          "type": "PDF",      "url": "/materials/lung-study-summary.pdf"},
]


async def seed():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(HCP).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        for data in SAMPLE_HCPS:
            db.add(HCP(**data))
        for data in SAMPLE_MATERIALS:
            db.add(Material(**data))

        await db.commit()
        print(f"✓ Seeded {len(SAMPLE_HCPS)} HCPs and {len(SAMPLE_MATERIALS)} materials.")


if __name__ == "__main__":
    asyncio.run(seed())

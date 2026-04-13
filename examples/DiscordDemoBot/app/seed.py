"""Seed initial persons and projects on first boot."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person
from app.models.project import Project

PERSONS = [
    ("Pavel Enderle",    "pavel.enderle@wingsdata.ai"),
    ("Roman Dvořák",     "roman.dvorak@wingsdata.ai"),
    ("Jan Kotrč",        "jan.kotrc@wingsdata.ai"),
    ("Tomas Dolezal",    "tomas.dolezal@wingsdata.ai"),
    ("Timothy Hobbs",    "timothy.hobbs@wingsdata.ai"),
    ("Lukáš Večerka",    "lukas.vecerka@wingsdata.ai"),
    ("Michal Dvořák",    "michal.dvorak@wingsdata.ai"),
    ("Matěj Outrata",    "matej.outrata@wingsdata.ai"),
    ("Anita Doležalová", "anita.dolezalova@wingsdata.ai"),
    ("Tomáš Ebert",      "tomas.ebert@wingsdata.ai"),
    ("Jakub Pogádl",     "jakub.pogadl@wingsdata.ai"),
    ("Tomáš Peroutka",   "tomas.peroutka@wingsdata.ai"),
    ("Jáchym Doležal",   "jachym.dolezal@wingsdata.ai"),
    ("Patrik Kišeda",    "patrik.kiseda@wingsdata.ai"),
    ("Matěj Novak",      "matej.novak@wingsdata.ai"),
]

# (project name, guarantor name)
PROJECTS = [
    ("Product",          "Lukáš Večerka"),
    ("CETIN",            "Jáchym Doležal"),
    ("Avant",            "Jan Kotrč"),
    ("Medin",            "Timothy Hobbs"),
    ("Faxchimp / Other", "Patrik Kišeda"),
    ("Organization",     "Patrik Kišeda"),
    ("VAFO",             "Patrik Kišeda"),
]


async def preseed(db: AsyncSession) -> None:
    """Insert default persons and projects if the tables are empty."""
    existing = (await db.execute(select(Person))).scalars().first()
    if existing:
        return

    person_map: dict[str, Person] = {}
    for name, email in PERSONS:
        p = Person(name=name, email=email)
        db.add(p)
        person_map[name] = p

    await db.flush()  # populate IDs before creating projects

    for proj_name, guarantor_name in PROJECTS:
        guarantor = (
            await db.execute(select(Person).where(Person.name == guarantor_name))
        ).scalars().first()
        if guarantor:
            db.add(Project(name=proj_name, guarantor_id=guarantor.id))

    await db.commit()

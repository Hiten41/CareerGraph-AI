import io
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from app.services.resume import parse_pdf


def test_valid_pdf_extracts_evidenced_skills():
    writer = PdfWriter()
    page = writer.add_blank_page(width=400, height=400)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 20 300 Td (Skills: Python and SQL) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    data = io.BytesIO()
    writer.write(data)
    profile = parse_pdf(data.getvalue())
    assert profile.skills == ["Python", "SQL"] and profile.graduation_year is None


def test_sections_aliases_and_actual_evidence():
    from app.services.resume import extract

    raw = "Name: Test Candidate\nEducation: BSc Computing\nExpected graduation: 2028\nProjects: Offline map service\nSkills: Postgres, PostgreSQL, K8s and C++\nExperience: Built tile cache in 2023"
    draft = extract(raw)
    assert draft.name == "Test Candidate" and draft.graduation_year == 2028
    assert draft.projects == ["Offline map service"] and draft.experience == ["Built tile cache in 2023"]
    assert draft.skills.count("PostgreSQL") == 1 and "Kubernetes" in draft.skills and "C++" in draft.skills
    assert draft.evidence["Kubernetes"] == "Skills: Postgres, PostgreSQL, K8s and C++"
    assert extract("Worked in 2028 with Javascript").graduation_year is None
    assert "Java" not in extract("JavaScript development").skills


def test_encrypted_and_blank_pdf_are_rejected():
    import pytest

    for encrypted in (True, False):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        if encrypted:
            writer.encrypt("local-test")
        buffer = io.BytesIO()
        writer.write(buffer)
        with pytest.raises(ValueError):
            parse_pdf(buffer.getvalue())

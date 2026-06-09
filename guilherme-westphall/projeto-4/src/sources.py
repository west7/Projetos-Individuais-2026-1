from dataclasses import dataclass, field


@dataclass(frozen=True)
class SeedDocument:
    title: str
    url: str
    year: int | None = None
    quarter: int | None = None


@dataclass(frozen=True)
class Source:
    company: str
    name: str
    url: str
    seed_documents: tuple[SeedDocument, ...] = field(default_factory=tuple)


SOURCES = {
    "mrv": Source(
        company="MRV",
        name="MRV Central de Resultados",
        url="https://ri.mrv.com.br/informacoes-financeiras/central-de-resultados/",
        seed_documents=(
            SeedDocument(
                title="Previa Operacional MRV 1T26",
                url="https://api.mziq.com/mzfilemanager/v2/d/4b56353d-d5d9-435f-bf63-dcbf0a6c25d5/9d9c8de1-c30a-0260-a69f-5c1c06219644?origin=2",
                year=2026,
                quarter=1,
            ),
        ),
    ),
    "pacaembu": Source(
        company="Pacaembu",
        name="Pacaembu RI",
        url="https://ri.pacaembu.com/",
    ),
}


def selected_sources(company: str) -> list[Source]:
    if company == "all":
        return list(SOURCES.values())
    if company not in SOURCES:
        valid = ", ".join(["all", *SOURCES.keys()])
        raise ValueError(f"Empresa invalida: {company}. Use uma de: {valid}")
    return [SOURCES[company]]

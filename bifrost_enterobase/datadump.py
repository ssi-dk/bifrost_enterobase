from bifrostlib import common
from bifrostlib.datahandling import Sample
from bifrostlib.datahandling import SampleComponentReference
from bifrostlib.datahandling import SampleComponent
from bifrostlib.datahandling import Category
from typing import Dict
import os


def ensure_tool_category(samplecomponent, category_name: str) -> Category:
    category = samplecomponent.get_category(category_name)
    if category is None:
        category = Category(value={
            "name": category_name,
            "component": {"id": samplecomponent["component"]["_id"], "name": samplecomponent["component"]["name"]},
            "summary": {
                "serotype": "",
                "antigenic_profile": "",
                "status": "",
            },
            "report": {},
        })

    if "summary" not in category:
        category["summary"] = {}
    if "report" not in category:
        category["report"] = {}

    category["summary"].setdefault("serotype", "")
    category["summary"].setdefault("antigenic_profile", "")
    category["summary"].setdefault("status", "")

    return category


def ensure_final_serotype_category(sample) -> Category:
    serotype = sample.get_category("serotype")
    if serotype is None:
        serotype = Category(value={
            "name": "serotype",
            "component": {
                "name": "serotype"
            },
            "summary": {
                "serotype": "",
                "antigenic_profile": "",
                "status": "",
            },
            "report": {},
        })

    if "summary" not in serotype:
        serotype["summary"] = {}
    if "report" not in serotype:
        serotype["report"] = {}

    serotype["summary"].setdefault("serotype", "")
    serotype["summary"].setdefault("antigenic_profile", "")
    serotype["summary"].setdefault("status", "")

    return serotype


def find_category_by_name(obj, category_name: str):
    return obj.get_category(category_name)


def update_consensus_field(summary: dict, field: str, value: str) -> bool:
    if value is None:
        return False

    value = value.strip()
    if value == "":
        return False

    current = summary.get(field, "")
    if current is None:
        current = ""
    current = current.strip()

    if current == "":
        summary[field] = value
        return False

    if current == value:
        return False

    return True


def update_consensus_summary(serotype: Category, tool_serotype: str) -> None:
    summary = serotype["summary"]
    previous_status = summary.get("status", "")

    serotype_conflict = update_consensus_field(summary, "serotype", tool_serotype)


    if serotype_conflict:
        summary["status"] = "Ambiguous"
    elif previous_status != "Ambiguous":
        has_serotype = summary.get("serotype", "").strip() != ""

        if has_serotype:
            summary["status"] = "Concordant"


def merge_tool_into_final(final_serotype: Category, tool_category) -> None:
    if tool_category is None:
        return

    tool_summary = tool_category["summary"]
    tool_report = tool_category["report"]

    update_consensus_summary(
        final_serotype,
        tool_summary.get("serotype", ""),

    )

    final_serotype["report"].update(tool_report)


def rebuild_final_serotype(sample) -> None:
    final_serotype = ensure_final_serotype_category(sample)

    final_serotype["summary"]["serotype"] = ""
    final_serotype["summary"]["antigenic_profile"] = ""
    final_serotype["summary"]["status"] = ""
    final_serotype["report"] = {}

    merge_tool_into_final(final_serotype, find_category_by_name(sample, "enterobase_serotype"))
    merge_tool_into_final(final_serotype, find_category_by_name(sample, "sistr_serotype"))
    merge_tool_into_final(final_serotype, find_category_by_name(sample, "seqsero_serotype"))

    sample.set_category(final_serotype)


def parse_enterobase_results(results: Dict, file_name: str) -> Dict:
    enterobase_serotype1 = ""
    enterobase_count1 = ""
    enterobase_serotype2 = ""
    enterobase_count2 = ""

    with open(file_name, "r", encoding="utf-8") as fh:
        for line in fh:
            fields = line.strip().split("\t")
            if len(fields) != 6:
                continue

            _, _, serotype1, count1, serotype2, count2 = fields
            enterobase_serotype1 = serotype1
            enterobase_count1 = count1
            enterobase_serotype2 = serotype2
            enterobase_count2 = count2

    results["enterobase_serotype1"] = enterobase_serotype1
    results["enterobase_count1"] = enterobase_count1
    results["enterobase_serotype2"] = enterobase_serotype2
    results["enterobase_count2"] = enterobase_count2

    return {
        "enterobase_serotype1": enterobase_serotype1,
        "enterobase_count1": enterobase_count1,
        "enterobase_serotype2": enterobase_serotype2,
        "enterobase_count2": enterobase_count2,
    }


def datadump(input: object, output: object, samplecomponent_ref_json: Dict):
    samplecomponent_ref = SampleComponentReference(value=samplecomponent_ref_json)
    samplecomponent = SampleComponent.load(samplecomponent_ref)
    sample = Sample.load(samplecomponent.sample)

    parsed = parse_enterobase_results(
        samplecomponent["results"],
        input.serotype_file,
    )

    enterobase_category = ensure_tool_category(samplecomponent, "enterobase_serotype")

    enterobase_category["summary"]["serotype"] = parsed["enterobase_serotype1"]
    enterobase_category["summary"]["antigenic_profile"] = ""
    enterobase_category["summary"]["status"] = ""

    enterobase_category["report"]["enterobase_serotype1"] = parsed["enterobase_serotype1"]
    enterobase_category["report"]["enterobase_count1"] = parsed["enterobase_count1"]
    enterobase_category["report"]["enterobase_serotype2"] = parsed["enterobase_serotype2"]
    enterobase_category["report"]["enterobase_count2"] = parsed["enterobase_count2"]

    samplecomponent.set_category(enterobase_category)
    sample.set_category(enterobase_category)

    samplecomponent.save_files()
    common.set_status_and_save(sample, samplecomponent, "Success")

    fresh_sample = Sample.load(samplecomponent.sample)
    rebuild_final_serotype(fresh_sample)
    common.set_status_and_save(fresh_sample, samplecomponent, "Success")

    with open(
        os.path.join(samplecomponent["component"]["name"], "datadump_complete"),
        "w+",
        encoding="utf-8",
    ) as fh:
        fh.write("done")


datadump(
    snakemake.input,
    snakemake.output,
    snakemake.params.samplecomponent_ref_json,
)

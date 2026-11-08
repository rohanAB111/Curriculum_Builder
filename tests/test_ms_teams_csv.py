import os
import sys

BASE_DIR = "/working_dir/c_d8d81eda79d2913e"
sys.path.insert(0, BASE_DIR)

import importlib.abc
import importlib.util

class DirectPathFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if not (fullname.startswith("backend") or fullname.startswith("frontend")):
            return None
        parts = fullname.split(".")
        rel_path = os.path.join(*parts)
        pkg_init = os.path.join(BASE_DIR, rel_path, "__init__.py")
        if os.path.exists(pkg_init):
            return importlib.util.spec_from_file_location(
                fullname, pkg_init, submodule_search_locations=[os.path.join(BASE_DIR, rel_path)]
            )
        mod_py = os.path.join(BASE_DIR, rel_path + ".py")
        if os.path.exists(mod_py):
            return importlib.util.spec_from_file_location(fullname, mod_py)
        return None

sys.meta_path.insert(0, DirectPathFinder())

from backend.app.rag.sakec_obe_rubrics import SAKEC_OBE_RUBRICS_CATALOG, generate_ms_teams_rubric_csv

output_dir = os.path.join(BASE_DIR, "artifacts/file_generation/ttl=63d/output")
sample_dir = os.path.join(BASE_DIR, "sample_output/ms_teams_rubrics")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(sample_dir, exist_ok=True)

for name, criteria in SAKEC_OBE_RUBRICS_CATALOG.items():
    safe_name = name.replace(" ", "_").replace("/", "_").replace("-", "_").replace("(", "").replace(")", "")
    while "__" in safe_name:
        safe_name = safe_name.replace("__", "_")
    csv_str = generate_ms_teams_rubric_csv(title=f"22CS501 - {name}", criteria_list=criteria, total_points=100)
    with open(os.path.join(sample_dir, f"{safe_name}.csv"), "w", encoding="utf-8") as f:
        f.write(csv_str)
    print(f"Generated MS Teams CSV: {safe_name}.csv")

# Also save the exact Reels rubric to output_dir for direct user inspection
reels_criteria = SAKEC_OBE_RUBRICS_CATALOG["25.8 Reel / Blog / Skit Activity Rubric (5 Criteria - MS Teams Standard)"]
reels_csv = generate_ms_teams_rubric_csv("22CS501 CIA Reels & Technical Explainer", reels_criteria, 100)
with open(os.path.join(output_dir, "MS_Teams_Rubric_22CS501_CIA_Reels.csv"), "w", encoding="utf-8") as f:
    f.write(reels_csv)

lab_criteria = SAKEC_OBE_RUBRICS_CATALOG["25.1.1 Computer-Allied Lab Experiment Rubric"]
lab_csv = generate_ms_teams_rubric_csv("22CS501 CIAP Computer-Allied Lab Experiment", lab_criteria, 100)
with open(os.path.join(output_dir, "MS_Teams_Rubric_22CS501_CIAP_Lab.csv"), "w", encoding="utf-8") as f:
    f.write(lab_csv)

print("All MS Teams CSV files generated successfully!")

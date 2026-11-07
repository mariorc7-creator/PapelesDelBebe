import importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name("superagente_official_content_tasks.py")
s=importlib.util.spec_from_file_location("official_content_tasks",P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
URL="https://tramits.gencat.cat/es/tramits/prestacio"
PAGE="https://www.papelesdelbebe.es/ayuda-nacimiento-cataluna/"
def source():
    return {"sources":[{"url":URL,"page":PAGE,"topics":["birth"]}]}
def report(status):
    return {"results":[{"url":URL,"status":status}]}
class OfficialContentTasksTest(unittest.TestCase):
    def test_changed_source_generates_unapproved_task(self):
        result=m.make_tasks(source(),report("changed_needs_review"))
        self.assertEqual(len(result["tasks"]),1)
        self.assertEqual(result["tasks"][0]["page"],PAGE)
        self.assertEqual(result["tasks"][0]["next_step"],"independent_semantic_comparison")
        self.assertFalse(result["tasks"][0]["may_change_html"])
        self.assertFalse(result["publication_allowed"])
    def test_unchanged_is_not_verified_review(self):
        self.assertEqual(m.make_tasks(source(),report("unchanged"))["tasks"],[])
    def test_failed_capture_is_not_a_change(self):
        result=m.make_tasks(source(),report("fetch_failed"))
        self.assertEqual(result["tasks"][0]["next_step"],"repair_capture")
    def test_missing_baseline_is_not_verified(self):
        result=m.make_tasks(source(),report("baseline_missing"))
        self.assertEqual(result["tasks"][0]["next_step"],"establish_verified_baseline")
    def test_unmapped_report_rejected(self):
        with self.assertRaises(ValueError):m.make_tasks(source(),{"results":[{"url":"https://other.example","status":"unchanged"}]})
    def test_unsafe_page_host_rejected(self):
        a=source();a["sources"][0]["page"]="https://external.example/guide"
        with self.assertRaises(ValueError):m.make_tasks(a,report("unchanged"))
    def test_duplicate_report_rejected(self):
        a=report("unchanged");a["results"].append(dict(a["results"][0]))
        with self.assertRaises(ValueError):m.make_tasks(source(),a)
if __name__=="__main__":
    unittest.main()

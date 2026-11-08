import importlib.util
from pathlib import Path
from time import sleep
import unittest
P=Path(__file__).with_name("superagente_official_watch.py")
s=importlib.util.spec_from_file_location("superagente_official_watch",P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class WatchParallelTests(unittest.TestCase):
    def setUp(self):
        self.sources={"sources":[{"url":f"https://official.example/{i}"} for i in range(7)]}
    @staticmethod
    def fake(item,baseline):
        index=int(item["url"].rsplit("/",1)[1])
        # Deliberately finish the initial items last, verifying stable mapping.
        if index<3:sleep(.015)
        return {"url":item["url"],"status":"unchanged"},None
    def test_parallel_keeps_exact_watchlist_order(self):
        results,snaps=m.run(self.sources,{},fetch=self.fake,max_workers=4)
        self.assertEqual([x["url"] for x in results],[x["url"] for x in self.sources["sources"]])
        self.assertEqual(snaps,[])
    def test_worker_count_is_capped(self):
        with self.assertRaises(ValueError):m.run(self.sources,{},fetch=self.fake,max_workers=5)
        with self.assertRaises(ValueError):m.run(self.sources,{},fetch=self.fake,max_workers=0)
    def test_duplicate_source_refused_before_fetch(self):
        self.sources["sources"].append(dict(self.sources["sources"][0]))
        with self.assertRaises(ValueError):m.run(self.sources,{},fetch=self.fake)
    def test_capture_succeeds_only_on_matching_official_host(self):
        item={"url":"https://evil.example/a","approved_host":"www.juntaex.es"}
        result,snapshot=m.capture_official(item,{})
        self.assertEqual(result["status"],"blocked_invalid_host")
        self.assertIsNone(snapshot)
    def test_worker_output_includes_failures_as_results(self):
        def fake(item,baseline):
            return ({"url":item["url"],"status":"fetch_failed"},None)
        results,snapshots=m.run(self.sources,{},fetch=fake)
        self.assertEqual(len(results),7)
        self.assertEqual(snapshots,[])
    def test_snapshot_order_matches_source_order(self):
        def fake(item,baseline):
            return {"url":item["url"],"status":"unchanged"},{"url":item["url"],"text":"source"}
        results,snapshots=m.run(self.sources,{},fetch=fake)
        self.assertEqual([x["url"] for x in snapshots],[x["url"] for x in results])
if __name__=="__main__":unittest.main()

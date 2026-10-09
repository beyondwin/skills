import json
from pathlib import Path
import tempfile
import unittest
import summarize as s

class StudySummaryTests(unittest.TestCase):
 def test_exact_tail(self):
  self.assertEqual(s.tail(0,0),1)
  self.assertEqual(s.tail(8,0),1/256)
  self.assertEqual(s.tail(9,1),11/1024)
  self.assertGreater(s.tail(7,2),.025)
 def test_label_independence(self):
  for mapping in ({'A':'candidate','B':'previous','C':'baseline'},{'A':'baseline','B':'candidate','C':'previous'},{'A':'previous','B':'baseline','C':'candidate'}):
   label=next(k for k,v in mapping.items() if v=='candidate')
   obj={'pairs':{p:{'preferred':label if label in p else 'tie'} for p in ['AB','AC','BC']}}
   self.assertEqual(s.preference(obj,mapping,'previous'),1)
   self.assertEqual(s.preference(obj,mapping,'baseline'),1)
 def test_reject_invalid_choice(self):
  obj={'drafts':{k:{'material_errors':[],'reading_obstacles':[]} for k in 'ABC'},'pairs':{p:{'preferred':'tie','reason':'No difference'} for p in ['AB','AC','BC']}}
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'answer.json';p.write_text(json.dumps(obj));self.assertEqual(s.parse(p),obj)
   obj['pairs']['AB']['preferred']='C';p.write_text(json.dumps(obj))
   with self.assertRaises(AssertionError):s.parse(p)
 def test_mask_only_archive_prefix(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);folder=root/'x--candidate';folder.mkdir()
   original=str(folder/'work/notes.md')+':9 says threshold <= 2; notes.md remains.'
   (folder/'response.txt').write_text(original)
   self.assertEqual(s.run.masked(root,{'id':'x','host':'codex'},'candidate'),'/source/notes.md:9 says threshold <= 2; notes.md remains.')
   self.assertEqual(s.run.masked(root,{'id':'x','host':'opus'},'candidate'),original)

if __name__=='__main__':unittest.main()

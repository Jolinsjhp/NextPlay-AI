import json
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
import server
from test_bound_agents import FixtureRepo

class CDHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
        cls.url='http://127.0.0.1:'+str(cls.http.server_port)
    @classmethod
    def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.thread.join()
    def request(self,path,data=None,headers=None):
        req=urllib.request.Request(self.url+path,data=None if data is None else json.dumps(data).encode(),
            headers={'Content-Type':'application/json',**(headers or {})})
        try:
            with urllib.request.urlopen(req,timeout=10) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:return e.code,json.load(e)
    def test_canonical_agent_route_returns_explicit_missing_configuration(self):
        repo=FixtureRepo();public=repo.compare(repo.request)[0]
        with patch('server.repository',return_value=repo),patch('server.configuration',return_value={}):
            status,value=self.request('/api/decision-analysis/agents',{'request':repo.request,'candidate_set_id':public['candidate_set_id']})
        self.assertEqual(status,200);self.assertEqual(value['status'],'model_unavailable');self.assertEqual(value['agent_trace'],[])
        self.assertEqual(value['candidates'],public['candidates'])
    def test_stale_set_rejected(self):
        repo=FixtureRepo()
        with patch('server.repository',return_value=repo),patch('server.configuration',return_value={}):
            status,_=self.request('/api/decision-analysis/agents',{'request':repo.request,'candidate_set_id':'old'})
        self.assertEqual(status,400)
    def test_public_demo_disables_settings_and_legacy_paid_routes(self):
        with patch.dict('os.environ',{'NEXTPLAY_PUBLIC_ORIGIN':'https://demo.example'}):
            headers={'Host':'demo.example','Origin':'https://demo.example'}
            for path in ('/api/model-settings','/api/agent-review','/api/match-summary'):
                self.assertEqual(self.request(path,{},headers)[0],403)
            self.assertEqual(self.request('/api/model-settings',headers=headers)[0],403)
            self.assertEqual(self.request('/api/decision-analysis/agent-status',headers={**headers,'Origin':'https://other.example'})[0],403)
    def test_status_contains_no_key_or_endpoint(self):
        with patch('server.configuration',return_value={'api_key':'secret','model':'model','base_url':'https://private.example'}):
            status,value=self.request('/api/decision-analysis/agent-status')
        self.assertEqual(status,200);self.assertTrue(value['configured']);self.assertNotIn('secret',json.dumps(value));self.assertNotIn('base_url',value)

if __name__=='__main__':unittest.main()

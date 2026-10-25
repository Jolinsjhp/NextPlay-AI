import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('azure_package',ROOT/'scripts/build_azure_package.py');package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)
class AzurePreparationTests(unittest.TestCase):
    def test_template_never_selects_paid_plan_or_creates_model(self):
        template=json.loads((ROOT/'deploy/azure/main.json').read_text())
        self.assertEqual([r['type'] for r in template['resources']],['Microsoft.Web/serverfarms','Microsoft.Web/sites'])
        self.assertEqual(template['resources'][0]['sku']['name'],'F1')
        settings={x['name']:x['value'] for x in template['resources'][1]['properties']['siteConfig']['appSettings']}
        self.assertEqual(settings['NEXTPLAY_DAILY_MODEL_CALLS'],'0');self.assertEqual(settings['NEXTPLAY_VIDEO_UPLOADS'],'0')
        self.assertNotIn('API_KEY',json.dumps(template))
    def test_package_excludes_uploads_secrets_and_large_duplicate_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ['server.py','.env','.local/model-service.json','.local/video-review/private/media','node_modules/key.json','data/league/matches/m/decisions.jsonl','data/league/matches/m/events.jsonl','realism/model.py','realism/profile.json','video_review/project.py']:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
            selected={p.relative_to(root).as_posix() for p in package.paths(root)}
            self.assertEqual(selected,{'server.py','data/league/matches/m/events.jsonl','realism/model.py','realism/profile.json','video_review/project.py'})
    def test_startup_uses_persistent_state_and_managed_hostname(self):
        script=(ROOT/'deploy/azure/start.sh').read_text()
        self.assertIn('/home/nextplay',script);self.assertIn('WEBSITE_HOSTNAME',script);self.assertNotIn('api_key',script)

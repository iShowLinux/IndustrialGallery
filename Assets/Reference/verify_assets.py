"""Offline checks. Never starts Unreal; run after reference_props.py --generate."""
from pathlib import Path
import ast
import json
import math
import unittest
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'Assets' / 'Reference'

class ReferenceAssetsTests(unittest.TestCase):
    def test_hero_is_real_closed_curved_mesh_with_correct_height(self):
        path = ASSETS / 'Meshes' / 'SM_BronzeLoop.obj'
        self.assertTrue(path.exists(), 'The authored bronze loop mesh must exist')
        vertices, faces = [], []
        for line in path.read_text().splitlines():
            if line.startswith('v '):
                vertices.append(tuple(map(float, line.split()[1:])))
            elif line.startswith('f '):
                faces.append(tuple(int(x.split('/')[0])-1 for x in line.split()[1:]))
        self.assertGreater(len(vertices), 1000)
        self.assertLess(len(faces), 15000)
        self.assertTrue(all(math.isfinite(n) for p in vertices for n in p))
        self.assertAlmostEqual(min(p[2] for p in vertices), 0, places=4)
        self.assertAlmostEqual(max(p[2] for p in vertices), 195, places=4)
        edges = Counter(tuple(sorted((f[i], f[(i+1)%3]))) for f in faces for i in range(3))
        self.assertTrue(all(n == 2 for n in edges.values()), 'Closed manifold sweeps required')
        self.assertGreater(max(p[0] for p in vertices)-min(p[0] for p in vertices), 95)
        volume6 = 0
        for face in faces:
            a,b,c = (vertices[i] for i in face)
            volume6 += a[0]*(b[1]*c[2]-b[2]*c[1]) + a[1]*(b[2]*c[0]-b[0]*c[2]) + a[2]*(b[0]*c[1]-b[1]*c[0])
        self.assertGreater(volume6, 0, 'Normals must point outward')

    def test_complete_asset_package(self):
        manifest_path = ASSETS / 'manifest.json'
        self.assertTrue(manifest_path.exists(), 'Reproducible asset manifest required')
        manifest = json.loads(manifest_path.read_text())
        self.assertGreaterEqual(len(manifest['textures']), 8)
        self.assertIn('SM_CeilingSlats', manifest['meshes'])
        self.assertIn('SM_DuctBands', manifest['meshes'])
        module = ROOT / 'Tools' / 'reference_props.py'
        tree = ast.parse(module.read_text())
        self.assertTrue(any(isinstance(n, ast.FunctionDef) and n.name == 'build' for n in tree.body))
        from PIL import Image
        for texture in manifest['textures']:
            with Image.open(ASSETS / texture) as image:
                self.assertGreaterEqual(image.width, 512)
                image.verify()

    def test_detail_normals_uvs_and_ceiling_envelope(self):
        for name in ['SM_DuctBands','SM_RearLoop','SM_BenchSlats','SM_CeilingSlats']:
            vertices, faces, uv = [], [], []
            for line in (ASSETS/'Meshes'/f'{name}.obj').read_text().splitlines():
                fields=line.split()
                if fields and fields[0]=='v': vertices.append(tuple(map(float,fields[1:])))
                if fields and fields[0]=='vt': uv.append(fields)
                if fields and fields[0]=='f': faces.append(tuple(int(x.split('/')[0])-1 for x in fields[1:]))
            volume=0
            for face in faces:
                a,b,c=(vertices[i] for i in face)
                volume+=a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0])
            self.assertGreater(volume,0,name+' faces must point outward')
            if 'Slats' in name: self.assertEqual(len(uv),len(vertices),'Slats need UVs even in merged fallback')
            if name in ['SM_DuctBands','SM_CeilingSlats']:
                self.assertLessEqual(max(p[2] for p in vertices),410)
                self.assertGreaterEqual(min(p[2] for p in vertices),375)

    def test_build_layout_dry_run_without_unreal(self):
        # Only engine calls are replaced. The real build and framing logic execute.
        # This verifies composition/data contracts, NOT Unreal import/rendering.
        import importlib.util
        import sys
        import types
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('props_under_test',ROOT/'Tools'/'reference_props.py')
        props=importlib.util.module_from_spec(spec); spec.loader.exec_module(props)
        fake=types.SimpleNamespace(load_asset=lambda p:p, log=lambda msg:None)
        records=[]
        mats={name:object() for name in ['wall','floor','ceiling','metal','bronze','wood','black','emissive','glass','stone']}
        def shape(name,loc,size,material,**kw):
            item=dict(name=name,loc=loc,size=size,material=material,**kw)
            records.append(item); return item
        ctx=dict(box=shape,cyl=shape,mat=mats,actors=records)
        def mesh(u,ctx,name,asset,loc,material,rotation=(0,0,0),scale=(1,1,1),folder=''):
            return shape(name,loc,scale,material,rotation=rotation,asset=asset)
        def batch(u,ctx,name,items,material,fallback,origin=(0,0,0)):
            return shape(name,origin,(1,1,1),material,instances=len(items))
        with patch.dict(sys.modules,{'unreal':fake}), patch.object(props,'_import_asset',lambda u,p,c:p), patch.object(props,'_texture_material',lambda u,n,t,r:n), patch.object(props,'_spawn_mesh',mesh), patch.object(props,'_slat_batch',batch):
            result=props.build(ctx)
        self.assertEqual(result['actors'],len(records))
        self.assertEqual(result['artworks'],7)
        self.assertEqual(result['ceiling_slats'],73)
        self.assertLess(len(records),300)
        hero=next(x for x in records if x['name']=='Continuity_Bronze_Interwoven_Loops')
        self.assertEqual(hero['loc'],(220,-120,40))
        self.assertEqual(hero['asset'],'Meshes/SM_BronzeLoop.obj')
        self.assertEqual(len([x for x in records if x['name'].endswith('_Canvas')]),7)
        for item in records:
            self.assertTrue(-700<=item['loc'][0]<=700,item['name'])
            self.assertTrue(-900<=item['loc'][1]<=900,item['name'])
            self.assertGreaterEqual(item['loc'][2],0,item['name'])
            self.assertLessEqual(item['loc'][2],420,item['name'])
        print('Dry-run prop actor count:',len(records))

if __name__ == '__main__':
    unittest.main(verbosity=2)

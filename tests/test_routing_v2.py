"""MEDIA-LTX/IMAGE-EDIT/MODELS/PATHS and ROUTE-2 contracts.

Graph/request tests inspect public prepared requests. Mocked service boundaries
prove diagnostics, not inference. The path regression uses the installed image
decoder and real temporary bytes, with HTTP replaced. Live smokes are separate.
"""
import base64
import json
from pathlib import Path
import os
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit
import harness
import media


def only(graph, kind):
    matches=[n['inputs'] for n in graph.values() if n['class_type']==kind]
    assert len(matches)==1,(kind,len(matches))
    return matches[0]


class RoutingV2Tests(unittest.TestCase):
    def test_default_video_uses_ltx_recipe_and_native_frame_grid(self):
        """MEDIA-LTX: duration drives matching video/audio native lengths and metadata."""
        for duration,frames in [(5,121),(6,145),(15,361)]:
            with self.subTest(duration=duration):
                prepared=media.prepare('video',{'prompt':'The robot raises its hand.','duration':duration,'seed':7})
                graph=prepared['prompt']
                self.assertEqual(only(graph,'UNETLoader')['unet_name'],'ltx-2.5-22b-distilled-transformer-nvfp4.safetensors')
                self.assertEqual(only(graph,'CLIPLoader')['clip_name'],'gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors')
                self.assertEqual(only(graph,'EmptyLTXVLatentVideo')['length'],frames)
                self.assertEqual(only(graph,'LTXVEmptyLatentAudio')['frames_number'],frames)
                self.assertEqual(prepared['frame_count'],frames)
                self.assertEqual(only(graph,'RandomNoise')['noise_seed'],7)
                self.assertEqual(only(graph,'CreateVideo')['fps'],24)
                self.assertEqual(only(graph,'LTXVConditioning')['frame_rate'],24)
                self.assertEqual(only(graph,'ManualSigmas')['sigmas'],'1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0')
                self.assertEqual(only(graph,'KSamplerSelect')['sampler_name'],'euler_ancestral')
                self.assertFalse(any(n['class_type'].startswith(('Wan','MiniMax')) for n in graph.values()))
                self.assertFalse(any(n['class_type'] in ('LoadImage','LTXVImgToVideoInplace') for n in graph.values()))
                empty=only(graph,'LTXVConcatAVLatent')['video_latent'][0]
                self.assertEqual(graph[empty]['class_type'],'EmptyLTXVLatentVideo')
        for values in [{'duration':4},{'duration':16},{'fps':30},{'width':513},{'steps':20},{'cfg':3}]:
            with self.subTest(values=values),self.assertRaises(ValueError):
                media.prepare('video',{'prompt':'x',**values})

    def test_generation_image_is_real_reference_conditioning(self):
        """MEDIA-LTX: source pixels flow through LTX preprocessing into its latent."""
        graph=media.prepare('video',{'prompt':'The robot waves.','reference_image':'refs/robot.png'})['prompt']
        anchor=only(graph,'LTXVImgToVideoInplace')
        prep,slot=anchor['image'];self.assertEqual(slot,0)
        self.assertEqual(graph[prep]['class_type'],'LTXVPreprocess')
        image=graph[prep]['inputs']['image'][0]
        self.assertEqual(graph[image]['class_type'],'LoadImage')
        self.assertEqual(graph[image]['inputs']['image'],'refs/robot.png')
        self.assertEqual(anchor['strength'],0.7)
        self.assertEqual(graph['positive']['inputs']['text'],'The robot waves.')
        latent=only(graph,'LTXVConcatAVLatent')['video_latent'][0]
        self.assertEqual(graph[latent]['class_type'],'LTXVImgToVideoInplace')

    def test_video_edit_uses_every_source_frame_and_plain_prompt(self):
        """MEDIA-LTX: actual source batch conditions regeneration, with no H3 tags."""
        prompt='The same brass robot moves beside a white ceramic plant pot.'
        for strength in (0.0,0.4,1.0):
            graph=media.prepare('video_edit',{'prompt':prompt,'reference_video':'clips/source.mp4','source_strength':strength})['prompt']
            self.assertEqual(graph['positive']['inputs']['text'],prompt)
            anchor=only(graph,'LTXVImgToVideoInplace');self.assertEqual(anchor['strength'],strength)
            prep,slot=anchor['image'];self.assertEqual(slot,0)
            self.assertEqual(graph[prep]['class_type'],'LTXVPreprocess')
            frames,slot=graph[prep]['inputs']['image'];self.assertEqual(slot,0)
            self.assertEqual(graph[frames]['class_type'],'GetVideoComponents')
            source=graph[frames]['inputs']['video'][0]
            self.assertEqual(graph[source]['class_type'],'LoadVideo')
            self.assertEqual(graph[source]['inputs']['file'],'clips/source.mp4')
            self.assertFalse(any(n['class_type'] in ('ImageCompositeMasked','LoadImage') for n in graph.values()))
        default=media.prepare('video_edit',{'prompt':prompt,'reference_video':'clip.mp4'})
        self.assertEqual(only(default['prompt'],'LTXVImgToVideoInplace')['strength'],0.4)
        self.assertEqual(default['frame_count'],121)

    def test_ltx_rejects_invalid_retention_and_h3_protocol_before_network(self):
        """MEDIA-LTX: model-specific controls must not silently change meaning."""
        with patch('media.api') as api:
            for value in (-0.01,1.01,True,'0.4',float('nan')):
                with self.subTest(value=value),self.assertRaises(ValueError):
                    media.prepare('video_edit',{'prompt':'white pot','reference_video':'clip.mp4','source_strength':value},'http://localhost:8189')
            for preset in ('video','video_edit'):
                values={'reference_video':'clip.mp4'} if preset=='video_edit' else {}
                with self.subTest(preset=preset),self.assertRaisesRegex(ValueError,'H3'):
                    media.prepare(preset,{'prompt':'<Video 1> [video editing] Make the pot white.',**values},'http://localhost:8189')
            api.assert_not_called()

    def test_edit_references_are_required_and_unsafe_names_rejected_before_network(self):
        """MEDIA-LTX/IMAGE-EDIT: no hidden worker or service call for missing input."""
        with patch('media.api') as api:
            for preset,key in [('video_edit','reference_video'),('image_edit','reference_image')]:
                with self.subTest(preset=preset),self.assertRaisesRegex(ValueError,key):
                    media.prepare(preset,{'prompt':'edit'},'http://localhost:8189')
                for value in ['../escape','C:\\private.png','%node.path%',None]:
                    with self.subTest(value=value),self.assertRaises(ValueError):
                        media.prepare(preset,{'prompt':'edit',key:value},'http://localhost:8189')
            api.assert_not_called()

    def test_image_edit_keeps_matching_native_reference_and_latent_scale(self):
        """MEDIA-IMAGE-EDIT: source appearance must not be stretched to a square."""
        graph=media.prepare('image_edit',{'prompt':'Make the jacket blue.','reference_image':'portrait.png','seed':9})['prompt']
        self.assertEqual(only(graph,'LoadImage')['image'],'portrait.png')
        self.assertEqual(only(graph,'UNETLoader')['unet_name'],'qwen_image_edit_2511_int8_convrot.safetensors')
        self.assertEqual(only(graph,'LoraLoaderModelOnly')['lora_name'],'Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors')
        self.assertEqual(only(graph,'KSampler')['steps'],4)
        self.assertEqual(only(graph,'KSampler')['seed'],9)
        self.assertEqual(only(graph,'ImageScaleToTotalPixels')['megapixels'],1.0)
        self.assertEqual(only(graph,'TextEncodeQwenImageEditPlus')['image1'],only(graph,'VAEEncode')['pixels'])

    def test_edit_deadlines_and_registry_are_consistent(self):
        """ROUTE-2: new presets work through the public job request validator."""
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'work') as tmp:
            for preset,key,name,deadline in [('video_edit','reference_video','clip.mp4',1800),('image_edit','reference_image','face.png',600)]:
                with self.subTest(preset=preset):
                    self.assertIn(preset,media.PRESETS)
                    request=harness.validate_request('asset',{'preset':preset,'prompt':'edit',key:name},tmp)
                    self.assertEqual(request['timeout_seconds'],deadline)

    def test_doctor_assets_remain_ready_when_optional_ollama_is_offline(self):
        """ROUTE-2: local coding availability must not disable asset diagnostics."""
        def service(url,data=None):
            if '11434' in url:raise OSError('optional worker offline')
            return {'system':{'comfyui_version':'fixture'},'devices':[]}
        def prepare(preset,request,url):
            if preset=='video_edit':self.assertTrue(request.get('reference_video'))
            if preset=='image_edit':self.assertTrue(request.get('reference_image'))
            return {'kind':'video' if preset.startswith('video') else 'image','prompt':{}}
        with patch('harness.http_json',side_effect=service),patch('media.prepare',side_effect=prepare):
            result=harness.doctor({'model':'qwen3.8:27b-codex','ollama_url':'http://localhost:11434','comfy_url':'http://localhost:8189'})
        self.assertTrue(result['ready'])
        self.assertFalse(result['local_worker_ready'])
        self.assertIn('video_edit',result['presets'])
        self.assertIn('image_edit',result['presets'])
        self.assertIn('reference_video',result['presets']['video_edit']['required_inputs'])

    def test_asset_status_names_ltx_instead_of_the_optional_coding_worker(self):
        """ROUTE-2: real job storage records the asset model; inference is replaced."""
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'work') as tmp:
            root=Path(tmp);store=harness.JobStore(root/'state')
            request={'preset':'video_edit','prompt':'Make the pot white.','reference_video':'clip.mp4','timeout_seconds':1800}
            job=store.create('asset',request,root)
            graph=media.prepare('video_edit',{k:v for k,v in request.items() if k not in {'preset','timeout_seconds'}})['prompt']
            info={n['class_type']:{'input':{'required':{}}} for n in graph.values()}
            config={'model':'qwen3.8:27b-codex','ollama_url':'http://localhost:11434','comfy_url':'http://localhost:8189'}
            with patch('harness.GPU_ROOT',root/'gpu'),patch('harness.prepare_gpu'),patch('media.validate_video_source',return_value={'frames':121,'fps':24}),patch('media.api',return_value=info),patch('media.submit',side_effect=lambda prepared,url,prompt_id:prompt_id),patch('media.poll',return_value={'state':'succeeded','outputs':[{'filename':'result.mp4','type':'output'}]}),patch('media.retrieve',return_value=[str(root/'result.mp4')]):
                harness.execute_job(store,job['id'],config)
            status=store.read(job['id'])
            self.assertEqual(status['state'],'succeeded')
            self.assertIn('ltx-2.5',status['model'].lower())
            self.assertNotIn('qwen',status['model'].lower())

    def test_video_source_guard_runs_before_gpu_and_submission(self):
        """MEDIA-SOURCE/ROUTE-2: an incompatible source stops the real job lifecycle."""
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'work') as tmp:
            root=Path(tmp);store=harness.JobStore(root/'state')
            request={'preset':'video_edit','prompt':'Make the pot white.','reference_video':'clip.mp4','timeout_seconds':1800}
            job=store.create('asset',request,root)
            graph=media.prepare('video_edit',{k:v for k,v in request.items() if k not in {'preset','timeout_seconds'}})['prompt']
            info={n['class_type']:{'input':{'required':{}}} for n in graph.values()}
            config={'model':'qwen3.8:27b-codex','ollama_url':'http://localhost:11434','comfy_url':'http://localhost:8189','comfy_input_dir':str(root/'input')}
            with patch('harness.GPU_ROOT',root/'gpu'),patch('harness.prepare_gpu') as gpu,patch('media.api',return_value=info),patch('media.validate_video_source',side_effect=ValueError('stage a 24fps native clip')) as probe,patch('media.submit',side_effect=RuntimeError('should not submit')) as submit:
                harness.execute_job(store,job['id'],config)
            self.assertIn('24fps',store.read(job['id'])['error'])
            probe.assert_called_once()
            self.assertEqual(probe.call_args.args[2],121)
            self.assertEqual(probe.call_args.kwargs['expected_aspect'],(512,512))
            gpu.assert_not_called()
            submit.assert_not_called()

    def test_vae_and_lora_missing_files_are_rejected_for_both_combo_formats(self):
        """MEDIA-MODELS: missing model weights are explicit preflight errors."""
        for preset,request,node,field in [('video',{'prompt':'x'},'VAELoader','vae_name'),('image_edit',{'prompt':'x','reference_image':'x.png'},'LoraLoaderModelOnly','lora_name')]:
            graph=media.prepare(preset,request)['prompt']
            for spec in [[['missing.safetensors']],['COMBO',{'options':['missing.safetensors']}]]:
                info={n['class_type']:{'input':{'required':{}}} for n in graph.values()}
                info[node]['input']['required'][field]=spec
                with self.subTest(preset=preset,spec=spec),patch('media.api',return_value=info),self.assertRaisesRegex(ValueError,'Missing model'):
                    media.prepare(preset,request,'http://localhost:8189')

    def test_windows_output_subfolder_roundtrips_without_allowing_traversal(self):
        """MEDIA-PATHS: server-native separators must survive safe output retrieval."""
        decoder=Path(os.environ.get('COMFY_PYTHON',''))
        if not decoder.is_file():self.skipTest('installed decoder absent')
        png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aS1cAAAAASUVORK5CYII=')
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'work') as tmp,patch('media.fetch',return_value=png) as fetch:
            paths=media.retrieve([{'filename':'image.png','subfolder':'harness\\project','type':'output'}],tmp,'image','http://localhost:8189',str(decoder))
            self.assertTrue(Path(paths[0]).is_file())
            self.assertEqual(parse_qs(urlsplit(fetch.call_args.args[1]).query)['subfolder'],['harness/project'])
        with patch('media.fetch') as fetch:
            for name in ['..\\input','\\absolute','C:\\input']:
                with self.subTest(name=name),self.assertRaises(ValueError):
                    media.retrieve([{'filename':'image.png','subfolder':name,'type':'output'}],'.','image','http://localhost:8189')
            fetch.assert_not_called()

    def test_input_names_reject_comfy_folder_annotations_and_windows_aliases(self):
        """MEDIA-LTX/PATHS: references cannot select non-input folders or OS aliases."""
        for name in ['folder/','folder//image.png','x.png [output]','x.png [temp]','.. /image.png','folder./image.png','image.png ']:
            with self.subTest(name=name),self.assertRaises(ValueError):
                media.prepare('video',{'prompt':'x','reference_image':name})

    def test_asset_gpu_handoff_tolerates_refused_optional_ollama_connection(self):
        """ROUTE-2/GPU-1: a stopped optional engine cannot block healthy Comfy work."""
        config={'model':'qwen3.8:27b-codex','ollama_url':'http://localhost:11434','comfy_url':'http://localhost:8189'}
        def service(url,data=None):
            if '11434' in url:raise URLError(ConnectionRefusedError('service stopped'))
            return {'queue_running':[],'queue_pending':[]}
        with patch('harness.http_json',side_effect=service):
            harness.prepare_gpu('asset',config,time.monotonic()+3,lambda:False)

    def test_asset_gpu_handoff_does_not_load_an_absent_worker_to_unload_it(self):
        """ROUTE-2/GPU-1: inspect residency first; no generation request when empty."""
        config={'model':'qwen3.8:27b-codex','ollama_url':'http://localhost:11434','comfy_url':'http://localhost:8189'}
        calls=[]
        def service(url,data=None):
            calls.append((url,data))
            if '11434' in url:return {'models':[]}
            return {'queue_running':[],'queue_pending':[]}
        with patch('harness.http_json',side_effect=service):
            harness.prepare_gpu('asset',config,time.monotonic()+3,lambda:False)
        self.assertFalse(any(url.endswith('/api/generate') for url,_ in calls))

    def test_asset_gpu_handoff_still_unloads_owned_worker_and_waits(self):
        """ROUTE-2/GPU-1: optional routing must retain unload-before-Comfy ordering."""
        config={'model':'qwen3.8:27b-codex','ollama_url':'http://localhost:11434','comfy_url':'http://localhost:8189'}
        calls=[];residency=[{'models':[{'name':config['model']}]},{'models':[]}]
        def service(url,data=None):
            calls.append((url,data))
            if url.endswith('/queue'):return {'queue_running':[],'queue_pending':[]}
            if url.endswith('/api/ps'):return residency.pop(0)
            return {}
        with patch('harness.http_json',side_effect=service):
            harness.prepare_gpu('asset',config,time.monotonic()+3,lambda:False)
        ollama=[(url,data) for url,data in calls if '11434' in url]
        self.assertEqual([url.rsplit('/',1)[-1] for url,_ in ollama],['ps','generate','ps'])
        self.assertEqual(ollama[1][1],{'model':config['model'],'keep_alive':0})

    def test_asset_gpu_handoff_keeps_unknown_residency_errors_visible(self):
        """ROUTE-2/GPU-1: timeout is not proof that the other engine released VRAM."""
        config={'model':'qwen3.8:27b-codex','ollama_url':'http://localhost:11434','comfy_url':'http://localhost:8189'}
        def service(url,data=None):
            if '11434' in url:raise TimeoutError('residency unknown')
            return {'queue_running':[],'queue_pending':[]}
        with patch('harness.http_json',side_effect=service),self.assertRaises(TimeoutError):
            harness.prepare_gpu('asset',config,time.monotonic()+3,lambda:False)

    def test_asset_gpu_handoff_rejects_unknown_model_names(self):
        """ROUTE-2/GPU-1: a malformed residency item is not an empty GPU."""
        config={'model':'qwen3.8:27b-codex','ollama_url':'http://localhost:11434','comfy_url':'http://localhost:8189'}
        for models in [[{'name':None}],[{'name':''}],[{}]]:
            def service(url,data=None):
                if '11434' in url:return {'models':models}
                return {'queue_running':[],'queue_pending':[]}
            with self.subTest(models=models),patch('harness.http_json',side_effect=service),self.assertRaises(ValueError):
                harness.prepare_gpu('asset',config,time.monotonic()+3,lambda:False)

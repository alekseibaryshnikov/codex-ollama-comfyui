"""MEDIA-SOURCE in media.py: actual CPU PyAV metadata/frame-time validation.

Fixtures are tiny locally encoded clips, not generation models. The installed
decoder is real; HTTP and GPU are not involved. Fixtures cover 30fps and a VFR
clip whose average rate remains exactly 24, plus native frame-count boundaries.
"""
from fractions import Fraction
import json
from pathlib import Path
import os
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import media


class VideoSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decoder=Path(os.environ.get('COMFY_PYTHON',''))
        if not cls.decoder.is_file():raise unittest.SkipTest('installed decoder absent')
        cls.temp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'work')
        cls.root=Path(cls.temp.name)
        script='''import av,sys,json,subprocess
from pathlib import Path
import os
from fractions import Fraction
from PIL import Image
root=Path(sys.argv[1])
for name,rate,count in [('valid',24,124),('fps30',30,124),('vfr',24,124),('short',24,123),('long',24,125),('wide',24,124)]:
 with av.open(str(root/(name+'.mp4')),'w') as target:
  stream=target.add_stream('libx264',rate=rate,options={'crf':'20','preset':'ultrafast'})
  size=(128,64) if name=='wide' else (64,64)
  stream.width,stream.height=size;stream.pix_fmt='yuv420p'
  time_base=Fraction(1,48 if name=='vfr' else rate)
  stream.time_base=time_base
  stream.codec_context.time_base=time_base
  for i in range(count):
   frame=av.VideoFrame.from_image(Image.new('RGB',size,(i%255,70,100)))
   frame.time_base=time_base
   frame.pts=i*2+(1 if 10<=i<20 else 0) if name=='vfr' else i
   for packet in stream.encode(frame):target.mux(packet)
  for packet in stream.encode():target.mux(packet)
with av.open(str(root/'vfr.mp4')) as c:
 assert c.streams.video[0].average_rate==24,c.streams.video[0].average_rate
 times=[f.pts*f.time_base for f in c.decode(video=0)]
 assert any(times[i]-times[i-1]!=Fraction(1,24) for i in range(1,len(times)))
try:
 import imageio_ffmpeg
except ImportError:
 pass
else:
 subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-display_rotation:v:0','90','-i',str(root/'wide.mp4'),'-c','copy',str(root/'rotated.mp4')],check=True)
 with av.open(str(root/'rotated.mp4')) as c:
  f=next(c.decode(video=0))
  assert (f.width,f.height)==(128,64) and abs(f.rotation)%180==90,(f.width,f.height,f.rotation)
print('fixture rates, VFR timestamps and rotation metadata independently checked')
'''
        result=subprocess.run([str(cls.decoder),'-c',script,str(cls.root)],capture_output=True,text=True,timeout=30)
        if result.returncode:
            cls.temp.cleanup();raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def probe(self,name,**kwargs):
        return media.validate_video_source(name,self.root,124,str(self.decoder),**kwargs)

    def test_verified_24fps_native_length_returns_real_metadata(self):
        """MEDIA-SOURCE: a 124-frame CFR clip is suitable for a native preview."""
        info=self.probe('valid.mp4')
        self.assertEqual(info['frames'],124)
        self.assertEqual(info['fps'],24)
        self.assertEqual((info['width'],info['height']),(64,64))
        self.assertAlmostEqual(info['duration_seconds'],124/24,places=6)

    def test_requested_aspect_must_match_before_implicit_center_crop(self):
        """MEDIA-ASPECT: real 64-square source may scale square, not crop to wide."""
        self.assertEqual(self.probe('valid.mp4',expected_aspect=(512,512))['width'],64)
        with self.assertRaisesRegex(ValueError,'aspect'):
            self.probe('valid.mp4',expected_aspect=(768,448))

    def test_display_rotation_controls_decoded_dimensions_and_aspect(self):
        """MEDIA-ASPECT: a real 90-degree display matrix must match native loading."""
        if not (self.root/'rotated.mp4').exists():self.skipTest('bundled FFmpeg absent')
        info=self.probe('rotated.mp4')
        self.assertEqual((info['width'],info['height']),(64,128))
        self.assertEqual(self.probe('rotated.mp4',expected_aspect=(256,512))['width'],64)
        with self.assertRaisesRegex(ValueError,'aspect'):
            self.probe('rotated.mp4',expected_aspect=(512,256))

    def test_non24fps_and_variable_timing_are_rejected(self):
        """MEDIA-SOURCE: source time must not be reinterpreted as another frame rate."""
        for name in ['fps30.mp4','vfr.mp4']:
            with self.subTest(name=name),self.assertRaises(ValueError):self.probe(name)

    def test_native_length_must_match_instead_of_silent_truncation(self):
        """MEDIA-SOURCE: both short input and an unselected long source are errors."""
        for name in ['short.mp4','long.mp4']:
            with self.subTest(name=name),self.assertRaises(ValueError):self.probe(name)

    def test_source_stays_inside_configured_input_root(self):
        """MEDIA-SOURCE: invalid paths, missing files and missing configuration fail."""
        for name in ['../outside.mp4','valid.mp4 [output]','missing.mp4']:
            with self.subTest(name=name),self.assertRaises(ValueError):self.probe(name)
        with self.assertRaises(ValueError):media.validate_video_source('valid.mp4',None,124,str(self.decoder))

    def test_pre_cancelled_or_expired_probe_never_starts_decoder(self):
        """MEDIA-SOURCE: invalidated jobs cannot launch another owned process."""
        with patch('media.subprocess.Popen') as spawn:
            with self.assertRaises(InterruptedError):self.probe('valid.mp4',cancelled=lambda:True)
            with self.assertRaises(TimeoutError):self.probe('valid.mp4',deadline=time.monotonic()-1)
            spawn.assert_not_called()

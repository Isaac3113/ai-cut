"""Real short PCM regression: BGM controls must not alter the voice baseline."""
import copy
import math
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from talking_head_editor.render import render_audio
from talking_head_editor.timeline import compile_clips, default_plan
from talking_head_editor.util import executable, file_hash


class AudioLevelTests(unittest.TestCase):
    @staticmethod
    def tone(path, frequency, amplitude, duration=6.6, rate=48000):
        time=np.arange(round(duration*rate),dtype=np.float64)/rate
        signal=amplitude*np.sin(2*np.pi*frequency*time)
        samples=np.round(np.column_stack([signal,signal])*32767).astype('<i2')
        with wave.open(str(path),'wb') as output:
            output.setparams((2,2,rate,len(samples),'NONE','not compressed'))
            output.writeframes(samples.tobytes())

    @staticmethod
    def pcm(path):
        with wave.open(str(path),'rb') as source:
            if source.getsampwidth()!=2:
                raise AssertionError('Expected final 16-bit PCM mix')
            rate=source.getframerate()
            signal=np.frombuffer(source.readframes(source.getnframes()),dtype='<i2')
            return signal.reshape(-1,source.getnchannels()).astype(np.float64)/32768,rate

    @staticmethod
    def amplitude(signal,frequency,rate):
        mono=signal.mean(axis=1)
        clock=np.arange(len(mono),dtype=np.float64)/rate
        return float(2*abs(np.mean(mono*np.exp(-2j*np.pi*frequency*clock))))

    def test_music_halves_after_voice_normalization_without_changing_voice(self):
        # Mandatory integration check: a missing local runtime is an explicit
        # failure, never a silently skipped audio regression.
        executable('ffmpeg');executable('ffprobe')
        with tempfile.TemporaryDirectory(prefix='talking-head-audio-level-') as temporary:
            job=Path(temporary)
            source=job/'quiet-voice.wav';music=job/'test-music.wav'
            self.tone(source,300,.003)
            self.tone(music,880,.3)
            plan=default_plan(6.6,0);plan['music_asset_id']='bg'
            plan['style']['music_gain_db']=-18.
            project={'plan':plan,'source':{'path':source.name,'sha256':file_hash(source)},
                     'assets':{'bg':{'path':music.name,'sha256':file_hash(music),'kind':'audio','duration':6.6}}}
            clips=compile_clips(plan['clips'],1.1)
            high,used=render_audio(job,project,clips,plan['style'])
            self.assertFalse(used)
            voice_files=list(job.rglob('voice.wav'))
            self.assertTrue(voice_files,'A separately normalized voice baseline must be retained')
            voice_hashes={str(path.relative_to(job)):file_hash(path) for path in voice_files}

            low_project=copy.deepcopy(project)
            low_project['plan']['style']['music_gain_db']=-18.-20*math.log10(2)
            low,used=render_audio(job,low_project,clips,low_project['plan']['style'])
            self.assertFalse(used);self.assertNotEqual(high,low)
            self.assertEqual(voice_hashes,{str(path.relative_to(job)):file_hash(path) for path in job.rglob('voice.wav')},
                             'Changing only BGM must reuse the same normalized voice cache')
            self.assertEqual(render_audio(job,low_project,clips,low_project['plan']['style']),(low,True))

            voice_project=copy.deepcopy(project);voice_project['plan'].pop('music_asset_id')
            voice,_=render_audio(job,voice_project,clips,voice_project['plan']['style'])
            self.assertEqual(voice_hashes,{str(path.relative_to(job)):file_hash(path) for path in job.rglob('voice.wav')})
            high_pcm,rate=self.pcm(high);low_pcm,low_rate=self.pcm(low);voice_pcm,voice_rate=self.pcm(voice)
            self.assertEqual(rate,48000);self.assertEqual((low_rate,voice_rate),(rate,rate))
            self.assertEqual(high_pcm.shape,low_pcm.shape);self.assertEqual(high_pcm.shape,voice_pcm.shape)
            self.assertAlmostEqual(len(voice_pcm)/rate,6.,places=3)
            # Avoid opening/final fades. Subtract the separately normalized voice
            # only after normalization, unlike subtracting original quiet speech.
            selection=slice(2*rate,4*rate)
            high_bg=high_pcm[selection]-voice_pcm[selection]
            low_bg=low_pcm[selection]-voice_pcm[selection]
            rms_high=float(np.sqrt(np.mean(high_bg**2)));rms_low=float(np.sqrt(np.mean(low_bg**2)))
            self.assertGreater(rms_high,5/32768,'Background must have measurable nonzero energy')
            self.assertAlmostEqual(rms_low/rms_high,.5,delta=.025)
            bg_high=self.amplitude(high_bg,880,rate);bg_low=self.amplitude(low_bg,880,rate)
            self.assertAlmostEqual(bg_low/bg_high,.5,delta=.015)
            voice_amp=self.amplitude(voice_pcm[selection],300,rate)
            self.assertGreater(voice_amp,.03,'The initially quiet narration must be normalized first')
            for label,signal in [('high',high_pcm),('low',low_pcm)]:
                with self.subTest(mix=label):
                    self.assertAlmostEqual(self.amplitude(signal[selection],300,rate)/voice_amp,1.,delta=.002)
                    self.assertLess(float(np.max(np.abs(signal))),.99)


if __name__=='__main__':unittest.main()

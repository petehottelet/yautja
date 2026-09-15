"""Execute tagged README/reference recipes on fixtures; models are opt-in."""
import argparse
from contextlib import redirect_stdout, redirect_stderr, contextmanager
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from yautja.cli import main as convert, parser
from .build_skill_bundle import ROOT
from .check_docs import recipes, inventory


@contextmanager
def working_directory(path):
    previous=Path.cwd(); os.chdir(path)
    try: yield
    finally: os.chdir(previous)


def fixtures(folder, source=None):
    image=Image.new('RGB',(320,180),(55,70,85))
    draw=ImageDraw.Draw(image)
    draw.rectangle((70,35,130,165),fill=(175,135,90)); draw.ellipse((78,10,123,58),fill=(205,165,130))
    image.save(folder/'photo.jpg')
    shutil.copyfile(ROOT/'src/yautja/assets/fonts/Michroma-Regular.ttf',folder/'my-font.ttf')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise ValueError('README video verification requires FFmpeg and ffprobe')
    if source:
        command=['ffmpeg','-v','error','-y','-i',str(source),'-t','4.2','-vf','scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2,fps=24','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(folder/'clip.mov')]
    else:
        command=['ffmpeg','-v','error','-y','-loop','1','-framerate','24','-i',str(folder/'photo.jpg'),'-f','lavfi','-i','sine=frequency=330:sample_rate=48000',
                 '-t','4.2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(folder/'clip.mov')]
    subprocess.run(command,check=True,capture_output=True)
    if source:
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(folder/'clip.mov'),'-frames:v','1',str(folder/'photo.jpg')],check=True,capture_output=True)
    return image


def catalog_fixture(folder, image):
    # Catalog selection is independent of detection; one declared fixture figure
    # makes the documented ID deterministic without falsifying model results.
    from yautja.figures import FigureCatalog
    from yautja.semantic import Subject
    mask=np.zeros((180,320),np.float32); mask[10:165,70:131]=1
    catalog=FigureCatalog(folder/'clip.mov',fps=24)
    for i in range(101): catalog.add(image,i/24,[Subject(mask,'person',.95,track_id=1)],1)
    (folder/'figures.json').write_text(json.dumps(catalog.data),encoding='utf-8')


def arguments(command):
    if command[0]=='yautja': return command[1:]
    if command[:3]==['python','-m','yautja']: return command[3:]
    raise ValueError('Tagged examples must invoke Yautja directly: '+str(command))


def verify(*, models=False, only=None, source=None, fast=False):
    records=recipes(); known=inventory(); flags={flag:dest for dest,r in known.items() for flag in r['flags']}
    result={'passed':[],'skipped':{},'exercised_families':[], 'commands':0}
    exercised=set(); model_cache={}
    # Cache model instances only, not masks or output: every conversion still
    # executes the real tracker and renderer. No downloads occur in this path.
    from yautja.semantic import GroundedSegmenter
    def cached_segmenter(**options):
        key=tuple(sorted(options.items()))
        if key not in model_cache: model_cache[key]=GroundedSegmenter(**options)
        return model_cache[key]
    with tempfile.TemporaryDirectory(prefix='yautja-readme-') as name:
        folder=Path(name); image=fixtures(folder,source)
        with working_directory(folder), patch('yautja.semantic.GroundedSegmenter',side_effect=cached_segmenter):
            for identifier, recipe in records.items():
                if only and identifier not in only: continue
                if recipe['tier']=='setup': result['skipped'][identifier]='explicit one-time network setup'; continue
                if recipe['tier']=='models' and not models: result['skipped'][identifier]='enable --models with cached weights'; continue
                if fast and identifier not in ('inspect','lightweight','led-inkblot','save','reuse','catalog-target'):
                    result['skipped'][identifier]='fast CI smoke'; continue
                recipe_folder=folder/identifier
                recipe_folder.mkdir()
                for filename in ('photo.jpg','clip.mov','my-font.ttf','my-style.json','readme-style.json'):
                    if (folder/filename).exists(): shutil.copyfile(folder/filename,recipe_folder/filename)
                os.chdir(recipe_folder)
                if identifier=='catalog-target': catalog_fixture(recipe_folder,image)
                for command in recipe['commands']:
                    args=arguments(command)
                    with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                        try: parsed=parser().parse_args(args)
                        except SystemExit as exc:
                            if exc.code: raise
                            parsed=SimpleNamespace(output=None,save_preset=None)
                    stdout,stderr=io.StringIO(),io.StringIO()
                    with redirect_stdout(stdout),redirect_stderr(stderr):
                        try: status=convert(args)
                        except SystemExit as exc: status=exc.code
                    if status: raise ValueError(f'{identifier} failed ({status}): {command}\n{stderr.getvalue()}\n{stdout.getvalue()}')
                    result['commands']+=1
                    exercised.update(flags[token.split('=',1)[0]] for token in args if token.split('=',1)[0] in flags)
                    if parsed.output:
                        if not parsed.output.is_file() or parsed.output.stat().st_size==0: raise ValueError(identifier+': missing output')
                        if parsed.output.suffix=='.png':
                            with Image.open(parsed.output) as im: im.verify()
                        if parsed.output.suffix=='.mp4':
                            subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(parsed.output),'-f','null','-'],check=True,capture_output=True)
                    if parsed.save_preset:
                        payload=json.loads(parsed.save_preset.read_text())
                        if payload['schema_version']!=1: raise ValueError(identifier+': invalid preset schema')
                        shutil.copyfile(parsed.save_preset,folder/parsed.save_preset.name)
                    if recipe.get('checks'):
                        report=json.loads(stdout.getvalue())
                        for key,expected in recipe['checks'].items():
                            if report.get(key)!=expected: raise ValueError(f'{identifier}: {key} expected {expected!r}, got {report.get(key)!r}')
                result['passed'].append(identifier)
                print('Verified '+identifier,flush=True)
    result['exercised_families']=sorted(exercised)
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--models',action='store_true',help='Also execute segmented examples with cached local models')
    p.add_argument('--source',type=Path,help='Optional local video fixture, resized to 320x180; never uploaded')
    p.add_argument('--only',nargs='+'); p.add_argument('--fast',action='store_true')
    args=p.parse_args(argv)
    result=verify(models=args.models,only=args.only,source=args.source.resolve() if args.source else None,fast=args.fast)
    print(json.dumps(result,indent=2)); return 0


if __name__=='__main__': raise SystemExit(main())

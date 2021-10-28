'''
  Copyright (c) 2021 caoccao.com Sam Cao
  All rights reserved.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
'''

import importlib
import logging
import os
import pathlib
import shutil
import sys

if hasattr(importlib, 'util') and importlib.util.find_spec('coloredlogs'):
  import coloredlogs
  coloredlogs.install(level=logging.DEBUG, fmt='%(asctime)-15s %(name)s %(levelname)s: %(message)s')

class PatchAndroidBuild(object):
  def __init__(self) -> None:
    self._line_separator = '\n'
    self._patch_dict = {
      'java.time.': 'org.threeten.bp.',
      '.getParameterCount()': '.getParameterTypes().length',
      'import java.util.stream.BaseStream;': '',
      'import java.util.stream.DoubleStream;': '',
      'import java.util.stream.IntStream;': '',
      'import java.util.stream.LongStream;': '',
      'import java.util.stream.Stream;': '',
    }
    self._ignore_begin = '// Javet Android Ignore Begin'
    self._ignore_end = '// Javet Android Ignore End'
    root_dir_path = pathlib.Path(__file__).parent.joinpath('../../').resolve().absolute()
    self._source_dir_path = root_dir_path.joinpath('src/main/java/com/caoccao/javet').resolve().absolute()
    self._target_dir_path = root_dir_path.joinpath('android/javet-android/src/main/java/com/caoccao/javet').resolve().absolute()

  def patch(self):
    logging.info('Patch Android Build')
    if not self._source_dir_path.exists():
      logging.error('%s is not found.', self._source_dir_path)
      return 1
    if not self._target_dir_path.exists():
      self._target_dir_path.mkdir(parents=True)
      logging.info('%s is created.', self._target_dir_path)
    logging.info('From %s', self._source_dir_path)
    logging.info('  To %s', self._target_dir_path)

    # Source to Target
    for root, dir_names, file_names in os.walk(str(self._source_dir_path)):
      root_path = pathlib.Path(root)
      for file_name in file_names:
        source_file_path = root_path.joinpath(file_name).resolve().absolute()
        target_file_path = self._target_dir_path.joinpath(source_file_path.relative_to(self._source_dir_path)).resolve().absolute()
        if not target_file_path.parent.exists():
          target_file_path.parent.mkdir(parents=True)
          logging.info('%s is created.', target_file_path.parent)
        lines = []
        ignore = False
        for line in source_file_path.read_bytes().decode('utf-8').split(self._line_separator):
          for (patch_key, patch_value) in self._patch_dict.items():
            if patch_key in line:
              line = line.replace(patch_key, patch_value)
          if self._ignore_begin in line:
            ignore = True
          if not ignore:
            lines.append(line)
          if self._ignore_end in line:
            ignore = False
        buffer = self._line_separator.join(lines).encode('utf-8')
        to_be_copied = True
        if target_file_path.exists():
          to_be_copied = buffer != target_file_path.read_bytes()
        if to_be_copied:
          target_file_path.write_bytes(buffer)
          logging.info('%s is copied.', target_file_path)

    # Target to Source
    for root, dir_names, file_names in os.walk(str(self._target_dir_path)):
      root_path = pathlib.Path(root)
      for dir_name in dir_names:
        target_dir_path = root_path.joinpath(dir_name).resolve().absolute()
        source_dir_path = self._source_dir_path.joinpath(target_dir_path.relative_to(self._target_dir_path)).resolve().absolute()
        if not source_dir_path.exists():
          shutil.rmtree(str(target_dir_path))
          logging.info('%s is deleted.', target_dir_path)
      for file_name in file_names:
        target_file_path = root_path.joinpath(file_name).resolve().absolute()
        source_file_path = self._source_dir_path.joinpath(target_file_path.relative_to(self._target_dir_path)).resolve().absolute()
        if not source_file_path.exists():
          target_file_path.unlink()
          logging.info('%s is deleted.', target_file_path)

    return 0

def main():
  return PatchAndroidBuild().patch()

if __name__ == '__main__':
  sys.exit(int(main() or 0))

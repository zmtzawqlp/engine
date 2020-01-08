#!/usr/bin/env python
#
# Copyright 2013 The Flutter Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''
Tests for font-subset
'''

import filecmp
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
MATERIAL_TTF = os.path.join(SCRIPT_DIR, 'fixtures', 'MaterialIcons-Regular.ttf')
IS_WINDOWS = sys.platform.startswith(('cygwin', 'win'))
EXE = '.exe' if IS_WINDOWS else ''
BAT = '.bat' if IS_WINDOWS else ''
FONT_SUBSET = os.path.join(SRC_DIR, 'out', 'host_debug', 'font-subset' + EXE)
if not os.path.isfile(FONT_SUBSET):
  FONT_SUBSET = os.path.join(SRC_DIR, 'out', 'host_debug_unopt', 'font-subset' + EXE)
if not os.path.isfile(FONT_SUBSET):
  raise Exception('Could not locate font-subset%s in host_debug or host_debug_unopt - build before running this script.' % EXE)

COMPARE_TESTS = (
  (True,  '1.ttf', MATERIAL_TTF, [r'57347']),
  (True,  '1.ttf', MATERIAL_TTF, [r'0xE003']),
  (True,  '1.ttf', MATERIAL_TTF, [r'\uE003']),
  (False, '1.ttf', MATERIAL_TTF, [r'57348']), # False because different codepoint
  (True,  '2.ttf', MATERIAL_TTF, [r'0xE003', r'0xE004']),
  (True,  '2.ttf', MATERIAL_TTF, [r'0xE003', r'0xE004', r'57347',]), # Duplicated codepoint
  (True,  '3.ttf', MATERIAL_TTF, [r'0xE003', r'0xE004', r'0xE021',]),
)

FAIL_TESTS = [
  ([FONT_SUBSET, 'output.ttf', 'does-not-exist.ttf'], ['1',]), # non-existant input font
  ([FONT_SUBSET, 'output.ttf', MATERIAL_TTF], ['0xFFFFFFFF',]), # Value too big.
  ([FONT_SUBSET, 'output.ttf', MATERIAL_TTF], ['-1',]), # invalid value
  ([FONT_SUBSET, 'output.ttf', MATERIAL_TTF], ['foo',]), # no valid values
  ([FONT_SUBSET, 'output.ttf', MATERIAL_TTF], ['0xE003', '0x12', '0xE004',]), # codepoint not in font
  ([FONT_SUBSET, 'non-existant-dir/output.ttf', MATERIAL_TTF], ['0xE003',]), # dir doesn't exist
  ([FONT_SUBSET, 'output.ttf', MATERIAL_TTF], [' ',]), # empty input
  ([FONT_SUBSET, 'output.ttf', MATERIAL_TTF], []), # empty input
  ([FONT_SUBSET, 'output.ttf', MATERIAL_TTF], ['']), # empty input
]

def RunCmd(cmd, codepoints, fail=False):
  print('Running command:')
  print('       %s' % ' '.join(cmd))
  print('STDIN: "%s"' % ' '.join(codepoints))
  p = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=SRC_DIR
  )
  stdout_data, stderr_data = p.communicate(input=' '.join(codepoints))
  if p.returncode != 0 and fail == False:
    print('FAILURE: %s' % p.returncode)
    print('STDOUT:')
    print(stdout_data)
    print('STDERR:')
    print(stderr_data)
  elif p.returncode == 0 and fail == True:
    print('FAILURE - test passed but should have failed.')
    print('STDOUT:')
    print(stdout_data)
    print('STDERR:')
    print(stderr_data)
  else:
    print('Success.')

  return p.returncode


def main():
  print('Using font subset binary at %s' % FONT_SUBSET)
  failures = 0
  for should_pass, golden_font, input_font, codepoints in COMPARE_TESTS:
    gen_ttf = os.path.join(SCRIPT_DIR, 'gen', golden_font)
    golden_ttf = os.path.join(SCRIPT_DIR, 'fixtures', golden_font)
    cmd = [FONT_SUBSET, gen_ttf, input_font]
    RunCmd(cmd, codepoints)
    cmp = filecmp.cmp(gen_ttf, golden_ttf, shallow=False)
    if (should_pass and not cmp) or (not should_pass and cmp):
      print('Test case %s failed.' % cmd)
      failures += 1

  with open(os.devnull, 'w') as devnull:
    for cmd, codepoints in FAIL_TESTS:
      if RunCmd(cmd, codepoints, fail=True) == 0:
        failures += 1

  if failures > 0:
    print('%s test(s) failed.' % failures)
    return 1

  print('All tests passed')
  return 0


if __name__ == '__main__':
  sys.exit(main())

